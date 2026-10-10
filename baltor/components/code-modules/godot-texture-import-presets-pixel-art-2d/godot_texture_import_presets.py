"""Write Godot 4 texture import presets (``.import`` sidecars), material ``.tres`` and project settings.

Pixel art and smooth art need opposite settings. Getting them wrong gives
blurry sprites, shimmering mipmaps or VRAM-compression blocks on UI. This
module writes the settings before Godot first imports the files:

* ``.import`` sidecars: ``[remap] importer="texture"`` plus a ``[params]``
  section. When Godot (re)imports a file whose ``.import`` already exists it
  reads ``importer`` from ``[remap]`` and every key of ``[params]`` and keeps
  them; it fills in ``uid``, ``path`` and ``[deps] dest_files`` itself.
* ``project.godot`` settings: the default canvas texture filter
  (``rendering/textures/canvas_textures/default_texture_filter``; 0 = Nearest,
  1 = Linear), integer stretch scaling and 2D pixel snapping for pixel art.
  In Godot 4 the 2D filter is a CanvasItem/project setting, not an import option.
* ``StandardMaterial3D`` ``.tres`` with ``texture_filter`` (0 = Nearest,
  3 = Linear with mipmaps, the default) for 3D pixel-art surfaces.

Values come from Godot's own sources: ResourceImporterTexture options
(compress/mode: Lossless=0, Lossy=1, VRAM Compressed=2, VRAM Uncompressed=3,
Basis Universal=4; compress/normal_map: Detect=0, Enable=1, Disabled=2;
detect_3d/compress_to: Disabled=0, VRAM Compressed=1, Basis Universal=2),
BaseMaterial3D.TextureFilter and Viewport.DefaultCanvasItemTextureFilter.

Usage::

    python godot_texture_import_presets.py apply PROJECT_DIR --preset pixel-art-2d --glob "art/**/*.png" [--overwrite]
    python godot_texture_import_presets.py check PROJECT_DIR --preset pixel-art-2d --glob "art/**/*.png"
    python godot_texture_import_presets.py project-settings --preset pixel-art-2d
    python godot_texture_import_presets.py material res://art/tiles.png --preset pixel-art-3d > tiles_material.tres
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".bmp", ".tga", ".exr", ".hdr"}

BASE_PARAMS: dict[str, object] = {
    "compress/mode": 0,
    "compress/high_quality": False,
    "compress/lossy_quality": 0.7,
    "compress/hdr_compression": 1,
    "compress/normal_map": 0,
    "compress/channel_pack": 0,
    "mipmaps/generate": False,
    "mipmaps/limit": -1,
    "roughness/mode": 0,
    "roughness/src_normal": "",
    "process/fix_alpha_border": True,
    "process/premult_alpha": False,
    "process/hdr_as_srgb": False,
    "process/hdr_clamp_exposure": False,
    "process/size_limit": 0,
    "detect_3d/compress_to": 1,
}

PRESETS: dict[str, dict] = {
    "pixel-art-2d": {
        "description": "Crisp pixel art in 2D: lossless, no mipmaps, Nearest filter project-wide, integer scaling, pixel snap.",
        "params": {"compress/mode": 0, "mipmaps/generate": False, "detect_3d/compress_to": 0},
        "project": {"rendering": {"textures/canvas_textures/default_texture_filter": 0,
                                  "2d/snap/snap_2d_transforms_to_pixel": True},
                    "display": {"window/stretch/mode": "canvas_items", "window/stretch/scale_mode": "integer"}},
        "material_filter": 0,
    },
    "pixel-art-3d": {
        "description": "Pixel-art textures on 3D meshes (Kenney/KayKit-style palettes): lossless, no mipmaps, Nearest material filter.",
        "params": {"compress/mode": 0, "mipmaps/generate": False, "detect_3d/compress_to": 0},
        "project": {},
        "material_filter": 0,
    },
    "smooth-2d": {
        "description": "Painted or vector-style 2D art and video overlays: lossless, Linear filter, no mipmaps.",
        "params": {"compress/mode": 0, "mipmaps/generate": False, "detect_3d/compress_to": 1},
        "project": {"rendering": {"textures/canvas_textures/default_texture_filter": 1}},
        "material_filter": 3,
    },
    "texture-3d": {
        "description": "Albedo/roughness/AO maps for 3D (Poly Haven, ambientCG): VRAM compressed with mipmaps.",
        "params": {"compress/mode": 2, "mipmaps/generate": True, "detect_3d/compress_to": 1},
        "project": {},
        "material_filter": 3,
    },
    "normal-map-3d": {
        "description": "Normal maps: VRAM compressed (RGTC via compress/normal_map=Enable), mipmaps on.",
        "params": {"compress/mode": 2, "mipmaps/generate": True, "compress/normal_map": 1, "detect_3d/compress_to": 1},
        "project": {},
        "material_filter": 3,
    },
    "ui-lossless": {
        "description": "UI, captions and icons: lossless, no mipmaps, never VRAM-compressed even if used in 3D.",
        "params": {"compress/mode": 0, "mipmaps/generate": False, "detect_3d/compress_to": 0},
        "project": {},
        "material_filter": 1,
    },
}


def _fmt(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return json.dumps(v)
    return str(v)


def preset_params(preset: str, overrides: dict | None = None) -> dict:
    if preset not in PRESETS:
        raise KeyError(f"unknown preset {preset!r}; choose from {sorted(PRESETS)}")
    params = dict(BASE_PARAMS)
    params.update(PRESETS[preset]["params"])
    params.update(overrides or {})
    return params


def import_file_text(source_res_path: str, preset: str, overrides: dict | None = None) -> str:
    """Contents of ``<file>.import`` for a texture at ``source_res_path`` (``res://...``)."""
    if not source_res_path.startswith("res://"):
        raise ValueError("source_res_path must start with res://")
    lines = ["[remap]", "", 'importer="texture"', 'type="CompressedTexture2D"', "", "[deps]", "",
             f"source_file={json.dumps(source_res_path)}", "", "[params]", ""]
    lines += [f"{k}={_fmt(v)}" for k, v in preset_params(preset, overrides).items()]
    return "\n".join(lines) + "\n"


def _parse_value(raw: str) -> object:
    raw = raw.strip()
    if raw in {"true", "false"}:
        return raw == "true"
    if raw.startswith('"') and raw.endswith('"'):
        return json.loads(raw)
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def parse_import(text: str) -> dict[str, dict[str, object]]:
    """Parse a Godot ``.import`` / ``project.godot``-style file (sections, key=value, multi-line {...} values)."""
    out: dict[str, dict[str, object]] = {}
    section = ""
    pending_key, pending_val, depth = None, [], 0
    for line in text.splitlines():
        if pending_key is not None:
            pending_val.append(line)
            depth += line.count("{") + line.count("[") - line.count("}") - line.count("]")
            if depth <= 0:
                out.setdefault(section, {})[pending_key] = "\n".join(pending_val)
                pending_key, pending_val = None, []
            continue
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if s.startswith("[") and s.endswith("]") and "=" not in s:
            section = s[1:-1]
            out.setdefault(section, {})
            continue
        if "=" in s:
            k, v = s.split("=", 1)
            depth = v.count("{") + v.count("[") - v.count("}") - v.count("]")
            if depth > 0:
                pending_key, pending_val = k.strip(), [v]
            else:
                out.setdefault(section, {})[k.strip()] = _parse_value(v)
    return out


def check_import(text: str, preset: str, overrides: dict | None = None) -> list[str]:
    """Differences between an existing ``.import`` and the preset (only the keys the preset pins)."""
    parsed = parse_import(text)
    problems = []
    if parsed.get("remap", {}).get("importer") not in (None, "texture"):
        problems.append(f"importer is {parsed['remap']['importer']!r}, not 'texture'")
    params = parsed.get("params", {})
    pinned = dict(PRESETS[preset]["params"])
    pinned.update(overrides or {})
    for k, v in pinned.items():
        if params.get(k) != v:
            problems.append(f"{k} = {params.get(k)!r}, preset wants {v!r}")
    return problems


def project_settings_text(preset: str) -> str:
    """Lines to merge into project.godot (sections and keys)."""
    proj = PRESETS[preset]["project"]
    if not proj:
        return "; preset needs no project-wide settings\n"
    chunks = []
    for section, kv in proj.items():
        chunks.append(f"[{section}]\n\n" + "\n".join(f"{k}={_fmt(v)}" for k, v in kv.items()))
    return "\n\n".join(chunks) + "\n"


def material_tres(texture_res_path: str, preset: str = "pixel-art-3d", unshaded: bool = False,
                  alpha_scissor: bool = False) -> str:
    """StandardMaterial3D resource using the preset's texture filter."""
    filt = PRESETS[preset]["material_filter"]
    lines = ['[gd_resource type="StandardMaterial3D" format=3]', "",
             f'[ext_resource type="Texture2D" path={json.dumps(texture_res_path)} id="1_albedo"]', "",
             "[resource]"]
    if alpha_scissor:
        lines.append("transparency = 2")  # BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
    if unshaded:
        lines.append("shading_mode = 0")  # SHADING_MODE_UNSHADED
    lines += ['albedo_texture = ExtResource("1_albedo")', f"texture_filter = {filt}"]
    return "\n".join(lines) + "\n"


def res_path(project_dir: Path, file: Path) -> str:
    return "res://" + file.resolve().relative_to(project_dir.resolve()).as_posix()


def apply_to_tree(project_dir: str | Path, preset: str, pattern: str = "**/*.png", overwrite: bool = False,
                  overrides: dict | None = None) -> list[Path]:
    """Write ``.import`` sidecars for matching images under ``project_dir``; returns the files written."""
    project_dir = Path(project_dir)
    if not (project_dir / "project.godot").exists():
        raise FileNotFoundError(f"{project_dir} has no project.godot")
    written = []
    for f in sorted(project_dir.glob(pattern)):
        if f.suffix.lower() not in IMAGE_SUFFIXES or ".godot" in f.relative_to(project_dir).parts:
            continue
        sidecar = f.with_name(f.name + ".import")
        if sidecar.exists() and not overwrite:
            continue
        sidecar.write_text(import_file_text(res_path(project_dir, f), preset, overrides), encoding="utf-8")
        written.append(sidecar)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("apply", "check"):
        p = sub.add_parser(name)
        p.add_argument("project_dir")
        p.add_argument("--preset", required=True, choices=sorted(PRESETS))
        p.add_argument("--glob", default="**/*.png")
        if name == "apply":
            p.add_argument("--overwrite", action="store_true")
    ps = sub.add_parser("project-settings")
    ps.add_argument("--preset", required=True, choices=sorted(PRESETS))
    mt = sub.add_parser("material")
    mt.add_argument("texture_res_path")
    mt.add_argument("--preset", default="pixel-art-3d", choices=sorted(PRESETS))
    mt.add_argument("--unshaded", action="store_true")
    mt.add_argument("--alpha-scissor", action="store_true")
    sub.add_parser("list")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for k, v in PRESETS.items():
            print(f"{k:<14} {v['description']}")
        return 0
    if a.cmd == "project-settings":
        sys.stdout.write(project_settings_text(a.preset))
        return 0
    if a.cmd == "material":
        sys.stdout.write(material_tres(a.texture_res_path, a.preset, a.unshaded, a.alpha_scissor))
        return 0
    if a.cmd == "apply":
        written = apply_to_tree(a.project_dir, a.preset, a.glob, a.overwrite)
        print(f"wrote {len(written)} .import file(s); merge these into project.godot:\n")
        sys.stdout.write(project_settings_text(a.preset))
        return 0
    bad = 0
    root = Path(a.project_dir)
    for f in sorted(root.glob(a.glob)):
        if f.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        sidecar = f.with_name(f.name + ".import")
        if not sidecar.exists():
            print(f"MISSING {sidecar}")
            bad += 1
            continue
        for problem in check_import(sidecar.read_text(encoding="utf-8"), a.preset):
            print(f"FAIL    {sidecar}: {problem}")
            bad += 1
    print("all imports match" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
