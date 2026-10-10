import shutil
import subprocess

import numpy as np
import pytest

from first_frame_title_check import check_frame, check_video


def frame(title_y=None, color=(255, 210, 31), w=200, h=356):
    f = np.full((h, w, 3), 40, np.uint8)
    if title_y is not None:
        f[title_y:title_y + 30, 20:180] = color
    return f


def test_upper_title_passes():
    r = check_frame(frame(60))
    assert r["passed"] and abs(r["bbox"][0] - 20) <= 2 and r["centre_y_fraction"] < 0.3


def test_low_title_fails():
    r = check_frame(frame(230))
    assert not r["passed"] and "centre" in r["problems"][0]


def test_missing_or_wrong_colour():
    assert not check_frame(frame())["passed"]
    assert not check_frame(frame(60, color=(255, 255, 255)))["passed"]
    with pytest.raises(ValueError):
        check_frame(np.zeros((10, 10)))


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg missing")
def test_video(tmp_path):
    p = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=0x202020:s=270x480:d=0.5:r=10",
                    "-vf", "drawbox=x=20:y=80:w=230:h=50:color=0xFFD21F:t=fill", "-pix_fmt", "yuv420p", str(p)],
                   check=True, timeout=60)
    assert check_video(str(p), width=270)["passed"]
