import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_letterbox_pillarbox as det

HERE = Path(__file__).resolve().parent


def texture(n, h, w, seed=0, speed=6):
    rng = np.random.default_rng(seed)
    base = core.blur(rng.uniform(0, 255, (h + 8, w + n * speed + 8, 3)).astype(np.float32), 1.0, axes=(0, 1))
    base = (base - base.min()) / (base.max() - base.min()) * 200 + 30
    return np.stack([base[:h, i * speed:i * speed + w] for i in range(n)]).astype(np.uint8)


def envelope(frames, **params):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 0.5,
                                   params=params, defaults=det.DEFAULTS)
    errs = core.check_envelope(env, HERE)
    if errs != ["jsonschema not installed"]:
        assert errs == []
    return env


def test_140px_black_letterbox():
    f = np.zeros((6, 600, 320, 3), np.uint8)
    f[:, 140:460] = texture(6, 320, 320)
    env = envelope(f)
    p = env["payload"]
    assert p["kind"] == "letterbox"
    sides = {b["side"]: b for b in p["bars"]}
    assert abs(sides["top"]["px"] - 140) <= 1 and abs(sides["bottom"]["px"] - 140) <= 1
    assert sides["top"]["style"] == "solid" and sides["top"]["color"] == "#000000"
    assert p["content_rect"] == {"x": 0, "y": 140, "w": 320, "h": 320}


def test_title_text_inside_top_bar_does_not_cut_bar():
    f = np.zeros((6, 600, 320, 3), np.uint8)
    f[:, 140:460] = texture(6, 320, 320, seed=1)
    f[:, 50:80, 40:280:10] = 255  # static white "glyph" columns inside the bar
    p = envelope(f)["payload"]
    top = next(b for b in p["bars"] if b["side"] == "top")
    assert abs(top["px"] - 140) <= 1 and top["overlay_in_bar"]


def test_blurred_fill_pillarbox():
    content = texture(6, 180, 180, seed=2)
    f = np.zeros((6, 180, 320, 3), np.uint8)
    for i in range(6):
        stretched = core.resize_bilinear(content[i], 180, 320)
        f[i] = np.clip(core.blur_rgb(stretched, 12), 0, 255).astype(np.uint8)
        f[i, :, 70:250] = content[i]
    p = envelope(f)["payload"]
    assert p["kind"] == "pillarbox"
    for b in p["bars"]:
        assert b["style"] == "blurred-fill" and abs(b["px"] - 70) <= 6


def test_full_frame_content_has_no_bars():
    p = envelope(texture(6, 240, 320, seed=3))["payload"]
    assert p["kind"] == "none" and p["bars"] == []


def test_dark_scene_does_not_widen_bar():
    f = np.zeros((10, 300, 200, 3), np.uint8)
    f[:, 50:250] = texture(10, 200, 200, seed=4)
    f[0, 50:90] = 0  # one frame with black content touching the bar
    p = envelope(f)["payload"]
    top = next(b for b in p["bars"] if b["side"] == "top")
    assert top["px"] == 50


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    f = np.zeros((8, 200, 160, 3), np.uint8)
    f[:, 40:160] = texture(8, 120, 160, seed=5)
    clip = core.write_clip(tmp_path / "lb.mkv", f, fps=4)
    out = tmp_path / "env.json"
    code = det.main([clip, "--fps", "4", "--width", "0", "--out", str(out), "--compact"])
    env = __import__("json").loads(out.read_text())
    assert code == 0 and env["status"] == "ok"
    assert env["payload"]["kind"] == "letterbox"
    assert {b["side"]: b["px"] for b in env["payload"]["bars"]} == {"top": 40, "bottom": 40}
    errs = core.check_envelope(env, HERE)
    assert errs in ([], ["jsonschema not installed"])
