"""Validate first-frame title placement against the house rules.

Rules checked (all thresholds are parameters):

* the title box centre sits in the upper part of the frame
  (centre y <= 40% of the height);
* the title is overlaid on the main photo (its box overlaps the photo box by
  at least ``min_overlap`` of the title area);
* the photo keeps its size: at least 80% of the frame width, and never
  smaller than the reference layout (``reference_photo``) to make room for
  the title;
* the title box stays inside the frame margins and has a minimum height
  (legible size).

Usage::

    from title_placement_validator import check
    findings = check(frame=(1080, 1920), title=(90, 300, 900, 260), photo=(54, 220, 972, 1300))
    # [] means every rule passes
"""

from __future__ import annotations


def _area(r):
    return max(0.0, r[2]) * max(0.0, r[3])


def _intersection(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def check(frame, title, photo=None, reference_photo=None, max_center_y: float = 0.40,
          min_overlap: float = 0.6, min_photo_width: float = 0.80, margin: float = 0.03,
          min_title_height: float = 0.05) -> list[dict]:
    W, H = frame
    out = []

    def add(rule, msg):
        out.append({"rule": rule, "message": msg})

    tx, ty, tw, th = title
    cy = (ty + th / 2) / H
    if cy > max_center_y:
        add("title_upper", f"title centre at {cy:.0%} of height (must be <= {max_center_y:.0%})")
    mx, my = W * margin, H * margin
    if tx < mx - 1e-9 or ty < my - 1e-9 or tx + tw > W - mx + 1e-9 or ty + th > H - my + 1e-9:
        add("title_margins", "title box crosses the frame margins")
    if th < min_title_height * H:
        add("title_size", f"title box is {th / H:.1%} of height (min {min_title_height:.0%})")
    if photo is not None:
        ov = _intersection(title, photo) / max(_area(title), 1e-9)
        if ov < min_overlap:
            add("title_over_photo", f"only {ov:.0%} of the title overlaps the photo (min {min_overlap:.0%})")
        if photo[2] < min_photo_width * W:
            add("photo_width", f"photo is {photo[2] / W:.0%} of frame width (min {min_photo_width:.0%})")
        if reference_photo is not None and _area(photo) < _area(reference_photo) * 0.999:
            add("photo_not_shrunk", "photo is smaller than the reference layout; move the title, not the photo")
    return out


def suggest_title_box(frame, photo, title_size, top_fraction: float = 0.22) -> tuple:
    """A compliant title box of ``title_size`` (w, h) centred on the photo's upper part."""
    W, H = frame
    tw, th = title_size
    x = photo[0] + (photo[2] - tw) / 2
    cy = max(photo[1] + th / 2 + 0.02 * H, top_fraction * H)
    return (round(x), round(cy - th / 2), tw, th)
