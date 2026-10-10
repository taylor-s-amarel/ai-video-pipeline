#!/usr/bin/env python3
"""Adversarial review bank, review lenses, copy-ready task templates and intake rules.

Source: the owner's *Animation and Video Production Master Guide* (10 Oct 2026),
``docs/reference/Animation_and_Video_Production_Master_Guide_2026-10-10.md``:

* lines 1328-1388: adversarial review without checklist theater, reusable
  components and actual intake, bounded adoption experiments;
* lines 1389-1548: copy-ready task templates and practical next steps;
* lines 6048-8213: Appendix E, all 1,024 adversarial review questions.

The guide is parsed into ``data/ref_review_templates/*.json``
(``python3 ref_review_templates.py --extract``). A normal run reads that data,
re-parses the guide when it is present and fails if the two have drifted, and
asserts exactly 1,024 questions with unique ids before writing anything.

This bank is the owner's authoritative one. Another builder (harness_kit)
independently wrote a different 1,024-question bank; the two are not the same
set and are not merged here.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from _lib import REPO_ROOT, GeneratorRun, agent_md, command_md, dumps, effects, skill_md

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "ref_review_templates"
GUIDE_REL = "docs/reference/Animation_and_Video_Production_Master_Guide_2026-10-10.md"
GUIDE = REPO_ROOT / GUIDE_REL
REPO_URL = "https://github.com/taylor-s-amarel/ai-video-pipeline"
EXPECTED_QUESTIONS = 1024
EXPECTED_AREAS = 32

# Line ranges assigned to this generator (1-based, inclusive).
RANGE_REVIEW = (1328, 1388)
RANGE_TEMPLATES = (1389, 1548)
RANGE_APPENDIX_E = (6048, 8213)

QUESTION_RE = re.compile(
    r"^- \*\*(?P<id>AVQ-(?P<dom>\d{3})-(?P<num>\d{3}))\*\* (?P<question>.+?) "
    r"\*\*Failure hypothesis:\*\* (?P<failure>.+?) "
    r"\*\*Check or fix:\*\* (?P<check>.+?) "
    r"\*\*Severity:\*\* (?P<severity>[a-z]+)\. "
    r"\*\*Modes:\*\* (?P<modes>[^*]+?)\. "
    r"\*\*Stages:\*\* (?P<stages>[^*]+?)\. "
    r"\*\*Style filters:\*\* (?P<styles>[^*]+?)\.$"
)
DOMAIN_RE = re.compile(r"^### (?P<dom>D(?P<n>\d{3})) (?P<area>.+)$")
PASS_ROW_RE = re.compile(r"^\| (?P<id>[a-z0-9_]+) \| (?P<purpose>[^|]+) \| (?P<n>\d+) \|$")
PASS_HEAD_RE = re.compile(r"^#### Pass (?P<id>[a-z0-9_]+)$")


# --------------------------------------------------------------------------- parsing the guide

def github_anchors(lines: list[str]) -> dict[int, str]:
    """GitHub-style heading anchors for every ATX heading outside code fences, keyed by 1-based line."""
    seen: Counter = Counter()
    out: dict[int, str] = {}
    fence = False
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#{1,6}) +(.+?)\s*#*\s*$", line)
        if not m:
            continue
        text = m.group(2).strip().lower()
        slug = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE).replace(" ", "-")
        n = seen[slug]
        seen[slug] += 1
        out[i] = slug if n == 0 else f"{slug}-{n}"
    return out


def _split_list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _area_slug(area: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", area.lower()).strip("_")


def parse_appendix_e(lines: list[str], anchors: dict[int, str]) -> dict:
    lo, hi = RANGE_APPENDIX_E
    passes: dict[str, dict] = {}
    areas: list[dict] = []
    questions: list[dict] = []
    current_pass = None
    current_area = None
    for ln in range(lo, hi + 1):
        line = lines[ln - 1]
        m = PASS_ROW_RE.match(line)
        if m:
            passes[m["id"]] = {"purpose": m["purpose"].strip(), "declared_count": int(m["n"]), "question_ids": []}
            continue
        m = PASS_HEAD_RE.match(line)
        if m:
            current_pass = m["id"]
            continue
        if current_pass and line.startswith("`AVQ-"):
            passes[current_pass]["question_ids"] = re.findall(r"`(AVQ-\d{3}-\d{3})`", line)
            current_pass = None
            continue
        m = DOMAIN_RE.match(line)
        if m:
            current_area = {
                "domain_id": m["dom"],
                "area": m["area"].strip(),
                "slug": _area_slug(m["area"]),
                "heading_line": ln,
                "anchor": anchors[ln],
            }
            areas.append(current_area)
            continue
        if line.startswith("- **AVQ-"):
            m = QUESTION_RE.match(line)
            if not m:
                raise ValueError(f"line {ln}: question entry does not match the expected structure")
            if current_area is None or f"D{m['dom']}" != current_area["domain_id"]:
                raise ValueError(f"line {ln}: {m['id']} is outside its domain section")
            questions.append({
                "id": m["id"],
                "domain_id": current_area["domain_id"],
                "area": current_area["area"],
                "question": m["question"].strip(),
                "failure_hypothesis": m["failure"].strip(),
                "check_or_fix": m["check"].strip(),
                "severity": m["severity"],
                "modes": _split_list(m["modes"]),
                "stages": _split_list(m["stages"]),
                "style_filters": _split_list(m["styles"]),
                "source_line": ln,
            })
    # Pass membership is something the appendix provides, so each question records it.
    membership: dict[str, list[str]] = {}
    for pid, p in passes.items():
        for qid in p["question_ids"]:
            membership.setdefault(qid, []).append(pid)
    for q in questions:
        q["passes"] = membership.get(q["id"], [])
    intro_text = []
    for line in lines[lo:hi]:
        if line.startswith("### "):
            break
        if line.strip():
            intro_text.append(line.strip())
    return {"intro": intro_text, "passes": passes, "areas": areas, "questions": questions}


def check_bank(bank: dict) -> None:
    qs = bank["questions"]
    ids = [q["id"] for q in qs]
    assert len(qs) == EXPECTED_QUESTIONS, f"expected {EXPECTED_QUESTIONS} questions, parsed {len(qs)}"
    assert len(set(ids)) == EXPECTED_QUESTIONS, "question ids are not unique"
    assert len(bank["areas"]) == EXPECTED_AREAS, f"expected {EXPECTED_AREAS} areas, parsed {len(bank['areas'])}"
    per_area = Counter(q["domain_id"] for q in qs)
    for a in bank["areas"]:
        assert per_area[a["domain_id"]] == 32, f"{a['domain_id']} has {per_area[a['domain_id']]} questions"
    assert len({a["slug"] for a in bank["areas"]}) == EXPECTED_AREAS, "area slugs collide"
    assert len(bank["passes"]) == 9, f"expected nine named passes, parsed {len(bank['passes'])}"
    known = set(ids)
    for pid, p in bank["passes"].items():
        assert len(p["question_ids"]) == p["declared_count"], \
            f"pass {pid}: {len(p['question_ids'])} ids listed, {p['declared_count']} declared"
        assert len(set(p["question_ids"])) == len(p["question_ids"]), f"pass {pid} repeats an id"
        missing = [q for q in p["question_ids"] if q not in known]
        assert not missing, f"pass {pid} names unknown ids {missing[:3]}"


def _paragraphs(block: list[str]) -> list[str]:
    paras, cur = [], []
    for line in block:
        if line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


def _section(lines: list[str], start: int, stop_prefixes: tuple[str, ...], limit: int) -> tuple[int, list[str]]:
    """Body lines after heading line ``start`` until the next heading with one of ``stop_prefixes``."""
    body = []
    ln = start + 1
    while ln <= limit and not lines[ln - 1].startswith(stop_prefixes):
        body.append(lines[ln - 1])
        ln += 1
    return ln, body


def parse_review_sections(lines: list[str], anchors: dict[int, str]) -> dict:
    lo, hi = RANGE_REVIEW[0], RANGE_TEMPLATES[1]
    heads = {ln: lines[ln - 1] for ln in range(lo, hi + 1) if lines[ln - 1].startswith("## ")}
    out: dict = {}
    for ln, head in heads.items():
        nxt, body = _section(lines, ln, ("## ",), hi)
        out[head[3:].strip()] = {"line": ln, "end_line": nxt - 1, "anchor": anchors[ln],
                                 "markdown": "\n".join(body).strip("\n")}
    return out


def parse_experiments(markdown: str) -> list[dict]:
    rows = [r for r in markdown.splitlines() if r.startswith("| ") and not r.startswith("|---")]
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    assert header == ["Experiment", "Intended outcome", "Evidence needed", "Stop or hold condition"], header
    out = []
    for r in rows[1:]:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        out.append(dict(zip(["experiment", "intended_outcome", "evidence_needed", "stop_or_hold_condition"], cells)))
    return out


def parse_templates(lines: list[str], anchors: dict[int, str]) -> dict:
    lo, hi = RANGE_TEMPLATES
    usage, templates = [], []
    ln = lo
    while ln <= hi:
        line = lines[ln - 1]
        if line.startswith("### "):
            nxt, body = _section(lines, ln, ("### ", "## "), hi)
            title = line[4:].strip()
            paras = _paragraphs(body)
            if title == "How to use the templates":
                usage = paras
            else:
                prompt = paras[0]
                assert prompt[0] in "“\"" and prompt[-1] in "”\"", f"template {title!r} prompt is not a quotation"
                templates.append({"title": title, "line": ln, "anchor": anchors[ln], "prompt": prompt,
                                  "guidance": paras[1:]})
            ln = nxt
            continue
        ln += 1
    return {"usage": usage, "templates": templates}


def parse_next_steps(markdown: str) -> dict:
    steps = [re.sub(r"^\d+\.\s+", "", l.strip()) for l in markdown.splitlines() if re.match(r"^\d+\.\s", l.strip())]
    closing = [p for p in _paragraphs(markdown.splitlines()) if not re.match(r"^\d+\.\s", p)]
    return {"steps": steps, "closing": closing}


def parse_library_records(lines: list[str]) -> list[dict]:
    """Library identities, sizes and SHA-256 values the guide records for the review bank (Appendix G)."""
    out = []
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\| (Adversarial Video Review [^|]+?) \| `(libfile_[0-9a-f]+)` \| (\d+) \| ([\d,]+) \| `([0-9a-f]{64})` \|$", line)
        if m:
            out.append({"artifact": m[1], "library_identity": m[2], "version": int(m[3]),
                        "bytes": int(m[4].replace(",", "")), "sha256": m[5], "guide_line": i,
                        "guide_section": "Appendix G Source inventory and refresh conditions"})
    return out


def extract() -> dict:
    raw = GUIDE.read_bytes()
    lines = raw.decode("utf-8").splitlines()
    anchors = github_anchors(lines)
    bank = parse_appendix_e(lines, anchors)
    check_bank(bank)
    sections = parse_review_sections(lines, anchors)
    templates = parse_templates(lines, anchors)
    source = {"file": GUIDE_REL, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "lines": len(lines)}
    library = parse_library_records(lines)
    return {
        "appendix_e_questions.json": {"source": {**source, "range": list(RANGE_APPENDIX_E)},
                                      "library_records": library, **bank},
        "review_sections.json": {
            "source": {**source, "ranges": [list(RANGE_REVIEW), list(RANGE_TEMPLATES)]},
            "sections": sections,
            "experiments": parse_experiments(sections["Bounded adoption experiments"]["markdown"]),
            "next_steps": parse_next_steps(sections["Practical next steps"]["markdown"]),
        },
        "templates.json": {"source": {**source, "range": list(RANGE_TEMPLATES)}, **templates},
    }


def load_data() -> dict:
    data = {name: json.loads((DATA / name).read_text(encoding="utf-8"))
            for name in ("appendix_e_questions.json", "review_sections.json", "templates.json")}
    if GUIDE.exists():
        fresh = extract()
        for name, value in fresh.items():
            if value != data[name]:
                raise SystemExit(f"{name} is stale: the guide changed. Re-run with --extract and review the diff.")
    check_bank(data["appendix_e_questions.json"])
    return data


# --------------------------------------------------------------------------- shared wording

GUIDE_TITLE = "Animation and Video Production Master Guide (10 Oct 2026)"
AUTHORITY = (
    "This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the "
    "Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, "
    "ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote "
    "a different 1,024-question bank; it is not this set and does not override it."
)
STATUSES = ["untested", "observed-pass", "observed-fail", "blocked", "not-applicable"]
FINDING_TYPES = ["none", "demonstrated_defect", "potential_improvement"]
MODES = ["visual", "auditory", "machine", "human-audience"]
STAGES = ["concept", "script", "storyboard", "animatic", "production", "edit", "final-encode", "delivery"]
COVERAGE = ["not_observed", "sampled", "interval", "full"]
OBSERVATIONS = ["frame-inspection", "contact-sheet", "decoded-stream", "metadata-probe", "measurement",
                "waveform-statistic", "listening", "audience-feedback", "owner-feedback", "source-inspection", "other"]
SHA = "^[0-9a-f]{64}$"
REVIEW_TOOLS = ["Read", "Grep", "Glob", "Bash"]
AGENT_HARNESSES = ["claude-code", "opencode", "baltor-harness"]


def src(anchor: str) -> dict:
    return {"type": "original", "url": REPO_URL, "upstream": f"{GUIDE_REL}#{anchor}"}


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


def ids_line(ids: list[str]) -> str:
    return ", ".join(f"`{i}`" for i in ids) if ids else "none"


# --------------------------------------------------------------------------- contract schemas

def question_schema(bank: dict) -> dict:
    styles = sorted({s for q in bank["questions"] for s in q["style_filters"]})
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{REPO_URL}/baltor/contract-schemas/adversarial-question/schema.json",
        "title": "Adversarial review question (owner's bank, Master Guide Appendix E)",
        "description": AUTHORITY + " One record per question. Fields follow the appendix: stable ID, question, "
                       "failure hypothesis, practical check/fix, severity and modality/stage/style filters, plus the "
                       "named passes that list the question. Filters are candidate filters: they cannot make an "
                       "irrelevant question applicable or turn missing evidence into a pass.",
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "domain_id", "area", "question", "failure_hypothesis", "check_or_fix", "severity",
                     "modes", "stages", "style_filters"],
        "properties": {
            "id": {"type": "string", "pattern": r"^AVQ-\d{3}-\d{3}$",
                   "description": "Stable id AVQ-<domain>-<number>, e.g. AVQ-006-002"},
            "domain_id": {"type": "string", "pattern": r"^D\d{3}$", "description": "Review area id, D001-D032"},
            "area": {"enum": [a["area"] for a in bank["areas"]], "description": "Review area name as the guide gives it"},
            "question": {"type": "string", "minLength": 5, "description": "The owner's exact question text"},
            "failure_hypothesis": {"type": "string", "minLength": 3,
                                   "description": "What goes wrong when the answer is no (the guide's 'Failure hypothesis')"},
            "check_or_fix": {"type": "string", "minLength": 3,
                             "description": "How to check it or fix it (the guide's 'Check or fix')"},
            "severity": {"enum": ["low", "medium", "high", "critical"]},
            "modes": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"enum": MODES},
                      "description": "How the question can be answered. 'auditory' means listening; a waveform "
                                     "statistic is a separate machine check."},
            "stages": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"enum": STAGES}},
            "style_filters": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"enum": styles}},
            "passes": {"type": "array", "uniqueItems": True, "items": {"enum": list(bank["passes"])},
                       "description": "Named review passes that list this question (Appendix E, 'Named review passes')"},
            "source_line": {"type": "integer", "minimum": 1,
                            "description": "Line of the entry in the guide file the bank was transcribed from"},
        },
    }


def result_schema() -> dict:
    sha = {"type": "string", "pattern": SHA}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{REPO_URL}/baltor/contract-schemas/adversarial-review-result/schema.json",
        "title": "Adversarial review result record",
        "description": "One question applied to one exact target, following the evidence contract of the Master "
                       "Guide's 'Adversarial review without checklist theater' section. untested is the default; "
                       "observed-pass/observed-fail need exact evidence for this target; blocked and not-applicable "
                       "need a stated reason; demonstrated_defect only with an observed failure. Cross-record rules "
                       "the schema cannot express (stale target hashes, retargeted evidence, unsupported coverage, "
                       "nonfinite numbers, listening questions passed on waveform statistics) are enforced by the "
                       "adversarial_review_kit code module.",
        "type": "object",
        "additionalProperties": False,
        "required": ["question_id", "target_artifact", "target_sha256", "status", "finding_type", "review_mode",
                     "scope", "evidence", "rationale", "required_recheck_after"],
        "properties": {
            "question_id": {"type": "string", "pattern": r"^AVQ-\d{3}-\d{3}$"},
            "target_artifact": {"type": "string", "minLength": 1,
                                "description": "The exact artifact reviewed: brief, storyboard, source state or final encode"},
            "target_sha256": {"type": "string", "minLength": 1,
                              "description": "SHA-256 of the exact target bytes. A placeholder such as "
                                             "COMPUTED_FINAL_HASH is allowed only while the record is not observed."},
            "status": {"enum": STATUSES},
            "finding_type": {"enum": FINDING_TYPES,
                             "description": "demonstrated_defect only with observed-fail; potential_improvement is a "
                                            "design hypothesis that still needs comparison"},
            "review_mode": {"enum": MODES},
            "scope": {
                "type": "object", "additionalProperties": False,
                "required": ["start_frame", "end_frame", "coverage"],
                "properties": {
                    "start_frame": {"type": ["integer", "null"], "minimum": 0},
                    "end_frame": {"type": ["integer", "null"], "minimum": 0},
                    "coverage": {"enum": COVERAGE},
                },
            },
            "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
            "rationale": {"type": "string"},
            "required_recheck_after": {"type": "array", "uniqueItems": True,
                                       "items": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                                       "description": "Changes that invalidate this record, e.g. rig_change, camera_change"},
            "reviewer": {"type": "string", "description": "Who observed: a named person, or an agent identity"},
            "reviewed_at": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}"},
        },
        "$defs": {
            "evidence": {
                "type": "object", "additionalProperties": False,
                "required": ["evidence_sha256", "target_sha256", "method", "locator", "coverage", "limitations"],
                "properties": {
                    "evidence_sha256": {**sha, "description": "Hash of the evidence itself (contact sheet, frame, log, notes)"},
                    "target_sha256": {**sha, "description": "Hash of the movie the evidence was extracted from"},
                    "method": {"type": "string", "minLength": 1, "description": "Extraction or observation method"},
                    "locator": {"type": "string", "minLength": 1, "description": "Frames, timestamps or file path"},
                    "coverage": {"enum": COVERAGE},
                    "limitations": {"type": "string", "minLength": 1},
                    "observation": {"enum": OBSERVATIONS,
                                    "description": "Kind of observation; a listening-only question passes only on "
                                                   "listening, audience or owner feedback"},
                    "path": {"type": "string"},
                    "measurements": {"type": "object",
                                     "additionalProperties": {"type": ["number", "string", "boolean", "null"]}},
                },
            },
        },
        "allOf": [
            {"if": {"required": ["finding_type"], "properties": {"finding_type": {"const": "demonstrated_defect"}}},
             "then": {"properties": {"status": {"const": "observed-fail"}}}},
            {"if": {"required": ["status"], "properties": {"status": {"enum": ["observed-pass", "observed-fail"]}}},
             "then": {"properties": {"target_sha256": {"pattern": SHA}, "evidence": {"minItems": 1},
                                     "scope": {"properties": {"coverage": {"not": {"const": "not_observed"}}}}}}},
            {"if": {"required": ["status"], "properties": {"status": {"enum": ["blocked", "not-applicable"]}}},
             "then": {"properties": {"rationale": {"pattern": r"\S"}}}},
            {"if": {"required": ["scope"],
                    "properties": {"scope": {"required": ["coverage"],
                                             "properties": {"coverage": {"enum": ["interval", "full"]}}}}},
             "then": {"properties": {"scope": {"properties": {"start_frame": {"type": "integer"},
                                                              "end_frame": {"type": "integer"}}}}}},
        ],
    }


GUIDE_RECORD = {
    "question_id": "AVQ-006-002",
    "target_artifact": "final.mp4",
    "target_sha256": "COMPUTED_FINAL_HASH",
    "status": "untested",
    "finding_type": "none",
    "review_mode": "visual",
    "scope": {"start_frame": None, "end_frame": None, "coverage": "not_observed"},
    "evidence": [],
    "rationale": "Awaiting matching encoded interval",
    "required_recheck_after": ["rig_change", "prop_attachment_change", "camera_change"],
}
# Illustrative only: the hashes below are obviously synthetic and no real film is described.
ILLUSTRATIVE_FILM = "1" * 64
ILLUSTRATIVE_SHEET = "2" * 64


def result_examples() -> dict[str, dict]:
    fail = {
        "question_id": "AVQ-006-002",
        "target_artifact": "illustrative-final.mp4",
        "target_sha256": ILLUSTRATIVE_FILM,
        "status": "observed-fail",
        "finding_type": "demonstrated_defect",
        "review_mode": "visual",
        "scope": {"start_frame": 412, "end_frame": 436, "coverage": "interval"},
        "evidence": [{
            "evidence_sha256": ILLUSTRATIVE_SHEET,
            "target_sha256": ILLUSTRATIVE_FILM,
            "method": "ffmpeg decode of every frame 412-436 from the exact final MP4, tiled 5x5",
            "locator": "frames 412-436 (00:17.17-00:18.17 at 24 fps)",
            "coverage": "interval",
            "limitations": "Illustrative record with synthetic hashes; one interval only, no other hand-offs inspected",
            "observation": "contact-sheet",
        }],
        "rationale": "Illustrative: the box starts sliding at frame 419; the hand first touches it at frame 423",
        "required_recheck_after": ["rig_change", "prop_attachment_change", "camera_change"],
        "reviewer": "illustrative example",
    }
    blocked = {
        "question_id": "AVQ-022-001",
        "target_artifact": "illustrative-final.mp4",
        "target_sha256": ILLUSTRATIVE_FILM,
        "status": "blocked",
        "finding_type": "none",
        "review_mode": "auditory",
        "scope": {"start_frame": None, "end_frame": None, "coverage": "not_observed"},
        "evidence": [],
        "rationale": "Illustrative: listening question; no listener or audio access in this pass. Loudness "
                     "statistics were measured separately and do not answer it.",
        "required_recheck_after": ["music_change", "narration_change", "mix_change"],
    }
    defect_unobserved = dict(GUIDE_RECORD, finding_type="demonstrated_defect")
    pass_without_evidence = dict(fail, status="observed-pass", finding_type="none", evidence=[])
    interval_without_frames = dict(fail, scope={"start_frame": None, "end_frame": None, "coverage": "interval"})
    return {
        "examples/guide-untested-awaiting-encoded-interval.json": GUIDE_RECORD,
        "examples/illustrative-observed-fail-hand-before-prop.json": fail,
        "examples/illustrative-blocked-listening-question.json": blocked,
        "examples/invalid-defect-without-observed-failure.json": defect_unobserved,
        "examples/invalid-pass-without-evidence.json": pass_without_evidence,
        "examples/invalid-interval-without-frames.json": interval_without_frames,
    }


def validate_against(schema: dict, records: list[dict], label: str) -> None:
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - the catalogue validator also checks examples
        print(f"jsonschema not installed; skipped checking {label}")
        return
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    v = cls(schema)
    bad = [(r.get("id") or r.get("question_id"), e.message) for r in records for e in v.iter_errors(r)]
    assert not bad, f"{label}: {len(bad)} record(s) fail the schema, first: {bad[0]}"


# --------------------------------------------------------------------------- per-area text

def q_block(q: dict, n: int) -> str:
    passes = f" Passes: {', '.join(q['passes'])}." if q["passes"] else ""
    return (
        f"{n}. **{q['id']}** {q['question']}\n"
        f"   - Failure hypothesis: {q['failure_hypothesis']}\n"
        f"   - Check or fix: {q['check_or_fix']}\n"
        f"   - Severity: {q['severity']}. Modes: {', '.join(q['modes'])}. Stages: {', '.join(q['stages'])}. "
        f"Style filters: {', '.join(q['style_filters'])}.{passes}"
    )


def area_facts(area: dict, qs: list[dict], passes: dict) -> dict:
    planning = {"concept", "script", "storyboard", "animatic"}
    return {
        "severity": Counter(q["severity"] for q in qs),
        "modes": Counter(m for q in qs for m in q["modes"]),
        "listening": [q["id"] for q in qs if "auditory" in q["modes"]],
        "listening_only": [q["id"] for q in qs if "auditory" in q["modes"]
                           and set(q["modes"]) <= {"auditory", "human-audience"}],
        "audience": [q["id"] for q in qs if "human-audience" in q["modes"]],
        "final_only": [q["id"] for q in qs if set(q["stages"]) <= {"final-encode", "delivery"}],
        "planning": [q["id"] for q in qs if set(q["stages"]) & planning],
        "styled": [(q["id"], q["style_filters"]) for q in qs if q["style_filters"] != ["any"]],
        "passes": {pid: [i for i in p["question_ids"] if i.startswith(f"AVQ-{area['domain_id'][1:]}-")]
                   for pid, p in passes.items()},
    }


def roundtrip_check(md: str, qs: list[dict]) -> None:
    """The shipped kit must read a placed bank RULES.md back to exactly the transcribed records."""
    sys.dont_write_bytecode = True
    if str(DATA / "modules") not in sys.path:
        sys.path.insert(0, str(DATA / "modules"))
    import adversarial_review_kit as kit
    keys = kit.COMPARED + ("id", "domain_id", "area", "passes")
    parsed = kit.parse_bank_markdown(md)
    assert [{k: p[k] for k in keys} for p in parsed] == [{k: q[k] for k in keys} for q in qs], \
        f"RULES.md for {qs[0]['domain_id']} does not round-trip through adversarial_review_kit"


def counter_text(c: Counter, order: list[str]) -> str:
    return ", ".join(f"{c[k]} {k}" for k in order if c.get(k))


def bank_rules_md(area: dict, qs: list[dict], facts: dict, intro: list[str]) -> str:
    pass_lines = [f"- `{pid}`: {ids_line(ids)}" for pid, ids in facts["passes"].items() if ids]
    return f"""# Adversarial review bank: {area['domain_id']} {area['area']} (32 questions)

