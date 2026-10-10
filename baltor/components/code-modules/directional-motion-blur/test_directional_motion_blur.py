import numpy as np
import pytest

import directional_motion_blur as mb


def test_horizontal_blur_spreads_vertical_line_only_horizontally():
    img = np.zeros((20, 40), np.float32)
    img[:, 20] = 1.0
    out = mb.motion_blur(img, 10, 0)
    assert out[10].sum() == pytest.approx(1.0, abs=1e-5)
    assert (out[:, 14:27] > 0).any(axis=0).sum() >= 9
    assert np.allclose(out[0], out[19])


def test_horizontal_blur_leaves_horizontal_stripes():
    img = np.zeros((20, 40), np.float32)
    img[::2] = 1.0
    assert np.allclose(mb.motion_blur(img, 15, 0), img)


def test_uint8_and_zero_length():
    img = (np.arange(48).reshape(4, 4, 3) * 5).astype(np.uint8)
    assert np.array_equal(mb.motion_blur(img, 0), img)
    assert mb.motion_blur(img, 3, 45).dtype == np.uint8


def test_profile_and_kernel():
    p = mb.whip_pan_profile(9, 100)
    assert max(p) == pytest.approx(100) and p[0] < 20 and p == pytest.approx(p[::-1])
    k = mb.blur_kernel(7, 0)
    assert k.sum() == pytest.approx(1) and k[3].sum() == pytest.approx(1)
