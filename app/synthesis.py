"""ElevenLabs synthesis and automatic, sample-accurate pause variants.

Reference speech endpoints come from provider alignment, not human annotation.
No detector under evaluation is used to construct reference labels.
"""

import base64
import json
import re
import uuid
from pathlib import Path
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import soundfile as sf
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.audio import RATE, digest
from app.store import Store, dumps, now
from app.study import STUDY_ID, protocol, study_cards
from eot_eval.settings import local_setting

DEFAULT_ELEVENLABS_URL = "https://api.elevenlabs.io"
ELEVENLABS_URLS = {
    DEFAULT_ELEVENLABS_URL,
    "https://api.eu.residency.elevenlabs.io",
    "https://api.in.residency.elevenlabs.io",
    "https://api.sg.residency.elevenlabs.io",
}

TEMPLATES = [
    {
        "id": "customer_number",
        "title": "Kundennummer in zwei Gruppen",
        "content_type": "K",
        "turn_pattern": "U",
        "ambiguous": True,
        "segments": ["Meine Kundennummer ist", "eins zwei drei vier", "fünf sechs sieben acht."],
    },
    {
        "id": "email",
        "title": "E-Mail-Adresse mit Denkpause",
        "content_type": "E",
        "turn_pattern": "U",
        "ambiguous": False,
        "segments": ["Meine E-Mail-Adresse lautet", "lea Punkt peters at", "example Punkt org."],
    },
    {
        "id": "connection",
        "title": "Anliegen mit offenem Satz",
        "content_type": "T",
        "turn_pattern": "U",
        "ambiguous": False,
        "segments": [
            "Ich rufe an, weil",
            "meine Internetverbindung immer abbricht,",
            "sobald ich ein Videogespräch starte.",
        ],
    },
    {
        "id": "cancellation",
        "title": "Vollständiger Satz und Nachtrag",
        "content_type": "V",
        "turn_pattern": "N",
        "ambiguous": True,
        "segments": ["Ich möchte meinen Vertrag kündigen.", "Allerdings erst zum Ende der Laufzeit."],
    },
    {
        "id": "correction",
        "title": "Hausnummer mit Selbstkorrektur",
        "content_type": "A",
        "turn_pattern": "R",
        "ambiguous": True,
        "segments": ["Die Hausnummer ist vierzehn,", "Entschuldigung,", "ich meine vierundzwanzig."],
    },
]
PROFILES = [
    {"id": "short", "name": "Kurze Pausen", "pauses_ms": [200, 200]},
    {"id": "medium", "name": "Mittlere Pausen", "pauses_ms": [700, 400]},
    {"id": "long", "name": "Lange Denkpausen", "pauses_ms": [1800, 1200]},
    {"id": "patient", "name": "Sehr lange Pausen", "pauses_ms": [2500, 1800]},
]


class Voice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,100}$")
    name: str = Field(default="", max_length=100)
    gender: str = Field(default="", max_length=40)


class SynthesisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    voices: list[Voice] = Field(min_length=1, max_length=5)
    size: Literal["pilot", "full", "study25"] = "pilot"
    female_voice_confirmed: bool = False
    model_id: Literal["eleven_multilingual_v2", "eleven_flash_v2_5"] = "eleven_multilingual_v2"
    seed: int = Field(default=42, ge=0, le=4294967295)

    @model_validator(mode="after")
    def valid_voices(self):
        if len({v.id for v in self.voices}) != len(self.voices):
            raise ValueError("Bitte verschiedene Stimmen auswählen.")
        if self.size == "full" and len(self.voices) != 5:
            raise ValueError("Für 100 Dateien werden genau fünf Stimmen benötigt.")
        if self.size == "pilot" and len(self.voices) != 1:
            raise ValueError("Der Pilot verwendet genau eine Stimme.")
        if self.size == "study25":
            if len(self.voices) != 1:
                raise ValueError("Die Studie verwendet genau eine synthetische weibliche Stimme.")
            gender = self.voices[0].gender.strip().casefold()
            if gender in {"male", "man", "männlich"} or not (
                gender in {"female", "woman", "weiblich"} or self.female_voice_confirmed
            ):
                raise ValueError(
                    "Bitte eine weibliche Stimme auswählen oder bei fehlendem Anbieterlabel ausdrücklich bestätigen."
                )
        return self


