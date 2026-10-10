"""Inspect glTF 2.0 / GLB files without a 3D library: counts, bounds, extensions, problems.

Reads the GLB header and JSON chunk (or a ``.gltf`` JSON file) and reports what
an agent needs before importing a downloaded model into Godot 4, Blender or a
video render:

* counts of scenes, nodes, meshes, primitives, materials, textures, images,
  animations (with durations), skins, cameras and punctual lights;
* vertex and triangle totals from accessor counts;
* world-space bounding box of the default scene from POSITION min/max and
  node transforms (TRS or matrix), so you can scale a model before placing it;
* ``extensionsUsed`` / ``extensionsRequired`` and flags for the ones that
  commonly break imports (Draco, meshopt, KTX2/Basis, WebP);
* the ``asset.copyright`` and ``asset.generator`` fields (licence evidence);
* image sources (embedded, data URI or external file, and whether the
  external files exist next to the ``.gltf``).

The binary chunk is never decoded beyond its length, so the inspector is fast
and safe on untrusted files. ``make_cube_glb`` builds tiny valid GLBs for tests.

Usage::

    python gltf_glb_inspector.py model.glb [more.glb ...] [--json] [--max-triangles 200000]
                                 [--deny-ext KHR_draco_mesh_compression]

Exit status 1 when a file cannot be parsed, needs a denied extension or exceeds --max-triangles.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import struct
import sys
from pathlib import Path

GLB_MAGIC = 0x46546C67  # b"glTF"
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942
COMPONENT_SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
RISKY_EXTENSIONS = {
    "KHR_draco_mesh_compression": "Draco-compressed geometry: decode first (e.g. with glTF-Transform) for importers without Draco support",
    "EXT_meshopt_compression": "meshopt-compressed buffers: confirm the target importer supports them",
    "KHR_texture_basisu": "KTX2/Basis textures: many importers cannot read them; convert to PNG/JPEG",
    "EXT_texture_webp": "WebP textures: check the importer; a PNG/JPEG fallback may exist",
}


class GLTFError(ValueError):
    """The file is not valid glTF/GLB."""


def read_glb(data: bytes) -> tuple[dict, bytes | None]:
    if len(data) < 20:
        raise GLTFError("file too short for GLB")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC:
        raise GLTFError("not a GLB (bad magic)")
    if version != 2:
        raise GLTFError(f"GLB version {version} is not 2")
    if length != len(data):
        raise GLTFError(f"header length {length} != file size {len(data)} (truncated download?)")
    offset, gltf, binary = 12, None, None
    while offset + 8 <= length:
        chunk_len, chunk_type = struct.unpack_from("<II", data, offset)
        start, end = offset + 8, offset + 8 + chunk_len
        if end > length:
            raise GLTFError("chunk runs past end of file")
        if chunk_type == CHUNK_JSON and gltf is None:
            try:
                gltf = json.loads(data[start:end].decode("utf-8").rstrip(" \x00"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise GLTFError(f"JSON chunk does not parse: {exc}") from exc
        elif chunk_type == CHUNK_BIN and binary is None:
            binary = data[start:end]
        offset = end + ((4 - chunk_len % 4) % 4 if chunk_len % 4 else 0)
    if gltf is None:
        raise GLTFError("no JSON chunk")
    return gltf, binary


def load(path_or_bytes: str | Path | bytes) -> tuple[dict, bytes | None, Path | None]:
    if isinstance(path_or_bytes, (bytes, bytearray)):
        data, path = bytes(path_or_bytes), None
    else:
        path = Path(path_or_bytes)
        data = path.read_bytes()
    if data[:4] == b"glTF":
        gltf, binary = read_glb(data)
    else:
        try:
            gltf, binary = json.loads(data.decode("utf-8")), None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GLTFError(f"neither GLB nor glTF JSON: {exc}") from exc
    if not isinstance(gltf, dict) or "asset" not in gltf:
        raise GLTFError("missing required 'asset' object")
    return gltf, binary, path


# ---------------------------------------------------------------- math

def _mat_mul(a: list[float], b: list[float]) -> list[float]:
    """4x4 column-major multiply (glTF convention)."""
    out = [0.0] * 16
    for c in range(4):
        for r in range(4):
            out[c * 4 + r] = sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
    return out


def node_matrix(node: dict) -> list[float]:
    if "matrix" in node:
        return [float(v) for v in node["matrix"]]
    tx, ty, tz = node.get("translation", [0, 0, 0])
    qx, qy, qz, qw = node.get("rotation", [0, 0, 0, 1])
    sx, sy, sz = node.get("scale", [1, 1, 1])
    n = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw) or 1.0
    qx, qy, qz, qw = qx / n, qy / n, qz / n, qw / n
    r = [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy + qz * qw), 2 * (qx * qz - qy * qw),
         2 * (qx * qy - qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz + qx * qw),
         2 * (qx * qz + qy * qw), 2 * (qy * qz - qx * qw), 1 - 2 * (qx * qx + qy * qy)]
    return [r[0] * sx, r[1] * sx, r[2] * sx, 0.0,
            r[3] * sy, r[4] * sy, r[5] * sy, 0.0,
            r[6] * sz, r[7] * sz, r[8] * sz, 0.0,
            float(tx), float(ty), float(tz), 1.0]


def _transform(m: list[float], p: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = p
    return (m[0] * x + m[4] * y + m[8] * z + m[12],
            m[1] * x + m[5] * y + m[9] * z + m[13],
            m[2] * x + m[6] * y + m[10] * z + m[14])


IDENTITY = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]


# ---------------------------------------------------------------- inspection

def _primitive_counts(gltf: dict, prim: dict) -> tuple[int, int]:
    accessors = gltf.get("accessors", [])
    pos = prim.get("attributes", {}).get("POSITION")
    verts = accessors[pos]["count"] if pos is not None and pos < len(accessors) else 0
    mode = prim.get("mode", 4)
    idx = prim.get("indices")
    n = accessors[idx]["count"] if idx is not None and idx < len(accessors) else verts
    if mode == 4:
        tris = n // 3
    elif mode in (5, 6):
        tris = max(0, n - 2)
    else:
        tris = 0
    return verts, tris


def _mesh_local_bounds(gltf: dict, mesh_index: int) -> list[tuple[float, float, float]] | None:
    accessors = gltf.get("accessors", [])
    corners = []
    for prim in gltf["meshes"][mesh_index].get("primitives", []):
        pos = prim.get("attributes", {}).get("POSITION")
        if pos is None or pos >= len(accessors):
            continue
        acc = accessors[pos]
        if "min" not in acc or "max" not in acc:
            return None
        (x0, y0, z0), (x1, y1, z1) = acc["min"][:3], acc["max"][:3]
        corners += [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    return corners


def world_bounds(gltf: dict) -> dict | None:
    """AABB of the default scene (or all root nodes) in world space; None when POSITION min/max are missing."""
    nodes = gltf.get("nodes", [])
    scenes = gltf.get("scenes", [])
    if scenes:
        roots = scenes[gltf.get("scene", 0)].get("nodes", [])
    else:
        children = {c for n in nodes for c in n.get("children", [])}
        roots = [i for i in range(len(nodes)) if i not in children]
    lo, hi, missing = [math.inf] * 3, [-math.inf] * 3, False
    stack = [(i, IDENTITY) for i in roots]
    seen = 0
    while stack:
        i, parent = stack.pop()
        seen += 1
        if seen > 100000 or i >= len(nodes):
            break
        node = nodes[i]
        m = _mat_mul(parent, node_matrix(node))
        if "mesh" in node and node["mesh"] < len(gltf.get("meshes", [])):
            corners = _mesh_local_bounds(gltf, node["mesh"])
            if corners is None:
                missing = True
            else:
                for c in corners:
                    p = _transform(m, c)
                    for k in range(3):
                        lo[k], hi[k] = min(lo[k], p[k]), max(hi[k], p[k])
        stack += [(c, m) for c in node.get("children", [])]
    if missing or lo[0] == math.inf:
        return None
    size = [hi[k] - lo[k] for k in range(3)]
    return {"min": [round(v, 6) for v in lo], "max": [round(v, 6) for v in hi],
            "size": [round(v, 6) for v in size], "largest_dimension": round(max(size), 6)}


def _animation_duration(gltf: dict, anim: dict) -> float:
    accessors = gltf.get("accessors", [])
    dur = 0.0
    for s in anim.get("samplers", []):
        acc = accessors[s["input"]] if s.get("input") is not None and s["input"] < len(accessors) else {}
        if acc.get("max"):
            dur = max(dur, float(acc["max"][0]))
    return round(dur, 4)


def inspect(path_or_bytes: str | Path | bytes) -> dict:
    gltf, binary, path = load(path_or_bytes)
    meshes = gltf.get("meshes", [])
    prims = [p for m in meshes for p in m.get("primitives", [])]
    verts = tris = 0
    for p in prims:
        v, t = _primitive_counts(gltf, p)
        verts, tris = verts + v, tris + t
    used = list(gltf.get("extensionsUsed", []))
    required = list(gltf.get("extensionsRequired", []))
    images = []
    for i, img in enumerate(gltf.get("images", [])):
        if "bufferView" in img:
            src = "embedded"
        elif str(img.get("uri", "")).startswith("data:"):
            src = "data-uri"
        else:
            src = "external"
        entry = {"index": i, "source": src, "mimeType": img.get("mimeType"), "name": img.get("name")}
        if src == "external":
            entry["uri"] = img.get("uri")
            if path is not None:
                from urllib.parse import unquote
                entry["exists"] = (path.parent / unquote(img.get("uri", ""))).exists()
        images.append(entry)
    buffers = []
    for b in gltf.get("buffers", []):
        uri = b.get("uri")
        kind = "glb-bin" if uri is None else ("data-uri" if str(uri).startswith("data:") else "external")
        buffers.append({"byteLength": b.get("byteLength"), "source": kind, **({"uri": uri} if kind == "external" else {})})
    lights = gltf.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])
    report = {
        "file": str(path) if path else None,
        "asset": {k: gltf["asset"].get(k) for k in ("version", "generator", "copyright", "minVersion") if k in gltf["asset"]},
        "counts": {
            "scenes": len(gltf.get("scenes", [])), "nodes": len(gltf.get("nodes", [])), "meshes": len(meshes),
            "primitives": len(prims), "materials": len(gltf.get("materials", [])),
            "textures": len(gltf.get("textures", [])), "images": len(gltf.get("images", [])),
            "animations": len(gltf.get("animations", [])), "skins": len(gltf.get("skins", [])),
            "cameras": len(gltf.get("cameras", [])), "lights": len(lights),
            "vertices": verts, "triangles": tris,
        },
        "animations": [{"name": a.get("name", f"animation_{i}"), "channels": len(a.get("channels", [])),
                        "duration_s": _animation_duration(gltf, a)} for i, a in enumerate(gltf.get("animations", []))],
        "extensions_used": used,
        "extensions_required": required,
        "images": images,
        "buffers": buffers,
        "bin_chunk_bytes": len(binary) if binary is not None else None,
        "bounds": world_bounds(gltf),
        "issues": [],
    }
    issues = report["issues"]
    for ext, why in RISKY_EXTENSIONS.items():
        if ext in required:
            issues.append(f"requires {ext}: {why}")
        elif ext in used:
            issues.append(f"uses {ext} (optional): {why}")
    for img in images:
        if img.get("exists") is False:
            issues.append(f"external image missing: {img.get('uri')}")
    for b in buffers:
        if b["source"] == "external" and path is not None:
            from urllib.parse import unquote
            if not (path.parent / unquote(b["uri"])).exists():
                issues.append(f"external buffer missing: {b['uri']}")
    if report["bounds"] is None and meshes:
        issues.append("POSITION accessors lack min/max: bounds unknown (glTF requires them; file may be invalid)")
    elif report["bounds"] and report["bounds"]["largest_dimension"] > 1000:
        issues.append("largest dimension > 1000 units: probably authored in centimetres or millimetres; scale on import")
    elif report["bounds"] and 0 < report["bounds"]["largest_dimension"] < 0.01:
        issues.append("largest dimension < 0.01 units: model is tiny; check units")
    static = [a["name"] for a in report["animations"] if a["duration_s"] == 0]
    if static:
        issues.append(f"{len(static)} animation(s) have zero duration (single-key pose tracks); "
                      "they will not move: delete them or re-export with real keyframes")
    if not gltf["asset"].get("copyright"):
        issues.append("asset.copyright is empty: keep the source page and licence in the media pack manifest")
    return report


def text_report(r: dict) -> str:
    c = r["counts"]
    lines = [f"{r.get('file') or '<bytes>'}",
             f"  generator: {r['asset'].get('generator', '-')}  copyright: {r['asset'].get('copyright', '-')}",
             "  " + ", ".join(f"{k}={v}" for k, v in c.items())]
    if r["bounds"]:
        lines.append(f"  bounds: min {r['bounds']['min']} max {r['bounds']['max']} size {r['bounds']['size']}")
    for a in r["animations"][:8]:
        lines.append(f"  animation {a['name']}: {a['channels']} channel(s), {a['duration_s']} s")
    if len(r["animations"]) > 8:
        lines.append(f"  ... {len(r['animations']) - 8} more animation(s) (use --json for all)")
    if r["extensions_required"]:
        lines.append(f"  extensionsRequired: {', '.join(r['extensions_required'])}")
    for i in r["issues"]:
        lines.append(f"  ! {i}")
    return "\n".join(lines)


# ---------------------------------------------------------------- fixture builder

def _pad4(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def make_cube_glb(size: float = 1.0, translation: tuple[float, float, float] | None = None,
                  scale: tuple[float, float, float] | None = None, animated: bool = False,
                  copyright: str = "CC0-1.0 test fixture", extensions_required: list[str] | None = None) -> bytes:
    """A minimal valid GLB: one cube mesh (8 vertices, 12 triangles), optional node TRS and a 1 s animation."""
    h = size / 2.0
    positions = [(-h, -h, -h), (h, -h, -h), (h, h, -h), (-h, h, -h), (-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h)]
    indices = [0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 3, 7, 6, 3, 6, 2, 1, 2, 6, 1, 6, 5, 0, 4, 7, 0, 7, 3]
    pos_bytes = b"".join(struct.pack("<3f", *p) for p in positions)
    idx_bytes = _pad4(struct.pack(f"<{len(indices)}H", *indices))
    blob = pos_bytes + idx_bytes
    buffer_views = [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos_bytes), "target": 34962},
                    {"buffer": 0, "byteOffset": len(pos_bytes), "byteLength": len(indices) * 2, "target": 34963}]
    accessors = [{"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3",
                  "min": [-h, -h, -h], "max": [h, h, h]},
                 {"bufferView": 1, "componentType": 5123, "count": len(indices), "type": "SCALAR"}]
    node: dict = {"mesh": 0, "name": "Cube"}
    if translation:
        node["translation"] = list(translation)
    if scale:
        node["scale"] = list(scale)
    gltf: dict = {
        "asset": {"version": "2.0", "generator": "baltor gltf_glb_inspector.make_cube_glb", "copyright": copyright},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [node],
        "meshes": [{"name": "Cube", "primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0}]}],
        "materials": [{"name": "Grey", "pbrMetallicRoughness": {"baseColorFactor": [0.8, 0.8, 0.8, 1.0]}}],
        "accessors": accessors, "bufferViews": buffer_views,
    }
    if animated:
        times = struct.pack("<2f", 0.0, 1.0)
        values = struct.pack("<6f", 0, 0, 0, 0, 1, 0)
        off = len(blob)
        blob += times + values
        buffer_views += [{"buffer": 0, "byteOffset": off, "byteLength": 8},
                         {"buffer": 0, "byteOffset": off + 8, "byteLength": 24}]
        accessors += [{"bufferView": 2, "componentType": 5126, "count": 2, "type": "SCALAR", "min": [0.0], "max": [1.0]},
                      {"bufferView": 3, "componentType": 5126, "count": 2, "type": "VEC3"}]
        gltf["animations"] = [{"name": "Bounce", "samplers": [{"input": 2, "output": 3, "interpolation": "LINEAR"}],
                               "channels": [{"sampler": 0, "target": {"node": 0, "path": "translation"}}]}]
    if extensions_required:
        gltf["extensionsUsed"] = list(extensions_required)
        gltf["extensionsRequired"] = list(extensions_required)
    gltf["buffers"] = [{"byteLength": len(blob)}]
    json_bytes = _pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    bin_bytes = _pad4(blob)
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    return (struct.pack("<III", GLB_MAGIC, 2, total) + struct.pack("<II", len(json_bytes), CHUNK_JSON) + json_bytes
            + struct.pack("<II", len(bin_bytes), CHUNK_BIN) + bin_bytes)


def gltf_with_data_uri(glb: bytes) -> dict:
    """Convert a GLB from make_cube_glb into .gltf JSON with an embedded data-URI buffer."""
    gltf, binary = read_glb(glb)
    gltf["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binary or b"").decode()
    return gltf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-triangles", type=int, default=0, help="fail when a file has more triangles (0 = no limit)")
    ap.add_argument("--deny-ext", action="append", default=[], help="fail when this extension is required")
    a = ap.parse_args(argv)
    failed, reports = False, []
    for f in a.files:
        try:
            r = inspect(f)
        except (OSError, GLTFError) as exc:
            failed = True
            reports.append({"file": f, "error": str(exc)})
            continue
        if a.max_triangles and r["counts"]["triangles"] > a.max_triangles:
            r["issues"].append(f"triangles {r['counts']['triangles']} > limit {a.max_triangles}")
            failed = True
        denied = sorted(set(a.deny_ext) & set(r["extensions_required"]))
        if denied:
            r["issues"].append(f"requires denied extension(s): {', '.join(denied)}")
            failed = True
        reports.append(r)
    if a.json:
        print(json.dumps(reports if len(reports) > 1 else reports[0], indent=2))
    else:
        for r in reports:
            print(r["file"] + ": ERROR " + r["error"] if "error" in r else text_report(r))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
