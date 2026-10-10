"""Onsets, tempo and beat times of a soundtrack, numpy only (no librosa needed).

Usage:
    python video_re_onsets_beats.py video.mp4 [--out beats.json]

* Onset envelope: spectral flux. Mono audio at 22.05 kHz, centred STFT (1024-sample Hann window,
  256-sample hop = 11.6 ms), magnitudes summed into 40 log-spaced bands (60 Hz - 10 kHz), log
  compressed (log1p(100 x)), and the half-wave-rectified frame-to-frame increase summed over bands.
* Onsets: peaks of the normalised envelope that are the maximum within 30 ms before, exceed the
  local mean (100 ms either side) by ``delta`` (0.07) and come at least ``wait_s`` (50 ms) after
  the previous onset. Time = frame centre plus one hop: on sharp clicks the flux peak arrives one
  hop before the attack, so this correction centres the error on zero; soft attacks read later.
* Tempo: autocorrelation of the (lightly smoothed) onset envelope over 30-300 BPM, weighted by a log-normal prior
  centred on 120 BPM with a one-octave spread (the same idea librosa uses), parabolic refinement.
  ``tempo_confidence`` is the weighted autocorrelation peak relative to lag 0; tempo is null when
  there are fewer than 4 onsets or the confidence is under 0.05.
* Beats: dynamic-programming beat tracker (Ellis 2007, tightness 100) on the onset envelope,
  kept between the first and last onset (half a beat of margin).

Accuracy on synthetic clicks: onset times within 30 ms, tempo within 2 BPM (see the tests). Real
music with soft attacks, rubato or no percussion gives weaker results; octave errors (half or double
tempo) are the typical failure. Speech-only soundtracks produce onsets at syllables and usually no
stable tempo.
"""

from __future__ import annotations

import argparse

import numpy as np

from video_re_common import ToolMissing, clean, dump_json, frame_signal, media_info, read_audio, unavailable

IDENTITY = "video_re_onsets_beats"
VERSION = "1.0.0"
SR = 22050
N_FFT = 1024
HOP = 256
LATENCY_FRAMES = 1


def band_matrix(sr: int = SR, n_fft: int = N_FFT, n_bands: int = 40, fmin: float = 60.0,
                fmax: float = 10000.0) -> np.ndarray:
    freqs = np.fft.rfftfreq(n_fft, 1 / sr)
    edges = np.geomspace(fmin, min(fmax, sr / 2 - 1), n_bands + 1)
    m = np.zeros((n_bands, len(freqs)))
    for i in range(n_bands):
        sel = (freqs >= edges[i]) & (freqs < edges[i + 1])
        if not sel.any():
            sel[np.argmin(np.abs(freqs - (edges[i] + edges[i + 1]) / 2))] = True
        m[i, sel] = 1.0
    return m


