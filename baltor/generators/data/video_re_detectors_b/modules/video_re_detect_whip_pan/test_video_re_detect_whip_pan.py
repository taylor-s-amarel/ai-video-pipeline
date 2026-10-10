import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_whip_pan as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 25.0
A = kit.synth_texture(108, 192, seed=31, rgb=True)
B = kit.synth_texture(108, 192, seed=32, rgb=True) * np.array([1.0, 0.6, 0.3]) + np.array([0, 20, 60])


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def hblur(img, shift):
    rolled = np.roll(img, shift, axis=1)
    return kit.box_mean(rolled.transpose(2, 0, 1), 0, 15).transpose(1, 2, 0)


def whip_transition():
    frames = [A] * 8 + [hblur(A, -16), hblur(A, -32), hblur(B, -48), hblur(B, -64)] + [B] * 8
    return np.stack(frames).astype(np.uint8)


def test_whip_transition_detected_with_axis_and_direction():
    env = m.detect(whip_transition(), FPS)
    assert_valid(env)
    ev = env["payload"]["events"]
    assert len(ev) == 1
    e = ev[0]
    assert e["axis"] == "horizontal" and e["frames"] == 4
    assert e["camera_direction"] == "right"  # content travels left
    assert e["at_cut"] is True and env["payload"]["as_transition"] == 1
    assert e["t_start_s"] == pytest.approx(8 / FPS)


def test_vertical_whip():
    vb = lambda img, s: kit.box_mean(np.roll(img, s, axis=0).transpose(2, 0, 1), 15, 0).transpose(1, 2, 0)  # noqa: E731
    frames = np.stack([A] * 8 + [vb(A, 10), vb(A, 20), vb(A, 30)] + [np.roll(A, 30, axis=0)] * 8).astype(np.uint8)
    ev = m.detect(frames, FPS)["payload"]["events"]
    assert len(ev) == 1 and ev[0]["axis"] == "vertical" and ev[0]["at_cut"] is False


def test_defocus_blur_is_not_a_whip():
    soft = kit.box_mean(A.transpose(2, 0, 1), 6).transpose(1, 2, 0)
    frames = np.stack([A] * 8 + [soft] * 3 + [A] * 8).astype(np.uint8)
    assert m.detect(frames, FPS)["payload"]["events"] == []


def test_sharp_static_has_no_whip():
    assert m.detect(np.repeat(A[None].astype(np.uint8), 20, axis=0), FPS)["payload"]["events"] == []


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_lavfi_blurred_pan(tmp_path):
    clip = tmp_path / "whip.mp4"
    graph = ("testsrc2=s=384x216:r=25:d=1.6,split[a][b];[a]trim=end=0.6,setpts=PTS-STARTPTS[a1];"
             "[b]trim=start=0.6,setpts=PTS-STARTPTS,split[c][d];[c]trim=end=0.16,dblur=angle=0:radius=30[c1];"
             "[d]trim=start=0.16,setpts=PTS-STARTPTS[d1];[a1][c1][d1]concat=n=3:v=1:a=0[out0]")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-pix_fmt", "yuv420p", str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    assert len(env["payload"]["events"]) == 1 and env["payload"]["events"][0]["axis"] == "horizontal"
