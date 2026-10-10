"""Run every video_re_* measurement on one video and write evidence.json (the 'disassembly').

Usage:
    python video_re_evidence_bundle.py video.mp4 --out-dir evidence/ [--reference URL] [--text-mode full|masked|none]
                                       [--skip ocr,transcribe] [--fast] [--sidecar subs.srt] [--transcript t.json]

Writes:

* ``evidence.json`` - exactly the shape in ``evidence.schema.json`` (spec baltor.video-evidence/v1):
  source, shots (with keyframe, palette, motion energy, camera move), shot_stats, text_regions,
  captions, audio (loudness, speech segments, onsets, tempo, speech rate, cut-beat alignment),
  overlay, safe_area, tools (name -> version) and errors
* ``details/<module>.json`` - each module's full output, for analysts who need more than the summary
* ``keyframes/`` and ``contact_sheet_NN.jpg`` - one representative frame per shot
* ``details/_run.json`` - timings and the options used

Every module is optional. A module that is missing, unavailable (no OCR engine, no speech
recogniser, no audio stream) or fails leaves its fields null and adds an ``errors`` entry naming the
module and the fields; nothing is estimated in its place. The other video_re_* packages are found
next to this package (catalogue or ``.baltor/lib`` layout), on ``sys.path``, or under
``VIDEO_RE_LIB``.

Boundary: evidence.json and its folder are local working files. They can hold caption text,
transcripts and frames of the analysed video. Analysts cite them; a format IR keeps only technique
and structure, never the source's footage, frames, music, voice or script. Use ``--text-mode
masked`` (or ``share_safe()``) before giving evidence to anyone else.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable

from video_re_common import (clean, import_sibling, package_version, tool_version, tool_versions)

IDENTITY = "video_re_evidence_bundle"
VERSION = "1.0.0"
SPEC = "baltor.video-evidence/v1"
SCHEMA_PATH = Path(__file__).resolve().parent / "evidence.schema.json"

MODULES = ["video_re_probe_metadata", "video_re_detect_shots", "video_re_shot_stats",
           "video_re_keyframes_contact_sheet", "video_re_palette_per_shot", "video_re_motion_energy",
           "video_re_camera_motion", "video_re_text_regions", "video_re_ocr_adapter", "video_re_caption_track",
           "video_re_overlay_transparency_probe", "video_re_safe_area_probe", "video_re_audio_loudness",
           "video_re_speech_segments", "video_re_onsets_beats", "video_re_transcribe_adapter",
           "video_re_speech_rate", "video_re_cut_beat_alignment"]
SKIP_ALIASES = {m.removeprefix("video_re_"): m for m in MODULES}
SKIP_ALIASES.update({"ocr": "video_re_ocr_adapter", "transcribe": "video_re_transcribe_adapter",
                     "keyframes": "video_re_keyframes_contact_sheet", "camera": "video_re_camera_motion",
                     "overlay": "video_re_overlay_transparency_probe", "palette": "video_re_palette_per_shot",
                     "motion": "video_re_motion_energy", "text": "video_re_text_regions",
                     "captions": "video_re_caption_track", "loudness": "video_re_audio_loudness",
                     "speech": "video_re_speech_segments", "beats": "video_re_onsets_beats",
                     "rate": "video_re_speech_rate", "alignment": "video_re_cut_beat_alignment",
                     "safe_area": "video_re_safe_area_probe"})
MAX_TEXT_REGIONS = 2000
MAX_VIOLATIONS = 500


def empty_evidence(reference: str) -> dict:
    return {
        "spec": SPEC,
        "source": {"reference": reference, "duration_s": None, "width": None, "height": None, "fps": None,
                   "has_audio": None},
        "shots": [],
        "shot_stats": {"count": None, "median_s": None, "mean_s": None, "cut_rate_per_min": None},
        "text_regions": [],
        "captions": [],
        "audio": {"integrated_lufs": None, "loudness_range": None, "speech_segments": None, "onsets_s": None,
                  "tempo_bpm": None, "speech_wpm": None, "cuts_on_beat_ratio": None},
        "overlay": {"semi_transparent_ratio": None},
        "safe_area": {"violations": []},
        "tools": {},
        "errors": [],
    }


class Runner:
    """Calls modules, records versions, timings, details and errors."""

    def __init__(self, out_dir: Path, skip: set[str]):
        self.out_dir = out_dir
        self.skip = skip
        self.errors: list[dict] = []
        self.tools: dict[str, str] = {}
        self.timings: dict[str, float] = {}
        self.mods: dict[str, Any] = {}

    def module(self, name: str):
        if name in self.mods:
            return self.mods[name]
        try:
            mod = import_sibling(name)
        except ImportError as exc:
            mod = None
            self.mods[name] = None
            self.errors.append({"module": name, "message": f"module not installed: {exc}"})
            return None
        self.mods[name] = mod
        self.tools[name] = getattr(mod, "VERSION", "unknown")
        return mod

    def call(self, name: str, fields: list[str], fn: Callable[[Any], dict],
             stored: Callable[[dict], dict] | None = None) -> dict | None:
        """Run fn(module). ``stored`` transforms what is written to details/ (e.g. to mask text)."""
        if name in self.skip:
            self.errors.append({"module": name, "message": "skipped by request", "fields": fields})
            return None
        mod = self.module(name)
        if mod is None:
            if fields:
                self.errors[-1]["fields"] = fields
            return None
        t0 = time.monotonic()
        try:
            res = fn(mod)
        except Exception as exc:  # noqa: BLE001 - one failing measurement must not stop the others
            res = {"status": "error", "reason": f"{type(exc).__name__}: {exc}"}
        self.timings[name] = round(time.monotonic() - t0, 3)
        details = self.out_dir / "details"
        details.mkdir(parents=True, exist_ok=True)
        keep = stored(json.loads(json.dumps(clean(res)))) if stored and res.get("status") == "ok" else res
        (details / f"{name}.json").write_text(json.dumps(clean(keep), indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8")
        if res.get("status") != "ok":
            self.errors.append({"module": name, "message": f"{res.get('status')}: {res.get('reason', '')}"[:500],
                                "fields": fields})
            return None
        return res


def assemble(ev: dict, r: dict[str, dict | None]) -> dict:
    """Fill the evidence skeleton from module results (any of which may be None)."""
    probe = r.get("probe")
    if probe:
        ev["source"].update({k: probe["source"].get(k) for k in ev["source"] if k != "reference"})
    shots_res = r.get("shots")
    if shots_res:
        kf = {k["index"]: k.get("path") for k in (r.get("keyframes") or {}).get("keyframes", [])}
        pal = {p["index"]: p.get("palette") for p in (r.get("palette") or {}).get("shots", [])}
        mot = {m["index"]: m for m in (r.get("motion") or {}).get("shots", [])}
        cam = {c["index"]: c for c in (r.get("camera") or {}).get("shots", [])}
        for s in shots_res["shots"]:
            i = s["index"]
            m = mot.get(i)
            c = cam.get(i)
            ev["shots"].append({
                "index": i, "start_s": s["start_s"], "end_s": s["end_s"], "duration_s": s["duration_s"],
                "keyframe": kf.get(i),
                "palette": pal.get(i) if r.get("palette") else None,
                "motion_energy": {"center": m.get("center"), "border": m.get("border")} if m else None,
                "camera": {"pan_x": c.get("pan_x"), "pan_y": c.get("pan_y"), "zoom": c.get("zoom")} if c else None,
            })
    st = r.get("shot_stats")
    if st:
        ev["shot_stats"] = {k: st.get(k) for k in ("count", "median_s", "mean_s", "cut_rate_per_min")}
    tr = r.get("text")
    if tr:
        ev["text_regions"] = [{k: x[k] for k in ("t_s", "bbox", "area_ratio", "y_center_ratio")}
                              for x in tr["regions"][:MAX_TEXT_REGIONS]]
    cap = r.get("captions")
    if cap:
        ev["captions"] = [{"start_s": c["start_s"], "end_s": c["end_s"], "text": c["text"]} for c in cap["captions"]]
    a = ev["audio"]
    if r.get("loudness"):
        a["integrated_lufs"] = r["loudness"].get("integrated_lufs")
        a["loudness_range"] = r["loudness"].get("loudness_range")
    if r.get("speech"):
        a["speech_segments"] = [{"start_s": s["start_s"], "end_s": s["end_s"]} for s in r["speech"]["segments"]]
    if r.get("beats"):
        a["onsets_s"] = r["beats"].get("onsets_s")
        a["tempo_bpm"] = r["beats"].get("tempo_bpm")
    if r.get("rate"):
        a["speech_wpm"] = r["rate"].get("speech_wpm")
    if r.get("alignment"):
        a["cuts_on_beat_ratio"] = r["alignment"].get("cuts_on_beat_ratio")
    if r.get("overlay"):
        ev["overlay"]["semi_transparent_ratio"] = r["overlay"].get("semi_transparent_ratio")
    if r.get("safe_area"):
        ev["safe_area"]["violations"] = [{k: v[k] for k in ("t_s", "zone", "bbox", "overlap_ratio")}
                                         for v in r["safe_area"]["violations"][:MAX_VIOLATIONS]]
    return ev


def mask_text(text: str) -> str:
    import re

    def tok(m):
        w = m.group(0)
        if re.fullmatch(r"\d[\d,.]*", w):
            return "{n}"
        if w.isupper() and len(w) > 1:
            return "WORD"
        return "Word" if w[0].isupper() else "word"
    return re.sub(r"[A-Za-z0-9][A-Za-z0-9,.'’]*(?<![,.])", tok, text)


def share_safe(evidence: dict) -> dict:
    """A copy without the source's words or frame paths: captions masked, keyframes dropped."""
    ev = json.loads(json.dumps(evidence))
    for c in ev["captions"]:
        c["text"] = mask_text(c["text"])
    for s in ev["shots"]:
        s["keyframe"] = None
    return ev


