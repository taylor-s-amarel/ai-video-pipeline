import numpy as np
import pytest
from PIL import Image

import feathered_alpha_mask as fm


def test_rounded_rect_centre_edges_and_cap():
    m = fm.rounded_rect(200, 100, radius=20, feather=16)
    assert m[50, 100] == pytest.approx(0.98)
    assert m[0, 0] == 0 and m[50, 0] < 0.1
    row = m[50, :100]
    assert np.all(np.diff(row) >= -1e-6)  # rises monotonically towards the centre
    # the feather is a band, not a step
    assert ((row > 0.05) & (row < 0.93)).sum() >= 8


def test_hard_edge_option():
    m = fm.rounded_rect(50, 50, radius=0, feather=0, max_alpha=1.0)
    assert set(np.unique(m)) <= {0.0, 1.0}


def test_ellipse_and_edge_fade():
    e = fm.ellipse(100, 60, feather=10)
    assert e[30, 50] > 0.9 and e[0, 0] == 0
    f = fm.edge_fade(10, 100, bottom=40)
    assert f[0, 5] == 1 and f[99, 5] == 0 and f[70, 5] < f[50, 5]


def test_combine_image_apply():
    m = fm.combine(fm.rounded_rect(40, 30), fm.edge_fade(40, 30, top=10))
    img = fm.to_image(m)
    assert img.mode == "L" and img.size == (40, 30)
    out = fm.apply_to(Image.new("RGB", (40, 30), "red"), m)
    assert out.mode == "RGBA" and out.getpixel((20, 20))[3] > out.getpixel((20, 5))[3] > 0
    with pytest.raises(ValueError):
        fm.combine(m, np.ones((2, 2)))
    with pytest.raises(ValueError):
        fm.rounded_rect(0, 10)
