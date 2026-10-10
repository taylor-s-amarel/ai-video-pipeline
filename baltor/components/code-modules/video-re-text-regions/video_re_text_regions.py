"""Find text-like regions (titles, captions, labels) in sampled frames, without OCR.

Usage:
    python video_re_text_regions.py video.mp4 [--fps 2] [--out text_regions.json]

Heuristic (documented so analysts can judge it):

1. Frames are sampled at ``sample_fps`` (default 2) and scaled to 360 px wide, grey.
2. Horizontal and vertical grey-level gradients are computed; a pixel is a stroke edge when its
   gradient exceeds max(18, 0.35 x the frame's 99th-percentile gradient).
3. The frame is divided into 4x4-pixel cells. A cell is 'text-like' when at least 12% of its pixels
   are vertical-stroke edges (text has many short vertical strokes).
4. Text cells are grouped with a horizontal morphological closing (3 cells), 4-connected
   components are labelled on the cell grid, and components on the same line with a gap of at most
   0.8 x line height are merged (word spacing of large type).
5. A component is kept when it is 7 px to 30% of the frame tall, at least 1.5x as wide as tall,
   at least 60% of its cell columns contain stroke cells, and its middle rows cross at least 2.0
   stroke edges per text-height of width (ordinary type crosses about 4 at any size) with a median
   spacing between edges of at most 0.28 x text height (letters: about 0.1-0.2; blobs and bokeh
   circles: 0.33 and more in calibration).

Output regions carry t_s, bbox [x, y, w, h] in source pixels, area_ratio, y_center_ratio and a 0-1
score. Regions in consecutive samples that overlap (IoU >= 0.5) are linked into tracks, which show
how long a title or caption band stays on screen.

Known limits: high-contrast textures, grids, foliage and fine patterns can be proposed as text;
very large display type with few strokes, low-contrast text, vertical or curved text and text on
busy backgrounds can be missed. This is a region proposer: OCR (video_re_ocr_adapter) or a look at
the keyframe confirms it.
"""

from __future__ import annotations

import argparse
from collections import deque

import numpy as np

from video_re_common import ToolMissing, clean, dump_json, iter_frames, media_info, unavailable

IDENTITY = "video_re_text_regions"
VERSION = "1.0.0"
CELL = 4
DEFAULTS = {"sample_fps": 2.0, "width": 360, "cell_density": 0.12, "close_cells": 3, "min_height_px": 7,
            "max_height_ratio": 0.30, "min_aspect": 1.5, "min_fill": 0.60, "min_edge_rate": 2.0,
            "max_stroke_gap": 0.28}


