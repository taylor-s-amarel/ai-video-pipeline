import numpy as np
import pytest
from PIL import Image

from rounded_panel import panel, paste_offset


def test_alpha_cap_and_corners():
    p = panel((200, 80), radius=30, opacity=0.6)
    a = np.asarray(p)[..., 3]
    cx, cy = p.width // 2, p.height // 2
    assert abs(int(a[cy, cx]) - 153) <= 2
    assert a[2, 2] == 0  # rounded corner and margin are transparent


def test_feather_is_soft():
    a = np.asarray(panel((200, 80), radius=10, opacity=0.9, feather=8))[..., 3]
    row = a[a.shape[0] // 2]
    assert len(set(row[:30].tolist())) > 8   # gradual ramp, not a step


def test_gradient_border_and_validation():
    p = panel((100, 100), color="#000000", gradient_to="#FFFFFF", border="#FFD21F", border_px=2, opacity=0.8)
    arr = np.asarray(p)
    assert arr[10, 50, 0] < arr[90, 50, 0] or arr[10, 50, 1] > 150
    with pytest.raises(ValueError):
        panel((10, 10), opacity=1.0)
    assert paste_offset((100, 200), feather=4) == (90, 190)


def test_composites():
    frame = Image.new("RGBA", (300, 200), (255, 255, 255, 255))
    frame.alpha_composite(panel((200, 80), opacity=0.5), paste_offset((50, 60)))
    assert frame.getpixel((150, 100))[0] < 160
