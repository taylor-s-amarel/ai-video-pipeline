import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

import vre_pixel_core as core

HERE = Path(__file__).resolve().parent


def test_phase_correlation_sign_and_subpixel():
    rng = np.random.default_rng(1)
    a = core.blur(rng.normal(0, 40, (96, 128)).astype(np.float32), 1.5)
    b = np.roll(a, (3, -5), axis=(0, 1))  # content moves down 3, left 5
    dx, dy, peak = core.phase_correlation(a, b)
    assert abs(dx + 5) < 0.2 and abs(dy - 3) < 0.2 and peak > 0.3


def test_blur_and_box_blur_preserve_mean():
    rng = np.random.default_rng(2)
    x = rng.uniform(0, 255, (40, 50)).astype(np.float32)
    for s in (0.8, 3, 9):
        y = core.blur(x, s)
        assert y.shape == x.shape and abs(y.mean() - x.mean()) < 2.0 and y.std() < x.std()
    assert abs(core.box_blur(x, 2).mean() - x.mean()) < 2.0


def test_label_components_counts_and_boxes():
    m = np.zeros((30, 40), bool)
    m[2:6, 3:9] = True
    m[10:20, 20:22] = True
    m[19, 22:30] = True  # L-shape joined
    m[25, 35] = True
    boxes = core.component_boxes(m)
    assert len(boxes) == 3
    assert boxes[0]["bbox"] == [20, 10, 10, 10]
    assert [3, 2, 6, 4] in [b["bbox"] for b in boxes]


def test_lab_roundtrip_and_hex():
    rgb = np.array([[255, 210, 31], [10, 20, 30], [128, 128, 128]], np.float32)
    back = core.lab_to_rgb(core.rgb_to_lab(rgb))
    assert np.abs(back - rgb).max() < 1.0
    assert core.hex_color([255, 210, 31]) == "#FFD21F"


def test_scan_edge_bars_finds_letterbox():
    rng = np.random.default_rng(3)
    f = np.zeros((4, 120, 80, 3), np.uint8)
    f[:, 30:90] = rng.integers(0, 255, (4, 60, 80, 3), dtype=np.uint8)
    bars = core.scan_edge_bars(f)
    assert bars["top"]["px"] == 30 and bars["bottom"]["px"] == 30
    assert bars["left"]["px"] == 0 and bars["top"]["style"] == "solid"


def test_kmeans_separates_clusters():
    x = np.concatenate([np.zeros((50, 3)), np.full((50, 3), 100.0)])
    c, lab = core.kmeans(x, 2)
    assert sorted(np.round(c[:, 0]).tolist()) == [0.0, 100.0]


def test_envelope_validates():
    env = core.make_envelope("video_re_detect_example_thing", "1.0.0", {"reference": "x.mp4"}, "ok",
                             [{"label": "x", "confidence": 1.2, "value": np.float32(1.5)}], {"a": 1})
    errs = core.validate_against(env, HERE / "envelope.schema.json")
    if errs == ["jsonschema not installed"]:
        pytest.skip("jsonschema not installed")
    assert errs == []
    assert env["results"][0]["confidence"] == 1.0


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg not installed")
def test_decode_video_sizes_and_times(tmp_path):
    clip = tmp_path / "c.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=25:d=1.2",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    frames, times, info = core.decode_video(str(clip), width=160, fps=5)
    assert frames.shape[1:] == (90, 160, 3) and len(frames) == 6
    assert np.allclose(np.diff(times), 0.2, atol=1e-3)
    assert info["analysis_scale"] == 2.0
    y, _, _ = core.decode_video(str(clip), width=None, fps=None, max_frames=3, mode="y")
    assert y.shape == (3, 180, 320) and y.dtype == np.uint8
