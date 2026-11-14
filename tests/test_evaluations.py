import io
import json
import zipfile

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import Store, dumps
from eot_eval.analysis import analyse, classify
from eot_eval.charts import CHARTS, figure_bytes
from eot_eval.config import ExperimentConfig


def observation(condition="baseline-500ms", commit=1500, error=None):
    return {
        "id": "fixture",
        "condition": condition,
        "commit_ms": commit,
        "gold_eot_ms": 1000,
        "error": error,
        "mode": "realtime",
        "content_type": "K",
        "trigger": "semantic",
    }


def test_outcomes_have_explicit_boundaries_and_exclusive_failures():
    assert classify(observation(commit=999))["outcome"] == "early"
    assert classify(observation(commit=1000))["outcome"] == "timely"
    assert classify(observation(commit=1500))["outcome"] == "timely"
    assert classify(observation(commit=2600))["outcome"] == "timely"
    assert classify(observation(commit=2601))["outcome"] == "late"
    assert classify(observation(commit=None))["outcome"] == "failure"
    assert classify(observation(commit=800, error="provider failed"))["outcome"] == "failure"
    assert classify(observation(commit=800))["early_ms"] == 200
    assert classify(observation(commit=1400), timely_ms=250)["outcome"] == "late"


def test_aggregate_keeps_failures_and_early_cutoffs_out_of_delay_statistics():
    rows = [observation(commit=n) for n in (500, 1000, 1600, None)]
    rows.append(observation(commit=1200, error="network error"))
    result = analyse(rows, timely_ms=500)
    summary = result["conditions"][0]
    assert summary["counts"] == {"early": 1, "timely": 1, "late": 1, "failure": 2}
    assert sum(summary["counts"].values()) == summary["n"] == 5
    assert summary["delay_n"] == 2 and summary["delay_median_ms"] == 300
    assert summary["early_lead_median_ms"] == 500
    assert summary["early_rate"] == 0.2


@pytest.fixture
def saved_run(tmp_path):
    store = Store(tmp_path)
    audio = io.BytesIO()
    sf.write(audio, np.zeros(8 * 16000), 16000, format="WAV")
    clip_id = "147a7619-42af-4d3a-a26a-01675fa1585d"
    store.upload(clip_id, "P01-K-F", audio.getvalue(), {})
    store.select(clip_id)
    store.annotate(
        clip_id,
        {
            "gold_eot_sample": 16000,
            "holds": [],
            "transcript": "Test",
            "annotator": "fixture",
            "reviewer": "",
            "status": "annotated",
            "ambiguous_transition": False,
            "notes": "",
        },
    )
    release = store.release("development")
    job = {
        "id": "legacy-run",
        "release_id": release["id"],
        "split": "dev",
        "created_at": "2026-11-12T09:00:00+00:00",
        "config": ExperimentConfig().model_dump(),
    }
    with store.connect() as db:
        db.execute(
            "INSERT INTO runs VALUES(?,?,?,?)", (job["id"], "completed", dumps(job), job["created_at"])
        )
    folder = tmp_path / "runs" / job["id"]
    folder.mkdir()
    rows = [
        observation(commit=800),
        observation("livekit-v1-cloud", 1300),
        observation("smart_turn", None),
        observation("scribe-v3-live", 1800),
    ]
    rows = [{**r, "id": clip_id} for r in rows]
    report = {"rows": rows, "summary": [], "paired_latencies": [], "dataset": {"source": "human"}}
    (folder / "report.json").write_text(dumps(report))
    with TestClient(create_app(tmp_path)) as client:
        yield client, store, folder


def test_legacy_runs_can_be_renamed_without_changing_measurements(saved_run):
    client, store, folder = saved_run
    original = (folder / "report.json").read_bytes()
    assert client.get("/api/runs").json()[0]["name"]
    response = client.patch("/api/runs/legacy-run", json={"name": "  Pilot mit langen Pausen  "})
    assert response.status_code == 200 and response.json()["name"] == "Pilot mit langen Pausen"
    assert client.get("/api/runs").json()[0]["report_ready"] is True
    assert client.patch("/api/runs/legacy-run", json={"name": " "}).status_code == 400
    assert client.patch("/api/runs/legacy-run", json={"name": "x" * 121}).status_code == 422
    assert client.patch("/api/runs/missing", json={"name": "Test"}).status_code == 400
    # Simulate an older worker payload being saved after the rename.
    with store.connect() as db:
        row = db.execute("SELECT payload FROM runs WHERE id='legacy-run'").fetchone()
        payload = json.loads(row["payload"])
        payload["name"] = "Old worker label"
        db.execute("UPDATE runs SET payload=? WHERE id='legacy-run'", (dumps(payload),))
    store.update_run("legacy-run", "completed", progress=4)
    assert store.get("runs", "legacy-run")["name"] == "Pilot mit langen Pausen"
    assert (folder / "report.json").read_bytes() == original


