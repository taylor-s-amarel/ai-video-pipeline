import numpy as np
import pytest

from sharpness_noise_check import check, laplacian_variance, noise_sigma


def checker(n=128, size=8):
    y, x = np.mgrid[0:n, 0:n]
    return (((x // size + y // size) % 2) * 200 + 25).astype(float)


def box_blur(a, r=3):
    k = 2 * r + 1
    p = np.pad(a, r, mode="edge")
    c = p.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def test_blur_lowers_sharpness():
    sharp = checker()
    assert laplacian_variance(sharp) > 10 * laplacian_variance(box_blur(sharp))


def test_noise_estimate_close_to_truth():
    rng = np.random.default_rng(0)
    flat = np.full((200, 200), 128.0)
    for sigma in (2.0, 5.0, 10.0):
        est = noise_sigma(flat + rng.normal(0, sigma, flat.shape))
        assert est == pytest.approx(sigma, rel=0.1)


def test_check_flags():
    rng = np.random.default_rng(1)
    assert "soft" in check(box_blur(checker(), 6))["flags"]
    assert "noisy" in check(checker() + rng.normal(0, 20, (128, 128)))["flags"]
    with pytest.raises(ValueError):
        noise_sigma(np.zeros((2, 2)))
