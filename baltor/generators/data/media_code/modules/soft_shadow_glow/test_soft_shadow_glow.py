import numpy as np
import pytest
from PIL import Image, ImageDraw

from soft_shadow_glow import drop_shadow, outer_glow


def layer():
    im = Image.new("RGBA", (100, 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([10, 10, 90, 30], fill=(255, 210, 31, 250))
    return im


def test_shadow_below_and_layer_intact():
    out, (ox, oy) = drop_shadow(layer(), offset=(0, 10), blur=4, opacity=0.5)
    a = np.asarray(out)
    assert out.width > 100 and out.height > 40
    assert a[oy + 20, ox + 50, 0] >= 250           # original pixel on top (alpha 250 over the shadow)
    below = a[oy + 38, ox + 50, 3]
    above = a[oy + 2, ox + 50, 3]
    assert below > above                            # shadow falls downward


def test_glow_surrounds():
    out, (ox, oy) = outer_glow(layer(), radius=6, spread=2, color="#FFFFFF", opacity=0.8)
    a = np.asarray(out)[..., 3]
    assert a[oy + 5, ox + 50] > 0 and a[oy + 35, ox + 50] > 0 and a[oy + 20, ox + 3] > 0


def test_validation():
    with pytest.raises(ValueError):
        drop_shadow(layer(), opacity=2)
