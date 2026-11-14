import base64
import io
import json
import re
import uuid
import zipfile
from collections import Counter
from urllib.error import HTTPError

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import Store, dumps, now
from app.synthesis import PROFILES, SynthesisConfig, character_spans, compose, generate, preview


class FakeElevenLabs:
    """Explicit test double. Does not access the network or synthesize human speech."""

    def __init__(self, silent=False):
        self.calls = 0
        self.silent = silent

    def speech(self, voice, body):
        self.calls += 1
        segments = re.split(r"\s*<break[^>]+>\s*", body["text"])
        samples = [np.zeros(1600, np.int16)]
        offset = 1600
        chars, starts, ends = [], [], []
        for position, segment in enumerate(segments):
            if position:
                chars.append(" ")
                starts.append(offset / 16000)
                samples.append(np.zeros(9600, np.int16))
                offset += 9600
                ends.append(offset / 16000)
            for char in segment:
                chars.append(char)
                starts.append(offset / 16000)
                samples.append(np.full(160, 0 if self.silent or not char.isalnum() else 5000, np.int16))
                offset += 160
                ends.append(offset / 16000)
        samples.append(np.zeros(2000, np.int16))
        return {
            "audio_base64": base64.b64encode(np.concatenate(samples).tobytes()).decode(),
            "normalized_alignment": {
                "characters": chars,
                "character_start_times_seconds": starts,
                "character_end_times_seconds": ends,
            },
        }, {"request_id": "mock-test", "character_cost": "0"}


def config(size="pilot"):
    return SynthesisConfig(
        size=size,
        voices=[{"id": f"voice0000{i}", "name": f"Mock {i}"} for i in range(1, 6 if size == "full" else 2)],
    )


def queued(store, cfg):
    ident = uuid.uuid4().hex
    payload = {
        "id": ident,
        "config": cfg.model_dump(),
        "created_at": now(),
        "progress": 0,
        "total": preview(cfg)["files"],
    }
    with store.connect() as db:
        db.execute("INSERT INTO syntheses VALUES(?,?,?,?)", (ident, "queued", dumps(payload), now()))
    return ident


def test_preview_is_free_and_counts_independent_bases():
    pilot = preview(config())
    full = preview(config("full"))
    assert (pilot["files"], pilot["base_generations"]) == (10, 5)
    assert (full["files"], full["base_generations"]) == (100, 25)
    with pytest.raises(ValueError):
        SynthesisConfig(size="full", voices=[{"id": "voice00001"}])
    with pytest.raises(ValueError):
        SynthesisConfig(size="full", voices=[{"id": "voice00001"}] * 5)


def test_invalid_header_key_is_never_reflected_in_error(monkeypatch):
    from app import synthesis

    monkeypatch.setattr(synthesis, "api_key", lambda: "very-secret\ninvalid")
    with pytest.raises(ValueError) as error:
        synthesis.ElevenLabs()
    assert "very-secret" not in str(error.value)


def test_eu_endpoint_routes_voice_and_tts_requests(monkeypatch):
    from app import synthesis

    monkeypatch.setattr(synthesis, "api_key", lambda: "test-secret")
    monkeypatch.setattr(
        synthesis, "local_setting", lambda *args, **kw: "https://api.eu.residency.elevenlabs.io/"
    )
    requests = []

    class Response(io.StringIO):
        headers = {}

    def open_request(request, **kwargs):
        requests.append(request)
        return Response('{"voices": []}')

    monkeypatch.setattr(synthesis, "urlopen", open_request)
    client = synthesis.ElevenLabs()
    client.voices()
    client.speech("voice00001", {"text": "Hallo"})
    assert all(r.full_url.startswith("https://api.eu.residency.elevenlabs.io/") for r in requests)
    assert "/v2/voices?" in requests[0].full_url
    assert "/v1/text-to-speech/voice00001/with-timestamps?" in requests[1].full_url
    assert requests[1].get_header("Xi-api-key") == "test-secret"


