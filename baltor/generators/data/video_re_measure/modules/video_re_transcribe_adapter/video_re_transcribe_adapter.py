"""Transcribe a soundtrack with a locally installed speech-recognition engine, with word timings.

Usage:
    python video_re_transcribe_adapter.py video.mp4 [--engine auto] [--model small] [--allow-download] [--out transcript.json]
    python video_re_transcribe_adapter.py video.mp4 --from-file subs.srt     # use an existing transcript

Engines, tried in this order by ``--engine auto`` (all optional, all imported lazily):

* ``faster-whisper`` (``pip install faster-whisper``) - word timestamps; CPU int8
* ``openai-whisper`` (``pip install openai-whisper``) - word timestamps
* ``whisper.cpp`` - the ``whisper-cli`` program with a ggml model named by ``WHISPER_CPP_MODEL``

Models are not downloaded unless ``--allow-download`` is given: faster-whisper runs with
``local_files_only`` and openai-whisper is only used when its model file is already in the cache.
Without a usable engine the result is ``{"status": "unavailable"}`` and nothing is guessed.

The transcript is the analysed video's script. It is local evidence for measuring structure
(speech rate, hook length, sentence rhythm, where numbers are said) and must never be copied into a
format IR or republished. ``--text-mode masked`` keeps word timings but replaces each word with its
shape ('Word', 'word', 'WORD', '{n}'); ``none`` drops the text.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from video_re_common import ToolMissing, clean, dump_json, media_info, require, unavailable

IDENTITY = "video_re_transcribe_adapter"
VERSION = "1.0.0"
ENGINES = ("faster-whisper", "openai-whisper", "whisper.cpp")
WHISPER_CPP_BINARIES = ("whisper-cli", "whisper-cpp")  # not "whisper": that is openai-whisper's CLI


# ---------------------------------------------------------------- text helpers

def mask_word(w: str) -> str:
    core = w.strip()
    if not core:
        return core
    if re.fullmatch(r"[\d,.%$]+", core):
        return "{n}"
    letters = re.sub(r"[^A-Za-z]", "", core)
    if letters.isupper() and len(letters) > 1:
        return "WORD"
    return "Word" if letters[:1].isupper() else "word"


def apply_text_mode(res: dict, mode: str) -> dict:
    if mode not in {"full", "masked", "none"}:
        raise ValueError("text_mode must be full, masked or none")
    if mode == "full":
        return res
    for w in res.get("words", []):
        w["word"] = mask_word(w["word"]) if mode == "masked" else ""
    for s in res.get("segments", []):
        s["text"] = " ".join(mask_word(x) for x in s["text"].split()) if mode == "masked" else ""
    return res


def words_from_segments(segments: list[dict]) -> list[dict]:
    """Even split of each segment's words over its duration (labelled estimate) when no word times exist."""
    out = []
    for s in segments:
        ws = s["text"].split()
        if not ws:
            continue
        step = (s["end_s"] - s["start_s"]) / len(ws)
        for i, w in enumerate(ws):
            out.append({"start_s": s["start_s"] + i * step, "end_s": s["start_s"] + (i + 1) * step, "word": w,
                        "estimated": True})
    return out


# ---------------------------------------------------------------- engines

def _faster_whisper(audio: str, model: str, allow_download: bool) -> dict:
    fw = importlib.import_module("faster_whisper")
    m = fw.WhisperModel(model, device="cpu", compute_type="int8", local_files_only=not allow_download)
    segments, info = m.transcribe(audio, word_timestamps=True)
    segs, words = [], []
    for s in segments:
        segs.append({"start_s": float(s.start), "end_s": float(s.end), "text": s.text.strip()})
        for w in s.words or []:
            words.append({"start_s": float(w.start), "end_s": float(w.end), "word": w.word.strip(),
                          "probability": float(getattr(w, "probability", 0.0) or 0.0)})
    return {"language": getattr(info, "language", None), "segments": segs, "words": words}


def _whisper_cache_has(model: str) -> bool:
    root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "whisper"
    return any(root.glob(f"{model}*.pt"))


def _openai_whisper(audio: str, model: str, allow_download: bool) -> dict:
    if not allow_download and not _whisper_cache_has(model):
        raise FileNotFoundError(f"openai-whisper model '{model}' is not cached; pass --allow-download")
    wh = importlib.import_module("whisper")
    res = wh.load_model(model).transcribe(audio, word_timestamps=True)
    segs, words = [], []
    for s in res.get("segments", []):
        segs.append({"start_s": float(s["start"]), "end_s": float(s["end"]), "text": s["text"].strip()})
        for w in s.get("words", []) or []:
            words.append({"start_s": float(w["start"]), "end_s": float(w["end"]), "word": w["word"].strip(),
                          "probability": float(w.get("probability", 0.0) or 0.0)})
    return {"language": res.get("language"), "segments": segs, "words": words}


def parse_whisper_cpp_json(data: dict) -> dict:
    """whisper.cpp -oj output (run with -ml 1 -sow for one word per entry)."""
    words = []
    for item in data.get("transcription", []):
        off = item.get("offsets") or {}
        text = (item.get("text") or "").strip()
        if not text or "from" not in off:
            continue
        words.append({"start_s": off["from"] / 1000.0, "end_s": off.get("to", off["from"]) / 1000.0, "word": text})
    segs = []
    for w in words:  # rebuild sentence-ish segments: break on gaps > 0.6 s or sentence punctuation
        if segs and w["start_s"] - segs[-1]["end_s"] <= 0.6 and not re.search(r"[.!?]$", segs[-1]["text"]):
            segs[-1]["end_s"] = w["end_s"]
            segs[-1]["text"] += " " + w["word"]
        else:
            segs.append({"start_s": w["start_s"], "end_s": w["end_s"], "text": w["word"]})
    lang = (data.get("result") or {}).get("language")
    return {"language": lang, "segments": segs, "words": words}


