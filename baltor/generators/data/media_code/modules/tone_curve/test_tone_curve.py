import shutil
import subprocess

import numpy as np
import pytest

from tone_curve import PRESETS, Curve


def test_linear_is_identity():
    c = Curve(PRESETS["linear"])
    assert np.array_equal(c.lut(), np.arange(256, dtype=np.uint8))


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_presets_monotonic_and_hit_points(name):
    c = Curve(PRESETS[name])
    lut = c.lut().astype(int)
    assert np.all(np.diff(lut) >= 0)
    for x, y in PRESETS[name]:
        assert float(c(x)) == pytest.approx(y, abs=1e-9)


def test_no_overshoot_with_steep_points():
    c = Curve([(0, 0), (0.1, 0.9), (0.2, 0.92), (1, 1)])
    v = c(np.linspace(0, 1, 1001))
    assert np.all(np.diff(v) >= -1e-12) and v.max() <= 1


def test_validation_and_ffmpeg():
    with pytest.raises(ValueError):
        Curve([(0, 0)])
    with pytest.raises(ValueError):
        Curve([(0, 0), (0, 1)])
    with pytest.raises(ValueError):
        Curve([(0, 0), (1, 1.5)])
    assert Curve(PRESETS["faded"]).ffmpeg() == "curves=all='0/0.08 0.5/0.5 1/0.92'"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_ffmpeg_curves_runs():
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=8x8:d=0.1:r=10",
                        "-vf", Curve(PRESETS["soft_s"]).ffmpeg(), "-f", "null", "-"], capture_output=True, timeout=60,
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
