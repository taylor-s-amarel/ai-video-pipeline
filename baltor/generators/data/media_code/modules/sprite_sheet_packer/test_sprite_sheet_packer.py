import numpy as np
import pytest
from PIL import Image, ImageDraw

from sprite_sheet_packer import pack, unpack


def frame(i):
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([10 + i, 12, 40 + i, 50], fill=(255, 100 + i * 10, 0, 255))
    return im


def test_pack_no_overlap_and_roundtrip():
    frames = {f"walk_{i}": frame(i) for i in range(6)}
    sheet, atlas = pack(frames, max_width=128, padding=2)
    rects = [(f["x"], f["y"], f["w"], f["h"]) for f in atlas["frames"].values()]
    for i, a in enumerate(rects):
        assert a[0] + a[2] <= sheet.width and a[1] + a[3] <= sheet.height
        for b in rects[i + 1:]:
            assert a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1]
    for name, img in frames.items():
        assert np.array_equal(np.asarray(unpack(sheet, atlas, name)), np.asarray(img))


def test_trim_and_pow2():
    sheet, atlas = pack({"a": frame(0)}, trim=True, pow2=True)
    f = atlas["frames"]["a"]
    assert f["w"] < 64 and f["offset"] == [10, 12]
    assert sheet.width & (sheet.width - 1) == 0 and sheet.height & (sheet.height - 1) == 0


def test_errors():
    with pytest.raises(ValueError):
        pack({})
    with pytest.raises(ValueError):
        pack({"big": Image.new("RGBA", (300, 10), (255, 0, 0, 255))}, max_width=100)
