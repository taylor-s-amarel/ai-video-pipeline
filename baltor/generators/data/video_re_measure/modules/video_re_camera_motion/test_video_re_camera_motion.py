import shutil

import numpy as np
import pytest

import video_re_camera_motion as m
import video_re_synth as synth

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
SIZE = (320, 180)


def measure(tmp_path, name, frames, size=SIZE):
    p = synth.encode_frames(tmp_path / f"{name}.mp4", frames, 25, size)
    res = m.run(str(p))
    assert res["status"] == "ok"
    return res["shots"][0]


@ffmpeg
def test_pan_right_has_positive_pan_x_and_right_magnitude(tmp_path):
    shot = measure(tmp_path, "panr", synth.pan_frames(40, SIZE, dx_per_frame=2.0))
    assert shot["pan_x"] == pytest.approx(2.0 * 25 / 320, rel=0.1)
    assert abs(shot["pan_y"]) < 0.01 and abs(shot["zoom"]) < 0.01
    assert shot["label"] == "pan-right"


@ffmpeg
def test_pan_left_and_tilt_down_signs(tmp_path):
    shot = measure(tmp_path, "panl", synth.pan_frames(40, SIZE, dx_per_frame=-3.0, dy_per_frame=1.5))
    assert shot["pan_x"] < 0 and shot["pan_y"] > 0
    assert shot["pan_y"] == pytest.approx(1.5 * 25 / 180, rel=0.1)
    assert shot["label"] == "pan-left+tilt-down"


@ffmpeg
def test_zoom_in_and_out(tmp_path):
    zin = measure(tmp_path, "zin", synth.zoom_frames(40, SIZE, 0.004))
    zout = measure(tmp_path, "zout", synth.zoom_frames(40, SIZE, -0.01))
    assert zin["zoom"] == pytest.approx(0.1, rel=0.3) and zin["label"] == "zoom-in"
    assert zout["zoom"] == pytest.approx(-0.25, rel=0.3) and zout["label"] == "zoom-out"
    assert abs(zin["pan_x"]) < 0.01


@ffmpeg
def test_static_flat_shot_is_unknown_not_invented(tmp_path):
    flat = (np.full((180, 320, 3), 90, np.uint8) for _ in range(20))
    shot = measure(tmp_path, "flat", flat)
    assert shot["pan_x"] is None and shot["label"] == "unknown"


def test_phase_correlation_sign_convention():
    rng = np.random.default_rng(0)
    a = rng.random((64, 64))
    b = np.roll(a, 5, axis=1)  # content moved right by 5 px
    dx, dy, peak = m.phase_correlate(a, b)
    assert dx == pytest.approx(5, abs=0.2) and abs(dy) < 0.2 and peak > 0.5


def test_labels():
    assert m.label_for(0.0, 0.0, 0.0) == "static"
    assert m.label_for(0.05, 0.0, 0.03) == "pan-right+zoom-in"
    assert m.label_for(None, None, None) == "unknown"
