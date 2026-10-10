import shutil
import subprocess

import numpy as np
import pytest

from background_motion_checker import check_frames, check_video, region_mask


def test_static_fails_moving_passes():
    static = np.full((40, 30, 40), 120, np.uint8)
    assert not check_frames(static, 10)["passed"]
    rng = np.random.default_rng(0)
    moving = rng.integers(0, 255, (40, 30, 40)).astype(np.uint8)
    assert check_frames(moving, 10)["passed"]


def test_exclusion_ignores_photo_motion():
    frames = np.full((20, 50, 50), 100, np.uint8)
    frames[::2, 10:40, 10:40] = 200   # only the "photo" area changes
    rep = check_frames(frames, 10, exclude=(0.2, 0.2, 0.6, 0.6))
    assert not rep["passed"] and rep["min_window"] == 0


def test_window_detects_frozen_section():
    rng = np.random.default_rng(1)
    frames = rng.integers(0, 255, (60, 20, 20)).astype(np.uint8)
    frames[30:] = frames[30]
    rep = check_frames(frames, 10, window_s=1.0)
    assert not rep["passed"] and rep["windows"][0]["passed"] and not rep["windows"][-1]["passed"]


def test_mask_validation():
    with pytest.raises(ValueError):
        region_mask(10, 10, (0, 0, 1, 1))


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg missing")
def test_real_videos(tmp_path):
    moving, still = tmp_path / "m.mp4", tmp_path / "s.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=160x284:d=3:r=10",
                    "-pix_fmt", "yuv420p", str(moving)], check=True, timeout=60)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=navy:s=160x284:d=3:r=10",
                    "-pix_fmt", "yuv420p", str(still)], check=True, timeout=60)
    assert check_video(str(moving), width=80)["passed"]
    assert not check_video(str(still), width=80)["passed"]
