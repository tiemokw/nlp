import csv
import os
import platform
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import soundfile as sf

from app.audio import digest
from app.store import Store, dumps, now
from eot_eval.config import ExperimentConfig
from eot_eval.metrics import aggregate, paired_latencies, score_turn
from eot_eval.models import Silero, fingerprints, load, version
from eot_eval.replay import replay


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plots(folder, rows, summary):
    from eot_eval.charts import figure_bytes

    for chart in ("outcomes", "timing", "latency", "cases", "tradeoff"):
        for fmt in ("png", "svg"):
            (folder / f"{chart}.{fmt}").write_bytes(figure_bytes(rows, chart, fmt))
    groups = []
    for category in sorted({r["content_type"] for r in rows}):
        for item in aggregate([r for r in rows if r["content_type"] == category]):
            groups.append({"content_type": category, **item})
    write_csv(folder / "by_content.csv", groups)
    groups = []
    for pattern in sorted({r["turn_pattern"] for r in rows}):
        for item in aggregate([r for r in rows if r["turn_pattern"] == pattern]):
            groups.append({"turn_pattern": pattern, **item})
    write_csv(folder / "by_pattern.csv", groups)
    groups = []
    for profile in sorted({r["pause_profile"] for r in rows if r.get("pause_profile")}):
        for item in aggregate([r for r in rows if r.get("pause_profile") == profile]):
            groups.append({"pause_profile": profile, **item})
    if groups:
        write_csv(folder / "by_pause_profile.csv", groups)


def evaluate_condition(root, records, config, model_name, timeout, cancelled=None):
    """Each thread owns its VAD, model and streaming session; only results are shared."""
    local = threading.local()
    contexts = []
    lock = threading.Lock()

    def evaluate(index, record):
        if cancelled and cancelled():
            return None
        if not hasattr(local, "context"):
            vad = Silero()
            model = load(model_name, root, livekit_version=config.livekit_version) if model_name else None
            local.context = (vad, model)
            with lock:
                contexts.append(local.context)
        vad, model = local.context
        audio_path = root / record["audio_path"]
        if digest(audio_path.read_bytes()) != record["sha256"]:
            raise ValueError("Eine freigegebene Audiodatei wurde verändert.")
        audio, rate = sf.read(audio_path, dtype="float32")
        if rate != 16000 or audio.ndim != 1:
            raise ValueError("Ungültiges Audioformat im freigegebenen Stand.")
        result = replay(audio, vad, config, model=model, timeout_ms=timeout)
        metadata = dict(model.metadata) if model else {"name": "VAD + silence timer", "timeout_ms": timeout}
        return index, record, result, dict(vad.metadata), metadata

    try:
        with ThreadPoolExecutor(
            max_workers=min(config.parallelism, len(records)), thread_name_prefix="eot-replay"
        ) as pool:
            futures = [pool.submit(evaluate, index, record) for index, record in enumerate(records)]
            try:
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        yield result
            finally:
                for future in futures:
                    future.cancel()
    finally:
        close_error = None
        for _, model in contexts:
            if model is not None:
                try:
                    model.close()
                except Exception as exc:
                    close_error = close_error or exc
        if close_error is not None and sys.exc_info()[0] is None:
            raise close_error


def run(root: Path, ident: str):
    store = Store(root)
    job = store.get("runs", ident)
    if job["status"] != "queued":
        raise ValueError(
            "Nur neue, eingereihte Läufe können ausgeführt werden. Bitte eine neue Lauf-ID anlegen."
        )
    folder = root / "runs" / ident
    folder.mkdir(exist_ok=True)
    store.update_run(ident, "running", started_at=now(), progress=0)
    try:
        config = ExperimentConfig.model_validate({"livekit_version": "v1-mini", **job["config"]})
        if job.get("configuration_id"):
            frozen = store.get("configurations", job["configuration_id"])
            if frozen.get("model_fingerprints") != fingerprints(root, config.models, config.livekit_version):
                raise ValueError(
                    "Modelle oder Bibliotheken entsprechen nicht der eingefrorenen Konfiguration."
                )
        if job.get("model_fingerprints") and job["model_fingerprints"] != fingerprints(
            root, config.models, config.livekit_version
        ):
            raise ValueError(
                "Modelle oder Bibliotheken wurden seit dem Start verändert. Bitte die Evaluation neu starten."
            )
        release = store.get("releases", job["release_id"])
        # New runs evaluate the complete dataset. Older saved runs retain their selection.
        records = [r for r in release["records"] if job.get("split") is None or r["split"] == job["split"]]
        if not records:
            raise ValueError("Der gewählte Datensatz enthält keine Aufnahmen.")
        conditions = []
        for name in config.models:
            if name == "baseline":
                conditions.extend((f"baseline-{n}ms", None, n) for n in config.baseline_timeouts_ms)
            else:
                label = (
                    f"livekit-{config.livekit_version}-{'cloud' if config.livekit_version == 'v1' else 'local'}"
                    if name == "livekit"
                    else "scribe-v3-live"
                    if name == "scribe"
                    else name
                )
                conditions.append((label, name, None))
        manifest = {
            **job,
            "release_sha256": digest(dumps(release).encode()),
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "packages": {
                p: version(p)
                for p in ("silero-vad", "livekit-local-inference", "transformers", "onnxruntime", "numpy")
            },
            "vad": {},
            "parallelism": config.parallelism,
            "effective_parallelism": min(config.parallelism, len(records)),
            "models": {},
            "started_at": now(),
        }
        rows = []
        total = len(conditions) * len(records)

        def cancelled():
            return store.get("runs", ident)["status"] == "cancelled"

        with (folder / "events.jsonl").open("w", encoding="utf-8") as events:
            for condition, model_name, timeout in conditions:
                if cancelled():
                    return
                completed = {}
                for index, record, result, vad_metadata, model_metadata in evaluate_condition(
                    root, records, config, model_name, timeout, cancelled=cancelled
                ):
                    if cancelled():
                        return
                    manifest["vad"] = vad_metadata
                    manifest["models"][condition] = model_metadata
                    (folder / "manifest.json").write_text(dumps(manifest), encoding="utf-8")
                    for event in result.get("events", []):
                        events.write(dumps({"id": record["id"], "condition": condition, **event}) + "\n")
                    completed[index] = {"condition": condition, **score_turn(record, result)}
                    write_csv(folder / "per_turn.csv", rows + [completed[i] for i in sorted(completed)])
                    events.flush()
                    store.update_run(ident, "running", progress=len(rows) + len(completed), total=total)
                rows.extend(completed[i] for i in sorted(completed))
                if cancelled():
                    return
        summary = aggregate(rows)
        report = {
            "parallelism": config.parallelism,
            "summary": summary,
            "rows": rows,
            "paired_latencies": paired_latencies(rows),
            "dataset": {
                "source": release.get("source", "human"),
                "kind": release["kind"],
                "independent_base_files": release.get("independent_base_files"),
                "annotation_method": release.get("annotation_method", "manual"),
                "study_id": release.get("study_id"),
                "protocol": release.get("protocol"),
            },
        }
        write_csv(folder / "summary.csv", summary)
        (folder / "report.json").write_text(dumps(report), encoding="utf-8")
        plots(folder, rows, summary)
        manifest["completed_at"] = now()
        (folder / "manifest.json").write_text(dumps(manifest), encoding="utf-8")
        store.update_run(ident, "completed", completed_at=now(), progress=total, total=total)
    except Exception as exc:
        if store.get("runs", ident)["status"] != "cancelled":
            (folder / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            store.update_run(ident, "failed", error=f"{type(exc).__name__}: {exc}")
