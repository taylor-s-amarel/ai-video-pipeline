import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_interlacing as det

HERE = Path(__file__).resolve().parent


def field_images(k, h=144, w=192, seed=0, speed=3):
    rng = np.random.default_rng(seed)
    base = core.blur(rng.uniform(0, 255, (h, w + speed * k)).astype(np.float32), 1.2)
    base = (base - base.min()) / (base.max() - base.min()) * 220 + 15
    return [base[:, speed * i:speed * i + w] for i in range(k)]


def weave(n, order="tff", seed=0):
    imgs = field_images(2 * n, seed=seed)
    out = []
    for i in range(n):
        first, second = imgs[2 * i], imgs[2 * i + 1]
        f = np.empty_like(first)
        if order == "tff":
            f[0::2], f[1::2] = first[0::2], second[1::2]
        else:
            f[1::2], f[0::2] = first[1::2], second[0::2]
        out.append(f)
    return np.repeat(np.stack(out)[..., None], 3, -1).astype(np.uint8)


def progressive(n, seed=0):
    imgs = field_images(2 * n, seed=seed)
    return np.repeat(np.stack(imgs[::2])[..., None], 3, -1).astype(np.uint8)


def run(frames):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) / 25,
                                   defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env


def test_top_field_first():
    p = run(weave(12, "tff"))["payload"]
    assert p["interlaced"] and p["field_order"] == "tff" and p["combed_frame_ratio"] > 0.9


def test_bottom_field_first():
    p = run(weave(12, "bff", seed=1))["payload"]
    assert p["interlaced"] and p["field_order"] == "bff"


def test_progressive_is_not_interlaced():
    p = run(progressive(12, seed=2))["payload"]
    assert not p["interlaced"] and p["field_order"] == "progressive" and p["combed_frame_ratio"] < 0.1


def test_still_frames_are_undetermined():
    env = run(np.repeat(progressive(1, seed=3), 6, axis=0))
    assert env["status"] == "partial" and env["payload"]["field_order"] == "unknown"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_with_idet(tmp_path):
    clip = core.write_clip(tmp_path / "i.mkv", weave(16, "tff", seed=4), fps=25)
    out = tmp_path / "e.json"
    assert det.main([clip, "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["interlaced"] and env["payload"]["field_order"] == "tff"
    assert env["payload"]["idet"] is None or set(env["payload"]["idet"]) == {"tff", "bff", "progressive", "undetermined"}
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
