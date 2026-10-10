"""Find overlay panels (caption boxes, title cards, frosted glass) and estimate how see-through they are.

Usage:
    python video_re_overlay_transparency_probe.py video.mp4 [--shots shots.json] [--out overlay.json]

Idea: a panel composited with opacity a over a moving background shows the background's changes
scaled by (1 - a). So inside every shot (at least ``min_window_s`` long; the whole clip when no shots
are given), frames are sampled at ``sample_fps`` (default 4) and 160 px wide, and the temporal
standard deviation of every 8x8-pixel cell is measured.

1. The moving-background level is the 90th percentile of cell deviations; if it is under
   ``min_motion`` (3 grey levels) the background does not move enough to test anything and the
   window is skipped.
2. Cells at most 0.8 x that level are 'attenuated'. Isolated cells are removed (a 3x3 majority
   filter); 4-connected groups covering 1-60% of the frame and filling at least 60% of their
   bounding box (panels are rectangles) are candidates.
3. For each candidate, attenuation = median deviation inside (one cell in from the edge) / median
   deviation in a 2-cell ring around it. The ring must itself move (at least 0.6 x the background
   level), otherwise the candidate is static scenery and is dropped.
4. estimated_opacity = 1 - attenuation. At least 0.98 is 'opaque' (nothing shows through);
   0.15-0.98 is 'semi-transparent'. The panel colour is estimated from the inside and ring means:
   tint = (mean_in - (1 - a) x mean_ring) / a.

semi_transparent_ratio = semi-transparent panel area / all detected panel area (summed over
windows): 1.0 means every detected panel lets the background through, 0.0 means all are solid.

Accuracy on synthetic tests (panning texture, flat panel, H.264): opacity within about 0.02 for
0.3-0.95; a 0.98 panel read 0.966 after H.264 and 0.980 lossless, so the opaque/semi class right at
the 0.98 boundary is not reliable. Limits: blur also lowers the variance, so a frosted (blurred) panel reads more opaque than its
alpha; changing text on a panel raises it; a static region of the scene bordered by motion can be
mistaken for an opaque panel (a split screen with one frozen half reads as an opaque panel); panels
smaller than about 1% or larger than 60% of the frame are ignored.
"""

from __future__ import annotations

import argparse

import numpy as np

from video_re_common import (ToolMissing, clean, dump_json, import_sibling, iter_frames, load_json, media_info,
                             shots_from_json, unavailable, whole_clip_shot)

IDENTITY = "video_re_overlay_transparency_probe"
VERSION = "1.0.0"
CELL = 8
DEFAULTS = {"sample_fps": 4.0, "width": 160, "min_window_s": 1.5, "min_motion": 3.0, "attenuated": 0.8,
            "min_area": 0.01, "max_area": 0.6, "min_rect_fill": 0.6, "ring_moving": 0.6, "opaque_at": 0.98, "semi_from": 0.15}


def cells(a: np.ndarray, cell: int = CELL) -> np.ndarray:
    """Mean over cell x cell blocks of a (h, w) or (h, w, c) array."""
    h, w = a.shape[:2]
    hc, wc = h // cell, w // cell
    a = a[:hc * cell, :wc * cell]
    return a.reshape(hc, cell, wc, cell, *a.shape[2:]).mean(axis=(1, 3))


def _components(mask: np.ndarray) -> list[np.ndarray]:
    h, w = mask.shape
    seen = np.zeros_like(mask)
    out = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        stack, comp = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop()
            comp.append((cy, cx))
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        out.append(np.array(comp))
    return out


def _dilate(m: np.ndarray, r: int) -> np.ndarray:
    out = m.copy()
    for _ in range(r):
        o = out.copy()
        o[1:] |= out[:-1]
        o[:-1] |= out[1:]
        o[:, 1:] |= out[:, :-1]
        o[:, :-1] |= out[:, 1:]
        out = o
    return out


def _erode(m: np.ndarray, r: int) -> np.ndarray:
    return ~_dilate(~m, r)


