import pytest

import godot_texture_import_presets as g

REAL_IMPORT = '''[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://b2aofu01vxvea"
path="res://.godot/imported/playerGrey_walk1.png-0000.ctex"
metadata={
"vram_texture": false
}

[deps]

source_file="res://art/playerGrey_walk1.png"
dest_files=["res://.godot/imported/playerGrey_walk1.png-0000.ctex"]

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
mipmaps/generate=false
process/fix_alpha_border=true
detect_3d/compress_to=1
'''


def test_import_text_has_remap_deps_params():
    text = g.import_file_text("res://art/tiles.png", "pixel-art-2d")
    parsed = g.parse_import(text)
    assert parsed["remap"] == {"importer": "texture", "type": "CompressedTexture2D"}
    assert parsed["deps"]["source_file"] == "res://art/tiles.png"
    p = parsed["params"]
    assert p["compress/mode"] == 0 and p["mipmaps/generate"] is False and p["detect_3d/compress_to"] == 0
    assert p["roughness/src_normal"] == ""


def test_presets_differ_where_they_should():
    assert g.preset_params("texture-3d")["compress/mode"] == 2
    assert g.preset_params("texture-3d")["mipmaps/generate"] is True
    assert g.preset_params("normal-map-3d")["compress/normal_map"] == 1
    assert g.preset_params("ui-lossless")["detect_3d/compress_to"] == 0
    with pytest.raises(KeyError):
        g.preset_params("blurry")
    with pytest.raises(ValueError):
        g.import_file_text("art/tiles.png", "pixel-art-2d")


def test_parse_real_godot_import_and_check():
    parsed = g.parse_import(REAL_IMPORT)
    assert parsed["remap"]["uid"] == "uid://b2aofu01vxvea"
    assert "vram_texture" in parsed["remap"]["metadata"]
    assert g.check_import(REAL_IMPORT, "smooth-2d") == []
    problems = g.check_import(REAL_IMPORT, "pixel-art-2d")
    assert problems == ["detect_3d/compress_to = 1, preset wants 0"]
    assert any("compress/mode" in p for p in g.check_import(REAL_IMPORT, "texture-3d"))


def test_project_settings_for_pixel_art():
    text = g.project_settings_text("pixel-art-2d")
    assert "[rendering]" in text and "textures/canvas_textures/default_texture_filter=0" in text
    assert 'window/stretch/scale_mode="integer"' in text
    assert "2d/snap/snap_2d_transforms_to_pixel=true" in text
    assert g.project_settings_text("texture-3d").startswith(";")


def test_material_tres():
    text = g.material_tres("res://art/tiles.png", "pixel-art-3d", unshaded=True, alpha_scissor=True)
    assert text.startswith('[gd_resource type="StandardMaterial3D" format=3]')
    assert "texture_filter = 0" in text and "shading_mode = 0" in text and "transparency = 2" in text
    assert "texture_filter = 3" in g.material_tres("res://a.png", "texture-3d")


def test_apply_to_tree_and_check_cli(tmp_path, capsys):
    (tmp_path / "project.godot").write_text("config_version=5\n")
    art = tmp_path / "art"
    art.mkdir()
    for n in ("a.png", "b.png", "notes.txt"):
        (art / n).write_bytes(b"x")
    (art / "b.png.import").write_text(REAL_IMPORT)
    written = g.apply_to_tree(tmp_path, "pixel-art-2d", "art/*")
    assert [w.name for w in written] == ["a.png.import"]
    assert 'source_file="res://art/a.png"' in (art / "a.png.import").read_text()
    assert g.main(["check", str(tmp_path), "--preset", "pixel-art-2d", "--glob", "art/*"]) == 1
    g.apply_to_tree(tmp_path, "pixel-art-2d", "art/*", overwrite=True)
    assert g.main(["check", str(tmp_path), "--preset", "pixel-art-2d", "--glob", "art/*"]) == 0


def test_apply_refuses_non_project(tmp_path):
    with pytest.raises(FileNotFoundError):
        g.apply_to_tree(tmp_path, "pixel-art-2d")
