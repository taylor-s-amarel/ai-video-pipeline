#!/usr/bin/env python3
"""The analyst swarm of the video reverse-engineering pipeline: question banks, analysts, challengers.

A binary reverse-engineering swarm loads a binary, disassembles it, lets specialist agents answer
questions about it, has others try to refute those answers, and lifts what survives into a typed
intermediate representation. This generator builds the same roles for video:

* 18 ``rules`` packages ``video_re_questions_<lens>``: a question bank per lens (RULES.md for people
  and harnesses, questions.json for tools). Every question names what it feeds (why_it_matters), how
  to answer it from evidence.json or targeted ffmpeg extracts, the evidence it needs, the JSON pointer
  in the Video format IR it fills, the answer type, and a challenge a sceptic would run.
* 18 ``subagent`` analysts ``video_re_analyst_<lens>`` (read-only; Read, Bash for ffmpeg, Glob, Grep)
  that answer their bank as JSON conforming to the ``video_re_analyst_answer`` contract.
* 4 more subagents: ``video_re_challenger`` (refutes answers; ships a mechanical pre-pass script),
  ``video_re_lifter`` (merges answers into the IR with ``video_re_ir_merge``),
  ``video_re_parameteriser`` (parameters with evidence-justified ranges and generation rules) and
  ``video_re_round_trip_judge`` (re-measures a rendered variant and scores fidelity per dimension).
* 4 ``command`` packages: reverse_engineer_video, lift_format_from_evidence, render_from_format,
  compare_formats.

Source of truth: ``data/video_re_swarm/`` (shared.yaml, lenses.yaml, detectors_by_lens.yaml,
questions/<lens>.yaml, challenge_prepass.py). The generator checks every question against the format
IR schema (``data/video_re/format_ir.schema.json``), the evidence schema when the measurement builder
has written it (``data/video_re_measure/evidence.schema.json``) and the detector registry
(``data/video_re/detectors.json``) before writing anything.

Run: ``cd baltor/generators && python3 video_re_swarm.py``
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from _lib import GeneratorRun, agent_md, command_md, dumps, effects

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "video_re_swarm"
IR_SCHEMA = HERE / "data" / "video_re" / "format_ir.schema.json"
EVIDENCE_SCHEMA = HERE / "data" / "video_re_measure" / "evidence.schema.json"
REGISTRY = HERE / "data" / "video_re" / "detectors.json"
ANSWER_CONTRACT = HERE.parent / "components" / "contract-schemas" / "video-re-analyst-answer" / "schema.json"
CHECKED = "2026-10-10"

AGENT_HARNESSES = ["claude-code", "opencode", "baltor-harness"]
ANALYST_TOOLS = ["Read", "Bash", "Glob", "Grep"]
QUESTION_FIELDS = ("id", "question", "why", "how", "evidence", "ir_path", "type", "challenge")
MIN_Q, MAX_Q = 30, 50

# Fixed identities owned by the other builders (see the shared design); used for depends_on.
MEASURE = "video_re_evidence_bundle"
ANSWER_SCHEMA = "video_re_analyst_answer"
EVIDENCE_CONTRACT = "video_re_evidence"
FORMAT_IR = "video_re_format_ir"
IR_MERGE, IR_PARAM, IR_COMPILE, IR_DIFF, IR_VALIDATE = (
    "video_re_ir_merge", "video_re_ir_parameterise", "video_re_ir_compile_render_plan",
    "video_re_ir_diff_fidelity", "video_re_ir_validate")
PIPELINE_SKILL = "video_re_pipeline"

# --------------------------------------------------------------------------- load and check data

SHARED = yaml.safe_load((DATA / "shared.yaml").read_text(encoding="utf-8"))
LENSES = yaml.safe_load((DATA / "lenses.yaml").read_text(encoding="utf-8"))
DETECTORS = yaml.safe_load((DATA / "detectors_by_lens.yaml").read_text(encoding="utf-8"))
PREPASS = (DATA / "challenge_prepass.py").read_text(encoding="utf-8")
PREPASS_TEST = (DATA / "tests" / "test_challenge_prepass.py").read_text(encoding="utf-8")
IR = json.loads(IR_SCHEMA.read_text(encoding="utf-8"))
LENS_IDS = [lens["id"] for lens in LENSES]
BANKS: dict[str, list[dict]] = {
    lid: yaml.safe_load((DATA / "questions" / f"{lid}.yaml").read_text(encoding="utf-8")) for lid in LENS_IDS}
ALL_IDS = {q["id"] for qs in BANKS.values() for q in qs}

NUMERIC = {"number", "integer", "ratio", "seconds", "ms", "range", "distribution"}
MULTI_WRITER_TEXT = {"/visual/grade", "/visual/subject_framing", "/visual/style_family", "/script/hook_pattern"}


def kebab(identity: str) -> str:
    return identity.replace("_", "-")


def _resolve(node: dict) -> dict:
    while "$ref" in node:
        node = IR["$defs"][node["$ref"].split("/")[-1]]
    return node


def ir_target(path: str) -> tuple[str, dict | None]:
    """Classify the IR schema node an ir_path points at. Raises ValueError for paths that do not exist."""
    if not path.startswith("/"):
        raise ValueError("must start with /")
    node, ref_name = IR, None
    parts = path.strip("/").split("/")
    for i, seg in enumerate(parts):
        last = i == len(parts) - 1
        if "$ref" in node:
            ref_name = node["$ref"].split("/")[-1]
        node = _resolve(node)
        if node.get("type") == "array":
            if seg not in {"*", "-"} and not seg.isdigit():
                raise ValueError(f"segment {seg!r} indexes an array; use '*', '-' or an index")
            if seg == "-" and not last:
                raise ValueError("'-' must be the last segment")
            item = node.get("items", {})
            ref_name = item["$ref"].split("/")[-1] if "$ref" in item else None
            node = item
            if seg == "-":
                return f"append:{ref_name or node.get('type', 'any')}", node
            continue
        props = node.get("properties")
        if props is None:
            if node.get("type") == "object" or not node:
                return "free", None
            raise ValueError(f"cannot descend into {seg!r}")
        if seg not in props:
            raise ValueError(f"unknown property {seg!r}")
        ref_name = props[seg]["$ref"].split("/")[-1] if "$ref" in props[seg] else None
        node = props[seg]
    if ref_name in {"observed_number", "observed_text", "evidence", "beat", "layer", "parameter"}:
        return ref_name, node
    node = _resolve(node)
    t = node.get("type")
    if "enum" in node:
        return "enum", node
    if t == "object" and not node.get("properties"):
        return "free", node
    return str(t), node


def compatible(target: str, path: str, atype: str) -> bool:
    """Whether an answer type can fill the IR node at ``path`` (the lifter's shaping rules, see LIFTER)."""
    if atype in {"layers", "beats"} and ("/layers" in path or "/beats" in path):
        return True  # a list of layer/beat objects updates the elements it names
    if path.endswith("/motion") and "/layers/" in path:
        return True  # free-form motion description; numbers are written into the text with units
    if target == "observed_number":
        return atype in NUMERIC
    if target == "observed_text":
        return path in MULTI_WRITER_TEXT or atype in {"text", "pattern", "enum", "list"}
    if target in {"number", "integer"}:
        return atype in NUMERIC
    if target == "boolean":
        return atype == "boolean"
    if target == "string":
        return atype in {"text", "pattern", "enum", "object", "list", "integer"}
    if target == "enum":
        return atype == "enum"
    if path == "/visual/palette":
        return atype in {"palette", "color"}
    return True  # free objects, arrays and appends: the lifter shapes them (documented in the lifter)


def evidence_fields() -> set[str]:
    """Dotted evidence.json paths from the measurement builder's schema, or the agreed minimal set."""
    if EVIDENCE_SCHEMA.exists():
        schema = json.loads(EVIDENCE_SCHEMA.read_text(encoding="utf-8"))
        out: set[str] = set()

        def walk(node: dict, prefix: str) -> None:
            node = schema.get("$defs", {}).get(node["$ref"].split("/")[-1], node) if "$ref" in node else node
            for k, v in (node.get("properties") or {}).items():
                out.add(prefix + k)
                walk(v, prefix + k + ".")
            items = node.get("items")
            if isinstance(items, dict):
                walk(items, prefix)
        walk(schema, "")
        return out
    return {"source", "source.reference", "source.duration_s", "source.width", "source.height", "source.fps",
            "source.has_audio", "shots", "shots.index", "shots.start_s", "shots.end_s", "shots.duration_s",
            "shots.keyframe", "shots.palette", "shots.motion_energy", "shots.motion_energy.center",
            "shots.motion_energy.border", "shots.camera", "shots.camera.pan_x", "shots.camera.pan_y",
            "shots.camera.zoom", "shot_stats", "shot_stats.count", "shot_stats.median_s", "shot_stats.mean_s",
            "shot_stats.cut_rate_per_min", "text_regions", "text_regions.t_s", "text_regions.bbox",
            "text_regions.area_ratio", "text_regions.y_center_ratio", "captions", "captions.start_s",
            "captions.end_s", "captions.text", "audio", "audio.integrated_lufs", "audio.loudness_range",
            "audio.speech_segments", "audio.speech_segments.start_s", "audio.speech_segments.end_s",
            "audio.onsets_s", "audio.tempo_bpm", "audio.speech_wpm", "audio.cuts_on_beat_ratio", "overlay",
            "overlay.semi_transparent_ratio", "safe_area", "safe_area.violations", "tools", "errors"}


EVIDENCE_REF = re.compile(r"evidence\.([a-z_]+(?:\[[^\]]*\])?(?:\.[a-z_]+(?:\[[^\]]*\])?)*)")
RECIPE_REF = re.compile(r"\b([FA][0-9]{1,2})\b")
QID_REF = re.compile(r"\b([a-z_]+-[0-9]{3})\b")


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - {"the", "a", "an", "of", "is", "are", "and", "or", "in",
                                                          "to", "what", "does", "do", "how", "which", "it", "on"}


def check_data() -> None:
    problems: list[str] = []
    ev_fields = evidence_fields()
    registry = {d["identity"] for d in json.loads(REGISTRY.read_text())["detectors"]} if REGISTRY.exists() else None
    if len(LENS_IDS) != 18 or len(set(LENS_IDS)) != 18:
        problems.append("expected 18 distinct lenses")
    for key, dets in DETECTORS.items():
        if key not in LENS_IDS and key != "round_trip_judge":
            problems.append(f"detectors_by_lens: unknown key {key}")
        if registry is not None:
            problems += [f"detectors_by_lens.{key}: {d} not in the detector registry" for d in dets if d not in registry]
    for lens in LENSES:
        lid, qs = lens["id"], BANKS[lens["id"]]
        if not MIN_Q <= len(qs) <= MAX_Q:
            problems.append(f"{lid}: {len(qs)} questions (want {MIN_Q}-{MAX_Q})")
        for p in lens["ir_focus"]:
            try:
                ir_target(p)
            except ValueError as exc:
                problems.append(f"{lid}: ir_focus {p}: {exc}")
        seen_text: list[tuple[str, set[str]]] = []
        for n, q in enumerate(qs, 1):
            qid = q.get("id", "?")
            if qid != f"{lid}-{n:03d}":
                problems.append(f"{lid}: question {n} has id {qid}, expected {lid}-{n:03d}")
            for f in QUESTION_FIELDS:
                if not q.get(f):
                    problems.append(f"{qid}: missing {f}")
            extra = set(q) - set(QUESTION_FIELDS) - {"choices"}
            if extra:
                problems.append(f"{qid}: unknown keys {sorted(extra)}")
            if q.get("type") not in SHARED["answer_types"]:
                problems.append(f"{qid}: unknown answer type {q.get('type')}")
            if (q.get("type") == "enum") != bool(q.get("choices")):
                problems.append(f"{qid}: choices must be given exactly when type is enum")
            if q.get("choices") and len(q["choices"]) < 2:
                problems.append(f"{qid}: an enum needs at least two choices")
            if any(not isinstance(c, str) for c in q.get("choices") or []):
                problems.append(f"{qid}: every choice must be a string (quote YAML words like on/off/yes/no)")
            try:
                target, _ = ir_target(q["ir_path"])
                if not compatible(target, q["ir_path"], q["type"]):
                    problems.append(f"{qid}: answer type {q['type']} does not fit {q['ir_path']} ({target})")
            except (ValueError, KeyError) as exc:
                problems.append(f"{qid}: ir_path {q.get('ir_path')}: {exc}")
            text = " ".join(str(q.get(k, "")) for k in ("how", "challenge")) + " " + " ".join(q.get("evidence", []))
            for ref in EVIDENCE_REF.findall(text):
                dotted = re.sub(r"\[[^\]]*\]", "", ref)
                if dotted not in ev_fields:
                    problems.append(f"{qid}: evidence.{ref} is not an evidence.json field")
            for code in RECIPE_REF.findall(text):
                if code not in SHARED["recipes"]:
                    problems.append(f"{qid}: unknown recipe {code}")
            for ref in QID_REF.findall(text):
                if ref not in ALL_IDS and ref.split("-")[0] in LENS_IDS:
                    problems.append(f"{qid}: refers to unknown question {ref}")
            w = words(q.get("question", ""))
            for other, ow in seen_text:
                if w and len(w & ow) / len(w | ow) > 0.8:
                    problems.append(f"{qid}: near-duplicate of {other}")
            seen_text.append((qid, w))
    for key in DETECTORS:
        if key in LENS_IDS and not DETECTORS[key]:
            problems.append(f"{key}: no detectors listed")
    compile(PREPASS, "challenge_prepass.py", "exec")
    if problems:
        raise SystemExit("video_re_swarm data problems:\n  " + "\n  ".join(problems))


check_data()

# --------------------------------------------------------------------------- shared text blocks

BOUNDARY = SHARED["boundary"]
BOUNDARY_EXTRA = [
    "Do not identify, name or describe people (identity, age, gender, ethnicity, accent origin); describe size, "
    "position, pitch register and delivery only.",
    "Never name the source's music track, artist, creator, channel or series in an answer.",
]


def methods_md() -> str:
    lines = [f"- **{k}**: {v}" for k, v in SHARED["methods"].items()]
    lines.append("")
    lines.append("Confidence bands:")
    lines += [f"- {c}" for c in SHARED["confidence"]]
    lines.append("")
    lines.append(f"Not determinable: {SHARED['not_determinable']}")
    return "\n".join(lines)


def pointer_md() -> str:
    return "\n".join(f"- {p}" for p in SHARED["pointer_conventions"])


def types_md(used: set[str] | None = None) -> str:
    return "\n".join(f"- `{k}`: {v}" for k, v in SHARED["answer_types"].items() if used is None or k in used)


def recipes_md(codes: set[str] | None = None) -> str:
    keys = [k for k in SHARED["recipes"] if codes is None or k in codes]
    head = ("Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. "
            "Frames and images you write can be inspected with the Read tool.")
    return head + "\n\n" + "\n".join(f"- **{k}** {SHARED['recipes'][k]}" for k in keys)


def used_recipes(qs: list[dict]) -> set[str]:
    codes: set[str] = set()
    for q in qs:
        codes.update(RECIPE_REF.findall(" ".join([q["how"], q["challenge"], " ".join(q["evidence"])])))
    return codes


def example_value(atype: str, choices: list | None):
    return {
        "number": {"value": 1.5, "unit": "s"}, "integer": {"value": 4}, "ratio": {"value": 0.5},
        "seconds": {"value": 2.0, "unit": "s"}, "ms": {"value": -40, "unit": "ms"},
        "range": {"value": 4, "min": 3, "max": 6, "unit": "items"},
        "distribution": {"median": 2.0, "p10": 1.0, "p90": 3.5, "n": 20, "unit": "s"},
        "boolean": True, "enum": (choices or ["a"])[0], "color": "#336699", "palette": ["#336699", "#F2F2F2"],
        "text": "short technique description with the numbers behind it",
        "pattern": "{label} {n}: {number} {unit}", "list": ["kind-a", "kind-b"], "timestamps": [1.0, 2.5],
        "segments": [{"start_s": 1.0, "end_s": 2.5, "label": "role"}],
        "beats": [{"role": "hook", "start_ratio": 0.0, "end_ratio": 0.1}],
        "layers": [{"z": 0, "kind": "background-video", "opacity": 0.9}],
        "parameter": {"name": "n_items", "type": "integer", "description": "number of repeated item beats",
                      "default": 4, "min": 3, "max": 6, "derived_from": "structure_beats-002"},
        "rule": "item_s = (target_duration_s - intro_s - outro_s) / n_items",
        "object": {"key": "value"},
    }[atype]


def example_answers(lens: str) -> str:
    q = BANKS[lens][0]
    lens_meta = next(x for x in LENSES if x["id"] == lens)
    tool = next((m.group(1) for e in lens_meta["evidence"] for m in [re.search(r"\((video_re_[a-z_]+)", e)] if m),
                "recipe F1")
    shaped = {"lens": lens, "question_id": q["id"], "answer": example_value(q["type"], q.get("choices")),
              "ir_path": q["ir_path"],
              "evidence": {"method": "measured", "confidence": 0.85, "timestamps_s": [0.0, 12.4],
                           "tool": tool, "note": "the evidence fields and numbers behind the answer"}}
    q2 = BANKS[lens][1]
    nd = {"lens": lens, "question_id": q2["id"], "answer": "not determinable", "ir_path": q2["ir_path"],
          "evidence": {"method": "assumed", "confidence": 0, "note": "which evidence was missing, e.g. a null field and its errors[] entry"}}
    return json.dumps([shaped, nd], indent=2, ensure_ascii=False)


def ir_paths_md(qs: list[dict]) -> str:
    counts: dict[str, int] = {}
    for q in qs:
        counts[q["ir_path"]] = counts.get(q["ir_path"], 0) + 1
    return "\n".join(f"- `{p}` ({n})" for p, n in sorted(counts.items()))


def detectors_md(key: str) -> str:
    dets = DETECTORS.get(key, [])
    return ", ".join(f"`{d}`" for d in dets) if dets else "none listed"


# --------------------------------------------------------------------------- rules (question banks)

def rules_md(lens: dict) -> str:
    lid, qs = lens["id"], BANKS[lens["id"]]
    used_types = {q["type"] for q in qs}
    out = [f"# Video RE question bank: {lens['title']}", "",
           f"Lens `{lid}` · {len(qs)} questions · answers follow the `{ANSWER_SCHEMA}` contract and fill the "
           f"`{FORMAT_IR}` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the "
           f"`{kebab('video_re_analyst_' + lid)}` subagent and challenged by `video-re-challenger`.", "",
           lens["purpose"], "",
           "## Rules for every answer", "",
           f"1. Boundary: {BOUNDARY}",
           f"2. {BOUNDARY_EXTRA[0]}",
           f"3. {BOUNDARY_EXTRA[1]}",
           "4. Cite evidence for every answer: method, confidence, the timestamps you used, the tool or recipe for "
           "measured values, and a note with the numbers behind the answer (at most 400 characters).",
           "5. Shape the answer by its answer type and write it to the question's ir_path exactly as given.",
           "6. Say 'not determinable' instead of guessing. A missing measurement is null with an errors[] entry in "
           "evidence.json, never zero.",
           "7. State observations, not taste: 'engaging' or 'cinematic' is not an answer; the measurement behind "
           "it is. Effects on viewers (retention, virality) are not observable from one video.",
           "8. A claim about every item, shot or caption needs at least 3 checked instances (or all of them when "
           "there are fewer).", "",
           "## Methods and confidence", "", methods_md(), "",
           "## IR pointer conventions", "", pointer_md(), "",
           "## Answer types used here", "", types_md(used_types), "",
           "## Evidence this lens leans on", "", "\n".join(f"- {e}" for e in lens["evidence"]), "",
           f"Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: {detectors_md(lid)}. "
           "Treat their results as measured evidence and cite the detector as the tool.", "",
           "## What to inspect beyond evidence.json", "", lens["inspect"], "",
           "## Pitfalls challengers check first", "", "\n".join(f"- {p}" for p in lens["pitfalls"]), "",
           "## Parameters this lens usually proposes", "", "\n".join(f"- {p}" for p in lens["parameter_hints"]), "",
           "## IR paths this lens writes", "", ir_paths_md(qs), "",
           f"## Questions ({len(qs)})", ""]
    for q in qs:
        out.append(f"### {q['id']} · `{q['type']}` → `{q['ir_path']}`")
        out.append("")
        out.append(f"**{q['question']}**")
        out.append("")
        if q.get("choices"):
            out.append(f"- Choices: {', '.join(f'`{c}`' for c in q['choices'])}")
        out.append(f"- Why it matters: {q['why']}")
        out.append(f"- How to answer: {q['how']}")
        out.append(f"- Evidence required: {'; '.join(q['evidence'])}")
        out.append(f"- Challenge: {q['challenge']}")
        out.append("")
    out += ["## Recipes referenced above", "", recipes_md(used_recipes(qs)), "",
            "## Machine-readable bank", "",
            "Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this "
            "package.", "", "<!-- machine-readable bank -->", "```json",
            json.dumps([{"id": q["id"], "ir_path": q["ir_path"], "answer_type": q["type"],
                         **({"choices": q["choices"]} if q.get("choices") else {})} for q in qs],
                       ensure_ascii=False), "```", ""]
    return "\n".join(out)


def questions_json(lens: dict) -> dict:
    qs = BANKS[lens["id"]]
    used = {q["type"] for q in qs}
    return {
        "spec": "baltor.video-re-questions/v1",
        "lens": lens["id"], "title": lens["title"], "purpose": lens["purpose"],
        "boundary": BOUNDARY, "answer_contract": ANSWER_SCHEMA, "ir_contract": FORMAT_IR,
        "ir_focus": lens["ir_focus"], "evidence": lens["evidence"], "inspect": lens["inspect"],
        "pitfalls": lens["pitfalls"], "parameter_hints": lens["parameter_hints"],
        "optional_detectors": DETECTORS.get(lens["id"], []),
        "methods": SHARED["methods"], "pointer_conventions": SHARED["pointer_conventions"],
        "answer_types": {k: v for k, v in SHARED["answer_types"].items() if k in used},
        "recipes": {k: SHARED["recipes"][k] for k in SHARED["recipes"] if k in used_recipes(qs)},
        "questions": [{
            "id": q["id"], "question": q["question"], "why_it_matters": q["why"], "how_to_answer": q["how"],
            "evidence_required": q["evidence"], "ir_path": q["ir_path"], "answer_type": q["type"],
            **({"choices": q["choices"]} if q.get("choices") else {}), "challenge": q["challenge"],
        } for q in qs],
    }


# --------------------------------------------------------------------------- analyst subagents

def analyst_body(lens: dict) -> str:
    lid, qs = lens["id"], BANKS[lens["id"]]
    bank_lines = []
    for i, q in enumerate(qs, 1):
        choices = f" Choices: {', '.join(q['choices'])}." if q.get("choices") else ""
        bank_lines.append(f"{i}. `{q['id']}` [{q['type']} → `{q['ir_path']}`] {q['question']}{choices}\n"
                          f"   How: {q['how']}")
    return f"""
# Video RE analyst: {lens['title']}

You are the **{lens['title']}** analyst in a swarm that reverse-engineers one video into a reusable,
parametric format: the Video format IR (contract `{FORMAT_IR}`). Measurement tools have already turned
the video into hard evidence. Your job is to answer this lens's question bank from that evidence, cite
the evidence for every answer, and say "not determinable" where it runs out. A challenger will try to
refute each answer, so make every answer checkable.

Lens purpose: {lens['purpose']}

## Boundary (applies to every answer)

- {BOUNDARY}
- {BOUNDARY_EXTRA[0]}
- {BOUNDARY_EXTRA[1]}
- You are read-only: never edit evidence.json, the source or other analysts' files. Write only inside `$WORK`
  and to `$OUT` when one is given.

## Inputs

- `EVIDENCE`: path to `evidence.json` (contract `{EVIDENCE_CONTRACT}`, spec `baltor.video-evidence/v1`, written by
  `{MEASURE}`), plus its `details/` folder when present. Read `errors[]` first: a null field with an error
  entry is a missing measurement, not a zero.
- `SRC`: the source video, for targeted extraction with the recipes below only.
- `WORK`: a scratch directory for frames, crops and spectrograms. Delete it when you finish; never copy its
  files anywhere else.
- Keyframes and the contact sheet referenced by `evidence.shots[].keyframe` (paths relative to evidence.json).
- Optional: other lenses' answers (read-only, for cross-checks) and detector envelopes (spec
  `baltor.video-detection/v1`) from these registry detectors when they are installed: {detectors_md(lid)}.
  Their results count as measured evidence; cite the detector as the tool.
- Captions: when `evidence.captions[]` holds masked text (`Word {{n}} word`), answer from word shapes, counts
  and numbers; when it holds full text, read it only to count and classify, and never write it out.

## Procedure

1. Read evidence.json (`source`, `shot_stats`, `errors`, `tools`) and list which fields your questions need are
   null. Those questions are "not determinable" unless a recipe below can measure them.
2. Work through the bank in order. Follow each question's *How*: evidence.json fields first, then the recipes.
   Look at every frame, crop, scope or spectrogram you extract with the Read tool before describing it.
3. For each answer record the method, a confidence inside the method's band, the timestamps you used, the tool
   or recipe, and a note with the numbers behind the answer.
4. Shape the answer by its answer type and write it to the question's `ir_path` exactly as given.
5. Before returning, re-read your answers: no copied text, no taste words presented as fact, no "all/every/
   always" without at least 3 checked instances, every timestamp inside 0..duration.
6. Delete `$WORK`.

## Methods and confidence

{methods_md()}

## Answer types

{types_md()}

## IR pointer conventions

{pointer_md()}

## Recipes

{recipes_md()}

## Output

Return one JSON array with exactly one object per question, in bank order, conforming to the
`{ANSWER_SCHEMA}` contract (fields `lens`, `question_id`, `answer`, `ir_path`, `evidence` with `method`,
`confidence`, `timestamps_s`, `tool`, `note`). Write it to `$OUT` when given, otherwise print only the array.
The values below show the shape only:

```json
{example_answers(lid)}
```

## Pitfalls challengers check first

{chr(10).join(f"- {p}" for p in lens['pitfalls'])}

## Question bank ({len(qs)})

The full bank (why each question matters, evidence required, challenge prompts) is the rules package
`video_re_questions_{lid}`, placed at `.baltor/rules/{kebab('video_re_questions_' + lid)}.md`. Read it when
it is there; the questions are repeated here so you can work without it.

{chr(10).join(bank_lines)}
"""


def analyst_description(lens: dict) -> str:
    return (f"Use in the video reverse-engineering swarm to answer the {lens['title'].lower()} question bank "
            f"({len(BANKS[lens['id']])} questions) for one analysed video from its evidence.json, keyframes and "
            "targeted ffmpeg extracts. Returns cited JSON answers for the challenger and lifter. Read-only; never "
            "copies source footage, music, voice or script text.")


# --------------------------------------------------------------------------- challenger, lifter, parameteriser, judge

CROSS_CHECKS = [
    ("structure_beats-001", "hook_first_seconds-027", "where the body starts"),
    ("structure_beats-031", "transitions_effects-020", "how the video ends"),
    ("structure_beats-010", "retention_cta-030", "dead tail versus end card"),
    ("hook_first_seconds-002", "typography_captions-021", "title position"),
    ("hook_first_seconds-016", "typography_captions-019", "title colour"),
    ("hook_first_seconds-015", "text_animation-006", "title entrance"),
    ("narration_voice-004", "script_rhetoric-015", "speaking rate and word count"),
    ("narration_voice-013", "music_sfx_mix-004", "music level under the voice"),
    ("typography_captions-011", "text_animation-005", "caption and keyword sync"),
    ("transitions_effects-018", "pacing_cut_rhythm-022", "share of non-cut transitions"),
    ("background_system-003", "layers_compositing-024", "which layers move"),
    ("camera_motion-011", "shot_list_framing-007", "filmed versus virtual motion and material kinds"),
    ("layers_compositing-009", "typography_captions-008", "frosted or solid text backing"),
    ("color_grade-001", "background_system-005", "palette versus background colours"),
    ("retention_cta-005", "script_rhetoric-021", "call to action versus closing line"),
    ("music_sfx_mix-011", "transitions_effects-008", "sound effects at transitions"),
    ("characters_animation_style-001", "layers_compositing-031", "style family and 2.5D"),
    ("platform_fit_safe_areas-005", "typography_captions-032", "text in the bottom band"),
    ("pacing_cut_rhythm-001", "structure_beats-011", "median shot length versus shots per item"),
]
for a, b, _ in CROSS_CHECKS:
    assert a in ALL_IDS and b in ALL_IDS, (a, b)


def path_owners_md() -> str:
    rows = []
    for lens in LENSES:
        rows.append(f"- `{lens['id']}`: {', '.join(f'`{p}`' for p in lens['ir_focus'])}")
    return "\n".join(rows)


CHALLENGER = f"""
# Video RE challenger

You try to refute the answers of the video reverse-engineering analysts before they are lifted into the
Video format IR. Be adversarial but fair: an answer survives when its evidence holds up, with its
confidence set to what the evidence supports. You never add new answers; you uphold, lower or reject.
The swarm runs one challenger per lens and then one cross-lens pass over all surviving answers.

## Boundary

- {BOUNDARY}
- {BOUNDARY_EXTRA[0]}
- {BOUNDARY_EXTRA[1]}
- Reject any answer that breaks the boundary, whatever its other merits. You are read-only apart from `$WORK`
  and `$OUT`.

## Inputs

- `ANSWERS`: a JSON array of analyst answers (contract `{ANSWER_SCHEMA}`): one lens, or all lenses for the
  cross-lens pass.
- `EVIDENCE`: evidence.json (contract `{EVIDENCE_CONTRACT}`) and its `details/`; `SRC` for re-measurement;
  `WORK` for scratch files.
- `BANK`: the question banks, i.e. the `video_re_questions_<lens>` rules placed at `.baltor/rules/` (or their
  `questions.json`). Every question carries its own challenge prompt.

## Step 1: mechanical pre-pass

Write the script at the end of this file to `$WORK/challenge_prepass.py` and run:

```
python3 $WORK/challenge_prepass.py "$ANSWERS" --evidence "$EVIDENCE" --bank .baltor/rules --out $WORK/prepass.json
```

It checks required fields, method and confidence bands, timestamps inside the video, ir_path and answer shape
against the bank, quotes longer than 6 words, 7-word overlaps with the source captions, taste words, absolute
claims with few timestamps and identity words. Rows marked `reject` are rejected unless the script is plainly
wrong (say why in the note). Rows marked `flag` must be resolved in step 2.

## Step 2: challenge each answer

Challenge every flagged answer, every answer with confidence 0.8 or more, every answer that feeds
`/parameters` or `/generation_rules`, and at least one in three of the rest:

1. Run the question's own challenge prompt from the bank.
2. Timestamps: each cited time must sit inside the shot, speech segment or text sample the answer talks about
   (`shots[]`, `audio.speech_segments`, `text_regions[].t_s`). Extract one cited frame
   (`ffmpeg -v error -ss T -i "$SRC" -frames:v 1 "$WORK/c_T.jpg"`) and confirm the claim is visible.
3. Measured values: recompute from the cited evidence field (a python one-liner over evidence.json). Tolerance
   is 5% for counts and times and 10% for derived rates; beyond it, lower confidence by at least 0.3, or reject
   when the answer is that number.
4. Method honesty: `measured` needs a tool and a field or filter output; looking at frames is `observed`;
   reasoning is `inferred`. Relabel and cap the confidence at the new method's band.
5. Over-generalisation: a claim about all items, shots or captions must hold on 3 instances you check (or all
   of them when there are fewer). One counter-example lowers the answer and narrows its scope in the note, or
   rejects it when the generalisation is the answer.
6. Taste presented as fact ('engaging', 'cinematic', 'premium', 'works') is rejected unless the note gives a
   measurable restatement you can verify. Claims about effects on viewers are never observable from one video.
7. Chance alignment: for 'X lines up with Y' answers (cuts on beats, effects on onsets), compute the chance
   rate (events per second × window width × 2). A share not clearly above chance is lowered to 0.4 or less.
8. Tool limits: shot detection misses dissolves and double-triggers on flashes; speech segments come from an
   energy heuristic (music with vocals counts as speech); text regions are edge-density proposals sampled
   about twice per second; tempo estimates can be doubled or halved; side-channel loudness means nothing on a
   mono source; camera.zoom is a log rate per second. An answer that ignores a relevant limit is lowered.
9. Rights: copied text, identity descriptions, named tracks or creators, or a parameter that points at source
   media are rejected.

## Step 3: cross-lens consistency (all-lens pass)

Compare these pairs and settle conflicts by evidence quality (method, then re-measurement), not by vote:

{chr(10).join(f"- `{a}` vs `{b}`: {why}" for a, b, why in CROSS_CHECKS)}
- `rights_originality_boundary-017` and `-018` against every answer: no copied words, no source media paths.

## Confidence changes

- Upheld after a re-measurement agrees: keep it; you may raise it by at most 0.05, never above the method cap.
- Upheld without re-measurement: keep it, capped at the method band.
- Lowered: subtract 0.1 to 0.4 by severity and append `[challenge: lowered from X: reason]` to evidence.note,
  shortening the original note so the whole note stays within 400 characters.
- Rejected: removed from `surviving` and listed with reasons; the lifter turns it into an open question.

## Output

Write `$OUT` (or print) one JSON object:

```json
{{"spec": "baltor.video-re-challenge/v1",
  "surviving": [{{"lens": "...", "question_id": "...", "answer": "...", "ir_path": "...", "evidence": {{"method": "...", "confidence": 0.6, "timestamps_s": [], "tool": "...", "note": "... [challenge: lowered from 0.8: reason]"}}}}],
  "rejected": [{{"answer": {{}}, "reasons": ["..."]}}],
  "cross_checks": [{{"question_ids": ["...", "..."], "result": "consistent", "note": "..."}}],
  "summary": {{"answers": 0, "upheld": 0, "lowered": 0, "rejected": 0, "re_measured": 0}}}}
```

`surviving` keeps the `{ANSWER_SCHEMA}` shape exactly, so the lifter can pass it to `{IR_MERGE}` unchanged.

## Pre-pass script (`challenge_prepass.py`, standard library only)

```python
{PREPASS.rstrip()}
```
"""

LIFTER = f"""
# Video RE lifter

You merge the answers that survived the challengers into one Video format IR (contract `{FORMAT_IR}`, spec
`baltor.video-format-ir/v1`), the way a decompiler lifts verified facts into a typed intermediate
representation. You do not analyse the video again and you never invent a value.

## Boundary

- {BOUNDARY}
- The IR stores technique and structure only: no file paths to frames, crops or source media, no names of
  tracks, people, channels or series, no quoted narration.

## Inputs

- `SURVIVING`: the challenger outputs (their `surviving` and `rejected` arrays) for every lens, plus the
  cross-lens pass.
- `EVIDENCE`: evidence.json (for `source` fields and to double-check numbers).
- `PRIOR_IR` (optional): an earlier IR of the same source to update.
- `OUT`: the output directory.

## Steps

1. Collect every surviving answer into `$OUT/answers.surviving.json` (one array) and count them per lens.
2. Group answers by `ir_path`. When several answers write the same scalar path, keep, in order of preference:
   (a) the stronger method (measured > observed > inferred > assumed), (b) the higher confidence, (c) the lens
   that owns the path (table below). Record each overruled alternative that differs materially in
   `open_questions` as `conflict at <path>: <kept> vs <other> (<question ids>)`.
3. Paths ending in `/-` append (drop exact duplicates). Paths with `*` apply to the array elements the answer
   names (for example beats whose role is `item`); when the scope is unclear, move the answer to
   `open_questions` instead of guessing.
4. Shape values:
   - numeric answers (number, integer, ratio, seconds, ms, range, distribution) become `observed_number`
     `{{value, unit, min, max, evidence}}` (a distribution's median is the value; p10/p90 become min/max);
   - text, pattern and enum answers become `observed_text` `{{value, evidence}}`;
   - the multi-writer fields `/visual/grade`, `/visual/subject_framing`, `/visual/style_family` and
     `/script/hook_pattern` join their parts as `key: value; ...` in one `observed_text` whose method is the
     weakest contributor's and whose confidence is the mean;
   - answers of other types appended to `observed_text` arrays become a short `topic: value` string with the
     answer's evidence;
   - `/visual/layers/-` answers become layer objects (`z`, `kind`, `opacity`, ...); a `false` answer adds no layer;
   - answers to `/parameters/-` and non-rule answers to `/generation_rules/-` are proposals: write them to
     `$OUT/proposals.json` for the parameteriser; only `rule` answers go straight into `generation_rules`.
5. Merge with the `{IR_MERGE}` code module (placed at `.baltor/lib/{kebab(IR_MERGE)}/`). Run its CLI with
   `--help` first and pass the surviving answers and evidence the way it asks; then apply the decisions from
   steps 2-4 that it leaves open.
6. Fill the required fields honestly: `spec`, `format_id` (kebab case, describes the technique, never the
   source's name), `source` (`reference`, `duration_s`, `resolution`, `fps`, `rights_note` from
   `rights_originality_boundary-001`), `parameters` (at least one), `timeline` (`target_duration_s`, `beats`),
   `visual.layers`, `typography`, `motion`, `audio` and `generation_rules` (at least one). A required value with
   no surviving answer gets method `assumed`, confidence 0.3 or lower, and an open question naming it.
7. Every 'not determinable' answer and every rejected answer becomes an `open_questions` entry:
   `<question_id>: <reason>`.
8. Validate with `{IR_VALIDATE}` (`.baltor/lib/{kebab(IR_VALIDATE)}/`, `--help` first). Then scan the IR for the
   boundary: quoted strings over 6 words, file paths to frames or media, names of tracks, people or channels.
   Fix and re-validate until both pass.
9. Write `$OUT/format_ir.json` and `$OUT/lift_report.json`:
   `{{"answers_in": n, "answers_used": n, "conflicts": [...], "proposals": n, "open_questions": n, "validation": "ok"}}`.

## Path ownership (tie-breaker in step 2)

{path_owners_md()}
"""

PARAMETERISER = f"""
# Video RE parameteriser

You turn a lifted IR from a description of one video into a format that can generate many: typed
parameters with ranges justified by evidence, and procedural `generation_rules` written in those
parameters, so one video becomes a reusable, parametric format.

## Boundary

- {BOUNDARY}
- Content slots (title text, hero images, script lines, music, voice) are parameters whose default is empty
  or generic, never the source's value.

## Inputs

- `IR`: `$OUT/format_ir.json` from the lifter; `PROPOSALS`: `$OUT/proposals.json`.
- `ANSWERS`: the surviving answers; `EVIDENCE`: evidence.json.

## Steps

1. Inventory what repeats and what varies: `structure_beats-013`, `structure_beats-032`,
   `layers_compositing-027`, and every proposal written to `/parameters/-`.
2. Write one IR parameter object per candidate: `name` (snake_case), `type` (string, integer, number,
   boolean, enum, color, duration_s, asset, list), `description` (what it controls; asset slots say they need a
   licence), `default`, `min`/`max` or `choices`, and `derived_from` (the question ids).
3. Justify every range from evidence, and say which kind it is in the description:
   - observed spread: variation inside the video (p10-p90 or min-max across items or shots);
   - structural derivation: a range implied by a formula, shown in the description (for example the n_items
     range from the shortest and longest item beats, `structure_beats-023`);
   - anything wider than the evidence is marked 'assumed'. Never widen a range silently.
4. Identity elements of the source (`rights_originality_boundary-010` and `-029`) get defaults that differ from
   the source, and the description says why.
5. Rewrite observations and proposals as generation rules of at most 400 characters each, in parameter names,
   ordered timeline → visuals → text → motion → audio. The form looks like this (your numbers come from the
   answers): `item_s = (target_duration_s - intro_s - outro_s) / n_items`; `label 'FACT {{n}}' pops at
   item_start + label_lead_s`; `shots per item = ceil(item_s / target_median_shot_s); zoom alternates in and out
   at zoom_per_s, centred on the subject`.
6. Reproduction check: set every parameter to its observed value, recompute beat times, shot counts and caption
   timings from the rules, and compare them with evidence.json (`shots[]`, `audio.speech_segments`,
   `text_regions[]`). Report the largest error per rule. A timeline rule off by more than 1 s, or a count rule off
   by more than 25%, is revised or marked approximate in the rule text.
7. Run `{IR_PARAM}` (`.baltor/lib/{kebab(IR_PARAM)}/`, `--help` first) for the mechanical part (beat ratios,
   parameter typing) and reconcile its output with yours.
8. Bind to a renderer: `render_binding.target_schema = "short_video_spec"` and `render_binding.mapping` from
   spec fields to parameters (for example `title_hook.text` ← `title_text`, `scenes[]` ← beats with role item,
   `scenes[].label` ← the label pattern, `captions` ← narration word timings, `narration.words_per_minute` ←
   `words_per_minute`, `music` ← `music_track`). That schema requires 60-180 s, layers at 98% opacity or less and
   labels of the form `FACT|TIP|STEP N`; add an open question wherever the source format conflicts with it and
   say how the binding resolves the conflict.
9. Validate with `{IR_VALIDATE}` and write the IR back, plus `$OUT/parameterise_report.json`:
   `{{"parameters": n, "rules": n, "reproduction_errors": {{}}, "assumed_ranges": [...], "binding_conflicts": [...]}}`.
"""

JUDGE = f"""
# Video RE round-trip judge

You close the loop. A format IR is only as good as the videos it regenerates: render a variant with new
content, run the same measurement and swarm on it, and compare the two IRs. You score fidelity per
dimension, check that the variant is original, propose IR fixes, and decide whether to iterate.

## Boundary

- {BOUNDARY}
- The variant must be original: it never contains the source's frames, music, voice or script text.

## Inputs

- `SOURCE_IR`, the source `EVIDENCE`, the rendered `VARIANT` (mp4) and optionally `VARIANT_IR`.
- `ROUND` (iteration number), `HISTORY` (earlier round reports), `WORK`, and the optional stop settings
  `min_gain`, `max_rounds`, `target`.

## Steps

1. Measure the variant with `{MEASURE}` using the same settings as the source run (record them).
2. Lift the variant when `VARIANT_IR` is missing: run the analysts restricted to questions answerable from
   evidence.json and recipes, the challenger and the lifter, exactly as for the source.
3. Score with `{IR_DIFF}` (`.baltor/lib/{kebab(IR_DIFF)}/`, `--help` first) on `SOURCE_IR` and `VARIANT_IR`.
   Dimensions: timeline, cut rhythm, layers, typography, motion, audio, script pattern. When installed, the
   registry detectors {detectors_md('round_trip_judge')} add measured comparisons.
4. Separate format deviations from content differences. New photos change palette and framing; a new topic
   changes the words. A difference counts against fidelity only where the IR fixes or bounds that property
   (a parameter range or a generation rule) and the variant falls outside it.
5. Originality gate: compare variant keyframes with source keyframes (SSIM 0.9 or more, or near-duplicate
   perceptual hashes, fails), variant captions with source captions (no shared 7-word run), and the audio (no
   source music or voice). Any failure stops the loop and is reported; do not score that variant.
6. Diagnose the two lowest dimensions: find the IR element responsible (a parameter default or range, a
   generation rule, a missing layer) by comparing the specific measurements, for example a variant median shot
   of 3.4 s against the source's 2.1 s points at the shots-per-item rule or `target_median_shot_s`.
7. Propose fixes as RFC 6902 JSON Patch operations on `SOURCE_IR`, each with the measurement behind it and the
   expected effect. Never patch in source content.
8. Stop when the overall score improved by less than `min_gain` (default 0.02) over the last two rounds, when
   `max_rounds` (default 5) is reached, or when every dimension reaches `target` (default 0.9). These defaults are
   this swarm's conventions, not industry standards; the run may override them.
9. Record `fidelity` (`score`, `by_dimension`, `variant_reference`) in the IR through a patch and write
   `$WORK/round_<n>_report.json`:
   `{{"round": n, "scores": {{}}, "deltas": {{}}, "originality": "pass", "patches": [], "stop": false, "reason": "..."}}`.
"""

# --------------------------------------------------------------------------- commands

LENS_LIST = ", ".join(f"`{kebab('video_re_analyst_' + lid)}`" for lid in LENS_IDS)

CMD_REVERSE = f"""
Reverse-engineer this video into a reusable, parametric format: $ARGUMENTS

Arguments: a local video file (required); optional `--lenses` (default: all 18), `--out DIR` (default
`video_re/<file stem>`), `--text-mode masked|full` (default masked).

Boundary: {BOUNDARY}

0. Preflight. Check the file exists and that the user supplied it or may analyse it. Do not download anything:
   if only a URL was given, ask for the file. Never upload or republish the source.
1. Measure (load and disassemble). Run the `{MEASURE}` code module (`.baltor/lib/{kebab(MEASURE)}/`, `--help`
   for its options) on the file, with caption text masked unless the user asked for full text, writing
   `OUT/evidence/evidence.json`, keyframes and the contact sheet. Report every `errors[]` entry.
2. Analyse. Start one subagent per lens, in parallel, each with `EVIDENCE`, `SRC`, `WORK=OUT/work/<lens>` and
   `OUT=OUT/answers/<lens>.json`: {LENS_LIST}.
3. Challenge. Run `video-re-challenger` on each lens's answers in parallel (`OUT/challenge/<lens>.json`), then
   once over all surviving answers for the cross-lens checks (`OUT/challenge/cross.json`).
4. Lift. Run `video-re-lifter` on the surviving answers: `OUT/format_ir.json`, `OUT/lift_report.json`.
5. Parameterise. Run `video-re-parameteriser`: updated `OUT/format_ir.json`, `OUT/parameterise_report.json`.
6. Validate with `{IR_VALIDATE}`; fix until it reports no errors.
7. Delete `OUT/work` (frames, crops, spectrograms) unless the user asked to keep it for review. It never goes
   into the IR.
8. Report: format_id, beats, parameters with ranges, the number of generation rules, open questions, the
   measurements that were missing, and the next step (`/render-from-format`, then `/compare-formats`).

The `{PIPELINE_SKILL}` skill ships a `workflow.js` that runs this same fan-out automatically.
"""

CMD_LIFT = f"""
Lift a reusable format from an existing evidence bundle: $ARGUMENTS

Arguments: `evidence.json` (required); optional answers directory with `<lens>.json` files already produced;
`--src VIDEO` for analysts that need frame extraction; `--out DIR` (default: next to evidence.json).

Boundary: {BOUNDARY}

1. Read evidence.json and its `errors[]`. Without `--src`, tell each analyst that recipes needing the video are
   unavailable, so those questions become "not determinable" rather than guesses.
2. Run the analysts whose answer files are missing ({LENS_LIST}), in parallel.
3. Run `video-re-challenger` per lens, then the cross-lens pass.
4. Run `video-re-lifter`, then `video-re-parameteriser`; validate with `{IR_VALIDATE}`.
5. Report what changed against any earlier `format_ir.json` in `--out` (parameters, rules, open questions).
"""

CMD_RENDER = f"""
Render a new video from a lifted format: $ARGUMENTS

Arguments: `format_ir.json` (required) and either `content.json` (values for the IR's content parameters) or a
topic; optional `--out DIR`.

Boundary: {BOUNDARY} The render uses only new or licensed assets.

1. Read the IR: parameters, beats with their `content_slot`, generation rules and `render_binding`. List the
   content parameters that need values.
2. Content. With `content.json`, check every required content parameter is filled. With a topic, research
   facts with numbers and a source URL for each (the IR's `script.claims_need_sources`), write the script to
   the IR's word budgets and patterns, and pick licensed or original images, music and a local TTS voice.
   Never reuse the source's assets, words or voice.
3. Compile with `{IR_COMPILE}` (`.baltor/lib/{kebab(IR_COMPILE)}/`, `--help` first) into a render plan bound to
   the `short_video_spec` contract schema; validate the plan against that schema.
4. Check the plan with the house-style skill's `scripts/check_rules.py` when the project uses it.
5. Render with the project's renderer (ffmpeg or the pipeline's composer), time captions from the narration's
   word timings and never time-stretch speech to fit.
6. QA the export with the `mp4_qa_probe` code module and fix failures before delivering.
7. Deliver the full MP4 with its render plan, sources and credits. Next: `/compare-formats` for the round trip.
"""

CMD_COMPARE = f"""
Compare a variant with its source format and propose fixes: $ARGUMENTS

Arguments: the source `format_ir.json` and either a rendered variant (mp4) or its `format_ir.json`; optional
`--round N` and `--history DIR`.

Boundary: {BOUNDARY}

1. Run `video-re-round-trip-judge` with `SOURCE_IR`, the variant and the history. It measures the variant with
   `{MEASURE}`, lifts it with the same swarm when needed, scores it with `{IR_DIFF}` per dimension (timeline,
   cut rhythm, layers, typography, motion, audio, script pattern) and checks originality.
2. Show the per-dimension scores, the change from the previous round, the originality result and the proposed
   JSON Patch fixes with their evidence.
3. If the judge says continue, apply the patches the user accepts to the IR, validate with `{IR_VALIDATE}`,
   re-render with `/render-from-format` and compare again. Stop when the judge's stop rule says fidelity has
   stopped improving.
"""

# --------------------------------------------------------------------------- write components

TAGS = ["video", "reverse-engineering", "video-re", "swarm"]
DESCRIPTION_BOUNDARY = ("Captures technique and structure only; never stores or reuses the source's footage, "
                        "frames, music, voice or script text.")


def lens_tag(lid: str) -> str:
    return kebab(lid)[:40]


with GeneratorRun(__file__, data="generators/data/video_re_swarm") as run:
    total = sum(len(v) for v in BANKS.values())
    for lens in LENSES:
        lid, qs = lens["id"], BANKS[lens["id"]]
        rules_id = f"video_re_questions_{lid}"
        run.component(
            "rules", rules_id,
            title=f"Video RE question bank: {lens['title']}",
            summary=(f"{len(qs)} answerable questions for reverse-engineering a video's {lens['title'].lower()}, "
                     "each with evidence to cite, the format-IR pointer it fills and a challenge prompt.")[:240],
            description=(f"{lens['purpose']} Every question says why it matters, how to answer it from evidence.json "
                         "or targeted ffmpeg extracts, the evidence required, the JSON pointer it fills in the Video "
                         "format IR, the answer type and how a sceptic would test the answer. " + DESCRIPTION_BOUNDARY),
            subkind="review-lens", domain="video",
            files={"RULES.md": rules_md(lens), "questions.json": dumps(questions_json(lens))},
            tags=TAGS + ["question-bank", lens_tag(lid)],
            step_kinds=["research", "measure", "review"],
            depends_on=[{"identity": FORMAT_IR}, {"identity": ANSWER_SCHEMA}, {"identity": EVIDENCE_CONTRACT}],
            parameters={"lens": lid, "questions": len(qs)},
            review={"status": "automated-passed", "checked": CHECKED,
                    "notes": "Generator checks ids, fields, answer types, enum choices, IR pointers against the format "
                             "IR schema, evidence field names, recipe codes and near-duplicate questions."},
        )
        run.component(
            "subagent", f"video_re_analyst_{lid}",
            title=f"Video RE analyst: {lens['title']}",
            summary=(f"Read-only subagent that answers the {lens['title'].lower()} question bank for one video from "
                     "evidence.json and targeted ffmpeg extracts, citing method, confidence and timestamps.")[:240],
            description=(lens["purpose"] + " Output: a JSON array conforming to the video_re_analyst_answer contract. "
                         "Says 'not determinable' rather than guessing. " + DESCRIPTION_BOUNDARY),
            subkind="review-lens", domain="video",
            files={"agent.md": agent_md(kebab(f"video_re_analyst_{lid}"), analyst_description(lens),
                                        analyst_body(lens), tools=ANALYST_TOOLS)},
            tags=TAGS + ["analyst", "subagent", lens_tag(lid)],
            step_kinds=["research", "measure", "review"],
            effects_=effects(filesystem="read", executes="shell",
                             side_effects=["runs ffmpeg/ffprobe to extract frames, crops and spectrograms into a scratch "
                                           "directory it deletes afterwards"]),
            harnesses=AGENT_HARNESSES,
            depends_on=[{"identity": f"video_re_questions_{lid}"}, {"identity": MEASURE},
                        {"identity": ANSWER_SCHEMA}, {"identity": EVIDENCE_CONTRACT},
                        {"identity": "ffmpeg", "external": True}],
            parameters={"lens": lid, "questions": len(qs)},
        )

    run.component(
        "subagent", "video_re_challenger",
        title="Video RE challenger",
        summary="Adversarial subagent that tries to refute each analyst answer: checks timestamps against evidence, "
                "re-measures, relabels methods, flags taste-as-fact and over-generalisation, then upholds, lowers or rejects.",
        description=("Runs a bundled standard-library pre-pass (fields, confidence bands, timestamp range, answer shape "
                     "against the bank, quotes over 6 words, overlaps with source captions, taste and identity words), "
                     "then each question's own challenge prompt and 19 cross-lens consistency checks. Output keeps the "
                     "video_re_analyst_answer shape so the lifter can merge it. " + DESCRIPTION_BOUNDARY),
        subkind="evaluator", domain="video",
        files={"agent.md": agent_md(
            "video-re-challenger",
            "Use after the video RE analysts answer their question banks and before lifting. Tries to refute every "
            "answer against evidence.json and the source, lowers or rejects what does not hold, and runs cross-lens "
            "consistency checks. Read-only apart from its scratch and output files.",
            CHALLENGER, tools=ANALYST_TOOLS),
            "challenge_prepass.py": PREPASS, "test_challenge_prepass.py": PREPASS_TEST},
        tags=TAGS + ["challenger", "adversarial-review", "subagent"],
        step_kinds=["review", "verify"],
        effects_=effects(filesystem="read", executes="shell",
                         side_effects=["runs ffmpeg/ffprobe and the bundled pre-pass script; writes only its scratch "
                                       "directory and its report"]),
        harnesses=AGENT_HARNESSES,
        depends_on=[{"identity": ANSWER_SCHEMA}, {"identity": EVIDENCE_CONTRACT}, {"identity": MEASURE},
                    {"identity": "ffmpeg", "external": True}]
                   + [{"identity": f"video_re_questions_{lid}"} for lid in LENS_IDS],
    )
    run.component(
        "subagent", "video_re_lifter",
        title="Video RE lifter",
        summary="Subagent that merges the answers surviving the challengers into one Video format IR with video_re_ir_merge, "
                "resolves conflicts by method and confidence, and turns gaps into open questions.",
        description=("Like a decompiler lifting verified facts into a typed IR: shapes answers into observed numbers and "
                     "texts, applies JSON-pointer appends and per-element paths, records conflicts, fills required fields "
                     "honestly (assumed values are marked) and validates with video_re_ir_validate. " + DESCRIPTION_BOUNDARY),
        subkind="workflow", domain="video",
        files={"agent.md": agent_md(
            "video-re-lifter",
            "Use after the video RE challengers. Merges surviving analyst answers into one Video format IR, resolves "
            "conflicts, writes proposals for the parameteriser and validates the IR.",
            LIFTER, tools=["Read", "Write", "Bash", "Glob"])},
        tags=TAGS + ["lifter", "format-ir", "subagent"],
        step_kinds=["build", "design"],
        effects_=effects(filesystem="write", executes="python",
                         side_effects=["writes format_ir.json, proposals.json and lift_report.json in the output directory"]),
        harnesses=AGENT_HARNESSES,
        depends_on=[{"identity": IR_MERGE}, {"identity": IR_VALIDATE}, {"identity": FORMAT_IR},
                    {"identity": ANSWER_SCHEMA}, {"identity": "video_re_challenger"}],
    )
    run.component(
        "subagent", "video_re_parameteriser",
        title="Video RE parameteriser",
        summary="Subagent that turns a lifted IR into a reusable format: typed parameters with evidence-justified ranges, "
                "procedural generation rules, a reproduction check and a short_video_spec render binding.",
        description=("Generalises concrete observations (for example 4 items of about 12 s) into parameters "
                     "(n_items with a derived range) and rules (item_s = (target_duration_s - intro_s - outro_s) / "
                     "n_items), checks that the rules reproduce the source when parameters take observed values, and "
                     "marks every range wider than the evidence as assumed. " + DESCRIPTION_BOUNDARY),
        subkind="series-format", domain="video",
        files={"agent.md": agent_md(
            "video-re-parameteriser",
            "Use after the video RE lifter. Generalises the lifted IR into typed parameters with evidence-justified "
            "ranges and procedural generation rules, checks the rules reproduce the source, and binds the format to "
            "the short_video_spec renderer contract.",
            PARAMETERISER, tools=["Read", "Write", "Bash", "Glob"])},
        tags=TAGS + ["parameteriser", "procedural", "format-ir", "subagent"],
        step_kinds=["design", "build"],
        effects_=effects(filesystem="write", executes="python",
                         side_effects=["rewrites format_ir.json and writes parameterise_report.json in the output directory"]),
        harnesses=AGENT_HARNESSES,
        depends_on=[{"identity": IR_PARAM}, {"identity": IR_VALIDATE}, {"identity": FORMAT_IR},
                    {"identity": "short_video_spec"}, {"identity": "video_re_lifter"}],
    )
    run.component(
        "subagent", "video_re_round_trip_judge",
        title="Video RE round-trip judge",
        summary="Subagent that re-measures a variant rendered from a format IR, scores IR fidelity per dimension with "
                "video_re_ir_diff_fidelity, gates originality, proposes JSON Patch fixes and decides when to stop iterating.",
        description=("Dimensions: timeline, cut rhythm, layers, typography, motion, audio and script pattern. Separates "
                     "format deviations from content-driven differences, refuses to score a variant that reuses source "
                     "frames, captions or audio, and stops when the gain over two rounds falls below a configurable "
                     "minimum. " + DESCRIPTION_BOUNDARY),
        subkind="evaluator", domain="video",
        files={"agent.md": agent_md(
            "video-re-round-trip-judge",
            "Use after a variant has been rendered from a format IR. Measures and lifts the variant, scores fidelity "
            "per dimension against the source IR, checks originality, and proposes IR patches until fidelity stops "
            "improving.",
            JUDGE, tools=["Read", "Write", "Bash", "Glob"])},
        tags=TAGS + ["round-trip", "fidelity", "evaluator", "subagent"],
        step_kinds=["verify", "measure"],
        effects_=effects(filesystem="write", executes="shell",
                         side_effects=["runs ffmpeg/ffprobe and the measurement bundle on the variant; writes round "
                                       "reports and proposed patches in its work directory"]),
        harnesses=AGENT_HARNESSES,
        depends_on=[{"identity": IR_DIFF}, {"identity": MEASURE}, {"identity": IR_VALIDATE}, {"identity": FORMAT_IR},
                    {"identity": "video_re_lifter"}, {"identity": "ffmpeg", "external": True}],
    )

    analyst_deps = [{"identity": f"video_re_analyst_{lid}"} for lid in LENS_IDS]
    commands = [
        ("reverse_engineer_video", "/reverse-engineer-video",
         "Slash command that reverse-engineers a local video into a parametric format: measure, 18 analysts in "
         "parallel, challengers, lifter, parameteriser, validation.",
         "Reverse-engineer a local video into a reusable, parametric format IR",
         CMD_REVERSE, "<video file> [--lenses all|a,b] [--out DIR] [--text-mode masked|full]",
         ["plan", "research", "measure", "build"],
         [{"identity": MEASURE}, *analyst_deps, {"identity": "video_re_challenger"}, {"identity": "video_re_lifter"},
          {"identity": "video_re_parameteriser"}, {"identity": IR_VALIDATE}, {"identity": PIPELINE_SKILL}]),
        ("lift_format_from_evidence", "/lift-format-from-evidence",
         "Slash command that lifts a format IR from an existing evidence.json: runs missing analysts, challengers, "
         "the lifter and the parameteriser, then validates.",
         "Lift a format IR from an existing evidence bundle",
         CMD_LIFT, "<evidence.json> [answers dir] [--src VIDEO] [--out DIR]",
         ["research", "build"],
         [*analyst_deps, {"identity": "video_re_challenger"}, {"identity": "video_re_lifter"},
          {"identity": "video_re_parameteriser"}, {"identity": IR_VALIDATE}]),
        ("render_from_format", "/render-from-format",
         "Slash command that compiles a format IR plus new content into a short_video_spec render plan, renders it "
         "with new or licensed assets and runs QA.",
         "Render a new video from a lifted format IR and new content",
         CMD_RENDER, "<format_ir.json> <content.json | topic> [--out DIR]",
         ["plan", "render", "verify"],
         [{"identity": IR_COMPILE}, {"identity": "short_video_spec"}, {"identity": "mp4_qa_probe"},
          {"identity": FORMAT_IR}]),
        ("compare_formats", "/compare-formats",
         "Slash command that runs the round-trip judge on a variant: per-dimension fidelity, originality gate, "
         "proposed IR patches and the stop decision.",
         "Score a variant against its source format and propose IR fixes",
         CMD_COMPARE, "<source format_ir.json> <variant.mp4 | variant format_ir.json> [--round N]",
         ["verify", "measure"],
         [{"identity": "video_re_round_trip_judge"}, {"identity": IR_DIFF}, {"identity": IR_VALIDATE}]),
    ]
    for ident, title, summary, desc, body, hint, steps, deps in commands:
        run.component(
            "command", ident, title=title, summary=summary,
            description=desc + ". " + DESCRIPTION_BOUNDARY,
            subkind="workflow", domain="video",
            files={"command.md": command_md(desc, body, argument_hint=hint)},
            tags=TAGS + ["command", "workflow"],
            step_kinds=steps,
            effects_=effects(filesystem="write", executes="shell",
                             side_effects=["runs ffmpeg/ffprobe and Python modules; writes evidence, answers, IR and "
                                           "reports under the chosen output directory"]),
            harnesses=AGENT_HARNESSES,
            depends_on=deps,
        )
    print(f"video_re_swarm: {len(LENSES)} lenses, {total} questions")
