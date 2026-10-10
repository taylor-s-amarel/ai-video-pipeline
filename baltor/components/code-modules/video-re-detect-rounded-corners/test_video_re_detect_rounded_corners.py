import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_rounded_corners as det

HERE = Path(__file__).resolve().parent


def moving_bg(n, h, w, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (n, h, w, 3)).astype(np.float32)


def with_panel(radius, rect=(60, 50, 160, 100), n=6, seed=0, colour=(240, 200, 40)):
    h, w = 240, 320
    f = moving_bg(n, h, w, seed)
    m = core.rounded_rect_mask(h, w, *rect, radius)
    f[:, m] = np.array(colour, np.float32)
    return f.astype(np.uint8)


def run(frames, **params):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 0.5,
                                   params=params, defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env["payload"]


def test_radius_20_card():
    p = run(with_panel(20))
    assert len(p["elements"]) == 1
    e = p["elements"][0]
    assert e["shape"] == "rounded" and abs(e["radius_px"] - 20) <= 2
    assert e["bbox"] == [60, 50, 160, 100]


def test_square_card_is_rect():
    e = run(with_panel(0, seed=1))["elements"][0]
    assert e["shape"] == "rect" and e["radius_px"] < 1.5


def test_pill_shape():
    e = run(with_panel(30, rect=(40, 90, 240, 60), seed=2))["elements"][0]
    assert e["shape"] == "pill" and abs(e["radius_px"] - 30) <= 3


def test_given_rect_with_edges_on_moving_content():
    # a rounded frame line (static white outline) around moving content inside, background moving too
    f = moving_bg(6, 240, 320, seed=3)
    outer = core.rounded_rect_mask(240, 320, 60, 50, 160, 120, 24)
    inner = core.rounded_rect_mask(240, 320, 63, 53, 154, 114, 21)
    f[:, outer & ~inner] = 255
    e = run(f.astype(np.uint8), rects=[[60, 50, 160, 120]])["elements"][0]
    assert e["source"] == "given" and abs(e["radius_px"] - 24) <= 3


def test_no_elements_in_plain_motion():
    p = run(moving_bg(6, 120, 160, seed=4).astype(np.uint8))
    assert p["elements"] == []


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "r.mkv", with_panel(16, n=5, seed=5), fps=2)
    out = tmp_path / "e.json"
    assert det.main([clip, "--width", "0", "--fps", "0", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert abs(env["payload"]["elements"][0]["radius_px"] - 16) <= 2
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
