import numpy as np
import pytest
from PIL import Image

from alpha_compositing import over, place, premultiply, stack, to_float, to_uint8, unpremultiply


def test_premultiply_roundtrip():
    a = np.random.default_rng(0).random((4, 4, 4)).astype(np.float32)
    a[..., 3] = np.clip(a[..., 3], 0.1, 1)
    assert np.allclose(unpremultiply(premultiply(a)), a, atol=1e-6)


def test_over_matches_pillow():
    rng = np.random.default_rng(1)
    s = rng.integers(0, 256, (8, 8, 4)).astype(np.uint8)
    d = rng.integers(0, 256, (8, 8, 4)).astype(np.uint8)
    ours = to_uint8(over(to_float(s), to_float(d)))
    ref = np.asarray(Image.alpha_composite(Image.fromarray(d, "RGBA"), Image.fromarray(s, "RGBA")))
    assert np.abs(ours.astype(int) - ref.astype(int)).max() <= 2


def test_place_clips_and_stack_caps():
    canvas = np.zeros((10, 10, 4), np.float32)
    canvas[..., 3] = 1
    layer = np.ones((4, 4, 4), np.float32)
    out = place(canvas, layer, 8, 8, 0.5)
    assert out[9, 9, 0] == pytest.approx(0.5) and out[0, 0, 0] == 0
    assert place(canvas, layer, 20, 20) is canvas
    f = stack((10, 10), [(np.full((10, 10, 3), 255, np.uint8), 0, 0, 0.98)])
    assert f[5, 5, 0] == pytest.approx(0.98)
    with pytest.raises(ValueError):
        stack((10, 10), [(np.zeros((2, 2, 3), np.uint8), 0, 0, 1.0)])
