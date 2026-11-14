"""Regression tests for starting the complete study without manual configuration gates."""

import json

import pytest
from fastapi.testclient import TestClient
from test_study import add_humans, confirm_synthetic, generate_study

from app.main import create_app
from app.store import Store


@pytest.fixture
def evaluation(tmp_path, monkeypatch):
    from app import main
    from eot_eval import runner

    store = Store(tmp_path)
    synthetic, _ = generate_study(store)
    add_humans(store)
    confirm_synthetic(store, synthetic)
    release = store.release_study(synthetic["id"])
    processes = []

    class Process:
        def __init__(self, command, **kwargs):
            self.command = command
            self.stopped = False
            processes.append(self)

        def poll(self):
            return 0 if self.stopped else None

        def terminate(self):
            self.stopped = True

        def wait(self, **kwargs):
            return 0

    monkeypatch.setattr(main.subprocess, "Popen", Process)
    monkeypatch.setattr(
        main,
        "inventory",
        lambda *args: [{"id": name, "ready": True} for name in ("baseline", "livekit", "scribe")],
    )
    monkeypatch.setattr(main, "validate_livekit_credentials", lambda: None)
    monkeypatch.setattr(main, "ElevenLabs", lambda: object())
    monkeypatch.setattr(main, "fingerprints", lambda *args: {"fixture": "v1"})
    monkeypatch.setattr(runner, "fingerprints", lambda *args: {"fixture": "v1"})
    monkeypatch.setattr(runner.platform, "platform", lambda: "explicit test platform")
    with TestClient(create_app(tmp_path)) as client:
        yield client, store, release, synthetic, processes


def test_study_starts_with_current_settings_and_no_manual_freeze(evaluation):
    client, store, release, _, processes = evaluation
    response = client.post(
        "/api/runs",
        json={
            "release_id": release["id"],
            "name": "Run 01",
            "config": {"models": ["baseline", "livekit", "scribe"], "baseline_timeouts_ms": [1500]},
        },
    )
    assert response.status_code == 200, response.text
    job = response.json()
    assert job["status"] == "queued" and job["record_count"] == 50
    assert job["name"] == "Run 01"
    assert job["config"]["mode"] == "realtime"
    assert job["config"]["baseline_timeouts_ms"] == [1500]
    assert "split" not in job and "configuration_id" not in job
    assert "smart_turn_threshold" not in job["config"]
    assert job["model_fingerprints"] == {"fixture": "v1"}
    assert not store.listing("configurations")
    assert len(processes) == 1 and job["id"] in processes[0].command


def test_worker_evaluates_all_50_samples_with_all_three_models(evaluation, monkeypatch):
    from eot_eval import runner

    client, store, release, _, processes = evaluation
    calls = []

    class VAD:
        metadata = {"name": "explicit test VAD"}

    class Model:
        def __init__(self, name):
            self.metadata = {"name": name}

        def close(self):
            pass

    def replay(audio, vad, config, model=None, timeout_ms=None, sink=None):
        calls.append((config.mode, model.metadata["name"] if model else "baseline"))
        return {
            "commit_ms": 1000,
            "trigger": "timeout",
            "mode": config.mode,
            "error": None,
            "inference_ms": [],
            "vad_total_ms": 0,
            "skipped_queries": 0,
        }

    monkeypatch.setattr(runner, "Silero", VAD)
    monkeypatch.setattr(runner, "load", lambda name, *args, **kwargs: Model(name))
    monkeypatch.setattr(runner, "replay", replay)
    monkeypatch.setattr(runner, "plots", lambda *args: None)
    response = client.post(
        "/api/runs",
        json={
            "release_id": release["id"],
            "config": {
                "models": ["baseline", "livekit", "scribe"],
                "baseline_timeouts_ms": [1500],
            },
        },
    )
    assert response.status_code == 200, response.text
    job = response.json()
    runner.run(store.root, job["id"])
    processes[0].stopped = True
    completed = store.get("runs", job["id"])
    assert completed["status"] == "completed", completed
    report = client.get(f"/api/runs/{job['id']}/report").json()
    assert len(report["clips"]) == 50
    assert len(report["report"]["rows"]) == len(calls) == 150
    assert {mode for mode, _ in calls} == {"realtime"}
    assert {name for _, name in calls} == {"baseline", "livekit", "scribe"}
    assert len({r["id"] for r in report["report"]["rows"]}) == 50
    assert {r["source"] for r in report["report"]["rows"]} == {"human", "synthetic"}
    manifest = json.loads((store.root / "runs" / job["id"] / "manifest.json").read_text())
    assert manifest["config"] == job["config"]
    assert manifest["model_fingerprints"] == job["model_fingerprints"]


def test_worker_detects_model_change_after_automatic_snapshot(evaluation, monkeypatch):
    from eot_eval import runner

    client, store, release, _, processes = evaluation
    response = client.post(
        "/api/runs", json={"release_id": release["id"], "config": {"models": ["baseline"]}}
    )
    assert response.status_code == 200, response.text
    job = response.json()
    monkeypatch.setattr(runner, "fingerprints", lambda *args: {"fixture": "v2"})
    runner.run(store.root, job["id"])
    processes[0].stopped = True
    result = store.get("runs", job["id"])
    assert result["status"] == "failed" and "verändert" in result["error"]


def test_failed_worker_launch_does_not_block_retry(evaluation, monkeypatch):
    from app import main

    client, store, release, _, _ = evaluation
    process_factory = main.subprocess.Popen

    def fail(*args, **kwargs):
        raise OSError("explicit test failure")

    monkeypatch.setattr(main.subprocess, "Popen", fail)
    body = {"release_id": release["id"], "config": {"models": ["baseline"]}}
    response = client.post("/api/runs", json=body)
    assert response.status_code == 400
    assert store.listing("runs")[0]["status"] == "failed"
    monkeypatch.setattr(main.subprocess, "Popen", process_factory)
    assert client.post("/api/runs", json=body).status_code == 200


def test_unreviewed_synthetic_study_cannot_start(evaluation):
    client, store, _, synthetic, processes = evaluation
    response = client.post(
        "/api/runs", json={"release_id": synthetic["id"], "config": {"models": ["baseline"]}}
    )
    assert response.status_code == 400 and "Referenzenden" in response.json()["detail"]
    assert not processes and not store.listing("runs")
