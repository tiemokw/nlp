import asyncio
import importlib.metadata
import importlib.util
import json
import os
import shutil
import threading
import time
from pathlib import Path

import numpy as np

from app.audio import digest
from app.synthesis import api_base_url, api_key
from eot_eval.settings import livekit_cloud_configured, livekit_credentials, validate_livekit_credentials


def version(package):
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def inventory(root: Path, livekit_version="v1"):
    has_silero = version("silero-vad") is not None
    smart = root / "models" / "smart-turn-v3.2-cpu.onnx"
    return [
        {
            "id": "baseline",
            "name": "Silero VAD + Stillezeit",
            "ready": has_silero,
            "detail": "Akustisches VAD mit festem Timeout.",
            "package_version": version("silero-vad"),
        },
        {
            "id": "livekit",
            "name": "LiveKit v1 Cloud" if livekit_version == "v1" else "LiveKit v1-mini lokal",
            "ready": has_silero
            and version("livekit-local-inference") is not None
            and version("livekit-agents") is not None
            and (livekit_version == "v1-mini" or livekit_cloud_configured()),
            "detail": (
                "Cloud v1: Dienstlaufzeit enthält Netzwerk. "
                + (
                    "Zugang konfiguriert; noch nicht authentifiziert."
                    if livekit_cloud_configured()
                    else "LIVEKIT_API_KEY und LIVEKIT_API_SECRET fehlen."
                )
            )
            if livekit_version == "v1"
            else "LiveKit Agents, lokal mit 1,2 s Audiofenster. Kein API-Schlüssel nötig.",
            "package_version": version("livekit-local-inference"),
            "cloud_configured": livekit_cloud_configured(),
            "local_ready": has_silero
            and version("livekit-local-inference") is not None
            and version("livekit-agents") is not None,
            "variant": livekit_version,
        },
        {
            "id": "smart_turn",
            "name": "Smart Turn v3.2 CPU",
            "ready": has_silero
            and smart.exists()
            and (root / "models" / "smart-turn.json").exists()
            and version("transformers") is not None,
            "detail": "Lokal, 8 s Audiofenster. Gewichte einmal mit prepare-models laden.",
            "package_version": version("transformers"),
        },
        {
            "id": "scribe",
            "name": "ElevenLabs Scribe v3 Live",
            "ready": has_silero and bool(api_key()) and version("aiohttp") is not None,
            "detail": "Cloud-STT mit semantischem Turn-Score. Verwendet euren ElevenLabs-Zugang und die konfigurierte Region; nur Echtzeit.",
            "package_version": version("aiohttp"),
            "default_selected": False,
        },
    ]


