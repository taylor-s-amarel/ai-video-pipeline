import shutil
import subprocess

import numpy as np
import pytest

from xstack_grid_layout import grid, xstack_filter


def test_grid_math():
    g = grid(2, 2, (1080, 1920), gutter=24, margin=40)
    assert g["cell"] == (488, 908)
    assert g["cells"][3] == (40 + 488 + 24, 40 + 908 + 24, 488, 908)
    assert g["layout"].startswith("40_40|552_40|")
    x, y, w, h = g["cells"][-1]
    assert x + w <= 1080 - 40 and y + h <= 1920 - 40


def test_errors():
    with pytest.raises(ValueError):
        grid(0, 2)
    with pytest.raises(ValueError):
        grid(2, 2, (100, 100), gutter=99)
    with pytest.raises(ValueError):
        xstack_filter(3, grid(2, 2))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_renders_quadrants():
    g = grid(2, 2, (64, 64), gutter=4, margin=2)
    graph, out = xstack_filter(4, g)
    argv = ["ffmpeg", "-nostdin", "-v", "error"]
    for c in ("red", "lime", "blue", "white"):
        argv += ["-f", "lavfi", "-i", f"color=c={c}:s=40x30:d=0.2:r=10"]
    argv += ["-filter_complex", graph + f";{out}format=rgb24[o]", "-map", "[o]", "-frames:v", "1", "-f", "rawvideo", "-"]
    r = subprocess.run(argv, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    img = np.frombuffer(r.stdout, np.uint8).reshape(64, 64, 3)
    assert img[10, 10, 0] > 200 and img[10, 50, 1] > 200 and img[50, 10, 2] > 200 and img[50, 50].min() > 200
    assert img[32, 32].max() < 30 and img[0, 0].max() < 30   # gutter and margin filled
