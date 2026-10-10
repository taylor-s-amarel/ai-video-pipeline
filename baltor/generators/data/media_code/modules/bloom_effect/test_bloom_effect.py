import numpy as np
import pytest

from bloom_effect import bloom, highlights


def spot():
    img = np.full((64, 64, 3), 20, np.uint8)
    img[28:36, 28:36] = 255
    return img


def test_glow_spreads_around_bright_spot():
    out = bloom(spot(), radii=(4,), intensity=1.0)
    assert out[32, 20, 0] > 20 and out[32, 32, 0] == 255
    assert out[2, 2, 0] <= 22


def test_dark_image_unchanged():
    dark = np.full((16, 16, 3), 40, np.uint8)
    assert np.array_equal(bloom(dark), dark)


def test_soft_knee_and_alpha():
    v = highlights(np.array([[[0.6] * 3, [0.75] * 3, [0.9] * 3]]), 0.75, 0.1)
    assert v[0, 0, 0] == 0 and 0 < v[0, 1, 0] < 0.75 and v[0, 2, 0] == pytest.approx(0.9)
    rgba = np.dstack([spot(), np.full((64, 64), 77, np.uint8)])
    assert bloom(rgba)[..., 3].max() == 77
    with pytest.raises(ValueError):
        bloom(spot(), mode="overlay")
