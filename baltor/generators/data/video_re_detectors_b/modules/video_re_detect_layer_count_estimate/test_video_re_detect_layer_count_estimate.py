import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_layer_count_estimate as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 10.0


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def moving_patch(tex, n, h, w, vx, vy, off=60):
    return np.stack([tex[off + i * vy:off + i * vy + h, off + i * vx:off + i * vx + w] for i in range(n)])


def grid_2x2(n=20):
    """Four quadrants with different textures; their content travels left, right, up and not at all."""
    out = np.zeros((n, 180, 320), dtype=np.float32)
    specs = [((0, 0), (2, 0)), ((0, 160), (-2, 0)), ((90, 0), (0, 2)), ((90, 160), (0, 0))]
    for k, ((y, x), (vx, vy)) in enumerate(specs):
        tex = kit.synth_texture(220, 300, seed=10 + k)
        out[:, y:y + 90, x:x + 160] = moving_patch(tex, n, 90, 160, vx, vy)
    return out.astype(np.uint8)


def test_2x2_grid_of_different_motions_is_four_layers():
    env = m.detect(grid_2x2(), FPS)
    assert_valid(env)
    shots = env["payload"]["shots"]
    assert len(shots) == 1
    assert shots[0]["layer_count"] == 4, shots[0]
    kinds = sorted(ly["kind"] for ly in shots[0]["layers"])
    assert kinds == ["moving", "moving", "moving", "static"]


def test_single_pan_is_one_layer():
    tex = kit.synth_texture(260, 400, seed=3)
    frames = moving_patch(tex, 20, 180, 320, 3, 1, off=10).astype(np.uint8)
    env = m.detect(frames, FPS)
    s = env["payload"]["shots"][0]
    assert s["layer_count"] == 1
    assert s["layers"][0]["kind"] == "moving"
    vx, vy = s["layers"][0]["velocity_fw_per_s"]
    # the crop window moves right/down, so the content travels left/up
    assert vx == pytest.approx(-3 / 320 * FPS, rel=0.1) and vy == pytest.approx(-1 / 180 * FPS, rel=0.15)


def test_zoom_is_one_zooming_layer():
    tex = kit.synth_texture(180, 320, seed=4)
    frames = np.stack([kit.warp_similarity(tex, 1.004 ** i) for i in range(20)]).astype(np.uint8)
    s = m.detect(frames, FPS)["payload"]["shots"][0]
    assert s["layer_count"] == 1 and s["layers"][0]["kind"] == "zooming"
    assert s["layers"][0]["zoom_per_s"] == pytest.approx(np.log(1.004) * FPS, rel=0.25)


def test_cut_splits_shots():
    a = grid_2x2(12)
    tex = kit.synth_texture(260, 400, seed=9)
    b = moving_patch(tex, 12, 180, 320, 2, 0, off=10).astype(np.uint8)
    env = m.detect(np.concatenate([a, b]), FPS)
    counts = [s["layer_count"] for s in env["payload"]["shots"]]
    assert counts == [4, 1]


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_lavfi_clip(tmp_path):
    clip = tmp_path / "pan.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=640x360:r=10", "-t", "2",
                    "-vf", "crop=320:180:x='20+t*40':y=90", "-pix_fmt", "yuv420p", str(clip)], check=True)
    env = m.detect_file(clip)
    assert env["status"] in {"ok", "partial"}
    assert_valid(env)
    assert env["payload"]["shots"][0]["layer_count"] is not None