{AUTHORITY}

Source: {GUIDE_TITLE}, Appendix E, section "{area['domain_id']} {area['area']}". The questions below are the
owner's exact text. `questions.json` holds the same 32 records in the `adversarial_question` contract.

## How to use this bank (the guide's rules)

{bullets(intro)}
- Use the bank twice: first on the brief, storyboard and source state; then on the exact final encode. Final-pixel
  and listening questions remain untested or blocked during planning.
- After a material camera, rig, sound, caption, factual or rights change, add a targeted pass: recheck the changed
  beat and neighbouring beats. Stop after the bounded pass and necessary repairs; do not execute every question to
  manufacture impressive totals.
- Every answer is a record in the `adversarial_review_result` contract: `untested` (the default), `observed-pass`,
  `observed-fail`, `blocked` or `not-applicable` (with a stated reason). `demonstrated_defect` only with an observed
  failure; `potential_improvement` for a design hypothesis that still needs comparison.
- Do not mark a listening-only question passed using a waveform statistic. Do not retarget evidence to a changed
  movie by editing its label.

## This area at a glance

- Severity: {counter_text(facts['severity'], ['critical', 'high', 'medium', 'low'])}.
- Modes: {counter_text(facts['modes'], MODES)}.
- Need listening: {len(facts['listening'])} ({ids_line(facts['listening_only'])} are listening-only).
- Need a human audience: {len(facts['audience'])}.
- Only answerable at final encode or delivery: {ids_line(facts['final_only'])}.
- Limited by style filter: {", ".join(f"`{i}` ({', '.join(s)})" for i, s in facts['styled']) or "none"}.

