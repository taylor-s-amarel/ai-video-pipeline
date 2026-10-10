import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_semi_transparent_layers as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 5.0


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def noise(n=30, h=180, w=320, seed=0):
    return np.random.default_rng(seed).integers(0, 256, size=(n, h, w, 3)).astype(np.uint8)


def with_panel(frames, opacity, color=(255, 255, 255), box=(100, 60, 120, 50)):
    out = frames.astype(np.float32)
    x, y, w, h = box
    out[:, y:y + h, x:x + w] = opacity * np.asarray(color, np.float32) + (1 - opacity) * out[:, y:y + h, x:x + w]
    return out.astype(np.uint8)


@pytest.mark.parametrize("opacity", [0.9, 0.5])
def test_panel_over_moving_noise_opacity(opacity):
    env = m.detect(with_panel(noise(), opacity), FPS)
    assert_valid(env)
    regs = env["payload"]["regions"]
    assert len(regs) == 1, regs
    r = regs[0]
    assert r["kind"] == "semi_transparent"
    assert r["opacity"] == pytest.approx(opacity, abs=0.05)
    assert kit.iou(r["bbox"], [100, 60, 120, 50]) > 0.8
    assert r["tint_color"] is not None and r["tint_color"].upper() in {"#FFFFFF", "#FEFEFE", "#FDFDFD", "#FCFCFC"} or \
        min(int(r["tint_color"][i:i + 2], 16) for i in (1, 3, 5)) > 230


def test_opaque_panel_is_reported_opaque():
    regs = m.detect(with_panel(noise(seed=1), 1.0, (30, 30, 30)), FPS)["payload"]["regions"]
    assert len(regs) == 1 and regs[0]["kind"] == "opaque" and regs[0]["opacity"] >= 0.98


def moving_texture(n=30, h=180, w=320, seed=2):
    big = kit.synth_texture(h + 160, w + 260, seed=seed, rgb=True)
    return np.stack([big[(i * 4) % 160:(i * 4) % 160 + h, (i * 8) % 260:(i * 8) % 260 + w] for i in range(n)])


def test_frosted_panel_flags_blur():
    # a natural-looking moving picture: blurring it removes far more edge energy than motion energy
    frames = moving_texture().astype(np.float32)
    x, y, w, h = 90, 50, 140, 60
    region = kit.box_mean(frames[:, y:y + h, x:x + w].transpose(0, 3, 1, 2), 4).transpose(0, 2, 3, 1)
    frames[:, y:y + h, x:x + w] = 0.6 * region + 0.4 * 255
    regs = m.detect(frames.astype(np.uint8), FPS)["payload"]["regions"]
    assert len(regs) == 1 and regs[0]["blurred_behind"] is True


def test_plain_alpha_panel_over_texture_is_not_frosted():
    frames = moving_texture(seed=4).astype(np.float32)
    frames[:, 50:110, 90:230] = 0.6 * frames[:, 50:110, 90:230] + 0.4 * 255
    regs = m.detect(frames.astype(np.uint8), FPS)["payload"]["regions"]
    assert len(regs) == 1 and regs[0]["blurred_behind"] is False
    assert regs[0]["opacity"] == pytest.approx(0.4, abs=0.08)


def test_noise_alone_has_no_panel():
    env = m.detect(noise(seed=3), FPS)
    assert env["payload"]["regions"] == []


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_lavfi_clip(tmp_path):
    clip = tmp_path / "panel.mp4"
    graph = ("nullsrc=s=320x180:r=10,geq=lum='random(1)*255':cb=128:cr=128,"
             "drawbox=x=100:y=60:w=120:h=50:color=white@0.7:t=fill")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", graph, "-t", "4", "-pix_fmt", "yuv420p",
                    "-c:v", "libx264", "-qp", "0", str(clip)], check=True)
    env = m.detect_file(clip)
    assert_valid(env)
    regs = env["payload"]["regions"]
    assert len(regs) == 1 and regs[0]["opacity"] == pytest.approx(0.7, abs=0.08)
