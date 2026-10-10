import shutil
import subprocess

import numpy as np
import pytest

from vignette_mask import apply, ffmpeg_vignette, vignette


def test_mask_shape_and_range():
    m = vignette(200, 100, strength=0.4, inner=0.3, outer=1.0)
    assert m[50, 100] == pytest.approx(1.0)
    assert m[0, 0] == pytest.approx(0.6, abs=0.02)
    assert m.min() >= 0.6 - 1e-6 and m.max() <= 1.0


def test_apply():
    f = np.full((100, 200, 3), 200, np.uint8)
    out = apply(f, vignette(200, 100, 0.5))
    assert out[50, 100, 0] == 200 and out[0, 0, 0] < 200
    with pytest.raises(ValueError):
        apply(f, vignette(10, 10))


def test_validation_and_filter():
    with pytest.raises(ValueError):
        vignette(10, 10, strength=2)
    with pytest.raises(ValueError):
        vignette(10, 10, inner=1, outer=0.5)
    assert ffmpeg_vignette(36) == "vignette=angle=0.62832"
    with pytest.raises(ValueError):
        ffmpeg_vignette(95)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_ffmpeg_vignette_darkens_corners():
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=white:s=64x64:d=0.1:r=10",
                        "-vf", ffmpeg_vignette(45) + ",format=gray", "-frames:v", "1", "-f", "rawvideo", "-"],
                       capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    img = np.frombuffer(r.stdout, np.uint8).reshape(64, 64)
    assert img[0, 0] < img[32, 32]
