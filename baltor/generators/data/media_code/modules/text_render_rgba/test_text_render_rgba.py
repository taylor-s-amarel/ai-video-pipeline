import os

import numpy as np
import pytest

from text_render_rgba import fit, render_text

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
pytestmark = pytest.mark.skipif(not os.path.exists(FONT), reason="DejaVu font not installed")


def test_fit_wraps_and_shrinks():
    size_wide, lines_wide = fit("SHE LIVED UNDERWATER FOR 14 DAYS", FONT, (900, 300))
    size_narrow, lines_narrow = fit("SHE LIVED UNDERWATER FOR 14 DAYS", FONT, (400, 300))
    assert size_narrow < size_wide or len(lines_narrow) > len(lines_wide)


def test_render_colour_alpha_and_bbox():
    img, info = render_text("HELLO 14", FONT, (400, 120), color="#FFD21F", stroke=3, opacity=0.98)
    a = np.asarray(img)
    assert img.size == (400, 120) and img.mode == "RGBA"
    assert a[..., 3].max() <= 250
    yellow = (a[..., 0] > 200) & (a[..., 1] > 170) & (a[..., 2] < 90) & (a[..., 3] > 200)
    assert yellow.sum() > 200
    x0, y0, x1, y1 = info["ink_bbox"]
    assert x1 - x0 > 200


def test_errors():
    with pytest.raises(ValueError):
        render_text("x", FONT, (100, 100), align="justify")
    with pytest.raises(ValueError):
        fit("word " * 200, FONT, (50, 20))
