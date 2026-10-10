import io
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_compression_blockiness as det

HERE = Path(__file__).resolve().parent


def smooth(h, w, seed=0):
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.normal(size=(h, w)))
    f = np.sqrt(np.fft.fftfreq(h)[:, None] ** 2 + np.fft.fftfreq(w)[None, :] ** 2)
    f[0, 0] = 1
    img = np.fft.ifft2(F / f ** 1.6).real
    return np.clip((img - img.mean()) / img.std() * 40 + 128, 0, 255)


def dct_matrix(n=8):
    k = np.arange(n)
    m = np.cos(np.pi * (2 * k[None, :] + 1) * k[:, None] / (2 * n)) * np.sqrt(2 / n)
    m[0] /= np.sqrt(2)
    return m


def dct_quantise(img, step=40.0):
    """JPEG-like coding: 8x8 DCT, coarse quantisation of AC coefficients, inverse DCT."""
    D = dct_matrix()
    out = img.copy()
    for y in range(0, img.shape[0] - 7, 8):
        for x in range(0, img.shape[1] - 7, 8):
            c = D @ (img[y:y + 8, x:x + 8] - 128) @ D.T
            q = np.round(c / step) * step
            q[0, 0] = np.round(c[0, 0] / 8) * 8
            out[y:y + 8, x:x + 8] = D.T @ q @ D + 128
    return np.clip(out, 0, 255)


def rgb(stack):
    return np.repeat(np.asarray(stack, np.float32)[..., None], 3, -1).astype(np.uint8)


def run(frames):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 1.0,
                                   defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env["payload"]


def test_clean_image_is_clean():
    p = run(rgb([smooth(256, 256, s) for s in range(2)]))
    assert p["label"] == "clean" and p["ratio"]["x"] < 1.1


def test_dct_quantised_image_is_blocky_and_grid_found_after_crop():
    imgs = [dct_quantise(smooth(256, 256, s)) for s in range(2)]
    p = run(rgb(imgs))
    assert p["label"] in ("visible", "heavy") and p["grid_phase"] == {"x": 0, "y": 0}
    shifted = run(rgb([im[3:, 5:] for im in imgs]))
    assert shifted["label"] in ("visible", "heavy")
    assert shifted["grid_phase"] == {"x": 3, "y": 5}


def test_jpeg_quality_levels_with_pil():
    Image = pytest.importorskip("PIL.Image")

    def jpeg(img, q):
        b = io.BytesIO()
        Image.fromarray(img.astype(np.uint8)).save(b, "JPEG", quality=q)
        return np.asarray(Image.open(b).convert("L"), np.float32)

    base = smooth(256, 256, 7)
    low = run(rgb([jpeg(base, 8)]))
    high = run(rgb([jpeg(base, 95)]))
    assert low["ratio"]["x"] > high["ratio"]["x"] + 0.2
    assert high["label"] in ("clean", "mild") and low["label"] in ("visible", "heavy")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "b.mkv", rgb([dct_quantise(smooth(128, 160, s)) for s in range(2)]), fps=1)
    out = tmp_path / "e.json"
    assert det.main([clip, "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["label"] in ("visible", "heavy") and env["payload"]["native_pixels"]
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
