import json
import random

import numpy as np
from PIL import Image

import texture_atlas_packer as t


def solid(w, h, colour):
    return Image.new("RGBA", (w, h), colour)


def test_no_overlap_and_inside_bounds_with_padding():
    rng = random.Random(7)
    sizes = {f"img{i:02d}": (rng.randint(4, 40), rng.randint(4, 40)) for i in range(40)}
    (aw, ah), placed = t.pack_sizes(sizes, padding=2, extrude=1)
    assert set(placed) == set(sizes)
    rects = list(placed.values())
    for r in rects:
        assert r.x >= 1 and r.y >= 1 and r.x + r.w <= aw and r.y + r.h <= ah
    def extruded(r):
        return t.Rect(r.x - 1, r.y - 1, r.w + 2, r.h + 2)

    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not a.intersects(b)
            assert not extruded(a).intersects(extruded(b))  # extruded borders never overlap


def test_power_of_two_and_deterministic():
    sizes = {"a": (30, 30), "b": (20, 10), "c": (5, 50)}
    s1 = t.pack_sizes(sizes)
    s2 = t.pack_sizes(dict(reversed(list(sizes.items()))))
    assert s1 == s2
    (w, h), _ = s1
    assert w & (w - 1) == 0 and h & (h - 1) == 0


def test_too_big_raises():
    try:
        t.pack_sizes({"huge": (5000, 10)}, max_size=4096)
    except ValueError as exc:
        assert "do not fit" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_pixels_copied_and_extruded():
    images = {"red": solid(8, 8, (255, 0, 0, 255)), "blue": solid(4, 12, (0, 0, 255, 255))}
    atlas, placed = t.build_atlas(images, padding=2, extrude=2)
    arr = np.asarray(atlas)
    r = placed["red"]
    assert (arr[r.y:r.y + r.h, r.x:r.x + r.w] == [255, 0, 0, 255]).all()
    # extruded border repeats the edge colour
    assert arr[r.y - 2, r.x].tolist() == [255, 0, 0, 255]
    assert arr[r.y + r.h + 1, r.x + r.w + 1].tolist() == [255, 0, 0, 255]


def test_json_and_tres(tmp_path):
    paths = []
    for i, c in enumerate([(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]):
        p = tmp_path / f"icon{i}.png"
        solid(10 + i, 10, c).save(p)
        paths.append(str(p))
    stem = tmp_path / "out" / "icons_atlas"
    assert t.main(paths + ["--out", str(stem), "--godot-res", "res://ui/icons_atlas.png"]) == 0
    data = json.loads(stem.with_suffix(".json").read_text())
    assert set(data["frames"]) == {"icon0", "icon1", "icon2"}
    assert data["meta"]["image"] == "icons_atlas.png"
    tres = (tmp_path / "out" / "icons_atlas_regions" / "icon2.tres").read_text()
    assert '[gd_resource type="AtlasTexture" format=3]' in tres and "region = Rect2(" in tres
