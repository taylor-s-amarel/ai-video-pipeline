"""Read the text inside proposed text regions with whatever OCR engine is installed.

Usage:
    python video_re_ocr_adapter.py video.mp4 --regions text_regions.json [--engine auto] [--out ocr.json]

Engines, tried in this order by ``--engine auto``:

* ``tesseract`` - the Tesseract command-line program (``tesseract img stdout --psm 7 tsv``)
* ``pytesseract`` - the Python wrapper around the same program
* ``easyocr`` - EasyOCR on CPU; models are only downloaded when ``--allow-download`` is given

None of them is required: without one the result is ``{"status": "unavailable", ...}`` and the
evidence bundle records the gap instead of guessing text.

Each region (from video_re_text_regions) is cropped from a frame decoded at its time stamp (up to
1280 px wide), padded by 15%, enlarged to at least 64 px tall, converted to grey and sent to the
engine. Regions at the same time stamp share one decoded frame.

Text handling (the analysis boundary): OCR text is local evidence for structure, never content to
reuse. ``text_mode`` 'full' keeps the words (default, local files only), 'masked' keeps only their
shape ("WORD {n}: {n} word word"), 'none' drops them. ``label_pattern`` turns "FACT 3" into
"FACT {n}" so the parameteriser can lift a numbered-label pattern without copying wording.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from video_re_common import ToolMissing, clean, dump_json, have, load_json, media_info, read_frame_at, unavailable

IDENTITY = "video_re_ocr_adapter"
VERSION = "1.0.0"
ENGINE_ORDER = ("tesseract", "pytesseract", "easyocr")

LABEL_RE = re.compile(r"^\s*(?P<word>[A-Za-z]{2,12})?\s*(?P<hash>#|No\.?|N[oº]\s*)?\s*(?P<num>\d{1,3})\s*[:.)-]?\s*$")


# ---------------------------------------------------------------- text utilities

def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def label_pattern(text: str) -> str | None:
    """'FACT 3' -> 'FACT {n}', '#2' -> '#{n}', 'Step 10:' -> 'Step {n}'. None when it is not a label."""
    m = LABEL_RE.match(normalise(text))
    if not m:
        return None
    word = m.group("word") or ""
    hash_ = "#" if m.group("hash") and m.group("hash").startswith("#") else ("No. " if m.group("hash") else "")
    if not word and not hash_:
        return "{n}"
    return f"{word} {hash_}{{n}}".strip() if word else f"{hash_}{{n}}"


def label_number(text: str) -> int | None:
    m = LABEL_RE.match(normalise(text))
    return int(m.group("num")) if m else None


def summarise_labels(items: list[dict]) -> dict:
    """{pattern: {count, numbers, first_t_s}}: e.g. FACT {n} seen with numbers 1-5."""
    out: dict[str, dict] = {}
    for it in sorted(items, key=lambda i: i["t_s"]):
        pat = it.get("label_pattern")
        if not pat:
            continue
        e = out.setdefault(pat, {"count": 0, "numbers": [], "first_t_s": it["t_s"]})
        e["count"] += 1
        n = it.get("label_number")
        if n is not None and n not in e["numbers"]:
            e["numbers"].append(n)
    for e in out.values():
        e["numbers"].sort()
    return out


def mask_text(text: str) -> str:
    """Keep the shape of text, not its words: UPPER -> WORD, Capital -> Word, lower -> word, digits -> {n}."""
    def tok(m):
        w = m.group(0)
        if w.isdigit() or re.fullmatch(r"\d[\d,.]*", w):
            return "{n}"
        if w.isupper() and len(w) > 1:
            return "WORD"
        if w[0].isupper():
            return "Word"
        return "word"
    return re.sub(r"[A-Za-z0-9][A-Za-z0-9,.'’]*(?<![,.])", tok, normalise(text))


def text_shape(text: str) -> dict:
    t = normalise(text)
    letters = [c for c in t if c.isalpha()]
    case = "none"
    if letters:
        up = sum(c.isupper() for c in letters) / len(letters)
        case = "upper" if up > 0.9 else "lower" if up < 0.1 else "title" if all(
            w[0].isupper() for w in t.split() if w[0].isalpha()) else "sentence"
    return {"words": len(t.split()), "chars": len(t), "case": case, "has_number": bool(re.search(r"\d", t))}


def apply_text_mode(text: str, mode: str) -> str:
    if mode == "full":
        return text
    if mode == "masked":
        return mask_text(text)
    if mode == "none":
        return ""
    raise ValueError("text_mode must be full, masked or none")


# ---------------------------------------------------------------- engines

def _tesseract_cli(img: Image.Image, psm: int = 7) -> tuple[str, float | None]:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "crop.png"
        img.save(p)
        proc = subprocess.run(["tesseract", str(p), "stdout", "--psm", str(psm), "tsv"], capture_output=True,
                              text=True, timeout=60, stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-300:])
    return parse_tesseract_tsv(proc.stdout)


def parse_tesseract_tsv(tsv: str) -> tuple[str, float | None]:
    words, confs = [], []
    lines = tsv.strip().splitlines()
    if not lines:
        return "", None
    header = lines[0].split("\t")
    try:
        ci, ti = header.index("conf"), header.index("text")
    except ValueError:
        return "", None
    for line in lines[1:]:
        cols = line.split("\t")
        if len(cols) <= max(ci, ti):
            continue
        try:
            conf = float(cols[ci])
        except ValueError:
            continue
        if conf >= 0 and cols[ti].strip():
            words.append(cols[ti].strip())
            confs.append(conf)
    return " ".join(words), (float(np.mean(confs)) / 100.0 if confs else None)


def _pytesseract(img: Image.Image, psm: int = 7) -> tuple[str, float | None]:
    pt = importlib.import_module("pytesseract")
    data = pt.image_to_data(img, config=f"--psm {psm}", output_type=pt.Output.DICT)
    words, confs = [], []
    for w, c in zip(data.get("text", []), data.get("conf", [])):
        try:
            c = float(c)
        except (TypeError, ValueError):
            continue
        if c >= 0 and str(w).strip():
            words.append(str(w).strip())
            confs.append(c)
    return " ".join(words), (float(np.mean(confs)) / 100.0 if confs else None)


_EASY = {}


def _easyocr(img: Image.Image, allow_download: bool = False) -> tuple[str, float | None]:
    easyocr = importlib.import_module("easyocr")
    key = ("en", allow_download)
    if key not in _EASY:
        _EASY[key] = easyocr.Reader(["en"], gpu=False, verbose=False, download_enabled=allow_download)
    res = _EASY[key].readtext(np.asarray(img))
    res = sorted(res, key=lambda r: min(p[0] for p in r[0]))
    text = " ".join(r[1] for r in res)
    return text, (float(np.mean([r[2] for r in res])) if res else None)


def engine_available(name: str) -> bool:
    if name == "tesseract":
        return have("tesseract")
    if name == "pytesseract":
        return importlib.util.find_spec("pytesseract") is not None and have("tesseract")
    if name == "easyocr":
        return importlib.util.find_spec("easyocr") is not None
    return False


def available_engines() -> list[str]:
    return [e for e in ENGINE_ORDER if engine_available(e)]


def pick_engine(engine: str = "auto") -> str | None:
    if engine == "auto":
        found = available_engines()
        return found[0] if found else None
    return engine if engine_available(engine) else None


def ocr_image(img: Image.Image, engine: str, allow_download: bool = False) -> tuple[str, float | None]:
    if engine == "tesseract":
        return _tesseract_cli(img)
    if engine == "pytesseract":
        return _pytesseract(img)
    if engine == "easyocr":
        return _easyocr(img, allow_download)
    raise ValueError(f"unknown OCR engine {engine}")


# ---------------------------------------------------------------- cropping

def crop_region(frame_rgb: np.ndarray, bbox: list[float], frame_size: tuple[int, int], pad: float = 0.15,
                min_height: int = 64) -> Image.Image:
    """Crop bbox (source pixels) from a decoded frame of any size, padded, grey, enlarged if small."""
    fh, fw = frame_rgb.shape[:2]
    sx, sy = fw / frame_size[0], fh / frame_size[1]
    x, y, w, h = bbox
    px, py = w * pad, h * pad
    x0, y0 = max(0, int((x - px) * sx)), max(0, int((y - py) * sy))
    x1, y1 = min(fw, int(np.ceil((x + w + px) * sx))), min(fh, int(np.ceil((y + h + py) * sy)))
    img = Image.fromarray(frame_rgb[y0:y1, x0:x1]).convert("L")
    if img.height < min_height and img.height > 0:
        k = min_height / img.height
        img = img.resize((max(1, int(img.width * k)), min_height), Image.LANCZOS)
    return img


def read_regions(video: str, regions: list[dict], engine: str, max_regions: int = 300, text_mode: str = "full",
                 allow_download: bool = False, info: dict | None = None) -> dict:
    info = info or media_info(video)
    size = (info["width"], info["height"])
    width = min(1280, size[0])
    by_t: dict[float, list[dict]] = defaultdict(list)
    for r in sorted(regions, key=lambda r: -r.get("score", 1.0))[:max_regions]:
        by_t[float(r["t_s"])].append(r)
    items, errors = [], []
    for t in sorted(by_t):
        try:
            frame = read_frame_at(video, t, width=width, pix_fmt="rgb24", info=info)
        except RuntimeError as exc:
            errors.append(f"{t:.2f}s: {exc}")
            continue
        for r in by_t[t]:
            try:
                text, conf = ocr_image(crop_region(frame, r["bbox"], size), engine, allow_download)
            except Exception as exc:  # noqa: BLE001 - engine failures are recorded, not fatal
                errors.append(f"{t:.2f}s: {type(exc).__name__}: {exc}"[:300])
                continue
            text = normalise(text)
            if not text:
                continue
            items.append({"t_s": t, "bbox": r["bbox"], "text": apply_text_mode(text, text_mode), "confidence": conf,
                          "label_pattern": label_pattern(text), "label_number": label_number(text),
                          "shape": text_shape(text)})
    summary = {"label_patterns": summarise_labels(items), "items": len(items)}
    return {"engine": engine, "items": items, "summary": summary, "errors": errors[:50], "text_mode": text_mode}


def run(video: str, regions: list[dict], engine: str = "auto", max_regions: int = 300, text_mode: str = "full",
        allow_download: bool = False) -> dict:
    chosen = pick_engine(engine)
    if chosen is None:
        return unavailable(f"no OCR engine available (tried {', '.join(ENGINE_ORDER) if engine == 'auto' else engine}); "
                           "install tesseract-ocr, or pip install pytesseract or easyocr",
                           module=IDENTITY, version=VERSION)
    if not regions:
        return clean({"status": "ok", "module": IDENTITY, "version": VERSION, "engine": chosen, "items": [],
                      "summary": {"label_patterns": {}, "items": 0}, "errors": [], "text_mode": text_mode})
    try:
        res = read_regions(video, regions, chosen, max_regions, text_mode, allow_download)
    except ToolMissing as exc:
        return unavailable(str(exc))
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **res})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--regions", required=True, help="video_re_text_regions JSON (or evidence.json)")
    ap.add_argument("--engine", default="auto", choices=("auto",) + ENGINE_ORDER)
    ap.add_argument("--max-regions", type=int, default=300)
    ap.add_argument("--text-mode", default="full", choices=["full", "masked", "none"])
    ap.add_argument("--allow-download", action="store_true", help="let EasyOCR download its models")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    data = load_json(a.regions)
    regions = data.get("regions") or data.get("text_regions") or [] if isinstance(data, dict) else data
    res = run(a.video, regions, a.engine, a.max_regions, a.text_mode, a.allow_download)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
