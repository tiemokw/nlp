import io
import json
import time
import uuid
from collections import Counter

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from app.main import create_app
from app.scenarios import cards
from app.store import Store
from eot_eval.config import ExperimentConfig
from eot_eval.metrics import aggregate, paired_latencies, score_turn
from eot_eval.replay import replay


def wav_bytes(rate=16000):
    samples = np.zeros(rate * 8, dtype=np.float32)
    samples[rate // 4 : rate] = 0.2 * np.sin(np.arange(rate - rate // 4) * 2 * np.pi * 220 / rate)
    output = io.BytesIO()
    sf.write(output, samples, rate, format="WAV", subtype="PCM_16")
    return output.getvalue()


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        yield client


def upload(client, ident=None, scenario="P01-K-F", data=None):
    return client.post(
        "/api/attempts",
        data={"attempt_id": ident or str(uuid.uuid4()), "scenario_id": scenario, "metadata": "{}"},
        files={"audio": ("take.wav", data or wav_bytes(), "audio/wav")},
    )


def annotation(**overrides):
    return {
        "gold_eot_sample": 16000,
        "holds": [],
        "transcript": "Test",
        "annotator": "A",
        "reviewer": "",
        "status": "annotated",
        "ambiguous_transition": False,
        "notes": "",
        **overrides,
    }


def test_balanced_scenarios():
    items = cards()
    assert len({c["id"] for c in items}) == 100
    assert set(Counter(c["participant_id"] for c in items).values()) == {20}
    assert set(Counter(c["content_type"] for c in items).values()) == {20}
    assert set(Counter(c["turn_pattern"] for c in items).values()) == {25}
    assert len({(c["participant_id"], c["content_type"], c["turn_pattern"]) for c in items}) == 100


def test_upload_idempotence_and_conflicting_content(client):
    ident = str(uuid.uuid4())
    first = upload(client, ident)
    assert first.status_code == 200
    assert upload(client, ident).json()["id"] == ident
    assert upload(client, ident, scenario="P01-E-F").status_code == 409
    assert len(client.get("/api/attempts").json()) == 1
    malformed = client.post(
        "/api/attempts",
        data={"attempt_id": str(uuid.uuid4()), "scenario_id": "P01-K-F"},
        files={"audio": ("bad.wav", b"not wave")},
    )
    assert malformed.status_code == 400


def test_resampling_preserves_duration(client):
    record = upload(client, data=wav_bytes(48000)).json()
    assert record["source_rate"] == 48000
    assert record["sample_rate"] == 16000
    assert record["samples"] == 128000
    assert client.get(f"/api/attempts/{record['id']}/audio").status_code == 200


def test_attempt_replacement_requires_reason(client):
    a, b = upload(client).json(), upload(client).json()
    assert client.post(f"/api/attempts/{a['id']}/select", json={}).status_code == 200
    assert client.post(f"/api/attempts/{b['id']}/select", json={}).status_code == 400
    assert client.post(f"/api/attempts/{b['id']}/select", json={"reason": "Störgeräusch"}).status_code == 200
    assert sum(x["selected"] for x in client.get("/api/attempts").json()) == 1


def test_annotation_tail_hold_and_review_validation(client):
    ident = upload(client).json()["id"]
    endpoint = f"/api/attempts/{ident}/annotation"
    assert client.post(endpoint, json=annotation(gold_eot_sample=48000)).status_code == 400
    assert (
        client.post(
            endpoint,
            json=annotation(
                holds=[{"start_sample": 100, "end_sample": 600}, {"start_sample": 500, "end_sample": 700}]
            ),
        ).status_code
        == 400
    )
    assert client.post(endpoint, json=annotation(status="reviewed", reviewer="a")).status_code == 400
    assert client.post(endpoint, json=annotation(status="reviewed", reviewer="B")).status_code == 200


def test_release_is_frozen_and_dev_excludes_test_speakers(client):
    a = upload(client).json()["id"]
    b = upload(client, scenario="P02-K-F").json()["id"]
    for ident in (a, b):
        client.post(f"/api/attempts/{ident}/select", json={})
        client.post(f"/api/attempts/{ident}/annotation", json=annotation())
    release = client.post("/api/releases", json={"kind": "development"}).json()
    assert len(release["records"]) == 1
    assert release["records"][0]["id"] == a
    client.post(f"/api/attempts/{a}/annotation", json=annotation(gold_eot_sample=20000))
    stored = client.get("/api/releases").json()[0]
    assert stored["records"][0]["annotation"]["gold_eot_sample"] == 16000
    assert client.post("/api/releases", json={"kind": "final"}).status_code == 400
    assert client.get(f"/api/releases/{release['id']}/download").content.startswith(b"PK")


def test_new_run_rejects_offline_smart_turn_and_split_controls(client):
    for config in ({"models": ["baseline"], "mode": "offline"}, {"models": ["smart_turn"]}, {"models": []}):
        result = client.post("/api/runs", json={"release_id": "unused", "config": config})
        assert result.status_code == 422
    result = client.post("/api/runs", json={"release_id": "unused", "split": "test"})
    assert result.status_code == 422
    assert client.get("/api/runs").json() == []


def test_cross_origin_writes_are_rejected(client):
    assert (
        client.post(
            "/api/releases", json={"kind": "development"}, headers={"Origin": "https://unrelated.example"}
        ).status_code
        == 403
    )
    assert client.get("/api/overview", headers={"Host": "unrelated.example"}).status_code == 403


class ScriptedVAD:
    def __init__(self, speech_frames):
        self.speech_frames = set(speech_frames)

    def reset(self):
        self.frame = 0

    def probability(self, frame):
        self.frame += 1
        return 1.0 if self.frame in self.speech_frames else 0.0


class FixtureModel:
    metadata = {"name": "Fixture"}

    def __init__(self, probability=1, delay=0):
        self.probability = probability
        self.delay = delay
        self.prefixes = []

    def score(self, audio):
        if len(audio) != 16000:  # ignore the deliberately separate warm-up
            self.prefixes.append(audio.copy())
        time.sleep(self.delay)
        return self.probability


def test_baseline_resets_and_first_commit_is_final():
    cfg = ExperimentConfig(models=["baseline"], mode="offline")
    # First pause is 160 ms, below timeout; next speech ends at 640 ms.
    result = replay(
        np.zeros(16000 * 2, np.float32),
        ScriptedVAD(list(range(1, 6)) + list(range(11, 21))),
        cfg,
        timeout_ms=300,
    )
    assert result["commit_ms"] == 960
    early = replay(
        np.zeros(16000 * 3, np.float32),
        ScriptedVAD(list(range(1, 6)) + list(range(50, 55))),
        cfg,
        timeout_ms=300,
    )
    assert early["commit_ms"] == 480
    assert len([e for e in early["events"] if e["event"] == "commit"]) == 1


def test_causal_prefixes_do_not_contain_future_audio():
    cfg = ExperimentConfig(livekit_version="v1-mini", mode="offline")
    audio = np.zeros(32000, np.float32)
    audio[16000:] = 0.95
    model = FixtureModel()
    result = replay(audio, ScriptedVAD(range(1, 6)), cfg, model=model)
    assert result["trigger"] == "semantic"
    assert model.prefixes
    assert all(len(p) <= 16000 and np.max(p) == 0 for p in model.prefixes)


def test_slow_score_is_stale_after_speech_resumes():
    cfg = ExperimentConfig(mode="realtime", min_silence_ms=250, inference_interval_ms=100)
    model = FixtureModel(delay=0.13)
    result = replay(np.zeros(16000, np.float32), ScriptedVAD([1, 2, 12, 13]), cfg, model=model)
    assert any(e["event"] == "score" and e["stale"] for e in result["events"])
    assert result["commit_ms"] is None or result["commit_ms"] >= 650


def test_fallback_and_missing_are_distinct():
    cfg = ExperimentConfig(livekit_version="v1-mini", mode="offline", max_silence_ms=1500)
    result = replay(np.zeros(32000, np.float32), ScriptedVAD([1, 2]), cfg, model=FixtureModel(probability=0))
    assert result["trigger"] == "fallback_timeout"
    missing = replay(np.zeros(32000, np.float32), ScriptedVAD([]), cfg, timeout_ms=500)
    assert missing["trigger"] == "missing" and missing["commit_ms"] is None


def test_metrics_do_not_reward_early_commits_or_hide_missing():
    record = {
        "id": "a",
        "scenario_id": "s",
        "participant_id": "P01",
        "content_type": "K",
        "turn_pattern": "U",
        "sample_rate": 16000,
        "annotation": {"gold_eot_sample": 16000, "ambiguous_transition": False},
    }

    def item(ident, commit, trigger):
        data = {
            "commit_ms": commit,
            "trigger": trigger,
            "mode": "offline",
            "error": None,
            "inference_ms": [],
            "vad_total_ms": 1,
            "skipped_queries": 0,
        }
        return {"condition": "livekit", **score_turn({**record, "id": ident}, data)}

    rows = [item("a", 500, "semantic"), item("b", 4000, "fallback_timeout"), item("c", None, "missing")]
    summary = aggregate(rows)[0]
    assert summary["n"] == 3 and summary["premature_count"] == 1
    assert summary["latency_n"] == 1 and summary["latency_median_ms"] == 3000
    assert summary["failures"] == 1 and summary["fallback_count"] == 1
    assert paired_latencies(rows) == []


def test_runner_exports_report_and_raw_events(tmp_path, monkeypatch):
    from eot_eval import runner

    store = Store(tmp_path)
    ident = str(uuid.uuid4())
    store.upload(ident, "P01-K-F", wav_bytes(), {})
    store.select(ident)
    store.annotate(ident, annotation())
    release = store.release("development")
    with store.connect() as db:
        payload = {
            "id": "run-test",
            "release_id": release["id"],
            "split": "dev",
            "config": ExperimentConfig(
                models=["baseline"], mode="offline", baseline_timeouts_ms=[500]
            ).model_dump(),
        }
        db.execute("INSERT INTO runs VALUES(?,?,?,?)", ("run-test", "queued", json.dumps(payload), "now"))

    class VAD(ScriptedVAD):
        metadata = {"name": "test fixture"}

        def __init__(self):
            super().__init__(range(1, 32))

    monkeypatch.setattr(runner, "Silero", VAD)
    runner.run(tmp_path, "run-test")
    assert store.get("runs", "run-test")["status"] == "completed"
    report = json.loads((tmp_path / "runs/run-test/report.json").read_text())
    assert report["summary"][0]["n"] == 1
    assert (tmp_path / "runs/run-test/tradeoff.png").is_file()
    assert (tmp_path / "runs/run-test/events.jsonl").read_text()
    # Results must show the transcript from the evaluated snapshot, not a later edit.
    store.annotate(ident, annotation(transcript="Spätere Änderung"))
    with TestClient(create_app(tmp_path)) as client:
        result = client.get("/api/runs/run-test/report").json()
        assert result["clips"][0]["annotation"]["transcript"] == "Test"
        defaults = client.get("/api/experiment-defaults").json()
        assert defaults["livekit_threshold"] is None
        assert defaults["max_silence_ms"] == 5000
    with pytest.raises(ValueError, match="neue"):
        runner.run(tmp_path, "run-test")


def test_manual_configuration_is_not_a_run_input(client):
    result = client.post("/api/runs", json={"release_id": "unused", "configuration_id": "legacy"})
    assert result.status_code == 422
    assert not client.get("/api/runs").json()