def gradients(grey: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    g = grey.astype(np.float32)
    gx = np.zeros_like(g)
    gy = np.zeros_like(g)
    gx[:, 1:] = np.abs(g[:, 1:] - g[:, :-1])
    gy[1:, :] = np.abs(g[1:, :] - g[:-1, :])
    return gx, gy


def edge_threshold(gx: np.ndarray) -> float:
    return float(max(18.0, np.percentile(gx, 99) * 0.35))


def cell_grid(mask: np.ndarray, cell: int = CELL) -> np.ndarray:
    h, w = mask.shape
    hc, wc = h // cell, w // cell
    m = mask[:hc * cell, :wc * cell].reshape(hc, cell, wc, cell)
    return m.mean(axis=(1, 3))


def dilate_h(b: np.ndarray, r: int) -> np.ndarray:
    out = b.copy()
    for k in range(1, r + 1):
        out[:, k:] |= b[:, :-k]
        out[:, :-k] |= b[:, k:]
    return out


def erode_h(b: np.ndarray, r: int) -> np.ndarray:
    out = b.copy()
    for k in range(1, r + 1):
        sh = np.zeros_like(b)
        sh[:, k:] = b[:, :-k]
        out &= sh
        sh = np.zeros_like(b)
        sh[:, :-k] = b[:, k:]
        out &= sh
    return out


def dilate_v(b: np.ndarray, r: int) -> np.ndarray:
    out = b.copy()
    for k in range(1, r + 1):
        out[k:, :] |= b[:-k, :]
        out[:-k, :] |= b[k:, :]
    return out


def components(b: np.ndarray) -> list[tuple[int, int, int, int, list[tuple[int, int]]]]:
    """4-connected components: (y0, x0, y1, x1 inclusive, cells)."""
    seen = np.zeros_like(b, dtype=bool)
    h, w = b.shape
    out = []
    for y, x in zip(*np.nonzero(b)):
        if seen[y, x]:
            continue
        q = deque([(y, x)])
        seen[y, x] = True
        cells = []
        while q:
            cy, cx = q.popleft()
            cells.append((cy, cx))
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < h and 0 <= nx < w and b[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        out.append((min(ys), min(xs), max(ys), max(xs), cells))
    return out


def median_stroke_gap(rows: np.ndarray) -> float:
    """Median distance in pixels between the starts of consecutive edge runs along the given rows.
    Letters put stroke edges close together (about 0.1-0.2 x text height); blobs do not."""
    gaps = []
    for r in rows:
        idx = np.flatnonzero(r)
        if len(idx) < 2:
            continue
        starts = idx[np.r_[True, np.diff(idx) > 1]]
        gaps.extend(np.diff(starts).tolist())
    return float(np.median(gaps)) if gaps else float("inf")


def merge_words(boxes: list[tuple[int, int, int, int]], max_gap_ratio: float = 0.8,
                min_overlap: float = 0.5) -> list[tuple[int, int, int, int]]:
    """Merge boxes (y0, x0, y1, x1 in cells, inclusive) that sit on the same line with a gap of at
    most ``max_gap_ratio`` x line height: joins words of large type that the fixed closing leaves apart."""
    boxes = sorted(boxes, key=lambda b: b[1])
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                ha, hb = a[2] - a[0] + 1, b[2] - b[0] + 1
                overlap = min(a[2], b[2]) - max(a[0], b[0]) + 1
                gap = max(a[1], b[1]) - min(a[3], b[3]) - 1
                if overlap >= min_overlap * min(ha, hb) and gap <= max_gap_ratio * max(ha, hb):
                    boxes[i] = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
                    del boxes[j]
                    changed = True
                    break
            if changed:
                break
    return boxes


def detect_in_frame(grey: np.ndarray, params: dict | None = None) -> list[dict]:
    """Text-like regions in one grey frame, bbox in this frame's pixels."""
    p = {**DEFAULTS, **(params or {})}
    h, w = grey.shape
    gx, gy = gradients(grey)
    thr = edge_threshold(gx)
    vert = gx > thr
    dens = cell_grid(vert)
    text = dens >= p["cell_density"]
    grouped = erode_h(dilate_h(text, p["close_cells"]), p["close_cells"]) | text
    regions = []
    boxes = merge_words([(y0, x0, y1, x1) for y0, x0, y1, x1, _ in components(grouped)])
    for y0, x0, y1, x1 in boxes:
        bx, by = x0 * CELL, y0 * CELL
        bw, bh = (x1 - x0 + 1) * CELL, (y1 - y0 + 1) * CELL
        if bh < p["min_height_px"] or bh > p["max_height_ratio"] * h or bw < p["min_aspect"] * bh:
            continue
        fill = float(text[y0:y1 + 1, x0:x1 + 1].any(axis=0).mean())  # share of columns with strokes
        if fill < p["min_fill"]:
            continue
        mid = vert[by + bh // 4: by + 3 * bh // 4 + 1, bx:bx + bw]
        # stroke edges per text-height of width: about 4 for ordinary Latin type at any size
        rate = float(mid.sum(axis=1).mean() / max(1, bw)) * bh if mid.size else 0.0
        if rate < p["min_edge_rate"]:
            continue
        gap = median_stroke_gap(mid) / bh
        if gap > p["max_stroke_gap"]:
            continue  # edges too far apart for letters: blobs, bokeh, shapes
        score = float(min(1.0, fill) * min(1.0, rate / 4.0))
        regions.append({"bbox": [bx, by, bw, bh], "score": score})
    return regions


def iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a[0], a[1], a[0] + a[2], a[1] + a[3]
    bx1, by1, bx2, by2 = b[0], b[1], b[0] + b[2], b[1] + b[3]
    iw, ih = max(0.0, min(ax2, bx2) - max(ax1, bx1)), max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def link_tracks(regions: list[dict], sample_dt: float, min_iou: float = 0.5) -> list[dict]:
    """Link regions of consecutive samples that overlap (IoU >= min_iou) into on-screen tracks."""
    tracks: list[dict] = []
    for t in sorted({r["t_s"] for r in regions}):
        used: set[int] = set()
        for r in sorted((r for r in regions if r["t_s"] == t), key=lambda r: -r["bbox"][2] * r["bbox"][3]):
            best, best_iou = None, min_iou
            for k, tr in enumerate(tracks):
                if k in used or t - tr["last_t"] > sample_dt * 1.5 + 1e-6:
                    continue
                v = iou(tr["bboxes"][-1], r["bbox"])
                if v >= best_iou:
                    best, best_iou = k, v
            if best is None:
                tracks.append({"first_t": t, "last_t": t, "bboxes": [r["bbox"]]})
                best = len(tracks) - 1
            else:
                tracks[best]["last_t"] = t
                tracks[best]["bboxes"].append(r["bbox"])
            used.add(best)
    out = []
    for tr in tracks:
        bb = np.median(np.array(tr["bboxes"], dtype=float), axis=0)
        out.append({"start_s": tr["first_t"], "end_s": tr["last_t"] + sample_dt, "samples": len(tr["bboxes"]),
                    "bbox": [float(v) for v in bb]})
    return out


def analyse(video: str, sample_fps: float = 2.0, width: int = 360, params: dict | None = None,
            info: dict | None = None) -> dict:
    info = info or media_info(video)
    W, H = info["width"], info["height"]
    regions, samples, first_t = [], 0, None
    sx = sy = None
    for t, grey in iter_frames(video, width=width, pix_fmt="gray", fps=sample_fps, info=info):
        samples += 1
        first_t = t if first_t is None else first_t
        if sx is None:
            sx, sy = W / grey.shape[1], H / grey.shape[0]
        for r in detect_in_frame(grey, params):
            x, y, w, h = r["bbox"]
            bbox = [x * sx, y * sy, w * sx, h * sy]
            regions.append({"t_s": t, "bbox": bbox, "area_ratio": (bbox[2] * bbox[3]) / (W * H),
                            "y_center_ratio": (bbox[1] + bbox[3] / 2) / H, "score": r["score"]})
    dt = 1.0 / sample_fps
    tracks = link_tracks(regions, dt)
    for tr in tracks:
        tr["y_center_ratio"] = (tr["bbox"][1] + tr["bbox"][3] / 2) / H
        tr["area_ratio"] = tr["bbox"][2] * tr["bbox"][3] / (W * H)
    times_with_text = {r["t_s"] for r in regions}
    lower = [r["y_center_ratio"] for r in regions if r["y_center_ratio"] > 0.5]
    summary = {
        "samples": samples,
        "text_presence_ratio": len(times_with_text) / samples if samples else None,
        "regions_per_sample": len(regions) / samples if samples else None,
        "lower_band_y_center_ratio": float(np.median(lower)) if lower else None,
        "first_sample_regions": [r for r in regions if first_t is not None and r["t_s"] == first_t],
    }
    return {"regions": regions, "tracks": tracks, "summary": summary, "frame_size": [W, H],
            "params": {**DEFAULTS, **(params or {}), "sample_fps": sample_fps, "width": width}}


def run(video: str, sample_fps: float = 2.0, **kw) -> dict:
    try:
        res = analyse(video, sample_fps=sample_fps, **kw)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except (RuntimeError, ValueError) as exc:
        return {"status": "error", "reason": str(exc)}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **res})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--fps", type=float, default=2.0, help="samples per second")
    ap.add_argument("--width", type=int, default=360, help="analysis width in pixels")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = run(a.video, sample_fps=a.fps, width=a.width)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
