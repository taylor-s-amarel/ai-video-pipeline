import subprocess
from pathlib import Path

import numpy as np
import pytest

import video_re_detect_static_overlay_regions as m
import vre_detect_kit as kit

HERE = Path(__file__).resolve().parent
FPS = 4.0


def assert_valid(env):
    pytest.importorskip("jsonschema")
    assert kit.validate_with_schema(env, HERE / "envelope.schema.json") == []
    if env["payload"] is not None:
        assert kit.validate_with_schema(env["payload"], HERE / "payload.schema.json") == []


def moving_background(n, h=180, w=320, seed=0):
    big = kit.synth_texture(h + 160, w + 160, seed=seed, rgb=True)
    return np.stack([big[(i * 3) % 160:(i * 3) % 160 + h, (i * 5) % 160:(i * 5) % 160 + w] for i in range(n)]).astype(np.uint8)


def with_logo(frames):
    out = frames.copy()
    for f in out:
        f[8:28, 282:312] = (20, 20, 90)
        kit.paste(f, kit.render_text("TV", 2), 286, 11, (255, 255, 255))
    return out


def test_opaque_logo_found_with_bbox_and_span():
    frames = with_logo(moving_background(24))
    env = m.detect(frames, FPS)
    assert_valid(env)
    regs = env["payload"]["regions"]
    assert len(regs) == 1, regs
    r = regs[0]
    x, y, w, h = r["bbox"]
    assert abs(x - 282) <= 3 and abs(y - 8) <= 3 and abs(w - 30) <= 5 and abs(h - 20) <= 5
    assert r["kind"] == "opaque" and r["position"] == "top-right"
    assert r["t_start_s"] == 0.0 and r["t_end_s"] == pytest.approx(24 / FPS)
    assert env["payload"]["handling"] == "detect-only"


def test_translucent_watermark_is_translucent():
    frames = moving_background(24, seed=3)
    for f in frames:
        kit.paste(f, kit.render_text("LOGO", 2), 12, 150, (255, 255, 255), alpha=0.5)
    env = m.detect(frames, FPS)
    regs = env["payload"]["regions"]
    assert len(regs) == 1, regs
    assert regs[0]["kind"] == "translucent"
    assert 0.25 <= regs[0]["opacity_estimate"] <= 0.75
    assert regs[0]["position"] == "bottom-left"


def test_moving_picture_alone_has_no_regions():
    env = m.detect(moving_background(24, seed=5), FPS)
    assert env["status"] == "ok"
    assert env["payload"]["regions"] == []


def test_static_picture_is_undecidable_not_an_overlay():
    still = np.repeat(moving_background(1)[:1], 16, axis=0)
    env = m.detect(still, FPS)
    assert env["payload"]["regions"] == []
    assert env["payload"]["windows_skipped_static"] >= 1 and env["status"] == "partial"
    assert_valid(env)


@pytest.mark.skipif(not (kit.have("ffmpeg") and kit.have("ffprobe")), reason="ffmpeg/ffprobe not installed")
def test_cli_on_lavfi_clip(tmp_path):
    clip = tmp_path / "waves_with_box.mp4"
    src = ("nullsrc=s=320x180:r=10,geq=lum='128+90*sin(X/4+T*7)*cos(Y/5-T*5)':cb=128:cr=128,"
           "drawbox=x=250:y=10:w=50:h=30:color=red@1:t=fill,drawbox=x=258:y=16:w=34:h=18:color=white@1:t=3")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", src, "-t", "4", "-pix_fmt", "yuv420p",
                    "-c:v", "libx264", "-crf", "18", str(clip)], check=True)
    out = tmp_path / "env.json"
    assert m.main([str(clip), "--out", str(out)]) == 0
    env = kit.load_json(out)
    assert_valid(env)
    assert any(kit.iou(r["bbox"], [250, 10, 50, 30]) > 0.5 for r in env["payload"]["regions"])
