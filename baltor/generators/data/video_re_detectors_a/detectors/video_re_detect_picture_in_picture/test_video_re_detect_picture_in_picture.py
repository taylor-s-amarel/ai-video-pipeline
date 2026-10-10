import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_picture_in_picture as det

HERE = Path(__file__).resolve().parent


def pink(h, w, seed=0):
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.normal(size=(h, w)))
    f = np.sqrt(np.fft.fftfreq(h)[:, None] ** 2 + np.fft.fftfreq(w)[None, :] ** 2)
    f[0, 0] = 1
    img = np.fft.ifft2(F / f ** 1.2).real
    return np.clip((img - img.mean()) / img.std() * 45 + 128, 0, 255)


def background(n, h, w, seed=0):
    big = pink(h + 4 * n, w + 6 * n, seed)
    return np.stack([np.repeat(big[2 * t:2 * t + h, 3 * t:3 * t + w, None], 3, -1) for t in range(n)])


def with_inset(n=28, on=(8, 20), border=3, shadow=False, seed=0):
    h, w = 240, 320
    f = background(n, h, w, seed)
    ins = background(n, 72 - 2 * border, 96 - 2 * border, seed + 50) * np.array([1.0, 0.8, 0.6])
    x, y = 212, 156
    for t in range(*on):
        if shadow:
            f[t, y + 6:y + 72 + 6, x + 6:x + 96 + 6] *= 0.45
        f[t, y:y + 72, x:x + 96] = 255
        f[t, y + border:y + 72 - border, x + border:x + 96 - border] = ins[t]
    return np.clip(f, 0, 255).astype(np.uint8)


def run(frames, fps=4.0):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) / fps,
                                   defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env["payload"]


def test_bottom_right_inset_with_border_and_timing():
    p = run(with_inset())
    assert len(p["insets"]) == 1
    i = p["insets"][0]
    assert i["corner"] == "bottom-right"
    x, y, w, h = i["bbox"]
    assert abs(x - 212) <= 3 and abs(y - 156) <= 3 and abs(w - 96) <= 4 and abs(h - 72) <= 4
    assert i["border"] is not None and abs(i["border"]["px"] - 3) <= 1.5 and i["border"]["color"] == "#FFFFFF"
    assert abs(i["t_start_s"] - 2.0) <= 1.01 and abs(i["t_end_s"] - 5.0) <= 1.01


def test_shadow_direction():
    i = run(with_inset(border=0, shadow=True, seed=3))["insets"][0]
    assert i["shadow"] is not None and i["shadow"]["direction"] == "bottom-right"
    assert i["shadow"]["offset_px"] == [6, 6]
    x, y, w, h = i["bbox"]
    assert abs(w - 96) <= 3 and abs(h - 72) <= 3


def test_no_inset_in_plain_moving_video():
    p = run(background(16, 240, 320, seed=7).astype(np.uint8))
    assert p["insets"] == []


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "p.mkv", with_inset(n=16, on=(0, 16), seed=11), fps=4)
    out = tmp_path / "e.json"
    assert det.main([clip, "--width", "0", "--fps", "4", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert len(env["payload"]["insets"]) == 1 and env["payload"]["insets"][0]["corner"] == "bottom-right"
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
