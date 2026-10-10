#!/usr/bin/env python3
"""Measurement tools of the video reverse-engineering swarm (the 'disassembler').

A binary reverse-engineering swarm first loads and disassembles the binary so its analysts argue
over hard facts. These 19 code modules do the same for a video: they turn it into measured
evidence (shots, cut rhythm, palettes, motion, camera moves, text regions, captions, overlay
transparency, safe-area clashes, loudness, speech, onsets, tempo, speech rate, cut-to-beat
alignment) and ``video_re_evidence_bundle`` writes it all to ``evidence.json``
(spec ``baltor.video-evidence/v1``), the file the analyst, challenger and lifter subagents cite.

Source layout under ``data/video_re_measure/``:

* ``common/video_re_common.py``, ``common/video_re_synth.py`` - shared helpers and synthetic test
  media, vendored into every package so each one works and tests on its own
* ``modules/<identity>/`` - ``<identity>.py``, ``test_<identity>.py``, ``meta.yaml`` and extra payload
  (the bundle also ships ``evidence.schema.json``)
* ``evidence.schema.json`` - the documented evidence.json schema (the format builder's
  ``video_re_evidence`` contract and the swarm builder's question banks read it from here)

Run: ``cd baltor/generators && python3 video_re_measure.py``
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import yaml

from _lib import GeneratorRun, effects

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "video_re_measure"
COMMON = DATA / "common"
MODULES = DATA / "modules"
SCHEMA = DATA / "evidence.schema.json"
CHECKED = "2026-10-10"

ORDER = [
    "video_re_probe_metadata", "video_re_detect_shots", "video_re_shot_stats", "video_re_keyframes_contact_sheet",
    "video_re_palette_per_shot", "video_re_motion_energy", "video_re_camera_motion", "video_re_text_regions",
    "video_re_ocr_adapter", "video_re_caption_track", "video_re_audio_loudness", "video_re_speech_segments",
    "video_re_onsets_beats", "video_re_transcribe_adapter", "video_re_speech_rate", "video_re_cut_beat_alignment",
    "video_re_overlay_transparency_probe", "video_re_safe_area_probe", "video_re_evidence_bundle",
]
SKIP_NAMES = {"meta.yaml", ".DS_Store"}
SKIP_DIRS = {"__pycache__", ".pytest_cache"}

BOUNDARY = (
    "Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, "
    "rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are "
    "local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of "
    "anything published and out of a format IR, which keeps only technique, structure and parameters - never "
    "the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an "
    "evidence note, no transcripts)."
)

SWARM = (
    "Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video "
    "into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute "
    "them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content "
    "(5), and the same measurements on the variant score fidelity (6)."
)


def payload_files(pkg_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(pkg_dir.rglob("*")):
        rel_parts = p.relative_to(pkg_dir).parts
        if not p.is_file() or p.name in SKIP_NAMES or SKIP_DIRS.intersection(rel_parts) or p.suffix in {".pyc", ".pyo"}:
            continue
        out[p.relative_to(pkg_dir).as_posix()] = p.read_text(encoding="utf-8")
    return out


def docstring(source: str) -> str:
    return (ast.get_docstring(ast.parse(source)) or "").strip()


def method_text(doc: str) -> str:
    """Docstring without its first line and its Usage block."""
    lines = doc.splitlines()[1:]
    out, skipping = [], False
    for ln in lines:
        if ln.strip().startswith("Usage:"):
            skipping = True
            continue
        if skipping:
            if ln.startswith("    ") or not ln.strip():
                if not ln.strip() and out and out[-1] != "":
                    skipping = False
                continue
            skipping = False
        out.append(ln)
    return "\n".join(out).strip()


def external(name: str) -> dict:
    return {"identity": name, "external": True}


def depends(meta: dict) -> list[dict]:
    deps = [external(d) for d in meta.get("deps", [])]
    deps += [external(d) for d in meta.get("optional", [])]
    internal = meta.get("internal") or []
    if internal == "ALL":
        internal = [{"identity": i} for i in ORDER if i != "video_re_evidence_bundle"]
    return deps + list(internal)


def effects_for(identity: str, meta: dict) -> dict:
    side = ["runs ffmpeg/ffprobe as subprocesses" if "ffmpeg" in meta.get("deps", []) or "ffprobe" in meta.get("deps", [])
            else "pure computation on JSON inputs",
            "writes only where --out / --out-dir point (stdout otherwise)"]
    if meta.get("optional"):
        side.append("imports optional engines lazily: " + ", ".join(meta["optional"]))
    if meta.get("network_note"):
        side.append(meta["network_note"])
    return effects(filesystem="write", executes="python", hosts=meta.get("network_hosts"), side_effects=side)


def readme(identity: str, meta: dict, files: dict[str, str], entry: str) -> str:
    doc = docstring(files[entry])
    tests = sorted(f for f in files if Path(f).name.startswith("test_"))
    lines = [f"# {meta['title']}", "", meta["summary"], "", f"Identity `{identity}`, version 1.0.0, MIT licence.", "",
             "## What it measures and how", "", method_text(doc), "",
             "## Use", "", "Command line:", "", "```sh"]
    lines += [ex for ex in meta.get("examples", [])]
    lines += ["```", "", "From Python (the package directory on `sys.path`):", "", "```python",
              f"import {identity}", f"result = {identity}.run(...)  # returns a JSON-ready dict with a 'status' field",
              "```", "",
              "Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) "
              "or `error`. Missing measurements are never estimated in their place.", ""]
    if identity == "video_re_evidence_bundle":
        lines += ["## evidence.json", "",
                  "`evidence.schema.json` in this package is the JSON Schema of the file this module writes "
                  "(spec `baltor.video-evidence/v1`); every write is validated against it and problems are recorded "
                  "in `errors` and `details/_run.json`. The sibling `video_re_*` packages are found next to this one "
                  "(catalogue layout or `.baltor/lib/`), on `sys.path`, or under `VIDEO_RE_LIB`.", ""]
    lines += ["## Files", "",
              f"- `{entry}` - the module (CLI and importable functions)",
              "- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)",
              "- `video_re_synth.py` - synthetic media with known ground truth, used by the tests"]
    for f in sorted(files):
        if f.endswith(".json"):
            lines.append(f"- `{f}` - JSON Schema of evidence.json")
    lines += ["", "## Test", "", "```sh", "python3 -m pytest -q .", "```", "",
              "Tests: " + ", ".join(f"`{t}`" for t in tests) + ". They build synthetic media with ffmpeg and numpy "
              "(hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known "
              "opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped "
              "when it is absent.", "",
              "## Dependencies", ""]
    lines += [f"- `{d}`" for d in meta.get("deps", [])]
    if meta.get("optional"):
        lines += [f"- `{d}` (optional, imported or run only when present)" for d in meta["optional"]]
    if meta.get("network_note"):
        lines += ["", f"Network: {meta['network_note']}."]
    if meta.get("refs"):
        lines += ["", "## References", ""] + [f"- {r}" for r in meta["refs"]]
    lines += ["", "## Analysis boundary", "", BOUNDARY, "", "## Swarm", "", SWARM, "",
              "## Licence", "", "MIT. Original work for the Baltor public-good collection."]
    return "\n".join(lines) + "\n"


def description(meta: dict, files: dict[str, str], entry: str) -> str:
    text = method_text(docstring(files[entry]))
    tail = "\n\n" + BOUNDARY
    budget = 3990 - len(tail)
    if len(text) > budget:
        text = text[:budget].rsplit("\n", 1)[0].rstrip() + " ..."
    return text + tail


def check_schema_copy() -> None:
    bundled = MODULES / "video_re_evidence_bundle" / "evidence.schema.json"
    if bundled.read_text(encoding="utf-8") != SCHEMA.read_text(encoding="utf-8"):
        raise ValueError("modules/video_re_evidence_bundle/evidence.schema.json differs from data/video_re_measure/"
                         "evidence.schema.json; copy the canonical schema into the bundle package")
    json.loads(SCHEMA.read_text(encoding="utf-8"))


def main() -> None:
    check_schema_copy()
    common = {p.name: p.read_text(encoding="utf-8") for p in sorted(COMMON.glob("*.py"))}
    found = sorted(p.name for p in MODULES.iterdir() if (p / "meta.yaml").exists())
    if found != sorted(ORDER):
        raise ValueError(f"module set mismatch: {sorted(set(found) ^ set(ORDER))}")
    with GeneratorRun(__file__, data="generators/data/video_re_measure") as run:
        for identity in ORDER:
            pkg = MODULES / identity
            meta = yaml.safe_load((pkg / "meta.yaml").read_text(encoding="utf-8"))
            files = payload_files(pkg)
            entry = f"{identity}.py"
            if entry not in files or f"test_{identity}.py" not in files:
                raise ValueError(f"{identity}: module or test missing")
            for name, text in common.items():
                if name in files:
                    raise ValueError(f"{identity}: {name} would shadow the shared helper")
                files[name] = text
            files["README.md"] = readme(identity, meta, files, entry)
            run.component(
                "code-module", identity,
                title=meta["title"], summary=meta["summary"], description=description(meta, files, entry),
                files=files, entry=entry, subkind=meta["subkind"], domain="video", tags=meta["tags"],
                step_kinds=meta["step_kinds"], effects_=effects_for(identity, meta), depends_on=depends(meta),
                examples=meta.get("examples"),
                parameters={"swarm_stage": "load-disassemble", "evidence_spec": "baltor.video-evidence/v1"},
                review={"status": "automated-passed", "checked": CHECKED,
                        "notes": "pytest passes with Python 3.13, numpy 2.5, Pillow 12 and ffmpeg 6.1 on synthetic "
                                 "media with known ground truth; optional OCR/ASR engines were not installed, so "
                                 "their adapters were tested through fakes and parsers only."},
            )


if __name__ == "__main__":
    main()