def _whisper_cpp_binary() -> str | None:
    return next((b for b in WHISPER_CPP_BINARIES if shutil.which(b)), None)


def _whisper_cpp(audio: str, model: str, allow_download: bool) -> dict:
    binary = _whisper_cpp_binary()
    model_path = os.environ.get("WHISPER_CPP_MODEL")
    if not binary or not model_path or not Path(model_path).exists():
        raise FileNotFoundError("whisper.cpp needs whisper-cli on PATH and WHISPER_CPP_MODEL pointing at a ggml model")
    require("ffmpeg")
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "a.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", audio, "-vn", "-ac", "1", "-ar", "16000",
                        str(wav)], check=True, timeout=600)
        prefix = Path(d) / "out"
        subprocess.run([binary, "-m", model_path, "-f", str(wav), "-oj", "-of", str(prefix), "-ml", "1", "-sow"],
                       check=True, capture_output=True, timeout=7200, stdin=subprocess.DEVNULL)
        return parse_whisper_cpp_json(json.loads(prefix.with_suffix(".json").read_text(encoding="utf-8")))


def engine_available(name: str) -> bool:
    if name == "faster-whisper":
        return importlib.util.find_spec("faster_whisper") is not None
    if name == "openai-whisper":
        return importlib.util.find_spec("whisper") is not None
    if name == "whisper.cpp":
        return _whisper_cpp_binary() is not None and bool(os.environ.get("WHISPER_CPP_MODEL"))
    return False


RUNNERS = {"faster-whisper": _faster_whisper, "openai-whisper": _openai_whisper, "whisper.cpp": _whisper_cpp}


# ---------------------------------------------------------------- existing transcripts

def from_file(path: str) -> dict:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() == ".json":
        data = json.loads(text)
        if "transcription" in data:
            return parse_whisper_cpp_json(data)
        segs, words = [], []
        for s in data.get("segments", []):
            start = float(s.get("start", s.get("start_s", 0)))
            end = float(s.get("end", s.get("end_s", start)))
            segs.append({"start_s": start, "end_s": end, "text": str(s.get("text", "")).strip()})
            for w in s.get("words", []) or []:
                words.append({"start_s": float(w.get("start", w.get("start_s", 0))),
                              "end_s": float(w.get("end", w.get("end_s", 0))), "word": str(w.get("word", "")).strip()})
        return {"language": data.get("language"), "segments": segs, "words": words}
    stamps = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})")

    def t(s):
        h, mi, se, ms = stamps.search(s).groups()
        return int(h or 0) * 3600 + int(mi) * 60 + int(se) + int(ms.ljust(3, "0")) / 1000

    segs = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = [x for x in block.split("\n") if x.strip()]
        for i, ln in enumerate(lines):
            if "-->" in ln:
                a, b = ln.split("-->", 1)
                body = re.sub(r"<[^>]+>", "", " ".join(lines[i + 1:])).strip()
                if body:
                    segs.append({"start_s": t(a), "end_s": t(b), "text": body})
                break
    return {"language": None, "segments": segs, "words": []}


# ---------------------------------------------------------------- entry point

def run(video: str, engine: str = "auto", model: str = "small", allow_download: bool = False,
        from_path: str | None = None, text_mode: str = "full") -> dict:
    if from_path:
        res = from_file(from_path)
        used = "file"
    else:
        try:
            if not media_info(video).get("has_audio"):
                return unavailable("no audio stream")
        except ToolMissing as exc:
            return unavailable(str(exc))
        order = ENGINES if engine == "auto" else (engine,)
        tried, res, used = [], None, None
        for name in order:
            if not engine_available(name):
                tried.append(f"{name}: not installed")
                continue
            try:
                res = RUNNERS[name](video, model, allow_download)
                used = name
                break
            except Exception as exc:  # noqa: BLE001 - one engine failing should not hide the next
                tried.append(f"{name}: {type(exc).__name__}: {exc}"[:240])
        if res is None:
            return unavailable("no speech-recognition engine produced a transcript", tried=tried, module=IDENTITY)
    words_estimated = False
    if not res.get("words") and res.get("segments"):
        res["words"] = words_from_segments(res["segments"])
        words_estimated = True
    res["word_count"] = len(res.get("words", []))
    res = apply_text_mode(res, text_mode)
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, "engine": used,
                  "model": model if used not in ("file",) else None, "words_estimated": words_estimated,
                  "text_mode": text_mode, **res}, nd=3)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--engine", default="auto", choices=("auto",) + ENGINES)
    ap.add_argument("--model", default="small", help="model size/name for the whisper engines")
    ap.add_argument("--allow-download", action="store_true", help="let the engine download model weights")
    ap.add_argument("--from-file", help="existing transcript: .srt, .vtt, whisper JSON or whisper.cpp JSON")
    ap.add_argument("--text-mode", default="full", choices=["full", "masked", "none"])
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = run(a.video, a.engine, a.model, a.allow_download, a.from_file, a.text_mode)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
