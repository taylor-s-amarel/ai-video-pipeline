import os

import numpy as np
from PIL import Image

from thumbnail_composer import compose, cover

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def photo(w=1600, h=1200):
    x = np.tile(np.linspace(80, 220, w), (h, 1))
    return Image.fromarray(np.stack([x, x * 0.9, x * 0.7], -1).astype(np.uint8))


def test_cover_size_and_focus():
    c = cover(photo(), (1280, 720), focus=(0.0, 0.5))
    assert c.size == (1280, 720)


def test_compose_fits_and_reports():
    font = FONT if os.path.exists(FONT) else None
    img, rep = compose(photo(), "SHE LIVED UNDERWATER FOR 14 DAYS", size=(640, 360), font_path=font,
                       text_box=(30, 30, 330, 300))
    assert img.size == (640, 360)
    assert rep["lines"] and " ".join(rep["lines"]) == "SHE LIVED UNDERWATER FOR 14 DAYS"
    assert rep["contrast_vs_median_bg"] > 1 and isinstance(rep["readable"], bool)
    # scrim darkens the text side
    arr = np.asarray(img).astype(float)
    assert arr[:, :20].mean() < arr[:, -20:].mean()
