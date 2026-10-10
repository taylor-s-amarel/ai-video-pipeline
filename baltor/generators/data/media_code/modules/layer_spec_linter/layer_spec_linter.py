"""Lint a scene/layer spec against the house compositing rules.

Works on plain dicts (for example the ``short_video_spec`` contract schema's
scenes) so it can run before anything is rendered:

* every layer opacity <= 0.98 (no fully opaque layer);
* at least ``min_layers`` layers per scene (default 5);
* at least one moving background layer per scene (background-video,
  grid-2x2, particles, light ... or a layer with a ``motion`` value);
* photos and overlays have feathered edges (``feather_px`` > 0);
* no forbidden layer kinds (progress bars, stacked label panels);
* scenes are contiguous and the total duration is at least ``min_duration``.

Usage::

    from layer_spec_linter import lint
    findings = lint(spec)       # [] when the spec follows the rules
"""

from __future__ import annotations

MOVING_KINDS = {"background-video", "grid-2x2", "particles", "light"}
NEEDS_FEATHER = {"photo", "overlay", "texture"}
FORBIDDEN = {"progress-bar", "label-stack"}


def lint(spec: dict, max_opacity: float = 0.98, min_layers: int = 5, min_duration: float = 60.0) -> list[dict]:
    out = []

    def add(rule, where, msg):
        out.append({"rule": rule, "where": where, "message": msg})

    scenes = spec.get("scenes", [])
    if not scenes:
        add("scenes", "spec", "no scenes")
        return out
    prev_end = 0.0
    for i, s in enumerate(scenes):
        where = f"scene {i + 1}"
        if abs(s["start_s"] - prev_end) > 1e-6:
            add("contiguous", where, f"starts at {s['start_s']} but the previous scene ended at {prev_end}")
        prev_end = s["end_s"]
        layers = s.get("layers", [])
        if len(layers) < min_layers:
            add("min_layers", where, f"{len(layers)} layers (min {min_layers})")
        if not any(l.get("kind") in MOVING_KINDS or l.get("motion") for l in layers):
            add("moving_background", where, "no moving layer")
        for j, l in enumerate(layers):
            lw = f"{where} layer {j + 1} ({l.get('source', l.get('kind'))})"
            if l.get("opacity", 1.0) > max_opacity:
                add("opacity_cap", lw, f"opacity {l.get('opacity', 1.0)} > {max_opacity}")
            if l.get("kind") in NEEDS_FEATHER and not l.get("feather_px"):
                add("feathered_edges", lw, "hard edge: set feather_px > 0")
            if l.get("kind") in FORBIDDEN:
                add("forbidden_layer", lw, f"{l['kind']} is not allowed")
    total = scenes[-1]["end_s"]
    if total < min_duration:
        add("min_duration", "spec", f"{total}s (min {min_duration}s)")
    return out
