"""Combine complete operating points without changing their recorded decisions."""

import json
from collections import Counter

from eot_eval.analysis import analyse, condition_label


def operating_point_label(condition, config):
    label = condition_label(condition)
    if condition.startswith("livekit"):
        threshold = config.get("livekit_threshold")
        value = "Deutsch-Standard" if threshold is None else str(threshold).replace(".", ",")
        return f"{label} · {value}"
    if condition == "scribe-v3-live":
        return f"{label} · {str(config.get('scribe_threshold', 0.9)).replace('.', ',')}"
    return label


def build_comparison(store, selections, timely_ms):
    if not 1 <= len(selections) <= 12 or len(set(selections)) != len(selections):
        raise ValueError("Bitte 1 bis 12 unterschiedliche Betriebspunkte auswählen.")
    combined, sources, clips = [], [], []
    reference = None
    reference_mode = None
    dataset = None
    for selection in selections:
        run_id, separator, condition = selection.partition(":")
        if not separator or not run_id or not condition:
            raise ValueError("Ungültige Auswahl eines Betriebspunkts.")
        run = store.get("runs", run_id)
        if run["status"] != "completed":
            raise ValueError("Nur abgeschlossene Läufe können kombiniert werden.")
        path = store.root / "runs" / run["id"] / "report.json"
        if not path.is_file():
            raise ValueError("Für einen ausgewählten Lauf fehlen die Ergebnisse.")
        report = json.loads(path.read_text())
        rows = [r for r in report["rows"] if r["condition"] == condition]
        if not rows:
            raise ValueError("Der ausgewählte Betriebspunkt ist in diesem Lauf nicht vorhanden.")
        release = store.get("releases", run["release_id"])
        records = [
            r for r in release["records"] if run.get("split") is None or r.get("split") == run["split"]
        ]
        record_map = {r["id"]: r for r in records}
        if len(rows) != len(records) or {r["id"] for r in rows} != set(record_map):
            raise ValueError("Der Betriebspunkt enthält nicht genau eine Auswertung je Audiodatei.")
        signature = {}
        for row in rows:
            record = record_map[row["id"]]
            gold_ms = record["annotation"]["gold_eot_sample"] * 1000 / record["sample_rate"]
            if abs(row["gold_eot_ms"] - gold_ms) > 0.000001:
                raise ValueError("Referenzenden von Lauf und Datensatz stimmen nicht überein.")
            signature[row["id"]] = (record["sha256"], record["sample_rate"], gold_ms)
        mode = run["config"]["mode"]
        if reference is None:
            reference, reference_mode = signature, mode
            dataset = report.get("dataset", {})
            clips = [
                {
                    k: r.get(k)
                    for k in ("id", "annotation", "provenance", "source", "sample_rate", "scenario_id")
                }
                for r in records
            ]
        elif signature != reference or mode != reference_mode:
            raise ValueError(
                "Bitte Läufe mit denselben Audiodateien, Referenzenden und demselben Zeitmodus wählen."
            )
        label = operating_point_label(condition, run["config"])
        sources.append({"selection": selection, "condition": condition, "label": label, "run": run})
        combined.extend(
            {
                **r,
                "condition": selection,
                "condition_label": label,
                "source_condition": condition,
                "source_run_id": run_id,
                "source_run_name": run["name"],
            }
            for r in rows
        )
    labels = Counter(source["label"] for source in sources)
    for source in sources:
        if labels[source["label"]] > 1:
            source["label"] += f" · {source['run']['name']}"
    source_labels = {source["selection"]: source["label"] for source in sources}
    for row in combined:
        row["condition_label"] = source_labels[row["condition"]]
    return {
        "comparison": {"selections": selections, "sources": sources},
        "run": {"name": "Modellvergleich", "status": "completed", "config": {"mode": reference_mode}},
        "report": {"rows": combined, "dataset": dataset},
        "clips": clips,
        "analysis": analyse(combined, timely_ms),
    }