def test_new_evaluation_name_is_saved_at_creation(saved_run, monkeypatch):
    from app import main

    client, store, _ = saved_run

    class Process:
        stopped = False

        def __init__(self, *args, **kwargs):
            pass

        def poll(self):
            return 0 if self.stopped else None

        def terminate(self):
            self.stopped = True

        def wait(self, **kwargs):
            return 0

    monkeypatch.setattr(main.subprocess, "Popen", Process)
    monkeypatch.setattr(main, "inventory", lambda *args: [{"id": "baseline", "ready": True}])
    response = client.post(
        "/api/runs",
        json={
            "name": "  Pilot · Zahlenfolgen  ",
            "release_id": store.get("runs", "legacy-run")["release_id"],
            "config": {"models": ["baseline"]},
        },
    )
    assert response.status_code == 200
    job = response.json()
    assert job["name"] == "Pilot · Zahlenfolgen"
    assert store.get("runs", job["id"])["name"] == job["name"]


def test_report_reclassification_and_figure_exports_work_for_legacy_runs(saved_run):
    client, _, _ = saved_run
    initial = client.get("/api/runs/legacy-run/report").json()["analysis"]
    changed = client.get("/api/runs/legacy-run/report?timely_ms=200").json()["analysis"]
    assert initial["conditions"][1]["counts"]["timely"] == 1
    assert changed["conditions"][1]["counts"]["late"] == 1
    assert client.get("/api/runs/legacy-run/report?timely_ms=-1").status_code == 422
    svg = client.get("/api/runs/legacy-run/charts/outcomes?format=svg&download=true")
    assert svg.status_code == 200 and "<svg" in svg.text
    assert "attachment" in svg.headers["content-disposition"]
    assert client.get("/api/runs/legacy-run/charts/missing").status_code == 404
    assert client.get("/api/runs/legacy-run/charts/timing?format=html").status_code == 422


def test_zip_contains_editable_figures_and_signed_observations(saved_run):
    client, _, folder = saved_run
    original = (folder / "report.json").read_bytes()
    client.patch("/api/runs/legacy-run", json={"name": "Auswertung für die Hausarbeit"})
    response = client.get("/api/runs/legacy-run/download?timely_ms=750")
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert json.loads(archive.read("display_metadata.json"))["name"] == "Auswertung für die Hausarbeit"
        assert json.loads(archive.read("analysis.json"))["timely_ms"] == 750
        assert "delta_ms" in archive.read("analysis_per_turn.csv").decode()
        assert "-200.0" in archive.read("analysis_per_turn.csv").decode()
        for name in CHARTS:
            assert archive.read(f"figures/{name}.png").startswith(b"\x89PNG")
            assert b"<svg" in archive.read(f"figures/{name}.svg")
    assert (folder / "report.json").read_bytes() == original


def test_charts_handle_empty_and_failed_only_evaluations():
    assert figure_bytes([], "outcomes").startswith(b"\x89PNG")
    for chart in ("timing", "latency", "tradeoff", "cases"):
        assert b"<svg" in figure_bytes([observation(commit=None)], chart, "svg")


def copy_run(store, folder, ident="second-run", **changes):
    run = {**store.get("runs", "legacy-run"), "id": ident, "name": "Zweiter Lauf", **changes}
    with store.connect() as db:
        db.execute("INSERT INTO runs VALUES(?,?,?,?)", (ident, "completed", dumps(run), run["created_at"]))
    target = folder.parent / ident
    target.mkdir()
    (target / "report.json").write_bytes((folder / "report.json").read_bytes())
    return target


