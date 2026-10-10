"""Speaking rate of a narration: words per minute from a transcript, or a labelled syllable estimate.

Usage:
    python video_re_speech_rate.py --transcript transcript.json            # from video_re_transcribe_adapter
    python video_re_speech_rate.py video.mp4                                # syllable estimate from audio

Method 'transcript' (preferred) uses word time stamps:

* speech_wpm = words / speaking time, where speaking time runs from the first word's start to the
  last word's end minus pauses longer than ``long_pause_s`` (1.0 s): words per minute while talking
* overall_wpm = words / (last end - first start)
* articulation_wpm = words / sum of word durations
* pauses between words of at least ``pause_s`` (0.3 s): count, mean, longest, pause_ratio

Word times that were only spread evenly over subtitle lines (``estimated`` in the transcript) give
the same wpm but no real pause data; the result says so.

Method 'syllable-estimate' needs no transcript: syllable nuclei are counted as peaks of the
300-3000 Hz energy envelope (10 ms frames, 40 ms smoothing, at least 100 ms apart, at least 4 dB
above the surrounding dip and 12 dB above the noise floor) and

    speech_wpm ~= syllables per second of voiced time x 60 / 1.5

The 1.5 syllables per word is an assumption for English narration, so this is an estimate (expect
roughly +-25%) and is reported with method 'syllable-estimate' and confidence 0.4.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from video_re_common import ToolMissing, clean, dump_json, frame_signal, load_json, media_info, read_audio, unavailable

IDENTITY = "video_re_speech_rate"
VERSION = "1.0.0"
SYLLABLES_PER_WORD = 1.5  # assumption for English narration, see module docstring
SR = 16000


def from_words(words: list[dict], pause_s: float = 0.3, long_pause_s: float = 1.0) -> dict:
    words = sorted((w for w in words if w.get("end_s") is not None), key=lambda w: w["start_s"])
    if len(words) < 2:
        return {"speech_wpm": None, "method": "transcript", "reason": "fewer than two timed words"}
    first, last = words[0]["start_s"], words[-1]["end_s"]
    span = max(1e-6, last - first)
    gaps = np.array([max(0.0, b["start_s"] - a["end_s"]) for a, b in zip(words, words[1:])])
    long_gaps = gaps[gaps > long_pause_s].sum()
    speaking = max(1e-6, span - long_gaps)
    dur = sum(max(0.0, w["end_s"] - w["start_s"]) for w in words)
    estimated = any(w.get("estimated") for w in words)
    pauses = gaps[gaps >= pause_s]
    return {
        "speech_wpm": len(words) * 60.0 / speaking,
        "overall_wpm": len(words) * 60.0 / span,
        "articulation_wpm": len(words) * 60.0 / dur if dur > 0 and not estimated else None,
        "words": len(words), "speaking_time_s": speaking, "span_s": span,
        "pauses": None if estimated else {"count": int(len(pauses)), "mean_s": float(pauses.mean()) if len(pauses) else 0.0,
                                          "longest_s": float(gaps.max()) if len(gaps) else 0.0,
                                          "pause_ratio": float(gaps[gaps >= pause_s].sum() / span)},
        "method": "transcript", "confidence": 0.6 if estimated else 0.9,
        "note": "word times were spread evenly over subtitle lines" if estimated else None,
    }


def syllable_nuclei(x: np.ndarray, sr: int = SR, min_gap_s: float = 0.1, min_prom_db: float = 4.0,
                    floor_margin_db: float = 12.0) -> tuple[np.ndarray, float]:
    """(nucleus times in s, voiced time in s)."""
    n, hop = int(0.025 * sr), int(0.010 * sr)
    frames = frame_signal(np.asarray(x, dtype=np.float64), n, hop) * np.hanning(n)
    spec = np.abs(np.fft.rfft(frames, 512)) ** 2
    f = np.fft.rfftfreq(512, 1 / sr)
    env = spec[:, (f >= 300) & (f <= 3000)].sum(axis=1) + 1e-12
    k = np.ones(4) / 4.0
    db = 10 * np.log10(np.convolve(env, k, mode="same"))
    floor = np.percentile(db, 10)
    voiced = db >= floor + floor_margin_db
    gap = int(min_gap_s / 0.010)
    peaks = []
    for i in range(1, len(db) - 1):
        if not voiced[i] or db[i] < db[i - 1] or db[i] < db[i + 1]:
            continue
        lo, hi = max(0, i - gap), min(len(db), i + gap + 1)
        if db[i] < db[lo:hi].max():
            continue
        left = db[max(0, i - 3 * gap):i].min() if i > 0 else db[i]
        right = db[i + 1:i + 3 * gap + 1].min() if i + 1 < len(db) else db[i]
        if db[i] - max(left, right) < min_prom_db:
            continue
        if peaks and i - peaks[-1] < gap:
            continue
        peaks.append(i)
    return np.asarray(peaks) * 0.010, float(voiced.sum() * 0.010)


def from_audio(x: np.ndarray, sr: int = SR) -> dict:
    nuclei, voiced_s = syllable_nuclei(x, sr)
    if voiced_s < 1.0 or len(nuclei) < 3:
        return {"speech_wpm": None, "method": "syllable-estimate", "reason": "too little voiced audio"}
    # syllables per second over the voiced stretch from the first to the last nucleus
    span = max(1e-6, nuclei[-1] - nuclei[0])
    rate = (len(nuclei) - 1) / span
    return {"speech_wpm": rate * 60.0 / SYLLABLES_PER_WORD, "syllables_per_s": rate, "syllables": int(len(nuclei)),
            "voiced_s": voiced_s, "method": "syllable-estimate", "confidence": 0.4,
            "assumption": f"{SYLLABLES_PER_WORD} syllables per word (English narration)"}


def run(video: str | None = None, transcript: dict | None = None, **kw) -> dict:
    if transcript and transcript.get("words"):
        res = from_words(transcript["words"], **kw)
    elif video:
        try:
            if not media_info(video).get("has_audio"):
                return unavailable("no audio stream")
            res = from_audio(read_audio(video, SR), SR)
        except ToolMissing as exc:
            return unavailable(str(exc))
        except RuntimeError as exc:
            return {"status": "error", "reason": str(exc)}
    else:
        return unavailable("needs a transcript with word times or a video with audio")
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **res}, nd=3)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?")
    ap.add_argument("--transcript", help="video_re_transcribe_adapter JSON")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    tr = load_json(a.transcript) if a.transcript and Path(a.transcript).exists() else None
    res = run(a.video, tr)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
