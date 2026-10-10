import json
import struct
from pathlib import Path

import pytest

import gltf_glb_inspector as g

HERE = Path(__file__).resolve().parent


def test_shipped_fixture_matches_builder_and_parses():
    data = (HERE / "fixtures" / "tiny_cube.glb").read_bytes()
    assert data == g.make_cube_glb(animated=True)  # fixture is reproducible
    r = g.inspect(data)
    c = r["counts"]
    assert (c["meshes"], c["primitives"], c["nodes"], c["materials"], c["animations"]) == (1, 1, 1, 1, 1)
    assert (c["vertices"], c["triangles"]) == (8, 12)
    assert r["bounds"]["min"] == [-0.5, -0.5, -0.5] and r["bounds"]["max"] == [0.5, 0.5, 0.5]
    assert r["animations"][0] == {"name": "Bounce", "channels": 1, "duration_s": 1.0}
    assert r["asset"]["copyright"] == "CC0-1.0 test fixture"


def test_node_translation_and_scale_move_bounds():
    r = g.inspect(g.make_cube_glb(size=2.0, translation=(10, 0, 0), scale=(1, 3, 1)))
    assert r["bounds"]["min"] == [9.0, -3.0, -1.0]
    assert r["bounds"]["max"] == [11.0, 3.0, 1.0]
    assert r["bounds"]["largest_dimension"] == 6.0


def test_rotation_quaternion():
    glb = g.make_cube_glb(size=2.0, scale=(4, 1, 1))
    gltf, binary = g.read_glb(glb)
    gltf["nodes"][0]["rotation"] = [0, 0, 0.7071068, 0.7071068]  # 90 degrees about Z
    b = g.world_bounds(gltf)
    assert b["size"] == pytest.approx([2.0, 8.0, 2.0], abs=1e-4)


def test_required_extensions_are_flagged():
    r = g.inspect(g.make_cube_glb(extensions_required=["KHR_draco_mesh_compression"]))
    assert "KHR_draco_mesh_compression" in r["extensions_required"]
    assert any("Draco" in i for i in r["issues"])


def test_bad_inputs_raise():
    with pytest.raises(g.GLTFError):
        g.read_glb(b"NOPE" + b"\x00" * 30)
    glb = bytearray(g.make_cube_glb())
    with pytest.raises(g.GLTFError):
        g.read_glb(bytes(glb[:-8]))  # truncated download
    struct.pack_into("<I", glb, 4, 1)
    with pytest.raises(g.GLTFError):
        g.read_glb(bytes(glb))


def test_gltf_json_with_data_uri_and_missing_external_image(tmp_path):
    gltf = g.gltf_with_data_uri(g.make_cube_glb())
    gltf["images"] = [{"uri": "textures/albedo.png"}]
    p = tmp_path / "cube.gltf"
    p.write_text(json.dumps(gltf))
    r = g.inspect(p)
    assert r["buffers"][0]["source"] == "data-uri"
    assert r["images"][0]["exists"] is False
    assert any("external image missing" in i for i in r["issues"])


def test_unit_warnings():
    r = g.inspect(g.make_cube_glb(size=250.0, scale=(10, 10, 10)))
    assert any("centimetres" in i for i in r["issues"])


def test_cli_exit_codes(tmp_path, capsys):
    ok = tmp_path / "ok.glb"
    ok.write_bytes(g.make_cube_glb())
    draco = tmp_path / "draco.glb"
    draco.write_bytes(g.make_cube_glb(extensions_required=["KHR_draco_mesh_compression"]))
    assert g.main([str(ok)]) == 0
    assert g.main([str(draco), "--deny-ext", "KHR_draco_mesh_compression"]) == 1
    assert g.main([str(ok), "--max-triangles", "5"]) == 1
    assert g.main([str(ok), "--json"]) == 0
    out = capsys.readouterr().out
    assert '"triangles": 12' in out


def test_zero_length_animation_flagged():
    gltf, binary = g.read_glb(g.make_cube_glb(animated=True))
    gltf["accessors"][2]["max"] = [0.0]
    import json as _j
    body = _j.dumps(gltf).encode()
    body += b" " * ((4 - len(body) % 4) % 4)
    total = 12 + 8 + len(body) + 8 + len(binary)
    glb = (struct.pack("<III", g.GLB_MAGIC, 2, total) + struct.pack("<II", len(body), g.CHUNK_JSON) + body
           + struct.pack("<II", len(binary), g.CHUNK_BIN) + binary)
    r = g.inspect(glb)
    assert any("zero duration" in i for i in r["issues"])
