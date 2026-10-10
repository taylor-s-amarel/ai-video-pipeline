import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_zoom_punch_in as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 25.0
STILL = kit.synth_texture(108, 192, seed=21)


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def scaled(scales):
    return np.stack([kit.warp_similarity(STILL, s) for s in scales]).astype(np.uint8)


def test_instant_punch_in_on_beat():
    frames = scaled([1.0] * 10 + [1.15] * 10)
    env = m.detect(frames, FPS, onsets=[0.41, 2.0])
    assert_valid(env)
    ev = env["payload"]["events"]
    assert len(ev) == 1
    e = ev[0]
    assert e["kind"] == "instant" and e["direction"] == "in"
    assert e["t_s"] == pytest.approx(10 / FPS) and e["scale_jump"] == pytest.approx(1.15, abs=0.015)
    assert e["on_beat"] is True and env["payload"]["beats_available"] is True


def test_punch_and_release():
    ev = m.detect(scaled([1.0] * 8 + [1.2] * 8 + [1.0] * 8), FPS)["payload"]["events"]
    assert [e["direction"] for e in ev] == ["in", "out"]
    assert ev[1]["scale_jump"] == pytest.approx(1 / 1.2, abs=0.015)


def test_fast_ramp_punch():
    ramp = [1.2 ** (k / 5) for k in range(1, 6)]
    ev = m.detect(scaled([1.0] * 8 + ramp + [1.2] * 8), FPS)["payload"]["events"]
    assert len(ev) == 1 and ev[0]["kind"] == "ramp" and ev[0]["direction"] == "in"
    assert ev[0]["scale_jump"] == pytest.approx(1.2, abs=0.05)


def test_cut_and_slow_zoom_are_not_punches():
    other = kit.synth_texture(108, 192, seed=99)
    cut = np.concatenate([scaled([1.0] * 8), np.repeat(other[None], 8, axis=0).astype(np.uint8)])
    assert m.detect(cut, FPS)["payload"]["events"] == []
    slow = scaled([1.0 + 0.002 * i for i in range(30)])
    assert m.detect(slow, FPS)["payload"]["events"] == []


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_ffmpeg_cropped_jump(tmp_path):
    clip = tmp_path / "punch.mp4"
    # first 0.6 s full frame, then a centred 334x188 crop scaled back up: a 1.15x punch-in
    graph = ("testsrc=s=384x216:r=25:d=1.2,split[a][b];[a]trim=end=0.6,setpts=PTS-STARTPTS[a1];"
             "[b]trim=start=0.6,setpts=PTS-STARTPTS,crop=334:188,scale=384:216,setsar=1[b1];[a1][b1]concat=n=2:v=1:a=0[out0]")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-pix_fmt", "yuv420p", "-crf", "12",
                    str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    ins = [e for e in env["payload"]["events"] if e["direction"] == "in"]
    assert len(ins) == 1 and ins[0]["scale_jump"] == pytest.approx(384 / 334, abs=0.03)
    assert ins[0]["t_s"] == pytest.approx(0.6, abs=0.05)
