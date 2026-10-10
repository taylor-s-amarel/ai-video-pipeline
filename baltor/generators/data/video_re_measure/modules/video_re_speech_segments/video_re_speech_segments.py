"""Find where someone (probably) speaks: a transparent energy/spectrum voice-activity heuristic.

Usage:
    python video_re_speech_segments.py video.mp4 [--method energy|silencedetect] [--out speech.json]

Method 'energy' (default, numpy only), on mono 16 kHz audio in 25 ms frames every 10 ms:

1. frame level in dBFS, the share of energy in the 100-4000 Hz voice band, and spectral flatness
   inside that band (voiced speech is harmonic, so its flatness is low);
2. the noise floor is the 10th percentile of frame levels; a frame is active when it is at least
   ``margin_db`` (10 dB) above the floor and above ``abs_floor_db`` (-55 dBFS), with at least 50% of
   its energy in the voice band and band flatness under 0.6;
3. gaps shorter than ``merge_gap_s`` (0.3 s) are bridged, segments shorter than ``min_segment_s``
   (0.2 s) dropped, and each segment padded by 50 ms.

Each segment also gets ``syllabic_modulation`` (dB): how much its voice-band energy rises and falls
at 2-8 Hz, the syllable rate of speech (measured without the segment's first and last 100 ms).
Speech is typically well above 3 dB; a sustained sound (a held music note) stays near 1 dB or less.
It is reported, not used to filter, because sung vocals and rhythmic music also modulate.

Method 'silencedetect' inverts ffmpeg's silencedetect (``-45 dB``, 0.3 s), which only says "not
silent".

Limits: music beds under narration usually merge into one long active region; whispering and
distant speech can be missed. A neural VAD (e.g. Silero) is more accurate when available; this
module keeps the evidence pipeline dependency-free.
"""

from __future__ import annotations

import argparse
import re

import numpy as np

from video_re_common import (ToolMissing, clean, dump_json, frame_signal, media_info, read_audio, run as run_cmd,
                             unavailable)

IDENTITY = "video_re_speech_segments"
VERSION = "1.0.0"
SR = 16000
DEFAULTS = {"margin_db": 10.0, "abs_floor_db": -55.0, "band_ratio": 0.5, "max_flatness": 0.6,
            "merge_gap_s": 0.3, "min_segment_s": 0.2, "pad_s": 0.05}


def frame_features(x: np.ndarray, sr: int = SR, frame_s: float = 0.025, hop_s: float = 0.010) -> dict:
    n, hop = int(frame_s * sr), int(hop_s * sr)
    frames = frame_signal(x, n, hop) * np.hanning(n)
    nfft = 1 << (n - 1).bit_length()
    spec = np.abs(np.fft.rfft(frames, nfft)) ** 2 + 1e-12
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    band = (freqs >= 100) & (freqs <= 4000)
    total = spec.sum(axis=1)
    bspec = spec[:, band]
    level = 10 * np.log10(np.mean((frame_signal(x, n, hop)) ** 2, axis=1) + 1e-12)
    flat = np.exp(np.mean(np.log(bspec), axis=1)) / np.mean(bspec, axis=1)
    return {"t": np.arange(len(frames)) * hop_s, "level_db": level, "band_ratio": bspec.sum(axis=1) / total,
            "flatness": flat, "band_energy": bspec.sum(axis=1), "hop_s": hop_s}


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    edges = np.diff(np.r_[0, mask.astype(int), 0])
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def syllabic_modulation(env: np.ndarray, rate: float) -> float | None:
    """Standard deviation, in dB, of the energy envelope after band-passing it to 2-8 Hz.

    Speech goes up and down with every syllable (typically well over 3 dB); a held note or steady
    noise stays within about 1 dB."""
    if len(env) < int(rate * 0.5):
        return None
    e = 10 * np.log10(env + 1e-12)
    e = e - e.mean()
    spec = np.fft.rfft(e)
    f = np.fft.rfftfreq(len(e), 1 / rate)
    spec[(f < 2) | (f > 8)] = 0
    return float(np.fft.irfft(spec, len(e)).std())


