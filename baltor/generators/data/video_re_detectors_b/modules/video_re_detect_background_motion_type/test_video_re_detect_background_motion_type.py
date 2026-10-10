import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_background_motion_type as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 10.0


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def only_shot(frames):
    env = m.detect(frames, FPS)
    assert_valid(env)
    shots = env["payload"]["shots"]
    assert len(shots) == 1, [s["t_start_s"] for s in shots]
    return shots[0]


STILL = kit.synth_texture(180, 320, seed=1, rgb=True)


def test_static_still():
    s = only_shot(np.repeat(STILL[None].astype(np.uint8), 12, axis=0))
    assert s["type"] == "static"


def test_ken_burns_zoom_on_still():
    frames = np.stack([kit.warp_similarity(STILL, 1.0 + 0.004 * i, -0.3 * i, 0.0) for i in range(16)])
    s = only_shot(frames.astype(np.uint8))
    assert s["type"] == "still_pan_zoom"
    assert s["zoom_per_s"] == pytest.approx(np.log(1.004) * FPS, rel=0.35)


def test_nonrigid_footage_is_video():
    rng = np.random.default_rng(0)
    out = np.zeros((16, 180, 320, 3), np.float32)
    for k, ((y, x), (vx, vy)) in enumerate([((0, 0), (2, 0)), ((0, 160), (-2, 1)), ((90, 0), (0, 2)), ((90, 160), (1, -1))]):
        tex = kit.synth_texture(260, 320, seed=30 + k, rgb=True)
        for i in range(16):
            out[i, y:y + 90, x:x + 160] = tex[60 + i * vy:150 + i * vy, 60 + i * vx:220 + i * vx]
    out += rng.normal(0, 3, out.shape)
    s = only_shot(np.clip(out, 0, 255).astype(np.uint8))
    assert s["type"] == "video" and s["loops"] is False


def plasma(n, period=None):
    yy, xx = np.mgrid[0:180, 0:320].astype(np.float32)
    frames = []
    for i in range(n):
        t = 2 * np.pi * i / period if period else 0.35 * i
        r = 128 + 60 * np.sin(xx / 17 + t) + 50 * np.sin(yy / 23 - 2 * t)
        g = 100 + 80 * np.sin((xx + yy) / 29 + t)
        b = 128 + 60 * np.cos((xx - yy) / 40 - t)
        frames.append(np.stack([r, g, b], -1))
    return np.clip(np.stack(frames), 0, 255).astype(np.uint8)


def test_plasma_is_procedural():
    s = only_shot(plasma(16))
    assert s["type"] == "procedural"


def test_seamless_procedural_loop_reports_period():
    s = only_shot(plasma(36, period=12))
    assert s["type"] == "procedural" and s["loops"] is True
    assert s["loop_period_s"] == pytest.approx(1.2, abs=0.11)


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_lavfi_zoompan(tmp_path):
    clip = tmp_path / "zoom.mp4"
    graph = "testsrc=s=320x180:r=1,trim=end_frame=1,zoompan=z='1+0.004*on':d=20:s=320x180:fps=10"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-pix_fmt", "yuv420p", str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    assert env["payload"]["shots"][0]["type"] in {"still_pan_zoom", "static"}
