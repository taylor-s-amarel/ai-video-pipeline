"""Pick one sharp representative frame per shot and lay them out as contact sheets.

Usage:
    python video_re_keyframes_contact_sheet.py video.mp4 --shots shots.json --out-dir evidence/
    python video_re_keyframes_contact_sheet.py video.mp4 --out-dir evidence/   # detects shots via the sibling package

For every shot it decodes candidate frames at 25%, 50% and 75% of the shot (``--candidates 1`` uses
only the middle) and keeps the sharpest one (variance of a Laplacian on the grey image), which avoids
motion-blurred frames and dissolve frames. It writes:

* ``keyframes/shot_000.jpg`` ... (default 360 px wide)
* ``contact_sheet_01.jpg`` ... grids of thumbnails labelled "#index start_s (duration)"

The frames are local analysis artefacts so an analyst (human or model) can look at every shot. They
are copies of the source's pictures: keep them out of anything published and out of a format IR.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from video_re_common import (ToolMissing, clean, dump_json, import_sibling, load_json, media_info, read_frame_at,
                             shots_from_json, unavailable, whole_clip_shot)

IDENTITY = "video_re_keyframes_contact_sheet"
VERSION = "1.0.0"


def sharpness(grey: np.ndarray) -> float:
    g = grey.astype(np.float32)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())


def candidate_times(shot: dict, fps: float, n: int = 3) -> list[float]:
    a, b = float(shot["start_s"]), float(shot["end_s"])
    lo, hi = a + 1.0 / fps, max(a + 1.0 / fps, b - 1.0 / fps)
    if n <= 1 or hi - lo < 3.0 / fps:
        return [min(hi, max(lo, (a + b) / 2.0))]
    return [lo + (hi - lo) * f for f in (0.25, 0.5, 0.75)][:n]


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def contact_sheets(images: list[tuple[Image.Image, str]], out_dir: Path, cols: int = 5, thumb_w: int = 216,
                   per_sheet: int = 40) -> list[Path]:
    paths = []
    font = _font(14)
    for s in range(0, len(images), per_sheet):
        chunk = images[s:s + per_sheet]
        thumbs = []
        for img, label in chunk:
            th = img.copy()
            th.thumbnail((thumb_w, thumb_w * 4))
            thumbs.append((th, label))
        cell_h = max(t.height for t, _ in thumbs) + 22
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (thumb_w + 6) + 6, rows * (cell_h + 6) + 6), (24, 24, 28))
        draw = ImageDraw.Draw(sheet)
        for i, (th, label) in enumerate(thumbs):
            x = 6 + (i % cols) * (thumb_w + 6)
            y = 6 + (i // cols) * (cell_h + 6)
            sheet.paste(th, (x + (thumb_w - th.width) // 2, y))
            draw.text((x + 2, y + cell_h - 20), label, fill=(240, 240, 240), font=font)
        p = out_dir / f"contact_sheet_{s // per_sheet + 1:02d}.jpg"
        sheet.save(p, quality=88)
        paths.append(p)
    return paths


def extract(video: str, shots: list[dict], out_dir: str | Path, width: int = 360, candidates: int = 3,
            cols: int = 5, info: dict | None = None) -> dict:
    out_dir = Path(out_dir)
    kdir = out_dir / "keyframes"
    kdir.mkdir(parents=True, exist_ok=True)
    info = info or media_info(video)
    fps = info.get("fps") or 25.0
    keyframes, images = [], []
    for shot in shots:
        best = None
        for t in candidate_times(shot, fps, candidates):
            try:
                rgb = read_frame_at(video, t, width=width, pix_fmt="rgb24", info=info)
            except RuntimeError:
                continue
            grey = rgb.mean(axis=2)
            sc = sharpness(grey)
            if best is None or sc > best[0]:
                best = (sc, t, rgb)
        if best is None:
            keyframes.append({"index": shot["index"], "t_s": None, "path": None, "sharpness": None})
            continue
        sc, t, rgb = best
        img = Image.fromarray(rgb)
        rel = Path("keyframes") / f"shot_{int(shot['index']):03d}.jpg"
        img.save(out_dir / rel, quality=90)
        keyframes.append({"index": shot["index"], "t_s": t, "path": rel.as_posix(), "sharpness": sc})
        images.append((img, f"#{shot['index']} {float(shot['start_s']):.2f}s ({float(shot['end_s']) - float(shot['start_s']):.1f}s)"))
    sheets = contact_sheets(images, out_dir, cols=cols) if images else []
    return {"keyframes": keyframes, "contact_sheets": [p.relative_to(out_dir).as_posix() for p in sheets],
            "out_dir": str(out_dir)}


def run(video: str, shots: list[dict] | None, out_dir: str | Path, **kw) -> dict:
    try:
        info = media_info(video)
        shots = shots or whole_clip_shot(info.get("duration_s") or 0.0)
        res = extract(video, shots, out_dir, info=info, **kw)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except (RuntimeError, ValueError) as exc:
        return {"status": "error", "reason": str(exc)}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **res})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--shots", help="detect_shots JSON; default: run video_re_detect_shots")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--width", type=int, default=360)
    ap.add_argument("--candidates", type=int, default=3, choices=[1, 3])
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--out", help="write the JSON result here (default stdout)")
    a = ap.parse_args(argv)
    if a.shots:
        shots = shots_from_json(load_json(a.shots))
    else:
        det = import_sibling("video_re_detect_shots").run(a.video)
        shots = det.get("shots") if det.get("status") == "ok" else None
    res = run(a.video, shots, a.out_dir, width=a.width, candidates=a.candidates, cols=a.cols)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
