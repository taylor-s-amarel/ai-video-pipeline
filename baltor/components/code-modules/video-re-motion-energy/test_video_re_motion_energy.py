import shutil

import numpy as np
import pytest

import video_re_motion_energy as m
import video_re_synth as synth

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
W, H = 160, 288


def moving_subject_frames(n=40):
    bg = np.full((H, W, 3), 60, np.uint8)
    for i in range(n):
        f = bg.copy()
        x = 50 + int(20 * np.sin(i / 3.0))
        f[120:170, x:x + 40] = (240, 200, 40)
        yield f


def moving_background_static_panel_frames(n=40):
    for i, f in enumerate(synth.pan_frames(n, (W, H), dx_per_frame=3)):
        f = f.copy()
        f[90:200, 40:120] = (30, 30, 30)  # opaque static panel in the centre
        yield f


@ffmpeg
def test_subject_motion_is_central(tmp_path):
    p = synth.encode_frames(tmp_path / "subj.mkv", moving_subject_frames(), 25, (W, H), codec="ffv1")
    res = m.run(str(p))
    shot = res["shots"][0]
    assert shot["center"] > 1.0 and shot["border"] < 0.2
    assert res["summary"]["background_moving_ratio"] == 0.0


@ffmpeg
def test_background_motion_is_in_the_border(tmp_path):
    p = synth.encode_frames(tmp_path / "bg.mkv", moving_background_static_panel_frames(), 25, (W, H), codec="ffv1")
    res = m.run(str(p))
    shot = res["shots"][0]
    assert shot["border"] > shot["center"] > 0
    assert res["summary"]["background_moving_ratio"] == 1.0
    assert res["summary"]["still_ratio"] == 0.0


def test_pairs_across_a_cut_are_excluded():
    frames = [np.zeros((10, 10), np.uint8)] * 5 + [np.full((10, 10), 200, np.uint8)] * 5
    times = [i / 10 for i in range(10)]
    series = m.pair_series(frames, times)
    shots = [{"index": 0, "start_s": 0.0, "end_s": 0.5}, {"index": 1, "start_s": 0.5, "end_s": 1.0}]
    res = m.summarise(series, shots, fps=10)
    assert res["shots"][0]["whole"] == 0 and res["shots"][1]["whole"] == 0
    assert series["whole"].max() == 200


def test_center_mask_covers_36_percent():
    assert m.center_mask(100, 100).mean() == pytest.approx(0.36)
