import csv
import io
import json
import os
import subprocess
import sys
import threading
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from app.audio import MAX_UPLOAD, digest, waveform
from app.store import Conflict, Store, dumps, now
from app.study import AUTHOR_ID, study_cards
from app.synthesis import PROFILES, TEMPLATES, ElevenLabs, SynthesisConfig, api_base_url, api_key, preview
from eot_eval.analysis import DEFAULT_TIMELY_MS, analyse, condition_label
from eot_eval.charts import CHARTS, cached_comparison_figure, cached_figure
from eot_eval.comparison import build_comparison
from eot_eval.config import ExperimentConfig
from eot_eval.models import fingerprints, inventory
from eot_eval.settings import validate_livekit_credentials


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Reason(Strict):
    reason: str = Field(default="", max_length=1000)


class Hold(Strict):
    start_sample: int = Field(ge=0)
    end_sample: int = Field(gt=0)


class Annotation(Strict):
    gold_eot_sample: int = Field(gt=0)
    holds: list[Hold] = Field(default_factory=list, max_length=30)
    transcript: str = Field(default="", max_length=10000)
    annotator: str = Field(default="local", min_length=1, max_length=80)
    reviewer: str = Field(default="", max_length=80)
    status: Literal["annotated", "reviewed"] = "annotated"
    ambiguous_transition: bool = False
    notes: str = Field(default="", max_length=2000)
    listened: bool = False


class StudyReleaseRequest(Strict):
    synthetic_release_id: str = Field(min_length=1, max_length=100)


class Participant(Strict):
    label: str = Field(min_length=1, max_length=80)
    age_group: str = Field(default="", max_length=40)
    notes: str = Field(default="", max_length=500)


class ReleaseRequest(Strict):
    kind: Literal["development", "final"] = "development"


class EvaluationConfig(ExperimentConfig):
    models: list[Literal["baseline", "livekit", "scribe"]] = Field(
        default_factory=lambda: ["baseline", "livekit"], min_length=1, max_length=3
    )
    mode: Literal["realtime"] = "realtime"
    parallelism: int = Field(default=6, ge=1, le=6)


class RunRequest(Strict):
    name: str = Field(default="", max_length=120)
    release_id: str
    config: EvaluationConfig = Field(default_factory=EvaluationConfig)


class RunName(Strict):
    name: str = Field(min_length=1, max_length=120)


