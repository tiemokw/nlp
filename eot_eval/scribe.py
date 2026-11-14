"""Scribe v3 Live turn scores, streamed causally with our common endpointing policy.

Manual commit avoids an undocumented mixture of provider VAD timers and our timer.
There is no request/response inference duration for this continuously running service.
"""

import asyncio
import base64
import json
import queue
import threading
import time
from urllib.parse import urlencode

import numpy as np

from app.synthesis import ElevenLabs

MODEL = "scribe_v3_live"


class Scribe:
    def __init__(self, root):
        import aiohttp

        self.aiohttp = aiohttp
        client = ElevenLabs()
        self.key = client.key
        self.endpoint = client.base_url
        self.events = queue.Queue()
        self.error = None
        self.seen_probability = False
        self.session = self.ws = None
        self.tasks = []
        self.closing = False
        self.submitted_samples = 0
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.metadata = {
            "name": "ElevenLabs Scribe v3 Live",
            "model_id": MODEL,
            "execution": "cloud",
            "endpoint": self.endpoint,
            "integration": "direct realtime WebSocket",
            "inference_measure": "streaming_service",
            "commit_strategy": "manual",
            "decision_policy": "turn_probability plus common VAD/minimum silence/maximum timeout",
            "language": "de",
            "audio_format": "pcm_16000",
            "send_chunk_samples": 2048,
            "initial_buffer_note": "Provider documents approximately 2 seconds before first transcription.",
            "score_alignment": "Audio submitted at event receipt is an upper bound, not a provider acknowledgement.",
            "sessions": [],
            "remote_revision": "not exposed by provider",
        }

    def _call(self, coro, timeout=20):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            future.cancel()
            raise RuntimeError(
                "Scribe hat die Zeitgrenze überschritten. Kein automatischer Neuversuch."
            ) from None

    def warmup(self):
        pass  # Never send billable warm-up audio.

    async def _disconnect(self):
        self.closing = True
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks = []
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
        if self.session is not None:
            await self.session.close()
            self.session = None

    def reset(self):
        self._call(self._open(), timeout=30)

    async def _open(self):
        await self._disconnect()
        self.closing = False
        self.error = None
        self.seen_probability = False
        self.events = queue.Queue()
        self.submitted_samples = 0
        self.audio_queue = asyncio.Queue(maxsize=64)
        params = {
            "model_id": MODEL,
            "audio_format": "pcm_16000",
            "language_code": "de",
            "commit_strategy": "manual",
            "keepalive_interval_ms": 1000,
        }
        url = (
            self.endpoint.replace("https://", "wss://", 1)
            + "/v1/speech-to-text/realtime?"
            + urlencode(params)
        )
        started = time.perf_counter()
        self.session = self.aiohttp.ClientSession()
        try:
            self.ws = await asyncio.wait_for(
                self.session.ws_connect(
                    url, headers={"xi-api-key": self.key}, timeout=self.aiohttp.ClientWSTimeout(ws_close=3)
                ),
                timeout=10,
            )
            hello = await self.ws.receive_json(timeout=10)
            if (
                hello.get("message_type") != "session_started"
                or hello.get("config", {}).get("model_id") != MODEL
            ):
                raise RuntimeError(
                    "Scribe v3 Live hat keine gültige Sitzung bestätigt. Modellzugriff und STT-Berechtigung prüfen."
                )
            self.metadata["sessions"].append(
                {
                    "session_id": hello.get("session_id"),
                    "setup_ms_excluded_from_replay": (time.perf_counter() - started) * 1000,
                    "model_id": MODEL,
                }
            )
            self.tasks = [asyncio.create_task(self._send()), asyncio.create_task(self._receive())]
        except Exception as exc:
            await self._disconnect()
            status = getattr(exc, "status", None)
            raise RuntimeError(
                f"Scribe v3 Live nicht verbunden ({'HTTP ' + str(status) if status else type(exc).__name__}). "
                "EU-Endpunkt, STT-Berechtigung und Kontingent prüfen. Kein automatischer Neuversuch."
            ) from None

    def feed(self, audio):
        pcm = np.ascontiguousarray((np.clip(audio, -1, 1) * 32767).astype("<i2")).tobytes()

        def enqueue():
            try:
                self.audio_queue.put_nowait(pcm)
            except asyncio.QueueFull:
                self.error = (
                    "Scribe-Audioeingang überlastet; ein kausaler Echtzeitvergleich ist nicht möglich."
                )

        self.loop.call_soon_threadsafe(enqueue)

    async def _send(self):
        pending = bytearray()
        try:
            while True:
                pending.extend(await self.audio_queue.get())
                while len(pending) >= 4096:
                    chunk = bytes(pending[:4096])
                    del pending[:4096]
                    await self.ws.send_json(
                        {
                            "message_type": "input_audio_chunk",
                            "audio_base_64": base64.b64encode(chunk).decode(),
                            "sample_rate": 16000,
                            "commit": False,
                        }
                    )
                    self.submitted_samples += len(chunk) // 2
        except asyncio.CancelledError:
            raise
        except Exception:
            self.error = "Scribe-Audioübertragung fehlgeschlagen. Kein automatischer Neuversuch."

    async def _receive(self):
        try:
            async for message in self.ws:
                if message.type != self.aiohttp.WSMsgType.TEXT:
                    continue
                data = json.loads(message.data)
                kind = data.get("message_type")
                if kind not in {
                    "partial_transcript",
                    "committed_transcript",
                    "committed_transcript_with_timestamps",
                }:
                    self.error = "Scribe hat einen Dienstfehler gemeldet. STT-Berechtigung, Modellzugriff und Kontingent prüfen."
                    return
                probability = data.get("turn_probability") if kind == "partial_transcript" else None
                if probability is not None:
                    probability = float(probability)
                    if not np.isfinite(probability) or not 0 <= probability <= 1:
                        raise ValueError("Invalid turn probability")
                    self.seen_probability = True
                self.events.put(
                    {
                        "provider_event": kind,
                        "score": probability,
                        "text": str(data.get("text", "")),
                        "received_at": time.perf_counter(),
                        "submitted_samples_upper_bound": self.submitted_samples,
                    }
                )
            if not self.closing:
                self.error = "Scribe-Verbindung wurde während der Aufnahme geschlossen."
        except asyncio.CancelledError:
            raise
        except Exception:
            self.error = "Scribe lieferte keine gültigen Streaming-Ergebnisse."

    def poll(self):
        if self.error:
            raise RuntimeError(self.error)
        results = []
        while True:
            try:
                results.append(self.events.get_nowait())
            except queue.Empty:
                return results

    def validate_observation(self):
        if self.error:
            raise RuntimeError(self.error)
        if not self.seen_probability:
            raise RuntimeError(
                "Scribe lieferte keine turn_probability. Der Lauf bestätigt keine semantische Turn-Erkennung."
            )

    def close(self):
        try:
            self._call(self._disconnect(), timeout=10)
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=5)
            self.loop.close()
