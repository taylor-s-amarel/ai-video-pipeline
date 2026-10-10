"""Turn scripted beats into a shot list with pacing and camera moves.

Each beat (narration line, with optional asset and emphasis) becomes one or
more shots: beats longer than ``max_shot_s`` are split into quick cuts so
the picture changes at least that often; every shot gets a camera move that
alternates (zoom in, zoom out, pan) and emphasised beats get a punch-in.
The output is a flat list that a renderer or an editor can follow.

Usage::

    from shot_list_planner import plan_shots
    shots = plan_shots([{"text": "In 1970, five scientists...", "duration": 5.2, "asset": "habitat.jpg"},
                        {"text": "They lived 50 feet down.", "duration": 3.1, "asset": "reef.mp4", "emphasis": True}])
"""

from __future__ import annotations

import math

MOVES = ("zoom_in", "zoom_out", "zoom_in", "pan_right", "zoom_out", "zoom_in", "pan_left")


def plan_shots(beats: list[dict], max_shot_s: float = 3.0, min_shot_s: float = 0.8, start: float = 0.0) -> list[dict]:
    if max_shot_s <= min_shot_s:
        raise ValueError("max_shot_s must be larger than min_shot_s")
    shots, t, k = [], start, 0
    for bi, b in enumerate(beats):
        d = float(b["duration"])
        if d <= 0:
            raise ValueError(f"beat {bi} has no duration")
        n = max(1, math.ceil(d / max_shot_s))
        while n > 1 and d / n < min_shot_s:
            n -= 1
        for si in range(n):
            sd = d / n
            move = "punch_in" if b.get("emphasis") and si == 0 else MOVES[k % len(MOVES)]
            shots.append({"index": len(shots), "beat": bi, "start": round(t, 3), "end": round(t + sd, 3),
                          "duration": round(sd, 3), "asset": b.get("asset"), "move": move,
                          "text": b.get("text", "") if si == 0 else ""})
            t += sd
            k += 1
    return shots


def pacing(shots: list[dict]) -> dict:
    ds = [s["duration"] for s in shots]
    return {"shots": len(ds), "mean_shot_s": round(sum(ds) / len(ds), 3) if ds else 0.0,
            "longest_s": max(ds, default=0.0), "cuts_per_minute": round(60 * len(ds) / sum(ds), 1) if ds else 0.0}
