"""Chain N clips with ffmpeg ``xfade`` (video) and ``acrossfade`` (audio).

Each transition overlaps two clips, so the offset of transition k is the sum
of the previous clip durations minus all previous transition durations. Wrong
offsets are the usual reason xfade chains freeze or cut early; this module
does the arithmetic and validates transition names against the xfade list in
ffmpeg 6.x.

Usage::

    from xfade_chain_builder import build_chain, total_duration
    graph, vout, aout = build_chain([5.0, 4.0, 6.0], [("fade", 0.5), ("slideleft", 0.4)])
    argv = ["ffmpeg", "-i", "a.mp4", "-i", "b.mp4", "-i", "c.mp4", "-filter_complex", graph,
            "-map", vout, "-map", aout, "out.mp4"]
"""

from __future__ import annotations

TRANSITIONS = {
    "fade", "wipeleft", "wiperight", "wipeup", "wipedown", "slideleft", "slideright", "slideup",
    "slidedown", "circlecrop", "rectcrop", "distance", "fadeblack", "fadewhite", "radial",
    "smoothleft", "smoothright", "smoothup", "smoothdown", "circleopen", "circleclose", "vertopen",
    "vertclose", "horzopen", "horzclose", "dissolve", "pixelize", "diagtl", "diagtr", "diagbl",
    "diagbr", "hlslice", "hrslice", "vuslice", "vdslice", "hblur", "fadegrays", "wipetl", "wipetr",
    "wipebl", "wipebr", "squeezeh", "squeezev", "zoomin", "fadefast", "fadeslow",
}


def offsets(durations, transitions) -> list[float]:
    if len(transitions) != len(durations) - 1:
        raise ValueError("need exactly one transition between each pair of clips")
    out, elapsed = [], 0.0
    for i, (name, d) in enumerate(transitions):
        if name not in TRANSITIONS:
            raise ValueError(f"unknown xfade transition {name!r}")
        if d <= 0:
            raise ValueError("transition duration must be > 0")
        if d >= durations[i] or d >= durations[i + 1]:
            raise ValueError(f"transition {i} ({d}s) is longer than a clip it joins")
        elapsed += durations[i] - d
        out.append(round(elapsed, 6))
    # a transition must also finish before the next transition starts
    for i in range(1, len(transitions)):
        if transitions[i - 1][1] + transitions[i][1] > durations[i] + 1e-9:
            raise ValueError(f"transitions around clip {i} overlap each other")
    return out


def total_duration(durations, transitions) -> float:
    return sum(durations) - sum(d for _, d in transitions)


def build_chain(durations, transitions, audio: bool = True, audio_curve: str = "tri") -> tuple[str, str, str | None]:
    """Return (filter_complex, video_label, audio_label) for inputs 0..N-1."""
    n = len(durations)
    if n < 2:
        raise ValueError("need at least two clips")
    offs = offsets(durations, transitions)
    parts = []
    prev_v = "[0:v]"
    prev_a = "[0:a]"
    for k, ((name, d), off) in enumerate(zip(transitions, offs), start=1):
        vout = f"[v{k}]"
        parts.append(f"{prev_v}[{k}:v]xfade=transition={name}:duration={d:g}:offset={off:g}{vout}")
        prev_v = vout
        if audio:
            aout = f"[a{k}]"
            parts.append(f"{prev_a}[{k}:a]acrossfade=d={d:g}:c1={audio_curve}:c2={audio_curve}{aout}")
            prev_a = aout
    return ";".join(parts), prev_v, (prev_a if audio else None)
