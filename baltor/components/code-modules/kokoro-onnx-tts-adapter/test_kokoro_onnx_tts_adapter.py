import sys
import types

import numpy as np
import pytest

from kokoro_onnx_tts_adapter import KokoroEngine


def install_fake(monkeypatch, calls):
    mod = types.ModuleType("kokoro_onnx")

    class Kokoro:
        def __init__(self, model, voices):
            calls.append(("init", model, voices))

        def create(self, text, voice, speed, lang):
            calls.append(("create", text, voice, speed, lang))
            return np.zeros(2400, np.float32) + 0.1, 24000

    mod.Kokoro = Kokoro
    monkeypatch.setitem(sys.modules, "kokoro_onnx", mod)


def test_calls_upstream_api(tmp_path, monkeypatch):
    calls = []
    install_fake(monkeypatch, calls)
    m, v = tmp_path / "kokoro-v1.0.onnx", tmp_path / "voices-v1.0.bin"
    m.write_bytes(b"x")
    v.write_bytes(b"x")
    eng = KokoroEngine(str(m), str(v), default_voice="af_heart")
    sp = eng.synthesize("Hello.", speed=1.1)
    assert sp.sample_rate == 24000 and sp.samples.dtype == np.float32
    assert calls[1] == ("create", "Hello.", "af_heart", 1.1, "en-us")
    eng.synthesize("Again.", voice="am_michael")
    assert sum(1 for c in calls if c[0] == "init") == 1  # model loaded once


def test_missing_files_message(tmp_path):
    eng = KokoroEngine(str(tmp_path / "nope.onnx"), str(tmp_path / "nope.bin"))
    with pytest.raises(FileNotFoundError, match="releases"):
        eng.synthesize("hi")


def test_validation(tmp_path):
    eng = KokoroEngine("a", "b")
    with pytest.raises(ValueError):
        eng.synthesize("  ")
    with pytest.raises(ValueError):
        eng.synthesize("x", speed=0)
