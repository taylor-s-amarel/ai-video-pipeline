import shutil
import subprocess

import numpy as np
import pytest

from aspect_reframe_filters import blur_pad, contain, cover, output_size


def run(vf=None, graph=None, out=None, w=90, h=160):
    argv = ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:d=0.1:r=10"]
    argv += ["-vf", vf + ",format=gray"] if vf else ["-filter_complex", graph + f";{out}format=gray[o]", "-map", "[o]"]
    r = subprocess.run(argv + ["-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, timeout=60,
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    return np.frombuffer(r.stdout, np.uint8).reshape(h, w)


def test_strings_and_validation():
    assert cover(1081, 1920).startswith("scale=1080:1920:force_original_aspect_ratio=increase")
    assert "pad=1080:1920" in contain(1080, 1920)
    with pytest.raises(ValueError):
        contain(10, 10, color="red;drawbox")
    with pytest.raises(ValueError):
        cover(10, 10, focus=(2, 0))
    with pytest.raises(ValueError):
        blur_pad(10, 10, darken=1.5)
    assert output_size(1920, 1080, 1080, 1920, "cover")[0] == 3413
    assert output_size(1920, 1080, 1080, 1920, "contain")[:2] == (1080, 608)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_rendered_sizes_and_bars():
    img = run(contain(90, 160))
    assert img[0].max() < 20 and img[80].max() > 50            # bars on top, content in the middle
    img = run(cover(90, 160))
    assert img[0].mean() > 20                                    # filled to the edge
    g, out = blur_pad(90, 160, sigma=5, darken=0.2)
    img = run(graph=g, out=out)
    assert img[0].mean() > 5                                     # blurred fill instead of black bars
