"""Effective detail resolution versus container resolution: upscale detection from the high-frequency
spectrum (video_re_detect_true_resolution).

Method: frames are decoded at native resolution (a centre crop of at most 1280 x 1280 px, no scaling). For each
axis the mean power spectrum of Hann-windowed rows (horizontal) and columns (vertical) is computed, per 128 px
tile and over all textured tiles. A power law fitted on 0.015-0.07 cycles/px predicts what a natively sharp image
would hold at higher frequencies. The cut-off is the lowest frequency above which at least 90% of the smoothed
spectrum lies 10 dB or more below that prediction (a missing band). An image upscaled by s has nothing above
0.5/s cycles/px, so upscale_factor = 0.5 / cut-off and effective size = container / factor. Tiles are
classified individually too, which reveals native-resolution overlays (captions, graphics) over upscaled footage
(verdict "mixed").

Limits: calibrated on 1/f-spectrum test images resampled with bicubic and Lanczos (median error about 5%,
90th percentile about 16%); bilinear upscales leak imaged energy above the cut-off and are estimated less
precisely. Heavy denoising, defocus or low-bitrate encoding also remove the top band and read as a lower
effective resolution, which is what the number means: detail actually present, not how it was lost.
Sharpening halos after upscaling can hide a cut-off. Flat tiles (sky, bars) are skipped.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_true_resolution"
VERSION = "1.0.0"
DEFAULTS = {"tile": 128, "fit_band": [0.015, 0.07], "drop_db": 10.0, "band_frac": 0.9, "min_tile_std": 6.0,
            "upscaled_factor": 1.15, "mixed_share": [0.25, 0.75]}
DECODE = {"width": 0, "fps": 0.5, "max_frames": 8, "crop": [1280, 1280]}


axis_spectrum = core.axis_spectrum
cutoff = core.spectral_cutoff


def estimate(gray_frames, **params) -> dict:
    """Upscale estimate for (N, H, W) grey frames at native resolution."""
    p = {**DEFAULTS, **params}
    g = np.asarray(gray_frames, dtype=np.float32)
    if g.ndim == 2:
        g = g[None]
    n, h, w = g.shape
    t = int(p["tile"])
    tiles = []
    for y in range(0, h - t + 1, t):
        for x in range(0, w - t + 1, t):
            block = g[:, y:y + t, x:x + t]
            if block.std(axis=(1, 2)).mean() >= p["min_tile_std"]:
                tiles.append(block)
    out = {"tiles_total": (h // t) * (w // t), "tiles_textured": len(tiles)}
    if not tiles:
        out.update({"fx": None, "fy": None, "tile_factors": []})
        return out
    stack = np.stack(tiles)  # (T, N, t, t)
    fx_f, Px = axis_spectrum(stack.reshape(-1, t, t), -1)
    fy_f, Py = axis_spectrum(stack.reshape(-1, t, t), -2)
    cx, _ = cutoff(fx_f, Px, p["fit_band"], p["drop_db"], p["band_frac"])
    cy, _ = cutoff(fy_f, Py, p["fit_band"], p["drop_db"], p["band_frac"])
    factors = []
    for blk in tiles:
        a, Pa = axis_spectrum(blk, -1)
        b, Pb = axis_spectrum(blk, -2)
        tx, _ = cutoff(a, Pa, p["fit_band"], p["drop_db"], p["band_frac"])
        ty, _ = cutoff(b, Pb, p["fit_band"], p["drop_db"], p["band_frac"])
        factors.append(float(np.sqrt((0.5 / tx) * (0.5 / ty))))
    out.update({"fx": cx, "fy": cy, "tile_factors": factors})
    return out


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    g = core.gray_frames(frames)
    n, h, w = g.shape
    est = estimate(g, **p)
    cw = int(info.get("width") or w)
    ch = int(info.get("height") or h)
    if est["fx"] is None or est["tiles_textured"] < 2:
        payload = {"container": {"w": cw, "h": ch}, "effective": None, "upscale_factor": None,
                   "per_axis": None, "cutoff_cycles_per_px": None, "verdict": "insufficient-detail",
                   "tiles": {"analysed": est["tiles_textured"], "total": est["tiles_total"], "upscaled_share": None},
                   "frames_analysed": int(n)}
        return {"status": "partial", "results": [{"label": "insufficient-detail", "confidence": 0.3,
                                                  "evidence": f"{est['tiles_textured']} textured {p['tile']} px tile(s)"}],
                "payload": payload, "errors": ["too few textured tiles for a spectral estimate"]}
    kx, ky = 0.5 / est["fx"], 0.5 / est["fy"]
    factor = float(np.sqrt(kx * ky))
    tf = np.array(est["tile_factors"])
    share = float(np.mean(tf >= p["upscaled_factor"]))
    if factor < p["upscaled_factor"] and share < p["mixed_share"][0]:
        verdict = "native"
    elif p["mixed_share"][0] <= share <= p["mixed_share"][1]:
        verdict = "mixed"
    else:
        verdict = "upscaled" if factor >= p["upscaled_factor"] else "native"
    payload = {
        "container": {"w": cw, "h": ch},
        "effective": {"w": int(round(cw / kx)), "h": int(round(ch / ky))},
        "upscale_factor": round(factor, 3),
        "per_axis": {"x": round(kx, 3), "y": round(ky, 3)},
        "cutoff_cycles_per_px": {"x": round(est["fx"], 4), "y": round(est["fy"], 4)},
        "verdict": verdict,
        "tiles": {"analysed": est["tiles_textured"], "total": est["tiles_total"], "upscaled_share": round(share, 3)},
        "frames_analysed": int(n),
    }
    conf = 0.75 if verdict in ("native", "upscaled") else 0.55
    results = [{"t_start_s": float(times[0]), "t_end_s": float(times[-1]), "label": verdict, "value": round(factor, 3),
                "confidence": conf,
                "evidence": f"spectral cut-off x={est['fx']:.3f} y={est['fy']:.3f} cycles/px over "
                            f"{est['tiles_textured']} textured tiles; {share:.0%} of tiles upscaled"}]
    return {"status": "ok", "results": results, "payload": payload, "errors": []}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
