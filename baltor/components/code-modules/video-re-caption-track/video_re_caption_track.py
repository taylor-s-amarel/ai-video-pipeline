"""Build the caption track of a video and measure its timing and density.

Usage:
    python video_re_caption_track.py video.mp4 [--sidecar subs.srt] [--ocr ocr.json] [--text-mode full] [--out captions.json]

Sources, first match wins:

1. ``sidecar`` - an .srt or .vtt file you were given with the video
2. ``embedded`` - the first subtitle stream in the container, converted to SRT by ffmpeg
3. ``ocr`` - burned-in captions rebuilt from video_re_ocr_adapter results in the caption band
   (``band``, default y_center_ratio 0.55-1.0): consecutive samples with near-identical text
   (difflib ratio >= 0.8) become one caption event from its first sample to its last sample plus
   one sample interval, so OCR timing is only as fine as the OCR sampling (default 0.5 s)
4. ``none`` - no caption text could be measured; an empty list, never invented text

Stats: count, words per caption (mean, max), characters per second (reading speed), caption
duration (mean, median), gaps between captions, coverage (share of the running time with a caption
on screen), share of words in capitals, and the first caption's start time.

Captions are the analysed video's words. ``text_mode`` 'masked' replaces words by their shape
('WORD {n} word') and 'none' empties them; use either before sharing results. Nothing here may be
copied into a format IR except the measured timing and density.
"""

from __future__ import annotations

import argparse
import difflib
import re
from pathlib import Path

import numpy as np

from video_re_common import ToolMissing, clean, dump_json, load_json, media_info, run as run_cmd, unavailable

IDENTITY = "video_re_caption_track"
VERSION = "1.0.0"

TIME_RE = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})")


def _t(text: str) -> float:
    m = TIME_RE.search(text)
    if not m:
        raise ValueError(f"bad time stamp {text!r}")
    h, mnt, s, ms = m.groups()
    return int(h or 0) * 3600 + int(mnt) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000.0


def _strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{\\[^}]*\}", "", text)
    return text.strip()


def parse_srt(text: str) -> list[dict]:
    out = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = [ln for ln in block.split("\n") if ln.strip()]
        for i, ln in enumerate(lines):
            if "-->" in ln:
                a, b = ln.split("-->", 1)
                body = _strip_tags("\n".join(lines[i + 1:]))
                if body:
                    out.append({"start_s": _t(a), "end_s": _t(b), "text": body})
                break
    return sorted(out, key=lambda c: c["start_s"])


def parse_vtt(text: str) -> list[dict]:
    body = re.sub(r"^﻿?WEBVTT[^\n]*\n", "", text.replace("\r\n", "\n"))
    body = re.sub(r"(?ms)^(NOTE|STYLE|REGION)\b.*?(?:\n\n|\Z)", "", body)
    return parse_srt(body)


def from_sidecar(path: str | Path) -> list[dict]:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    return parse_vtt(text) if p.suffix.lower() == ".vtt" or text.lstrip("﻿").startswith("WEBVTT") else parse_srt(text)


def embedded(video: str, info: dict | None = None) -> list[dict] | None:
    info = info or media_info(video)
    if not info.get("subtitle_streams"):
        return None
    proc = run_cmd(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", video, "-map", "0:s:0",
                    "-f", "srt", "-"], timeout=300, check=False)
    if proc.returncode != 0:
        return None  # bitmap subtitles (PGS, DVB) cannot become text without OCR
    return parse_srt(proc.stdout.decode("utf-8", "replace"))


