import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_banding as det

HERE = Path(__file__).resolve().parent


def ramp(h=128, w=256, lo=40.0, hi=120.0):
    return np.broadcast_to(np.linspace(lo, hi, w, dtype=np.float32)[None, :], (h, w)).copy()


def rgb(img):
    return np.repeat(np.asarray(img, np.float32)[..., None], 3, -1)


def run(frames, info=None):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 2.0,
                                   info=info, defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env


def test_injected_banding_is_found():
    g = np.round(ramp() / 8) * 8
    p = run(np.stack([rgb(g)] * 2).astype(np.uint8))["payload"]
    assert p["banded"] and p["score"] > 0.5 and 6 <= p["step_code_values"] <= 10
    assert p["regions"] and p["flat_run_px"] >= 20


def test_clean_8bit_ramp_is_not_banded():
    p = run(np.stack([rgb(np.round(ramp()))] * 2).astype(np.uint8))["payload"]
    assert not p["banded"] and p["ramp_blocks"] > 10


def test_dithered_coarse_ramp_is_not_banded():
    rng = np.random.default_rng(0)
    g = np.round(ramp() + rng.normal(0, 1.2, (128, 256)))
    p = run(np.stack([rgb(g)] * 2).astype(np.uint8))["payload"]
    assert not p["banded"]


def test_y_codes_input_and_flat_frames():
    g = np.round(ramp(lo=20, hi=60) / 4) * 4
    p = run(np.stack([g] * 2).astype(np.uint8))["payload"]
    assert p["banded"] and 3 <= p["step_code_values"] <= 5
    env = run(np.full((2, 64, 64), 90, np.uint8))
    assert env["status"] == "partial" and env["payload"]["score"] is None


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_reads_raw_y_plane(tmp_path):
    g = np.round(ramp(96, 256) / 8) * 8
    clip = core.write_clip(tmp_path / "b.mkv", np.stack([rgb(g)] * 2).astype(np.uint8), fps=1)
    out = tmp_path / "e.json"
    assert det.main([clip, "--fps", "0", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["banded"]
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