## Named passes that draw on this area

{chr(10).join(pass_lines) or "- none"}

## Questions

{chr(10).join(q_block(q, n) for n, q in enumerate(qs, 1))}
"""


def lens_md(area: dict, qs: list[dict], facts: dict, bank_identity: str) -> str:
    listen = facts["listening"]
    audience = facts["audience"]
    mode_notes = []
    if listen:
        mode_notes.append(
            f"- {len(listen)} question(s) need listening ({ids_line(listen)}). Only an actual listening pass of the "
            "exact final audio answers them. You cannot listen: mark them `blocked` (\"no listener or audio access in "
            "this pass\") unless the caller supplies a named listener's notes for this exact file. Loudness, clipping "
            "and silence measurements are separate machine checks; report them as such and never pass a listening "
            "question on them.")
    if audience:
        mode_notes.append(
            f"- {len(audience)} question(s) involve a human audience ({ids_line(audience)}). Your own critique is not "
            "audience validation. Answer only the part you can observe in the artifact; record audience response as "
            "`blocked` unless real audience or owner feedback for this version is supplied.")
    if facts["final_only"]:
        mode_notes.append(
            f"- Only answerable on the exact final encode or delivery: {ids_line(facts['final_only'])}. During planning "
            "they stay `untested`.")
    if facts["styled"]:
        mode_notes.append("- Style-limited questions (candidate filter only): "
                          + ", ".join(f"`{i}` ({', '.join(s)})" for i, s in facts["styled"]) + ".")
    if not mode_notes:
        mode_notes.append("- Every question here is answerable from pictures, probes or source; none needs listening "
                          "or a human audience.")
    in_passes = [f"`{pid}` ({len(ids)})" for pid, ids in facts["passes"].items() if ids]
    body = f"""
