import shutil
import subprocess

import numpy as np
import pytest

from overlay_timeline_filter import Item, build, conflicts


def test_graph_and_validation():
    g, out = build("[0:v]", [Item(1, x=10, y="H*0.7", start=2, end=5, fade=0.25)])
    assert "setpts=PTS-STARTPTS+2/TB" in g and "fade=t=out:st=4.75:d=0.25:alpha=1" in g
    assert "y='H*0.7'" in g and g.endswith("[ov_out]")
    for bad in (Item(1, start=2, end=1), Item(1, opacity=1.0), Item(1, start=0, end=0.3, fade=0.2)):
        with pytest.raises(ValueError):
            build("[0:v]", [bad])


def test_conflicts():
    a = Item(1, x=0, y=0, w=100, h=100, start=0, end=3)
    b = Item(2, x=50, y=50, w=100, h=100, start=2, end=4)
    c = Item(3, x=500, y=500, w=10, h=10, start=0, end=4)
    d = Item(4, x="W/2", y=0, start=5, end=6)
    assert conflicts([a, b, c, d]) == [(0, 1)]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_overlay_appears_only_in_window():
    g, out = build("[0:v]", [Item(1, x=8, y=8, start=0.4, end=0.8, fade=0.0)])
    argv = ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=black:s=32x32:d=1.2:r=10",
            "-f", "lavfi", "-i", "color=white:s=16x16:d=1.2:r=10",
            "-filter_complex", g + f";{out}format=gray[o]", "-map", "[o]", "-f", "rawvideo", "-"]
    r = subprocess.run(argv, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    frames = np.frombuffer(r.stdout, np.uint8).reshape(-1, 32, 32)
    centre = [int(f[16, 16]) for f in frames]
    assert centre[2] < 20 and centre[5] > 200 and centre[10] < 20
