import json

import numpy as np
from PIL import Image

import sprite_sheet_slicer as s

COLOURS = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255),
           (255, 0, 255, 255), (0, 255, 255, 255), (128, 128, 128, 255), (255, 128, 0, 255)]


def grid_sheet(cols=4, rows=2, size=16, margin=1, spacing=2, empty=()):
    w = margin * 2 + cols * size + (cols - 1) * spacing
    h = margin * 2 + rows * size + (rows - 1) * spacing
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            if i in empty:
                continue
            x = margin + c * (size + spacing)
            y = margin + r * (size + spacing)
            img.paste(Image.new("RGBA", (size - 4, size - 4), COLOURS[i % len(COLOURS)]), (x + 2, y + 2))
    return img


def test_grid_slicing_with_margin_and_spacing():
    img = grid_sheet()
    frames = s.slice_grid(img, 16, 16, margin=1, spacing=2)
    assert len(frames) == 8
    assert (frames[0].x, frames[0].y) == (1, 1)
    assert (frames[1].x, frames[1].y) == (19, 1)
    assert (frames[4].x, frames[4].y) == (1, 19)


def test_grid_skips_empty_cells_unless_asked():
    img = grid_sheet(empty=(3, 7))
    assert len(s.slice_grid(img, 16, 16, margin=1, spacing=2)) == 6
    assert len(s.slice_grid(img, 16, 16, margin=1, spacing=2, skip_empty=False)) == 8


def test_detect_finds_each_sprite_in_reading_order():
    img = grid_sheet()
    frames = s.detect_sprites(img)
    assert len(frames) == 8
    assert all((f.w, f.h) == (12, 12) for f in frames)
    assert frames[0].x < frames[1].x and frames[0].y == frames[1].y
    assert frames[4].y > frames[0].y


def test_detect_connectivity_and_min_area():
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    px = img.load()
    px[2, 2] = px[3, 3] = (255, 255, 255, 255)  # diagonal neighbours
    px[8, 8] = (255, 255, 255, 255)  # a lone speck
    assert len(s.detect_sprites(img, min_area=1, connectivity=8)) == 2
    assert len(s.detect_sprites(img, min_area=1, connectivity=4)) == 3
    assert len(s.detect_sprites(img, min_area=2, connectivity=8)) == 1


def test_aseprite_hash_and_array_forms_with_tags():
    frames_hash = {
        "frames": {"hero 0.aseprite": {"frame": {"x": 0, "y": 0, "w": 16, "h": 16}, "duration": 100},
                   "hero 1.aseprite": {"frame": {"x": 16, "y": 0, "w": 16, "h": 16}, "duration": 200},
                   "hero 2.aseprite": {"frame": {"x": 32, "y": 0, "w": 16, "h": 16}, "duration": 100}},
        "meta": {"image": "hero.png", "frameTags": [{"name": "walk", "from": 0, "to": 2, "direction": "pingpong"}]},
    }
    frames, tags, meta = s.parse_aseprite_json(frames_hash)
    assert [f.duration_ms for f in frames] == [100, 200, 100]
    assert tags[0].frames == [0, 1, 2, 1]
    array_form = {"frames": [dict(v, filename=k) for k, v in frames_hash["frames"].items()], "meta": {}}
    frames2, tags2, _ = s.parse_aseprite_json(array_form)
    assert [f.x for f in frames2] == [0, 16, 32] and tags2 == []


def test_spriteframes_tres_structure():
    frames = [s.Frame(0, 0, 0, 16, 16, duration_ms=100), s.Frame(1, 16, 0, 16, 16, duration_ms=200)]
    text = s.spriteframes_tres("res://art/hero.png", frames, {"walk": [0, 1]}, fps=10)
    assert text.startswith('[gd_resource type="SpriteFrames" format=3]')
    assert 'path="res://art/hero.png"' in text
    assert "region = Rect2(16, 0, 16, 16)" in text
    assert '"name": &"walk"' in text
    assert '"duration": 2.0' in text  # 200 ms at 10 fps = 2 frames of relative duration
    assert text.count("[sub_resource") == 2


def test_export_and_cli_roundtrip(tmp_path):
    sheet = tmp_path / "sheet.png"
    grid_sheet().save(sheet)
    out = tmp_path / "frames"
    rc = s.main(["grid", str(sheet), "--size", "16x16", "--margin", "1", "--spacing", "2", "--out", str(out),
                 "--tres", str(tmp_path / "hero.tres"), "--res-path", "res://sheet.png"])
    assert rc == 0
    data = json.loads((out / "frames.json").read_text())
    assert len(data["frames"]) == 8
    first = Image.open(out / "000.png")
    assert first.size == (16, 16)
    assert np.asarray(first)[8, 8].tolist() == list(COLOURS[0])
    assert (tmp_path / "hero.tres").read_text().count("AtlasTexture_") >= 8
