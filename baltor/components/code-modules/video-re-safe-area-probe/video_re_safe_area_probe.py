"""Check whether on-screen text sits where platform UI or frame edges would cover it.

Usage:
    python video_re_safe_area_probe.py text_regions.json [--profile auto] [--zones zones.json] [--out safe.json]

Input: text regions from video_re_text_regions (t_s, bbox in source pixels) and the frame size.
A violation is a text region with at least ``min_overlap`` (25%) of its area inside a zone.

Profiles (zones are fractions of width/height, origin top-left). The numbers are working
assumptions, not published platform specifications: app layouts differ and change, so measure the
app you target (screenshot its player) and pass your own zones with ``--zones``.

* ``vertical_ui_conservative`` - for 9:16: top-ui (top 10%), bottom-ui (bottom 20%), right-rail
  (right 14% between 40% and 80% of the height), where vertical-video apps commonly overlay
  their header, caption/handle text and action buttons
* ``margins_10`` - a 10% margin on every side, the old title-safe rule of thumb
* ``none`` - no zones
* ``auto`` - vertical_ui_conservative for portrait frames, margins_10 otherwise
"""

from __future__ import annotations

import argparse

import numpy as np

from video_re_common import clean, dump_json, load_json

IDENTITY = "video_re_safe_area_probe"
VERSION = "1.0.0"

PROFILES = {
    "vertical_ui_conservative": {
        "basis": "assumption: conservative zones where vertical-video apps overlay UI; not a platform specification",
        "zones": [{"name": "top-ui", "x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 0.10},
                  {"name": "bottom-ui", "x0": 0.0, "y0": 0.80, "x1": 1.0, "y1": 1.0},
                  {"name": "right-rail", "x0": 0.86, "y0": 0.40, "x1": 1.0, "y1": 0.80}],
    },
    "margins_10": {
        "basis": "rule of thumb: keep text 10% in from every edge",
        "zones": [{"name": "margin-top", "x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 0.10},
                  {"name": "margin-bottom", "x0": 0.0, "y0": 0.90, "x1": 1.0, "y1": 1.0},
                  {"name": "margin-left", "x0": 0.0, "y0": 0.0, "x1": 0.10, "y1": 1.0},
                  {"name": "margin-right", "x0": 0.90, "y0": 0.0, "x1": 1.0, "y1": 1.0}],
    },
    "none": {"basis": "no zones", "zones": []},
}


def resolve_profile(name: str, width: int, height: int) -> tuple[str, dict]:
    if name == "auto":
        name = "vertical_ui_conservative" if height > width else "margins_10"
    if name not in PROFILES:
        raise ValueError(f"unknown profile {name}; choose from {sorted(PROFILES)} or pass zones")
    return name, PROFILES[name]


def overlap_ratio(bbox: list[float], zone: dict, width: int, height: int) -> float:
    x, y, w, h = bbox
    if w <= 0 or h <= 0:
        return 0.0
    zx0, zy0, zx1, zy1 = zone["x0"] * width, zone["y0"] * height, zone["x1"] * width, zone["y1"] * height
    ix = max(0.0, min(x + w, zx1) - max(x, zx0))
    iy = max(0.0, min(y + h, zy1) - max(y, zy0))
    return ix * iy / (w * h)


def check(regions: list[dict], width: int, height: int, zones: list[dict], min_overlap: float = 0.25) -> dict:
    violations = []
    for r in regions:
        for z in zones:
            ov = overlap_ratio(r["bbox"], z, width, height)
            if ov >= min_overlap:
                violations.append({"t_s": r["t_s"], "zone": z["name"], "bbox": r["bbox"], "overlap_ratio": min(1.0, ov)})
    by_zone: dict[str, int] = {}
    for v in violations:
        by_zone[v["zone"]] = by_zone.get(v["zone"], 0) + 1
    times = sorted({r["t_s"] for r in regions})
    bad_times = sorted({v["t_s"] for v in violations})
    return {"violations": violations,
            "summary": {"regions_checked": len(regions), "violations": len(violations), "by_zone": by_zone,
                        "share_of_text_samples": (len(bad_times) / len(times)) if times else None,
                        "first_violation_s": bad_times[0] if bad_times else None}}


def run(regions: list[dict], width: int, height: int, profile: str = "auto", zones: list[dict] | None = None,
        min_overlap: float = 0.25) -> dict:
    if zones is not None:
        name, prof = "custom", {"basis": "zones supplied by the caller", "zones": zones}
    else:
        name, prof = resolve_profile(profile, width, height)
    res = check(regions, width, height, prof["zones"], min_overlap)
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, "profile": name, "basis": prof["basis"],
                  "zones": prof["zones"], "frame_size": [width, height], "min_overlap": min_overlap, **res})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("regions", help="video_re_text_regions JSON (or evidence.json)")
    ap.add_argument("--profile", default="auto", choices=["auto"] + sorted(PROFILES))
    ap.add_argument("--zones", help="JSON list of {name, x0, y0, x1, y1} fractions")
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--min-overlap", type=float, default=0.25)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    data = load_json(a.regions)
    regions = data.get("regions") or data.get("text_regions") or []
    size = data.get("frame_size") or [(data.get("source") or {}).get("width"), (data.get("source") or {}).get("height")]
    width, height = a.width or size[0], a.height or size[1]
    if not width or not height:
        ap.error("frame size unknown: pass --width and --height")
    zones = load_json(a.zones) if a.zones else None
    res = run(regions, int(width), int(height), a.profile, zones, a.min_overlap)
    dump_json(res, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
