import shutil
import subprocess

import pytest

import camera_shake_noise as cs


def test_deterministic_and_bounded():
    a = cs.shake_offsets(60, amplitude_px=10, seed=4)
    b = cs.shake_offsets(60, amplitude_px=10, seed=4)
    assert a == b
    assert all(abs(x) <= 10 and abs(y) <= 10 for x, y, _ in a)
    assert a != cs.shake_offsets(60, amplitude_px=10, seed=5)


def test_noise_is_smooth():
    vals = [cs.value_noise_1d(i / 100) for i in range(300)]
    assert max(abs(b - a) for a, b in zip(vals, vals[1:])) < 0.06


def test_decay_reaches_zero():
    offs = cs.shake_offsets(40, fps=10, decay_s=2.0)
    assert offs[-1] == (0.0, 0.0, 0.0) or max(map(abs, offs[-1])) < 1e-9
    assert offs[0] != (0.0, 0.0, 0.0)


def test_overscan():
    assert cs.overscan_scale(1080, 1920, 0) == pytest.approx(1.0)
    assert cs.overscan_scale(1080, 1920, 20) > 1.0


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_crop_filter_runs():
    vf = cs.ffmpeg_crop_filter(160, 90, 6, 5)
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=160x90:d=0.5:r=25",
                        "-vf", vf, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr
    assert len(r.stdout) == 160 * 90 * 13 or len(r.stdout) % (160 * 90) == 0
