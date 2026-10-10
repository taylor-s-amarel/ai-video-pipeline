import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_foreground_subject_mask as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 2.0


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def background(n=4, seed=0):
    rng = np.random.default_rng(seed)
    base = kit.synth_texture(144, 256, seed=seed, rgb=False, lo=70, hi=150)
    frames = np.repeat(np.stack([base * 0.9, base * 0.95, base * 1.05], -1)[None], n, axis=0)
    return np.clip(frames + rng.normal(0, 4, frames.shape), 0, 255).astype(np.uint8)


def disc(frames, cx, cy, r, color):
    yy, xx = np.mgrid[0:frames.shape[1], 0:frames.shape[2]]
    m_ = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    out = frames.copy()
    out[:, m_] = color
    return out


def test_red_disc_on_left_third():
    frames = disc(background(), 64, 72, 26, (220, 30, 30))
    env = m.detect(frames, FPS)
    assert_valid(env)
    shot = env["payload"]["shots"][0]
    cx, cy = shot["center_ratio"]
    assert cx == pytest.approx(64 / 256, abs=0.04) and cy == pytest.approx(0.5, abs=0.05)
    assert shot["framing"] == "left-third"
    true_area = (52 * 52) / (256 * 144)
    assert shot["area_ratio"] == pytest.approx(true_area, rel=0.35)
    assert env["payload"]["identity_inference"] == "none"


def test_large_subject_is_closeup():
    frames = background()
    frames[:, 20:124, 50:206] = (240, 200, 20)
    shot = m.detect(frames, FPS)["payload"]["shots"][0]
    assert shot["size_class"] == "close-up" and shot["framing"] == "center"


def test_plain_background_has_no_subject():
    env = m.detect(background(seed=5), FPS)
    shot = env["payload"]["shots"][0]
    assert shot["bbox"] is None and shot["present_share"] <= 0.25
    assert env["results"] == []


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_lavfi_clip(tmp_path):
    clip = tmp_path / "subject.mp4"
    graph = ("color=c=0x5A6470:s=512x288:r=2,noise=alls=12:allf=t,"
             "drawbox=x=300:y=80:w=120:h=140:color=0xF0A000@1:t=fill")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-t", "2", "-pix_fmt", "yuv420p",
                    str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    shot = env["payload"]["shots"][0]
    assert shot["framing"] in {"center", "right-third"} and shot["center_ratio"][0] > 0.55
