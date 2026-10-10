"""Plan a camera move for every shot so consecutive shots alternate.

Quick-cut shorts read as lively when shot moves alternate (in, out, in...)
and pans break up long runs. This planner assigns a move to each shot:

* zooms alternate direction, and the same move never repeats back to back;
* every ``pan_every``-th shot is a pan, alternating left/right;
* zoom strength grows with shot length at ``zoom_rate`` per second, clamped
  to [``min_zoom``, ``max_zoom``], so short shots do not snap and long shots
  do not crawl;
* shots shorter than ``punch_below`` seconds get a "punch" (an instant scale
  step at the cut) instead of a slow move.

Output views use the same ``(cx, cy, zoom)`` convention as the ken_burns_path
module, so the plan can be rendered with it directly.

Usage::

    from alternating_zoom_planner import plan_moves
    for m in plan_moves([3.2, 2.8, 0.9, 4.0], focus=[(0.5, 0.4)] * 4):
        print(m["move"], m["start"], m["end"])
"""

from __future__ import annotations


def plan_moves(durations, focus=None, zoom_rate: float = 0.04, min_zoom: float = 1.06,
               max_zoom: float = 1.25, pan_every: int = 4, punch_below: float = 1.2,
               punch_scale: float = 1.08, start_with: str = "zoom_in") -> list[dict]:
    if start_with not in ("zoom_in", "zoom_out"):
        raise ValueError("start_with must be zoom_in or zoom_out")
    if focus is not None and len(focus) != len(durations):
        raise ValueError("focus needs one (fx, fy) per shot")
    moves: list[dict] = []
    zoom_dir = start_with
    pan_dir = "pan_right"
    prev = None
    for i, d in enumerate(durations):
        if d <= 0:
            raise ValueError(f"shot {i} has non-positive duration")
        fx, fy = focus[i] if focus is not None else (0.5, 0.5)
        strength = min(max_zoom, max(min_zoom, 1.0 + zoom_rate * d))
        if d < punch_below:
            move = "punch"
            start, end = (fx, fy, punch_scale), (fx, fy, punch_scale)
        elif pan_every and (i + 1) % pan_every == 0:
            move = pan_dir
            pan_dir = "pan_left" if pan_dir == "pan_right" else "pan_right"
            travel = 0.5 - 0.5 / strength
            sx, ex = (0.5 - travel, 0.5 + travel) if move == "pan_right" else (0.5 + travel, 0.5 - travel)
            start, end = (sx, fy, strength), (ex, fy, strength)
        else:
            move = zoom_dir
            if move == prev:
                move = "zoom_out" if move == "zoom_in" else "zoom_in"
            start, end = ((fx, fy, 1.0), (fx, fy, strength)) if move == "zoom_in" else \
                ((fx, fy, strength), (fx, fy, 1.0))
            zoom_dir = "zoom_out" if move == "zoom_in" else "zoom_in"
        moves.append({"index": i, "duration": d, "move": move, "start": start, "end": end})
        prev = move
    return moves


def summary(moves: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for m in moves:
        counts[m["move"]] = counts.get(m["move"], 0) + 1
    repeats = sum(1 for a, b in zip(moves, moves[1:]) if a["move"] == b["move"] and a["move"] != "punch")
    return {"counts": counts, "back_to_back_repeats": repeats}
