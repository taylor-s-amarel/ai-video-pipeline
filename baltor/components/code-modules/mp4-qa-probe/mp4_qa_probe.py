"""Check an exported MP4 against measurable short-video house rules using ffprobe.

Usage: python mp4_qa_probe.py video.mp4 [--min-duration 60] [--json]
Exit status 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def probe(path: str) -> dict:
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is not installed")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def evaluate(info: dict, min_duration: float = 60.0, width: int = 1080, height: int = 1920) -> list[Check]:
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    checks = [Check("duration", duration >= min_duration, f"{duration:.2f}s (minimum {min_duration:.0f}s)")]
    if video is None:
        checks.append(Check("video_stream", False, "no video stream"))
    else:
        w, h = int(video.get("width", 0)), int(video.get("height", 0))
        checks.append(Check("resolution", (w, h) == (width, height), f"{w}x{h} (expected {width}x{height})"))
        checks.append(Check("codec", video.get("codec_name") in {"h264", "hevc"}, str(video.get("codec_name"))))
        checks.append(Check("pixel_format", video.get("pix_fmt") == "yuv420p", str(video.get("pix_fmt"))))
    checks.append(Check("audio_stream", audio is not None, audio.get("codec_name", "") if audio else "no audio"))
    if audio is not None:
        checks.append(Check("audio_rate", int(audio.get("sample_rate", 0)) >= 44100, f"{audio.get('sample_rate')} Hz"))
    faststart = info.get("format", {}).get("format_name", "")
    checks.append(Check("container", "mp4" in faststart, faststart))
    return checks


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video")
    ap.add_argument("--min-duration", type=float, default=60.0)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    checks = evaluate(probe(a.video), a.min_duration, a.width, a.height)
    if a.json:
        print(json.dumps([asdict(c) for c in checks], indent=2))
    else:
        for c in checks:
            print(f"{'PASS' if c.passed else 'FAIL'}  {c.name:<14} {c.detail}")
    return 0 if all(c.passed for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
