#!/usr/bin/env python3
"""Check a video style preset: JSON Schema validation plus the numeric rules a schema cannot express.

Usage: python3 scripts/check_preset.py [preset.json] [schema.json]
Defaults to preset.json and schema.json next to this scripts/ folder. Exit 0 when every check
passes, 1 otherwise. jsonschema is optional; without it only the numeric checks run.

Numeric checks:
* every opacity anywhere in the preset (including keyframed opacities) is <= 0.98;
* every recorded contrast ratio is recomputed from its colours (WCAG 2.x formula; for
  semi-transparent panels, the worst case over any video underneath) and must match the recorded
  value and reach its threshold: 4.5:1, or 3:1 only for text that is both >= 24 px and >= 700 weight;
* layer stacks: at least 5 layers, unique z, a moving background layer, photo at least 80% wide;
* house titles: #FFD21F, centred no lower than 40% of the height, visible on the first frame,
  frosted backing at 55-75%.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MAX_OPACITY = 0.98
HOUSE_YELLOW = "#FFD21F"
BACKGROUND_ROLES = {"base", "background-video", "background-image", "grid-2x2", "texture", "light", "particles",
                    "haze", "grain", "vignette", "overlay"}


def _rgb(h: str) -> tuple[float, float, float]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb) -> float:
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ratio_l(a: float, b: float) -> float:
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def contrast(fg: str, bg: str) -> float:
    return ratio_l(luminance(_rgb(fg)), luminance(_rgb(bg)))


def panel_worst(fg: str, tint: str, opacity: float) -> float:
    t = _rgb(tint)
    dark = tuple(opacity * c for c in t)
    light = tuple(opacity * c + (1 - opacity) * 255 for c in t)
    lf, ld, ll = luminance(_rgb(fg)), luminance(dark), luminance(light)
    if ld <= lf <= ll:
        return 1.0
    return min(ratio_l(lf, ld), ratio_l(lf, ll))


def required_ratio(size_px: float, weight: int) -> float:
    return 3.0 if size_px >= 24 and weight >= 700 else 4.5


def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}/{i}")
    else:
        yield path, obj


def opacity_problems(preset: dict) -> list[str]:
    out = []
    for path, value in walk(preset):
        leaf = path.rsplit("/", 1)[-1]
        parent = path.rsplit("/", 2)[-2] if path.count("/") >= 2 else ""
        is_opacity = "opacity" in leaf and leaf != "opacity_keyframes"
        in_keyframes = "opacity_keyframes" in path and leaf == "1"
        if (is_opacity or in_keyframes) and isinstance(value, (int, float)) and not isinstance(value, bool):
            if value > MAX_OPACITY:
                out.append(f"{path} = {value} exceeds {MAX_OPACITY}")
        del parent
    return out


def contrast_entries(preset: dict):
    """Yield (path, entry) for every recorded contrast measurement."""
    for key in ("contrast",):
        block = preset.get(key)
        if isinstance(block, dict):
            for name, entry in block.items():
                if isinstance(entry, dict) and "ratio" in entry:
                    yield f"/{key}/{name}", entry
    for i, pair in enumerate(preset.get("pairs", []) or []):
        yield f"/pairs/{i}", pair


def contrast_problems(preset: dict) -> list[str]:
    out = []
    for path, e in contrast_entries(preset):
        fg, bg = e.get("fg"), e.get("bg")
        if not (isinstance(fg, str) and isinstance(bg, str)):
            out.append(f"{path}: needs fg and bg colours")
            continue
        if e.get("basis") == "panel-worst-case":
            got = panel_worst(fg, bg, float(e["opacity"]))
        else:
            got = contrast(fg, bg)
        if abs(got - float(e["ratio"])) > 0.02:
            out.append(f"{path}: recorded ratio {e['ratio']} but colours give {got:.2f}")
        need = float(e.get("required", 4.5))
        size, weight = e.get("size_px"), e.get("weight")
        if size is not None and weight is not None and need < required_ratio(size, weight):
            out.append(f"{path}: {size}px weight {weight} needs {required_ratio(size, weight)}:1, entry claims {need}:1")
        if e.get("use") == "large-bold-only" and need < 4.5 and not (e.get("min_size_px", 0) >= 24 and e.get("min_weight", 0) >= 700):
            out.append(f"{path}: a 3:1 pair must be limited to >= 24 px bold text")
        if got + 1e-9 < need:
            out.append(f"{path}: contrast {got:.2f} is below {need}:1")
    return out


def stack_problems(preset: dict) -> list[str]:
    layers = preset.get("layers", [])
    out = []
    if len(layers) < 5:
        out.append(f"{len(layers)} layers; at least 5 required")
    zs = [layer.get("z") for layer in layers]
    if len(zs) != len(set(zs)):
        out.append("duplicate z values")
    if not any(layer.get("role") in BACKGROUND_ROLES and (layer.get("motion") or {}).get("type", "static") != "static"
               for layer in layers):
        out.append("no moving background layer")
    for layer in layers:
        if layer.get("role") == "photo" and isinstance(layer.get("rect"), dict) and layer["rect"].get("w", 1) < 0.8:
            out.append(f"photo layer {layer.get('id')} is only {layer['rect']['w']} of the frame width")
    return out


def house_title_problems(preset: dict) -> list[str]:
    if not preset.get("house"):
        return []
    out = []
    if str(preset.get("fill", "")).upper() != HOUSE_YELLOW:
        out.append(f"house title fill must be {HOUSE_YELLOW}")
    if preset.get("position", {}).get("center_y_fraction", 1) > 0.40:
        out.append("house title must be centred no lower than 40% of the frame height")
    if not preset.get("timing", {}).get("first_frame"):
        out.append("house title must be visible on the first frame")
    backing = preset.get("backing", {})
    if backing.get("type") != "frosted-glass" or not 0.55 <= backing.get("opacity", 0) <= 0.75:
        out.append("house title needs a frosted-glass backing at 55-75% opacity")
    return out


def schema_problems(preset: dict, schema: dict) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        print("note: jsonschema not installed; skipped schema validation (pip install jsonschema)")
        return []
    cls = jsonschema.validators.validator_for(schema, default=jsonschema.Draft202012Validator)
    return [f"schema {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(cls(schema).iter_errors(preset), key=lambda e: list(e.absolute_path))]


def check(preset: dict, schema: dict | None = None) -> list[str]:
    problems = []
    if schema is not None:
        problems += schema_problems(preset, schema)
    problems += opacity_problems(preset)
    problems += contrast_problems(preset)
    if preset.get("type") == "layer-stack":
        problems += stack_problems(preset)
    if preset.get("type") == "title-style":
        problems += house_title_problems(preset)
    return problems


def main(argv: list[str]) -> int:
    base = Path(__file__).resolve().parents[1]
    preset_path = Path(argv[1]) if len(argv) > 1 else base / "preset.json"
    schema_path = Path(argv[2]) if len(argv) > 2 else base / "schema.json"
    preset = json.loads(preset_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else None
    problems = check(preset, schema)
    for p in problems:
        print("FAIL", p)
    print(f"{preset.get('id', preset_path.name)}: " + ("all checks pass" if not problems else f"{len(problems)} problem(s)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
