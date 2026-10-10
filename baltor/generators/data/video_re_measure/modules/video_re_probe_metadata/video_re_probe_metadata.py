"""Probe a video's container and stream facts with ffprobe (the 'file header' of the disassembly).

Usage:
    python video_re_probe_metadata.py video.mp4 [--out probe.json]

Returns display width/height with rotation metadata and non-square pixels applied, average fps,
duration, audio presence and codec facts. Everything comes straight from ffprobe; nothing is guessed.
"""

from __future__ import annotations

import argparse

from video_re_common import clean, dump_json, media_info_from_probe, probe, tool_versions, ToolMissing, unavailable

IDENTITY = "video_re_probe_metadata"
VERSION = "1.0.0"


def describe(info: dict) -> dict:
    """Derived, still measured, facts: orientation and aspect label."""
    w, h = info.get("width"), info.get("height")
    out = {"orientation": None, "aspect": None}
    if w and h:
        out["orientation"] = "vertical" if h > w else "horizontal" if w > h else "square"
        r = w / h
        known = {"9:16": 9 / 16, "16:9": 16 / 9, "1:1": 1.0, "4:5": 4 / 5, "4:3": 4 / 3, "3:4": 3 / 4, "21:9": 21 / 9}
        name, val = min(known.items(), key=lambda kv: abs(kv[1] - r))
        out["aspect"] = name if abs(val - r) / val < 0.02 else f"{w}:{h}"
    return out


def run(video: str) -> dict:
    try:
        raw = probe(video)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except RuntimeError as exc:
        return {"status": "error", "reason": str(exc)}
    from pathlib import Path

    info = media_info_from_probe(raw, reference=Path(video).name)
    if info.get("width") is None:
        return {"status": "error", "reason": "no video stream", "source": info}
    source = {k: info[k] for k in ("reference", "duration_s", "width", "height", "fps", "has_audio")}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, "source": source,
                  "details": {**info, **describe(info)}, "tools": tool_versions(("ffprobe",), ())})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    a = ap.parse_args(argv)
    res = run(a.video)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