You are the adversarial review lens for **{area['domain_id']} {area['area']}**. You apply the owner's 32 questions for
this area (Appendix E of the {GUIDE_TITLE}; rules package `{bank_identity}`) to one artifact and return
evidence-backed findings. This is the owner's authoritative bank; a different 1,024-question bank written by the
harness_kit builder is not this one.

You are not a checklist. Do not rubber-stamp, do not answer a question you did not observe, and do not run all 32
questions to make the totals look impressive. A question bank is a menu, not a requirement.

## Input

The caller names the artifact (brief, storyboard, source state or the exact final encode), the review stage, and
optionally the change that triggered this pass. If the artifact cannot be read, say so and stop.

## Method

1. **Fix the target.** Run `sha256sum` on the exact file under review and record the hash. For a final review the
   target is the delivered encode, never pre-encode frames or a preview. If the file changes during the review, every
   record made against the old hash is stale.
2. **Choose a bounded set.** From the questions below, pick those whose feature is present and whose stage matches
   the artifact. Tags are candidate filters: they cannot make an irrelevant question applicable. Mark an absent
   feature `not-applicable` with the reason. After a material change, recheck the changed beat and its neighbours
   only. Applicability depends on the feature and the evidence, not on a tag alone.
3. **Measure, then judge.** Visual questions: decode frames from the exact file
   (`ffmpeg -v error -ss T -i FILE -frames:v 1 frame_T.png`, or a contact sheet made from that file) and cite frame
   numbers or timestamps. Machine questions: run the probe, decode or hash and quote the measured values. Write
   extracted frames and sheets only to a scratch directory you name in the report, and hash each one you cite.
4. **Record.** One `adversarial_review_result` record per question you examined: `observed-pass` or `observed-fail`
   only with exact evidence for this target (its own hash, the target hash, method, locator, coverage,
   limitations); otherwise `untested`, `blocked` (name the missing access) or `not-applicable` (name the absent
   feature). Use `demonstrated_defect` only with an observed failure and `potential_improvement` for a design
   hypothesis that still needs comparison. Never claim more coverage than the evidence shows.
5. **Report.** Findings ranked by impact on the intended viewer task, each with its frame/time reference and the
   smallest repair. Separate taste judgments from objective errors and from measured audience results. Then list
   **what was not checked** and why. A viewer may dislike a story even when every measured gate passes; that is
   meaningful feedback, not something to argue away.

## Notes for this area

{chr(10).join(mode_notes)}
- Named passes that include questions from this area: {", ".join(in_passes) or "none"}.

## Output

```
## {area['domain_id']} {area['area']} lens: <artifact>
Target sha256: <hash>   Stage: <stage>   Trigger: <change or "full pass">
### Findings (most consequential first)
| Question | Status | Finding type | Evidence (locator) | Smallest repair |
### Not checked
- <id>: untested / blocked / not-applicable, and why
### Records
<JSON array of adversarial_review_result records>
```

## Questions ({area['domain_id']} {area['area']}, owner's exact text)