def prepare(root: Path):
    target = root / "models" / "smart-turn-v3.2-cpu.onnx"
    metadata_path = root / "models" / "smart-turn.json"
    if target.exists() and metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        if digest(target.read_bytes()) != metadata["sha256"]:
            raise RuntimeError(
                "Vorhandene Smart-Turn-Gewichte wurden verändert. Bitte vor einer neuen Vorbereitung prüfen."
            )
        return metadata
    os.environ.setdefault("HF_HOME", str(root / "models" / "hf-cache"))
    from huggingface_hub import HfApi, hf_hub_download

    folder = root / "models"
    folder.mkdir(parents=True, exist_ok=True)
    revision = HfApi().model_info("pipecat-ai/smart-turn-v3").sha
    filename = "smart-turn-v3.2-cpu.onnx"
    source = hf_hub_download("pipecat-ai/smart-turn-v3", filename, revision=revision)
    target = folder / filename
    shutil.copyfile(source, target)
    metadata = {
        "repository": "pipecat-ai/smart-turn-v3",
        "revision": revision,
        "filename": filename,
        "sha256": digest(target.read_bytes()),
        "license": "BSD-2-Clause",
    }
    (folder / "smart-turn.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def fingerprints(root: Path, models, livekit_version="v1-mini"):
    """Freeze package versions and local artifacts without loading inference sessions."""
    result = {
        "packages": {p: version(p) for p in ("numpy", "scipy", "onnxruntime", "torch", "silero-vad")},
        "adapter_sha256": digest(Path(__file__).read_bytes()),
    }
    spec = importlib.util.find_spec("silero_vad") if version("silero-vad") else None
    vad_file = Path(spec.origin).parent / "data" / "silero_vad.onnx" if spec else None
    result["vad_sha256"] = digest(vad_file.read_bytes()) if vad_file and vad_file.exists() else None
    if "livekit" in models and livekit_version == "v1":
        # Credentials are deliberately excluded. Hosted model weights cannot be pinned locally.
        endpoint = livekit_credentials()["base_url"]
        from urllib.parse import urlsplit

        parsed = urlsplit(endpoint)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Die Inferenzadresse darf keine Zugangsdaten oder Query enthalten.")
        result["livekit"] = {
            "model": "v1",
            "execution": "cloud",
            "agents_version": version("livekit-agents"),
            "endpoint": endpoint,
            "remote_revision": "not exposed by provider",
        }
    elif "livekit" in models:
        package = (
            importlib.metadata.distribution("livekit-local-inference")
            if version("livekit-local-inference")
            else None
        )
        native = (
            next(
                (
                    package.locate_file(f)
                    for f in package.files
                    if "_native" in str(f) and str(f).endswith((".so", ".pyd"))
                ),
                None,
            )
            if package
            else None
        )
        result["livekit"] = {
            "version": version("livekit-local-inference"),
            "agents_version": version("livekit-agents"),
            "native_sha256": digest(native.read_bytes()) if native else None,
        }
    if "smart_turn" in models:
        target = root / "models" / "smart-turn-v3.2-cpu.onnx"
        result["smart_turn"] = {
            "sha256": digest(target.read_bytes()) if target.exists() else None,
            "transformers": version("transformers"),
        }
    if "scribe" in models:
        result["scribe"] = {
            "model": "scribe_v3_live",
            "endpoint": api_base_url(),
            "commit_strategy": "manual",
            "language": "de",
            "aiohttp": version("aiohttp"),
            "adapter_sha256": digest(Path(__file__).with_name("scribe.py").read_bytes()),
            "remote_revision": "not exposed by provider",
        }
    return result


class Silero:
    def __init__(self):
        import torch
        from silero_vad import load_silero_vad

        torch.set_num_threads(1)
        self.torch = torch
        self.model = load_silero_vad(onnx=True)
        spec = importlib.util.find_spec("silero_vad")
        artifact = Path(spec.origin).parent / "data" / "silero_vad.onnx"
        self.metadata = {
            "name": "silero-vad",
            "version": version("silero-vad"),
            "sha256": digest(artifact.read_bytes()),
            "window_samples": 512,
        }

    def reset(self):
        self.model.reset_states()

    def probability(self, frame):
        return float(
            self.model(self.torch.from_numpy(np.array(frame, dtype=np.float32, copy=True)), 16000).item()
        )


class LiveKit:
    def __init__(self, root, variant="v1-mini"):
        import aiohttp
        from livekit import rtc
        from livekit.agents.inference import TurnDetector
        from livekit.agents.types import APIConnectOptions
        from livekit.local_inference import EOT_MAX_SAMPLES, _native

        if variant not in {"v1", "v1-mini"}:
            raise ValueError("Unbekannte LiveKit-Variante.")
        self.cloud = variant == "v1"
        credentials = validate_livekit_credentials() if self.cloud else {}
        self.rtc = rtc
        self.window = None if self.cloud else EOT_MAX_SAMPLES
        self.streaming = False
        self.warmed = False
        self.call_metrics = {}
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()

        async def setup():
            self.http_session = aiohttp.ClientSession() if self.cloud else None
            options = APIConnectOptions(max_retry=0, timeout=10)
            fallback_options = {"local_fallback": False} if self.cloud else {}
            try:
                self.detector = TurnDetector(
                    version=variant,
                    sample_rate=16000,
                    http_session=self.http_session,
                    conn_options=options,
                    **credentials,
                    **fallback_options,
                )
                self.stream = self.detector.stream(conn_options=options)
            except Exception:
                if self.http_session is not None:
                    await self.http_session.close()
                raise

        try:
            asyncio.run_coroutine_threadsafe(setup(), self.loop).result(timeout=30)
        except Exception:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=5)
            self.loop.close()
            raise
        self.metadata = {
            "name": "LiveKit v1 Cloud" if self.cloud else "LiveKit v1-mini",
            "version": version("livekit-local-inference"),
            "agents_version": version("livekit-agents"),
            "integration": f"livekit.agents.inference.TurnDetector(version={variant})",
            "execution": "cloud" if self.cloud else "local",
            "inference_measure": "service_roundtrip" if self.cloud else "local_adapter",
            "model_id": variant,
            "local_fallback": False,
            "sdk_ingress_yield_ms": 5,
            "audio_delivery": "continuous released replay frames",
            "window_samples": self.window,
            "license": "LiveKit Model License",
            "score": "probability of end of turn",
        }
        if self.cloud:
            self.metadata.update(
                {"endpoint": credentials["base_url"], "remote_revision": "not exposed by provider"}
            )
        else:
            self.metadata["native_sha256"] = digest(Path(_native.__file__).read_bytes())

    def reset(self):
        async def clear():
            self.stream.flush()
            await asyncio.sleep(0.005)

        asyncio.run_coroutine_threadsafe(clear(), self.loop).result(timeout=10)
        self.streaming = True

    def feed(self, audio):
        pcm = np.ascontiguousarray((np.clip(audio, -1, 1) * 32767).astype(np.int16))
        frame = self.rtc.AudioFrame(
            data=pcm.tobytes(), sample_rate=16000, num_channels=1, samples_per_channel=len(pcm)
        )
        self.loop.call_soon_threadsafe(self.stream.push_audio, frame)

    def warmup(self):
        if not self.cloud and not self.warmed:
            self.score(np.zeros(16000, dtype=np.float32))
            self.warmed = True

    def score(self, audio):
        async def predict():
            if not self.streaming:
                self.stream.flush()
                context = audio if self.window is None else audio[-self.window :]
                self.feed(context)
            if self.cloud:
                # The pinned SDK currently exposes no public connection-ready signal. The
                # read-only guard prevents predict() being dropped before its websocket exists.
                deadline = self.loop.time() + 10
                while getattr(self.stream._transport, "_ws", None) is None:
                    if self.stream.is_degraded or self.loop.time() >= deadline:
                        raise RuntimeError(
                            "LiveKit v1 Cloud nicht verbunden. Zugang, Kontingent und Netzwerk prüfen."
                        )
                    await asyncio.sleep(0.01)
            # Let the public SDK stream drain its queued flush/frame before requesting a prediction.
            # This ingress scheduling time is included in our measured adapter inference time.
            await asyncio.sleep(0.005)
            event = await asyncio.wait_for(self.stream.predict(), timeout=8)
            if self.cloud and (
                self.stream.model != "turn-detector-v1"
                or self.stream.is_fallback
                or self.stream.is_degraded
                or event.inference_duration is None
            ):
                raise RuntimeError(
                    "LiveKit Cloud lieferte keine gültige v1-Antwort. Ein Ersatzmodell wird nicht gewertet."
                )
            self.call_metrics = (
                {"sdk_server_e2e_ms": event.inference_duration * 1000}
                if self.cloud and event.inference_duration is not None
                else {}
            )
            from livekit.agents.language import LanguageCode

            threshold = await self.stream.unlikely_threshold(LanguageCode("de"))
            if threshold is None:
                raise RuntimeError("LiveKit lieferte keine kalibrierte Entscheidungsschwelle für Deutsch.")
            self.call_metrics["eot_threshold"] = checked(threshold)
            self.metadata["german_default_threshold"] = threshold
            return checked(event.end_of_turn_probability)

        return asyncio.run_coroutine_threadsafe(predict(), self.loop).result(timeout=20)

    def close(self):
        async def finish():
            await self.stream.aclose()
            if self.http_session is not None:
                await self.http_session.close()
            await self.loop.shutdown_default_executor()

        try:
            asyncio.run_coroutine_threadsafe(finish(), self.loop).result(timeout=10)
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=5)
            self.loop.close()


