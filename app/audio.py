import hashlib
import io
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

RATE = 16000
MAX_UPLOAD = 32 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode(data: bytes):
    if not data or len(data) > MAX_UPLOAD:
        raise ValueError("Audio fehlt oder überschreitet 32 MB.")
    try:
        audio, rate = sf.read(io.BytesIO(data), dtype="float32", always_2d=True)
    except (RuntimeError, sf.LibsndfileError) as exc:
        raise ValueError("Keine lesbare Audiodatei. Bitte WAV verwenden.") from exc
    if not 8000 <= rate <= 192000 or not 1 <= audio.shape[1] <= 2:
        raise ValueError("Erwartet werden ein oder zwei Kanäle mit 8–192 kHz.")
    if not 1 <= len(audio) / rate <= 90 or not np.isfinite(audio).all():
        raise ValueError("Die Aufnahme muss 1–90 Sekunden lang sein und gültige Samples enthalten.")
    mono = audio.mean(axis=1)
    if float(np.max(np.abs(mono))) > 1.0001:
        raise ValueError("Audiosamples liegen außerhalb des gültigen Pegelbereichs.")
    if rate != RATE:
        factor = math.gcd(rate, RATE)
        mono = resample_poly(mono, RATE // factor, rate // factor).astype(np.float32)
    output = io.BytesIO()
    sf.write(output, np.clip(mono, -1, 1), RATE, format="WAV", subtype="PCM_16")
    warnings = []
    if np.max(np.abs(audio)) < 0.005:
        warnings.append("Sehr leiser Pegel – bitte anhören.")
    if np.mean(np.abs(audio) >= 0.999) > 0.001:
        warnings.append("Mögliche Übersteuerung – bitte anhören.")
    return output.getvalue(), {
        "source_rate": rate,
        "source_channels": audio.shape[1],
        "sample_rate": RATE,
        "samples": len(mono),
        "duration_ms": round(len(mono) / RATE * 1000),
        "warnings": warnings,
        "original_sha256": digest(data),
        "canonical_sha256": digest(output.getvalue()),
    }


def waveform(path: Path, bins: int = 1200):
    audio, rate = sf.read(path, dtype="float32")
    edges = np.linspace(0, len(audio), min(bins, len(audio)) + 1, dtype=int)
    peaks = [[float(audio[a:b].min()), float(audio[a:b].max())] for a, b in zip(edges[:-1], edges[1:])]
    return {"peaks": peaks, "samples": len(audio), "sample_rate": rate}
