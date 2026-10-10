import shutil

import numpy as np
import pytest

import video_re_overlay_transparency_probe as m
import video_re_synth as synth

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
W, H = 160, 288
PANEL = (40, 90, 80, 110)  # x, y, w, h


def panel_frames(alpha, n=50, color=(20, 20, 30)):
    x, y, w, h = PANEL
    for f in synth.pan_frames(n, (W, H), dx_per_frame=3):
        f = f.astype(float)
        f[y:y + h, x:x + w] = alpha * np.array(color) + (1 - alpha) * f[y:y + h, x:x + w]
        yield f.clip(0, 255).astype(np.uint8)


def iou(a, b):
    ix = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return ix * iy / (a[2] * a[3] + b[2] * b[3] - ix * iy)


@ffmpeg
@pytest.mark.parametrize("alpha", [0.4, 0.75])
def test_semi_transparent_panel_found_with_its_opacity(tmp_path, alpha):
    p = synth.encode_frames(tmp_path / "v.mp4", panel_frames(alpha), 25, (W, H))
    res = m.run(str(p))
    assert res["status"] == "ok" and len(res["panels"]) == 1
    pan = res["panels"][0]
    assert pan["class"] == "semi-transparent"
    assert pan["estimated_opacity"] == pytest.approx(alpha, abs=0.1)
    assert iou(pan["bbox"], PANEL) > 0.7
    assert res["semi_transparent_ratio"] == 1.0
    tint = [int(pan["tint_estimate"][i:i + 2], 16) for i in (1, 3, 5)]
    assert max(abs(a - b) for a, b in zip(tint, (20, 20, 30))) <= 25


@ffmpeg
def test_solid_panel_is_opaque(tmp_path):
    p = synth.encode_frames(tmp_path / "v.mp4", panel_frames(1.0), 25, (W, H))
    res = m.run(str(p))
    assert [x["class"] for x in res["panels"]] == ["opaque"]
    assert res["semi_transparent_ratio"] == 0.0


@ffmpeg
def test_no_panel_and_no_motion_give_null_with_reason(tmp_path):
    moving = synth.encode_frames(tmp_path / "m.mp4", synth.pan_frames(50, (W, H), 3), 25, (W, H))
    res = m.run(str(moving))
    assert res["semi_transparent_ratio"] is None and res["summary"]["reason"] == "no overlay panel detected"
    still = synth.encode_frames(tmp_path / "s.mp4", (np.full((H, W, 3), 90, np.uint8) for _ in range(40)), 25, (W, H))
    res = m.run(str(still))
    assert res["semi_transparent_ratio"] is None
    assert res["summary"]["reason"] == "no moving background to test against"


def test_large_static_scenery_is_not_a_panel():
    rng = np.random.default_rng(0)
    frames = np.repeat(rng.integers(0, 255, (1, 96, 96, 3)), 8, axis=0).astype(np.uint8)
    frames[:, :24, :24] = rng.integers(0, 255, (8, 24, 24, 3))  # only the top-left corner moves
    assert m.panels_in_window(frames)["panels"] == []
