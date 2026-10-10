#!/usr/bin/env python3
"""Check a short-video spec (see the short_video_spec contract schema) against the house rules in ../rules.json."""

import json
import sys
from pathlib import Path

RULES = json.loads((Path(__file__).resolve().parents[1] / "rules.json").read_text())


def problems(spec: dict) -> list[str]:
    out = []
    if spec.get("duration_s", 0) < RULES["min_duration_s"]:
        out.append(f"duration {spec.get('duration_s')}s is under {RULES['min_duration_s']}s")
    title = spec.get("title_hook", {})
    if title.get("color", "").upper() != RULES["title"]["color"]:
        out.append(f"title colour {title.get('color')} is not {RULES['title']['color']}")
    if title.get("position") != "upper-third-over-photo":
        out.append("title must sit in the upper third over the photo")
    for i, scene in enumerate(spec.get("scenes", [])):
        for layer in scene.get("layers", []):
            if layer.get("opacity", 1) > RULES["max_layer_opacity"]:
                out.append(f"scene {i + 1}: layer {layer.get('source')} opacity {layer['opacity']} > {RULES['max_layer_opacity']}")
        if len(scene.get("layers", [])) < RULES["background"]["layers_min"]:
            out.append(f"scene {i + 1}: fewer than {RULES['background']['layers_min']} layers")
        if not any(l.get("kind", "").startswith(("background-video", "grid-2x2")) for l in scene.get("layers", [])):
            out.append(f"scene {i + 1}: no moving background layer")
    for c in spec.get("captions", []):
        if not c.get("text", "").strip():
            out.append(f"caption at {c.get('start_s')}s is empty; captions must be faithful to the narration")
    return out


if __name__ == "__main__":
    found = problems(json.loads(Path(sys.argv[1]).read_text()))
    for p in found:
        print("FAIL", p)
    print("all house rules pass" if not found else f"{len(found)} problem(s)")
    sys.exit(1 if found else 0)
