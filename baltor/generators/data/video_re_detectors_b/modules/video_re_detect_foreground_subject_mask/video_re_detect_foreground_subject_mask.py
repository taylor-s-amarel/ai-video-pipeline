"""Locate the main subject region by colour saliency: size and position ratios per sample and per shot.

Method (sampled frames, default 2 fps, long side 256):

1. Saliency map: frequency-tuned colour saliency (Achanta et al. 2009) with a boundary prior. The
   frame is box-blurred (radius ``blur_r``) in CIE L*a*b*, and each pixel's saliency is its colour
   distance (Delta E 1976) from the reference background colour, taken as the median colour of a
   border band (``border_band`` of the width/height) rather than the frame mean, so a subject that
   fills much of the frame still stands out.
2. Pixels above ``thr_k`` x the mean saliency form the mask; the connected region with the largest
   saliency mass is the candidate subject. It is accepted when its mean saliency is at least
   ``min_delta_e`` and ``min_z`` standard deviations above the rest of the frame (texture blobs
   in a busy background score around 2-3).
3. Per shot: median box, area ratio and centre; framing (left/centre/right third) and a size class
   from the area ratio (``closeup_area`` and ``wide_area`` cut points, heuristic).

Presence and geometry only: no face detection, no recognition, no identity of any kind.
Limits: colour saliency is not semantics (a bright sign can outrank a person); subjects coloured
like their surroundings, subjects touching most of the frame border, and frames with several
equal subjects give no or low-confidence results.
"""

from __future__ import annotations

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_foreground_subject_mask"
VERSION = "1.0.0"
DEFAULTS = {
    "blur_r": 2,
    "border_band": 0.08,
    "thr_k": 2.0,
    "min_delta_e": 15.0,
    "min_z": 4.0,
    "closeup_area": 0.35,
    "wide_area": 0.08,
    "cut_threshold": 0.3,
}
PARAM_DOCS = {
    "blur_r": "box-blur radius before the colour-saliency distance (analysed px)",
    "border_band": "share of width/height whose median colour is the background reference",
    "thr_k": "mask threshold as a multiple of mean saliency (Achanta's adaptive threshold uses 2)",
    "min_delta_e": "smallest mean colour distance (Delta E) of an accepted subject",
    "min_z": "smallest (mean inside - mean outside) / std outside of an accepted subject",
    "closeup_area": "subject box area ratio at or above which the size class is close-up",
    "wide_area": "area ratio below which the size class is wide",
    "cut_threshold": "cut score for the built-in shot splitter",
}


def _norm(a: np.ndarray) -> np.ndarray:
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a)


def saliency(rgb: np.ndarray, p: dict) -> np.ndarray:
    lab = kit.rgb_to_lab(rgb)
    bl = np.stack([kit.box_mean(lab[..., c], int(p["blur_r"])) for c in range(3)], axis=-1)
    H, W = rgb.shape[:2]
    by, bx = max(1, int(H * p["border_band"])), max(1, int(W * p["border_band"]))
    border = np.concatenate([bl[:by].reshape(-1, 3), bl[-by:].reshape(-1, 3),
                             bl[:, :bx].reshape(-1, 3), bl[:, -bx:].reshape(-1, 3)])
    ref = np.median(border, axis=0)
    return np.sqrt(((bl - ref) ** 2).sum(axis=-1)).astype(np.float32)


def subject_in_frame(rgb: np.ndarray, p: dict) -> dict:
    sal = saliency(rgb, p)
    mask = sal > p["thr_k"] * max(float(sal.mean()), 1e-6)
    labels, comps = kit.components(mask)
    if not comps:
        return {"bbox": None, "delta_e": 0.0, "z": 0.0}
    mass = np.bincount(labels.ravel(), weights=sal.ravel(), minlength=len(comps) + 2)
    best = max(comps, key=lambda c: mass[c["label"]])
    inside = labels == best["label"]
    out = sal[~inside]
    de = float(sal[inside].mean())
    z = (de - float(out.mean())) / (float(out.std()) + 1e-6) if out.size else 0.0
    return {"bbox": best["bbox"], "delta_e": de, "z": z}


def framing_of(cx: float) -> str:
    return "left-third" if cx < 1 / 3 else ("right-third" if cx > 2 / 3 else "center")


def size_class(area: float, p: dict) -> str:
    return "close-up" if area >= p["closeup_area"] else ("wide" if area < p["wide_area"] else "medium")


def analyse(frames, fps, p, ctx):
    rgb = kit.as_rgb(np.asarray(frames))
    N, H, W = rgb.shape[:3]
    t0 = ctx["t0"]
    cuts = None if ctx.get("shots") else kit.detect_cuts(rgb, fps, abs_thr=p["cut_threshold"])
    ranges = kit.shot_ranges(N, fps, t0, cuts, ctx.get("shots"))
    samples, shots, results = [], [], []
    for k, (a, b) in enumerate(ranges):
        found = []
        for i in range(a, b):
            r = subject_in_frame(rgb[i], p)
            t = t0 + i / fps
            if r["bbox"] is None or r["delta_e"] < p["min_delta_e"] or r["z"] < p["min_z"]:
                samples.append({"t_s": t, "shot_index": k, "present": False, "bbox": None, "area_ratio": None,
                                "center_ratio": None, "delta_e": r["delta_e"], "separation_z": r["z"]})
                continue
            x, y, w, h = r["bbox"]
            rec = {"t_s": t, "shot_index": k, "present": True, "bbox": r["bbox"], "area_ratio": w * h / float(W * H),
                   "center_ratio": [(x + w / 2) / W, (y + h / 2) / H], "delta_e": r["delta_e"],
                   "separation_z": r["z"]}
            samples.append(rec)
            found.append(rec)
        shot = {"shot_index": k, "t_start_s": t0 + a / fps, "t_end_s": t0 + b / fps,
                "present_share": len(found) / max(1, b - a)}
        if found:
            bb = np.median(np.array([f["bbox"] for f in found], dtype=np.float64), axis=0)
            area = float(np.median([f["area_ratio"] for f in found]))
            cen = np.median(np.array([f["center_ratio"] for f in found]), axis=0)
            z = float(np.median([f["separation_z"] for f in found]))
            shot.update(bbox=bb.tolist(), bbox_ratio=kit.bbox_ratio(bb, W, H), area_ratio=area,
                        center_ratio=cen.tolist(), framing=framing_of(float(cen[0])), size_class=size_class(area, p),
                        separation_z=z)
            conf = float(np.clip((z - p["min_z"]) / 8.0 + 0.5, 0, 1)) * shot["present_share"]
            results.append(kit.result("main_subject", conf, t_start_s=shot["t_start_s"], t_end_s=shot["t_end_s"],
                                      bbox=bb.tolist(), value=shot["size_class"],
                                      evidence=f"salient region {area:.0%} of frame, {shot['framing']}, "
                                               f"separation {z:.1f} sd; presence only, no identity"))
        else:
            shot.update(bbox=None, bbox_ratio=None, area_ratio=None, center_ratio=None, framing=None,
                        size_class=None, separation_z=None)
        shots.append(shot)
    payload = {"identity_inference": "none", "samples": samples, "shots": shots}
    return {"status": "ok", "results": results, "payload": payload, "errors": []}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=256, fps=2.0, pix_fmt="rgb24",
                   description="Locate the main salient subject region: size and position ratios (presence only).")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W, 3) uint8 at ``fps``."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