class SmartTurn:
    def __init__(self, root):
        import onnxruntime as ort
        from transformers import WhisperFeatureExtractor

        path = root / "models" / "smart-turn-v3.2-cpu.onnx"
        meta = root / "models" / "smart-turn.json"
        if not path.exists() or not meta.exists():
            raise RuntimeError(
                "Smart-Turn-Gewichte fehlen. Zuerst python -m eot_eval.cli prepare-models ausführen."
            )
        self.metadata = json.loads(meta.read_text())
        if digest(path.read_bytes()) != self.metadata["sha256"]:
            raise RuntimeError("Smart-Turn-Prüfsumme stimmt nicht mit dem vorbereiteten Modell überein.")
        self.metadata.update(
            {
                "name": "Smart Turn v3.2 CPU",
                "onnxruntime_version": version("onnxruntime"),
                "transformers_version": version("transformers"),
                "window_samples": 128000,
                "score": "probability of completed turn",
            }
        )
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(
            str(path), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self.features = WhisperFeatureExtractor(chunk_length=8)

    def score(self, audio):
        context = np.zeros(128000, dtype=np.float32)
        tail = np.asarray(audio[-128000:], dtype=np.float32)
        if len(tail):
            context[-len(tail) :] = tail
        features = self.features(
            context,
            sampling_rate=16000,
            return_tensors="np",
            padding="max_length",
            max_length=128000,
            truncation=True,
            do_normalize=True,
        ).input_features
        output = self.session.run(
            None, {self.session.get_inputs()[0].name: np.asarray(features, dtype=np.float32)}
        )
        return checked(float(np.asarray(output[0]).flat[0]))

    def close(self):
        pass


def checked(value):
    value = float(value)
    if not np.isfinite(value) or not 0 <= value <= 1:
        raise RuntimeError("Das Modell lieferte keinen gültigen EOT-Wahrscheinlichkeitswert.")
    return value


def load(name, root, livekit_version="v1-mini"):
    if name == "livekit":
        return LiveKit(root, variant=livekit_version)
    if name == "smart_turn":
        return SmartTurn(root)
    if name == "scribe":
        from eot_eval.scribe import Scribe

        return Scribe(root)
    raise ValueError("Unbekannter Modelladapter.")


def timed_score(model, audio):
    start = time.perf_counter()
    score = model.score(audio)
    return {
        "score": score,
        "started": start,
        "finished": time.perf_counter(),
        **getattr(model, "call_metrics", {}),
    }
