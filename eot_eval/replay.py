"""Frame release stays independent from semantic inference; no gold input here."""

import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from eot_eval.models import timed_score

RATE = 16000
FRAME = 512


def replay(audio, vad, config, model=None, timeout_ms=None, sink=None):
    events = []

    def emit(kind, **values):
        event = {"event": kind, **values}
        if sink:
            sink(event)
        events.append(event)

    realtime = config.mode == "realtime"
    streaming = model is not None and hasattr(model, "poll")
    if streaming and not realtime:
        raise ValueError("Streaming-Dienste benötigen Echtzeit-Replay.")
    vad.reset()
    if model is not None:
        if hasattr(model, "warmup"):
            model.warmup()
        else:
            model.score(np.zeros(RATE, dtype=np.float32))  # excluded local warm-up
        if hasattr(model, "reset"):
            model.reset()
    started = time.perf_counter()
    pending = None
    pending_epoch = None
    pending_sample = None
    epoch = 0
    in_speech = False
    speech_seen = False
    last_speech = 0
    last_query = -10 * RATE
    inference_ms = []
    server_e2e_ms = []
    vad_ms = []
    skipped = 0
    committed = None
    latest_stream_score = None
    pause_started = None
    error = None
    pool = ThreadPoolExecutor(max_workers=1)

    def commit(cursor, trigger, score=None):
        nonlocal committed
        elapsed = (time.perf_counter() - started) * 1000 if realtime else cursor * 1000 / RATE
        committed = {"commit_ms": elapsed, "trigger": trigger, "score": score}
        emit("commit", audio_sample=cursor, **committed)

    def consume(result, cursor, generation, source_sample):
        duration = (result["finished"] - result["started"]) * 1000
        inference_ms.append(duration)
        if result.get("sdk_server_e2e_ms") is not None:
            server_e2e_ms.append(result["sdk_server_e2e_ms"])
        stale = generation != epoch or in_speech
        is_livekit = model.metadata["name"].startswith("LiveKit")
        threshold = config.livekit_threshold if is_livekit else config.smart_turn_threshold
        if threshold is None:
            threshold = result.get("eot_threshold")
            if threshold is None:
                raise RuntimeError("Keine automatische LiveKit-Schwelle verfügbar.")
        emit(
            "score",
            audio_sample=source_sample,
            observed_sample=cursor,
            available_ms=(result["finished"] - started) * 1000,
            inference_ms=duration,
            score=result["score"],
            stale=stale,
            sdk_server_e2e_ms=result.get("sdk_server_e2e_ms"),
            eot_threshold=threshold,
        )
        if not stale and result["score"] >= threshold:
            commit(cursor, "semantic", result["score"])

    try:
        for cursor in range(FRAME, len(audio) + 1, FRAME):
            if realtime:
                delay = started + cursor / RATE - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)
            before = time.perf_counter()
            if model is not None and hasattr(model, "feed"):
                model.feed(audio[cursor - FRAME : cursor])
            probability = vad.probability(audio[cursor - FRAME : cursor])
            vad_ms.append((time.perf_counter() - before) * 1000)
            speech = probability >= config.vad_threshold
            if speech:
                if not in_speech:
                    epoch += 1
                speech_seen = True
                last_speech = cursor
            if speech != in_speech:
                pause_started = time.perf_counter() if not speech else None
                latest_stream_score = None
                emit("vad_transition", audio_sample=cursor, speech=speech, probability=probability)
            in_speech = speech
            silence_ms = (cursor - last_speech) * 1000 / RATE
            if streaming:
                for update in model.poll():
                    stale = speech or pause_started is None or update["received_at"] < pause_started
                    if update["score"] is not None:
                        emit(
                            "stream_score",
                            observed_sample=cursor,
                            available_ms=(update["received_at"] - started) * 1000,
                            score=update["score"],
                            eot_threshold=config.scribe_threshold,
                            stale=stale,
                            provider_event=update["provider_event"],
                            text=update["text"],
                            submitted_samples_upper_bound=update["submitted_samples_upper_bound"],
                        )
                        if not stale:
                            latest_stream_score = update["score"]
                    else:
                        emit(
                            "provider_transcript",
                            observed_sample=cursor,
                            provider_event=update["provider_event"],
                            text=update["text"],
                        )
                if (
                    speech_seen
                    and not speech
                    and silence_ms >= config.min_silence_ms
                    and latest_stream_score is not None
                    and latest_stream_score >= config.scribe_threshold
                ):
                    commit(cursor, "semantic", latest_stream_score)
                    break
            if model is not None and speech_seen and not speech and silence_ms >= config.max_silence_ms:
                commit(cursor, "fallback_timeout")
                break
            if pending is not None and pending.done():
                consume(pending.result(), cursor, pending_epoch, pending_sample)
                pending = None
                if committed:
                    break
            if not speech_seen or speech:
                continue
            if model is None:
                if silence_ms >= timeout_ms:
                    commit(cursor, "silence_timeout")
                    break
                continue
            if streaming:
                continue  # Scores arrive continuously; do not fabricate per-call inference times.
            if (
                silence_ms < config.min_silence_ms
                or (cursor - last_query) * 1000 / RATE < config.inference_interval_ms
            ):
                continue
            if pending is not None:
                skipped += 1
                continue
            last_query = cursor
            # Immutable copy is the entire input contract: no path, future samples, or labels.
            prefix = np.array(audio[:cursor], dtype=np.float32, copy=True)
            if realtime:
                pending_epoch, pending_sample = epoch, cursor
                pending = pool.submit(timed_score, model, prefix)
            else:
                consume(timed_score(model, prefix), cursor, epoch, cursor)
                if committed:
                    break
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        emit("error", message=error)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        if streaming and hasattr(model, "validate_observation"):
            try:
                model.validate_observation()
            except Exception as exc:
                if error is None:
                    error = f"{type(exc).__name__}: {exc}"
                    emit("error", message=error)
        if pending is not None and not pending.cancelled():
            try:
                unused = pending.result()
                duration = (unused["finished"] - unused["started"]) * 1000
                inference_ms.append(duration)
                emit(
                    "unused_score",
                    audio_sample=pending_sample,
                    score=unused["score"],
                    inference_ms=duration,
                    reason="commit_or_observation_end",
                )
            except Exception as exc:
                emit("unused_score_error", message=f"{type(exc).__name__}: {exc}")
                if error is None:
                    error = f"{type(exc).__name__}: {exc}"
    elapsed = (time.perf_counter() - started) * 1000
    return {
        **(committed or {"commit_ms": None, "trigger": "missing", "score": None}),
        "mode": config.mode,
        "error": error,
        "inference_ms": inference_ms,
        "sdk_server_e2e_ms": server_e2e_ms,
        "inference_measure": getattr(model, "metadata", {}).get("inference_measure", "local_adapter"),
        "vad_total_ms": sum(vad_ms),
        "skipped_queries": skipped,
        "runtime_ms": elapsed,
        "events": events,
    }
