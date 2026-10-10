import sys
import types
import wave

import numpy as np
import pytest

from piper_tts_adapter import PiperEngine, cli_argv


def install_fake(monkeypatch, seen):
    mod = types.ModuleType("piper")

    class SynthesisConfig:
        def __init__(self, length_scale=1.0):
            self.length_scale = length_scale

    class PiperVoice:
        @staticmethod
        def load(path):
            seen.append(("load", path))
            return PiperVoice()

        def synthesize_wav(self, text, wav_file, syn_config=None):
            seen.append(("synth", text, getattr(syn_config, "length_scale", None)))
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes((np.ones(2205) * 1000).astype("<i2").tobytes())

    mod.PiperVoice, mod.SynthesisConfig = PiperVoice, SynthesisConfig
    monkeypatch.setitem(sys.modules, "piper", mod)


def test_api_path_and_speed(tmp_path, monkeypatch):
    seen = []
    install_fake(monkeypatch, seen)
    model = tmp_path / "en_US-lessac-medium.onnx"
    model.write_bytes(b"x")
    eng = PiperEngine(str(model))
    sp = eng.synthesize("Hello.", speed=1.25)
    assert sp.sample_rate == 22050 and abs(len(sp.samples) - 2205) == 0
    assert seen[-1] == ("synth", "Hello.", 0.8)
    eng.synthesize("Plain.")
    assert seen[-1] == ("synth", "Plain.", None)


def test_cli_argv_keeps_text_as_one_operand():
    argv = cli_argv("en_US-lessac-medium", "o.wav", "--help; rm -rf /", python="python3")
    assert argv == ["python3", "-m", "piper", "-m", "en_US-lessac-medium", "-f", "o.wav", "--", "--help; rm -rf /"]


def test_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        PiperEngine(str(tmp_path / "missing.onnx")).synthesize("x")
    with pytest.raises(ValueError):
        PiperEngine("x").synthesize("")