{chr(10).join(q_block(q, n) for n, q in enumerate(qs, 1))}
"""
    desc = (f"Use to review a brief, storyboard, source state or exact final encode for {area['area']} with the owner's "
            f"32 {area['domain_id']} adversarial review questions. Returns ranked, evidence-backed findings as "
            "adversarial_review_result records and states what was not checked; never rubber-stamps.")
    return agent_md(f"review-lens-{area['slug'].replace('_', '-')}", desc, body, tools=REVIEW_TOOLS)


# --------------------------------------------------------------------------- templates

# title -> (identity, argument hint, what the input is, step kinds, tags, filesystem effect)
TEMPLATE_META = {
    "Audit an existing creative project": (
        "audit_existing_creative_project", "<selected project: path or name>",
        "the selected project (path or name)", ["review", "verify"], ["audit", "reproducibility"], "read"),
    "Research a rendering route": (
        "research_rendering_route_for_scene", "<scene> <quality target>",
        "the specified scene and quality target", ["research", "plan"], ["rendering", "route-choice"], "read"),
    "Develop a rich original background": (
        "develop_rich_original_background", "<episode, its setting and any exact-count target>",
        "the specified episode", ["design", "build"], ["background", "rights"], "write"),
    "Ground a character in the scene": (
        "ground_character_in_scene", "<exact background file> <character asset>",
        "the exact background and character asset", ["build", "verify"], ["grounding", "contact-shadow"], "write"),
    "Design progressive-size counting": (
        "design_progressive_size_counting", "<target character and count> <scene>",
        "the target character, the exact count and the scene", ["design", "build", "verify"],
        ["puzzle", "counting"], "write"),
    "Improve a dance cycle": (
        "improve_dance_cycle", "<existing rig and animation: paths>",
        "the existing rig and animation", ["build", "render"], ["dance", "rig"], "write"),
    "Adapt the performance to a bunny": (
        "adapt_performance_to_bunny", "<established scene style> <existing duck rig for comparison>",
        "the established scene style and the existing rig to compare against", ["design", "build"],
        ["character", "rig"], "write"),
    "Add continuous camera motion": (
        "add_continuous_camera_motion", "<approved scene and its answer logic>",
        "the approved scene and its answer logic", ["build", "render", "verify"], ["camera", "continuity"], "write"),
    "Design a moving border": (
        "design_moving_border", "<episode>",
        "the episode the border is for", ["design", "build"], ["border", "layers"], "write"),
    "Build the twenty-plus-layer composition": (
        "build_twenty_plus_layer_composition", "<agreed layer manifest: path>",
        "the agreed layer manifest", ["build", "render", "verify"], ["layers", "compositing"], "write"),
    "Write an original meme episode": (
        "write_original_meme_episode", "<stated cast> <visual setting>",
        "the stated duck/bunny cast and visual setting", ["write", "plan"], ["story", "meme"], "write"),
    "Make an honest before-and-after comparison": (
        "make_honest_before_after_comparison", "<earlier revision> <later revision>",
        "the two specified actual revisions", ["review", "render"], ["comparison", "revision"], "write"),
    "Evaluate a historical anomaly scene": (
        "evaluate_historical_anomaly_scene", "<date> <place> <household or institution type> <scene>",
        "the date, place, household or institution type, and the scene", ["research", "verify"],
        ["history", "puzzle", "anachronism"], "read"),
    "Verify a final media file": (
        "verify_final_media_file_bytes", "<exact final MP4 path>",
        "the exact final MP4", ["verify"], ["mp4", "final-encode", "qa"], "read"),
    "Reopen the source package": (
        "reopen_source_package", "<source package archive path>",
        "the source package", ["verify", "build"], ["source-package", "reproducibility"], "write"),
    "Extract a reusable component": (
        "extract_reusable_component_from_episode", "<completed episode: path>",
        "the completed episode", ["build", "test"], ["component", "intake"], "write"),
    "Research a competitor without inventing traction": (
        "research_competitor_without_inventing_traction", "<competitor name or URL>",
        "the specified competitor", ["research"], ["competitor", "product"], "none"),
    "Plan a showcase page": (
        "plan_showcase_page", "<completed examples to feature>",
        "the real completed examples to feature", ["plan", "design"], ["showcase", "information-architecture"], "read"),
    "Diagnose a failed render and recover safely": (
        "diagnose_failed_render_and_recover_safely", "<failed job id, log path or output directory>",
        "the failed job (id, logs or output directory)", ["operate", "verify"], ["render", "recovery"], "write"),
    "Challenge the design before scaling it": (
        "challenge_design_before_scaling", "<episode: path to the current render>",
        "the episode under review", ["review"], ["critique", "adversarial-review"], "read"),
    "Expand variety without padding": (
        "expand_variety_without_padding", "<proposed new episode> <current catalogue path>",
        "the proposed new episode and the current catalogue", ["plan", "review"], ["catalogue", "variety"], "read"),
    "Write a funny suspenseful story before rendering": (
        "write_funny_suspenseful_story_before_rendering", "<intended audience>",
        "the intended audience", ["write", "plan"], ["story", "storyboard", "comedy", "suspense"], "write"),
    "Adopt one physics interaction": (
        "adopt_one_physics_interaction", "<selected storyboard beat>",
        "the selected storyboard beat", ["build", "test", "verify"], ["physics", "pymunk"], "write"),
    "Audition narration honestly": (
        "audition_narration_honestly", "<approved short script> <permitted local voice candidates>",
        "the approved short script and the permitted local candidates", ["test", "review"],
        ["narration", "tts", "listening"], "write"),
}


def command_body(t: dict, meta: tuple, usage: list[str]) -> str:
    _, _, input_what, *_ = meta
    guidance = ""
    if t["guidance"]:
        guidance = "\n## What a useful result looks like (the guide's notes)\n\n" + "\n\n".join(t["guidance"]) + "\n"
    return f"""
# {t['title']}

Copy-ready task template from the owner's {GUIDE_TITLE}, section "Copy-ready task templates". The quoted task is
the owner's text, unchanged; only the input line is added.

**Input ({input_what}):** $ARGUMENTS

Fill the input with actual project data. If an input is missing, mark it unresolved rather than inventing a source,
license, test result, or customer preference.

## Task

> {t['prompt']}
{guidance}
## Using the template (the guide's rules)

{chr(10).join(f"{p}" + chr(10) for p in usage)}"""


# --------------------------------------------------------------------------- main

def main() -> int:
    if "--extract" in sys.argv:
        DATA.mkdir(parents=True, exist_ok=True)
        for name, value in extract().items():
            (DATA / name).write_text(dumps(value), encoding="utf-8")
            print(f"wrote {DATA / name}")
        return 0

    data = load_data()
    bank = data["appendix_e_questions.json"]
    secs = data["review_sections.json"]
    tpl = data["templates.json"]
    questions, areas, passes = bank["questions"], bank["areas"], bank["passes"]
    by_area = {a["domain_id"]: [q for q in questions if q["domain_id"] == a["domain_id"]] for a in areas}
    source_guide = {k: bank["source"][k] for k in ("file", "sha256", "bytes", "lines")}
    library = bank["library_records"]
    review_sec = secs["sections"]["Adversarial review without checklist theater"]
    intake_sec = secs["sections"]["Reusable components and actual intake"]
    exp_sec = secs["sections"]["Bounded adoption experiments"]
    next_sec = secs["sections"]["Practical next steps"]
    appendix_anchor = "appendix-e-all-1024-adversarial-review-questions"

    q_schema = question_schema(bank)
    r_schema = result_schema()
    validate_against(q_schema, questions, "the 1,024 transcribed questions")
    examples = result_examples()
    validate_against(r_schema, [v for k, v in examples.items() if "/invalid" not in k], "valid result examples")

    bank_notes = ("Transcribed verbatim from Appendix E (lines {lo}-{hi} of the guide file, SHA-256 {sha}). The guide "
                  "states the source bank (Library libfile_40e3c6edac1c8191b3fe1ffed949ef9b v0, 980,912 bytes) was "
                  "demonstrated with selection and evidence contracts, 39 validator regression tests and bounded "
                  "applications to actual films (a 17-record focused application; BOXED IN's later 32-record review). "
                  "That does not mean any question here was executed on a film; the bank is a menu, not completed tests.")
    review_tags = ["video", "animation", "adversarial-review", "review-questions"]
    rev = {"status": "automated-passed", "checked": "2026-10-10",
           "notes": "Generator asserts 1,024 questions with unique ids, 32 per area, nine passes matching declared counts, "
                    "and every record valid against the adversarial_question schema."}

    with GeneratorRun(__file__, data="generators/data/ref_review_templates") as run:
        # ---- contract schemas
        q_examples = {
            "examples/avq-001-001-concept-first-image.json": next(q for q in questions if q["id"] == "AVQ-001-001"),
            "examples/avq-022-001-listening-question.json": next(q for q in questions if q["id"] == "AVQ-022-001"),
            "examples/avq-029-001-machine-question.json": next(q for q in questions if q["id"] == "AVQ-029-001"),
            "examples/invalid-unknown-severity.json": dict(next(q for q in questions if q["id"] == "AVQ-001-001"),
                                                           severity="urgent"),
            "examples/invalid-missing-check-or-fix.json": {k: v for k, v in questions[0].items() if k != "check_or_fix"},
        }
        run.component(
            "contract-schema", "adversarial_question",
            title="Adversarial review question",
            summary="JSON Schema for one question of the owner's 1,024-question review bank: AVQ id, area, exact question, "
                    "failure hypothesis, check or fix, severity, modes, stages, style filters, named passes.",
            description=AUTHORITY,
            subkind="review-lens", domain="video",
            files={"schema.json": dumps(q_schema), **{k: dumps(v) for k, v in q_examples.items()}},
            tags=review_tags + ["schema", "contract"],
            step_kinds=["review", "verify"],
            source=src(appendix_anchor),
            evidence_stage="isolated-execution",
            evidence_notes="All 1,024 transcribed questions validate against this schema (jsonschema, Draft 2020-12) in "
                           "the generator run, and the examples validate in the catalogue validator. Field names follow "
                           "the appendix's own labels.",
            review=rev,
        )
        run.component(
            "contract-schema", "adversarial_review_result",
            title="Adversarial review result record",
            summary="JSON Schema for one review answer: target hash, status (untested/observed-pass/observed-fail/blocked/"
                    "not-applicable), finding type, scope and hashed evidence with method, locator, coverage, limits.",
            description=AUTHORITY + " The record shape is the guide's own example (included verbatim as an example); "
                        "evidence items carry the fields the guide requires of real evidence.",
            subkind="evaluator", domain="video",
            files={"schema.json": dumps(r_schema), **{k: dumps(v) for k, v in examples.items()}},
            tags=review_tags + ["schema", "evidence", "contract"],
            step_kinds=["review", "verify"],
            source=src("evidence-states"),  # heading "### Evidence states" (unique anchor in the guide)
            depends_on=[{"identity": "adversarial_question"}],
            evidence_stage="isolated-execution",
            evidence_notes="Valid and invalid examples behave as labelled under jsonschema Draft 2020-12. The guide's own "
                           "untested record is an example verbatim; the other valid examples are illustrative with "
                           "synthetic hashes. Not yet used to record a review of a real film through this package.",
        )

        # ---- code module
        mod_dir = DATA / "modules"
        run.component(
            "code-module", "adversarial_review_kit",
            title="Adversarial review kit",
            summary="Selects a named pass or filtered questions from the owner's bank, plans honest starting records, and "
                    "fails stale hashes, absent intervals, unsupported coverage and waveform-passed listening questions.",
            description=AUTHORITY + " Standard library only. Reads the review_bank_<area> questions.json files and the "
                        "nine named passes (passes.json, shipped here).",
            subkind="evaluator", domain="video",
            files={
                "adversarial_review_kit.py": (mod_dir / "adversarial_review_kit.py").read_text(encoding="utf-8"),
                "test_adversarial_review_kit.py": (mod_dir / "test_adversarial_review_kit.py").read_text(encoding="utf-8"),
                "passes.json": dumps(passes),
            },
            entry="adversarial_review_kit.py",
            tags=review_tags + ["validator", "python", "evidence"],
            step_kinds=["review", "verify", "test"],
            source=src(review_sec["anchor"]),
            effects_=effects(filesystem="read", executes="python",
                             side_effects=["reads question banks and result files; hashes the target file"]),
            depends_on=[{"identity": "adversarial_review_result"}, {"identity": "adversarial_question"}],
            evidence_stage="headless-tested",
            evidence_notes="Focused tested in the guide's sense: the shipped pytest suite (positive, boundary and negative "
                           "cases, including the guide's own record) passes with Python 3 in this repository. It is a new "
                           "implementation of the guide's stated rules, not the source bank's 39-test validator suite, "
                           "and has not been used on a real film review.",
        )

        # ---- one rules package and one lens per area
        index_rows = []
        for area in areas:
            qs = by_area[area["domain_id"]]
            facts = area_facts(area, qs, passes)
            bank_id = f"review_bank_{area['slug']}"
            lens_id = f"review_lens_{area['slug']}"
            lines = [q["source_line"] for q in qs]
            prov = {
                "guide": source_guide,
                "section": f"Appendix E / {area['domain_id']} {area['area']}",
                "heading_line": area["heading_line"],
                "question_lines": [min(lines), max(lines)],
                "anchor": area["anchor"],
                "library_records": library,
                "library_note": "Library identities are retrieval references, not public sharing links (Appendix G).",
                "extracted": "2026-10-10",
            }
            sev = facts["severity"]
            rules_md = bank_rules_md(area, qs, facts, bank["intro"])
            roundtrip_check(rules_md, qs)
            run.component(
                "rules", bank_id,
                title=f"Review bank: {area['area']} ({area['domain_id']})",
                summary=f"The owner's 32 adversarial review questions for {area['area']} ({area['domain_id']}), exact text, "
                        f"with failure hypothesis, check or fix, severity, modes, stages and named passes.",
                description=AUTHORITY + f" Area {area['domain_id']} {area['area']}: "
                            f"{counter_text(sev, ['critical', 'high', 'medium', 'low'])} severity.",
                subkind="review-lens", domain="video",
                files={"RULES.md": rules_md,
                       "questions.json": dumps(qs), "provenance.json": dumps(prov)},
                tags=review_tags + [area["slug"].replace("_", "-")[:40]],
                step_kinds=["review", "verify"],
                source=src(area["anchor"]),
                evidence_stage="source-inspected",
                evidence_notes=bank_notes.format(lo=min(lines), hi=max(lines), sha=source_guide["sha256"][:16] + "..."),
                review=rev,
            )
            run.component(
                "subagent", lens_id,
                title=f"Review lens: {area['area']} ({area['domain_id']})",
                summary=f"Applies the owner's 32 {area['area']} questions to a brief, storyboard or exact final encode and "
                        "returns ranked, evidence-backed findings plus what was not checked.",
                description=AUTHORITY + f" The lens embeds the {area['domain_id']} questions verbatim and returns "
                            "adversarial_review_result records.",
                subkind="review-lens", domain="video",
                files={"agent.md": lens_md(area, qs, facts, bank_id)},
                tags=review_tags + ["subagent", area["slug"].replace("_", "-")[:40]],
                step_kinds=["review", "verify"],
                source=src(area["anchor"]),
                effects_=effects(filesystem="write", executes="shell",
                                 side_effects=["runs sha256sum, ffprobe and ffmpeg on the artifact under review",
                                               "writes extracted frames and contact sheets to a scratch directory"]),
                harnesses=AGENT_HARNESSES,
                depends_on=[{"identity": bank_id}, {"identity": "adversarial_review_result"},
                            {"identity": "adversarial_review_without_theater"}],
                evidence_stage="considered",
                evidence_notes="Agent definition written for this catalogue from the guide's method and the area's "
                               "questions; it has not been run on a film. Its questions are the owner's exact text.",
            )
            index_rows.append({
                "domain_id": area["domain_id"], "area": area["area"], "questions": len(qs),
                "first_id": qs[0]["id"], "last_id": qs[-1]["id"],
                "rules_package": bank_id, "lens_subagent": lens_id, "anchor": area["anchor"],
                "severity": {k: sev[k] for k in ("critical", "high", "medium", "low") if sev.get(k)},
                "needs_listening": len(facts["listening"]), "needs_human_audience": len(facts["audience"]),
            })

        # ---- index
        total = sum(r["questions"] for r in index_rows)
        assert total == EXPECTED_QUESTIONS
        sev_all = Counter(q["severity"] for q in questions)
        pass_areas = {pid: sorted({i[4:7] for i in p["question_ids"]}) for pid, p in passes.items()}
        index_md = f"""# Adversarial review bank index: 32 areas, 1,024 questions, nine passes

