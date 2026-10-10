import numpy as np
import pytest

import wipe_transition_masks as wm

MASKS = [
    lambda p: wm.linear(64, 36, p, 30),
    lambda p: wm.radial(64, 36, p),
    lambda p: wm.clock(64, 36, p),
    lambda p: wm.diamond(64, 36, p),
    lambda p: wm.blinds(64, 36, p, 4),
]


@pytest.mark.parametrize("fn", MASKS)
def test_endpoints_and_monotonic(fn):
    assert fn(0.0).max() == 0.0
    assert fn(1.0).min() == 1.0
    means = [fn(p).mean() for p in np.linspace(0, 1, 11)]
    assert all(b >= a - 1e-6 for a, b in zip(means, means[1:]))


def test_linear_direction():
    m = wm.linear(100, 10, 0.5, angle_deg=0, softness=0)
    assert m[:, 0].min() == 1 and m[:, -1].max() == 0


def test_blend():
    a = np.zeros((4, 4, 3), np.uint8)
    b = np.full((4, 4, 3), 200, np.uint8)
    out = wm.blend(a, b, np.full((4, 4), 0.5, np.float32))
    assert out.dtype == np.uint8 and int(out[0, 0, 0]) == 100
    with pytest.raises(ValueError):
        wm.blend(a, b[:2], np.zeros((4, 4)))
