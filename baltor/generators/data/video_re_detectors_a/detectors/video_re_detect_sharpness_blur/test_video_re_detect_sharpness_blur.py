import json
import shutil
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core
import video_re_detect_sharpness_blur as det

HERE = Path(__file__).resolve().parent


def pink(h, w, seed=0):
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.normal(size=(h, w)))
    f = np.sqrt(np.fft.fftfreq(h)[:, None] ** 2 + np.fft.fftfreq(w)[None, :] ** 2)
    f[0, 0] = 1
    img = np.fft.ifft2(F / f).real
    return np.clip((img - img.mean()) / img.std() * 40 + 128, 0, 255)


def rgb(stack):
    return np.repeat(np.asarray(stack, np.float32)[..., None], 3, -1).astype(np.uint8)


def run(frames, shots=None):
    params = {"_shots": shots} if shots else {}
    env = core.analyse_to_envelope(det.IDENTITY, det.VERSION, det.analyse, frames, np.arange(len(frames)) * 0.5,
                                   params=params, defaults=det.DEFAULTS)
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
    return env["payload"]


def test_metric_orders_sharp_and_blurred():
    g = pink(180, 320, 1)
    assert det.blur_metric(g) < 0.35 < det.blur_metric(core.blur(g, 1.5)) < det.blur_metric(core.blur(g, 3))
    assert det.variance_of_laplacian(g) > 10 * det.variance_of_laplacian(core.blur(g, 1.5))


def test_per_shot_labels_with_given_shots():
    sharp = [pink(180, 320, s) for s in range(4)]
    soft = [core.blur(pink(180, 320, s + 10), 3) for s in range(4)]
    p = run(rgb(sharp + soft), shots=[(0.0, 2.0), (2.0, 4.0)])
    assert [s["label"] for s in p["shots"]] == ["sharp", "blurred"]
    assert p["shots_source"] == "given"


def test_selective_focus():
    frames = []
    for s in range(4):
        g = core.blur(pink(180, 320, s + 20), 4)
        g[60:120, 107:213] = pink(60, 106, s + 30)
        frames.append(g)
    p = run(rgb(frames))
    assert p["video"]["selective_focus_share"] >= 0.75


def test_blur_in_within_one_shot():
    base = pink(180, 320, 40)
    frames = [core.blur(base, s) if s else base for s in (4, 3, 2, 1, 0, 0)]
    p = run(rgb(frames), shots=[(0.0, 3.0)])
    assert p["shots"][0]["focus_change"] == "blur-in"


def test_uniformly_sharp_video_has_no_defocus():
    p = run(rgb([pink(180, 320, s + 50) for s in range(4)]))
    assert p["video"]["label"] == "sharp" and p["video"]["selective_focus_share"] == 0.0


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_cli_on_lossless_clip(tmp_path):
    clip = core.write_clip(tmp_path / "s.mkv", rgb([core.blur(pink(180, 320, s), 3) for s in range(4)]), fps=2)
    out = tmp_path / "e.json"
    assert det.main([clip, "--width", "0", "--out", str(out)]) == 0
    env = json.loads(out.read_text())
    assert env["payload"]["video"]["label"] == "blurred"
    assert core.check_envelope(env, HERE) in ([], ["jsonschema not installed"])
