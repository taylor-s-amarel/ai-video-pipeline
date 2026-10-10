"""Piper text-to-speech adapter (piper-tts, GPL-3.0, run as a separate package).

Two ways to run Piper (both verified against the piper1-gpl documentation):

* Python API (``pip install piper-tts``)::

      voice = PiperVoice.load("en_US-lessac-medium.onnx")
      with wave.open("out.wav", "wb") as f:
          voice.synthesize_wav(text, f, syn_config=SynthesisConfig(length_scale=...))

  Speed maps to ``length_scale = 1 / speed`` (larger is slower).
* Command line: ``python3 -m piper -m <voice> -f out.wav -- 'text'``. This
  adapter passes text after ``--`` as one argv element (no shell), so text
  cannot be read as options. The CLI path does not set speed.

Voices are downloaded separately (``python3 -m piper.download_voices
en_US-lessac-medium``). Piper itself is GPL-3.0; this adapter only calls it.

Usage::

    from piper_tts_adapter import PiperEngine, cli_argv
    eng = PiperEngine("voices/en_US-lessac-medium.onnx")
    speech = eng.synthesize("Hello there.", speed=1.05)
"""

from __future__ import annotations

import io
import os
import sys
import wave
from dataclasses import dataclass

import numpy as np


@dataclass
class Speech:
    samples: np.ndarray
    sample_rate: int


def cli_argv(model: str, out_wav: str, text: str, data_dir: str | None = None, python: str | None = None) -> list[str]:
    if "\x00" in text:
        raise ValueError("text may not contain NUL")
    argv = [python or sys.executable, "-m", "piper", "-m", model, "-f", out_wav]
    if data_dir:
        argv += ["--data-dir", data_dir]
    return argv + ["--", text]


def _wav_bytes_to_speech(data: bytes) -> Speech:
    with wave.open(io.BytesIO(data), "rb") as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768.0
        if w.getnchannels() > 1:
            pcm = pcm.reshape(-1, w.getnchannels()).mean(axis=1)
        return Speech(pcm, w.getframerate())


class PiperEngine:
    name = "piper"

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._voice = None

    def _load(self):
        if self._voice is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"{self.model_path} not found; download a voice with "
                                        "python3 -m piper.download_voices <name>")
            try:
                from piper import PiperVoice  # lazy optional dependency (GPL-3.0 package)
            except ImportError as exc:
                raise RuntimeError("piper-tts is not installed: pip install piper-tts") from exc
            self._voice = PiperVoice.load(self.model_path)
        return self._voice

    def synthesize(self, text: str, voice: str | None = None, speed: float = 1.0) -> Speech:
        if not text.strip():
            raise ValueError("empty text")
        if speed <= 0:
            raise ValueError("speed must be > 0")
        v = self._load()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            if abs(speed - 1.0) > 1e-9:
                try:
                    from piper import SynthesisConfig
                except ImportError as exc:
                    raise RuntimeError("this piper version has no SynthesisConfig; use speed=1.0") from exc
                v.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=1.0 / speed))
            else:
                v.synthesize_wav(text, wf)
        return _wav_bytes_to_speech(buf.getvalue())