def api_key():
    return local_setting("ELEVENLABS_API_KEY")


def api_base_url():
    url = local_setting("ELEVENLABS_BASE_URL", default=DEFAULT_ELEVENLABS_URL).rstrip("/")
    if url not in ELEVENLABS_URLS:
        raise ValueError(
            "ELEVENLABS_BASE_URL muss ein offizieller ElevenLabs-API-Endpunkt ohne /v1-Pfad sein. "
            "EU: https://api.eu.residency.elevenlabs.io"
        )
    return url


class ElevenLabs:
    def __init__(self):
        self.base_url = api_base_url()
        self.key = api_key()
        if not self.key:
            raise ValueError("ElevenLabs-API-Schlüssel fehlt. ELEVENLABS_API_KEY lokal in .env eintragen.")
        if any(not 33 <= ord(char) <= 126 for char in self.key):
            raise ValueError(
                "Der API-Schlüssel enthält unzulässige Leer- oder Steuerzeichen. Bitte den lokalen Eintrag prüfen."
            )

    def request(self, path, body=None):
        payload = json.dumps(body).encode() if body is not None else None
        request = Request(
            self.base_url + path,
            data=payload,
            headers={"xi-api-key": self.key, "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=120) as response:
                data = json.load(response)
                return data, {
                    "request_id": response.headers.get("request-id"),
                    "character_cost": response.headers.get("character-cost"),
                }
        except HTTPError as exc:
            messages = {
                401: "API-Schlüssel und Region prüfen; ein EU-Residency-Schlüssel benötigt den EU-Endpunkt",
                403: "Berechtigung oder Tarif prüfen",
                429: "Kontingent oder Anfragelimit erreicht",
            }
            raise ValueError(
                f"ElevenLabs HTTP {exc.code} ({self.base_url}): {messages.get(exc.code, 'Anfrage fehlgeschlagen')}. Bereits erzeugte Basisdateien bleiben im Cache."
            ) from None
        except (URLError, TimeoutError):
            raise ValueError(
                "ElevenLabs ist nicht erreichbar oder hat die Zeit überschritten. Kein automatischer kostenpflichtiger Wiederholungsversuch."
            ) from None

    def voices(self):
        result, token = [], None
        for _ in range(10):
            params = {"page_size": 100}
            if token:
                params["next_page_token"] = token
            data, _ = self.request("/v2/voices?" + urlencode(params))
            result.extend(
                {"id": v["voice_id"], "name": v["name"], "labels": v.get("labels", {})}
                for v in data.get("voices", [])
            )
            token = data.get("next_page_token")
            if not data.get("has_more") or not token:
                break
        return result

    def speech(self, voice_id, body):
        return self.request(f"/v1/text-to-speech/{voice_id}/with-timestamps?output_format=pcm_16000", body)


def request_body(template, config):
    body = {
        "text": ' <break time="0.6s" /> '.join(template["segments"]),
        "model_id": config.model_id,
        "seed": config.seed,
        "voice_settings": {"stability": 0.65, "similarity_boost": 0.75, "use_speaker_boost": True},
    }
    if config.size == "study25":
        body["language_code"] = "de"
        body["voice_settings"].update(speed=template["speed"], style=template["style"])
    return body


def preview(config, root=None):
    if config.size == "study25":
        templates = study_cards()
        return {
            "base_generations": 25,
            "files": 25,
            "characters_before_cache": sum(len(request_body(t, config)["text"]) for t in templates),
            "profiles": [],
            "templates": templates,
            "protocol": protocol(),
            "voices": [v.model_dump() for v in config.voices],
            "note": "25 Szenarien mit einer Stimme. Referenzenden sind Vorschläge und müssen nach Anhören in der Wellenform bestätigt werden. Tempo und Ausdruck werden über TTS-Einstellungen angenähert; die Tonlage bitte beim Anhören prüfen. Die Zeichenmenge ist keine verbindliche Credit-Abrechnung.",
        }
    profiles = PROFILES if config.size == "full" else [PROFILES[0], PROFILES[2]]
    characters = sum(len(request_body(t, config)["text"]) for t in TEMPLATES) * len(config.voices)
    return {
        "base_generations": len(config.voices) * len(TEMPLATES),
        "files": len(config.voices) * len(TEMPLATES) * len(profiles),
        "characters_before_cache": characters,
        "profiles": profiles,
        "templates": TEMPLATES,
        "voices": [v.model_dump() for v in config.voices],
        "note": "Zeichenmenge ist keine verbindliche Credit-Abrechnung. Pausenvarianten werden lokal aus denselben Basisdateien erzeugt.",
    }


def normalize(text):
    return "".join(c for c in text.casefold() if c.isalnum())


def character_spans(alignment, segments, samples):
    """Map only spoken symbols, stripping possible SSML character spans first."""
    characters = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])
    if not characters or not len(characters) == len(starts) == len(ends):
        raise ValueError("ElevenLabs hat keine verwendbaren Zeichen-Zeitmarken geliefert.")
    joined = "".join(characters)
    # Provider entries are character-level. Multi-character entries would break index mapping.
    if any(len(c) != 1 for c in characters):
        raise ValueError("Unerwartetes Zeitmarkenformat: einzelne Zeichen erwartet.")
    hidden = set()
    for match in re.finditer(r"<[^>]*>", joined):
        hidden.update(range(match.start(), match.end()))
    text, indexes = "", []
    for i, char in enumerate(characters):
        if i in hidden:
            continue
        symbol = normalize(char)
        text += symbol
        indexes.extend([i] * len(symbol))
    expected = "".join(normalize(s) for s in segments)
    if text != expected:
        raise ValueError(
            "Die zurückgegebenen Text-Zeitmarken passen nicht zum geplanten gesprochenen Text. Generierung wird nicht mit geratenen Labels übernommen."
        )
    spans, offset = [], 0
    for segment in segments:
        length = len(normalize(segment))
        first, last = indexes[offset], indexes[offset + length - 1]
        a, b = float(starts[first]), float(ends[last])
        if not np.isfinite([a, b]).all() or not 0 <= a < b <= samples / RATE + 0.03:
            raise ValueError("Ungültige Sprach-Zeitmarken im erzeugten Audio.")
        spans.append((round(a * RATE), min(samples, round(b * RATE))))
        offset += length
    if any(left[1] > right[0] for left, right in zip(spans[:-1], spans[1:])):
        raise ValueError("Sprachabschnitte überlappen in den Zeitmarken.")
    return spans


