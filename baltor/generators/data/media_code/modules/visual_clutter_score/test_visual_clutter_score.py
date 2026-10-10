import numpy as np
import pytest
from PIL import Image, ImageDraw

from visual_clutter_score import calibrate, clutter_score, compare, edge_density


def background():
    y = np.linspace(40, 200, 360)[:, None]
    return np.repeat(y, 200, axis=1).astype(np.uint8)


def with_text(img, lines):
    im = Image.fromarray(img).convert("L")
    d = ImageDraw.Draw(im)
    for i in range(lines):
        d.text((10, 10 + i * 14), "FACT 1 SAY IT CLEARLY 86% 1,000", fill=255)
    return np.asarray(im)


def test_more_text_is_busier():
    bg = background()
    a, b = clutter_score(with_text(bg, 2)), clutter_score(with_text(bg, 20))
    assert clutter_score(bg) < a < b


def test_compare_and_range():
    bg = background()
    r = compare(bg, with_text(bg, 10))
    assert r["added"] > 0 and 0 <= r["with_overlays"] <= 100
    assert edge_density(np.zeros((10, 10))) == 0.0


def test_calibrate():
    assert calibrate([10, 12, 14, 30]) == pytest.approx(np.percentile([10, 12, 14, 30], 90) + 5, abs=0.01)
    with pytest.raises(ValueError):
        calibrate([])
