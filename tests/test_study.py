"""The study must preserve pairing, manual references and frozen 50-file exports."""

import csv
import io
import zipfile
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from test_lab import annotation, wav_bytes
from test_synthesis import FakeElevenLabs, queued

from app.main import create_app
from app.store import Conflict, Store
from app.study import AUTHOR_ID, STUDY_ID, study_cards
from app.synthesis import SynthesisConfig, generate, preview, request_body


def study_config(**overrides):
    return SynthesisConfig(
        size="study25", voices=[{"id": "voice00001", "name": "Test female", "gender": "female"}], **overrides
    )


def generate_study(store, config=None):
    fake = FakeElevenLabs()
    ident = queued(store, config or study_config())
    generate(store.root, ident, client=fake)
    job = store.get("syntheses", ident)
    assert job["status"] == "completed", job
    return store.get("releases", job["release_id"]), fake


def add_humans(store, count=25):
    import uuid

    data = wav_bytes()
    for card in study_cards()[:count]:
        ident = str(uuid.uuid4())
        store.upload(ident, card["id"], data, {"study_id": STUDY_ID})
        store.select(ident)
        store.annotate(ident, annotation(transcript=card["transcript"], listened=True))


def confirm_synthetic(store, release):
    for record in release["records"]:
        reference = record["annotation"]
        store.annotate(
            record["id"],
            annotation(
                gold_eot_sample=reference["gold_eot_sample"],
                holds=reference["holds"],
                transcript=reference["transcript"],
                listened=True,
            ),
        )


def test_protocol_covers_six_by_four_plus_long_iban():
    cards = study_cards()
    assert len(cards) == len({c["id"] for c in cards}) == len({c["pair_id"] for c in cards}) == 25
    assert Counter((c["content_type"], c["turn_pattern"]) for c in cards[:24]) == {
        (content, pattern): 1 for content in "KIEATV" for pattern in "FURN"
    }
    assert len({tuple(c["segments"]) for c in cards}) == 25
    assert cards[-1]["content_type"] == "I" and cards[-1]["pauses_ms"] == [3500]
    assert all(len(c["pauses_ms"]) == len(c["segments"]) - 1 for c in cards)
    assert all(c["transcript"] == " ".join(c["segments"]) for c in cards)
    assert len({c["delivery"] for c in cards}) == 4


def test_bootstrap_preserves_legacy_and_is_idempotent(tmp_path):
    store = Store(tmp_path)
    add_humans(store, count=1)
    store = Store(tmp_path)
    assert len(store.scenarios(AUTHOR_ID)) == 25
    assert len(store.scenarios("P01")) == 20
    assert store.participants()[0]["total"] == 25  # AUTHOR sorts before P01
    state = store.study_state()
    assert state["counts"]["human"] == state["counts"]["human_annotated"] == 1
    assert not state["ready"]
    assert state["counts"]["complete_pairs"] == 0


def test_one_female_voice_and_free_preview():
    cfg = study_config()
    plan = preview(cfg)
    assert plan["files"] == plan["base_generations"] == 25
    assert len(plan["templates"]) == 25
    assert request_body(plan["templates"][0], cfg)["language_code"] == "de"
    assert request_body(plan["templates"][1], cfg)["voice_settings"]["speed"] == 0.9
    for voices in [
        [{"id": "voice00001"}],
        [{"id": "voice00001", "gender": "male"}],
        [{"id": "voice00001", "gender": "female"}] * 2,
    ]:
        with pytest.raises(ValueError):
            SynthesisConfig(size="study25", voices=voices)
    assert SynthesisConfig(size="study25", voices=[{"id": "voice00001"}], female_voice_confirmed=True)
    with pytest.raises(ValueError):
        SynthesisConfig(
            size="study25", voices=[{"id": "voice00001", "gender": "male"}], female_voice_confirmed=True
        )


def test_generation_matches_all_25_cards_but_does_not_confirm_references(tmp_path):
    store = Store(tmp_path)
    release, fake = generate_study(store)
    assert fake.calls == 25
    assert release["kind"] == "study_synthetic"
    assert len(release["records"]) == len({r["base_id"] for r in release["records"]}) == 25
    for card, record in zip(study_cards(), release["records"]):
        assert record["scenario_id"] == card["id"] and record["pair_id"] == card["pair_id"]
        assert record["annotation"]["transcript"] == card["transcript"]
        assert [h["end_sample"] - h["start_sample"] for h in record["annotation"]["holds"]] == [
            ms * 16 for ms in card["pauses_ms"]
        ]
        assert record["samples"] - record["annotation"]["gold_eot_sample"] >= 6 * 16000
        assert record["annotation"]["status"] == "generated"
        assert record["split"] == "test"
    state = store.study_state()
    assert state["counts"]["synthetic"] == 25
    assert state["counts"]["synthetic_annotated"] == 0
    assert not state["ready"]
    with pytest.raises(ValueError, match="25 eigene"):
        store.release_study(release["id"])
    # Same provider requests are reused even for a new generation job.
    ident = queued(store, study_config())
    generate(tmp_path, ident, client=fake)
    assert fake.calls == 25


