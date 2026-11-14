import asyncio
import base64
import io
import json
import time
from types import SimpleNamespace

import numpy as np
import pytest

from eot_eval.config import ExperimentConfig
from eot_eval.metrics import aggregate, score_turn
from eot_eval.models import fingerprints
from eot_eval.replay import replay
from eot_eval.scribe import Scribe


def test_scribe_is_explicit_opt_in_and_realtime_only():
    assert "scribe" not in ExperimentConfig().models
    assert ExperimentConfig(models=["scribe"]).scribe_threshold == 0.9
    assert len(ExperimentConfig(models=["baseline", "livekit", "smart_turn", "scribe"]).models) == 4
    with pytest.raises(ValueError, match="Echtzeit"):
        ExperimentConfig(models=["scribe"], mode="offline")


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    import aiohttp

    from eot_eval import scribe

    monkeypatch.setattr(
        scribe,
        "ElevenLabs",
        lambda: SimpleNamespace(key="test-secret", base_url="https://api.eu.residency.elevenlabs.io"),
    )
    opened = []

    class Socket:
        def __init__(self):
            self.incoming = asyncio.Queue()
            self.sent = []
            self.closed = False
            self.model = "scribe_v3_live"

        async def receive_json(self, **kwargs):
            return {
                "message_type": "session_started",
                "session_id": "fake-session",
                "config": {"model_id": self.model},
            }

        async def send_json(self, data):
            self.sent.append(data)

        async def close(self):
            self.closed = True

        def __aiter__(self):
            return self

        async def __anext__(self):
            data = await self.incoming.get()
            return SimpleNamespace(type=aiohttp.WSMsgType.TEXT, data=json.dumps(data))

    class Session:
        def __init__(self):
            self.closed = False

        async def ws_connect(self, url, **kwargs):
            ws = Socket()
            opened.append((self, ws, url, kwargs))
            return ws

        async def close(self):
            self.closed = True

    monkeypatch.setattr(aiohttp, "ClientSession", Session)
    model = Scribe(tmp_path)
    model.reset()
    yield model, opened
    model.close()
    assert all(session.closed and ws.closed for session, ws, _, _ in opened)


def test_adapter_sends_only_released_audio_to_eu_without_auto_commits(adapter):
    model, opened = adapter
    _, ws, url, kwargs = opened[0]
    assert url.startswith("wss://api.eu.residency.elevenlabs.io/")
    assert "model_id=scribe_v3_live" in url and "commit_strategy=manual" in url
    assert "test-secret" not in url and kwargs["headers"]["xi-api-key"] == "test-secret"
    model.warmup()
    assert ws.sent == []
    frame = np.full(512, 0.125, dtype=np.float32)
    for _ in range(4):
        model.feed(frame)

    async def settle():
        for _ in range(50):
            if ws.sent:
                return
            await asyncio.sleep(0.001)

    model._call(settle())
    assert len(ws.sent) == 1
    message = ws.sent[0]
    assert message["commit"] is False
    assert len(base64.b64decode(message["audio_base_64"])) == 4096
    assert model.submitted_samples == 2048
    assert "test-secret" not in json.dumps(model.metadata)


def test_streamed_probabilities_and_session_reset(adapter):
    model, opened = adapter
    _, ws, _, _ = opened[0]

    async def deliver():
        await ws.incoming.put(
            {"message_type": "partial_transcript", "text": "Meine Nummer ist", "turn_probability": 0.12}
        )
        await asyncio.sleep(0.005)

    model._call(deliver())
    model.validate_observation()
    result = model.poll()
    assert result[0]["score"] == 0.12 and result[0]["text"] == "Meine Nummer ist"
    assert result[0]["submitted_samples_upper_bound"] == 0
    model.reset()
    assert ws.closed and model.poll() == []
    with pytest.raises(RuntimeError, match="turn_probability"):
        model.validate_observation()


@pytest.mark.parametrize(
    "message",
    [
        {"message_type": "partial_transcript", "turn_probability": 1.5},
        {"message_type": "auth_error", "error": "test-secret"},
    ],
)
def test_provider_errors_do_not_become_model_decisions(adapter, message):
    model, opened = adapter

    async def deliver():
        await opened[0][1].incoming.put(message)
        await asyncio.sleep(0.005)

    model._call(deliver())
    with pytest.raises(RuntimeError) as error:
        model.poll()
    assert "test-secret" not in str(error.value)


