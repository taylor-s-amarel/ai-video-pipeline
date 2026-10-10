import shutil

import pytest

from espeak_ng_tts_adapter import EspeakEngine


def test_argv():
    eng = EspeakEngine(voice="en-us", wpm=150, ssml=True)
    a = eng.argv(speed=1.2)
    assert a[:2] == ["espeak-ng", "-m"] and a[a.index("-s") + 1] == "180"
    assert a[-2:] == ["--stdout", "--stdin"]


def test_validation():
    with pytest.raises(ValueError):
        EspeakEngine(wpm=20)
    with pytest.raises(ValueError):
        EspeakEngine(pitch=120)
    with pytest.raises(ValueError):
        EspeakEngine().argv(voice="-w /etc/passwd")
    with pytest.raises(ValueError):
        EspeakEngine().synthesize(" ")


def test_missing_binary_message():
    with pytest.raises(RuntimeError, match="not installed"):
        EspeakEngine(binary="espeak-ng-definitely-missing").synthesize("hi")


@pytest.mark.skipif(not shutil.which("espeak-ng"), reason="espeak-ng not installed")
def test_real_synthesis():
    sp = EspeakEngine().synthesize("-v hello there")
    assert sp.sample_rate > 8000 and len(sp.samples) > sp.sample_rate * 0.3