def test_synthetic_annotation_is_manual_validated_and_revisioned(tmp_path):
    store = Store(tmp_path)
    release, _ = generate_study(store)
    record = release["records"][0]
    with TestClient(create_app(tmp_path)) as client:
        endpoint = f"/api/clips/{record['id']}/annotation"
        assert client.post(endpoint, json=annotation()).status_code == 400
        assert client.post(endpoint, json=annotation(listened=True, transcript="")).status_code == 400
        assert (
            client.post(
                endpoint, json=annotation(listened=True, gold_eot_sample=record["samples"])
            ).status_code
            == 400
        )
        gold = record["annotation"]["gold_eot_sample"]
        response = client.post(endpoint, json=annotation(listened=True, gold_eot_sample=gold))
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["annotation"]["reference_method"] == "human_waveform_annotation"
        assert result["generated_reference"]["status"] == "generated"
        assert client.get(f"/api/clips/{record['id']}").json()["annotation"]["gold_eot_sample"] == gold
        assert client.get(f"/api/clips/{record['id']}/waveform").status_code == 200
        # A generated draft is immutable even after its working annotation changes.
        assert store.get("releases", release["id"])["records"][0]["annotation"]["status"] == "generated"


def test_release_requires_complete_pairs_and_freezes_manual_annotations(tmp_path):
    store = Store(tmp_path)
    release, _ = generate_study(store)
    add_humans(store)
    assert store.study_state()["counts"]["human_annotated"] == 25
    with pytest.raises(ValueError):
        store.release_study(release["id"])
    confirm_synthetic(store, release)
    assert store.study_state()["ready"]
    with TestClient(create_app(tmp_path)) as client:
        result = client.post("/api/study/releases", json={"synthetic_release_id": release["id"]})
        assert result.status_code == 200, result.text
        paired = result.json()
        assert paired["kind"] == "study_paired" and paired["source"] == "mixed"
        assert len(paired["records"]) == 50
        assert Counter(r["source"] for r in paired["records"]) == {"human": 25, "synthetic": 25}
        assert Counter(r["pair_id"] for r in paired["records"]) == {f"S{i:02}": 2 for i in range(1, 26)}
        assert all(
            r["annotation"]["reference_method"] == "human_waveform_annotation" for r in paired["records"]
        )
        assert {r["split"] for r in paired["records"]} == {"test"}
        clip_id = paired["records"][1]["id"]
        previous = paired["records"][1]["annotation"]["gold_eot_sample"]
        store.annotate(clip_id, annotation(listened=True, gold_eot_sample=previous + 10))
        assert store.get("releases", paired["id"])["records"][1]["annotation"]["gold_eot_sample"] == previous
        exported = client.get(f"/api/releases/{paired['id']}/download")
        assert exported.status_code == 200
        with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
            assert len([n for n in archive.namelist() if n.endswith(".wav")]) == 50
            assert len([n for n in archive.namelist() if n.startswith("bases/")]) == 25
            assert len(list(csv.reader(io.StringIO(archive.read("annotations.csv").decode())))) == 51
            assert "scenarios.json" in archive.namelist()
        first = paired["records"][0]
        (tmp_path / first["audio_path"]).write_bytes(b"changed")
        assert client.get(f"/api/releases/{paired['id']}/download").status_code == 409
        with pytest.raises(Conflict):
            store.release_study(release["id"])


def test_chosen_voice_group_does_not_mix_or_reuse_other_annotations(tmp_path):
    store = Store(tmp_path)
    first, _ = generate_study(store)
    confirm_synthetic(store, first)
    second, _ = generate_study(store, study_config(seed=43))
    assert store.study_state(first["id"])["counts"]["synthetic_annotated"] == 25
    assert store.study_state(second["id"])["counts"]["synthetic_annotated"] == 0
    with pytest.raises(ValueError, match="25-Szenarien"):
        store.study_state("missing")


def test_minimal_annotation_saves_both_sources_and_preserves_pause_metadata(tmp_path):
    import uuid

    store = Store(tmp_path)
    release, _ = generate_study(store)
    synthetic = release["records"][1]
    human_id = str(uuid.uuid4())
    store.upload(human_id, "ST25-02", wav_bytes(), {})
    store.select(human_id)
    with TestClient(create_app(tmp_path)) as client:
        for ident, gold in ((human_id, 16000), (synthetic["id"], synthetic["annotation"]["gold_eot_sample"])):
            response = client.post(
                f"/api/clips/{ident}/annotation",
                json={
                    "gold_eot_sample": gold,
                    "transcript": "Testbeitrag",
                },
            )
            assert response.status_code == 200, response.text
            saved = response.json()["annotation"]
            assert saved["reference_method"] == "human_waveform_annotation"
            assert saved["status"] == "annotated" and saved["annotator"] == "local"
            assert not saved["reviewer"] and not saved["listened"]
        saved = store.clip(synthetic["id"])
        assert saved["annotation"]["holds"] == synthetic["annotation"]["holds"]
        assert saved["generated_reference"] == synthetic["generated_reference"]
        state = store.study_state(release["id"])
        assert state["counts"]["complete_pairs"] == 1


def test_editing_gold_end_does_not_retain_an_old_review_status(tmp_path):
    store = Store(tmp_path)
    add_humans(store, count=1)
    human = store.attempts(AUTHOR_ID)[0]
    store.annotate(human["id"], annotation(status="reviewed", reviewer="B", listened=True))
    with TestClient(create_app(tmp_path)) as client:
        response = client.post(
            f"/api/clips/{human['id']}/annotation",
            json={
                "gold_eot_sample": 16010,
                "transcript": "Korrigiertes Transkript",
            },
        )
        assert response.status_code == 200, response.text
        saved = response.json()["annotation"]
        assert saved["status"] == "annotated" and saved["reviewer"] == ""
        assert saved["gold_eot_sample"] == 16010