def test_endpoint_validation_and_global_default(monkeypatch):
    from app import synthesis

    monkeypatch.setattr(synthesis, "local_setting", lambda *args, **kw: kw["default"])
    assert synthesis.api_base_url() == "https://api.elevenlabs.io"
    for invalid in (
        "http://api.eu.residency.elevenlabs.io",
        "https://example.org",
        "https://api.elevenlabs.io/v1",
    ):
        monkeypatch.setattr(synthesis, "local_setting", lambda *args, **kw: invalid)
        with pytest.raises(ValueError, match="offizieller"):
            synthesis.api_base_url()


def test_401_names_region_without_reflecting_provider_body(monkeypatch):
    from app import synthesis

    monkeypatch.setattr(synthesis, "api_key", lambda: "test-secret")
    monkeypatch.setattr(synthesis, "api_base_url", lambda: "https://api.eu.residency.elevenlabs.io")

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, io.BytesIO(b"test-secret"))

    monkeypatch.setattr(synthesis, "urlopen", fail)
    with pytest.raises(ValueError) as error:
        synthesis.ElevenLabs().voices()
    assert "EU-Endpunkt" in str(error.value)
    assert "api.eu.residency.elevenlabs.io" in str(error.value)
    assert "test-secret" not in str(error.value)


def test_region_changes_do_not_reuse_other_environments_cache(tmp_path):
    from app.synthesis import TEMPLATES, cached_speech

    fake = FakeElevenLabs()
    cfg = config()
    first = cached_speech(tmp_path, cfg.voices[0], TEMPLATES[0], cfg, fake)
    fake.base_url = "https://api.eu.residency.elevenlabs.io"
    eu = cached_speech(tmp_path, cfg.voices[0], TEMPLATES[0], cfg, fake)
    assert first[2] != eu[2]
    assert fake.calls == 2
    assert eu[3]["api_base_url"] == fake.base_url
    cached_speech(tmp_path, cfg.voices[0], TEMPLATES[0], cfg, fake)
    assert fake.calls == 2


def test_compose_replaces_only_silence_and_maps_reference():
    fake = FakeElevenLabs()
    segments = ["Meine Nummer ist", "eins zwei", "drei vier."]
    data, _ = fake.speech("voice00001", {"text": ' <break time="0.6s" /> '.join(segments)})
    audio = np.frombuffer(base64.b64decode(data["audio_base64"]), dtype=np.int16).astype(np.float32) / 32768
    alignment = data["normalized_alignment"]
    original_spans = character_spans(alignment, segments, len(audio))
    for profile in PROFILES:
        result, gold, holds, gaps = compose(audio, alignment, segments, profile["pauses_ms"])
        assert [h["end_sample"] - h["start_sample"] for h in holds] == [n * 16 for n in profile["pauses_ms"]]
        assert all(np.max(np.abs(result[h["start_sample"] : h["end_sample"]])) == 0 for h in holds)
        assert len(result) - gold >= 6 * 16000
        assert np.count_nonzero(result) == np.count_nonzero(audio)
        delta = sum((h["end_sample"] - h["start_sample"]) - (b - a) for h, (a, b) in zip(holds, gaps))
        assert gold == original_spans[-1][1] + delta


def test_unusable_alignment_or_silence_is_not_auto_annotated():
    with pytest.raises(ValueError, match="Zeitmarken"):
        character_spans({}, ["Hallo"], 16000)
    fake = FakeElevenLabs(silent=True)
    data, _ = fake.speech("voice00001", {"text": "Hallo"})
    audio = np.frombuffer(base64.b64decode(data["audio_base64"]), dtype=np.int16).astype(np.float32)
    with pytest.raises(ValueError, match="stumm"):
        compose(audio, data["normalized_alignment"], ["Hallo"], [1000])