{AUTHORITY}

The final bank contains 1,024 authored questions in 32 domains, with nine defined passes. It is a searchable
diagnostic resource, not 1,024 people, audience responses, completed tests, or production capabilities. A default
pass selects 32 questions. Domain-specific passes contain 50–64 questions; the longer-cardboard pass selects 32.
Applicability depends on the feature and evidence, not on a tag alone.

{bullets(bank["intro"])}

Severity across the bank: {counter_text(sev_all, ['critical', 'high', 'medium', 'low'])}.

## Areas

| Id | Area | Questions | Rules package | Lens subagent | Need listening | Need audience |
|---|---|---:|---|---|---:|---:|
{chr(10).join(f"| {r['domain_id']} | {r['area']} | {r['questions']} | `{r['rules_package']}` | `{r['lens_subagent']}` | {r['needs_listening']} | {r['needs_human_audience']} |" for r in index_rows)}
| | **Total** | **{total}** | | | | |

## Named review passes

| Pass | Purpose | Questions | Areas drawn on |
|---|---|---:|---|
{chr(10).join(f"| `{pid}` | {p['purpose']} | {p['declared_count']} | {', '.join('D' + a for a in pass_areas[pid])} |" for pid, p in passes.items())}

The exact ordered question ids of every pass are in `passes.json` (as listed in Appendix E). The
`adversarial_review_kit` module selects a pass across the loaded area banks.

## Provenance

`provenance.json` records the guide file hash and the Library records the guide gives for the source bank
(Appendix G). Library identities are retrieval references, not public sharing links.
"""
        run.component(
            "rules", "review_bank_index",
            title="Review bank index (1,024 questions)",
            summary="Index of the owner's adversarial review bank: 32 areas x 32 questions with their rules packages and "
                    "lenses, and the nine named passes with exact ordered question ids.",
            description=AUTHORITY,
            subkind="review-lens", domain="video",
            files={
                "RULES.md": index_md,
                "index.json": dumps({"total_questions": total, "areas": index_rows,
                                     "severity": dict(sev_all), "passes": {pid: {"purpose": p["purpose"],
                                                                                 "questions": p["declared_count"]}
                                                                           for pid, p in passes.items()}}),
                "passes.json": dumps(passes),
                "provenance.json": dumps({"guide": source_guide, "section": "Appendix E All 1024 adversarial review questions",
                                          "lines": list(RANGE_APPENDIX_E), "anchor": appendix_anchor,
                                          "library_records": library, "extracted": "2026-10-10",
                                          "earlier_related_artifact": {
                                              "artifact": "Adversarial Review Configurations and Questions v1.0.0.zip",
                                              "library_identity": "libfile_3c1d6989163c8191afaa24ad0c868808",
                                              "version": 0,
                                              "sha256": "e42106fc67003cf15217ad857e2acbeeec438d1a2478223ad3914eb40a868314",
                                              "recorded_in": "docs/reference/Creative_Media_Game_Reference_2026-10-10.md",
                                              "note": "Earlier (evidence AV-20261005-074) artifact; the guides do not state "
                                                      "that it is the same as the 10 Oct 1,024-question bank."}}),
            },
            tags=review_tags + ["index", "review-passes"],
            step_kinds=["review", "verify", "plan"],
            source=src(appendix_anchor),
            depends_on=[{"identity": r["rules_package"]} for r in index_rows],
            evidence_stage="source-inspected",
            evidence_notes=bank_notes.format(lo=RANGE_APPENDIX_E[0], hi=RANGE_APPENDIX_E[1],
                                             sha=source_guide["sha256"][:16] + "..."),
            review=rev,
        )

        # ---- skill: the method
        pass_table = "\n".join(
            f"| `{pid}` | {p['purpose']} | {p['declared_count']} | {', '.join('D' + a for a in pass_areas[pid])} |"
            for pid, p in passes.items())
        area_table = "\n".join(f"| {r['domain_id']} | {r['area']} | `{r['rules_package']}` | `{r['lens_subagent']}` |"
                               for r in index_rows)
        skill_body = f"""
