"""Budget how much of the frame text covers, scene by scene.

Takes the text boxes a render spec will draw (title, caption, labels,
numbers) with their time windows and reports, for every moment where the set
of visible boxes changes:

* the union area of visible text boxes as a share of the frame (overlaps are
  not double counted);
* the number of separate text elements on screen;

and flags moments above ``max_fraction`` (default 18%) or ``max_elements``
(default 3). This keeps frames focused on the hook and captions instead of
piling on labels.

Usage::

    from text_area_budget import audit
    audit(frame=(1080, 1920), boxes=[{"name": "title", "rect": (90, 300, 900, 260), "start": 0, "end": 2.5}, ...])
"""

from __future__ import annotations


def _union_area(rects) -> float:
    """Area of the union of axis-aligned rectangles (coordinate compression)."""
    if not rects:
        return 0.0
    xs = sorted({r[0] for r in rects} | {r[0] + r[2] for r in rects})
    area = 0.0
    for x0, x1 in zip(xs, xs[1:]):
        spans = sorted((r[1], r[1] + r[3]) for r in rects if r[0] <= x0 and r[0] + r[2] >= x1)
        covered, cur_s, cur_e = 0.0, None, None
        for s, e in spans:
            if cur_e is None or s > cur_e:
                if cur_e is not None:
                    covered += cur_e - cur_s
                cur_s, cur_e = s, e
            else:
                cur_e = max(cur_e, e)
        if cur_e is not None:
            covered += cur_e - cur_s
        area += covered * (x1 - x0)
    return area


def audit(frame, boxes: list[dict], max_fraction: float = 0.18, max_elements: int = 3) -> dict:
    W, H = frame
    times = sorted({b["start"] for b in boxes} | {b["end"] for b in boxes})
    moments = []
    for t0, t1 in zip(times, times[1:]):
        mid = (t0 + t1) / 2
        vis = [b for b in boxes if b["start"] <= mid < b["end"]]
        frac = _union_area([b["rect"] for b in vis]) / (W * H)
        issues = []
        if frac > max_fraction:
            issues.append(f"text covers {frac:.0%} (max {max_fraction:.0%})")
        if len(vis) > max_elements:
            issues.append(f"{len(vis)} text elements (max {max_elements})")
        moments.append({"start": t0, "end": t1, "fraction": round(frac, 4), "elements": [b["name"] for b in vis],
                        "issues": issues})
    return {"passed": all(not m["issues"] for m in moments), "moments": moments,
            "peak_fraction": max((m["fraction"] for m in moments), default=0.0)}
