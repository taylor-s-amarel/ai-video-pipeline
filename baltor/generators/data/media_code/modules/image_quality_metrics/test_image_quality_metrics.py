import math

import numpy as np
import pytest

from image_quality_metrics import mse, psnr, ssim


def img(seed=0, shape=(64, 64, 3)):
    rng = np.random.default_rng(seed)
    base = np.cumsum(rng.normal(0, 4, shape), axis=1)
    return np.clip(base - base.min(), 0, 255).astype(np.uint8)


def test_identical():
    a = img()
    assert mse(a, a) == 0 and psnr(a, a) == math.inf
    assert ssim(a, a) == pytest.approx(1.0)


def test_psnr_known_value():
    a = np.zeros((10, 10), np.uint8)
    b = np.full((10, 10), 10, np.uint8)
    assert psnr(a, b) == pytest.approx(10 * math.log10(255 ** 2 / 100))


def test_ssim_orders_degradations():
    a = img(1)
    rng = np.random.default_rng(2)
    light = np.clip(a + rng.normal(0, 3, a.shape), 0, 255).astype(np.uint8)
    heavy = np.clip(a + rng.normal(0, 30, a.shape), 0, 255).astype(np.uint8)
    assert ssim(a, light) > ssim(a, heavy) > 0
    s, m = ssim(a, light, return_map=True)
    assert m.shape == (54, 54)


def test_validation():
    with pytest.raises(ValueError):
        mse(np.zeros((2, 2)), np.zeros((3, 3)))
    with pytest.raises(ValueError):
        ssim(np.zeros((5, 5)), np.zeros((5, 5)))
