import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_safe_margin_usage as det

HERE = Path(__file__).resolve().parent


def smooth_moving(n, h, w, seed=0):
    rng = np.random.default_rng(seed)
    big = core.blur(rng.uniform(0, 255, (h + 40, w + 10 * n)).astype(np.float32), 8)
    big = (big - big.min()) / (big.max() - big.min()) * 180 + 40
    return np.stack([np.repeat(big[20:20 + h, 10 * i:10 * i + w, None], 3, -1) for i in range(n)])


def glyphs(h, w, seed=1):
    rng = np.random.default_rng(seed)
    g = np.full((h, w), 255, np.float32)
    for x in range(0, w - 6, 9):
        top = rng.integers(0, 4)
        g[top:h - rng.integers(0, 4), x:x + 5] = 0
    return g


def with_caption(n=8, h=640, w=360, left=24, bottom=30, cw=236, ch=40, seed=0):
    f = smooth_moving(n, h, w, seed)
    y = h - bottom - ch
    f[:, y:y + ch, left:left + cw] = glyphs(ch, cw)[None, ..., None]
    return f.astype(np.uint8)


def run(frames, info=None, **params):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 0.5,
                                   info=info, params=params, defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env


def test_caption_margins():
    p = run(with_caption())["payload"]
    m = p["min_margin_px"]
    assert abs(m["bottom"] - 30) <= 3 and abs(m["left"] - 24) <= 3
    assert abs(m["right"] - (360 - 24 - 236)) <= 6 and m["top"] > 500
    assert abs(p["min_margin_ratio"]["bottom"] - 30 / 640) < 0.01


def test_no_overlay_on_moving_background():
    env = run(smooth_moving(8, 320, 180, seed=3).astype(np.uint8))
    assert env["payload"]["min_margin_px"] is None


def test_regions_input_from_evidence(tmp_path):
    ev = {"text_regions": [{"t_s": 1.0, "bbox": [100, 1700, 880, 120], "area_ratio": 0.05, "y_center_ratio": 0.9},
                           {"t_s": 2.5, "bbox": [60, 1500, 600, 90], "area_ratio": 0.03, "y_center_ratio": 0.8}]}
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(ev))
    p = run(np.zeros((2, 64, 36, 3), np.uint8), info={"width": 1080, "height": 1920}, regions=str(path))["payload"]
    assert p["source"] == "regions"
    assert p["min_margin_px"] == {"top": 1500, "bottom": 100, "left": 60, "right": 100}
    assert p["closest_t_s"]["bottom"] == 1.0


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "s.mkv", with_caption(n=8, h=320, w=180, left=12, bottom=16, cw=120, ch=24), fps=2)
    out = tmp_path / "e.json"
    assert det.main([clip, "--width", "0", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert abs(env["payload"]["min_margin_px"]["bottom"] - 16) <= 3
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
