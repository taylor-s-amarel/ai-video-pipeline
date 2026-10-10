import numpy as np
import pytest

from gradient_map_duotone import DUOTONES, gradient_lut, gradient_map


def test_endpoints_map_to_stops():
    img = np.array([[[0, 0, 0], [255, 255, 255]]], np.uint8)
    out = gradient_map(img, DUOTONES["navy_yellow"])
    assert out[0, 0].tolist() == [0x0B, 0x1D, 0x3A] and out[0, 1].tolist() == [0xFF, 0xD2, 0x1F]


def test_three_stops_and_amount():
    lut = gradient_lut([(0, "#000000"), (0.5, "#FF0000"), (1, "#FFFFFF")])
    assert lut[128, 0] > 0.99 and lut[128, 1] < 0.02
    img = np.full((2, 2, 3), 100, np.uint8)
    assert np.array_equal(gradient_map(img, DUOTONES["plum_peach"], amount=0), img)


def test_errors():
    with pytest.raises(ValueError):
        gradient_lut([(0.2, "#000000"), (1, "#FFFFFF")])
    with pytest.raises(ValueError):
        gradient_map(np.zeros((1, 1, 3), np.uint8), DUOTONES["teal_cream"], amount=2)
