import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_aspect_reframe as det

HERE = Path(__file__).resolve().parent


def pink(h, w, seed=0):
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.normal(size=(h, w)))
    f = np.sqrt(np.fft.fftfreq(h)[:, None] ** 2 + np.fft.fftfreq(w)[None, :] ** 2)
    f[0, 0] = 1
    img = np.fft.ifft2(F / f).real
    return np.clip((img - img.mean()) / img.std() * 40 + 128, 0, 255)


def rgb(g):
    return np.repeat(np.asarray(g, np.float32)[..., None], 3, -1).astype(np.uint8)


def fft_upscale(img, k):
    h, w = img.shape
    F = np.fft.fftshift(np.fft.fft2(img))
    G = np.zeros((h * k, w * k), complex)
    G[(h * k - h) // 2:(h * k - h) // 2 + h, (w * k - w) // 2:(w * k - w) // 2 + w] = F
    return np.clip(np.fft.ifft2(np.fft.ifftshift(G)).real * k * k, 0, 255)


def run(frames, info=None):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 1.0,
                                   info=info, defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env["payload"]


def clip_16x9(n=5, seed=0):
    return np.stack([rgb(pink(180, 320, seed + i)) for i in range(n)])


def test_16x9_fitted_in_9x16_with_black_bars():
    f = np.zeros((5, 640, 360, 3), np.uint8)
    c = clip_16x9()
    for i in range(5):
        f[i, 218:421, :] = rgb(core.resize_bilinear(c[i, ..., 0], 203, 360))
    p = run(f)
    assert p["method"] == "fit" and p["frame_aspect"] == "9:16" and p["content_aspect"] == "16:9"


def test_blur_pad_uses_same_footage():
    c = clip_16x9(seed=3)
    f = np.zeros((5, 640, 360, 3), np.uint8)
    for i in range(5):
        g = c[i, ..., 0].astype(np.float32)
        big = core.resize_bilinear(g, 640, 1138)[:, 389:749]
        f[i] = rgb(core.blur(big, 14))
        f[i, 218:421] = rgb(core.resize_bilinear(g, 203, 360))
    p = run(f)
    assert p["method"] == "blur-pad" and p["content_aspect"] == "16:9"
    assert p["fill"]["same_footage_corr"] > 0.5


def test_native_full_frame():
    p = run(np.stack([rgb(pink(256, 256, s)) for s in range(3)]))
    assert p["method"] == "full-frame" and p["upscale_factor"] < 1.15


def test_crop_zoom_from_upscaled_full_frame():
    p = run(np.stack([rgb(fft_upscale(pink(128, 128, s + 7), 2)) for s in range(3)]))
    assert p["method"] == "crop-zoom" and p["upscale_factor"] > 1.6


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_second_native_decode_for_zoom(tmp_path):
    frames = np.stack([rgb(fft_upscale(pink(128, 128, s), 2)) for s in range(4)])
    clip = core.write_clip(tmp_path / "z.mkv", frames, fps=1)
    out = tmp_path / "e.json"
    assert det.main([clip, "--width", "128", "--fps", "1", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["method"] == "crop-zoom"
    assert env["payload"]["content_rect"] == {"x": 0, "y": 0, "w": 256, "h": 256}
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
