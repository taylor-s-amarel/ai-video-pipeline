"""Interlacing: combing artefacts and field order (video_re_detect_interlacing).

Method: frames are decoded at native resolution (a centre crop of at most 720 x 480 px with even offsets, so field
parity is kept; no scaling, which would destroy combing). On pixels that move (|frame - previous| >= 6/255),
the inter-field second difference |2I(y) - I(y-1) - I(y+1)| is compared with the intra-field one
|2I(y) - I(y-2) - I(y+2)|. Progressive pictures are smooth, so the first is the smaller; woven fields of a moving
scene make it larger. A frame is combed when the ratio of their sums is >= 1.3. Field order is tested on the
fields themselves: with top field first, the bottom field of frame n is half a frame from the top field of frame
n+1 and the opposite pairing is one and a half frames apart, so mean |B(n) - T(n+1)| (bottom field resampled to
top-field lines, both fields blurred with sigma 2 px so the difference keeps growing with displacement) is the
smaller one; with bottom field first it is the reverse (decision margin 15%).
A combed share of 0.3-0.55 with two combed frames in every five is reported as telecine-like (3:2 pulldown).
The command line also runs ffmpeg's idet filter and reports its multi-frame counts, and ffprobe's field_order.

Limits: still or vertically uniform content shows no combing either way (frames without motion are not
counted); deinterlaced-then-encoded video is progressive here even if it was shot interlaced; scaled interlaced
video loses its combing pattern.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_interlacing"
VERSION = "1.0.0"
DEFAULTS = {"motion_thr": 6.0, "min_moving_share": 0.01, "comb_ratio": 1.3, "interlaced_share": 0.3,
            "order_margin": 0.15, "field_blur": 2.0, "idet_frames": 300}
DECODE = {"width": 0, "fps": 0, "max_frames": 120, "crop": [720, 480], "crop_align": 4}


def comb_scores(gray, p) -> list[float | None]:
    g = np.asarray(gray, dtype=np.float32)
    out: list[float | None] = [None]
    for i in range(1, len(g)):
        cur = g[i]
        moving = np.abs(cur - g[i - 1])[2:-2] >= p["motion_thr"]
        if moving.mean() < p["min_moving_share"]:
            out.append(None)
            continue
        inter = np.abs(2 * cur[2:-2] - cur[1:-3] - cur[3:-1])
        intra = np.abs(2 * cur[2:-2] - cur[:-4] - cur[4:])
        out.append(float(inter[moving].sum() / max(1e-6, intra[moving].sum())))
    return out


def field_order(gray, p) -> tuple[str, dict | None]:
    g = np.asarray(gray, dtype=np.float32)
    if len(g) < 3:
        return "unknown", None
    h = g.shape[1] - g.shape[1] % 2
    top, bot = g[:, 0:h:2], g[:, 1:h:2]
    if p["field_blur"] > 0:  # low-pass so the difference keeps growing with displacement
        top, bot = core.blur(top, p["field_blur"]), core.blur(bot, p["field_blur"])
    # bottom field lines sit at 2k+1; resample to top-field positions 2k with the mean of lines 2k-1 and 2k+1
    bot_at_top = np.concatenate([bot[:, :1], 0.5 * (bot[:, :-1] + bot[:, 1:])], axis=1)
    d_tff = float(np.mean(np.abs(bot_at_top[:-1] - top[1:])))
    d_bff = float(np.mean(np.abs(top[:-1] - bot_at_top[1:])))
    costs = {"tff": round(d_tff, 4), "bff": round(d_bff, 4)}
    if d_tff < (1 - p["order_margin"]) * d_bff:
        return "tff", costs
    if d_bff < (1 - p["order_margin"]) * d_tff:
        return "bff", costs
    return "unknown", costs


def run_idet(path: str, frames: int) -> dict | None:
    exe = shutil.which("ffmpeg")
    if not exe:
        return None
    proc = subprocess.run([exe, "-hide_banner", "-nostats", "-i", path, "-vf", "idet", "-frames:v", str(frames),
                           "-an", "-f", "null", "-"], capture_output=True, text=True, timeout=600)
    m = re.search(r"Multi frame detection:\s*TFF:\s*(\d+)\s*BFF:\s*(\d+)\s*Progressive:\s*(\d+)\s*Undetermined:\s*(\d+)",
                  proc.stderr)
    if not m:
        return None
    return dict(zip(("tff", "bff", "progressive", "undetermined"), (int(v) for v in m.groups())))


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    g = core.gray_frames(frames)
    n = len(g)
    t = np.asarray(times, dtype=np.float64)
    scores = comb_scores(g, p)
    valid = [s for s in scores if s is not None]
    combed = [s is not None and s >= p["comb_ratio"] for s in scores]
    share = (sum(combed) / len(valid)) if valid else None
    interlaced = bool(share is not None and share >= p["interlaced_share"])
    order, costs = field_order(g, p) if interlaced else ("progressive" if valid else "unknown", None)
    telecine = False
    if share is not None and 0.3 <= share <= 0.55 and len(combed) >= 10:
        flags = np.array(combed[1:], dtype=int)
        per5 = [flags[i:i + 5].sum() for i in range(0, len(flags) - 4, 5)]
        telecine = bool(per5) and np.mean(np.array(per5) == 2) >= 0.8
    idet = None
    tools = {}
    if params.get("_video_path"):
        idet = run_idet(params["_video_path"], int(p["idet_frames"]))
        if idet is not None:
            tools["ffmpeg_idet"] = "ffmpeg idet filter"
    payload = {
        "interlaced": interlaced,
        "field_order": order,
        "telecine_like": telecine,
        "combed_frame_ratio": None if share is None else round(share, 4),
        "comb_score_median": None if not valid else round(float(np.median(valid)), 4),
        "moving_frames": len(valid),
        "field_order_costs": costs,
        "metadata_field_order": info.get("field_order"),
        "idet": idet,
        "frames_analysed": int(n),
    }
    label = ("telecine-like" if telecine else "interlaced") if interlaced else ("progressive" if valid else "undetermined")
    results = [{"t_start_s": float(t[0]), "t_end_s": float(t[-1]), "label": label, "value": order,
                "confidence": 0.85 if valid and len(valid) >= 5 else 0.4,
                "evidence": f"{sum(combed)} of {len(valid)} moving frames combed (ratio >= {p['comb_ratio']}); "
                            f"field costs {costs}; idet {idet}; metadata {info.get('field_order')}"}]
    errors = [] if valid else ["no moving frames: combing cannot be measured"]
    return {"status": "ok" if valid else "partial", "results": results, "payload": payload, "errors": errors,
            "tools": tools}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
