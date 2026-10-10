"""Kyutai Pocket TTS adapter (CPU text-to-speech with built-in voices).

Upstream Python API (verified from the project README)::

    model = TTSModel.load_model()
    voice = model.get_state_for_audio_prompt("alba")   # built-in name, wav path or hf:// path
    audio = model.generate_audio(voice, "Hello world.") # 1D torch tensor
    model.sample_rate

The package (``pip install pocket-tts``) and torch are imported lazily.
Loading the model is slow, so the engine keeps it and caches voice states.
Check each voice's licence on the project's voices page before publishing
and credit voices that require attribution.

Usage::

    from pocket_tts_adapter import PocketTTSEngine
    eng = PocketTTSEngine(default_voice="alba")
    speech = eng.synthesize("In 1970, five scientists lived underwater.")
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ENGLISH_VOICES = ("alba", "anna", "azelma", "bill_boerst", "caro_davy", "charles", "cosette", "eponine", "eve",
                  "fantine", "george", "jane", "jean", "javert", "marius", "mary", "michael", "paul",
                  "peter_yearsley", "stuart_bell", "vera")


@dataclass
class Speech:
    samples: np.ndarray
    sample_rate: int


class PocketTTSEngine:
    name = "pocket-tts"

    def __init__(self, default_voice: str = "alba"):
        self.default_voice = default_voice
        self._model = None
        self._voices: dict = {}

    def _load(self):
        if self._model is None:
            try:
                from pocket_tts import TTSModel  # lazy optional dependency
            except ImportError as exc:
                raise RuntimeError("pocket-tts is not installed: pip install pocket-tts") from exc
            self._model = TTSModel.load_model()
        return self._model

    def _voice_state(self, voice: str):
        if voice not in self._voices:
            self._voices[voice] = self._load().get_state_for_audio_prompt(voice)
        return self._voices[voice]

    def synthesize(self, text: str, voice: str | None = None, speed: float = 1.0) -> Speech:
        if not text.strip():
            raise ValueError("empty text")
        if abs(speed - 1.0) > 1e-9:
            raise ValueError("Pocket TTS has no speed control here; time-stretch afterwards (atempo)")
        model = self._load()
        audio = model.generate_audio(self._voice_state(voice or self.default_voice), text)
        arr = audio.numpy() if hasattr(audio, "numpy") else np.asarray(audio)
        return Speech(np.asarray(arr, dtype=np.float32).reshape(-1), int(model.sample_rate))
