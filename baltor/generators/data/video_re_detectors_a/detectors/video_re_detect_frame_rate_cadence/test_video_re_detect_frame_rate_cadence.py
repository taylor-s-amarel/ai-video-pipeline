import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_frame_rate_cadence as det

HERE = Path(__file__).resolve().parent


def images(k, h=72, w=96, seed=0):
    rng = np.random.default_rng(seed)
    base = core.blur(rng.uniform(0, 255, (h, w + 4 * k)).astype(np.float32), 2)
    return [base[:, 4 * i:4 * i + w] for i in range(k)]


def sequence(index, noise=0.6, seed=0):
    """Frames showing image index[i]; small per-frame noise like an encoder would leave."""
    imgs = images(max(index) + 1, seed=seed)
    rng = np.random.default_rng(seed + 1)
    out = [imgs[j] + rng.normal(0, noise, imgs[j].shape) for j in index]
    return np.repeat(np.clip(np.stack(out), 0, 255)[..., None], 3, -1).astype(np.uint8)


def run(frames, fps, times=None):
    t = np.arange(len(frames)) / fps if times is None else times
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, t, info={"r_frame_rate": fps},
                                   defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env


def test_animation_on_twos_at_24():
    p = run(sequence([i // 2 for i in range(48)]), 24)["payload"]
    assert p["cadence"] == "on-twos" and abs(p["effective_fps"] - 12) <= 0.6
    assert abs(p["duplicate_ratio"] - 0.5) <= 0.06


def test_24_in_30_hold_pattern():
    p = run(sequence([int(k * 24 / 30) for k in range(60)]), 30)["payload"]
    assert p["cadence"] == "pattern" and p["hold_pattern"] == [1, 1, 1, 2]
    assert abs(p["effective_fps"] - 24) <= 1


def test_all_unique_frames_are_on_ones():
    p = run(sequence(list(range(40))), 30)["payload"]
    assert p["cadence"] == "on-ones" and p["effective_fps"] == 30 and p["duplicate_ratio"] < 0.05
    assert not p["vfr"]


def test_variable_frame_rate_timestamps():
    rng = np.random.default_rng(3)
    t = np.cumsum(rng.choice([1 / 30, 1 / 24, 1 / 60], size=40))
    p = run(sequence(list(range(40))), 30, times=t)["payload"]
    assert p["vfr"]


def test_still_video_has_no_cadence():
    env = run(sequence([0] * 30), 30)
    assert env["payload"]["cadence"] == "static" and env["payload"]["effective_fps"] is None
    assert env["status"] == "partial"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "c.mkv", sequence([i // 3 for i in range(36)], seed=4), fps=24)
    out = tmp_path / "e.json"
    assert det.main([clip, "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["cadence"] == "on-threes" and abs(env["payload"]["effective_fps"] - 8) <= 0.5
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
