from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    models: list[Literal["baseline", "livekit", "smart_turn", "scribe"]] = Field(
        default_factory=lambda: ["baseline", "livekit", "smart_turn"], min_length=1, max_length=4
    )
    baseline_timeouts_ms: list[int] = Field(
        default_factory=lambda: [500, 1000, 1500], min_length=1, max_length=8
    )
    mode: Literal["realtime", "offline"] = "realtime"
    parallelism: int = Field(default=1, ge=1, le=6)
    vad_threshold: float = Field(default=0.5, gt=0, lt=1)
    min_silence_ms: int = Field(default=300, ge=250, le=1500)
    inference_interval_ms: int = Field(default=100, ge=50, le=1000)
    max_silence_ms: int = Field(default=5000, ge=1500, le=5000)
    livekit_threshold: float | None = Field(default=None, gt=0, lt=1)
    livekit_version: Literal["v1", "v1-mini"] = "v1"
    smart_turn_threshold: float = Field(default=0.5, gt=0, lt=1)
    scribe_threshold: float = Field(default=0.9, gt=0, lt=1)

    @model_validator(mode="after")
    def consistency(self):
        if len(set(self.models)) != len(self.models):
            raise ValueError("Modelle dürfen nicht doppelt vorkommen.")
        if any(not 250 <= n <= 5000 for n in self.baseline_timeouts_ms) or len(
            set(self.baseline_timeouts_ms)
        ) != len(self.baseline_timeouts_ms):
            raise ValueError(
                "Baseline-Stillezeiten müssen verschieden sein und zwischen 250 und 5000 ms liegen."
            )
        if self.min_silence_ms > self.max_silence_ms:
            raise ValueError("Die Mindestpause darf den maximalen Timeout nicht überschreiten.")
        if "livekit" in self.models and self.livekit_version == "v1" and self.mode != "realtime":
            raise ValueError(
                "LiveKit v1 Cloud benötigt Echtzeitmodus. Für Offline-Tests v1-mini auswählen oder LiveKit abwählen."
            )
        if "scribe" in self.models and self.mode != "realtime":
            raise ValueError("Scribe v3 Live benötigt Echtzeitmodus für den Streaming-Vergleich.")
        return self
