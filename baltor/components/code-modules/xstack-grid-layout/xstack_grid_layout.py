"""Layouts for ffmpeg ``xstack``: any rows x columns grid with gutters.

``grid`` computes even cell sizes (rounded down to even numbers for
yuv420p) with an outer margin and gutters between cells, and returns the
``layout`` string with absolute pixel positions plus per-cell rectangles.
``xstack_filter`` produces the full filter text, scaling each input to its
cell (cover-crop so nothing is letterboxed) and filling gaps with a colour.

Usage::

    from xstack_grid_layout import grid, xstack_filter
    g = grid(rows=2, cols=2, size=(1080, 1920), gutter=24, margin=40)
    graph, out = xstack_filter(4, g, fill="black")
"""

from __future__ import annotations


def _even(v: float) -> int:
    v = int(v)
    return v - (v % 2)


def grid(rows: int, cols: int, size=(1080, 1920), gutter: int = 0, margin: int = 0) -> dict:
    if rows < 1 or cols < 1:
        raise ValueError("rows and cols must be >= 1")
    W, H = size
    cw = _even((W - 2 * margin - (cols - 1) * gutter) / cols)
    ch = _even((H - 2 * margin - (rows - 1) * gutter) / rows)
    if cw < 2 or ch < 2:
        raise ValueError("gutters and margins leave no room for cells")
    cells = []
    for r in range(rows):
        for c in range(cols):
            cells.append((margin + c * (cw + gutter), margin + r * (ch + gutter), cw, ch))
    layout = "|".join(f"{x}_{y}" for x, y, _, _ in cells)
    return {"size": (W, H), "cell": (cw, ch), "cells": cells, "layout": layout}


def xstack_filter(n_inputs: int, g: dict, fill: str = "black", label_prefix: str = "") -> tuple[str, str]:
    if n_inputs != len(g["cells"]):
        raise ValueError(f"layout has {len(g['cells'])} cells but {n_inputs} inputs were given")
    cw, ch = g["cell"]
    W, H = g["size"]
    parts = []
    labels = []
    for i in range(n_inputs):
        lab = f"[{label_prefix}c{i}]"
        parts.append(f"[{i}:v]scale={cw}:{ch}:force_original_aspect_ratio=increase,crop={cw}:{ch},setsar=1{lab}")
        labels.append(lab)
    out = f"[{label_prefix}grid]"
    stack = f"{''.join(labels)}xstack=inputs={n_inputs}:layout={g['layout']}:fill={fill}"
    # xstack sizes its canvas to the cells; pad to the full frame so margins are kept
    parts.append(f"{stack},pad={W}:{H}:0:0:color={fill}{out}")
    return ";".join(parts), out