@pytest.mark.parametrize("stale", [False, True])
def test_replay_uses_available_stream_scores_without_future_audio(monkeypatch, stale):
    from eot_eval import replay as module

    clock = {"time": 100.0}
    monkeypatch.setattr(module.time, "perf_counter", lambda: clock["time"])
    monkeypatch.setattr(module.time, "sleep", lambda delay: clock.update(time=clock["time"] + delay))

    class VAD:
        def reset(self):
            self.frames = 0

        def probability(self, frame):
            self.frames += 1
            return float(self.frames <= 5)

    class Model:
        metadata = {"name": "Scribe test", "inference_measure": "streaming_service"}

        def warmup(self):
            pass

        def reset(self):
            self.fed = 0

        def feed(self, frame):
            assert np.max(frame) == 0  # later audio contains a sentinel; must never arrive
            self.fed += len(frame)

        def poll(self):
            if self.fed != 16 * 512:
                return []
            return [
                {
                    "score": 0.95,
                    "text": "Fertig",
                    "received_at": clock["time"] - (1 if stale else 0),
                    "provider_event": "partial_transcript",
                    "submitted_samples_upper_bound": self.fed,
                }
            ]

        def validate_observation(self):
            pass

    audio = np.zeros(32000, np.float32)
    audio[30000:] = 0.9
    config = ExperimentConfig(models=["scribe"], max_silence_ms=1500)
    result = replay(audio, VAD(), config, model=Model())
    assert result["trigger"] == ("fallback_timeout" if stale else "semantic")
    assert result["inference_ms"] == []
    event = next(e for e in result["events"] if e["event"] == "stream_score")
    assert event["stale"] == stale
    record = {
        "id": "a",
        "scenario_id": "a",
        "participant_id": "a",
        "content_type": "K",
        "turn_pattern": "U",
        "sample_rate": 16000,
        "annotation": {"gold_eot_sample": 100, "ambiguous_transition": False},
    }
    row = {"condition": "scribe-v3-live", **score_turn(record, result)}
    assert row["inference_total_ms"] is None
    assert aggregate([row])[0]["inference_per_turn_median_ms"] is None


def test_scribe_fingerprint_contains_endpoint_but_no_credentials(tmp_path, monkeypatch):
    from eot_eval import models

    monkeypatch.setattr(models, "api_base_url", lambda: "https://api.eu.residency.elevenlabs.io")
    fp = fingerprints(tmp_path, ["scribe"])
    assert fp["scribe"]["model"] == "scribe_v3_live"
    assert fp["scribe"]["commit_strategy"] == "manual"
    assert "api_key" not in json.dumps(fp)


def test_segment_commit_is_not_a_semantic_turn_signal(adapter):
    model, opened = adapter

    async def deliver():
        await opened[0][1].incoming.put({"message_type": "committed_transcript", "text": "Teilsegment"})
        await asyncio.sleep(0.005)

    model._call(deliver())
    assert model.poll()[0]["score"] is None
    with pytest.raises(RuntimeError, match="turn_probability"):
        model.validate_observation()


def test_scribe_runner_exports_streaming_results(tmp_path, monkeypatch):
    import soundfile as sf

    from app.store import Store
    from eot_eval import runner

    store = Store(tmp_path)
    wav = io.BytesIO()
    sf.write(wav, np.zeros(8 * 16000, np.float32), 16000, format="WAV")
    store.upload("fefcd3b2-7d85-43dd-bfd0-482a8094b80a", "P01-K-F", wav.getvalue(), {})
    store.select("fefcd3b2-7d85-43dd-bfd0-482a8094b80a")
    store.annotate(
        "fefcd3b2-7d85-43dd-bfd0-482a8094b80a",
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
    config = ExperimentConfig(models=["scribe"], max_silence_ms=1500)
    job = {"id": "scribe-test", "release_id": release["id"], "split": "dev", "config": config.model_dump()}
    with store.connect() as db:
        db.execute("INSERT INTO runs VALUES(?,?,?,?)", (job["id"], "queued", json.dumps(job), "now"))

    class VAD:
        metadata = {"name": "fixture VAD"}

        def reset(self):
            self.frames = 0

        def probability(self, frame):
            self.frames += 1
            return float(self.frames <= 5)

    class Model:
        metadata = {"name": "Scribe fixture", "inference_measure": "streaming_service"}
        closed = False

        def warmup(self):
            pass

        def reset(self):
            self.fed = 0

        def feed(self, frame):
            self.fed += len(frame)

        def poll(self):
            return [
                {
                    "score": 0.95,
                    "text": "Test",
                    "received_at": time.perf_counter(),
                    "provider_event": "partial_transcript",
                    "submitted_samples_upper_bound": self.fed,
                }
            ]

        def validate_observation(self):
            pass

        def close(self):
            self.closed = True

    model = Model()
    monkeypatch.setattr(runner, "Silero", VAD)
    monkeypatch.setattr(runner, "load", lambda *args, **kwargs: model)
    runner.run(tmp_path, job["id"])
    assert store.get("runs", job["id"])["status"] == "completed"
    folder = tmp_path / "runs" / job["id"]
    report = json.loads((folder / "report.json").read_text())
    assert report["summary"][0]["condition"] == "scribe-v3-live"
    assert report["summary"][0]["inference_per_turn_median_ms"] is None
    assert any(
        json.loads(line)["event"] == "stream_score"
        for line in (folder / "events.jsonl").read_text().splitlines()
    )
    assert model.closed
