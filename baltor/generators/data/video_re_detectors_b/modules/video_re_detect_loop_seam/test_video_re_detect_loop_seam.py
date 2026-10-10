import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_loop_seam as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 12.0


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def plasma_loop(n, period):
    yy, xx = np.mgrid[0:90, 0:160].astype(np.float32)
    out = []
    for i in range(n):
        t = 2 * np.pi * i / period
        out.append(128 + 50 * np.sin(xx / 9 + t) + 40 * np.sin(yy / 7 - t) + 20 * np.cos((xx + yy) / 13 + 2 * t))
    return np.clip(np.stack(out), 0, 255).astype(np.uint8)


def test_seamless_loop_period_and_end_to_start():
    env = m.detect(plasma_loop(36, 12), FPS)
    assert_valid(env)
    pl = env["payload"]
    whole = [lp for lp in pl["loops"] if lp["scope"] == "whole"]
    assert len(whole) == 1
    assert whole[0]["period_s"] == pytest.approx(1.0, abs=1 / FPS)
    assert whole[0]["seamless"] is True and whole[0]["seam_times_s"] == []
    assert pl["end_to_start"]["seamless"] is True


def test_loop_with_visible_seam():
    strip = kit.synth_texture(90, 160 + 80, seed=51)
    clip = [strip[:, 5 * i:5 * i + 160] for i in range(12)]
    env = m.detect(np.stack(clip * 3).astype(np.uint8), FPS)
    lp = [x for x in env["payload"]["loops"] if x["scope"] == "whole"][0]
    assert lp["period_s"] == pytest.approx(1.0, abs=1 / FPS)
    assert lp["seamless"] is False and lp["seam_ratio"] > 4
    assert lp["seam_times_s"][:2] == pytest.approx([1.0, 2.0], abs=1 / FPS)
    assert env["payload"]["end_to_start"]["seamless"] is False


def test_non_repeating_footage_has_no_loop():
    frames = np.stack([kit.synth_texture(90, 160, seed=200 + i) for i in range(36)]).astype(np.uint8)
    pl = m.detect(frames, FPS)["payload"]
    assert pl["loops"] == [] and pl["end_to_start"]["seamless"] is False


def test_static_picture_is_static_not_loop():
    pl = m.detect(np.repeat(plasma_loop(1, 12), 30, axis=0), FPS)["payload"]
    assert pl["static"] is True and pl["loops"] == []


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_ffmpeg_loop_filter(tmp_path):
    clip = tmp_path / "loop.mp4"
    graph = "testsrc2=s=320x180:r=12:d=1,loop=loop=2:size=12:start=0"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-pix_fmt", "yuv420p", "-crf", "10",
                    str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    whole = [lp for lp in env["payload"]["loops"] if lp["scope"] == "whole"]
    assert len(whole) == 1 and whole[0]["period_s"] == pytest.approx(1.0, abs=0.09)
