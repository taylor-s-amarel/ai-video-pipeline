import pytest

from image_fit_math import crop_for_cover, even, even_size, fit, upscale_factor


def test_cover_contain():
    c = fit((4000, 3000), (1080, 1920), "cover")
    assert c["size"] == (2560, 1920) and c["offset"] == (-740, 0)
    k = fit((4000, 3000), (1080, 1920), "contain")
    assert k["size"] == (1080, 810) and k["offset"] == (0, 555)
    assert fit((100, 50), (200, 200), "width")["size"] == (200, 100)
    assert fit((10, 10), (20, 30), "fill")["scale"] == (2.0, 3.0)
    with pytest.raises(ValueError):
        fit((1, 1), (1, 1), "stretch")


def test_crop_for_cover_inside():
    x, y, w, h = crop_for_cover((4000, 3000), (1080, 1920), focus=(0.95, 0.5))
    assert x + w == pytest.approx(4000) and w / h == pytest.approx(1080 / 1920)


def test_even_and_upscale():
    assert even(1081) == 1080 and even(1081, "up") == 1082 and even_size(607.6, 1080.2) == (608, 1080)
    assert upscale_factor((800, 600), (1080, 1920)) > 3
    assert upscale_factor((4000, 3000), (1080, 1920)) < 1
