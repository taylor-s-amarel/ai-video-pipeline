import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_split_screen_layout as det

HERE = Path(__file__).resolve().parent


def pink(h, w, seed=0):
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.normal(size=(h, w)))
    f = np.sqrt(np.fft.fftfreq(h)[:, None] ** 2 + np.fft.fftfreq(w)[None, :] ** 2)
    f[0, 0] = 1
    img = np.fft.ifft2(F / f ** 1.2).real
    return np.clip((img - img.mean()) / img.std() * 45 + 128, 0, 255)


def moving_pattern(n, h, w, kind, seed):
    out = np.zeros((n, h, w, 3), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    big = pink(h + 4 * n + 8, w + 4 * n + 8, seed)
    tint = np.array([[1, 0.8, 0.6], [0.6, 0.9, 1], [1, 1, 1], [0.7, 1, 0.7]][seed % 4], np.float32)
    for t in range(n):
        if kind == "grating":
            g = 128 + 90 * np.sin(2 * np.pi * (xx * np.cos(seed) + yy * np.sin(seed)) / 14 + t * 0.9)
        else:
            g = big[2 * t:2 * t + h, 3 * t:3 * t + w]
        out[t] = g[..., None] * tint
    return np.clip(out, 0, 255)


def grid2x2(n=8, size=240, gutter=4):
    f = np.full((n, size, size, 3), 20, np.float32)
    half = (size - gutter) // 2
    kinds = ["noise", "grating", "noise", "grating"]
    for k, (ox, oy) in enumerate([(0, 0), (half + gutter, 0), (0, half + gutter), (half + gutter, half + gutter)]):
        f[:, oy:oy + half, ox:ox + half] = moving_pattern(n, half, half, kinds[k], seed=k + 1)
    return f.astype(np.uint8)


def run(frames):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 0.5,
                                   defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env["payload"]


def test_2x2_grid_with_gutter():
    p = run(grid2x2())
    assert p["layout"] == "2x2" and len(p["panels"]) == 4
    expected = [(0, 0), (122, 0), (0, 122), (122, 122)]
    for panel, (ex, ey) in zip(p["panels"], expected):
        assert abs(panel["x"] - ex) <= 3 and abs(panel["y"] - ey) <= 3
        assert abs(panel["w"] - 118) <= 3 and abs(panel["h"] - 118) <= 3
    assert 2 <= p["gutter_px"] <= 6


def test_stacked_2x1_without_gutter():
    f = np.zeros((8, 320, 180, 3), np.float32)
    f[:, :160] = moving_pattern(8, 160, 180, "noise", 5)
    f[:, 160:] = moving_pattern(8, 160, 180, "noise", 6)
    p = run(f.astype(np.uint8))
    assert p["layout"] == "2x1" and p["rows"] == 2 and p["cols"] == 1
    assert abs(p["panels"][1]["y"] - 160) <= 2


def test_three_up_one_plus_two():
    f = np.zeros((8, 240, 320, 3), np.float32)
    f[:, :, :160] = moving_pattern(8, 240, 160, "noise", 7)
    f[:, :120, 160:] = moving_pattern(8, 120, 160, "grating", 8)
    f[:, 120:, 160:] = moving_pattern(8, 120, 160, "noise", 9)
    p = run(f.astype(np.uint8))
    assert p["layout"] == "3-up" and len(p["panels"]) == 3


def test_single_moving_picture_is_single():
    p = run(moving_pattern(8, 240, 240, "noise", 11).astype(np.uint8))
    assert p["layout"] == "single" and len(p["panels"]) == 1


def test_static_stripes_are_texture_not_layout():
    xx = np.arange(240)
    stripes = np.where((xx // 12) % 2 == 0, 40, 220).astype(np.uint8)
    f = np.repeat(np.broadcast_to(stripes[None, :, None], (180, 240, 3))[None], 5, axis=0)
    assert run(f)["layout"] == "single"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "g.mkv", grid2x2(n=6, size=160), fps=4)
    out = tmp_path / "e.json"
    assert det.main([clip, "--width", "0", "--fps", "0", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["layout"] == "2x2"
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