def validate(evidence: dict, schema_path: Path = SCHEMA_PATH) -> list[str]:
    """Schema problems (empty list = valid). Uses jsonschema when installed, else a key check."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        missing = [k for k in schema["required"] if k not in evidence]
        extra = [k for k in evidence if k not in schema["properties"]]
        return [f"missing {k}" for k in missing] + [f"unexpected {k}" for k in extra]
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}"[:300] for e in v.iter_errors(evidence)]


def build(video: str, out_dir: str | Path, reference: str | None = None, text_mode: str = "full",
          skip: set[str] | None = None, fast: bool = False, sidecar: str | None = None,
          transcript: str | None = None, ocr_engine: str = "auto", transcribe_engine: str = "auto",
          whisper_model: str = "small", allow_download: bool = False, profile: str = "auto") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    skip = {SKIP_ALIASES.get(s, s) for s in (skip or set())}
    run = Runner(out, skip)
    ev = empty_evidence(reference or Path(video).name)
    r: dict[str, dict | None] = {}
    t_start = time.monotonic()

    r["probe"] = run.call("video_re_probe_metadata", ["source"], lambda m: m.run(video))
    if r["probe"] is None:
        run.errors.append({"module": IDENTITY, "message": "video could not be probed; no other measurement ran"})
        ev["errors"], ev["tools"] = run.errors, {**tool_versions(("ffmpeg", "ffprobe"), ("numpy",)), **run.tools}
        return finish(ev, out, run, t_start, run_options(video, text_mode, skip, fast))
    src = r["probe"]["source"]
    duration = src.get("duration_s")
    r["shots"] = run.call("video_re_detect_shots", ["shots", "shot_stats"], lambda m: m.run(video))
    shots = (r["shots"] or {}).get("shots")
    if shots:
        r["shot_stats"] = run.call("video_re_shot_stats", ["shot_stats"], lambda m: m.run(shots, duration))
        r["keyframes"] = run.call("video_re_keyframes_contact_sheet", ["shots[].keyframe"],
                                  lambda m: m.run(video, shots, out, candidates=1 if fast else 3))
    r["palette"] = run.call("video_re_palette_per_shot", ["shots[].palette"],
                            lambda m: m.run(video, shots, sample_fps=2.0 if fast else 4.0)) if shots else None
    r["motion"] = run.call("video_re_motion_energy", ["shots[].motion_energy"],
                           lambda m: m.run(video, shots)) if shots else None
    r["camera"] = run.call("video_re_camera_motion", ["shots[].camera"],
                           lambda m: m.run(video, shots, stride_s=0.4 if fast else 0.2)) if shots else None
    r["text"] = run.call("video_re_text_regions", ["text_regions"],
                         lambda m: m.run(video, sample_fps=1.0 if fast else 2.0))
    regions = (r["text"] or {}).get("regions") or []
    if r["text"] and len(regions) > MAX_TEXT_REGIONS:
        run.errors.append({"module": "video_re_text_regions", "fields": ["text_regions"],
                           "message": f"truncated to {MAX_TEXT_REGIONS} of {len(regions)} regions; see details"})
    def redact_ocr(res: dict) -> dict:  # OCR runs with full text (captions are grouped by it); store it masked
        for it in res.get("items", []):
            it["text"] = mask_text(it["text"]) if text_mode == "masked" else ""
        return res

    ocr = run.call("video_re_ocr_adapter", ["captions"],
                   lambda m: m.run(video, regions, engine=ocr_engine, text_mode="full", allow_download=allow_download),
                   stored=None if text_mode == "full" else redact_ocr) if regions else None
    r["ocr"] = ocr
    ocr_items = [dict(it, y_center_ratio=(it["bbox"][1] + it["bbox"][3] / 2) / src["height"])
                 for it in (ocr or {}).get("items", [])] if src.get("height") else None
    r["captions"] = run.call("video_re_caption_track", ["captions"],
                             lambda m: m.run(video, sidecar, ocr_items, text_mode,
                                             ocr_sample_dt=1.0 if fast else 0.5))
    if r["captions"] and r["captions"].get("source") == "none":
        run.errors.append({"module": "video_re_caption_track", "fields": ["captions"],
                           "message": "no caption text measured (no subtitle stream, sidecar or OCR text)"})
    r["overlay"] = run.call("video_re_overlay_transparency_probe", ["overlay.semi_transparent_ratio"],
                            lambda m: m.run(video, shots, sample_fps=2.0 if fast else 4.0))
    if r["overlay"] and r["overlay"].get("semi_transparent_ratio") is None:
        run.errors.append({"module": "video_re_overlay_transparency_probe", "fields": ["overlay.semi_transparent_ratio"],
                           "message": (r["overlay"].get("summary") or {}).get("reason") or "no result"})
    if r["text"] is not None:
        r["safe_area"] = run.call("video_re_safe_area_probe", ["safe_area.violations"],
                                  lambda m: m.run(regions, src["width"], src["height"], profile))
        if r["safe_area"] and len(r["safe_area"]["violations"]) > MAX_VIOLATIONS:
            run.errors.append({"module": "video_re_safe_area_probe", "fields": ["safe_area.violations"],
                               "message": f"truncated to {MAX_VIOLATIONS} violations; see details"})

    if src.get("has_audio"):
        r["loudness"] = run.call("video_re_audio_loudness", ["audio.integrated_lufs", "audio.loudness_range"],
                                 lambda m: m.run(video))
        r["speech"] = run.call("video_re_speech_segments", ["audio.speech_segments"], lambda m: m.run(video))
        r["beats"] = run.call("video_re_onsets_beats", ["audio.onsets_s", "audio.tempo_bpm"], lambda m: m.run(video))
        if r["beats"] and r["beats"].get("tempo_bpm") is None:
            run.errors.append({"module": "video_re_onsets_beats", "fields": ["audio.tempo_bpm"],
                               "message": "no stable tempo found (fewer than 4 onsets or weak periodicity)"})
        tr = run.call("video_re_transcribe_adapter", [],
                      lambda m: m.run(video, transcribe_engine, whisper_model, allow_download, transcript, text_mode))
        r["transcript"] = tr
        r["rate"] = run.call("video_re_speech_rate", ["audio.speech_wpm"],
                             lambda m: m.run(video, tr if tr and tr.get("words") else None))
        if r["rate"] and r["rate"].get("speech_wpm") is None:
            run.errors.append({"module": "video_re_speech_rate", "fields": ["audio.speech_wpm"],
                               "message": r["rate"].get("reason") or "no rate measured"})
        if shots and r["beats"]:
            cuts = [float(s["start_s"]) for s in shots[1:]]
            r["alignment"] = run.call("video_re_cut_beat_alignment", ["audio.cuts_on_beat_ratio"],
                                      lambda m: m.run(cuts, r["beats"].get("beats_s"), r["beats"].get("onsets_s")))
            if r["alignment"] and r["alignment"].get("cuts_on_beat_ratio") is None:
                run.errors.append({"module": "video_re_cut_beat_alignment", "fields": ["audio.cuts_on_beat_ratio"],
                                   "message": r["alignment"].get("reason") or "no result"})
    else:
        run.errors.append({"module": IDENTITY, "message": "no audio stream: audio fields are null",
                           "fields": ["audio"]})

    ev = assemble(ev, r)
    tools = tool_versions(("ffmpeg", "ffprobe"), ("numpy", "Pillow"))
    engine_versions = {"tesseract": lambda: tool_version("tesseract"),
                       "pytesseract": lambda: package_version("pytesseract"),
                       "easyocr": lambda: package_version("easyocr"),
                       "faster-whisper": lambda: package_version("faster-whisper"),
                       "openai-whisper": lambda: package_version("openai-whisper"),
                       "whisper.cpp": lambda: tool_version("whisper-cli") or tool_version("whisper-cpp")}
    for used in ((ocr or {}).get("engine"), (r.get("transcript") or {}).get("engine")):
        if used in engine_versions:
            tools[used] = engine_versions[used]() or "unknown"
    ev["tools"] = {**tools, **run.tools, IDENTITY: VERSION}
    ev["errors"] = run.errors
    return finish(ev, out, run, t_start, run_options(video, text_mode, skip, fast))


def run_options(video: str, text_mode: str, skip: set[str], fast: bool) -> dict:
    return {"video": Path(video).name, "text_mode": text_mode, "skip": sorted(skip), "fast": fast}


def finish(ev: dict, out: Path, run: Runner, t_start: float, options: dict) -> dict:
    ev = clean(ev)
    problems = validate(ev)
    if problems:
        ev["errors"].append({"module": IDENTITY, "message": "evidence failed its schema: " + "; ".join(problems[:5])})
    (out / "evidence.json").write_text(json.dumps(ev, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "details").mkdir(parents=True, exist_ok=True)
    (out / "details" / "_run.json").write_text(json.dumps(
        {"options": options, "timings_s": run.timings, "total_s": round(time.monotonic() - t_start, 3),
         "schema_problems": problems}, indent=2) + "\n", encoding="utf-8")
    return ev


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--reference", help="URL or name to record instead of the file name")
    ap.add_argument("--text-mode", default="full", choices=["full", "masked", "none"])
    ap.add_argument("--skip", default="", help="comma-separated modules to skip, e.g. ocr,transcribe,keyframes")
    ap.add_argument("--fast", action="store_true", help="fewer samples: quicker, coarser")
    ap.add_argument("--sidecar", help=".srt/.vtt captions supplied with the video")
    ap.add_argument("--transcript", help="existing transcript (.srt/.vtt/whisper JSON) instead of running ASR")
    ap.add_argument("--ocr-engine", default="auto")
    ap.add_argument("--asr-engine", default="auto")
    ap.add_argument("--whisper-model", default="small")
    ap.add_argument("--allow-download", action="store_true", help="let OCR/ASR engines download model weights")
    ap.add_argument("--profile", default="auto", help="safe-area profile (see video_re_safe_area_probe)")
    ap.add_argument("--share-safe", action="store_true", help="also write evidence.share.json (masked text, no frames)")
    a = ap.parse_args(argv)
    ev = build(a.video, a.out_dir, a.reference, a.text_mode, {s.strip() for s in a.skip.split(",") if s.strip()},
               a.fast, a.sidecar, a.transcript, a.ocr_engine, a.asr_engine, a.whisper_model, a.allow_download,
               a.profile)
    if a.share_safe:
        Path(a.out_dir, "evidence.share.json").write_text(json.dumps(share_safe(ev), indent=2) + "\n", encoding="utf-8")
    print(f"evidence.json: {len(ev['shots'])} shots, {len(ev['text_regions'])} text regions, "
          f"{len(ev['captions'])} captions, {len(ev['errors'])} error entries -> {Path(a.out_dir) / 'evidence.json'}")
    return 0 if ev["source"]["duration_s"] is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
