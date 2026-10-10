import numpy as np

from exposure_clipping_check import analyse


def ramp(lo=20, hi=230, shape=(50, 200)):
    x = np.tile(np.linspace(lo, hi, shape[1]), (shape[0], 1))
    return np.stack([x] * 3, -1).astype(np.uint8)


def test_good_exposure_no_flags():
    assert analyse(ramp())["flags"] == []


def test_clipped_and_crushed():
    img = ramp(0, 255)
    img[:, :40] = 0
    img[:, -40:] = 255
    flags = analyse(img)["flags"]
    assert "clipped_highlights" in flags and "crushed_shadows" in flags


def test_dark_bright_flat():
    assert "too_dark" in analyse(ramp(5, 60))["flags"]
    assert "too_bright" in analyse(ramp(200, 245))["flags"]
    assert "low_contrast" in analyse(ramp(120, 140))["flags"]
    assert analyse(np.full((10, 10), 128, np.uint8))["spread"] == 0
