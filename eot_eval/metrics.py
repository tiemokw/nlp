import numpy as np


def percentile(values, q):
    return float(np.percentile(values, q)) if values else None


def score_turn(record, result):
    gold = record["annotation"]["gold_eot_sample"] / record["sample_rate"] * 1000
    commit = result["commit_ms"]
    premature = commit is not None and commit < gold
    return {
        "id": record["id"],
        "source": record.get("source", "human"),
        "base_id": record.get("base_id"),
        "pause_profile": record.get("provenance", {}).get("profile", {}).get("id"),
        "reference_method": record["annotation"].get("reference_method", "manual"),
        "scenario_id": record["scenario_id"],
        "pair_id": record.get("pair_id"),
        "participant_id": record["participant_id"],
        "content_type": record["content_type"],
        "turn_pattern": record["turn_pattern"],
        "gold_eot_ms": gold,
        "commit_ms": commit,
        "premature": premature,
        "latency_ms": commit - gold if commit is not None and not premature else None,
        "trigger": result["trigger"],
        "mode": result["mode"],
        "error": result["error"],
        "inference_median_ms": percentile(result["inference_ms"], 50),
        "inference_p95_ms": percentile(result["inference_ms"], 95),
        "inference_total_ms": None
        if result.get("inference_measure") == "streaming_service"
        else sum(result["inference_ms"]),
        "inference_measure": result.get("inference_measure", "local_adapter"),
        "sdk_server_e2e_median_ms": percentile(result.get("sdk_server_e2e_ms", []), 50),
        "vad_total_ms": result["vad_total_ms"],
        "ambiguous": record["annotation"]["ambiguous_transition"],
        "skipped_queries": result["skipped_queries"],
    }


def aggregate(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["condition"], []).append(row)
    summary = []
    for condition, items in groups.items():
        latencies = [r["latency_ms"] for r in items if r["latency_ms"] is not None]
        failures = sum(bool(r["error"]) or r["commit_ms"] is None for r in items)
        summary.append(
            {
                "condition": condition,
                "mode": items[0]["mode"],
                "inference_measure": items[0].get("inference_measure", "local_adapter"),
                "n": len(items),
                "premature_count": sum(r["premature"] for r in items),
                "premature_rate": sum(r["premature"] for r in items) / len(items),
                "latency_n": len(latencies),
                "latency_median_ms": percentile(latencies, 50),
                "latency_p95_ms": percentile(latencies, 95),
                "failures": failures,
                "fallback_count": None
                if condition.startswith("baseline")
                else sum(r["trigger"] == "fallback_timeout" for r in items),
                "inference_per_turn_median_ms": percentile(
                    [r["inference_total_ms"] for r in items if r["inference_total_ms"] is not None], 50
                ),
            }
        )
    return summary


def paired_latencies(rows):
    conditions = sorted({r["condition"] for r in rows})
    indexed = {(r["condition"], r["id"]): r for r in rows}
    result = []
    for pos, left in enumerate(conditions):
        for right in conditions[pos + 1 :]:
            differences = []
            for ident in {r["id"] for r in rows}:
                a, b = indexed.get((left, ident)), indexed.get((right, ident))
                if a and b and a["latency_ms"] is not None and b["latency_ms"] is not None:
                    differences.append(a["latency_ms"] - b["latency_ms"])
            result.append(
                {
                    "left": left,
                    "right": right,
                    "n": len(differences),
                    "median_left_minus_right_ms": percentile(differences, 50),
                }
            )
    return result
