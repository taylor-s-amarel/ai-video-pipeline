"""Follow an ffmpeg render: parse ``-progress pipe:1`` output into percent and ETA.

ffmpeg's ``-progress`` writes blocks of ``key=value`` lines ending with
``progress=continue`` or ``progress=end``. ``ProgressParser.feed(line)``
returns a snapshot dict at the end of each block (frame, fps, out_time in
seconds, speed, percent of the expected duration and ETA in seconds).
``run_with_progress`` runs an argv list and calls back on every snapshot.

Usage::

    from ffmpeg_progress_parser import run_with_progress
    run_with_progress(["ffmpeg", "-i", "in.mp4", ..., "out.mp4"], duration=64.0,
                      on_progress=lambda s: print(f"{s['percent']:.0f}% eta {s['eta_s']:.0f}s"))
"""

from __future__ import annotations

import subprocess


def _seconds(v: str) -> float | None:
    try:
        if ":" in v:
            h, m, s = v.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
        return int(v) / 1_000_000  # out_time_us / out_time_ms (both microseconds in ffmpeg)
    except ValueError:
        return None


class ProgressParser:
    def __init__(self, duration: float | None = None):
        self.duration = duration
        self.block: dict[str, str] = {}

    def feed(self, line: str) -> dict | None:
        line = line.strip()
        if "=" not in line:
            return None
        k, v = line.split("=", 1)
        self.block[k.strip()] = v.strip()
        if k != "progress":
            return None
        b, self.block = self.block, {}
        t = None
        if "out_time" in b:
            t = _seconds(b["out_time"])
        if t is None and "out_time_us" in b:
            t = _seconds(b["out_time_us"])
        speed = None
        if b.get("speed", "N/A") not in ("N/A", ""):
            try:
                speed = float(b["speed"].rstrip("x"))
            except ValueError:
                speed = None
        snap = {"frame": int(b["frame"]) if b.get("frame", "").isdigit() else None,
                "fps": float(b["fps"]) if b.get("fps") not in (None, "", "N/A") else None,
                "out_time_s": t, "speed": speed, "done": v == "end", "percent": None, "eta_s": None}
        if self.duration and t is not None:
            snap["percent"] = 100.0 if v == "end" else max(0.0, min(100.0, 100.0 * t / self.duration))
            if speed and speed > 0:
                snap["eta_s"] = max(0.0, (self.duration - t) / speed)
        return snap


def with_progress_flags(argv: list[str]) -> list[str]:
    if not argv or "ffmpeg" not in argv[0]:
        raise ValueError("argv must start with ffmpeg")
    return [argv[0], "-progress", "pipe:1", "-nostats", "-nostdin"] + argv[1:]


def run_with_progress(argv: list[str], duration: float | None, on_progress=None, timeout: float | None = None) -> int:
    parser = ProgressParser(duration)
    proc = subprocess.Popen(with_progress_flags(argv), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.stdout is not None
    for line in proc.stdout:
        snap = parser.feed(line)
        if snap and on_progress:
            on_progress(snap)
    proc.wait(timeout=timeout)
    return proc.returncode
