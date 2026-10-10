import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_blend_mode_hint as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 5.0
BOX = (slice(48, 136), slice(80, 240))


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def content(n=40, hi=1.0, seed=0):
    return np.random.default_rng(seed).random((n, 180, 320, 3)).astype(np.float32) * hi


def light_leak():
    """Static overlay colour varying across the box: warm gradient, like a light leak."""
    ramp = np.linspace(0.25, 0.95, 160, dtype=np.float32)[None, :, None]
    return np.broadcast_to(ramp * np.array([1.0, 0.65, 0.3], np.float32), (88, 160, 3))


def composite(mode, b, o, alpha=0.5):
    out = b.copy()
    region = out[:, BOX[0], BOX[1]]
    if mode == "screen":
        out[:, BOX[0], BOX[1]] = 1 - (1 - o) * (1 - region)
    elif mode == "multiply":
        out[:, BOX[0], BOX[1]] = o * region
    elif mode == "add":
        out[:, BOX[0], BOX[1]] = np.minimum(1, region + o * 0.45)
    elif mode == "normal":
        out[:, BOX[0], BOX[1]] = alpha * o + (1 - alpha) * region
    return (np.clip(out, 0, 1) * 255).round().astype(np.uint8)


@pytest.mark.parametrize("mode", ["screen", "multiply", "normal"])
def test_light_leak_mode_is_identified(mode):
    env = m.detect(composite(mode, content(), light_leak()), FPS)
    assert_valid(env)
    pl = env["payload"]
    assert pl["mode"] == mode, pl["scores"]
    assert kit.iou(pl["region"]["bbox"], [80, 48, 160, 88]) > 0.7


def test_add_over_dark_content_is_add():
    env = m.detect(composite("add", content(hi=0.5, seed=2), light_leak()), FPS)
    assert env["payload"]["mode"] == "add", env["payload"]["scores"]


def test_uniform_white_overlay_is_honestly_ambiguous():
    # 50% white in normal mode equals screen with 50% grey, pixel for pixel
    o = np.full((88, 160, 3), 1.0, np.float32)
    pl = m.detect(composite("normal", content(seed=3), o), FPS)["payload"]
    assert pl["mode"] == "ambiguous" and {"normal", "screen"} <= set(pl["candidates"])


def test_uniform_black_overlay_is_normal_or_multiply():
    o = np.zeros((88, 160, 3), np.float32)
    pl = m.detect(composite("normal", content(seed=5), o, alpha=0.6), FPS)["payload"]
    assert pl["mode"] == "ambiguous" and {"normal", "multiply"} <= set(pl["candidates"])


def test_no_overlay_is_none():
    pl = m.detect((content(seed=4) * 255).astype(np.uint8), FPS)["payload"]
    assert pl["mode"] == "none" and pl["region"] is None


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_lavfi_multiply(tmp_path):
    clip = tmp_path / "multiply.mkv"
    graph = ("nullsrc=s=320x180:r=5,geq=r='random(1)*255':g='random(2)*255':b='random(3)*255'[bg];"
             "color=c=white:s=320x180:r=5,drawbox=x=80:y=48:w=160:h=88:color=0xFF8040@1:t=fill[ov];"
             "[bg][ov]blend=all_mode=multiply,format=rgb24")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-t", "6", "-c:v", "ffv1", str(clip)],
                   check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    assert env["payload"]["mode"] == "multiply", env["payload"]["scores"]
