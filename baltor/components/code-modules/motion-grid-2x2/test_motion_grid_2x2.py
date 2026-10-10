import shutil
import subprocess

import numpy as np
import pytest

from motion_grid_2x2 import cells, motion_grid


def test_cells():
    rects, (cw, ch) = cells((1080, 1920), 24, 40)
    assert (cw, ch) == (488, 908) and len(rects) == 4
    assert rects[3][0] + cw == 1040 and rects[3][1] + ch == 1880


def test_validation():
    with pytest.raises(ValueError):
        motion_grid("[0:v]", ["[1:v]"] * 3)
    with pytest.raises(ValueError):
        motion_grid("[0:v]", ["[1:v]"] * 4, grid_opacity=1.0)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_renders_and_panels_move():
    W, H = 96, 160
    graph, out = motion_grid("[0:v]", [f"[{i}:v]" for i in range(1, 5)], size=(W, H), gutter=6, margin=6,
                             fps=10, duration=1.0, grid_opacity=0.9, radius=4, feather=4, drift=0.3)
    argv = ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d=1:r=10"]
    for _ in range(4):
        argv += ["-f", "lavfi", "-i", "testsrc2=s=80x80:d=1:r=10"]
    argv += ["-filter_complex", graph + f";{out}format=gray[o]", "-map", "[o]", "-f", "rawvideo", "-"]
    r = subprocess.run(argv, capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    frames = np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W).astype(float)
    assert len(frames) == 10
    assert frames[0][2, 2] < 5                       # margin shows the background
    assert frames[0][H // 4, W // 4] > 5             # panel content
    assert np.abs(frames[9] - frames[0]).mean() > 1  # panels drift over time