def _majority(m: np.ndarray) -> np.ndarray:
    p = np.pad(m.astype(int), 1)
    s = sum(p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    return s >= 5


def panels_in_window(frames_rgb: np.ndarray, params: dict | None = None) -> dict:
    """Panels in one stack of RGB frames (n, h, w, 3). bbox in analysis pixels."""
    p = {**DEFAULTS, **(params or {})}
    f = frames_rgb.astype(np.float64)
    grey = f @ np.array([0.299, 0.587, 0.114])
    dev = cells(grey.std(axis=0))
    mean_rgb = cells(f.mean(axis=0))
    level = float(np.percentile(dev, 90))
    if level < p["min_motion"]:
        return {"background_level": level, "panels": [], "skipped": "background does not move"}
    att = _majority(dev <= p["attenuated"] * level)
    hc, wc = dev.shape
    panels = []
    for comp in _components(att):
        if len(comp) < max(4, p["min_area"] * hc * wc) or len(comp) > p["max_area"] * hc * wc:
            continue  # too small to judge, or so large it is the scene rather than an overlay
        y0, x0 = comp.min(axis=0)
        y1, x1 = comp.max(axis=0)
        box_cells = (y1 - y0 + 1) * (x1 - x0 + 1)
        if len(comp) / box_cells < p["min_rect_fill"]:
            continue
        mask = np.zeros_like(att)
        mask[comp[:, 0], comp[:, 1]] = True
        inner = _erode(mask, 1)
        if not inner.any():
            inner = mask
        ring = _dilate(mask, 3) & ~_dilate(mask, 1)
        if not ring.any():
            continue
        ring_dev = float(np.median(dev[ring]))
        if ring_dev < p["ring_moving"] * level:
            continue  # surroundings static too: scenery, not an overlay
        a_in = float(np.median(dev[inner]))
        attenuation = min(1.0, a_in / ring_dev)
        opacity = 1.0 - attenuation
        if opacity < p["semi_from"]:
            continue
        kind = "opaque" if opacity >= p["opaque_at"] else "semi-transparent"
        m_in, m_ring = mean_rgb[inner].mean(axis=0), mean_rgb[ring].mean(axis=0)
        tint = None
        if opacity >= 0.2:
            t = np.clip((m_in - (1 - opacity) * m_ring) / opacity, 0, 255)
            tint = "#%02X%02X%02X" % tuple(int(round(v)) for v in t)
        panels.append({"bbox": [int(x0 * CELL), int(y0 * CELL), int((x1 - x0 + 1) * CELL), int((y1 - y0 + 1) * CELL)],
                       "area_cells": int(mask.sum()), "estimated_opacity": opacity, "attenuation": attenuation,
                       "class": kind, "tint_estimate": tint})
    return {"background_level": level, "panels": panels, "grid": [int(hc), int(wc)]}


def analyse(video: str, shots: list[dict], info: dict | None = None, **params) -> dict:
    p = {**DEFAULTS, **params}
    info = info or media_info(video)
    W, H = info["width"], info["height"]
    times, frames = [], []
    for t, fr in iter_frames(video, width=int(p["width"]), pix_fmt="rgb24", fps=p["sample_fps"], info=info):
        times.append(t)
        frames.append(fr)
    if not frames:
        raise RuntimeError("no frames decoded")
    times_a = np.asarray(times)
    stack = np.stack(frames)
    sx, sy = W / stack.shape[2], H / stack.shape[1]
    panels, windows = [], []
    semi_area = opaque_area = 0.0
    for s in shots:
        a, b = float(s["start_s"]), float(s["end_s"])
        if b - a < p["min_window_s"]:
            continue
        sel = (times_a >= a + 0.1) & (times_a < b - 0.1)
        if sel.sum() < 5:
            continue
        res = panels_in_window(stack[sel], p)
        windows.append({"index": s.get("index"), "start_s": a, "end_s": b, "background_level": res["background_level"],
                        "skipped": res.get("skipped")})
        for pan in res["panels"]:
            x, y, w, h = pan["bbox"]
            pan = dict(pan, bbox=[x * sx, y * sy, w * sx, h * sy], start_s=a, end_s=b, shot=s.get("index"))
            area = pan["area_cells"] * (b - a)
            if pan["class"] == "opaque":
                opaque_area += area
            else:
                semi_area += area
            panels.append(pan)
    total = semi_area + opaque_area
    tested = [w for w in windows if not w.get("skipped")]
    return {"semi_transparent_ratio": (semi_area / total) if total > 0 else None,
            "panels": panels, "windows": windows,
            "summary": {"windows_tested": len(tested), "windows_skipped": len(windows) - len(tested),
                        "panels": len(panels),
                        "reason": None if total > 0 else ("no moving background to test against" if not tested
                                                          else "no overlay panel detected")},
            "params": p}


def run(video: str, shots: list[dict] | None = None, **params) -> dict:
    try:
        info = media_info(video)
        shots = shots or whole_clip_shot(info.get("duration_s") or 0.0)
        res = analyse(video, shots, info=info, **params)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except RuntimeError as exc:
        return {"status": "error", "reason": str(exc)}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **res})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--shots", help="detect_shots JSON; default: run video_re_detect_shots")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.shots:
        shots = shots_from_json(load_json(a.shots))
    else:
        det = import_sibling("video_re_detect_shots").run(a.video)
        shots = det.get("shots") if det.get("status") == "ok" else None
    res = run(a.video, shots)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
