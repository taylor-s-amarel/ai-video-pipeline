import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_speed_ramp_freeze as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 25.0
STRIP = kit.synth_texture(90, 160 + 400, seed=41)


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def pan(offsets):
    return np.stack([STRIP[:, o:o + 160] for o in offsets]).astype(np.uint8)


def test_freeze_then_half_speed():
    offs = [4 * i for i in range(30)]
    offs += [offs[-1]] * 15
    offs += [offs[-1] + 2 * (i + 1) for i in range(20)]
    env = m.detect(pan(offs), FPS)
    assert_valid(env)
    ev = env["payload"]["events"]
    fr = [e for e in ev if e["type"] == "freeze"]
    sc = [e for e in ev if e["type"] == "speed_change"]
    assert len(fr) == 1 and fr[0]["t_start_s"] == pytest.approx(30 / FPS) and fr[0]["t_end_s"] == pytest.approx(45 / FPS)
    assert len(sc) == 1 and sc[0]["rate"] == pytest.approx(0.5, abs=0.08)
    assert sc[0]["t_start_s"] == pytest.approx(45 / FPS, abs=0.1)


def test_duplicated_frames_are_half_speed_slow_motion():
    offs = [4 * (i // 2) for i in range(40)]
    ev = m.detect(pan(offs), FPS)["payload"]["events"]
    dup = [e for e in ev if e["type"] == "duplicate_slowmo"]
    assert len(dup) == 1 and dup[0]["rate"] == pytest.approx(0.5)


def test_constant_pan_has_no_events():
    env = m.detect(pan([3 * i for i in range(40)]), FPS)
    assert env["payload"]["events"] == []


def test_static_shot_is_not_a_freeze():
    assert m.detect(pan([0] * 30), FPS)["payload"]["events"] == []


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_ffmpeg_freeze(tmp_path):
    clip = tmp_path / "freeze.mp4"
    graph = "testsrc2=s=320x180:r=25:d=2,loop=loop=12:size=1:start=20"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-pix_fmt", "yuv420p", "-crf", "10",
                    str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    fr = [e for e in env["payload"]["events"] if e["type"] == "freeze"]
    assert len(fr) == 1 and fr[0]["t_start_s"] == pytest.approx(0.84, abs=0.05) and fr[0]["frames"] >= 11
