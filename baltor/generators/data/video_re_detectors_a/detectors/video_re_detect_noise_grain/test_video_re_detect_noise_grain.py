import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_noise_grain as det

HERE = Path(__file__).resolve().parent
H, W = 160, 200


def base_image():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = 40 + 170 * xx / W + 10 * np.sin(yy / 23.0)
    return np.repeat(g[..., None], 3, -1)


def frames_with(noise_fn, n=4, seed=0):
    rng = np.random.default_rng(seed)
    return np.stack([np.clip(base_image() + noise_fn(rng, i), 0, 255) for i in range(n)]).astype(np.uint8)


def run(frames):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 1.0,
                                   defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env["payload"]


def mono(rng, sigma, blur=0.0):
    z = rng.normal(0, 1, (H, W)).astype(np.float32)
    if blur:
        z = core.blur(z, blur)
        z /= z.std()
    return (sigma * z)[..., None]


def test_sigma_5_monochrome_grain():
    p = run(frames_with(lambda r, i: mono(r, 5.0)))
    assert abs(p["noise_sigma"] - 5.0) <= 0.8
    assert p["grain_size_px"] <= 1.6
    assert p["hint"] == "synthetic-grain-like" and abs(p["temporal_correlation"]) < 0.2


def test_coarse_grain_is_larger():
    p = run(frames_with(lambda r, i: mono(r, 6.0, blur=1.5), seed=1))
    assert p["grain_size_px"] >= 2.5


def test_signal_dependent_colour_noise_is_sensor_like():
    def sensor(r, i):
        lvl = base_image()
        return r.normal(0, 1, lvl.shape) * 0.55 * np.sqrt(lvl)
    p = run(frames_with(sensor, seed=2))
    assert p["hint"] == "sensor-like"
    assert p["chroma_luma_ratio"] >= 0.5 or p["signal_dependence_ratio"] >= 1.4


def test_reused_grain_plate_is_static_overlay():
    plate = mono(np.random.default_rng(9), 5.0)
    p = run(frames_with(lambda r, i: plate, seed=3))
    assert p["hint"] == "static-overlay" and p["temporal_correlation"] > 0.9


def test_clean_frames():
    p = run(frames_with(lambda r, i: 0.0, seed=4))
    assert p["hint"] == "clean" and p["noise_sigma"] < 1.0


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "n.mkv", frames_with(lambda r, i: mono(r, 4.0), seed=5), fps=1)
    out = tmp_path / "e.json"
    assert det.main([clip, "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert abs(env["payload"]["noise_sigma"] - 4.0) <= 0.8 and env["payload"]["native_pixels"]
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