def quiet_gap(audio, start, end):
    if end <= start:
        raise ValueError("Zwischen den Sprachabschnitten fehlt eine erkennbare Pause.")
    quiet = np.abs(audio[start:end]) <= 0.001
    padded = np.pad(quiet.astype(np.int8), (1, 1))
    changes = np.diff(padded)
    begins, finishes = np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)
    if not len(begins):
        raise ValueError("Die geplante Pause enthält keine ausreichend leise Stelle.")
    idx = int(np.argmax(finishes - begins))
    left, right = start + int(begins[idx]), start + int(finishes[idx])
    if right - left < round(0.03 * RATE):
        raise ValueError(
            "Die geplante Pause ist nicht sicher automatisch bearbeitbar. Die Basisgenerierung bleibt im Cache; kein Abschneiden von Sprache."
        )
    # Stay strictly between aligned spoken segments; do not trim speech or breaths outside this gap.
    return left, right


def compose(audio, alignment, segments, pauses_ms):
    spans = character_spans(alignment, segments, len(audio))
    if any(np.max(np.abs(audio[start:end])) < 0.003 for start, end in spans):
        raise ValueError(
            "Ein geplanter Sprachabschnitt ist praktisch stumm. Der Clip wird nicht automatisch freigegeben."
        )
    gaps = [quiet_gap(audio, a[1], b[0]) for a, b in zip(spans[:-1], spans[1:])]
    pieces, holds, cursor, output_count = [], [], 0, 0
    for i, (left, right) in enumerate(gaps):
        if left < cursor:
            raise ValueError("Pausenbereiche überlappen.")
        pieces.append(audio[cursor:left])
        output_count += left - cursor
        length = round(pauses_ms[min(i, len(pauses_ms) - 1)] * RATE / 1000)
        holds.append({"start_sample": output_count, "end_sample": output_count + length})
        pieces.append(np.zeros(length, np.float32))
        output_count += length
        cursor = right
    pieces.append(audio[cursor:])
    delta = sum(
        (h["end_sample"] - h["start_sample"]) - (right - left) for h, (left, right) in zip(holds, gaps)
    )
    gold = spans[-1][1] + delta
    combined = np.concatenate([*pieces, np.zeros(6 * RATE, np.float32)])
    if not 0 < gold <= len(combined) - 6 * RATE or any(h["end_sample"] > gold for h in holds):
        raise ValueError("Die automatisch konstruierten Zeitmarken sind inkonsistent.")
    return combined, gold, holds, gaps


