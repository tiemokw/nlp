"""Local credentials; secret values never enter configurations or reports."""

import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values

DEFAULT_LIVEKIT_ENDPOINT = "https://agent-gateway.livekit.cloud/v1"


def local_setting(*names, default=""):
    values = dotenv_values(Path(__file__).resolve().parent.parent / ".env")
    for name in names:
        value = os.environ.get(name, "").strip() or str(values.get(name) or "").strip()
        if value:
            return value
    return default


def livekit_credentials():
    return {
        "api_key": local_setting("LIVEKIT_INFERENCE_API_KEY", "LIVEKIT_API_KEY"),
        "api_secret": local_setting("LIVEKIT_INFERENCE_API_SECRET", "LIVEKIT_API_SECRET"),
        "base_url": local_setting("LIVEKIT_INFERENCE_URL", default=DEFAULT_LIVEKIT_ENDPOINT),
    }


def livekit_cloud_configured():
    values = livekit_credentials()
    return bool(values["api_key"] and values["api_secret"])


def validate_livekit_credentials():
    values = livekit_credentials()
    if not values["api_key"] or not values["api_secret"]:
        raise ValueError(
            "LiveKit Cloud benötigt LIVEKIT_API_KEY und LIVEKIT_API_SECRET in der lokalen .env-Datei."
        )
    if any(not 33 <= ord(c) <= 126 for name in ("api_key", "api_secret") for c in values[name]):
        raise ValueError(
            "LiveKit-Zugang enthält ungültige Leer- oder Steuerzeichen. Bitte die lokalen Einträge prüfen."
        )
    url = urlsplit(values["base_url"])
    if (
        url.scheme not in {"https", "wss"}
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ValueError(
            "LIVEKIT_INFERENCE_URL muss eine HTTPS-/WSS-Inferenzadresse ohne Zugangsdaten oder Query sein."
        )
    values["base_url"] = values["base_url"].rstrip("/")
    return values
