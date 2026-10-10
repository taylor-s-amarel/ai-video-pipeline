import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_true_resolution as det

HERE = Path(__file__).resolve().parent


def pink(h, w, seed=0, beta=1.0):
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.normal(size=(h, w)))
    f = np.sqrt(np.fft.fftfreq(h)[:, None] ** 2 + np.fft.fftfreq(w)[None, :] ** 2)
    f[0, 0] = 1
    img = np.fft.ifft2(F / f ** beta).real
    return np.clip((img - img.mean()) / img.std() * 40 + 128, 0, 255)


def fft_upscale(img, k):
    """Ideal (band-limited) upscale by integer k: zero-padding the spectrum."""
    h, w = img.shape
    F = np.fft.fftshift(np.fft.fft2(img))
    H, W = h * k, w * k
    G = np.zeros((H, W), complex)
    G[(H - h) // 2:(H - h) // 2 + h, (W - w) // 2:(W - w) // 2 + w] = F
    return np.clip(np.fft.ifft2(np.fft.ifftshift(G)).real * k * k, 0, 255)


def as_rgb(grays):
    return np.repeat(np.asarray(grays, np.float32)[..., None], 3, axis=-1).astype(np.uint8)


def run(frames, info=None):
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 2.0,
                                   info=info, defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env


def test_native_pink_noise_is_native():
    p = run(as_rgb([pink(256, 384, s) for s in range(3)]))["payload"]
    assert p["verdict"] == "native" and p["upscale_factor"] < 1.15


def test_ideal_2x_upscale_halves_effective_size():
    p = run(as_rgb([fft_upscale(pink(128, 192, s), 2) for s in range(3)]), info={"width": 384, "height": 256})["payload"]
    assert p["verdict"] == "upscaled"
    assert 1.75 <= p["upscale_factor"] <= 2.3
    assert abs(p["effective"]["w"] - 192) <= 30


def test_bicubic_2x_upscale_with_pil():
    Image = pytest.importorskip("PIL.Image")
    frames = []
    for s in range(3):
        small = Image.fromarray(pink(128, 192, s + 5).astype(np.uint8))
        frames.append(np.asarray(small.resize((384, 256), Image.BICUBIC), np.float32))
    p = run(as_rgb(frames))["payload"]
    assert p["verdict"] == "upscaled" and 1.6 <= p["upscale_factor"] <= 2.5


def test_native_caption_over_upscaled_footage_is_mixed():
    frames = []
    for s in range(3):
        img = fft_upscale(pink(128, 256, s + 9), 2)  # 256 x 512
        img[:, 256:] = pink(256, 256, s + 20)  # right half native detail (e.g. a rendered graphic)
        frames.append(img)
    p = run(as_rgb(frames))["payload"]
    assert p["verdict"] == "mixed" and 0.25 <= p["tiles"]["upscaled_share"] <= 0.75


def test_flat_frames_are_insufficient():
    env = run(np.full((2, 256, 256, 3), 90, np.uint8))
    assert env["status"] == "partial" and env["payload"]["verdict"] == "insufficient-detail"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_upscaled_clip(tmp_path):
    frames = as_rgb([fft_upscale(pink(128, 128, s), 2) for s in range(3)])
    clip = core.write_clip(tmp_path / "u.mkv", frames, fps=1)
    out = tmp_path / "e.json"
    assert det.main([clip, "--fps", "0", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["verdict"] == "upscaled" and 1.7 <= env["payload"]["upscale_factor"] <= 2.3
    assert env["payload"]["container"] == {"w": 256, "h": 256}
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