def cached_speech(root, voice, template, config, client):
    body = request_body(template, config)
    endpoint = getattr(client, "base_url", DEFAULT_ELEVENLABS_URL)
    identity = {"voice": voice.id, "body": body, "format": "pcm_16000"}
    # Preserve existing global cache IDs, while keeping residency environments isolated.
    if endpoint != DEFAULT_ELEVENLABS_URL:
        identity["api_base_url"] = endpoint
    cache_id = digest(dumps(identity).encode())
    folder = root / "synthetic" / "cache" / cache_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "response.json"
    if path.exists():
        cached = json.loads(path.read_text())
    else:
        data, request_meta = client.speech(voice.id, body)
        cached = {
            "response": data,
            "provider": request_meta,
            "request": body,
            "voice_id": voice.id,
            "api_base_url": endpoint,
            "created_at": now(),
        }
        temporary = folder / "response.tmp"
        temporary.write_text(dumps(cached), encoding="utf-8")
        temporary.replace(path)
    response = cached["response"]
    try:
        pcm = base64.b64decode(response["audio_base64"], validate=True)
        if len(pcm) % 2 or not 0 < len(pcm) <= 90 * RATE * 2:
            raise ValueError()
        audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
    except (KeyError, ValueError):
        raise ValueError("ElevenLabs lieferte kein gültiges PCM-16-kHz-Audio.") from None
    alignment = response.get("normalized_alignment") or response.get("alignment") or {}
    return (
        audio,
        alignment,
        cache_id,
        {
            "provider": cached["provider"],
            "api_base_url": cached.get("api_base_url", endpoint),
            "model_id": config.model_id,
            "seed": config.seed,
            "voice_id": voice.id,
            "voice_name": voice.name,
            "base_audio_sha256": digest(pcm),
            "cache_response_sha256": digest(path.read_bytes()),
            "tts_parameters": body,
            "segments": template["segments"],
        },
    )


def generate(root: Path, ident: str, client=None):
    store = Store(root)
    job = store.get("syntheses", ident)
    if job["status"] != "queued":
        raise ValueError("Nur neu eingereihte Generierungen können starten.")
    config = SynthesisConfig.model_validate(job["config"])
    store.update_synthesis(ident, "running", progress=0)
    try:
        client = client or ElevenLabs()
        if config.size == "study25":
            generate_study(store, ident, config, client)
            return
        profiles = preview(config)["profiles"]
        folder = root / "synthetic" / ident
        folder.mkdir(parents=True, exist_ok=True)
        records = []
        for voice_index, voice in enumerate(config.voices):
            for template in TEMPLATES:
                if store.get("syntheses", ident)["status"] == "cancelled":
                    return
                audio, alignment, base_id, provenance = cached_speech(root, voice, template, config, client)
                for profile in profiles:
                    generated, gold, holds, gaps = compose(
                        audio, alignment, template["segments"], profile["pauses_ms"]
                    )
                    clip_id = "syn-" + uuid.uuid4().hex
                    relative = f"synthetic/{ident}/{clip_id}.wav"
                    sf.write(root / relative, generated, RATE, subtype="PCM_16")
                    record = {
                        "id": clip_id,
                        "scenario_id": f"V{voice_index + 1:02}-{template['id']}-{profile['id']}",
                        "participant_id": f"V{voice_index + 1:02}",
                        "content_type": template["content_type"],
                        "turn_pattern": template["turn_pattern"],
                        "split": "dev" if voice_index == 0 else "test",
                        "audio_path": relative,
                        "sha256": digest((root / relative).read_bytes()),
                        "samples": len(generated),
                        "sample_rate": RATE,
                        "source": "synthetic",
                        "base_id": base_id,
                        "synthesis_job_id": ident,
                        "provenance": {**provenance, "profile": profile, "replaced_base_gaps": gaps},
                        "annotation": {
                            "gold_eot_sample": gold,
                            "holds": holds,
                            "transcript": " ".join(template["segments"]),
                            "ambiguous_transition": template["ambiguous"],
                            "status": "generated",
                            "reference_method": "provider_character_alignment_and_sample_mapping",
                            "annotator": "automatic",
                            "reviewer": "",
                            "notes": "Konstruiertes Referenzende aus TTS-Alignment; keine menschliche Gegenprüfung.",
                        },
                    }
                    records.append(record)
                store.update_synthesis(
                    ident, "running", progress=len(records), total=preview(config)["files"]
                )
        splits = {}
        for record in records:
            splits.setdefault(record["base_id"], set()).add(record["split"])
        if any(len(s) != 1 for s in splits.values()):
            raise ValueError("Varianten einer Basisdatei dürfen nicht in verschiedenen Splits liegen.")
        payload = {
            "schema_version": 2,
            "kind": "synthetic" if config.size == "full" else "synthetic_pilot",
            "source": "synthetic",
            "created_at": now(),
            "records": records,
            "synthesis_config": config.model_dump(),
            "annotation_method": "provider_alignment; automatic_pause_replacement",
            "independent_base_files": len(splits),
            "generator_sha256": digest(Path(__file__).read_bytes()),
            "generator_libraries": {"numpy": np.__version__, "soundfile": sf.__version__},
        }
        release = store.save_synthetic_release(payload)
        store.update_synthesis(
            ident, "completed", release_id=release["id"], progress=len(records), total=len(records)
        )
    except Exception as exc:
        if store.get("syntheses", ident)["status"] != "cancelled":
            store.update_synthesis(ident, "failed", error=str(exc), error_type=type(exc).__name__)


