import colorsys

import numpy as np
import pytest

import colour_space_convert as cs


def test_transfer_roundtrip():
    x = np.linspace(0, 1, 101)
    assert np.allclose(cs.linear_to_srgb(cs.srgb_to_linear(x)), x, atol=1e-9)
    assert cs.srgb_to_linear(0.5) == pytest.approx(0.214041, abs=1e-6)


def test_hsv_hsl_match_colorsys():
    rng = np.random.default_rng(0)
    cols = rng.random((200, 3))
    hsv = cs.rgb_to_hsv(cols)
    hls = np.array([colorsys.rgb_to_hls(*c) for c in cols])
    ref_hsv = np.array([colorsys.rgb_to_hsv(*c) for c in cols])
    assert np.allclose(hsv[:, 0], ref_hsv[:, 0] * 360, atol=1e-6)
    assert np.allclose(hsv[:, 1:], ref_hsv[:, 1:], atol=1e-9)
    hsl = cs.rgb_to_hsl(cols)
    assert np.allclose(hsl[:, 1], hls[:, 2], atol=1e-9) and np.allclose(hsl[:, 2], hls[:, 1], atol=1e-9)
    assert np.allclose(cs.hsv_to_rgb(hsv), cols, atol=1e-9)
    assert np.allclose(cs.hsl_to_rgb(hsl), cols, atol=1e-9)


def test_hex_and_luma():
    assert cs.hex_to_rgb("#FFD21F") == (255, 210, 31) and cs.hex_to_rgb("fff") == (255, 255, 255)
    assert cs.rgb_to_hex((255, 210, 31)) == "#FFD21F"
    assert cs.luma709([1, 1, 1]) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        cs.hex_to_rgb("#12")
