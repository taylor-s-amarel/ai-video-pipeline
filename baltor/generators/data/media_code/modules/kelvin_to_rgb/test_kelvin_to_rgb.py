import pytest

from kelvin_to_rgb import cmf, ffmpeg_colorchannelmixer, kelvin_rgb, kelvin_xyz, wb_gains


def test_cmf_peaks():
    assert cmf(555)[1] > cmf(450)[1] and cmf(445)[2] > cmf(600)[2] and cmf(600)[0] > cmf(500)[0]


def test_warm_neutral_cool():
    r, g, b = kelvin_rgb(2700)
    assert r == pytest.approx(1.0) and r > g > b
    r, g, b = kelvin_rgb(6500)
    assert min(r, g, b) > 0.9           # close to neutral
    r, g, b = kelvin_rgb(12000)
    assert b == pytest.approx(1.0) and b > r


def test_chromaticity_near_planckian_reference():
    X, Y, Z = kelvin_xyz(6500)
    x, y = X / (X + Y + Z), Y / (X + Y + Z)
    assert x == pytest.approx(0.3135, abs=0.004) and y == pytest.approx(0.3236, abs=0.006)


def test_gains_and_filter():
    r, g, b = wb_gains(6500, 4500)
    assert g == 1.0 and r > 1 and b < 1        # warming up
    assert ffmpeg_colorchannelmixer((1.1, 1.0, 0.9)) == "colorchannelmixer=rr=1.1000:gg=1.0000:bb=0.9000"
    with pytest.raises(ValueError):
        kelvin_rgb(500)