def generate_study(store, ident, config, client):
    """One distinct base generation per scenario; endpoints require human review."""
    root = store.root
    folder = root / "synthetic" / ident
    folder.mkdir(parents=True, exist_ok=True)
    voice = config.voices[0]
    records = []
    for template in study_cards():
        if store.get("syntheses", ident)["status"] == "cancelled":
            return
        audio, alignment, base_id, provenance = cached_speech(root, voice, template, config, client)
        generated, gold, holds, gaps = compose(audio, alignment, template["segments"], template["pauses_ms"])
        clip_id = "syn-" + uuid.uuid4().hex
        relative = f"synthetic/{ident}/{clip_id}.wav"
        sf.write(root / relative, generated, RATE, subtype="PCM_16")
        reference = {
            "gold_eot_sample": gold,
            "holds": holds,
            "transcript": template["transcript"],
            "ambiguous_transition": template["ambiguous"],
            "status": "generated",
            "reference_method": "provider_character_alignment_and_sample_mapping",
            "annotator": "automatic",
            "reviewer": "",
            "listened": False,
            "notes": "Vorschlag aus TTS-Zeitmarken. Vollständigen Beitrag anhören und Ende manuell bestätigen.",
        }
        records.append(
            {
                "id": clip_id,
                "study_id": STUDY_ID,
                "pair_id": template["pair_id"],
                "scenario_id": template["id"],
                "participant_id": "ELEVENLABS",
                "content_type": template["content_type"],
                "turn_pattern": template["turn_pattern"],
                "split": "test",
                "audio_path": relative,
                "sha256": digest((root / relative).read_bytes()),
                "samples": len(generated),
                "sample_rate": RATE,
                "source": "synthetic",
                "base_id": base_id,
                "synthesis_job_id": ident,
                "scenario": template,
                "provenance": {
                    **provenance,
                    "delivery": template["delivery"],
                    "planned_pauses_ms": template["pauses_ms"],
                    "replaced_base_gaps": gaps,
                },
                "generated_reference": reference,
                "annotation": reference,
            }
        )
        store.update_synthesis(ident, "running", progress=len(records), total=25)
    if store.get("syntheses", ident)["status"] == "cancelled":
        return
    release = store.save_synthetic_release(
        {
            "schema_version": 3,
            "kind": "study_synthetic",
            "source": "synthetic",
            "study_id": STUDY_ID,
            "protocol": protocol(),
            "created_at": now(),
            "records": records,
            "synthesis_config": config.model_dump(),
            "independent_base_files": 25,
            "annotation_method": "provider_alignment_proposal_requires_human_waveform_annotation",
            "generator_sha256": digest(Path(__file__).read_bytes()),
        }
    )
    store.update_synthesis(ident, "completed", release_id=release["id"], progress=25, total=25)
