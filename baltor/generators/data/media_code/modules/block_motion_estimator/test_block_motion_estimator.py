import numpy as np
import pytest

from block_motion_estimator import block_vectors, describe, global_motion


def textured(h=96, w=128, seed=0):
    rng = np.random.default_rng(seed)
    return (rng.random((h, w)) * 255).astype(np.uint8)


@pytest.mark.parametrize("dx,dy", [(3, 0), (-2, 4), (0, -5)])
def test_recovers_shift(dx, dy):
    a = textured()
    b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
    mx, my, conf = global_motion(a, b, block=16, search=8)
    assert (mx, my) == (dx, dy) and conf > 0.8


def test_flat_frames_and_validation():
    flat = np.full((64, 64), 100, np.uint8)
    assert global_motion(flat, flat) == (0.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        block_vectors(flat, flat[:10])


def test_describe():
    assert describe(3, 0) == "content moves right (camera pans left)"
    assert describe(0.1, 0.2) == "static"
