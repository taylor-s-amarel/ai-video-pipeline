"""Split a video's length across hook, numbered items and outro.

Given a target total (default 64 s, never below the 60 s house minimum),
the number of items (FACT 1..N, TIP 1..N, top-10 entries) and their relative
weights (for example words of narration per item), allocates durations:
fixed hook and outro, the rest shared by weight, each item clamped to
[min_item, max_item], with rounding to whole frames and the remainder put on
the last item so the total is exact. Returns scenes with labels and times.

Usage::

    from scene_duration_planner import plan
    plan(n_items=4, total=64, label="FACT", weights=[38, 42, 35, 40])
"""

from __future__ import annotations


def plan(n_items: int, total: float = 64.0, label: str = "FACT", weights=None, hook: float = 4.0,
         outro: float = 4.0, min_item: float = 6.0, max_item: float = 30.0, fps: float = 30.0,
         min_total: float = 60.0) -> list[dict]:
    if n_items < 1:
        raise ValueError("need at least one item")
    if total < min_total:
        raise ValueError(f"total {total}s is below the {min_total}s minimum")
    weights = list(weights) if weights is not None else [1.0] * n_items
    if len(weights) != n_items or any(w <= 0 for w in weights):
        raise ValueError("weights must be positive, one per item")
    body = total - hook - outro
    if body < n_items * min_item:
        raise ValueError(f"{body:.1f}s cannot hold {n_items} items of at least {min_item}s")
    if body > n_items * max_item:
        raise ValueError(f"{body:.1f}s is more than {n_items} items of at most {max_item}s; add items or shorten")
    # water-filling: clamp items over the maximum first, then items under the minimum,
    # and share what is left by weight among the rest until nothing violates the bounds
    durs: list = [None] * n_items
    remaining, free = body, list(range(n_items))
    while free:
        wsum = sum(weights[i] for i in free)
        share = {i: remaining * weights[i] / wsum for i in free}
        over = [i for i in free if share[i] > max_item]
        under = [i for i in free if share[i] < min_item]
        fix, value = (over, max_item) if over else (under, min_item)
        if not fix:
            for i in free:
                durs[i] = share[i]
            break
        for i in fix:
            durs[i] = value
            remaining -= value
            free.remove(i)
    if not free and abs(remaining) > 1e-9:
        durs[-1] += remaining  # cannot happen within the checked bounds; keep the total exact anyway
    frame = 1.0 / fps
    out, t = [], 0.0
    scenes = [("HOOK", hook)] + [(f"{label} {i + 1}", d) for i, d in enumerate(durs)] + [("OUTRO", outro)]
    for k, (name, d) in enumerate(scenes):
        end = total if k == len(scenes) - 1 else round((t + d) / frame) * frame
        out.append({"label": name, "start_s": round(t, 4), "end_s": round(end, 4), "duration_s": round(end - t, 4)})
        t = end
    return out