def test_comparison_preserves_source_identity_and_counts_each_record_once(saved_run):
    client, store, folder = saved_run
    original = (folder / "report.json").read_bytes()
    copy_run(store, folder)
    params = [("selection", "legacy-run:baseline-500ms"), ("selection", "second-run:baseline-500ms")]
    response = client.get("/api/comparisons/report", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"]["timely_ms"] == 1600
    assert data["analysis"]["record_count"] == 1
    assert data["analysis"]["observation_count"] == 2
    assert len(data["clips"]) == 1
    assert len(data["analysis"]["conditions"]) == 2
    assert len({s["label"] for s in data["analysis"]["conditions"]}) == 2
    assert [r["source_run_id"] for r in data["report"]["rows"]] == ["legacy-run", "second-run"]
    assert all(s["fallback_count"] is None for s in data["analysis"]["conditions"])
    assert (folder / "report.json").read_bytes() == original


@pytest.mark.parametrize("problem", ["duplicate", "missing", "reference", "mode", "incomplete"])
def test_comparison_rejects_incomplete_or_incompatible_observations(saved_run, problem):
    client, store, folder = saved_run
    target = copy_run(store, folder)
    report_path = target / "report.json"
    data = json.loads(report_path.read_text())
    if problem == "duplicate":
        data["rows"].append(data["rows"][0])
    elif problem == "missing":
        data["rows"] = data["rows"][1:]
    elif problem == "reference":
        data["rows"][0]["gold_eot_ms"] += 10
    elif problem == "mode":
        run = store.get("runs", "second-run")
        run["config"]["mode"] = "offline"
        store.update_run("second-run", "completed", config=run["config"])
    else:
        store.update_run("second-run", "interrupted")
    report_path.write_text(dumps(data))
    params = [("selection", "legacy-run:baseline-500ms"), ("selection", "second-run:baseline-500ms")]
    assert client.get("/api/comparisons/report", params=params).status_code == 400


def test_comparison_rejects_changed_audio_and_duplicate_selections(saved_run):
    client, store, folder = saved_run
    run = store.get("runs", "legacy-run")
    release = store.get("releases", run["release_id"])
    release["id"] = "changed-audio"
    release["records"][0]["sha256"] = "different-audio"
    with store.connect() as db:
        db.execute("INSERT INTO releases VALUES(?,?,?)", (release["id"], dumps(release), run["created_at"]))
    copy_run(store, folder, release_id=release["id"])
    params = [("selection", "legacy-run:baseline-500ms"), ("selection", "second-run:baseline-500ms")]
    assert client.get("/api/comparisons/report", params=params).status_code == 400
    assert client.get("/api/comparisons/report", params=[params[0], params[0]]).status_code == 400
    assert client.get("/api/comparisons/report", params={"selection": "bad-format"}).status_code == 400


def test_comparison_exports_include_provenance_window_and_figures(saved_run):
    client, store, folder = saved_run
    copy_run(store, folder)
    params = [("selection", "legacy-run:baseline-500ms"), ("selection", "second-run:scribe-v3-live")]
    svg = client.get("/api/comparisons/charts/timing", params=[*params, ("format", "svg")])
    assert svg.status_code == 200 and "1600 ms" in svg.text
    assert client.get("/api/comparisons/charts/unknown", params=params).status_code == 404
    response = client.get("/api/comparisons/download", params=params)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert json.loads(archive.read("comparison.json"))["timely_ms"] == 1600
        assert json.loads(archive.read("analysis.json"))["observation_count"] == 2
        assert "source_run_id" in archive.read("per_turn.csv").decode()
        assert "delta_mean_ms" in archive.read("summary.csv").decode()
        for name in CHARTS:
            assert archive.read(f"figures/{name}.png").startswith(b"\x89PNG")
            assert b"<svg" in archive.read(f"figures/{name}.svg")


def test_means_exclude_failures_and_keep_signed_and_early_statistics_separate():
    rows = [
        observation(commit=500),
        observation(commit=1400),
        observation(commit=2000),
        observation(commit=200, error="network"),
        observation(commit=None),
    ]
    summary = analyse(rows)["conditions"][0]
    assert summary["delta_n"] == 3
    assert summary["delta_mean_ms"] == 300
    assert summary["early_lead_mean_ms"] == 500
    assert summary["counts"] == {"early": 1, "timely": 2, "late": 0, "failure": 2}
