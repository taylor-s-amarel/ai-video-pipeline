import shutil
import subprocess

import numpy as np
import pytest

from auto_levels import apply, compute, ffmpeg_colorlevels


def dull(lo=60, hi=180, shape=(40, 100)):
    x = np.tile(np.linspace(lo, hi, shape[1]), (shape[0], 1))
    return np.stack([x, x, x], -1).astype(np.uint8)


def test_stretches_range():
    img = dull()
    p = compute(img, low=0, high=100)
    out = apply(img, p)
    assert out.min() <= 2 and out.max() >= 253


def test_midtone_gamma_moves_median():
    img = dull(0, 255)
    img = (255 * (img / 255.0) ** 2).astype(np.uint8)    # darkened midtones
    p = compute(img, target_mid=0.5)
    out = apply(img, p)
    assert p["gamma"] < 1 and abs(np.median(out) - 128) < abs(np.median(img) - 128)


def test_flat_image_untouched_and_errors():
    flat = np.full((5, 5, 3), 100, np.uint8)
    assert np.array_equal(apply(flat, compute(flat)), flat)
    with pytest.raises(ValueError):
        compute(flat, mode="hsv")
    assert ffmpeg_colorlevels({"low": [51] * 3, "high": [204] * 3, "gamma": 1.0}).startswith("colorlevels=rimin=0.2000")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_ffmpeg_filter_runs():
    vf = ffmpeg_colorlevels(compute(dull(), target_mid=0.5))
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=32x32:d=0.1:r=10",
                        "-vf", vf, "-f", "null", "-"], capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
