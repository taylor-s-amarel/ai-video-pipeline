import shutil
import subprocess

import numpy as np
import pytest

from video_fingerprint import dhash_gray, fingerprint_frames, fingerprint_video, similarity


def test_dhash_stable_under_brightness_shift():
    rng = np.random.default_rng(0)
    f = rng.integers(0, 200, (64, 72)).astype(np.uint8)
    assert dhash_gray(f) == dhash_gray(f + 20)


def test_similarity_logic():
    a = {"duration": 60.0, "hashes": ["0f0f0f0f0f0f0f0f"] * 10}
    b = {"duration": 60.5, "hashes": ["0f0f0f0f0f0f0f0e"] * 10}
    c = {"duration": 60.0, "hashes": ["f0f0f0f0f0f0f0f0"] * 10}
    assert similarity(a, b)["same_video"]
    assert not similarity(a, c)["same_video"]
    assert not similarity(a, {"duration": 30.0, "hashes": a["hashes"]})["same_video"]
    with pytest.raises(ValueError):
        similarity({"duration": 1, "hashes": []}, a)


def test_frames_api():
    assert len(fingerprint_frames([np.zeros((10, 10)), np.ones((10, 10, 3))])) == 2


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg missing")
def test_reencode_matches_other_video_does_not(tmp_path):
    a, a2, b = tmp_path / "a.mp4", tmp_path / "a2.mp4", tmp_path / "b.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:d=3:r=10",
                    "-pix_fmt", "yuv420p", str(a)], check=True, timeout=60)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(a), "-vf", "scale=160:90", "-crf", "35", str(a2)],
                   check=True, timeout=60)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "mandelbrot=s=320x180:r=10", "-t", "3",
                    "-pix_fmt", "yuv420p", str(b)], check=True, timeout=60)
    fa, fa2, fb = (fingerprint_video(str(p)) for p in (a, a2, b))
    assert similarity(fa, fa2)["same_video"]
    assert not similarity(fa, fb)["same_video"]