def create_app(data_dir=None):
    root = Path(data_dir or os.environ.get("EOT_DATA_DIR", "data")).resolve()
    store = Store(root)
    processes = {}
    synthesis_processes = {}
    run_lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        for job in store.listing("runs"):
            if job["status"] in {"running", "queued"}:
                store.update_run(
                    job["id"], "interrupted", error="Webserver wurde neu gestartet; Lauf nicht vollständig."
                )
        for job in store.listing("syntheses"):
            if job["status"] in {"queued", "running"}:
                store.update_synthesis(
                    job["id"],
                    "interrupted",
                    error="Server neu gestartet. Erfolgreiche Basisgenerierungen bleiben im Cache.",
                )
        yield
        for ident, proc in processes.items():
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                store.update_run(ident, "interrupted", error="Anwendung wurde beendet.")
        for ident, proc in synthesis_processes.items():
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                store.update_synthesis(
                    ident, "interrupted", error="Anwendung wurde beendet; Basisdateien bleiben im Cache."
                )

    app = FastAPI(title="EOT Lab", lifespan=lifespan)
    app.state.store = store

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409 if isinstance(exc, Conflict) else 400)

    @app.middleware("http")
    async def local_only(request, call_next):
        # Local utility: prevent cross-origin writes and DNS rebinding against localhost.
        host = request.url.hostname
        if host not in {"localhost", "127.0.0.1", "::1", "testserver"}:
            return JSONResponse({"detail": "Bitte die Anwendung über localhost öffnen."}, status_code=403)
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
            from urllib.parse import urlparse

            if urlparse(origin).netloc != request.url.netloc:
                return JSONResponse({"detail": "Unerlaubter Ursprung."}, status_code=403)
        return await call_next(request)

    @app.get("/api/overview")
    def overview():
        attempts = store.attempts()
        releases = store.listing("releases")
        latest_synthetic = next((r for r in releases if r.get("source") == "synthetic"), None)
        return {
            "participants": store.participants(),
            "selected": sum(a["selected"] for a in attempts),
            "annotated": sum(a["selected"] and a["annotation"] is not None for a in attempts),
            "reviewed": sum(
                a["selected"] and a["annotation"] is not None and a["annotation"]["status"] == "reviewed"
                for a in attempts
            ),
            "models": [m for m in inventory(root) if m["id"] != "smart_turn"],
            "synthetic_files": len(latest_synthetic["records"]) if latest_synthetic else 0,
            "release_count": len(releases),
        }

    @app.get("/api/synthesis/status")
    def synthesis_status():
        return {
            "configured": bool(api_key()),
            "api_base_url": api_base_url(),
            "env_file": str(Path(__file__).resolve().parent.parent / ".env"),
            "models": ["eleven_multilingual_v2", "eleven_flash_v2_5"],
            "templates": TEMPLATES,
            "profiles": PROFILES,
            "study_templates": study_cards(),
        }

    @app.get("/api/study")
    def study(synthetic_release_id: str | None = None):
        return store.study_state(synthetic_release_id)

    @app.post("/api/study/releases")
    def study_release(body: StudyReleaseRequest):
        return store.release_study(body.synthetic_release_id)

    @app.get("/api/experiment-defaults")
    def experiment_defaults():
        return EvaluationConfig().model_dump(exclude={"smart_turn_threshold"})

    @app.get("/api/synthesis/voices")
    def synthesis_voices():
        return ElevenLabs().voices()

    @app.post("/api/synthesis/preview")
    def synthesis_preview(body: SynthesisConfig):
        return preview(body, root)

    @app.get("/api/synthesis/jobs")
    def synthesis_jobs():
        for ident, proc in list(synthesis_processes.items()):
            if proc.poll() is not None:
                if store.get("syntheses", ident)["status"] in {"queued", "running"}:
                    store.update_synthesis(
                        ident, "failed", error="Generierungsprozess wurde unerwartet beendet."
                    )
                synthesis_processes.pop(ident)
        return store.listing("syntheses")

    @app.post("/api/synthesis/jobs")
    def start_synthesis(body: SynthesisConfig):
        with run_lock:
            if any(p.poll() is None for p in [*processes.values(), *synthesis_processes.values()]):
                raise Conflict("Ein Vergleich oder eine Generierung läuft bereits.")
            if not api_key():
                raise ValueError(
                    "ElevenLabs-API-Schlüssel fehlt. ELEVENLABS_API_KEY lokal in .env eintragen."
                )
            api_base_url()
            ident = uuid.uuid4().hex
            plan = preview(body, root)
            payload = {
                "id": ident,
                "config": body.model_dump(),
                "created_at": now(),
                "progress": 0,
                "total": plan["files"],
            }
            with store.connect() as db:
                db.execute("INSERT INTO syntheses VALUES(?,?,?,?)", (ident, "queued", dumps(payload), now()))
            folder = root / "synthetic" / ident
            folder.mkdir(parents=True, exist_ok=True)
            with (folder / "process.log").open("w") as log:
                synthesis_processes[ident] = subprocess.Popen(
                    [sys.executable, "-m", "eot_eval.cli", "--data-dir", str(root), "generate", ident],
                    cwd=Path(__file__).resolve().parent.parent,
                    env={**os.environ, "EOT_DATA_DIR": str(root)},
                    stdout=log,
                    stderr=log,
                )
            return {**payload, "status": "queued"}

    @app.post("/api/synthesis/jobs/{ident}/cancel")
    def cancel_synthesis(ident: str):
        job = store.get("syntheses", ident)
        if job["status"] in {"queued", "running"}:
            proc = synthesis_processes.get(ident)
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
            store.update_synthesis(ident, "cancelled")
        return store.get("syntheses", ident)

    @app.get("/api/clips/{ident}/audio")
    def clip_audio(ident: str):
        clip = store.clip(ident)
        return FileResponse(root / clip["audio_path"], media_type="audio/wav")

    @app.get("/api/clips/{ident}/waveform")
    def clip_waveform(ident: str):
        return waveform(root / store.clip(ident)["audio_path"])

    @app.get("/api/clips/{ident}")
    def clip(ident: str):
        return store.clip(ident)

    @app.post("/api/clips/{ident}/annotation")
    def annotate_clip(ident: str, body: Annotation):
        return store.annotate(ident, body.model_dump(exclude_unset=True))

    @app.put("/api/participants/{ident}")
    def participant(ident: str, body: Participant):
        store.update_participant(ident, body.model_dump())
        return {"ok": True}

    @app.get("/api/scenarios")
    def scenarios(participant_id: str = AUTHOR_ID):
        return store.scenarios(participant_id)

    @app.get("/api/attempts")
    def attempts(participant_id: str | None = None):
        return store.attempts(participant_id)

    @app.post("/api/attempts")
    async def upload(
        attempt_id: str = Form(),
        scenario_id: str = Form(),
        metadata: str = Form("{}"),
        audio: UploadFile = File(),
    ):
        data = await audio.read(MAX_UPLOAD + 1)
        if len(metadata) > 20000:
            raise ValueError("Aufnahmemetadaten sind zu groß.")
        capture = json.loads(metadata)
        if not isinstance(capture, dict):
            raise ValueError("Aufnahmemetadaten müssen ein Objekt sein.")
        return store.upload(attempt_id, scenario_id, data, capture)

    @app.post("/api/attempts/{ident}/select")
    def select(ident: str, body: Reason):
        return store.select(ident, body.reason)

    @app.post("/api/attempts/{ident}/reject")
    def reject(ident: str, body: Reason):
        store.reject(ident, body.reason)
        return {"ok": True}

    @app.get("/api/attempts/{ident}/audio")
    def audio_file(ident: str, original: bool = False):
        store.attempt(ident)
        return FileResponse(
            root / ("originals" if original else "canonical") / f"{ident}.wav", media_type="audio/wav"
        )

    @app.get("/api/attempts/{ident}/waveform")
    def peaks(ident: str):
        store.attempt(ident)
        return waveform(root / "canonical" / f"{ident}.wav")

    @app.post("/api/attempts/{ident}/annotation")
    def annotate(ident: str, body: Annotation):
        return store.annotate(ident, body.model_dump())

    @app.get("/api/releases")
    def releases():
        return store.listing("releases")

    @app.post("/api/releases")
    def release(body: ReleaseRequest):
        return store.release(body.kind)

    @app.get("/api/releases/{ident}/download")
    def download_release(ident: str):
        payload = store.get("releases", ident)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", dumps(payload))
            if payload.get("kind") == "study_paired":
                scenarios = {r["scenario_id"]: r["scenario"] for r in payload["records"]}
                archive.writestr("scenarios.json", dumps(list(scenarios.values())))
                table = io.StringIO()
                writer = csv.writer(table)
                writer.writerow(
                    [
                        "pair_id",
                        "scenario_id",
                        "source",
                        "content_type",
                        "turn_pattern",
                        "audio_path",
                        "gold_eot_seconds",
                        "transcript",
                    ]
                )
                for r in payload["records"]:
                    writer.writerow(
                        [
                            r["pair_id"],
                            r["scenario_id"],
                            r["source"],
                            r["content_type"],
                            r["turn_pattern"],
                            r["audio_path"],
                            r["annotation"]["gold_eot_sample"] / r["sample_rate"],
                            r["annotation"]["transcript"],
                        ]
                    )
                archive.writestr("annotations.csv", table.getvalue())
            included_bases = set()
            for record in payload["records"]:
                audio_path = root / record["audio_path"]
                if digest(audio_path.read_bytes()) != record["sha256"]:
                    raise Conflict("Eine freigegebene Audiodatei wurde verändert; Export abgebrochen.")
                archive.write(audio_path, record["audio_path"])
                if record.get("source") == "synthetic" and record["base_id"] not in included_bases:
                    base = root / "synthetic" / "cache" / record["base_id"] / "response.json"
                    expected = record["provenance"].get("cache_response_sha256")
                    if expected and digest(base.read_bytes()) != expected:
                        raise Conflict("Eine TTS-Basisantwort wurde verändert; Export abgebrochen.")
                    archive.write(base, f"bases/{record['base_id']}.json")
                    included_bases.add(record["base_id"])
        return Response(
            buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="dataset-{ident}.zip"'},
        )

    @app.get("/api/configurations")
    def configurations():
        return store.listing("configurations")

    @app.post("/api/configurations")
    def freeze(body: ExperimentConfig):
        return store.freeze_config(body.model_dump(), fingerprints(root, body.models, body.livekit_version))

    @app.get("/api/runs")
    def runs():
        for ident, proc in list(processes.items()):
            if proc.poll() is not None:
                job = store.get("runs", ident)
                if job["status"] in {"running", "queued"}:
                    store.update_run(ident, "failed", error="Evaluationsprozess wurde unerwartet beendet.")
                processes.pop(ident)
        result = store.listing("runs")
        for job in result:
            path = root / "runs" / job["id"] / "report.json"
            job["report_ready"] = path.exists()
            if path.exists():
                report = json.loads(path.read_text())
                job["record_count"] = len({r["id"] for r in report["rows"]})
                job["condition_count"] = len({r["condition"] for r in report["rows"]})
                job["conditions"] = [
                    {"id": condition, "label": condition_label(condition)}
                    for condition in dict.fromkeys(r["condition"] for r in report["rows"])
                ]
                job["source"] = report.get("dataset", {}).get("source", "human")
        return result

    @app.patch("/api/runs/{ident}")
    def rename_run(ident: str, body: RunName):
        return store.rename_run(ident, body.name)

    @app.post("/api/runs")
    def start_run(body: RunRequest):
        with run_lock:
            return start_run_locked(body)

    def start_run_locked(body: RunRequest):
        if any(proc.poll() is None for proc in [*processes.values(), *synthesis_processes.values()]):
            raise Conflict("Ein Vergleich läuft bereits. Modelle werden nacheinander gemessen.")
        release = store.get("releases", body.release_id)
        config = body.config
        if release["kind"] == "study_synthetic":
            raise ValueError(
                "Bitte zuerst die Referenzenden bestätigen und den Studiendatensatz abschließen."
            )
        if not release["records"]:
            raise ValueError("Der gewählte Datensatz enthält keine Aufnahmen.")
        if "livekit" in config.models and config.livekit_version == "v1":
            validate_livekit_credentials()
        if "scribe" in config.models:
            ElevenLabs()  # Validate credentials and residency endpoint before starting a worker.
        available = {m["id"]: m["ready"] for m in inventory(root, config.livekit_version)}
        if any(not available.get(name, False) for name in config.models):
            raise ValueError(
                "Mindestens ein Modell ist nicht vorbereitet. Bitte Modellstatus und README prüfen."
            )
        ident = uuid.uuid4().hex
        payload = {
            "id": ident,
            "name": body.name.strip() or f"Evaluation {ident[:8]}",
            "release_id": body.release_id,
            "config": config.model_dump(exclude={"smart_turn_threshold"}),
            "model_fingerprints": fingerprints(root, config.models, config.livekit_version),
            "record_count": len(release["records"]),
            "total": len(release["records"])
            * sum(len(config.baseline_timeouts_ms) if model == "baseline" else 1 for model in config.models),
            "created_at": now(),
            "progress": 0,
        }
        with store.connect() as db:
            db.execute("INSERT INTO runs VALUES(?,?,?,?)", (ident, "queued", dumps(payload), now()))
        folder = root / "runs" / ident
        folder.mkdir(exist_ok=True)
        env = {
            **os.environ,
            "EOT_DATA_DIR": str(root),
            "MPLCONFIGDIR": str(folder / "matplotlib-cache"),
            "HF_HOME": str(root / "models" / "hf-cache"),
        }
        try:
            with (folder / "process.log").open("w") as log:
                processes[ident] = subprocess.Popen(
                    [sys.executable, "-m", "eot_eval.cli", "--data-dir", str(root), "run", ident],
                    cwd=Path(__file__).resolve().parent.parent,
                    env=env,
                    stdout=log,
                    stderr=log,
                )
        except OSError:
            store.update_run(ident, "failed", error="Der Evaluationsprozess konnte nicht gestartet werden.")
            raise ValueError(
                "Der Evaluationsprozess konnte nicht gestartet werden. Bitte erneut versuchen."
            ) from None
        return {**payload, "status": "queued"}

    @app.post("/api/runs/{ident}/cancel")
    def cancel(ident: str):
        store.get("runs", ident)
        proc = processes.get(ident)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        if store.get("runs", ident)["status"] in {"running", "queued"}:
            store.update_run(ident, "cancelled")
        return store.get("runs", ident)

    @app.get("/api/comparisons/report")
    def comparison_report(
        selection: list[str] = Query(min_length=1, max_length=12),
        timely_ms: int = Query(default=DEFAULT_TIMELY_MS, ge=0, le=5000),
    ):
        return build_comparison(store, selection, timely_ms)

    @app.get("/api/comparisons/charts/{chart}")
    def comparison_chart(
        chart: str,
        selection: list[str] = Query(min_length=1, max_length=12),
        format: Literal["png", "svg"] = "png",
        timely_ms: int = Query(default=DEFAULT_TIMELY_MS, ge=0, le=5000),
        download: bool = False,
    ):
        if chart not in CHARTS:
            return JSONResponse({"detail": "Unbekannte Grafik."}, status_code=404)
        data = build_comparison(store, selection, timely_ms)
        content = cached_comparison_figure(dumps(data["report"]["rows"]), chart, format, timely_ms)
        headers = (
            {"Content-Disposition": f'attachment; filename="eot-vergleich-{chart}-{timely_ms}ms.{format}"'}
            if download
            else {}
        )
        return Response(
            content, media_type="image/svg+xml" if format == "svg" else "image/png", headers=headers
        )

    @app.get("/api/comparisons/download")
    def comparison_download(
        selection: list[str] = Query(min_length=1, max_length=12),
        timely_ms: int = Query(default=DEFAULT_TIMELY_MS, ge=0, le=5000),
    ):
        data = build_comparison(store, selection, timely_ms)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("comparison.json", dumps({**data["comparison"], "timely_ms": timely_ms}))
            archive.writestr("analysis.json", dumps(data["analysis"]))
            for name, rows in (
                ("per_turn", data["analysis"]["rows"]),
                ("summary", data["analysis"]["conditions"]),
            ):
                table = io.StringIO()
                writer = csv.DictWriter(table, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
                writer.writeheader()
                writer.writerows(rows)
                archive.writestr(f"{name}.csv", table.getvalue())
            for chart_name in sorted(CHARTS):
                for fmt in ("png", "svg"):
                    archive.writestr(
                        f"figures/{chart_name}.{fmt}",
                        cached_comparison_figure(dumps(data["report"]["rows"]), chart_name, fmt, timely_ms),
                    )
        return Response(
            buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="eot-vergleich-{timely_ms}ms.zip"'},
        )

    @app.get("/api/runs/{ident}/report")
    def report(ident: str, timely_ms: int = Query(default=DEFAULT_TIMELY_MS, ge=0, le=5000)):
        runs()  # Also reconcile unexpectedly terminated workers while viewing a live detail page.
        job = store.get("runs", ident)
        path = root / "runs" / ident / "report.json"
        release = store.get("releases", job["release_id"])
        clips = [
            {
                key: record.get(key)
                for key in ("id", "annotation", "provenance", "source", "sample_rate", "scenario_id")
            }
            for record in release["records"]
            if job.get("split") is None or record["split"] == job["split"]
        ]
        result = json.loads(path.read_text()) if path.exists() else None
        return {
            "run": job,
            "report": result,
            "clips": clips,
            "analysis": analyse(result["rows"], timely_ms) if result else None,
        }

    @app.get("/api/runs/{ident}/download")
    def download_run(ident: str, timely_ms: int = Query(default=DEFAULT_TIMELY_MS, ge=0, le=5000)):
        store.get("runs", ident)
        if store.get("runs", ident)["status"] in {"running", "queued"}:
            raise Conflict("Bitte warten, bis der Lauf beendet ist.")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in (root / "runs" / ident).glob("*"):
                if path.is_file():
                    archive.write(path, path.name)
            job = store.get("runs", ident)
            archive.writestr(
                "display_metadata.json",
                dumps({"id": ident, "name": job["name"], "name_updated_at": job.get("name_updated_at")}),
            )
            report_path = root / "runs" / ident / "report.json"
            if report_path.exists():
                analysis = analyse(json.loads(report_path.read_text())["rows"], timely_ms)
                archive.writestr("analysis.json", dumps(analysis))
                table = io.StringIO()
                if analysis["rows"]:
                    writer = csv.DictWriter(table, fieldnames=list(analysis["rows"][0]))
                    writer.writeheader()
                    writer.writerows(analysis["rows"])
                archive.writestr("analysis_per_turn.csv", table.getvalue())
                for chart_name in sorted(CHARTS):
                    for fmt in ("png", "svg"):
                        archive.writestr(
                            f"figures/{chart_name}.{fmt}",
                            cached_figure(
                                str(report_path), report_path.stat().st_mtime_ns, chart_name, fmt, timely_ms
                            ),
                        )
        return Response(
            buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="run-{ident}.zip"'},
        )

    @app.get("/api/runs/{ident}/plot")
    def plot(ident: str):
        store.get("runs", ident)
        path = root / "runs" / ident / "report.json"
        if not path.exists():
            return JSONResponse({"detail": "Noch keine Abbildung verfügbar."}, status_code=404)
        return Response(
            cached_figure(str(path), path.stat().st_mtime_ns, "tradeoff", "png", DEFAULT_TIMELY_MS),
            media_type="image/png",
        )

    @app.get("/api/runs/{ident}/charts/{chart}")
    def chart(
        ident: str,
        chart: str,
        format: Literal["png", "svg"] = "png",
        timely_ms: int = Query(default=DEFAULT_TIMELY_MS, ge=0, le=5000),
        download: bool = False,
    ):
        store.get("runs", ident)
        if chart not in CHARTS:
            return JSONResponse({"detail": "Unbekannte Grafik."}, status_code=404)
        path = root / "runs" / ident / "report.json"
        if not path.exists():
            return JSONResponse({"detail": "Ergebnisse liegen noch nicht vor."}, status_code=404)
        content = cached_figure(str(path), path.stat().st_mtime_ns, chart, format, timely_ms)
        headers = (
            {"Content-Disposition": f'attachment; filename="eot-{ident[:8]}-{chart}-{timely_ms}ms.{format}"'}
            if download
            else {}
        )
        return Response(
            content, media_type="image/svg+xml" if format == "svg" else "image/png", headers=headers
        )

    app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")
    return app
