import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_parallax_depth_layers as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 10.0


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def bands(speeds, n=20, h=180, w=320):
    """Horizontal bands whose content travels left at the given px/frame speeds (camera trucking right)."""
    out = np.zeros((n, h, w), dtype=np.float32)
    bh = h // len(speeds)
    for k, v in enumerate(speeds):
        tex = kit.synth_texture(bh + 8, w + v * n + 8, seed=20 + k)
        for i in range(n):
            out[i, k * bh:(k + 1) * bh] = tex[4:4 + bh, 4 + i * v:4 + i * v + w]
    return out.astype(np.uint8)


def test_three_bands_at_1_2_4_px_per_frame():
    env = m.detect(bands([1, 2, 4]), FPS)
    assert_valid(env)
    s = env["payload"]["shots"][0]
    assert s["parallax"] is True
    assert len(s["layers"]) == 3
    ratios = [ly["speed_ratio"] for ly in s["layers"]]
    assert ratios == pytest.approx([4.0, 2.0, 1.0], rel=0.08)
    assert s["direction_deg"] == pytest.approx(180.0, abs=5)
    # fastest (nearest) layer is the bottom band
    assert s["layers"][0]["depth_rank"] == 0 and s["layers"][0]["region"]["y_center_ratio"] > 0.66
    assert env["results"] and env["results"][0]["label"] == "parallax"


def test_uniform_pan_is_not_parallax():
    s = m.detect(bands([3, 3, 3]), FPS)["payload"]["shots"][0]
    assert s["parallax"] is False


def test_opposite_directions_are_not_parallax():
    a = bands([2], n=20)
    b = bands([2], n=20)[:, :, ::-1]
    frames = np.concatenate([a[:, :90], np.ascontiguousarray(b[:, 90:])], axis=1)
    env = m.detect(frames, FPS)
    s = env["payload"]["shots"][0]
    assert s["parallax"] is False and s["other_moving_layers"] == 1


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_lavfi_clip(tmp_path):
    clip = tmp_path / "bands.mp4"
    graph = ("testsrc=s=640x180:r=10,split[a][b];[a]crop=320:90:x='t*20':y=0[top];"
             "[b]crop=320:90:x='t*60':y=90[bot];[top][bot]vstack")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-t", "2", "-pix_fmt", "yuv420p",
                    str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    assert env["status"] in {"ok", "partial"}
    s = env["payload"]["shots"][0]
    assert s["parallax"] is True and 2.4 <= s["max_speed_ratio"] <= 3.4  # 60 vs 20 px/s
