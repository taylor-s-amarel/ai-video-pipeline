"""Safe areas for vertical video: keep text clear of platform UI overlays.

Short-video apps draw buttons, captions and progress UI over the edges of a
9:16 frame. Platforms publish and change their own guidance, so this module
is profile-driven: a profile is margins as fractions of the frame
(top, bottom, left, right). The built-in ``house-9x16-conservative`` profile
is this project's own conservative default (not a platform specification);
add profiles from current official guidance as JSON when you have it.

Functions: ``safe_rect``, ``check_box`` (is a text box inside the safe
area?), ``caption_band`` (where a caption line may sit) and ``load_profiles``.

Usage::

    from platform_safe_areas import safe_rect, check_box, caption_band
    safe_rect((1080, 1920))                              # (x, y, w, h)
    check_box((1080, 1920), (90, 300, 900, 260))         # [] when inside
"""

from __future__ import annotations

import json

PROFILES = {
    "house-9x16-conservative": {"top": 0.12, "bottom": 0.22, "left": 0.06, "right": 0.12,
                                "note": "Project default; verify against each platform's current guidance."},
    "house-9x16-minimal": {"top": 0.05, "bottom": 0.10, "left": 0.04, "right": 0.04,
                           "note": "Only for full-screen players without overlays (e.g. a website embed)."},
    "house-16x9-title-safe": {"top": 0.10, "bottom": 0.10, "left": 0.10, "right": 0.10,
                              "note": "Generic 10% title-safe margin for landscape video."},
}


def load_profiles(text: str) -> dict:
    data = json.loads(text)
    for name, p in data.items():
        for k in ("top", "bottom", "left", "right"):
            v = p.get(k)
            if not isinstance(v, (int, float)) or not 0 <= v < 0.5:
                raise ValueError(f"profile {name}: {k} must be a fraction in [0, 0.5)")
    return {**PROFILES, **data}


def safe_rect(frame, profile: str = "house-9x16-conservative", profiles: dict | None = None) -> tuple[int, int, int, int]:
    p = (profiles or PROFILES)[profile]
    W, H = frame
    x, y = round(W * p["left"]), round(H * p["top"])
    return x, y, round(W * (1 - p["right"])) - x, round(H * (1 - p["bottom"])) - y


def check_box(frame, box, profile: str = "house-9x16-conservative", profiles: dict | None = None) -> list[str]:
    sx, sy, sw, sh = safe_rect(frame, profile, profiles)
    bx, by, bw, bh = box
    out = []
    if bx < sx:
        out.append(f"left edge {bx} is inside the {sx}px left UI margin")
    if by < sy:
        out.append(f"top edge {by} is inside the {sy}px top UI margin")
    if bx + bw > sx + sw:
        out.append(f"right edge {bx + bw} passes the safe edge at {sx + sw}")
    if by + bh > sy + sh:
        out.append(f"bottom edge {by + bh} passes the safe edge at {sy + sh}")
    return out


def caption_band(frame, line_height: int, profile: str = "house-9x16-conservative", position: float = 0.78,
                 profiles: dict | None = None) -> tuple[int, int, int, int]:
    """Box for one caption line near ``position`` (fraction of height), clamped into the safe area."""
    sx, sy, sw, sh = safe_rect(frame, profile, profiles)
    y = round(frame[1] * position - line_height / 2)
    y = min(max(y, sy), sy + sh - line_height)
    return sx, y, sw, line_height
