"""Content aspect inside the frame and the reframing method: fit with bars, blur-pad, crop-zoom or full frame
(video_re_detect_aspect_reframe).

Method: the content rectangle comes from the edge-bar scan shared with the letterbox detector (solid bars,
blurred-fill bars, static textured fills). The method is then decided from evidence:
* fit: solid bars around the content;
* blur-pad: blurred-fill bars; the fill is compared with a blurred, stretched copy of the content itself
  (Pearson correlation of low-passed luma); a high value means the fill is the same footage blurred;
* static-pad: a non-moving textured fill (a still background graphic);
* crop-zoom: no bars but the content is upscaled (spectral cut-off; see video_re_detect_true_resolution),
  which is what cropping a wider source and scaling it up to fill the frame leaves behind;
* full-frame: no bars and native detail (native framing, or a crop of a higher-resolution source; pixels alone
  cannot tell those apart).
The content aspect is matched to common ratios within 3%.

Limits: the upscale test needs native-resolution pixels; the command line decodes a second, native centre crop
for it. Footage that was already soft looks upscaled. A crop of a higher-resolution source is indistinguishable
from native framing.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_aspect_reframe"
VERSION = "1.0.0"
DEFAULTS = {"tol": 12.0, "min_bar_px": 2, "same_footage_corr": 0.5, "zoom_factor": 1.25, "ratio_tol": 0.03}
DECODE = {"width": 480, "fps": 1.0, "max_frames": 60}
RATIOS = [("9:16", 9 / 16), ("2:3", 2 / 3), ("3:4", 3 / 4), ("4:5", 4 / 5), ("1:1", 1.0), ("5:4", 5 / 4),
          ("4:3", 4 / 3), ("3:2", 3 / 2), ("16:10", 16 / 10), ("16:9", 16 / 9), ("1.85:1", 1.85), ("2:1", 2.0),
          ("2.39:1", 2.39)]


def name_ratio(r: float, tol: float = 0.03) -> str:
    best = min(RATIOS, key=lambda kv: abs(np.log(r / kv[1])))
    return best[0] if abs(np.log(r / best[1])) <= tol else "custom"


def fill_correlation(frames, rect) -> float | None:
    """Correlation between fill pixels and a blurred copy of the content stretched to the full frame."""
    f = np.asarray(frames, dtype=np.float32)
    n, h, w = f.shape[:3]
    x, y, cw, ch = rect
    if cw < 8 or ch < 8:
        return None
    fill = np.ones((h, w), bool)
    fill[y:y + ch, x:x + cw] = False
    if fill.sum() < 50:
        return None
    a, b = [], []
    for fr in f[: min(n, 12)]:
        g = core.luma(fr)
        content = g[y:y + ch, x:x + cw]
        # cover-fit the content to the frame (scale until it fills) and blur both
        s = max(w / cw, h / ch)
        big = core.resize_bilinear(content, int(round(ch * s)), int(round(cw * s)))
        oy, ox = (big.shape[0] - h) // 2, (big.shape[1] - w) // 2
        big = big[oy:oy + h, ox:ox + w]
        a.append(core.blur(big, 6)[fill])
        b.append(core.blur(g, 6)[fill])
    a, b = np.concatenate(a), np.concatenate(b)
    if a.std() < 1e-3 or b.std() < 1e-3:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def native_upscale_factor(frames, info, params) -> float | None:
    if core.scale_of(info) <= 1.0:
        return core.upscale_factor_estimate(core.gray_frames(frames))
    path = params.get("_video_path")
    if not path:
        return None
    nat, _, _ = core.decode_video(path, info, width=None, fps=0.5, max_frames=4, crop=(1024, 1024))
    return core.upscale_factor_estimate(core.gray_frames(nat))


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    f = np.asarray(frames)
    n, h, w = f.shape[:3]
    scale = core.scale_of(info)
    bars = core.scan_edge_bars(f, tol=p["tol"])
    use = {s: (b if b["px"] >= p["min_bar_px"] else {**b, "px": 0, "style": "none"}) for s, b in bars.items()}
    rect = core.content_rect_from_bars(use, h, w)
    styles = {b["style"] for b in use.values() if b["px"] > 0}
    errors, fill, factor = [], None, None
    if not styles:
        try:
            factor = native_upscale_factor(f, info, p)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"native decode for the zoom test failed: {exc}")
        if factor is None:
            method = "full-frame"
            errors.append("no native-resolution texture to test for crop-zoom")
        else:
            method = "crop-zoom" if factor >= p["zoom_factor"] else "full-frame"
    elif "solid" in styles:
        method = "fit"
    elif "blurred-fill" in styles:
        corr = fill_correlation(f, rect)
        fill = {"style": "blurred-fill", "same_footage_corr": None if corr is None else round(corr, 3)}
        method = "blur-pad"
    else:
        method = "static-pad"
        fill = {"style": "static-texture", "same_footage_corr": None}
    cr = rect[2] / rect[3] if rect[3] else None
    payload = {
        "frame_aspect": name_ratio(w / h, p["ratio_tol"]), "frame_ratio": round(w / h, 4),
        "content_aspect": name_ratio(cr, p["ratio_tol"]) if cr else None,
        "content_ratio": round(cr, 4) if cr else None,
        "content_rect": {"x": int(round(rect[0] * scale)), "y": int(round(rect[1] * scale)),
                         "w": int(round(rect[2] * scale)), "h": int(round(rect[3] * scale))},
        "method": method,
        "fill": fill,
        "upscale_factor": None if factor is None else round(factor, 3),
        "frames_analysed": int(n),
    }
    conf = {"fit": 0.9, "blur-pad": 0.8, "static-pad": 0.6, "crop-zoom": 0.6, "full-frame": 0.5}[method]
    if method == "blur-pad" and fill["same_footage_corr"] is not None and fill["same_footage_corr"] < p["same_footage_corr"]:
        conf = 0.6
    results = [{"t_start_s": float(times[0]), "t_end_s": float(times[-1]), "label": method,
                "value": payload["content_aspect"], "confidence": conf,
                "bbox": [rect[0], rect[1], rect[2], rect[3]],
                "evidence": f"content {rect[2]}x{rect[3]} analysis px in {w}x{h}; bars {[s for s in use if use[s]['px']]}; "
                            f"upscale factor {payload['upscale_factor']}"}]
    return {"status": "ok" if not errors else "partial", "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