# Adversarial review without checklist theater

{AUTHORITY}

Source: {GUIDE_TITLE}, "Adversarial review without checklist theater" and Appendix E. The guide's section is in
`references/guide-section.md` verbatim.

## What the bank is, and is not

The final bank contains 1,024 authored questions in 32 domains, with nine defined passes. It is a searchable
diagnostic resource, not 1,024 people, audience responses, completed tests, or production capabilities. Applicability
depends on the feature and evidence, not on a tag alone. Technical completeness, a long runtime, and a large question
bank do not establish watchability.

## When to run it

1. **Planning pass** on the brief, storyboard and source state. Final-pixel and listening questions remain `untested`
   or `blocked` here.
2. **Final pass** on the exact final encode: hash the delivered bytes; never review pre-encode frames in its place.
3. **Targeted pass** after a material camera, rig, sound, caption, factual or rights change: recheck the changed beat
   and neighbouring beats.
4. **Stop** after the bounded pass and necessary repairs. Do not execute every question to manufacture impressive totals.

## Choose a pass

| Pass | Purpose | Questions | Areas |
|---|---|---:|---|
{pass_table}

For a deep look at one area, use that area's lens subagent (below). The default pass takes one question per area.

## Evidence states

- `untested`: insufficient observation to answer the question; the default.
- `observed-pass`: exact evidence supports a bounded statement for this target.
- `observed-fail`: matching direct evidence shows a defect.
- `blocked`: the check applies, but required access or evidence is missing.
- `not-applicable`: the relevant feature is absent, with a stated reason.

Use `demonstrated_defect` only with an observed failure. Use `potential_improvement` for a design hypothesis that still
needs comparison.

## What evidence must carry

Real evidence includes its own hash, the target movie hash, the extraction or observation method, locator, coverage,
and limitations. These fail validation: nonfinite numbers, absent intervals, stale target hashes and unsupported
claimed coverage. Do not retarget a contact sheet to a changed movie by editing its label. Do not mark a
listening-only question passed using a waveform statistic.

The guide's own record (an `adversarial_review_result` instance):

```json
{json.dumps(GUIDE_RECORD, indent=2)}
```

## No theater: the working rules

- **No rubber-stamping.** `observed-pass` needs exact evidence for this target; anything else stays `untested`,
  `blocked` or `not-applicable` with its reason.
- **Measure.** Decode the actual file, probe it, hash it; quote values and frame numbers rather than impressions.
- **Cite.** Every finding names its locator (frame range, timestamp, file) and evidence hash.
- **Say what was not checked.** The report lists every untested and blocked question and why; a count of passes is
  never the headline.
- **Rank by the viewer.** Order findings by impact on the intended viewer task; separate taste from objective error
  and from measured audience results.
- **Listen for real.** Listening questions need an actual listening pass of the final audio. Synthetic critique is
  not audience validation.
- **Respect the viewer's verdict.** A viewer may dislike a story despite all measured technical gates passing; this
  is meaningful feedback and should guide the next story, not be dismissed by the checklist.

## Tools in this catalogue

| Id | Area | Question bank (rules) | Lens (subagent) |
|---|---|---|---|
{area_table}

- `review_bank_index`: areas, counts and the nine passes with exact ordered ids.
- `adversarial_question` and `adversarial_review_result`: the record contracts.
- `adversarial_review_kit`: `select` a pass, `plan` honest starting records, `validate` results against the target
  hash, `summary` of statuses and what was not checked.

```bash
python3 adversarial_review_kit.py plan --bank .baltor/rules --pass default_32 --target final.mp4 \\
  --stage final-encode --modes visual,machine > review.json
# ...observe, then update records with evidence...
python3 adversarial_review_kit.py validate review.json --bank .baltor/rules --target final.mp4
```

## What has been observed with this method (the guide's record; do not generalise)

The earlier focused film application contains 17 scoped records: eleven observed passes, four untested potential
improvements, and two audio blockers. The validator suite reports 39 passing regression tests. Three contact-sheet
lineages were reproduced from exact MP4s, with matching byte or pixel evidence. Those results protect the review
contract; they do not establish that the whole films were watched continuously or listened to independently.
"""
        skill_desc = ("Use before a substantial render and again on the exact final encode of an animation or video, or "
                      "after a material camera, rig, sound, caption, factual or rights change. Runs a bounded pass of the "
                      "owner's 1,024-question adversarial review bank with explicit evidence states, hashed evidence and "
                      "a list of what was not checked; never a rubber stamp.")
        run.component(
            "skill", "adversarial_review_without_theater",
            title="Adversarial review without checklist theater",
            summary="Bounded adversarial review of a film: pick a named pass, review the brief then the exact final "
                    "encode, record untested/observed/blocked/not-applicable with hashed evidence, say what was not checked.",
            description=AUTHORITY,
            subkind="review-lens", domain="video",
            files={
                "SKILL.md": skill_md("adversarial-review-without-theater", skill_desc, skill_body),
                "references/guide-section.md": f"# {GUIDE_TITLE}: Adversarial review without checklist theater\n\n"
                                               f"Verbatim from `{GUIDE_REL}` lines {review_sec['line']}-{review_sec['end_line']}.\n\n"
                                               f"## Adversarial review without checklist theater\n\n{review_sec['markdown']}\n",
                "references/passes.json": dumps(passes),
            },
            tags=review_tags + ["method", "evidence", "qa"],
            step_kinds=["review", "verify"],
            source=src(review_sec["anchor"]),
            effects_=effects(filesystem="read", executes="shell",
                             side_effects=["hashes, probes and decodes the artifact under review"]),
            depends_on=[{"identity": "review_bank_index"}, {"identity": "adversarial_review_result"},
                        {"identity": "adversarial_review_kit"}],
            evidence_stage="source-inspected",
            evidence_notes="Method taken from the guide's section. The guide records a 17-record focused film application "
                           "(11 observed passes, 4 untested potential improvements, 2 audio blockers), 39 passing validator "
                           "regression tests and 3 contact-sheet lineages reproduced from exact MP4s; it says these do not "
                           "establish that whole films were watched continuously or listened to independently.",
        )

        # ---- commands: one per copy-ready template
        titles = [t["title"] for t in tpl["templates"]]
        assert sorted(titles) == sorted(TEMPLATE_META), set(titles) ^ set(TEMPLATE_META)
        command_rows = []
        for t in tpl["templates"]:
            meta = TEMPLATE_META[t["title"]]
            ident, hint, _what, steps, tags, fs = meta
            first = re.split(r"(?<=[.!?])\s", t["prompt"].strip("“”\""), maxsplit=1)[0]
            summary = f"Owner's copy-ready task template, verbatim: {first}"
            if len(summary) > 240:
                summary = summary[:236].rsplit(" ", 1)[0] + " ..."
            run.component(
                "command", ident,
                title=f"/{ident.replace('_', '-')}",
                summary=summary,
                description=f"The owner's copy-ready task template \"{t['title']}\" ({GUIDE_TITLE}), with the template "
                            "text unchanged and its inputs passed as $ARGUMENTS. Instructions for bounded work, not a "
                            "guarantee: missing inputs are marked unresolved, never invented.",
                subkind="prompt-template", domain="video",
                files={"command.md": command_md(f"{t['title']} (owner's copy-ready template)",
                                                command_body(t, meta, tpl["usage"]), argument_hint=hint)},
                tags=["video", "animation", "task-template"] + tags,
                step_kinds=steps,
                source=src(t["anchor"]),
                effects_=effects(filesystem=fs),
                harnesses=AGENT_HARNESSES,
                evidence_stage="considered",
                evidence_notes="Prompt template from the guide. The guide calls the templates instructions for bounded "
                               "work, not magic guarantees, and records no run of this template; a successful output "
                               "cannot be assumed reproducible from the prompt alone.",
            )
            command_rows.append((t["title"], ident, t["anchor"]))

        # ---- rules: how to use the templates
        usage_rules = [s for p in tpl["usage"] for s in re.split(r"(?<=\.)\s+(?=[A-Z])", p)]
        run.component(
            "rules", "copy_ready_task_template_rules",
            title="Rules for the copy-ready task templates",
            summary="How to use the owner's 24 copy-ready task templates: real inputs only, unresolved instead of invented, "
                    "keep prompt/inputs/output/versions/corrections, use selectively; index of the 24 commands.",
            subkind="prompt-template", domain="video",
            files={
                "RULES.md": f"""# Rules for the copy-ready task templates

Source: {GUIDE_TITLE}, "Copy-ready task templates" / "How to use the templates". The rules are the owner's sentences,
one per line.

{chr(10).join(f"{n}. {s}" for n, s in enumerate(usage_rules, 1))}

## The templates (one command each)