def segments_from_audio(x: np.ndarray, sr: int = SR, **params) -> dict:
    p = {**DEFAULTS, **{k: v for k, v in params.items() if v is not None}}
    if len(x) == 0:
        return {"segments": [], "speech_ratio": None, "noise_floor_db": None, "params": p}
    f = frame_features(x, sr)
    floor = float(np.percentile(f["level_db"], 10))
    active = ((f["level_db"] >= max(floor + p["margin_db"], p["abs_floor_db"]))
              & (f["band_ratio"] >= p["band_ratio"]) & (f["flatness"] <= p["max_flatness"]))
    hop = f["hop_s"]
    gap = int(round(p["merge_gap_s"] / hop))
    runs = _runs(active)
    merged: list[list[int]] = []
    for a, b in runs:
        if merged and a - merged[-1][1] <= gap:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    duration = len(x) / sr
    trim = int(round(0.1 / hop))  # leave onsets/offsets out of the modulation estimate
    segs = []
    for a, b in merged:
        if (b - a) * hop < p["min_segment_s"]:
            continue
        s, e = max(0.0, a * hop - p["pad_s"]), min(duration, b * hop + 0.025 + p["pad_s"])
        segs.append({"start_s": s, "end_s": e,
                     "syllabic_modulation": syllabic_modulation(f["band_energy"][a + trim:b - trim] if b - a > 4 * trim
                                                                else f["band_energy"][a:b], 1 / hop),
                     "mean_level_db": float(f["level_db"][a:b].mean())})
    speech = sum(s["end_s"] - s["start_s"] for s in segs)
    return {"segments": segs, "speech_ratio": speech / duration if duration else None, "speech_s": speech,
            "noise_floor_db": floor, "params": p}


def segments_silencedetect(video: str, noise_db: float = -45.0, min_silence_s: float = 0.3,
                           duration: float | None = None) -> dict:
    proc = run_cmd(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", video, "-map", "0:a:0", "-vn",
                    "-af", f"silencedetect=n={noise_db}dB:d={min_silence_s}", "-f", "null", "-"], timeout=1800)
    err = proc.stderr.decode("utf-8", "replace")
    starts = [float(v) for v in re.findall(r"silence_start:\s*(-?[\d.]+)", err)]
    ends = [float(v) for v in re.findall(r"silence_end:\s*(-?[\d.]+)", err)]
    silences = [(max(0.0, s), ends[i] if i < len(ends) else duration) for i, s in enumerate(starts)]
    segs, t = [], 0.0
    for s, e in silences:
        if s > t:
            segs.append({"start_s": t, "end_s": s})
        t = e if e is not None else t
    if duration and duration > t:
        segs.append({"start_s": t, "end_s": duration})
    speech = sum(s["end_s"] - s["start_s"] for s in segs)
    return {"segments": segs, "speech_ratio": speech / duration if duration else None, "speech_s": speech,
            "params": {"noise_db": noise_db, "min_silence_s": min_silence_s}}


def run(video: str, method: str = "energy", **params) -> dict:
    try:
        info = media_info(video)
        if not info.get("has_audio"):
            return unavailable("no audio stream")
        if method == "silencedetect":
            res = segments_silencedetect(video, duration=info.get("duration_s"))
        else:
            res = segments_from_audio(read_audio(video, SR), SR, **params)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except RuntimeError as exc:
        return {"status": "error", "reason": str(exc)}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, "method": method, **res}, nd=3)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--method", choices=["energy", "silencedetect"], default="energy")
    ap.add_argument("--margin-db", type=float, default=DEFAULTS["margin_db"])
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = run(a.video, a.method, margin_db=a.margin_db) if a.method == "energy" else run(a.video, a.method)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
