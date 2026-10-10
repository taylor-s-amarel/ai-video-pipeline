"""Loudness, dynamics and silence of a video's soundtrack (EBU R128 via ffmpeg).

Usage:
    python video_re_audio_loudness.py video.mp4 [--silence-db -50] [--out loudness.json]

One ffmpeg pass runs ``ebur128=peak=true:metadata=1`` (momentary/short-term loudness every 100 ms
and the R128 summary), ``astats`` (RMS and sample peak) and ``silencedetect``. Reported:

* integrated_lufs, loudness_range (LU), lra_low/lra_high (LUFS), true_peak_dbtp - the ebur128 summary
* rms_db, sample_peak_db - astats over all channels
* short_term - short-term (3 s) loudness once per second, LUFS; momentary_max_lufs
* silence - segments quieter than ``silence_db`` for at least ``silence_min_s`` and their share of
  the running time

Values are measurements of the delivered file, after any platform re-encode. For files under about
3 s the loudness range is not meaningful. A video without an audio stream returns status
'unavailable' and no numbers.
"""

from __future__ import annotations

import argparse
import re

from video_re_common import ToolMissing, clean, dump_json, media_info, run as run_cmd, tool_versions, unavailable

IDENTITY = "video_re_audio_loudness"
VERSION = "1.0.0"

NUM = r"(-?\d+(?:\.\d+)?|-?inf|nan)"


def _f(x: str | None) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)
    except ValueError:
        return None
    return None if v != v or v in (float("inf"), float("-inf")) else v


def parse_summary(stderr: str) -> dict:
    part = stderr[stderr.rfind("Summary:"):] if "Summary:" in stderr else ""
    def grab(label):
        m = re.search(label + r":\s*" + NUM, part)
        return _f(m.group(1)) if m else None
    integrated = grab(r"\bI")
    return {"integrated_lufs": integrated if integrated is not None and integrated > -69.99 else None,
            "loudness_range": grab("LRA"), "lra_low": grab("LRA low"), "lra_high": grab("LRA high"),
            "true_peak_dbtp": grab("Peak")}


def parse_astats(stderr: str) -> dict:
    i = stderr.rfind("Overall")
    part = stderr[i:] if i >= 0 else ""
    def grab(label):
        m = re.search(label + r":\s*" + NUM, part)
        return _f(m.group(1)) if m else None
    return {"rms_db": grab("RMS level dB"), "sample_peak_db": grab("Peak level dB")}


def parse_silence(stderr: str, duration: float | None) -> dict:
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?\d+(?:\.\d+)?)", stderr)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?\d+(?:\.\d+)?)", stderr)]
    segs = []
    for k, s in enumerate(starts):
        e = ends[k] if k < len(ends) else duration
        if e is not None:
            segs.append({"start_s": max(0.0, s), "end_s": e})
    total = sum(s["end_s"] - s["start_s"] for s in segs)
    return {"segments": segs, "share": (total / duration) if duration else None}


def parse_series(stdout: str) -> tuple[list[dict], float | None]:
    series, mmax = [], None
    t = None
    for line in stdout.splitlines():
        if line.startswith("frame:"):
            m = re.search(r"pts_time:(-?\d+(?:\.\d+)?)", line)
            t = float(m.group(1)) if m else None
        elif line.startswith("lavfi.r128.M=") and t is not None:
            v = _f(line.split("=", 1)[1])
            if v is not None and v > -70 and t >= 0.4:
                mmax = v if mmax is None else max(mmax, v)
        elif line.startswith("lavfi.r128.S=") and t is not None:
            v = _f(line.split("=", 1)[1])
            if abs(t - round(t)) < 0.051 and t >= 1.0:
                series.append({"t_s": round(t), "short_term_lufs": v if v is not None and v > -70 else None})
    dedup = {}
    for s in series:
        dedup.setdefault(s["t_s"], s)
    return list(dedup.values()), mmax


def measure(video: str, silence_db: float = -50.0, silence_min_s: float = 0.3, info: dict | None = None) -> dict:
    info = info or media_info(video)
    if not info.get("has_audio"):
        return unavailable("no audio stream")
    af = (f"ebur128=peak=true:metadata=1,ametadata=mode=print:file=-,astats=metadata=0,"
          f"silencedetect=n={silence_db}dB:d={silence_min_s}")
    proc = run_cmd(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-loglevel", "info", "-i", video,
                    "-map", "0:a:0", "-vn", "-sn", "-af", af, "-f", "null", "-"], timeout=1800)
    err = proc.stderr.decode("utf-8", "replace")
    out = proc.stdout.decode("utf-8", "replace")
    series, mmax = parse_series(out)
    duration = info.get("duration_s")
    return {"status": "ok", **parse_summary(err), **parse_astats(err), "momentary_max_lufs": mmax,
            "short_term": series, "silence": parse_silence(err, duration),
            "params": {"silence_db": silence_db, "silence_min_s": silence_min_s}}


def run(video: str, **kw) -> dict:
    try:
        res = measure(video, **kw)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except RuntimeError as exc:
        return {"status": "error", "reason": str(exc)}
    if res.get("status") != "ok":
        return res
    return clean({**res, "module": IDENTITY, "version": VERSION, "tools": tool_versions(("ffmpeg",), ())}, nd=3)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--silence-db", type=float, default=-50.0)
    ap.add_argument("--silence-min", type=float, default=0.3)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = run(a.video, silence_db=a.silence_db, silence_min_s=a.silence_min)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
