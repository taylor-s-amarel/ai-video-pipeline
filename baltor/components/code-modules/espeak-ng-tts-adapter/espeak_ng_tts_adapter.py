"""espeak-ng adapter: always-available, robotic but intelligible fallback TTS.

Runs ``espeak-ng`` as a subprocess (no shell) with the text on stdin, so text
that starts with '-' or contains quotes cannot be read as options. Options:
voice (``-v``), speed in words per minute (``-s``), pitch 0-99 (``-p``),
amplitude 0-200 (``-a``), word gap in 10 ms units (``-g``) and SSML input
(``-m``). Output WAV is read back into float32 samples.

Usage::

    from espeak_ng_tts_adapter import EspeakEngine
    eng = EspeakEngine(voice="en-us", wpm=155)
    speech = eng.synthesize("Hello there.")
"""

from __future__ import annotations

import io
import shutil
import subprocess
import wave
from dataclasses import dataclass

import numpy as np


@dataclass
class Speech:
    samples: np.ndarray
    sample_rate: int


class EspeakEngine:
    name = "espeak-ng"

    def __init__(self, voice: str = "en-us", wpm: int = 160, pitch: int = 50, amplitude: int = 100,
                 word_gap: int = 0, ssml: bool = False, binary: str = "espeak-ng"):
        if not 80 <= wpm <= 450:
            raise ValueError("wpm must be within 80-450")
        if not 0 <= pitch <= 99 or not 0 <= amplitude <= 200:
            raise ValueError("pitch must be 0-99 and amplitude 0-200")
        self.voice, self.wpm, self.pitch, self.amplitude = voice, wpm, pitch, amplitude
        self.word_gap, self.ssml, self.binary = word_gap, ssml, binary

    def argv(self, voice: str | None = None, speed: float = 1.0) -> list[str]:
        v = voice or self.voice
        if not v or v.startswith("-") or any(c.isspace() for c in v):
            raise ValueError(f"bad voice name {v!r}")
        wpm = int(round(self.wpm * speed))
        args = [self.binary, "-v", v, "-s", str(wpm), "-p", str(self.pitch), "-a", str(self.amplitude),
                "-g", str(self.word_gap), "--stdout", "--stdin"]
        if self.ssml:
            args.insert(1, "-m")
        return args

    def synthesize(self, text: str, voice: str | None = None, speed: float = 1.0) -> Speech:
        if not text.strip():
            raise ValueError("empty text")
        if not shutil.which(self.binary):
            raise RuntimeError(f"{self.binary} is not installed (apt install espeak-ng)")
        proc = subprocess.run(self.argv(voice, speed), input=text.encode("utf-8"), capture_output=True,
                              timeout=120, check=True)
        with wave.open(io.BytesIO(proc.stdout), "rb") as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768.0
            return Speech(pcm, w.getframerate())
