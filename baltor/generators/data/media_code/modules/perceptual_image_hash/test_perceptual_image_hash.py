import io

import numpy as np
from PIL import Image, ImageDraw

from perceptual_image_hash import ahash, dhash, find_near_duplicates, hamming, phash, to_hex


def picture(seed=0, size=(320, 240)):
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", size, (30, 60, 90))
    d = ImageDraw.Draw(img)
    for _ in range(12):
        x, y = rng.integers(0, size[0]), rng.integers(0, size[1])
        r = int(rng.integers(10, 60))
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v) for v in rng.integers(0, 255, 3)))
    return img


def jpeg_roundtrip(img, q=40):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q)
    return Image.open(io.BytesIO(buf.getvalue()))


def test_robust_to_resize_and_jpeg():
    a = picture(1)
    b = jpeg_roundtrip(a.resize((160, 120)))
    for fn in (ahash, dhash, phash):
        assert hamming(fn(a), fn(b)) <= 8


def test_different_images_differ():
    for fn in (dhash, phash):
        assert hamming(fn(picture(1)), fn(picture(2))) > 12


def test_helpers():
    h = phash(picture(3))
    assert len(to_hex(h)) == 16 and hamming(h, h) == 0
    pairs = find_near_duplicates({"a": phash(picture(1)), "a_small": phash(picture(1).resize((100, 75))),
                                  "b": phash(picture(2))})
    assert [(p[0], p[1]) for p in pairs] == [("a", "a_small")]
