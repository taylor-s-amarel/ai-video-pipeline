import numpy as np
import pytest

from tts_engine_interface import FallbackTTS, Speech, read_wav, to_mono_float, write_wav


class Fake:
    def __init__(self, name, ok=True, silent=False):
        self.name, self.ok, self.silent = name, ok, silent

    def synthesize(self, text, voice=None, speed=1.0):
        if not self.ok:
            raise OSError("model file missing")
        n = int(24000 * 0.06 * len(text))
        s = np.zeros(n) if self.silent else 0.3 * np.sin(np.arange(n) / 10)
        return Speech(s, 24000)


def test_fallback_order_and_failures():
    tts = FallbackTTS([Fake("kokoro", ok=False), Fake("piper", silent=True), Fake("espeak")])
    sp, used, failures = tts.synthesize("Hello there.")
    assert used == "espeak"
    assert [f[0] for f in failures] == ["kokoro", "piper"]
    assert "silent" in failures[1][1]


def test_all_fail():
    with pytest.raises(RuntimeError, match="all TTS engines failed"):
        FallbackTTS([Fake("a", ok=False)]).synthesize("x")
    with pytest.raises(ValueError):
        FallbackTTS([])


def test_wav_roundtrip(tmp_path):
    sp = Speech(0.5 * np.sin(np.linspace(0, 100, 2400)).astype(np.float32), 24000)
    p = tmp_path / "a.wav"
    write_wav(str(p), sp)
    back = read_wav(str(p))
    assert back.sample_rate == 24000 and abs(back.duration - 0.1) < 1e-9
    assert np.abs(back.samples - sp.samples).max() < 1e-3


def test_to_mono():
    stereo = np.stack([np.ones(10, np.int16) * 16384, np.zeros(10, np.int16)], 1)
    assert np.allclose(to_mono_float(stereo), 0.25)
