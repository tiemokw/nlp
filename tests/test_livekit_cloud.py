import asyncio
import json
from types import SimpleNamespace

import numpy as np
import pytest

from eot_eval.config import ExperimentConfig
from eot_eval.models import LiveKit, fingerprints, inventory
from eot_eval.replay import replay


def test_cloud_is_default_and_requires_realtime():
    assert ExperimentConfig().livekit_version == "v1"
    with pytest.raises(ValueError, match="Echtzeit"):
        ExperimentConfig(models=["livekit"], mode="offline")
    assert ExperimentConfig(models=["livekit"], livekit_version="v1-mini", mode="offline")
    assert ExperimentConfig(models=["baseline"], mode="offline")


def test_cloud_readiness_is_separate_from_local_readiness(tmp_path, monkeypatch):
    from eot_eval import models

    monkeypatch.setattr(models, "livekit_cloud_configured", lambda: False)
    cloud = next(m for m in inventory(tmp_path, "v1") if m["id"] == "livekit")
    local = next(m for m in inventory(tmp_path, "v1-mini") if m["id"] == "livekit")
    assert not cloud["ready"]
    assert cloud["variant"] == "v1"
    assert local["ready"] == local["local_ready"]


def test_cloud_fingerprint_contains_no_credentials(tmp_path, monkeypatch):
    from eot_eval import models

    monkeypatch.setattr(
        models,
        "livekit_credentials",
        lambda: {
            "api_key": "unique-test-key",
            "api_secret": "unique-test-secret",
            "base_url": "https://agent-gateway.livekit.cloud/v1",
        },
    )
    fp = fingerprints(tmp_path, ["livekit"], "v1")
    assert fp["livekit"]["execution"] == "cloud"
    assert "native_sha256" not in fp["livekit"]
    assert "unique-test" not in json.dumps(fp)


class FakeStream:
    def __init__(self):
        self._transport = SimpleNamespace(_ws=object())
        self.model = "turn-detector-v1"
        self.is_fallback = False
        self.is_degraded = False
        self.probability = 0.8
        self.duration = 0.001
        self.predictions = 0
        self.frames = []
        self.closed = False

    def flush(self):
        self.frames.clear()

    def push_audio(self, frame):
        self.frames.append(frame)

    def predict(self):
        self.predictions += 1
        future = asyncio.get_running_loop().create_future()
        future.set_result(
            SimpleNamespace(end_of_turn_probability=self.probability, inference_duration=self.duration)
        )
        return future

    async def aclose(self):
        self.closed = True

    async def unlikely_threshold(self, language):
        return 0.245


@pytest.fixture
def cloud_adapter(tmp_path, monkeypatch):
    from livekit.agents import inference

    from eot_eval import models

    stream = FakeStream()
    captured = {}

    class Detector:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def stream(self, **kwargs):
            return stream

    monkeypatch.setattr(inference, "TurnDetector", Detector)
    monkeypatch.setattr(
        models,
        "validate_livekit_credentials",
        lambda: {
            "api_key": "dummy-test-key",
            "api_secret": "dummy-test-secret",
            "base_url": "https://agent-gateway.livekit.cloud/v1",
        },
    )
    model = LiveKit(tmp_path, variant="v1")
    yield model, stream, captured
    model.close()
    assert stream.closed


def test_cloud_adapter_pins_v1_and_disables_fallback(cloud_adapter):
    model, stream, captured = cloud_adapter
    assert captured["version"] == "v1"
    assert captured["local_fallback"] is False
    assert captured["http_session"] is not None
    model.warmup()
    assert stream.predictions == 0  # no extra billable cloud warm-up requests
    assert model.score(np.zeros(16000, np.float32)) == 0.8
    assert model.call_metrics["sdk_server_e2e_ms"] == 1
    assert model.call_metrics["eot_threshold"] == 0.245
    assert model.metadata["inference_measure"] == "service_roundtrip"
    assert model.metadata["window_samples"] is None
    assert "dummy-test" not in json.dumps(model.metadata)


@pytest.mark.parametrize("failure", ["fallback", "wrong_model", "degraded", "default_response"])
def test_cloud_never_accepts_fallback_or_sdk_default(cloud_adapter, failure):
    model, stream, _ = cloud_adapter
    if failure == "fallback":
        stream.is_fallback = True
    elif failure == "wrong_model":
        stream.model = "turn-detector-v1-mini"
    elif failure == "degraded":
        stream.is_degraded = True
    else:
        stream.probability = 1.0
        stream.duration = None
    with pytest.raises(RuntimeError, match="v1-Antwort"):
        model.score(np.zeros(16000, np.float32))


def test_streaming_adapter_only_receives_released_frames():
    class VAD:
        def reset(self):
            self.frames = 0

        def probability(self, frame):
            self.frames += 1
            return 1.0 if self.frames <= 5 else 0.0

    class Model:
        metadata = {"name": "LiveKit test stream"}

        def warmup(self):
            pass

        def reset(self):
            self.frames = []

        def feed(self, frame):
            self.frames.append(frame.copy())

        def score(self, prefix):
            assert np.array_equal(np.concatenate(self.frames), prefix)
            assert len(prefix) < 16000
            return 1.0

    audio = np.zeros(32000, np.float32)
    audio[16000:] = 0.9
    result = replay(
        audio,
        VAD(),
        ExperimentConfig(livekit_version="v1-mini", livekit_threshold=0.5, mode="offline"),
        model=Model(),
    )
    assert result["trigger"] == "semantic"


@pytest.mark.parametrize("override,expected", [(None, "semantic"), (0.9, "fallback_timeout")])
def test_replay_uses_manufacturer_threshold_or_explicit_override(override, expected):
    class VAD:
        def reset(self):
            self.frames = 0

        def probability(self, frame):
            self.frames += 1
            return float(self.frames < 5)

    class Model:
        metadata = {"name": "LiveKit calibrated fixture"}
        call_metrics = {"eot_threshold": 0.245}

        def score(self, audio):
            return 0.3

    config = ExperimentConfig(
        livekit_version="v1-mini", livekit_threshold=override, mode="offline", max_silence_ms=1500
    )
    result = replay(np.zeros(32000, np.float32), VAD(), config, model=Model())
    assert result["trigger"] == expected
    score = next(event for event in result["events"] if event["event"] == "score")
    assert score["eot_threshold"] == (0.245 if override is None else override)
