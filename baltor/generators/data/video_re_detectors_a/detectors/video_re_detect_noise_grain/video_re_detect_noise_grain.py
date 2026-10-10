"""Luma noise level, grain size, and a synthetic-grain versus sensor-noise hint (video_re_detect_noise_grain).

Method: frames are decoded at native resolution (centre crop of at most 640 x 640 px; scaling would average the
noise away). Noise sigma uses Immerkaer's (1996) fast estimator: the mean absolute response to the 3x3 mask
[1 -2 1; -2 4 -2; 1 -2 1] times sqrt(pi/2)/6, computed only on homogeneous pixels (the 60% of pixels with the
lowest local gradient) so edges do not count as noise. The residual (frame minus a Gaussian blur of sigma 2 px)
gives a second, coarse-grain-inclusive level and the grain size: the full width at half maximum of its
autocorrelation (about 1 px for per-pixel noise, larger for clumped film-like grain). Hints:
* signal dependence: noise measured in intensity bins; a sigma ratio of at least 1.4 between the brightest and
  darkest populated bins suggests photon (sensor) noise;
* chroma noise: Immerkaer sigma of the colour-difference channels relative to luma (sensor noise is coloured;
  grain overlays are usually monochrome);
* temporal correlation of residuals between consecutive frames: a grain plate reused on every frame correlates
  (>= 0.5), real noise does not.
Hint: clean (sigma < 1.0/255), static-overlay, sensor-like (signal-dependent or chroma ratio >= 0.5),
synthetic-grain-like (signal-independent and monochrome), otherwise mixed.

Limits: denoised or heavily compressed video loses its noise (reads clean); texture finer than the blur scale
(foliage, fabric) inflates the estimates despite the homogeneity mask; compression can make reused grain look
less correlated; the hint is evidence for an analyst, not a classification of the camera.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_noise_grain"
VERSION = "1.0.0"
DEFAULTS = {"homogeneous_share": 0.6, "clean_sigma": 1.0, "signal_dep_ratio": 1.4, "chroma_ratio": 0.5,
            "static_corr": 0.5, "residual_sigma": 2.0, "bins": 6}
DECODE = {"width": 0, "fps": 1.0, "max_frames": 12, "crop": [640, 640], "crop_align": 2}
_N = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)


def immerkaer_map(g) -> np.ndarray:
    g = np.asarray(g, dtype=np.float32)
    out = np.zeros((g.shape[0] - 2, g.shape[1] - 2), np.float32)
    for dy in range(3):
        for dx in range(3):
            out += _N[dy, dx] * g[dy:dy + out.shape[0], dx:dx + out.shape[1]]
    return np.abs(out)


def homogeneous_mask(g, share: float) -> np.ndarray:
    gm = core.grad_mag(core.blur(g, 1.0))[1:-1, 1:-1]
    return gm <= np.quantile(gm, share)


def sigma_estimate(g, mask) -> float:
    resp = immerkaer_map(g)
    if mask.sum() < 50:
        return float("nan")
    return float(np.sqrt(np.pi / 2) / 6.0 * resp[mask].mean())


def grain_size(residual) -> float:
    r = np.asarray(residual, dtype=np.float64)
    r = r - r.mean()
    F = np.fft.fft2(r)
    acf = np.fft.ifft2(np.abs(F) ** 2).real
    acf /= acf[0, 0] if acf[0, 0] > 0 else 1.0
    prof = 0.5 * (acf[0, :12] + acf[:12, 0])
    below = np.flatnonzero(prof < 0.5)
    if not len(below):
        return 24.0
    i = int(below[0])
    lag = i - 1 + (prof[i - 1] - 0.5) / max(1e-9, prof[i - 1] - prof[i])
    return float(2 * lag)


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    f = np.asarray(frames, dtype=np.float32)
    n = len(f)
    Y = core.luma(f)
    cb = f[..., 2] - Y
    cr = f[..., 0] - Y
    sig, res_sig, sizes, chroma, bins_all = [], [], [], [], []
    residuals = []
    for i in range(n):
        m = homogeneous_mask(Y[i], p["homogeneous_share"])
        s = sigma_estimate(Y[i], m)
        sig.append(s)
        res = Y[i] - core.blur(Y[i], p["residual_sigma"])
        residuals.append(res)
        inner = res[1:-1, 1:-1][m]
        res_sig.append(float(inner.std()) if inner.size else float("nan"))
        sizes.append(grain_size(res))
        sc = 0.5 * (sigma_estimate(cb[i], m) + sigma_estimate(cr[i], m))
        chroma.append(sc / s if s > 1e-3 else float("nan"))
        smooth = core.blur(Y[i], p["residual_sigma"])[1:-1, 1:-1]
        resp = immerkaer_map(Y[i])
        edges = np.quantile(smooth[m], np.linspace(0, 1, int(p["bins"]) + 1)) if m.sum() > 100 else None
        if edges is not None:
            for k in range(int(p["bins"])):
                sel = m & (smooth >= edges[k]) & (smooth <= edges[k + 1])
                if sel.sum() >= 50:
                    bins_all.append((float(smooth[sel].mean()), float(np.sqrt(np.pi / 2) / 6 * resp[sel].mean())))
    sigma = float(np.nanmedian(sig))
    corr = None
    if n >= 2:
        cs = []
        for a, b in zip(residuals[:-1], residuals[1:]):
            if a.std() > 1e-3 and b.std() > 1e-3:
                cs.append(float(np.corrcoef(a.ravel(), b.ravel())[0, 1]))
        corr = float(np.median(cs)) if cs else None
    sd_ratio = None
    if len(bins_all) >= 4:
        arr = np.array(sorted(bins_all))
        q = max(1, len(arr) // 4)
        lo, hi = arr[:q, 1].mean(), arr[-q:, 1].mean()
        sd_ratio = float(hi / lo) if lo > 1e-3 else None
    chroma_ratio = float(np.nanmedian(chroma)) if np.isfinite(np.nanmedian(chroma)) else None
    if sigma < p["clean_sigma"]:
        hint = "clean"
    elif corr is not None and corr >= p["static_corr"]:
        hint = "static-overlay"
    elif (sd_ratio is not None and sd_ratio >= p["signal_dep_ratio"]) or (chroma_ratio is not None and chroma_ratio >= p["chroma_ratio"]):
        hint = "sensor-like"
    elif sd_ratio is not None and chroma_ratio is not None:
        hint = "synthetic-grain-like"
    else:
        hint = "mixed"
    payload = {
        "noise_sigma": round(sigma, 4),
        "residual_sigma": round(float(np.nanmedian(res_sig)), 4),
        "grain_size_px": round(float(np.median(sizes)), 3),
        "signal_dependence_ratio": None if sd_ratio is None else round(sd_ratio, 4),
        "chroma_luma_ratio": None if chroma_ratio is None else round(chroma_ratio, 4),
        "temporal_correlation": None if corr is None else round(corr, 4),
        "hint": hint,
        "native_pixels": core.scale_of(info) == 1.0,
        "frames_analysed": int(n),
    }
    t = np.asarray(times, dtype=np.float64)
    results = [{"t_start_s": float(t[0]), "t_end_s": float(t[-1]), "label": hint, "value": payload["noise_sigma"],
                "confidence": 0.7 if payload["native_pixels"] else 0.35,
                "evidence": f"Immerkaer sigma {sigma:.2f}/255, grain FWHM {payload['grain_size_px']} px, signal dependence "
                            f"{payload['signal_dependence_ratio']}, chroma/luma {payload['chroma_luma_ratio']}, "
                            f"frame-to-frame residual correlation {payload['temporal_correlation']}"}]
    errors = [] if payload["native_pixels"] else ["frames were scaled: noise is averaged down"]
    return {"status": "ok" if not errors else "partial", "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
