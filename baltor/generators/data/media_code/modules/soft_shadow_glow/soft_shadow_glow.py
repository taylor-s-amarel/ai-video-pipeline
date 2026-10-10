"""Drop shadows and outer glows for RGBA layers (Pillow).

Both effects come from the layer's own alpha: a shadow is the alpha blurred,
tinted, offset and placed under the layer; a glow is the alpha dilated
(``spread``), blurred and tinted around it. The canvas grows so nothing is
clipped, and the function returns the new image plus the offset of the
original layer inside it.

Usage::

    from soft_shadow_glow import drop_shadow, outer_glow
    img, (ox, oy) = drop_shadow(title_rgba, offset=(0, 8), blur=14, color="#000000", opacity=0.55)
    img, (ox, oy) = outer_glow(title_rgba, radius=18, spread=3, color="#FFD21F", opacity=0.6)
"""

from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _tinted(alpha: Image.Image, color: str, opacity: float) -> Image.Image:
    if not 0 <= opacity <= 1:
        raise ValueError("opacity must be within [0, 1]")
    a = alpha.point(lambda v: int(v * opacity))
    out = Image.new("RGBA", alpha.size, _rgb(color) + (0,))
    out.putalpha(a)
    return out


def drop_shadow(layer: Image.Image, offset=(0, 8), blur: float = 12.0, color: str = "#000000",
                opacity: float = 0.5):
    layer = layer.convert("RGBA")
    m = int(blur * 2 + max(abs(offset[0]), abs(offset[1]))) + 2
    W, H = layer.width + 2 * m, layer.height + 2 * m
    alpha = Image.new("L", (W, H), 0)
    alpha.paste(layer.getchannel("A"), (m + offset[0], m + offset[1]))
    if blur > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(blur))
    out = _tinted(alpha, color, opacity)
    out.alpha_composite(layer, (m, m))
    return out, (m, m)


def outer_glow(layer: Image.Image, radius: float = 16.0, spread: int = 2, color: str = "#FFFFFF",
               opacity: float = 0.6):
    layer = layer.convert("RGBA")
    m = int(radius * 2 + spread) + 2
    W, H = layer.width + 2 * m, layer.height + 2 * m
    alpha = Image.new("L", (W, H), 0)
    alpha.paste(layer.getchannel("A"), (m, m))
    if spread > 0:
        alpha = alpha.filter(ImageFilter.MaxFilter(spread * 2 + 1))
    if radius > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius))
    out = _tinted(alpha, color, opacity)
    out.alpha_composite(layer, (m, m))
    return out, (m, m)


def alpha_union(a: Image.Image, b: Image.Image) -> Image.Image:
    return ImageChops.lighter(a.getchannel("A"), b.getchannel("A"))
