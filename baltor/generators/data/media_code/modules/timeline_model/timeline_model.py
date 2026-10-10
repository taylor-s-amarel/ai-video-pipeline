"""A small multi-track timeline model with validation and JSON round trip.

Tracks hold clips (source, in/out within the source, start on the timeline,
optional opacity and label). The model answers what a renderer needs:
total duration, what is active at time t on each track, gaps and overlaps
per track, and clips that run past their source length.

Usage::

    from timeline_model import Timeline, Clip
    tl = Timeline(fps=30)
    tl.add("bg", Clip("waves.mp4", 0, 64, start=0, source_duration=120))
    tl.add("photo", Clip("p1.jpg", 0, 16, start=0, opacity=0.98))
    tl.problems()        # gaps, overlaps, out-of-range clips
    tl.at(10.0)          # {'bg': Clip(...), 'photo': Clip(...)}
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class Clip:
    source: str
    in_s: float
    out_s: float
    start: float
    opacity: float = 0.98
    label: str = ""
    source_duration: float | None = None

    @property
    def duration(self) -> float:
        return self.out_s - self.in_s

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass
class Timeline:
    fps: float = 30.0
    tracks: dict = field(default_factory=dict)

    def add(self, track: str, clip: Clip) -> None:
        if clip.out_s <= clip.in_s:
            raise ValueError(f"{clip.source}: out must be after in")
        if clip.start < 0:
            raise ValueError(f"{clip.source}: start must be >= 0")
        self.tracks.setdefault(track, []).append(clip)
        self.tracks[track].sort(key=lambda c: c.start)

    @property
    def duration(self) -> float:
        return max((c.end for cs in self.tracks.values() for c in cs), default=0.0)

    def at(self, t: float) -> dict:
        out = {}
        for name, clips in self.tracks.items():
            for c in clips:
                if c.start <= t < c.end:
                    out[name] = c
        return out

    def problems(self, continuous: tuple = (), tol: float = 1e-6, max_opacity: float = 0.98) -> list[str]:
        probs = []
        for name, clips in self.tracks.items():
            for a, b in zip(clips, clips[1:]):
                if b.start < a.end - tol:
                    probs.append(f"{name}: {a.source} overlaps {b.source} by {a.end - b.start:.3f}s")
                elif name in continuous and b.start > a.end + tol:
                    probs.append(f"{name}: gap of {b.start - a.end:.3f}s before {b.source}")
            if name in continuous and clips and clips[0].start > tol:
                probs.append(f"{name}: starts at {clips[0].start:.3f}s instead of 0")
            if name in continuous and clips and clips[-1].end < self.duration - tol:
                probs.append(f"{name}: ends at {clips[-1].end:.3f}s before the timeline ends")
            for c in clips:
                if c.source_duration is not None and c.out_s > c.source_duration + tol:
                    probs.append(f"{name}: {c.source} out point {c.out_s}s is past its {c.source_duration}s source")
                if c.opacity > max_opacity:
                    probs.append(f"{name}: {c.source} opacity {c.opacity} > {max_opacity}")
        return probs

    def to_json(self) -> str:
        return json.dumps({"fps": self.fps, "tracks": {k: [asdict(c) for c in v] for k, v in self.tracks.items()}},
                          indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "Timeline":
        d = json.loads(text)
        tl = cls(fps=d["fps"])
        for name, clips in d["tracks"].items():
            for c in clips:
                tl.add(name, Clip(**c))
        return tl