def from_ocr(items: list[dict], band: tuple[float, float] = (0.55, 1.0), sample_dt: float = 0.5,
             frame_height: float | None = None, similarity: float = 0.8) -> list[dict]:
    rows = []
    for it in sorted(items, key=lambda i: i["t_s"]):
        bbox = it.get("bbox") or [0, 0, 0, 0]
        yc = it.get("y_center_ratio")
        if yc is None and frame_height:
            yc = (bbox[1] + bbox[3] / 2) / frame_height
        if yc is not None and not (band[0] <= yc <= band[1]):
            continue
        if it.get("text"):
            rows.append(it)
    by_t: dict[float, list[dict]] = {}
    for r in rows:
        by_t.setdefault(float(r["t_s"]), []).append(r)
    samples = [(t, " ".join(r["text"] for r in sorted(rs, key=lambda r: (r["bbox"][1], r["bbox"][0]))))
               for t, rs in sorted(by_t.items())]
    events: list[dict] = []
    for t, text in samples:
        last = events[-1] if events else None
        if last and t - last["_last"] <= sample_dt * 1.5 + 1e-6 and \
                difflib.SequenceMatcher(None, last["text"].lower(), text.lower()).ratio() >= similarity:
            last["_last"] = t
            if len(text) > len(last["text"]):
                last["text"] = text
            continue
        events.append({"start_s": t, "_last": t, "text": text})
    return [{"start_s": e["start_s"], "end_s": e["_last"] + sample_dt, "text": e["text"]} for e in events]


def mask(text: str) -> str:
    def tok(m):
        w = m.group(0)
        if re.fullmatch(r"\d[\d,.]*", w):
            return "{n}"
        if w.isupper() and len(w) > 1:
            return "WORD"
        return "Word" if w[0].isupper() else "word"
    return re.sub(r"[A-Za-z0-9][A-Za-z0-9,.'’]*(?<![,.])", tok, text)


def apply_text_mode(captions: list[dict], mode: str) -> list[dict]:
    if mode not in {"full", "masked", "none"}:
        raise ValueError("text_mode must be full, masked or none")
    if mode == "full":
        return captions
    return [{**c, "text": mask(c["text"]) if mode == "masked" else ""} for c in captions]


def stats(captions: list[dict], duration_s: float | None = None) -> dict:
    if not captions:
        return {"count": 0}
    d = np.array([max(0.0, c["end_s"] - c["start_s"]) for c in captions])
    words = np.array([len(c["text"].split()) for c in captions])
    chars = np.array([len(c["text"].replace("\n", " ")) for c in captions])
    gaps = np.array([max(0.0, b["start_s"] - a["end_s"]) for a, b in zip(captions, captions[1:])])
    all_words = [w for c in captions for w in re.findall(r"[A-Za-z]{2,}", c["text"])]
    out = {
        "count": len(captions),
        "words_mean": float(words.mean()), "words_max": int(words.max()),
        "chars_per_s_mean": float(np.mean(chars / np.maximum(d, 1e-3))),
        "duration_mean_s": float(d.mean()), "duration_median_s": float(np.median(d)),
        "gap_mean_s": float(gaps.mean()) if len(gaps) else None,
        "lines_max": int(max(c["text"].count("\n") + 1 for c in captions)),
        "caps_word_share": float(np.mean([w.isupper() for w in all_words])) if all_words else None,
        "first_start_s": float(captions[0]["start_s"]),
    }
    if duration_s:
        out["coverage"] = float(min(1.0, d.sum() / duration_s))
    return out


def run(video: str | None = None, sidecar: str | None = None, ocr_items: list[dict] | None = None,
        text_mode: str = "full", ocr_sample_dt: float = 0.5) -> dict:
    source, caps, info = "none", [], None
    try:
        if video:
            info = media_info(video)
        if sidecar:
            caps, source = from_sidecar(sidecar), "sidecar"
        elif video and (emb := embedded(video, info)) is not None:
            caps, source = emb, "embedded"
        elif ocr_items:
            caps = from_ocr(ocr_items, sample_dt=ocr_sample_dt, frame_height=(info or {}).get("height"))
            source = "ocr"
    except ToolMissing as exc:
        return unavailable(str(exc))
    duration = (info or {}).get("duration_s")
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, "source": source,
                  "captions": apply_text_mode(caps, text_mode), "stats": stats(caps, duration), "text_mode": text_mode,
                  "note": "no caption text measured" if source == "none" else None})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?")
    ap.add_argument("--sidecar", help=".srt or .vtt file")
    ap.add_argument("--ocr", help="video_re_ocr_adapter JSON")
    ap.add_argument("--ocr-dt", type=float, default=0.5, help="seconds between OCR samples")
    ap.add_argument("--text-mode", default="full", choices=["full", "masked", "none"])
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    items = load_json(a.ocr).get("items") if a.ocr else None
    res = run(a.video, a.sidecar, items, a.text_mode, a.ocr_dt)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