| Template | Command |
|---|---|
{chr(10).join(f"| {title} | `/{ident.replace('_', '-')}` |" for title, ident, _ in command_rows)}
""",
                "rules.json": dumps({"rules": usage_rules,
                                     "templates": [{"title": a, "command": b, "anchor": c} for a, b, c in command_rows]}),
            },
            tags=["video", "animation", "task-template", "rules"],
            step_kinds=["plan", "review"],
            source=src("how-to-use-the-templates"),
            depends_on=[{"identity": ident} for _, ident, _ in command_rows],
            evidence_stage="considered",
            evidence_notes="The guide's usage rules for its templates; no execution is implied.",
        )

        # ---- skill: bounded adoption experiments
        exps = secs["experiments"]
        exp_closing = [p for p in _paragraphs(exp_sec["markdown"].splitlines()) if not p.startswith("|")]
        exp_table = "\n".join(f"| {e['experiment']} | {e['intended_outcome']} | {e['evidence_needed']} | "
                              f"{e['stop_or_hold_condition']} |" for e in exps)
        exp_body = f"""
# Run a bounded adoption experiment

Source: {GUIDE_TITLE}, "Bounded adoption experiments". The table is the owner's, verbatim.

{chr(10).join(exp_closing)}

## The experiments

| Experiment | Intended outcome | Evidence needed | Stop or hold condition |
|---|---|---|---|
{exp_table}

## How to run one

1. Pick one experiment and write down its intended outcome, the evidence it needs and its stop or hold condition
   from the table before starting. One experiment at a time.
2. Check authorization first. The experiments are proposals: no new installation, paid compute, account, upload,
   outreach or publication without explicit approval. Prefer tools that are already available.
3. Build only the bounded proof the evidence column asks for (a matched short shot, representative clips, one
   collision, one insert), never a full film.
4. Compare against the current route. A new dependency should win a real comparison on quality, controllability,
   maintainability or accepted-output effort.
5. Apply the stop or hold condition literally. Record holds and blocks (access, licence, hardware, missing listener)
   as such; technical success alone does not settle a creative choice.
6. Report the result with its evidence status (proposed, invoked, focused tested, used in a film, ...) and what was
   not tested. Owner feedback, when given, is recorded as owner feedback and nothing more.

`experiments.json` holds the same rows for tools.
"""
        run.component(
            "skill", "run_bounded_adoption_experiment",
            title="Run a bounded adoption experiment",
            summary="Nine proposed adoption experiments (storyboards, rig polish, Pymunk prop, depth, voice, sketch, pixel/"
                    "block, generative insert, sound review) with the evidence each needs and when to stop or hold.",
            subkind="workflow", domain="video",
            files={
                "SKILL.md": skill_md(
                    "run-bounded-adoption-experiment",
                    "Use when considering a new style, rig, physics, depth, voice, sketch, pixel or block, generative-video "
                    "or sound-review route for an animation. Runs one of the owner's nine bounded adoption experiments with "
                    "its required evidence and stop or hold condition; proposals only, never an authorization to install, "
                    "pay, upload or publish.",
                    exp_body),
                "experiments.json": dumps({"source": src(exp_sec["anchor"]), "status": "proposed", "experiments": exps,
                                           "closing": exp_closing}),
            },
            tags=["video", "animation", "experiment", "adoption", "evaluation"],
            step_kinds=["plan", "test", "review"],
            source=src(exp_sec["anchor"]),
            evidence_stage="considered",
            evidence_notes="The guide labels these proposed adoption experiments, not authorizations. None is recorded "
                           "as run in this section.",
        )

        # ---- rules: reusable components and actual intake
        intake_paras = _paragraphs(intake_sec["markdown"].splitlines())
        states = ["authored", "rights-reviewed", "focused-tested", "source-reopened", "minimally invoked by a consumer",
                  "actual isolated intake-qualified", "admitted", "published", "used successfully"]
        assert all(s in intake_sec["markdown"] for s in states), "intake states drifted from the guide"
        intake_library = [
            {"name": "motion_helpers", "library_identity": "libfile_9da84ebd1d808191ae0300c7c98199bb",
             "recorded": "catalogue record reports 48 tests",
             "does_not_establish": ["native intake", "final-film adoption for every helper", "universal compatibility"]},
            {"name": "Pymunk recovery package", "library_identity": "libfile_98caae390d188191a2e432cf29728cff",
             "version": 0, "recorded": "single props-only trace capability with its own test scope"},
        ]
        intake_md = f"""# Reusable components and actual intake

Source: {GUIDE_TITLE}, "Reusable components and actual intake". Rules are the owner's sentences, lightly numbered.

## Extract

1. Extract the smallest task that saved effort in a completed episode: crop planning, text fit, anchor projection,
   two-bone contact, prop ownership, timeline validation, mask-to-answer joins, audio ducking, chunk verification, or
   final-stream inspection.
2. Keep episode content in data. A renamed whole-film script is not automatically a reusable library.

## Define

3. Define each component's inputs, outputs, errors, dependencies, time/resource limits, deterministic behavior and
   effects.
4. A crop planner should not access the network; a renderer should not publish; a source check should not create
   accounts.

## Test

5. Test positive cases, boundaries, known-wrong consumers and failure behavior.
6. Keep the real failed fixture when it teaches a useful boundary.

## Keep the states separate

7. Keep these states separate: {", ".join(states[:-1])}, and {states[-1]}. One never implies the next.
8. Neutral packages stay neutral until the real current target contract is inspected and tested.
9. Do not invent producer/source bindings, write directly to a production database, bypass admission, or infer
   publication from a private Library save.

## Recorded examples (status as the guide gives it)

- The earlier original `motion_helpers` candidate is retained as Library `libfile_9da84ebd1d808191ae0300c7c98199bb`;
  its catalogue record reports 48 tests. That record does not establish native intake, final-film adoption for every
  helper, or universal compatibility.
- The Pymunk recovery package is `libfile_98caae390d188191a2e432cf29728cff` v0; its single props-only trace capability
  has its own test scope.

## The guide's text

{(chr(10) + ">" + chr(10)).join("> " + p for p in intake_paras)}
"""
        run.component(
            "rules", "reusable_component_intake_rules",
            title="Reusable component intake rules",
            summary="Extract the smallest effort-saving task, declare inputs/outputs/errors/limits/effects, test boundaries "
                    "and known-wrong consumers, and keep authored, tested, intake-qualified, admitted and published apart.",
            subkind="rule-set", domain="video",
            files={
                "RULES.md": intake_md,
                "rules.json": dumps({
                    "candidate_tasks": ["crop planning", "text fit", "anchor projection", "two-bone contact",
                                        "prop ownership", "timeline validation", "mask-to-answer joins", "audio ducking",
                                        "chunk verification", "final-stream inspection"],
                    "component_definition": ["inputs", "outputs", "errors", "dependencies", "time/resource limits",
                                             "deterministic behavior", "effects"],
                    "effect_boundaries": {"crop planner": "no network access", "renderer": "does not publish",
                                          "source check": "does not create accounts"},
                    "tests": ["positive cases", "boundaries", "known-wrong consumers", "failure behavior"],
                    "separate_states": states,
                    "never": ["invent producer/source bindings", "write directly to a production database",
                              "bypass admission", "infer publication from a private Library save"],
                }),
                "provenance.json": dumps({"guide": source_guide, "section": "Reusable components and actual intake",
                                          "line": intake_sec["line"], "anchor": intake_sec["anchor"],
                                          "library_records": intake_library}),
            },
            tags=["components", "intake", "testing", "provenance", "rules"],
            step_kinds=["build", "test", "review"],
            source=src(intake_sec["anchor"]),
            evidence_stage="source-inspected",
            evidence_notes="Rules transcribed from the guide. Recorded examples keep their stated limits: motion_helpers "
                           "(libfile_9da84ebd1d808191ae0300c7c98199bb) reports 48 tests but not native intake, adoption of "
                           "every helper or universal compatibility; the Pymunk recovery package "
                           "(libfile_98caae390d188191a2e432cf29728cff v0) has a props-only trace scope.",
        )

        # ---- instruction file: practical next steps
        ns = secs["next_steps"]
        run.component(
            "instruction-file", "story_first_production_next_steps",
            title="Story-first production next steps",
            summary="CLAUDE.md / AGENTS.md section with the owner's seven next steps: stronger storyboards before renders, "
                    "one hard-action proof, one new style at a time, honest status, refreshed licences.",
            subkind="step-template", domain="video",
            files={"INSTRUCTIONS.md": f"""## Story-first production: next steps (owner's guide, 10 Oct 2026)

From the {GUIDE_TITLE}, "Practical next steps". These are the owner's stated priorities, verbatim; none is recorded as
done here.

{chr(10).join(f"{n}. {s}" for n, s in enumerate(ns['steps'], 1))}

{chr(10).join(ns['closing'])}
"""},
            tags=["video", "animation", "story", "priorities", "agents-md"],
            step_kinds=["plan", "write"],
            source=src(next_sec["anchor"]),
            evidence_stage="considered",
            evidence_notes="Owner's next steps as of 10 Oct 2026; they are plans, not completed work.",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
