"""Kokoro-82M text-to-speech through the kokoro-onnx package (CPU friendly).

kokoro-onnx (MIT) runs the Kokoro model (Apache-2.0) with ONNX Runtime. It
needs two files you download once from the project's releases page:
``kokoro-v1.0.onnx`` and ``voices-v1.0.bin``. The package is imported lazily;
nothing is downloaded by this module.

Upstream usage (verified from the project's example)::

    kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
    samples, sample_rate = kokoro.create(text, voice="af_sarah", speed=1.0, lang="en-us")

Usage::

    from kokoro_onnx_tts_adapter import KokoroEngine
    eng = KokoroEngine("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin", default_voice="af_heart")
    speech = eng.synthesize("In 1970, five scientists lived underwater.", speed=1.0)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

MODEL_FILES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases"


@dataclass
class Speech:
    samples: np.ndarray
    sample_rate: int


class KokoroEngine:
    name = "kokoro-onnx"

    def __init__(self, model_path: str, voices_path: str, default_voice: str = "af_heart", lang: str = "en-us"):
        self.model_path, self.voices_path = model_path, voices_path
        self.default_voice, self.lang = default_voice, lang
        self._kokoro = None

    def _load(self):
        if self._kokoro is None:
            for p in (self.model_path, self.voices_path):
                if not os.path.exists(p):
                    raise FileNotFoundError(f"{p} not found; download the model files from {MODEL_FILES_URL}")
            try:
                from kokoro_onnx import Kokoro  # lazy optional dependency
            except ImportError as exc:
                raise RuntimeError("kokoro-onnx is not installed: pip install kokoro-onnx") from exc
            self._kokoro = Kokoro(self.model_path, self.voices_path)
        return self._kokoro

    def synthesize(self, text: str, voice: str | None = None, speed: float = 1.0) -> Speech:
        if not text.strip():
            raise ValueError("empty text")
        if speed <= 0:
            raise ValueError("speed must be > 0")
        k = self._load()
        samples, sr = k.create(text, voice=voice or self.default_voice, speed=float(speed), lang=self.lang)
        return Speech(np.asarray(samples, dtype=np.float32).reshape(-1), int(sr))
