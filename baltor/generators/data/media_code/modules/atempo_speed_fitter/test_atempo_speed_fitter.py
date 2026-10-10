import shutil
import subprocess
import wave

import pytest

from atempo_speed_fitter import atempo_chain, command, fit_factor


def test_factor_and_limits():
    assert fit_factor(66, 60) == pytest.approx(1.1)
    with pytest.raises(ValueError, match="re-synthesize"):
        fit_factor(80, 60)
    assert fit_factor(80, 60, max_change=0.5) == pytest.approx(4 / 3)
    with pytest.raises(ValueError):
        fit_factor(0, 1)


def test_chain_stages():
    assert atempo_chain(1.25) == "atempo=1.25"
    assert atempo_chain(3.0) == "atempo=2,atempo=1.5"
    assert atempo_chain(0.3) == "atempo=0.5,atempo=0.6"
    prod = 1.0
    for part in atempo_chain(5.5).split(","):
        prod *= float(part.split("=")[1])
    assert prod == pytest.approx(5.5)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_real_stretch(tmp_path):
    src, dst = tmp_path / "a.wav", tmp_path / "b.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "sine=f=300:d=2:r=16000", str(src)],
                   check=True, timeout=60)
    argv = command(str(src), str(dst), fit_factor(2.0, 1.8))
    subprocess.run(argv[:1] + ["-v", "error"] + argv[1:], check=True, timeout=60)
    with wave.open(str(dst)) as w:
        assert abs(w.getnframes() / w.getframerate() - 1.8) < 0.05
