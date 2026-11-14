"""Presentation analysis derived from immutable per-turn observations, including legacy runs."""

import math

from eot_eval.metrics import percentile

OUTCOMES = ["early", "timely", "late", "failure"]
DEFAULT_TIMELY_MS = 1600
OUTCOME_LABELS = {
    "early": "Zu früh",
    "timely": "Im Zeitfenster",
    "late": "Verzögert",
    "failure": "Technischer Ausfall / kein Ende",
}
CONTENT_LABELS = {
    "I": "IBAN",
    "K": "Kundennummer",
    "E": "E-Mail",
    "A": "Adresse / Termin",
    "T": "Technisches Anliegen",
    "V": "Vertrag / Rechnung",
}


def condition_label(condition):
    if condition.startswith("baseline-"):
        return "Silero · " + condition.removeprefix("baseline-").replace("ms", " ms")
    return {
        "livekit-v1-cloud": "LiveKit v1 Cloud",
        "livekit-v1-mini-local": "LiveKit v1-mini lokal",
        "livekit": "LiveKit (ältere Integration)",
        "smart_turn": "Smart Turn v3.2",
        "scribe-v3-live": "Scribe v3 Live",
    }.get(condition, condition)


def classify(row, timely_ms=DEFAULT_TIMELY_MS):
    commit, gold = row.get("commit_ms"), row.get("gold_eot_ms")
    valid = all(isinstance(v, (int, float)) and math.isfinite(v) for v in (commit, gold))
    delta = float(commit - gold) if valid else None
    if row.get("error") or not valid:
        outcome = "failure"
    elif delta < 0:
        outcome = "early"
    elif delta <= timely_ms:
        outcome = "timely"
    else:
        outcome = "late"
    return {
        **row,
        "outcome": outcome,
        "delta_ms": delta,
        "early_ms": -delta if outcome == "early" else None,
        "delay_ms": delta if outcome in {"timely", "late"} else None,
    }


def analyse(rows, timely_ms=DEFAULT_TIMELY_MS):
    classified = [classify(row, timely_ms) for row in rows]
    conditions = list(dict.fromkeys(row["condition"] for row in rows))
    summaries = []
    for condition in conditions:
        items = [r for r in classified if r["condition"] == condition]
        counts = {outcome: sum(r["outcome"] == outcome for r in items) for outcome in OUTCOMES}
        early = [r["early_ms"] for r in items if r["early_ms"] is not None]
        delays = [r["delay_ms"] for r in items if r["delay_ms"] is not None]
        deltas = [r["delta_ms"] for r in items if r["outcome"] != "failure"]
        summaries.append(
            {
                "condition": condition,
                "label": items[0].get("condition_label") or condition_label(condition),
                "n": len(items),
                "counts": counts,
                "early_rate": counts["early"] / len(items),
                "delta_n": len(deltas),
                "delta_mean_ms": sum(deltas) / len(deltas) if deltas else None,
                "early_lead_mean_ms": sum(early) / len(early) if early else None,
                "early_lead_median_ms": percentile(early, 50),
                "early_lead_p95_ms": percentile(early, 95),
                "delay_n": len(delays),
                "delay_median_ms": percentile(delays, 50),
                "delay_p95_ms": percentile(delays, 95),
                "fallback_count": None
                if items[0].get("source_condition", condition).startswith("baseline")
                else sum(r.get("trigger") == "fallback_timeout" and r["outcome"] != "failure" for r in items),
            }
        )
    return {
        "timely_ms": timely_ms,
        "conditions": summaries,
        "rows": classified,
        "record_count": len({r["id"] for r in rows}),
        "observation_count": len(rows),
        "failure_count": sum(r["outcome"] == "failure" for r in classified),
    }
