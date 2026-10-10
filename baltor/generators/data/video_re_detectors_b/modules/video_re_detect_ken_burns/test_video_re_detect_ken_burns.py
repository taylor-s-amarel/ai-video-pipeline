import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_ken_burns as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 10.0
STILL = kit.synth_texture(180, 320, seed=11)


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def kb(n=31, zoom_to=1.12, dx_total=-12.0):
    return np.stack([kit.warp_similarity(STILL, zoom_to ** (i / (n - 1)), dx_total * i / (n - 1), 0.0)
                     for i in range(n)]).astype(np.uint8)


def test_slow_zoom_in_with_pan():
    env = m.detect(kb(), FPS)
    assert_valid(env)
    moves = env["payload"]["moves"]
    assert len(moves) == 1
    mv = moves[0]
    assert mv["zoom_to"] == pytest.approx(1.12, abs=0.02) and mv["zoom_direction"] == "in"
    assert mv["camera_pan"] == "right"  # content travels left
    assert mv["end_crop"][2] == pytest.approx(1 / 1.12, abs=0.02)
    assert mv["progress_r2"] > 0.95


def test_zoom_out_has_end_crop_larger_than_frame():
    mv = m.detect(kb(zoom_to=1 / 1.1, dx_total=0.0), FPS)["payload"]["moves"][0]
    assert mv["zoom_direction"] == "out" and mv["end_crop"][2] > 1.0 and mv["camera_pan"] == "none"


def test_static_still_is_not_a_move():
    env = m.detect(np.repeat(STILL[None].astype(np.uint8), 20, axis=0), FPS)
    assert env["payload"]["moves"] == []


def test_fast_punch_zoom_is_not_ken_burns():
    frames = np.stack([kit.warp_similarity(STILL, 1.5 ** (i / 9)) for i in range(10)]).astype(np.uint8)
    assert m.detect(frames, FPS)["payload"]["moves"] == []


def test_nonrigid_content_is_not_ken_burns():
    rng = np.random.default_rng(1)
    frames = np.stack([kit.synth_texture(180, 320, seed=100 + i) for i in range(12)])
    frames = np.clip(frames + rng.normal(0, 2, frames.shape), 0, 255).astype(np.uint8)
    assert m.detect(frames, FPS)["payload"]["moves"] == []


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_ffmpeg_zoompan(tmp_path):
    clip = tmp_path / "kb.mp4"
    graph = "testsrc=s=320x180:r=1,trim=end_frame=1,zoompan=z='1+0.003*on':d=30:s=320x180:fps=10"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-pix_fmt", "yuv420p", str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    moves = env["payload"]["moves"]
    assert len(moves) == 1 and moves[0]["zoom_direction"] == "in"
    assert moves[0]["zoom_to"] == pytest.approx(1 + 0.003 * 29, abs=0.03)
