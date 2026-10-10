"""A common interface for local TTS engines, with a fallback chain.

Every engine adapter returns ``Speech(samples, sample_rate)`` where
``samples`` is a mono float32 numpy array in [-1, 1]. ``FallbackTTS`` tries
engines in order and records why each failed, so a render never silently
switches to a worse voice: the result says which engine produced it.

Usage::

    from tts_engine_interface import FallbackTTS, Speech, write_wav
    tts = FallbackTTS([kokoro_engine, piper_engine, espeak_engine])
    speech, used, failures = tts.synthesize("Hello there.", voice="af_heart", speed=1.0)
    write_wav("line.wav", speech)
"""

from __future__ import annotations

import wave
from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class Speech:
    samples: np.ndarray
    sample_rate: int

    @property
    def duration(self) -> float:
        return len(self.samples) / float(self.sample_rate)


class TTSEngine(Protocol):
    name: str

    def synthesize(self, text: str, voice: str | None = None, speed: float = 1.0) -> Speech: ...


def to_mono_float(samples) -> np.ndarray:
    a = np.asarray(samples)
    if a.dtype == np.int16:
        a = a.astype(np.float32) / 32768.0
    a = a.astype(np.float32)
    if a.ndim == 2:
        a = a.mean(axis=1) if a.shape[1] <= 8 else a.mean(axis=0)
    return np.clip(a.reshape(-1), -1.0, 1.0)


def write_wav(path: str, speech: Speech) -> None:
    pcm = (np.clip(speech.samples, -1, 1) * 32767.0).round().astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(speech.sample_rate))
        w.writeframes(pcm.tobytes())


def read_wav(path: str) -> Speech:
    with wave.open(path, "rb") as w:
        if w.getsampwidth() != 2:
            raise ValueError("only 16-bit PCM WAV is supported here")
        data = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768.0
        ch = w.getnchannels()
        if ch > 1:
            data = data.reshape(-1, ch).mean(axis=1)
        return Speech(data, w.getframerate())


class FallbackTTS:
    def __init__(self, engines: list, min_seconds_per_char: float = 0.02):
        if not engines:
            raise ValueError("need at least one engine")
        self.engines = engines
        self.min_seconds_per_char = min_seconds_per_char

    def synthesize(self, text: str, voice: str | None = None, speed: float = 1.0):
        failures: list[tuple[str, str]] = []
        for eng in self.engines:
            try:
                sp = eng.synthesize(text, voice=voice, speed=speed)
                sp = Speech(to_mono_float(sp.samples), int(sp.sample_rate))
                if sp.duration < self.min_seconds_per_char * len(text.strip()) / max(speed, 1e-6) * 0.25:
                    raise RuntimeError(f"suspiciously short audio ({sp.duration:.2f}s)")
                if not np.isfinite(sp.samples).all() or float(np.abs(sp.samples).max(initial=0)) == 0.0:
                    raise RuntimeError("silent or invalid audio")
                return sp, eng.name, failures
            except Exception as exc:  # noqa: BLE001 - record and try the next engine
                failures.append((getattr(eng, "name", repr(eng)), f"{type(exc).__name__}: {exc}"))
        raise RuntimeError("all TTS engines failed: " + "; ".join(f"{n}: {e}" for n, e in failures))
