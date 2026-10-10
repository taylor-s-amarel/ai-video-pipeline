import sys
import types

import numpy as np
import pytest

from pocket_tts_adapter import ENGLISH_VOICES, PocketTTSEngine


class FakeTensor:
    def __init__(self, a):
        self.a = a

    def numpy(self):
        return self.a


def install_fake(monkeypatch, log):
    mod = types.ModuleType("pocket_tts")

    class TTSModel:
        sample_rate = 24000

        @classmethod
        def load_model(cls):
            log.append("load")
            return cls()

        def get_state_for_audio_prompt(self, voice):
            log.append(("voice", voice))
            return {"voice": voice}

        def generate_audio(self, state, text):
            log.append(("gen", state["voice"], text))
            return FakeTensor(np.full(1200, 0.2, np.float32))

    mod.TTSModel = TTSModel
    monkeypatch.setitem(sys.modules, "pocket_tts", mod)


def test_api_and_caching(monkeypatch):
    log = []
    install_fake(monkeypatch, log)
    eng = PocketTTSEngine()
    a = eng.synthesize("Hello.")
    eng.synthesize("Again.")
    assert a.sample_rate == 24000 and len(a.samples) == 1200
    assert log.count("load") == 1 and log.count(("voice", "alba")) == 1


def test_speed_and_text_validation(monkeypatch):
    install_fake(monkeypatch, [])
    with pytest.raises(ValueError, match="atempo"):
        PocketTTSEngine().synthesize("x", speed=1.2)
    with pytest.raises(ValueError):
        PocketTTSEngine().synthesize(" ")
    assert "alba" in ENGLISH_VOICES