def onset_envelope(x: np.ndarray, sr: int = SR) -> np.ndarray:
    x = np.pad(np.asarray(x, dtype=np.float64), (N_FFT // 2, N_FFT // 2))
    frames = frame_signal(x, N_FFT, HOP) * np.hanning(N_FFT)
    mag = np.abs(np.fft.rfft(frames, axis=1))
    bands = np.log1p(100.0 * (mag @ band_matrix(sr).T))
    flux = np.maximum(0.0, np.diff(bands, axis=0)).sum(axis=1)
    return np.r_[0.0, flux]


def pick_onsets(env: np.ndarray, sr: int = SR, delta: float = 0.07, wait_s: float = 0.05,
                pre_max_s: float = 0.03, avg_s: float = 0.10) -> np.ndarray:
    if env.max() <= 0:
        return np.array([], dtype=int)
    e = env / env.max()
    fr = sr / HOP
    pre_max, avg, wait = max(1, int(pre_max_s * fr)), max(1, int(avg_s * fr)), max(1, int(wait_s * fr))
    out, last = [], -10 ** 9
    for n in range(1, len(e)):
        lo = max(0, n - pre_max)
        if e[n] < e[lo:n + 2].max():
            continue
        local = e[max(0, n - avg):n + avg + 1].mean()
        if e[n] < local + delta:
            continue
        if n - last < wait:
            continue
        out.append(n)
        last = n
    return np.asarray(out, dtype=int)


def estimate_tempo(env: np.ndarray, sr: int = SR, start_bpm: float = 120.0, std_octaves: float = 1.0,
                   min_bpm: float = 30.0, max_bpm: float = 300.0) -> tuple[float | None, float]:
    fr = sr / HOP
    # smooth over about +-2 frames so a period that falls between two lags is not split in half
    kernel = np.array([1.0, 4.0, 6.0, 4.0, 1.0]) / 16.0
    e = np.convolve(np.convolve(env, kernel, mode="same"), kernel, mode="same")
    e = e - e.mean()
    if not np.any(e):
        return None, 0.0
    n = len(e)
    ac = np.fft.irfft(np.abs(np.fft.rfft(e, 2 * n)) ** 2)[:n]
    if ac[0] <= 0:
        return None, 0.0
    ac /= ac[0]
    lags = np.arange(n)
    with np.errstate(divide="ignore"):
        bpm = 60.0 * fr / np.maximum(lags, 1e-9)
    valid = (bpm >= min_bpm) & (bpm <= max_bpm) & (lags > 0)
    if not valid.any():
        return None, 0.0
    weight = np.exp(-0.5 * (np.log2(np.maximum(bpm, 1e-9) / start_bpm) / std_octaves) ** 2)
    score = np.where(valid, ac * weight, -np.inf)
    k = int(np.argmax(score))
    conf = float(ac[k])
    lag = float(k)
    if 1 <= k < n - 1 and np.isfinite(score[k - 1]) and np.isfinite(score[k + 1]):
        a, b, c = ac[k - 1], ac[k], ac[k + 1]
        den = a - 2 * b + c
        if abs(den) > 1e-12:
            lag = k + 0.5 * (a - c) / den
    return 60.0 * fr / lag, conf


def track_beats(env: np.ndarray, tempo_bpm: float, sr: int = SR, tightness: float = 100.0) -> np.ndarray:
    fr = sr / HOP
    period = 60.0 * fr / tempo_bpm
    e = env / (env.std() + 1e-9)
    n = len(e)
    score = e.copy()
    back = np.full(n, -1)
    lo_off, hi_off = int(round(period / 2)), int(round(2 * period))
    for t in range(n):
        lo, hi = max(0, t - hi_off), t - lo_off
        if hi <= lo:
            continue
        prev = np.arange(lo, hi)
        cand = score[prev] - tightness * (np.log((t - prev) / period)) ** 2
        j = int(np.argmax(cand))
        if cand[j] > 0:  # otherwise this frame starts a new beat sequence
            score[t] = e[t] + cand[j]
            back[t] = prev[j]
    # start from the best-scoring frame in the last period, then follow the back-pointers
    tail = slice(max(0, n - int(round(period))), n)
    t = int(np.arange(n)[tail][np.argmax(score[tail])])
    beats = []
    while t >= 0:
        beats.append(t)
        t = back[t]
    beats = np.array(beats[::-1], dtype=int)
    if len(beats) and e[beats[0]] < 0.1 * e.max():
        beats = beats[1:]
    return beats


def analyse_audio(x: np.ndarray, sr: int = SR, delta: float = 0.07) -> dict:
    env = onset_envelope(x, sr)
    fr = sr / HOP
    onsets = pick_onsets(env, sr, delta=delta)
    tempo, conf = (None, 0.0)
    beats = np.array([], dtype=int)
    if len(onsets) >= 4:
        tempo, conf = estimate_tempo(env, sr)
        if tempo is not None and conf >= 0.05:
            beats = track_beats(env, tempo, sr)
            half = 0.5 * 60.0 * fr / tempo  # keep beats where there is music: first to last onset
            beats = beats[(beats >= onsets[0] - half) & (beats <= onsets[-1] + half)]
        else:
            tempo = None
    ioi = np.diff(onsets) / fr if len(onsets) > 1 else np.array([])
    # flux peaks one hop before a sharp attack's start (calibrated on clicks); shift onsets back
    onset_t = np.clip((onsets + LATENCY_FRAMES) / fr, 0.0, None)
    return {"onsets_s": onset_t.tolist(), "tempo_bpm": tempo, "tempo_confidence": conf,
            "beats_s": np.clip((beats + LATENCY_FRAMES) / fr, 0.0, None).tolist(),
            "onset_rate_per_s": len(onsets) / (len(x) / sr) if len(x) else None,
            "median_ioi_s": float(np.median(ioi)) if len(ioi) else None,
            "params": {"sr": sr, "n_fft": N_FFT, "hop": HOP, "delta": delta}}


def run(video: str, delta: float = 0.07) -> dict:
    try:
        info = media_info(video)
        if not info.get("has_audio"):
            return unavailable("no audio stream")
        res = analyse_audio(read_audio(video, SR), SR, delta)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except RuntimeError as exc:
        return {"status": "error", "reason": str(exc)}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **res})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--delta", type=float, default=0.07, help="onset threshold above the local mean (0-1)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = run(a.video, a.delta)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
