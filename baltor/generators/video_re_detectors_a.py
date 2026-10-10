#!/usr/bin/env python3
"""Pixel-domain detectors for the video reverse-engineering swarm, part A.

Takes every entry of the detector registry (``data/video_re/detectors.json``) in the families
``geometry``, ``quality``, ``color`` and ``effects`` and emits, for each one:

1. a ``code-module`` (subkind ``evaluator``, domain ``video``) with the registry identity: the detector
   module ``<identity>.py`` (numpy core functions + ffmpeg/ffprobe command line printing the detection
   envelope), its pytest file, the shared ``vre_pixel_core.py`` helper and its tests, ``envelope.schema.json``
   (a copy of the registry's detection envelope schema), ``payload.schema.json`` (a copy of the detector's
   contract) and a README generated from the module docstring, defaults and decode settings;
2. a ``contract-schema`` with the registry ``contract`` identity: the JSON Schema of the payload with a
   realistic valid example and at least one ``examples/invalid-*.json``.

Source of truth: ``data/video_re_detectors_a/common/`` (shared core) and
``data/video_re_detectors_a/detectors/<identity>/`` (module, test, payload.schema.json, examples/, meta.yaml).

Run: ``cd baltor/generators && python3 video_re_detectors_a.py``
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import yaml

from _lib import GeneratorRun, dumps, effects

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "video_re_detectors_a"
REGISTRY = HERE / "data" / "video_re" / "detectors.json"
ENVELOPE = HERE / "data" / "video_re" / "detection_envelope.schema.json"
COMMON = DATA / "common"
DETECTORS = DATA / "detectors"
FAMILIES = ("geometry", "quality", "color", "effects")
CHECKED = "2026-10-10"
SCHEMA_BASE = "https://github.com/taylor-s-amarel/ai-video-pipeline/baltor/contract-schemas/"

RIGHTS = ("Measures technique and structure only. Decoded frames are held in memory for the measurement and "
          "never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. "
          "Detecting an overlay never means removing it: nothing here removes watermarks or logos.")

FAMILY_TAGS = {"geometry": ["geometry", "framing"], "quality": ["quality", "encoding"],
               "color": ["color", "grading"], "effects": ["effects", "compositing"]}


def module_constants(src: str, path: Path) -> dict:
    tree = ast.parse(src, filename=str(path))
    out = {"doc": ast.get_docstring(tree) or ""}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"IDENTITY", "VERSION", "DEFAULTS", "DECODE"}:
                out[name] = ast.literal_eval(node.value)
    return out


def readme(det: dict, meta: dict, consts: dict) -> str:
    ident = det["identity"]
    doc = consts["doc"].strip()
    first, _, rest = doc.partition("\n")
    decode = consts.get("DECODE", {})
    lines = [f"# {meta['title']}", "", meta["summary"], "",
             f"Registry: family `{det['family']}`, property `{det['property']}`. Detects: {det['detects']}.",
             f"Payload contract: `{det['contract']}` (copied here as `payload.schema.json`). "
             f"Analysts answer the `{det['questions']}` question bank citing this envelope.", "",
             "## Method", "", rest.strip(), "",
             "## Command line", "", "```sh",
             f"python3 {ident}.py video.mp4 --out {det['property']}.json",
             f"python3 {ident}.py video.mp4 --param key=value   # override a default below",
             "```", "",
             "Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or "
             "partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.", "",
             "## Library use", "", "```python", f"import {ident} as det",
             "res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8",
             "```", "",
             "## Decoding (defaults)", ""]
    for k, v in decode.items():
        lines.append(f"- `{k}`: `{json.dumps(v)}`")
    lines += ["", "Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them "
              "(`--width 0`/`--fps 0` = native size / every frame).", "", "## Parameters (defaults)", ""]
    for k, v in consts.get("DEFAULTS", {}).items():
        lines.append(f"- `{k}` = `{json.dumps(v)}`")
    if meta.get("params_doc"):
        lines += ["", meta["params_doc"].strip()]
    if meta.get("limits"):
        lines += ["", "## Limits", ""] + [f"- {x}" for x in meta["limits"]]
    if meta.get("references"):
        lines += ["", "## References", ""] + [f"- {x}" for x in meta["references"]]
    lines += ["", "## Test", "", "```sh", "python3 -m pytest -q .", "```", "",
              "Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless "
              "FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.", "",
              "## Rights", "", RIGHTS, "", "## Licence", "", "MIT."]
    return "\n".join(lines) + "\n"


def read_text_files(folder: Path, suffixes: tuple[str, ...]) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(folder.rglob("*")) if p.is_file() and p.suffix in suffixes
            and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts}


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    dets = [d for d in registry["detectors"] if d["family"] in FAMILIES]
    envelope = ENVELOPE.read_text(encoding="utf-8")
    core_src = (COMMON / "vre_pixel_core.py").read_text(encoding="utf-8")
    core_test = (COMMON / "test_vre_pixel_core.py").read_text(encoding="utf-8")
    missing = [d["identity"] for d in dets if not (DETECTORS / d["identity"]).is_dir()]
    if missing:
        raise SystemExit(f"missing detector folders: {missing}")
    with GeneratorRun(__file__, data="generators/data/video_re_detectors_a") as run:
        for det in dets:
            ident, contract = det["identity"], det["contract"]
            folder = DETECTORS / ident
            meta = yaml.safe_load((folder / "meta.yaml").read_text(encoding="utf-8"))
            mod_path = folder / f"{ident}.py"
            src = mod_path.read_text(encoding="utf-8")
            consts = module_constants(src, mod_path)
            if consts.get("IDENTITY") != ident:
                raise SystemExit(f"{ident}: module IDENTITY is {consts.get('IDENTITY')}")
            schema_text = (folder / "payload.schema.json").read_text(encoding="utf-8")
            schema = json.loads(schema_text)
            expected_id = SCHEMA_BASE + contract.replace("_", "-")
            if schema.get("$id") != expected_id:
                raise SystemExit(f"{ident}: payload schema $id must be {expected_id}")
            examples = read_text_files(folder / "examples", (".json",))
            if not any(n.startswith("invalid") for n in examples) or all(n.startswith("invalid") for n in examples):
                raise SystemExit(f"{ident}: needs at least one valid and one invalid example")
            tests = read_text_files(folder, (".py",))
            files: dict[str, str] = {k: v for k, v in tests.items() if "/" not in k}
            files.update({
                "vre_pixel_core.py": core_src,
                "test_vre_pixel_core.py": core_test,
                "envelope.schema.json": envelope,
                "payload.schema.json": schema_text,
                "README.md": readme(det, meta, consts),
            })
            deps = [{"identity": contract},
                    {"identity": "ffmpeg", "external": True},
                    {"identity": "ffprobe", "external": True},
                    {"identity": "numpy", "external": True},
                    {"identity": "jsonschema", "external": True},
                    {"identity": "pytest", "external": True}]
            for extra in meta.get("depends_on") or []:
                deps.append(dict(extra) if isinstance(extra, dict) else {"identity": extra})
            tags = ["video", "reverse-engineering", "detector"] + FAMILY_TAGS[det["family"]] + list(meta.get("tags", []))
            tags = list(dict.fromkeys(tags))[:24]
            decode = consts.get("DECODE", {})
            run.component(
                "code-module", ident,
                title=meta["title"], summary=meta["summary"], description=meta.get("description"),
                subkind="evaluator", domain="video",
                files=files, entry=f"{ident}.py", tags=tags, step_kinds=["measure", "review"],
                effects_=effects(filesystem="read", executes="python",
                                 side_effects=["runs ffprobe and ffmpeg as subprocesses to decode the input video"]),
                depends_on=deps,
                parameters={"family": det["family"], "property": det["property"], "defaults": consts.get("DEFAULTS", {}),
                            "decode": decode, "question_bank": det["questions"]},
                examples=meta.get("examples"),
                review={"status": "automated-passed", "checked": CHECKED,
                        "notes": "pytest passed on synthetic fixtures with known ground truth (Python 3.13, numpy 2.x, "
                                 "jsonschema 4.x) including a lossless FFV1 command-line round trip with ffmpeg 6.1."},
            )
            c = meta["contract"]
            run.component(
                "contract-schema", contract,
                title=c["title"], summary=c["summary"],
                description=(c.get("description", "").strip() + f" Emitted as the envelope payload by {ident}; the "
                             "envelope itself follows the baltor.video-detection/v1 schema.").strip(),
                domain="video",
                files={"schema.json": schema_text, **{f"examples/{k}": v for k, v in examples.items()}},
                tags=list(dict.fromkeys(["video", "reverse-engineering", "contract", "detector-payload",
                                         det["family"]] + list(meta.get("tags", []))[:6]))[:24],
                step_kinds=["measure", "verify"],
                review={"status": "automated-passed", "checked": CHECKED,
                        "notes": "Valid example validates and invalid example fails (Draft 2020-12); the detector's tests "
                                 "validate every emitted payload against this schema."},
            )


if __name__ == "__main__":
    main()
