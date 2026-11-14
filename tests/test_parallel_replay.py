"""Parallel audio replays must have independent state and a hard concurrency bound."""

import threading

import numpy as np
import pytest
import soundfile as sf

from app.audio import digest
from app.main import EvaluationConfig
from eot_eval import runner
from eot_eval.config import ExperimentConfig


def records(root, count):
    path = root / "clip.wav"
    sf.write(path, np.zeros(16000), 16000)
    return [
        {"id": str(i), "audio_path": path.name, "sha256": digest(path.read_bytes())} for i in range(count)
    ]


def test_six_replays_overlap_with_private_vad_and_model_state(tmp_path, monkeypatch):
    created = []
    active = 0
    maximum = 0
    lock = threading.Lock()
    barrier = threading.Barrier(6, timeout=10)

    class VAD:
        def __init__(self):
            self.owner = threading.get_ident()
            self.metadata = {"name": "private VAD", "owner": self.owner}

    class Model:
        def __init__(self):
            self.owner = threading.get_ident()
            self.metadata = {"name": "private model", "owner": self.owner}
            self.closed = False
            created.append(self)

        def close(self):
            self.closed = True

    def replay(audio, vad, config, model=None, **kwargs):
        nonlocal active, maximum
        assert vad.owner == model.owner == threading.get_ident()
        assert config.mode == "realtime"
        with lock:
            active += 1
            maximum = max(maximum, active)
        barrier.wait()
        with lock:
            active -= 1
        return {"events": [{"owner": model.owner}]}

    monkeypatch.setattr(runner, "Silero", VAD)
    monkeypatch.setattr(runner, "load", lambda *args, **kwargs: Model())
    monkeypatch.setattr(runner, "replay", replay)
    cfg = ExperimentConfig(models=["livekit"], parallelism=6)
    result = list(runner.evaluate_condition(tmp_path, records(tmp_path, 12), cfg, "livekit", None))
    assert len(result) == 12 and {r[0] for r in result} == set(range(12))
    assert maximum == len(created) == 6
    assert len({m.owner for m in created}) == 6 and all(m.closed for m in created)
    for _, _, replay_result, vad_meta, model_meta in result:
        assert replay_result["events"][0]["owner"] == vad_meta["owner"] == model_meta["owner"]


def test_models_are_closed_after_a_parallel_task_fails(tmp_path, monkeypatch):
    created = []

    class Model:
        metadata = {"name": "fixture"}

        def __init__(self):
            self.closed = False
            created.append(self)

        def close(self):
            self.closed = True

    class VAD:
        metadata = {"name": "fixture"}

    def fail(*args, **kwargs):
        raise ValueError("explicit replay failure")

    monkeypatch.setattr(runner, "Silero", VAD)
    monkeypatch.setattr(runner, "load", lambda *args, **kwargs: Model())
    monkeypatch.setattr(runner, "replay", fail)
    cfg = ExperimentConfig(models=["livekit"], parallelism=6)
    with pytest.raises(ValueError, match="explicit replay failure"):
        list(runner.evaluate_condition(tmp_path, records(tmp_path, 12), cfg, "livekit", None))
    assert 1 <= len(created) <= 6 and all(m.closed for m in created)


def test_cancelled_work_does_not_open_more_models(tmp_path, monkeypatch):
    def unexpected():
        raise AssertionError("Cancelled audio must not start a session")

    monkeypatch.setattr(runner, "Silero", unexpected)
    cfg = ExperimentConfig(models=["baseline"], parallelism=6)
    assert (
        list(
            runner.evaluate_condition(tmp_path, records(tmp_path, 12), cfg, None, 500, cancelled=lambda: True)
        )
        == []
    )


def test_new_evaluations_default_to_six_and_historical_configs_stay_sequential():
    assert EvaluationConfig().parallelism == 6
    assert ExperimentConfig().parallelism == 1
    for value in (0, 7):
        with pytest.raises(ValueError):
            EvaluationConfig(parallelism=value)


def test_cancellation_stops_waiting_audio_before_it_starts(tmp_path, monkeypatch):
    cancelled = threading.Event()
    barrier = threading.Barrier(6, timeout=10)
    calls = []

    class VAD:
        metadata = {"name": "fixture"}

    def replay(*args, **kwargs):
        calls.append(threading.get_ident())
        barrier.wait()
        cancelled.set()
        return {"events": []}

    monkeypatch.setattr(runner, "Silero", VAD)
    monkeypatch.setattr(runner, "replay", replay)
    cfg = ExperimentConfig(models=["baseline"], parallelism=6)
    result = list(
        runner.evaluate_condition(tmp_path, records(tmp_path, 18), cfg, None, 500, cancelled=cancelled.is_set)
    )
    assert len(calls) == len(result) == 6
