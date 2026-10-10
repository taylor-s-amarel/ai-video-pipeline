import shutil
import subprocess

import numpy as np
import pytest

from layer_stack_compositor import Layer, compose, validate


def test_opacity_cap_enforced_or_clamped():
    with pytest.raises(ValueError, match="0.98"):
        compose([Layer(0, opacity=1.0)])
    layers = [Layer(0, opacity=1.0)]
    compose(layers, clamp=True)
    assert layers[0].opacity == 0.98


def test_validation_messages():
    probs = validate([Layer(0, blend="sparkle"), Layer(1, start=2, end=1), Layer(2, start=1)])
    assert len(probs) == 3


def test_graph_text():
    g, out = compose([Layer(0, 0.9), Layer(1, 0.35, "screen", start=1, end=3)], size=(64, 64), fps=10, duration=2)
    assert out == "[stack]" and "blend=all_mode=screen:all_opacity=0.35" in g
    assert "colorchannelmixer=aa=0.9" in g and "between(t,1,3)" in g


def render(graph, out, inputs, w, h):
    argv = ["ffmpeg", "-nostdin", "-v", "error"]
    for src in inputs:
        argv += ["-f", "lavfi", "-i", src]
    argv += ["-filter_complex", graph + f";{out}format=rgb24[o]", "-map", "[o]", "-frames:v", "1",
             "-f", "rawvideo", "-"]
    r = subprocess.run(argv, capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    return np.frombuffer(r.stdout, np.uint8).reshape(h, w, 3).astype(float)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_rendered_values_match_blend_maths():
    # grey 128 at 0.5 over black, then white screened at 0.5
    g, out = compose([Layer(0, 0.5), Layer(1, 0.5, "screen")], size=(32, 32), fps=10, duration=0.5)
    img = render(g, out, ["color=c=0x808080:s=32x32:d=1:r=10", "color=c=white:s=32x32:d=1:r=10"], 32, 32)
    base = 128 * 0.5                      # normal at 50% over black
    screened = 255 - (255 - base) * (255 - 255) / 255
    expected = base + (screened - base) * 0.5
    assert abs(img[16, 16, 0] - expected) < 4


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_positioned_layer():
    g, out = compose([Layer(0, 0.98, x=8, y=8, w=16, h=16)], size=(32, 32), fps=10, duration=0.5)
    img = render(g, out, ["color=c=red:s=4x4:d=1:r=10"], 32, 32)
    assert img[16, 16, 0] > 200 and img[2, 2, 0] < 10