def test_pilot_generates_complete_usable_release_and_cache(tmp_path):
    store = Store(tmp_path)
    fake = FakeElevenLabs()
    ident = queued(store, config())
    generate(tmp_path, ident, client=fake)
    job = store.get("syntheses", ident)
    assert job["status"] == "completed", job
    release = store.get("releases", job["release_id"])
    assert len(release["records"]) == 10 and fake.calls == 5
    assert release["kind"] == "synthetic_pilot" and release["independent_base_files"] == 5
    assert not store.attempts()  # does not pollute human recordings
    assert all(r["annotation"]["status"] == "generated" for r in release["records"])
    assert all(r["annotation"]["reviewer"] == "" for r in release["records"])
    again = queued(store, config())
    generate(tmp_path, again, client=fake)
    assert store.get("syntheses", again)["status"] == "completed"
    assert fake.calls == 5
    with TestClient(create_app(tmp_path)) as client:
        first = release["records"][0]
        assert client.get(f"/api/clips/{first['id']}/audio").status_code == 200
        assert client.get(f"/api/clips/{first['id']}/waveform").json()["sample_rate"] == 16000
        assert client.get("/api/overview").json()["synthetic_files"] == 10
        exported = client.get(f"/api/releases/{release['id']}/download")
        assert exported.content.startswith(b"PK")
        with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
            assert len([name for name in archive.namelist() if name.startswith("bases/")]) == 5
        (tmp_path / first["audio_path"]).write_bytes(b"changed")
        assert client.get(f"/api/releases/{release['id']}/download").status_code == 409


def test_full_dataset_has_100_variants_without_split_leakage(tmp_path):
    store = Store(tmp_path)
    fake = FakeElevenLabs()
    ident = queued(store, config("full"))
    generate(tmp_path, ident, client=fake)
    job = store.get("syntheses", ident)
    assert job["status"] == "completed", job
    release = store.get("releases", job["release_id"])
    assert release["kind"] == "synthetic"
    assert len(release["records"]) == 100 and fake.calls == 25
    assert Counter(r["split"] for r in release["records"]) == {"dev": 20, "test": 80}
    assert len({r["base_id"] for r in release["records"]}) == 25
    for base_id in {r["base_id"] for r in release["records"]}:
        assert len({r["split"] for r in release["records"] if r["base_id"] == base_id}) == 1


def test_failed_generation_never_releases_broken_audio(tmp_path):
    store = Store(tmp_path)
    ident = queued(store, config())
    generate(tmp_path, ident, client=FakeElevenLabs(silent=True))
    assert store.get("syntheses", ident)["status"] == "failed"
    assert store.listing("releases") == []


def test_missing_key_is_clear_and_does_not_create_paid_job(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "api_key", lambda: "")
    with TestClient(create_app(tmp_path)) as client:
        assert not client.get("/api/synthesis/status").json()["configured"]
        assert client.post("/api/synthesis/preview", json=config().model_dump()).json()["files"] == 10
        result = client.post("/api/synthesis/jobs", json=config().model_dump())
        assert result.status_code == 400 and "API-Schlüssel" in result.json()["detail"]
        assert client.get("/api/synthesis/jobs").json() == []


def test_synthetic_release_can_be_evaluated_without_manual_annotation(tmp_path, monkeypatch):
    from eot_eval import runner
    from eot_eval.config import ExperimentConfig

    store = Store(tmp_path)
    ident = queued(store, config())
    generate(tmp_path, ident, client=FakeElevenLabs())
    release_id = store.get("syntheses", ident)["release_id"]

    class FakeVAD:
        metadata = {"name": "explicit test fixture"}

        def reset(self):
            self.frames = 0

        def probability(self, frame):
            self.frames += 1
            return 1.0 if self.frames <= 5 else 0.0

    payload = {
        "id": "synthetic-run-test",
        "release_id": release_id,
        "split": "dev",
        "config": ExperimentConfig(
            models=["baseline"], baseline_timeouts_ms=[500], mode="offline"
        ).model_dump(),
    }
    with store.connect() as db:
        db.execute("INSERT INTO runs VALUES(?,?,?,?)", (payload["id"], "queued", dumps(payload), now()))
    monkeypatch.setattr(runner, "Silero", FakeVAD)
    runner.run(tmp_path, payload["id"])
    assert store.get("runs", payload["id"])["status"] == "completed"
    report = json.loads((tmp_path / "runs" / payload["id"] / "report.json").read_text())
    assert len(report["rows"]) == 10
    assert report["dataset"]["source"] == "synthetic"
    assert all(
        r["reference_method"] == "provider_character_alignment_and_sample_mapping" for r in report["rows"]
    )
    assert (tmp_path / "runs" / payload["id"] / "by_pause_profile.csv").exists()
    assert store.attempts() == []
