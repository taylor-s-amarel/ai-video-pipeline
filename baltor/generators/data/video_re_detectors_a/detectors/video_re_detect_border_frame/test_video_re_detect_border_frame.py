import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_border_frame as det

HERE = Path(__file__).resolve().parent


def moving(n, h, w, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (n, h, w, 3), dtype=np.uint8)


def framed(n=8, h=240, w=340, bw=20, colour=(30, 60, 200), radius=0, seed=0, top=None):
    f = np.empty((n, h, w, 3), np.uint8)
    f[:] = np.array(colour, np.uint8)
    if top is not None:
        f[:, :, :] = top
    inside = core.rounded_rect_mask(h, w, bw, bw, w - 2 * bw, h - 2 * bw, radius)
    content = moving(n, h, w, seed)
    f[:, inside] = content[:, inside]
    return f


def run(frames):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 0.5,
                                   defaults=det.DEFAULTS)
    errs = core.check_envelope(env, HERE)
    assert errs in ([], ["jsonschema not installed"]), errs
    return env


def test_solid_border_with_rounded_inner_corners():
    p = run(framed(radius=24))["payload"]
    assert p["detected"]
    b = p["border"]
    for s in ("top", "right", "bottom", "left"):
        assert abs(b[s] - 20) <= 1
    assert b["style"] == "solid" and b["color"] == "#1E3CC8"
    assert abs(b["inner_radius_px"] - 24) <= 3


def test_square_inner_corners_have_zero_radius():
    b = run(framed(radius=0, seed=1))["payload"]["border"]
    assert b["inner_radius_px"] <= 1.0


def test_vertical_gradient_border():
    h, w = 240, 340
    ramp = np.linspace(0, 1, h)[:, None, None]
    top = (np.array([250, 120, 20]) * (1 - ramp) + np.array([20, 40, 160]) * ramp).astype(np.uint8)
    top = np.broadcast_to(top, (h, w, 3))
    b = run(framed(top=top, seed=2))["payload"]["border"]
    assert b["style"] == "gradient"
    assert 80 <= b["gradient"]["angle_deg"] <= 100  # pointing down the frame
    assert b["gradient"]["from"].startswith("#F") or b["gradient"]["from"].startswith("#E")


def test_full_frame_motion_has_no_border():
    p = run(moving(8, 200, 300, seed=3))["payload"]
    assert not p["detected"] and p["border"] is None


def test_still_image_is_partial_not_a_border():
    f = np.repeat(moving(1, 120, 160, seed=4), 6, axis=0)
    env = run(f)
    assert env["status"] == "partial" and not env["payload"]["detected"]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "b.mkv", framed(n=6, h=120, w=160, bw=10, seed=5), fps=4)
    out = tmp_path / "e.json"
    assert det.main([clip, "--width", "0", "--fps", "4", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["detected"] and env["payload"]["border"]["top"] == 10
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
