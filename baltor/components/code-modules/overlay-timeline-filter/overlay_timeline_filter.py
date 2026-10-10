"""Schedule image/video overlays on a timeline with alpha fades (ffmpeg).

Each overlay item: input index, position (numbers or expressions), optional
size, start/end time, fade-in/out seconds and opacity (capped at 0.98). The
builder chains ``overlay`` filters with ``enable='between(t,a,b)'`` and makes
the overlay stream fade with ``fade=...:alpha=1`` shifted to its start time
(``setpts=PTS-STARTPTS+a/TB``), so a sticker or label input that starts at
t=0 appears at its slot.

``conflicts`` lists overlays that occupy the same region at the same time
(the house style avoids stacked labels).

Usage::

    from overlay_timeline_filter import Item, build, conflicts
    graph, out = build("[0:v]", [Item(1, x=60, y=240, start=2.0, end=5.0, fade=0.25, w=960),
                                 Item(2, x="(W-w)/2", y="H*0.7", start=6, end=9)])
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Item:
    input: int
    x: float | str = 0
    y: float | str = 0
    start: float = 0.0
    end: float = 1.0
    fade: float = 0.2
    opacity: float = 0.98
    w: int | None = None
    h: int | None = None
    box: tuple | None = None  # (x, y, w, h) footprint for conflict checks when x/y are expressions


def _expr(v) -> str:
    s = str(v)
    if "'" in s:
        raise ValueError("expressions may not contain quotes")
    return f"'{s}'" if not isinstance(v, (int, float)) else f"{v:g}"


def build(base: str, items: list[Item], out_label: str = "[ov_out]") -> tuple[str, str]:
    parts = []
    acc = base
    for i, it in enumerate(items):
        if it.end <= it.start:
            raise ValueError(f"item {i}: end must be after start")
        if not 0 < it.opacity <= 0.98:
            raise ValueError(f"item {i}: opacity must be within (0, 0.98]")
        if it.fade * 2 > it.end - it.start:
            raise ValueError(f"item {i}: fades are longer than the item")
        chain = [f"[{it.input}:v]format=rgba"]
        if it.w or it.h:
            chain.append(f"scale={it.w or -1}:{it.h or -1}")
        chain.append(f"colorchannelmixer=aa={it.opacity:g}")
        chain.append(f"setpts=PTS-STARTPTS+{it.start:g}/TB")
        if it.fade > 0:
            chain.append(f"fade=t=in:st={it.start:g}:d={it.fade:g}:alpha=1")
            chain.append(f"fade=t=out:st={it.end - it.fade:g}:d={it.fade:g}:alpha=1")
        parts.append(",".join(chain) + f"[ov{i}]")
        nxt = out_label if i == len(items) - 1 else f"[ovacc{i}]"
        parts.append(f"{acc}[ov{i}]overlay=x={_expr(it.x)}:y={_expr(it.y)}:"
                     f"enable='between(t,{it.start:g},{it.end:g})':eof_action=pass:format=auto{nxt}")
        acc = nxt
    if not items:
        return f"{base}null{out_label}", out_label
    return ";".join(parts), out_label


def conflicts(items: list[Item]) -> list[tuple[int, int]]:
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if a.end <= b.start or b.end <= a.start:
                continue
            ba = a.box or ((a.x, a.y, a.w or 0, a.h or 0) if isinstance(a.x, (int, float)) and isinstance(a.y, (int, float)) else None)
            bb = b.box or ((b.x, b.y, b.w or 0, b.h or 0) if isinstance(b.x, (int, float)) and isinstance(b.y, (int, float)) else None)
            if ba is None or bb is None:
                out.append((i, j))  # unknown footprint: report the time overlap
                continue
            if ba[0] < bb[0] + bb[2] and bb[0] < ba[0] + ba[2] and ba[1] < bb[1] + bb[3] and bb[1] < ba[1] + ba[3]:
                out.append((i, j))
    return out
