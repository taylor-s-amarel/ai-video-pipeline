#!/usr/bin/env python3
"""Story components from the owner's Animation and Video Production Master Guide (v1.1, 10 October 2026).

Sources (``docs/reference/Animation_and_Video_Production_Master_Guide_2026-10-10.md``):

* "Story quality comes before production scale": the BOXED IN lesson, the story
  contract, comedy mechanisms, suspense, the storyboard gate and the longer-film
  structure -> rules packages ``story_contract_rules``, ``storyboard_gate``,
  ``comedy_mechanisms``, ``suspense_rules`` and the ``story_contract`` schema.
* "New suspense and comedy storyboards": three timed boards and five pitches
  (the eight-story development slate) -> eight ``storyboard`` skills, the
  ``timed_storyboard`` schema, ``story_tests`` rules and a slate overview.
* Appendix C: creative banks and exact treatment addressing -> nine idea-bank
  skills, the ``treatment_address`` schema and the ``treatment_address_resolver``
  code module.
* Appendix D: all 240 story premises -> 240 ``story_premise_*`` skills (each with
  ``premise.json``) and the ``story_premise`` schema.

Plus a ``story_doctor`` subagent, a ``storyboard_before_render`` command and the
``timed_storyboard_check`` code module.

The guide is parsed by ``data/ref_stories/parse_guide.py`` (sections found by
heading, not line number); the parsed records are cached in
``data/ref_stories/extracted/`` so the generator still runs if the guide moves.
Every status stays at what the guide records: premises are ideas, boards are
proposed and unrendered, banks are proposals. Nothing here is upgraded.

Run: ``cd baltor/generators && python3 ref_stories.py``
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import sys
from pathlib import Path

from _lib import REPO_URL, GeneratorRun, agent_md, command_md, dumps, effects, skill_md

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "ref_stories"
DATA_REL = "generators/data/ref_stories"
MODULES = DATA / "modules"
sys.path.insert(0, str(DATA))
import parse_guide as pg  # noqa: E402

if pg.GUIDE.exists():
    D = pg.parse_all(pg.GUIDE)
    pg.write_extracted(D)
else:  # pragma: no cover - fallback when the guide is not checked out
    D = pg.load_extracted()

GUIDE_REL = pg.GUIDE_REL
GUIDE_TITLE = "Animation and Video Production Master Guide (v1.1, 10 October 2026)"
SQ = D["story_quality"]
SLATE = D["slate"]
APPC = D["appendix_c"]
APPD = D["appendix_d"]
PROV = D["provenance"]
PREMISES = APPD["premises"]
BANKS = APPC["banks"]
CAT = PROV["creative_catalogue_bundle"]
SLATE_STATUS = re.sub(r"^Status:\s*", "", SLATE["status"])
SLATE_STATUS = SLATE_STATUS[:1].upper() + SLATE_STATUS[1:]

# ----------------------------------------------------------------------------- counts the guide states
assert len(PREMISES) == 240, f"expected 240 premises, parsed {len(PREMISES)}"
assert len({p["id"] for p in PREMISES}) == 240
assert sum(p["family"] == "learning" for p in PREMISES) == 120
assert sum(p["family"] == "fiction" for p in PREMISES) == 120
_EXPECTED_BANKS = {"hooks": 60, "intros": 30, "styles": 40, "motions": 30, "formats": 20, "axes": 25,
                   "style_applications": 18, "top_picks": 20}
for _k, _n in _EXPECTED_BANKS.items():
    assert len(BANKS[_k]["records"]) == _n, f"bank {_k}: expected {_n}, parsed {len(BANKS[_k]['records'])}"
assert len(APPC["count_contract"]["approaches"]["records"]) == 4
assert len(SLATE["boards"]) == 3 and len(SLATE["pitches"]) == 5
assert all(len(b["shots"]) == b["shot_count"] == 10 for b in SLATE["boards"])
assert len(SQ["story_contract"]["sentences"]) == 9
assert len(SQ["comedy_mechanisms"]["records"]) == 10
assert len(SQ["storyboard_gate"]["questions"]) == 10
assert len(SLATE["story_tests"]["questions"]) == 7
assert len(SLATE["story_tests"]["global_kill_criteria"]) == 7
_GROUP_STORIES = [s for g in APPC["treatment_map"]["groups"] for s in g["stories"]]
assert sorted(_GROUP_STORIES) == sorted(p["id"] for p in PREMISES), "treatment groups must cover every premise once"
assert all(len(g["rows"]) == 10 for g in APPC["treatment_map"]["groups"])
assert len(_GROUP_STORIES) * 10 == 2400

# ----------------------------------------------------------------------------- lookups
FORMATS = {r["id"]: r for r in BANKS["formats"]["records"]}
INTROS = {r["id"]: r for r in BANKS["intros"]["records"]}
MOTIONS = {r["id"]: r for r in BANKS["motions"]["records"]}
STYLES = BANKS["styles"]["records"]
APPROACHES = {r["id"]: r for r in APPC["count_contract"]["approaches"]["records"]}
GROUP_OF = {s: g for g in APPC["treatment_map"]["groups"] for s in g["stories"]}
SU_BY_STORY = {r["story"]: r for r in BANKS["style_applications"]["records"]}
PICK_BY_STORY = {r["story"]: r for r in BANKS["top_picks"]["records"]}
EDITORIAL_RULES = {r.split(" ", 1)[0]: r for r in APPC["treatment_map"]["editorial_rules"]}
_COMBO = " ".join(APPC["treatment_map"]["editorial_rules_after"])
COMBINATION_RULES = {
    "learning": next(s for s in re.split(r"(?<=\.)\s+", _COMBO) if s.startswith("Learning combinations")),
    "fiction": next(s for s in re.split(r"(?<=\.)\s+", _COMBO) if s.startswith("Fiction combinations")),
    "every": next(s for s in re.split(r"(?<=\.)\s+", _COMBO) if s.startswith("Every combination")),
}
# Representation approach -> renderer family named in the forty-style bank's "Approaches" column.
# This join is made by the generator from the approach names; the guide does not tabulate it.
APPROACH_FAMILY = {"A01": "vector", "A02": "sketch", "A03": "block3d", "A04": "cutout"}

CONTRACT = SQ["story_contract"]["sentences"]
GATE_QUESTIONS = SQ["storyboard_gate"]["questions"]
STORY_TESTS = SLATE["story_tests"]
KILL = STORY_TESTS["global_kill_criteria"]
KILL_CLOSING = "A technically clean render does not rescue any of these."
assert KILL_CLOSING in STORY_TESTS["global_kill_criteria_text"]

CAT_REF = (f"{CAT['artifact']} (Library `{CAT['library_identity']}` v{CAT['version_read']}, "
           f"{CAT['bytes']} bytes, SHA-256 `{CAT['sha256']}`)")
CAT_REF_PLAIN = (f"{CAT['artifact']}, Library {CAT['library_identity']} v{CAT['version_read']}, "
                 f"SHA-256 {CAT['sha256']}")

# identities
ID_PREMISE_SCHEMA = "story_premise"
ID_BOARD_SCHEMA = "timed_storyboard"
ID_CONTRACT_SCHEMA = "story_contract"
ID_ADDRESS_SCHEMA = "treatment_address"
ID_CONTRACT_RULES = "story_contract_rules"
ID_GATE = "storyboard_gate"
ID_COMEDY = "comedy_mechanisms"
ID_SUSPENSE = "suspense_rules"
ID_TESTS = "story_tests"
ID_DOCTOR = "story_doctor"
ID_COMMAND = "storyboard_before_render"
ID_CHECK = "timed_storyboard_check"
ID_RESOLVER = "treatment_address_resolver"
ID_SLATE = "suspense_comedy_development_slate"


def source(anchor: str, notes: str | None = None) -> dict:
    out = {"type": "original", "url": REPO_URL, "upstream": f"{GUIDE_REL}#{anchor}"}
    if notes:
        out["notes"] = notes
    return out


def slug(text: str) -> str:
    text = text.replace("’", "").replace("'", "").lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def tag(text: str) -> str:
    return re.sub(r"[^a-z0-9+.-]+", "-", text.lower()).strip("-")[:41]


def truncate_identity(prefix: str, rest: str, limit: int = 64) -> str:
    ident = f"{prefix}_{rest}"
    if len(ident) <= limit:
        return ident
    words = rest.split("_")
    while words and len(f"{prefix}_{'_'.join(words)}") > limit:
        words.pop()
    return f"{prefix}_{'_'.join(words)}"


def clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"'(*])", text) if s.strip()]


def blocks(paras: list[str]) -> list[str]:
    """Markdown lines for a list of paragraphs, each followed by a blank line."""
    out: list[str] = []
    for para in paras:
        out += [para, ""]
    return out


def md_table(columns: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


def premise_identity(p: dict) -> str:
    return truncate_identity("story_premise", f"{p['id'].lower()}_{slug(p['title'])}")


PREMISE_ID = {p["id"]: premise_identity(p) for p in PREMISES}
PREMISE_BY_ID = {p["id"]: p for p in PREMISES}
assert len(set(PREMISE_ID.values())) == 240


def treatments(p: dict) -> list[dict]:
    group = GROUP_OF[p["id"]]
    return [{"address": f"R-{p['id']}-{r['format']}-{r['approach']}", "format_id": r["format"],
             "approach_id": r["approach"], "intro_id": r["intro"], "motion_id": r["motion"]} for r in group["rows"]]


# ----------------------------------------------------------------------------- shared text blocks

def contract_lines() -> list[str]:
    return [f"- **{s['label']}:** {s['question']}" for s in CONTRACT]


def gate_lines() -> list[str]:
    return [f"{n}. {q}" for n, q in enumerate(GATE_QUESTIONS, 1)]


def story_test_lines() -> list[str]:
    return [f"{n}. {q}" for n, q in enumerate(STORY_TESTS["questions"], 1)]


def kill_lines() -> list[str]:
    return [f"- {k}" for k in KILL]


STATUS_LADDER_NOTE = (
    "Status language: an idea or proposal is not a script; a storyboard is not a render; a render is not "
    "a delivery; a technical delivery is not creative acceptance; an editorial review is not audience evidence. "
    "Record the strongest stage actually observed and never upgrade it.")


# ============================================================================= contract schemas

FORMAT_TAGS = sorted({t for p in PREMISES for t in p["original_format_tags"]})
EVIDENCE_CLASSES = sorted({p["evidence_class"] for p in PREMISES})
PREMISE_STATUSES = ["idea", "selected", "contract-written", "storyboarded", "animatic-reviewed", "rendered",
                    "delivered", "owner-accepted", "rejected", "rewritten"]

STORY_PREMISE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": f"{REPO_URL}/baltor/contract-schemas/story-premise",
    "title": "Story premise",
    "description": ("One premise record in the shape Appendix D of the Animation and Video Production Master Guide "
                    "uses: authored premise, hook, visible action, intended takeaway or theme, gate, evidence class "
                    "and original format tags, plus its ten treatment addresses. Status starts at 'idea'; any later "
                    "status needs status_evidence. An evidence class is a checkability label, not verification."),
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "title", "family", "category", "premise", "hook", "visible_action",
                 "intended_takeaway_or_theme", "gate", "evidence_class", "original_format_tags", "status"],
    "properties": {
        "id": {"type": "string", "pattern": "^(EDU|ENT)[0-9]{3}$",
               "description": "Stable catalogue id: EDU for learning, ENT for fiction."},
        "title": {"type": "string", "minLength": 3, "maxLength": 120},
        "family": {"enum": ["learning", "fiction"]},
        "category": {"type": "string", "minLength": 3, "maxLength": 80},
        "premise": {"type": "string", "minLength": 40,
                    "description": "The authored premise paragraph: who wants what, what stands in the way and how it resolves."},
        "hook": {"type": "string", "minLength": 5},
        "visible_action": {"type": "string", "minLength": 10},
        "intended_takeaway_or_theme": {"type": "string", "minLength": 5},
        "gate": {"type": "string", "minLength": 10, "description": "The premise's own risk gate, satisfied before production."},
        "evidence_class": {"enum": EVIDENCE_CLASSES},
        "original_format_tags": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"enum": FORMAT_TAGS}},
        "status": {"enum": PREMISE_STATUSES},
        "status_evidence": {"type": "string", "minLength": 10,
                            "description": "What was observed to justify a status beyond 'idea' (who, when, which bytes)."},
        "treatment_group": {"type": "integer", "minimum": 1, "maximum": 4},
        "treatments": {
            "type": "array", "minItems": 10, "maxItems": 10,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["address", "format_id", "approach_id", "intro_id", "motion_id"],
                "properties": {
                    "address": {"type": "string", "pattern": "^R-(EDU|ENT)[0-9]{3}-F[0-9]{2}-A0[1-4]$"},
                    "format_id": {"type": "string", "pattern": "^F[0-9]{2}$"},
                    "approach_id": {"enum": ["A01", "A02", "A03", "A04"]},
                    "intro_id": {"type": "string", "pattern": "^I[0-9]{2}$"},
                    "motion_id": {"type": "string", "pattern": "^M[0-9]{2}$"},
                },
            },
        },
        "style_application": {
            "type": "object", "additionalProperties": False, "required": ["id", "treatment"],
            "properties": {k: {"type": "string"} for k in
                           ("id", "treatment", "view", "geometry", "material", "aesthetic", "layout", "why", "check")},
        },
        "editorial_pick": {
            "type": "object", "additionalProperties": False, "required": ["rank", "note"],
            "properties": {"rank": {"type": "integer", "minimum": 1, "maximum": 20},
                           "original_reason": {"type": "string"}, "proposed_first_version": {"type": "string"},
                           "gate": {"type": "string"}, "note": {"type": "string"}},
        },
        "source": {
            "type": "object", "additionalProperties": False, "required": ["document", "section"],
            "properties": {
                "document": {"type": "string"}, "section": {"type": "string"}, "anchor": {"type": "string"},
                "line": {"type": "integer", "minimum": 1},
                "catalogue_artifact": {"type": "string"},
                "catalogue_library_identity": {"type": "string", "pattern": "^libfile_[0-9a-f]{32}$"},
                "catalogue_version": {"type": "string"},
                "catalogue_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            },
        },
    },
    "allOf": [
        {"if": {"properties": {"family": {"const": "learning"}}, "required": ["family"]},
         "then": {"properties": {"id": {"pattern": "^EDU"}}}},
        {"if": {"properties": {"family": {"const": "fiction"}}, "required": ["family"]},
         "then": {"properties": {"id": {"pattern": "^ENT"}}}},
        {"if": {"properties": {"status": {"not": {"const": "idea"}}}, "required": ["status"]},
         "then": {"required": ["status_evidence"]}},
    ],
}


def premise_record(p: dict) -> dict:
    rec = {
        "id": p["id"], "title": p["title"], "family": p["family"], "category": p["category"],
        "premise": p["premise"], "hook": p["hook"], "visible_action": p["visible_action"],
        "intended_takeaway_or_theme": p["intended_takeaway_or_theme"], "gate": p["gate"],
        "evidence_class": p["evidence_class"], "original_format_tags": p["original_format_tags"],
        "status": "idea",
        "treatment_group": GROUP_OF[p["id"]]["group"],
        "treatments": treatments(p),
    }
    su = SU_BY_STORY.get(p["id"])
    if su:
        rec["style_application"] = {k: su[k] for k in ("id", "treatment", "view", "geometry", "material",
                                                       "aesthetic", "layout", "why", "check")}
    pick = PICK_BY_STORY.get(p["id"])
    if pick:
        rec["editorial_pick"] = {"rank": int(pick["rank"]), "original_reason": pick["original_reason"],
                                 "proposed_first_version": pick["proposed_first_version"], "gate": pick["gate"],
                                 "note": BANKS["top_picks"]["intro"][0]}
    rec["source"] = {"document": GUIDE_REL, "section": f"Appendix D All 240 story premises / {p['category_heading']}",
                     "anchor": p["anchor"], "line": p["line"], "catalogue_artifact": CAT["artifact"],
                     "catalogue_library_identity": CAT["library_identity"], "catalogue_version": CAT["version_read"],
                     "catalogue_sha256": CAT["sha256"]}
    return rec


BOARD_STATUSES = ["proposed", "owner-selected", "animatic-reviewed", "rendered", "delivered", "owner-accepted", "rejected"]
_TEXT = {"type": "string", "minLength": 10}
TIMED_REQUIRED = ["title", "dramatic_question", "characters_and_goals", "stakes", "escalation_chain",
                  "planted_details", "shots", "midpoint_change", "kill_criteria"]
PITCH_REQUIRED = ["title", "opening_frame", "question_and_goals", "rule", "causal_escalation", "plant_and_payoff",
                  "visual_test"]

TIMED_STORYBOARD_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": f"{REPO_URL}/baltor/contract-schemas/timed-storyboard",
    "title": "Timed storyboard or story pitch",
    "description": ("A development board in the shape of the guide's suspense and comedy boards. board_type 'timed' "
                    "needs the story fields and contiguous timed shots; board_type 'pitch' needs opening frame, "
                    "question and goals, rule, causal escalation, plant and payoff and the visual test. Shot fields "
                    "follow the storyboard gate: composition, duration, action, new information, decision, sound and "
                    "the story reason for the cut. Contiguity is checked by the timed_storyboard_check module. "
                    "Status beyond 'proposed' needs status_evidence."),
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "title", "board_type", "status"],
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{1,80}$"},
        "title": {"type": "string", "minLength": 2, "maxLength": 120},
        "board_type": {"enum": ["timed", "pitch"]},
        "status": {"enum": BOARD_STATUSES},
        "status_evidence": {"type": "string", "minLength": 10},
        "approx_duration_s": {"type": "number", "exclusiveMinimum": 0, "maximum": 900},
        "shot_count": {"type": "integer", "minimum": 1},
        "cast": {"type": "string"},
        "format_text": {"type": "string"},
        "opening_image": _TEXT, "dramatic_question": _TEXT, "characters_and_goals": _TEXT, "world_rule": _TEXT,
        "stakes": _TEXT,
        "escalation_chain": {"type": "array", "minItems": 2, "items": {"type": "string", "minLength": 3}},
        "planted_details": _TEXT,
        "shots": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["index", "start_s", "end_s", "title", "action"],
                "properties": {
                    "index": {"type": "integer", "minimum": 1},
                    "start_s": {"type": "number", "minimum": 0},
                    "end_s": {"type": "number", "exclusiveMinimum": 0},
                    "title": {"type": "string", "minLength": 2},
                    "action": {"type": "string", "minLength": 10},
                    "composition": {"type": "string"}, "new_information": {"type": "string"},
                    "decision": {"type": "string"}, "sound": {"type": "string"}, "cut_reason": {"type": "string"},
                },
            },
        },
        "midpoint_change": _TEXT, "why_watch_next_beat": _TEXT, "alternate_ending": _TEXT,
        "obvious_weakness": _TEXT, "kill_criteria": _TEXT,
        "opening_frame": _TEXT, "question_and_goals": _TEXT, "rule": _TEXT, "causal_escalation": _TEXT,
        "plant_and_payoff": _TEXT, "visual_test": _TEXT,
        "editorial_note": {"type": "string"},
        "source": {"type": "object", "additionalProperties": False, "required": ["document"],
                   "properties": {"document": {"type": "string"}, "section": {"type": "string"},
                                  "anchor": {"type": "string"}, "line": {"type": "integer", "minimum": 1}}},
    },
    "allOf": [
        {"if": {"properties": {"board_type": {"const": "timed"}}, "required": ["board_type"]},
         "then": {"required": TIMED_REQUIRED, "properties": {"shots": {"minItems": 3}}}},
        {"if": {"properties": {"board_type": {"const": "pitch"}}, "required": ["board_type"]},
         "then": {"required": PITCH_REQUIRED}},
        {"if": {"properties": {"status": {"not": {"const": "proposed"}}}, "required": ["status"]},
         "then": {"required": ["status_evidence"]}},
    ],
}


def board_record(b: dict) -> dict:
    rec = {"id": slug(b["title"]).replace("_", "-"), "title": b["title"], "board_type": "timed", "status": "proposed",
           "approx_duration_s": b["approx_duration_s"], "shot_count": b["shot_count"], "cast": b["cast"],
           "format_text": b["format_text"]}
    for k in ("opening_image", "dramatic_question", "characters_and_goals", "world_rule", "stakes"):
        rec[k] = b[k]
    rec["escalation_chain"] = b["escalation_chain"]
    rec["planted_details"] = b["planted_details"]
    rec["shots"] = [dict(s) for s in b["shots"]]
    for k in ("midpoint_change", "why_watch_next_beat", "alternate_ending", "obvious_weakness", "kill_criteria"):
        rec[k] = b[k]
    rec["editorial_note"] = SLATE["status"]
    rec["source"] = {"document": GUIDE_REL, "section": "New suspense and comedy storyboards", "anchor": b["anchor"],
                     "line": b["line"]}
    return rec


def pitch_record(p: dict) -> dict:
    rec = {"id": slug(p["title"]).replace("_", "-"), "title": p["title"], "board_type": "pitch", "status": "proposed"}
    for k in ("opening_frame", "question_and_goals", "rule", "causal_escalation", "plant_and_payoff", "visual_test"):
        rec[k] = p[k]
    rec["editorial_note"] = " ".join(SLATE["slate_intro"])
    rec["source"] = {"document": GUIDE_REL, "section": "Five more distinct topics: an eight-story development slate",
                     "anchor": p["anchor"], "line": p["line"]}
    return rec


MECHANISM_NAMES = [r["mechanism"] for r in SQ["comedy_mechanisms"]["records"]]
STORY_CONTRACT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": f"{REPO_URL}/baltor/contract-schemas/story-contract",
    "title": "Story contract",
    "description": ("The nine sentences the guide asks for before drawing shots: want, stakes, constraint, choice, "
                    "escalation, knowledge (viewer, character, still uncertain), plant, reversal and consequence. "
                    "Optional fields name the comedy mechanisms in play and the suspense question. A complete contract "
                    "is a writing gate, not evidence that the story works."),
    "type": "object",
    "additionalProperties": False,
    "required": [s["key"] for s in CONTRACT],
    "properties": {
        "title": {"type": "string", "minLength": 2},
        "premise_ref": {"type": "string", "description": "Catalogue id (EDU001), board id or path of the draft."},
        **{s["key"]: {"type": "string", "minLength": 10, "description": s["question"]}
           for s in CONTRACT if s["key"] != "knowledge"},
        "knowledge": {
            "type": "object", "additionalProperties": False, "required": ["viewer", "character", "uncertain"],
            "description": next(s["question"] for s in CONTRACT if s["key"] == "knowledge"),
            "properties": {"viewer": {"type": "string", "minLength": 5}, "character": {"type": "string", "minLength": 5},
                           "uncertain": {"type": "string", "minLength": 5}},
        },
        "comedy_mechanisms": {"type": "array", "uniqueItems": True, "items": {"enum": MECHANISM_NAMES}},
        "suspense_question": {"type": "string", "minLength": 10},
        "notes": {"type": "string"},
    },
}
assert [s["key"] for s in CONTRACT] == ["want", "stakes", "constraint", "choice", "escalation", "knowledge", "plant",
                                        "reversal", "consequence"]

_DECOY = next(b for b in SLATE["boards"] if b["title"] == "The Decoy Job")
_DECOY_SHOT = {s["index"]: s for s in _DECOY["shots"]}
DECOY_CONTRACT = {
    "title": "The Decoy Job",
    "premise_ref": "the-decoy-job",
    "want": "The thief wants an effortless valuable score.",
    "stakes": _DECOY["stakes"],
    "constraint": ("The paid living-statue performer wants a break and refuses to be treated as an object. "
                   "The approaching guard makes their disagreement urgent."),
    "choice": "The thief looks toward the doorway, then accepts with a miserable handshake.",
    "escalation": _DECOY["escalation_chain_text"],
    "knowledge": {
        "viewer": "The audience may realize the truth before the thief.",
        "character": "The thief's plan to steal an object is now a negotiation with a person.",
        "uncertain": ("We anticipate the statue revealing itself, then wonder what it will demand, whether the "
                      "disguise will hold, and whether the thief will leave or accept the unexpected reward."),
    },
    "plant": _DECOY["planted_details"].split(" Do not conceal")[0],
    "reversal": _DECOY["midpoint_change"],
    "consequence": "End on the thief trying to hold the grand pose while counting his tip with one furtive finger.",
    "comedy_mechanisms": ["Dramatic irony", "Opposed goals", "Status reversal"],
    "suspense_question": "Can the thief avoid being caught after choosing the worst possible thing to steal?",
    "notes": ("Every sentence is quoted from the guide's board for The Decoy Job; only the arrangement into contract "
              "fields and the mechanism names were chosen by the generator. Board status: proposed, unrendered."),
}
for _quoted in ("The thief wants an effortless valuable score.", DECOY_CONTRACT["choice"], DECOY_CONTRACT["constraint"],
                *DECOY_CONTRACT["knowledge"].values(), DECOY_CONTRACT["consequence"], DECOY_CONTRACT["plant"]):
    assert _quoted in json.dumps(_DECOY, ensure_ascii=False), _quoted

ADDRESS_GROUPS = APPC["treatment_map"]["groups"]
TREATMENT_ADDRESS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": f"{REPO_URL}/baltor/contract-schemas/treatment-address",
    "title": "Creative-catalogue treatment address",
    "description": ("One of the 2,400 addressable candidate treatments: R-{story_id}-{format_id}-{approach_id}, with "
                    "the intro and motion the story's treatment group assigns. The oneOf branches encode the four "
                    "treatment groups exactly, so a format or approach a group does not use fails. That the address "
                    "string agrees with its parts is checked by the treatment_address_resolver module. A compatible "
                    "combination is still not a screenplay."),
    "type": "object",
    "additionalProperties": False,
    "required": ["address", "story_id", "format_id", "approach_id", "intro_id", "motion_id", "status"],
    "properties": {
        "address": {"type": "string", "pattern": "^R-(EDU|ENT)[0-9]{3}-F[0-9]{2}-A0[1-4]$"},
        "story_id": {"type": "string", "pattern": "^(EDU|ENT)[0-9]{3}$"},
        "format_id": {"type": "string", "pattern": "^F[0-9]{2}$"},
        "approach_id": {"enum": ["A01", "A02", "A03", "A04"]},
        "intro_id": {"type": "string", "pattern": "^I[0-3][0-9]$"},
        "motion_id": {"type": "string", "pattern": "^M[0-3][0-9]$"},
        "treatment_group": {"type": "integer", "minimum": 1, "maximum": 4},
        "status": {"enum": ["addressable-candidate", "selected", "scripted", "storyboarded", "rendered", "rejected"],
                   "description": "Every catalogue address starts as addressable-candidate."},
        "status_evidence": {"type": "string", "minLength": 10},
    },
    "oneOf": [
        {
            "properties": {"story_id": {"enum": g["stories"]}, "treatment_group": {"const": g["group"]}},
            "anyOf": [
                {"properties": {"format_id": {"const": r["format"]}, "approach_id": {"const": r["approach"]},
                                "intro_id": {"const": r["intro"]}, "motion_id": {"const": r["motion"]}}}
                for r in g["rows"]
            ],
        }
        for g in ADDRESS_GROUPS
    ],
    "if": {"properties": {"status": {"not": {"const": "addressable-candidate"}}}, "required": ["status"]},
    "then": {"required": ["status_evidence"]},
}


def address_record(story: str, fmt: str, approach: str) -> dict:
    g = GROUP_OF[story]
    row = next((r for r in g["rows"] if r["format"] == fmt and r["approach"] == approach), None)
    intro, motion = (row["intro"], row["motion"]) if row else ("I01", "M01")
    return {"address": f"R-{story}-{fmt}-{approach}", "story_id": story, "format_id": fmt, "approach_id": approach,
            "intro_id": intro, "motion_id": motion, "treatment_group": g["group"], "status": "addressable-candidate"}


# ============================================================================= premise skills

def style_menu(p: dict) -> list[str]:
    families = sorted({APPROACH_FAMILY[t["approach_id"]] for t in treatments(p)})
    out = []
    for s in STYLES:
        fams = [x.strip() for x in s["approaches"].split(";")]
        hit = [f for f in fams if f in families]
        if hit:
            out.append(f"- {s['id']} {s['style']} ({'; '.join(fams)}): {s['value']} Check: {s['check']}")
    return out


def premise_skill(p: dict) -> str:
    tr = treatments(p)
    group = GROUP_OF[p["id"]]["group"]
    fam_word = "Learning" if p["family"] == "learning" else "Fiction"
    claim_note = ("Learning claims remain unverified until a claim-level check." if p["family"] == "learning"
                  else "Fictional themes are not empirical claims.")
    L: list[str] = [f"# {p['id']} {p['title']}", ""]
    L.append(f"**Catalogue family:** {fam_word}, {p['category']} (Appendix D section \"{p['category_heading']}\").  ")
    L.append(f"**Status:** idea. Not a completed script, not a rendered catalogue treatment, no audience study. "
             f"{claim_note} Originality means authored for the catalogue, not an exhaustive prior-art search. "
             "The current story-first review may reject or substantially rewrite this premise.")
    L += ["", "## Premise (authored wording)", "", p["premise"], "",
          f"**Hook:** {p['hook']}", "", f"**Visible action:** {p['visible_action']}", "",
          f"**Intended takeaway or theme:** {p['intended_takeaway_or_theme']}", "", f"**Gate:** {p['gate']}", "",
          f"**Evidence class:** `{p['evidence_class']}`. **Original format tags:** {', '.join(p['original_format_tags'])}.",
          "", "Factual checkability is not factual verification: the evidence class classifies how a claim could be "
          "checked; it does not record that any check was done.", ""]

    L += ["## Beat structure as given", "",
          "The guide gives this premise as one paragraph and one visible-action line. They are split below in their "
          "written order; nothing is added. Before boarding, write the story contract and test the escalation: "
          "each attempt should change the situation rather than reset it.", "", "Premise, sentence by sentence:", ""]
    L += [f"{n}. {s}" for n, s in enumerate(sentences(p["premise"]), 1)]
    L += ["", "Visible action, in the order written:", ""]
    L += [f"{n}. {s.strip().rstrip('.')}" for n, s in enumerate(p["visible_action"].split(";"), 1)]
    L.append("")

    L += ["## Treatment addresses (exactly ten)", "",
          f"Treatment group {group} of Appendix C. Stable ID `R-{{story_id}}-{{format_id}}-{{approach_id}}`. "
          "A compatible combination is still not a screenplay; the catalogue held zero independently written "
          "treatment scripts, zero recipe renders and zero audience studies.", ""]
    rows = []
    for t in tr:
        f, a, i, m = FORMATS[t["format_id"]], APPROACHES[t["approach_id"]], INTROS[t["intro_id"]], MOTIONS[t["motion_id"]]
        rows.append([f"`{t['address']}`", f"{f['id']} {f['format']} ({f['original_proposed_duration']})",
                     f"{a['id']} {a['approach']}", f"{i['id']} {i['intro']}: {i['first_frame']}",
                     f"{m['id']} {m['motion']}"])
    L += [md_table(["Address", "Format (original proposed duration)", "Approach", "Intro: first frame", "Motion"], rows), ""]
    L += ["Editorial treatment rules for these formats:", ""]
    for fid in dict.fromkeys(t["format_id"] for t in tr):
        L.append(f"- {EDITORIAL_RULES[fid]}")
    L += ["", "Resolve any address into its joined records with the `treatment_address_resolver` code module.", ""]

    L += ["## Suggested styles", ""]
    su = SU_BY_STORY.get(p["id"])
    if su:
        L += [f"**Concrete style application {su['id']}** (authored in the catalogue for this story): "
              f"{su['treatment']}. View: {su['view']}. Geometry: {su['geometry']}. Material: {su['material']}. "
              f"Aesthetic: {su['aesthetic']}. Layout: {su['layout']}. Why: {su['why']} Check: {su['check']}", ""]
    pick = PICK_BY_STORY.get(p["id"])
    if pick:
        L += [f"**Original top-twenty editorial pick, rank {pick['rank']}.** {BANKS['top_picks']['intro'][0]} "
              f"Reason: {pick['original_reason']} Proposed first version: {pick['proposed_first_version']} "
              f"Gate: {pick['gate']}", ""]
    if not su and not pick:
        L += ["The catalogue authored no concrete style application or editorial pick for this story.", ""]
    approaches = sorted({t["approach_id"] for t in tr})
    fam_desc = ", ".join(f"{a} {APPROACHES[a]['approach']} -> `{APPROACH_FAMILY[a]}`" for a in approaches)
    L += [f"Style menu matching this story's approaches ({fam_desc}). This join was made by the generator from the "
          "forty-style bank's Approaches column; it is a menu, not an authored choice for this premise:", ""]
    L += style_menu(p)
    L.append("")

    L += ["## Story tests to apply", "",
          f"1. **This premise's gate:** {p['gate']}",
          "2. **Format gates:** " + " ".join(f"{fid} {FORMATS[fid]['format']}: {FORMATS[fid]['gate']}"
                                             for fid in dict.fromkeys(t["format_id"] for t in tr)),
          "3. **Approach gates:** " + " ".join(f"{a} {APPROACHES[a]['approach']}: {APPROACHES[a]['gate']}" for a in approaches),
          f"4. **Combination rule:** {COMBINATION_RULES[p['family']]} {COMBINATION_RULES['every']}",
          "5. **Story contract** (write these sentences before drawing shots; `story_contract` schema):", ""]
    L += ["   " + ln for ln in contract_lines()]
    L += ["", "6. **Storyboard gate before a full render** (`storyboard_gate`):", ""]
    L += ["   " + ln for ln in gate_lines()]
    L += ["", f"7. **Production-independent story tests** on a rough animatic: {STORY_TESTS['intro'][0]}", ""]
    L += ["   " + ln for ln in story_test_lines()]
    L += ["", "   " + " ".join(STORY_TESTS["after"]), "",
          "8. **Global kill criteria:** " + "; ".join(KILL) + ". " + KILL_CLOSING, ""]
    if p["family"] == "fiction":
        L += ["For comedy and suspense, check the `comedy_mechanisms` table (each mechanism has a failure to reject) "
              "and the `suspense_rules`.", ""]
    L += ["Run the whole gate with the `storyboard_before_render` command or ask the `story_doctor` subagent to apply "
          "the contract and tests to a draft.", "", "## Source", "",
          f"{GUIDE_TITLE}, Appendix D, line {p['line']} (`{GUIDE_REL}#{p['anchor']}`). Catalogue record: {CAT_REF}.",
          "`premise.json` holds this record in the `story_premise` contract-schema shape."]
    return "\n".join(L)


def premise_description(p: dict) -> str:
    return clip(f"Use when choosing, developing or storyboarding catalogue premise {p['id']} \"{p['title']}\" "
                f"({p['family']}, {p['category']}). Hook: {p['hook']} Gives the authored premise, visible action, "
                f"intended {'takeaway' if p['family'] == 'learning' else 'theme'}, gate, evidence class, its ten exact "
                "treatment addresses, suggested styles and the story tests to apply before any render. "
                "Status: idea, not a script or a render.", 1020)


# ============================================================================= storyboard skills

def recommendation_for(title: str) -> str:
    para = SLATE["recommendation"][0]
    sents = sentences(para)
    out, on = [], False
    for s in sents:
        if "**" in s:
            on = f"**{title}**" in s
        if on:
            out.append(s)
    return " ".join(out)


PRE_FIELDS = ["format_text", "opening_image", "dramatic_question", "characters_and_goals", "world_rule", "stakes",
              "escalation_chain_text", "planted_details"]
POST_FIELDS = ["midpoint_change", "why_watch_next_beat", "alternate_ending", "obvious_weakness", "kill_criteria"]


def board_skill(b: dict) -> str:
    L = [f"# {b['title']} (timed storyboard {b['number']} of 3)", ""]
    L += [f"**Status:** {SLATE_STATUS}", "",
          f"**Scope:** {SLATE['scope']}", "",
          f"**Editorial recommendation:** {recommendation_for(b['title'])} {SLATE['recommendation'][1]}", ""]
    for k in PRE_FIELDS:
        L += [f"**{b['field_labels'][k]}:** {b[k]}", ""]
    L += ["## Timed storyboard", ""]
    for s in b["shots"]:
        L += [f"{s['index']}. **{s['start_s']}–{s['end_s']} seconds. {s['title']}.** {s['action']}", ""]
    for k in POST_FIELDS:
        L += [f"**{b['field_labels'][k]}:** {b[k]}", ""]
    L += ["## Before any render", "",
          "1. Keep the board's status at proposed until something stronger is observed. "
          "A table read, silent animatic, or owner storyboard choice can prevent a wasted full render; these are "
          "proposed review methods, not proof that a fresh audience has approved a premise.",
          "2. `storyboard.json` follows the `timed_storyboard` schema. Check timing and required story fields with "
          "`python3 timed_storyboard_check.py storyboard.json` and print the review sheet with `--sheet`.",
          "3. Answer the storyboard gate with shot numbers as evidence:", ""]
    L += ["   " + ln for ln in gate_lines()]
    L += ["", f"4. Test a rough animatic with people unfamiliar with the pitch. {' '.join(STORY_TESTS['after'])}", ""]
    L += ["   " + ln for ln in story_test_lines()]
    L += ["", "5. Global kill criteria: " + "; ".join(KILL) + ". " + KILL_CLOSING,
          "6. Apply this board's own kill criteria above. Use the `storyboard_before_render` command for the whole "
          "sequence and the `story_doctor` subagent for an editorial pass.", "",
          "## Source", "", f"{GUIDE_TITLE}, \"New suspense and comedy storyboards\", line {b['line']} "
          f"(`{GUIDE_REL}#{b['anchor']}`)."]
    return "\n".join(L)


def pitch_skill(p: dict) -> str:
    L = [f"# {p['title']} (development pitch {p['number']} of 8)", ""]
    L += ["**Status:** pitch, proposed.", "", f"From the guide's development slate: {' '.join(SLATE['slate_intro'])}",
          "", f"Slate status, from the guide: {SLATE_STATUS}", "",
          f"**Scope:** {SLATE['scope']}", ""]
    for k in ("opening_frame", "question_and_goals", "rule", "causal_escalation", "plant_and_payoff", "visual_test"):
        L += [f"**{p['field_labels'][k]}:** {p[k]}", ""]
    L += ["## Developing this pitch", "",
          "This is a pitch, not a timed board. Develop it only if its visual test works. Next steps, in order:", "",
          "1. Write the story contract (`story_contract` schema):", ""]
    L += ["   " + ln for ln in contract_lines()]
    L += ["", "2. Draft a timed board (`timed_storyboard` schema, board_type `timed`) and run "
          "`timed_storyboard_check` on it.",
          "3. Answer the storyboard gate:", ""]
    L += ["   " + ln for ln in gate_lines()]
    L += ["", "4. Test a rough animatic with the seven production-independent story tests (`story_tests`), then apply "
          "the global kill criteria: " + "; ".join(KILL) + ". " + KILL_CLOSING, "",
          "## Source", "", f"{GUIDE_TITLE}, \"Five more distinct topics: an eight-story development slate\", line "
          f"{p['line']} (`{GUIDE_REL}#{p['anchor']}`)."]
    return "\n".join(L)


def board_identity(title: str, timed: bool) -> str:
    return ("storyboard_" if timed else "story_pitch_") + slug(title)


# ============================================================================= banks

BANK_SPECS = {
    "approaches": ("creative_catalogue_representation_approaches", "Creative catalogue: four representation approaches",
                   "The four representation approaches (A01-A04) every catalogue treatment uses, with construction, "
                   "communicative difference and gate for each."),
    "hooks": ("creative_catalogue_hook_patterns", "Creative catalogue: sixty hook patterns",
              "Sixty opening hook patterns (H01-H60) with copy seed, use and the guard each must satisfy."),
    "intros": ("creative_catalogue_visual_intros", "Creative catalogue: thirty visual intros",
               "Thirty visual intros (I01-I30): first frame, action, text seed, sound and fit."),
    "styles": ("creative_catalogue_visual_styles", "Creative catalogue: forty visual styles",
               "Forty visual styles (S01-S40): visual language, value, check and the representation families each fits."),
    "motions": ("creative_catalogue_motion_patterns", "Creative catalogue: thirty motion patterns",
                "Thirty motion patterns (M01-M30): mechanism, fit and the check each needs."),
    "formats": ("creative_catalogue_editorial_formats", "Creative catalogue: twenty editorial formats",
                "Twenty editorial formats (F01-F20) with structure, fit, gate, original proposed duration and the "
                "editorial treatment rules."),
    "axes": ("creative_catalogue_visual_axes", "Creative catalogue: twenty-five visual axes",
             "Twenty-five independent visual-axis choices (AX01-AX25) across camera, geometry, material, aesthetic and "
             "composition, with use and check."),
    "style_applications": ("creative_catalogue_style_applications", "Creative catalogue: eighteen style applications",
                           "Eighteen concrete style applications (SU01-SU18), each authored for one catalogue story: "
                           "view, geometry, material, aesthetic, layout, why and check."),
    "top_picks": ("creative_catalogue_top_twenty_picks", "Creative catalogue: original top twenty editorial picks",
                  "The catalogue's historical top-twenty editorial picks with reason, proposed first version and gate; "
                  "not current owner-approved selections."),
}

BANK_USE = {
    "approaches": "when deciding how a short film represents its story: diagrammatic vector, sketch and cutaway, "
                  "tactile miniature 3D, or layered 2.5D illustration.",
    "hooks": "when writing the opening hook or first line of a short animated or explainer film.",
    "intros": "when designing the first frame and first seconds of a short animated or explainer film.",
    "styles": "when picking a visual style for a short animated or explainer film.",
    "motions": "when choosing camera or object motion that carries a story beat or an explanation.",
    "formats": "when choosing the editorial structure of a short film (mechanism, prediction, fable, dilemma, "
               "dramatic irony, comedy chain and more).",
    "axes": "when specifying a film's look one decision at a time: projection, geometry, material, aesthetic, composition.",
    "style_applications": "when looking for a worked example of a full style specification for a catalogue story.",
    "top_picks": "when looking for the catalogue's historically recommended starting premises.",
}

BANK_GUIDANCE = {
    "approaches": ["Every treatment address names one approach. Learning stories use A01 and A02; fiction stories use "
                   "A01 with A03 (group 3) or with A04 (group 4).",
                   "Each approach's gate is part of every treatment that uses it."],
    "hooks": ["Pick a hook for what it makes the viewer ask, then check its Guard against the chosen story. "
              "A hook whose guard fails for this story is not usable for it."],
    "intros": ["The Fit column names the kinds of story each intro was catalogued for; the treatment groups fix one "
               "intro per format for every catalogue story."],
    "styles": ["Choose a style by what it helps the viewer understand or feel. The Approaches column names the "
               "representation families each style was catalogued for (vector, cutout, sketch, block3d, raster, mixed).",
               "Each style's Check is a review item for any film that uses it."],
    "motions": ["Each motion's Check must hold in the exact final encode, not only in a preview."],
    "formats": ["The treatment groups use F01-F10 and F20. Original proposed durations are the catalogue's "
                "historical proposals, not exact requirements."],
    "axes": ["The Axis column groups the choices into camera / projection, geometry, material / surface, aesthetic "
             "and composition."],
    "style_applications": ["Each row is authored for one story; the premise skill for that story repeats it."],
    "top_picks": [],
}


def bank_records(key: str) -> tuple[list[str], list[str], list[dict], list[str]]:
    if key == "approaches":
        t = APPC["count_contract"]["approaches"]
    else:
        t = BANKS[key]
    records = copy.deepcopy(t["records"])
    if key in ("style_applications", "top_picks"):
        for r in records:
            r["story_title"] = PREMISE_BY_ID[r["story"]]["title"] if key == "style_applications" else r.get("title")
            r["premise_identity"] = PREMISE_ID[r["story"]]
    return t["columns"], t["keys"], records, t["intro"] + t["after"]


def bank_skill(key: str) -> tuple[str, dict]:
    ident, title, summary = BANK_SPECS[key]
    columns, keys, records, notes = bank_records(key)
    heading = (APPC["count_contract"]["approaches"]["heading"] if key == "approaches" else BANKS[key]["heading"])
    anchor = (APPC["count_contract"]["anchor"] if key == "approaches" else BANKS[key]["anchor"])
    L = [f"# {title}", "", f"**Status:** {APPC['intro'][0]}", ""]
    for n in notes:
        L += [n, ""]
    for gtxt in BANK_GUIDANCE[key]:
        L += [f"- {gtxt}"]
    if BANK_GUIDANCE[key]:
        L.append("")
    rows = [[r[k] for k in keys] for r in records]
    if key in ("style_applications", "top_picks"):
        columns = columns + ["Premise skill"]
        rows = [row + [f"`{r['premise_identity']}`"] for row, r in zip(rows, records)]
    L += [md_table(columns, rows), ""]
    if key == "formats":
        L += ["## Editorial treatment rules", ""] + [f"- {r}" for r in APPC["treatment_map"]["editorial_rules"]] + [""]
        L += APPC["treatment_map"]["editorial_rules_after"] + [""]
    L += ["These are menus, not obligations to execute every entry. `bank.json` holds the same rows as data.", "",
          "## Source", "", f"{GUIDE_TITLE}, Appendix C, \"{heading}\" (`{GUIDE_REL}#{anchor}`). Materialized from the "
          f"{CAT_REF}."]
    bank = {"bank": key, "title": title, "status": "proposal", "status_note": APPC["intro"][0],
            "columns": columns, "keys": keys, "count": len(records), "records": records,
            "source": {"document": GUIDE_REL, "section": f"Appendix C Creative banks and exact treatment addressing / {heading}",
                       "anchor": anchor, "catalogue_library_identity": CAT["library_identity"],
                       "catalogue_sha256": CAT["sha256"]}}
    if key == "formats":
        bank["editorial_treatment_rules"] = APPC["treatment_map"]["editorial_rules"]
        bank["combination_rules"] = COMBINATION_RULES
    return "\n".join(L), bank


# ============================================================================= rules packages

def allocation() -> list[dict]:
    para = next(p for p in SQ["longer_film_structure"]["paragraphs"] if p.startswith("An illustrative"))
    segs = re.findall(r"(\d+)–(\d+) (?:seconds )?for (?:the )?([^,.]+?)(?=, |\. |\.$)", para)
    out = [{"start_s": int(a), "end_s": int(b), "beat": c.replace("and ", "", 1) if c.startswith("and ") else c}
           for a, b, c in segs]
    assert len(out) == 7 and out[-1]["end_s"] == 108
    return out


def boxed_in_provenance() -> dict:
    row, rec = PROV["boxed_in_row"], PROV["boxed_in_receipt"]
    return {
        "film": "BOXED IN",
        "evidence_stage": "delivered",
        "creative_status": "rejected (story quality rejected by Taylor)",
        "guide_statement": SQ["boxed_in_lesson"]["paragraphs"],
        "latest_creative_direction": ("The 108-second BOXED IN film was technically completed and delivered, but "
                                      "Taylor rejected its story quality. Its physics and export receipts remain useful "
                                      "engineering evidence; it is not a recommended example of successful entertainment."),
        "library_identities": [{"role": r, "library_identity": i, "version": v} for r, i, v in row["library_identities"]],
        "sha256": {"mp4": rec["sha256"][0], "source_zip": rec["sha256"][1]},
        "receipt_text": rec["text"],
        "film_row_text": row["text"],
        "guide": {"document": GUIDE_REL, "film_row_line": row["guide_line"], "receipt_line": rec["guide_line"],
                  "section": row["guide_section"], "lesson_line": SQ["boxed_in_lesson"]["line"]},
    }


def contract_rules_md() -> str:
    L = ["# Story contract rules", "",
         f"Source: {GUIDE_TITLE}, \"Story quality comes before production scale\". Status: editorial guidance; the "
         "review methods it names are proposed, not validated audience research.", "",
         "## The lesson from BOXED IN", ""]
    for p in SQ["boxed_in_lesson"]["paragraphs"]:
        L += [p, ""]
    L += ["Evidence: BOXED IN (108 s) was technically delivered and Taylor rejected its story quality. "
          "`provenance.json` keeps its Library identities and SHA-256 values so the history stays traceable; none of "
          "its technical receipts overrides the story rejection.", "",
          "## The contract", "", SQ["story_contract"]["intro"], ""]
    L += [f"{n}. **{s['label']}:** {s['question']}" for n, s in enumerate(CONTRACT, 1)]
    L += ["", "Check: all nine sentences are written for this premise before any shot is drawn, each traceable to a "
          "board line or shot. The `story_contract` contract schema holds them as data.", ""]
    for p in SQ["story_contract"]["after"]:
        L += [p, ""]
    L += ["## A flexible longer-film structure", ""]
    for p in SQ["longer_film_structure"]["paragraphs"]:
        L += [p, ""]
    L += [md_table(["Seconds", "Beat (illustrative 108-second allocation)"],
                   [[f"{a['start_s']}–{a['end_s']}", a["beat"]] for a in allocation()]), "",
          "This allocation is a writing scaffold, not an empirically optimized retention formula; do not treat the "
          "segments as mandatory or equal.", "", "## Related", "",
          "`storyboard_gate`, `comedy_mechanisms`, `suspense_rules`, `story_tests`, `story_doctor`, "
          "`storyboard_before_render`.", "", STATUS_LADDER_NOTE]
    return "\n".join(L)


def gate_md() -> str:
    g = SQ["storyboard_gate"]
    L = ["# Storyboard gate before a full render", "",
         f"Source: {GUIDE_TITLE}, \"Storyboard gate before a full render\" (line {g['line']}).", ""]
    for p in g["intro"]:
        L += [p, ""]
    L += ["Board columns (one row per shot; the `timed_storyboard` schema names them `composition`, duration "
          "(`start_s`/`end_s`), `action`, `new_information`, `decision`, `sound`, `cut_reason`):", "",
          "- shot image or clear composition description", "- duration estimate", "- action", "- new information",
          "- character decision", "- dialogue or sound", "- the story reason for the cut", "",
          "## Challenge questions", ""]
    L += gate_lines()
    L.append("")
    for p in g["after"]:
        L += [p, ""]
    L += ["## Mechanical part", "",
          "`timed_storyboard_check` verifies only structure: required story fields, shots from 0 with no gaps or "
          "overlaps, declared shot count and duration. It prints the ten questions above as a review sheet with "
          "every answer starting as \"not checked\". Passing it says nothing about story quality.", "",
          STATUS_LADDER_NOTE]
    return "\n".join(L)


def comedy_md() -> str:
    t = SQ["comedy_mechanisms"]
    hooks = [h for h in BANKS["hooks"]["records"] if re.search(r"Com(?:edy|ic)", h["use"])]
    L = ["# Comedy mechanisms", "", f"Source: {GUIDE_TITLE}, \"Comedy mechanisms to develop\" (line {t['line']}).", "",
         "Name the mechanism a board relies on, make it playable the way the table says, and reject the board if it "
         "shows the failure in the third column.", "",
         md_table(t["columns"], [[r[k] for k in t["keys"]] for r in t["records"]]), ""]
    L += ["From the story contract: " + SQ["story_contract"]["after"][0], "",
          "Related hook patterns whose catalogued use is comedy (a join made by the generator from the hook bank's Use "
          "column; each keeps its guard):", ""]
    L += [f"- {h['id']} {h['pattern']}: \"{h['copy_seed']}\" Guard: {h['guard']}" for h in hooks]
    L += ["", "BOXED IN lesson (see `story_contract_rules`): repeated unsuccessful attempts are not automatically an "
          "arc.", "", STATUS_LADDER_NOTE]
    return "\n".join(L)


def suspense_rules() -> list[str]:
    out = []
    for p in SQ["suspense"]["paragraphs"]:
        out += sentences(p)
    return out


def suspense_md() -> str:
    s = SQ["suspense"]
    L = ["# Suspense rules", "", f"Source: {GUIDE_TITLE}, \"Suspense without empty delay\" (line {s['line']}).", "",
         "Each sentence of the guide's section is one rule, in its original order:", ""]
    L += [f"{n}. {r}" for n, r in enumerate(suspense_rules(), 1)]
    tail = sentences(SQ["story_contract"]["after"][0])[-1]
    L += ["", f"From the story contract: {tail}", "",
          "Operational check added for this package (not guide wording): write the concrete question in one sentence; point to the shots that show success and "
          "failure; list the choices still open after each shot and confirm the list narrows; for any clock, name the "
          "decision it changes; for any apparent escape, name its cost or the relationship it reveals.", "",
          STATUS_LADDER_NOTE]
    return "\n".join(L)


def story_tests_md() -> str:
    t = STORY_TESTS
    L = ["# Production-independent story tests", "",
         f"Source: {GUIDE_TITLE}, \"Production-independent story tests\" (line {t['line']}).", ""]
    L += t["intro"] + [""] + story_test_lines() + [""] + t["after"] + ["", "## Global kill criteria", ""]
    L += kill_lines() + ["", KILL_CLOSING, "",
                         "Record who answered, what they saw (pitch, board, animatic), and their answers verbatim. "
                         "An agent's own answers are not viewer answers.", "", STATUS_LADDER_NOTE]
    return "\n".join(L)


# ============================================================================= subagent and command

DOCTOR_BODY = f"""
You are a story doctor for short animated and factual films. You apply this project's story contract and story
tests to a draft (catalogue premise, pitch, script, timed storyboard or animatic notes) and say what must change
before anyone renders. Your review is editorial: it is not audience evidence and it never approves a film.

Source of the rules: {GUIDE_TITLE}, "Story quality comes before production scale" and "New suspense and comedy
storyboards". The rules packages `story_contract_rules`, `storyboard_gate`, `comedy_mechanisms`, `suspense_rules`
and `story_tests` hold the exact wording.

## Procedure

1. Read the whole draft. When it is a catalogue premise, read its `premise.json` (keep its id, gate, evidence class
   and status). When it is a board, read its `storyboard.json`. Quote the draft when you cite it.
2. **Story contract.** Fill each sentence only with what the draft establishes, citing the line or shot. Write
   MISSING when the draft does not establish it. Never invent a plant, rule or reversal to fill a gap; put a proposed
   fix under "Suggested revisions", labelled as a proposal.
{chr(10).join('   ' + ln for ln in contract_lines())}
3. **Causality.** Rewrite the middle beats as one chain joined by "because" or "therefore". Mark every link that is
   only "and then".
4. **Escalation.** For each attempt, state what it changes: options, risk, relationship or knowledge. Flag attempts
   that reset or repeat. BOXED IN lesson: repeated unsuccessful attempts are not automatically an arc, and a renamed
   obstacle or a swapped prop is not a new story.
5. **Comedy and suspense.** Name the comedy mechanisms in use and test each against its failure to reject
   ({'; '.join(f"{r['mechanism']}: {r['failure_to_reject']}" for r in SQ['comedy_mechanisms']['records'])}).
   For suspense: is there a concrete question, are success and failure shown, do the choices narrow, does any clock
   change decisions, is the geography legible?
6. **Storyboard gate.** Answer each question with evidence (shot numbers or quotes), or "not answerable from the
   draft":
{chr(10).join('   ' + ln for ln in gate_lines())}
   If a timed board JSON exists, run `python3 timed_storyboard_check.py storyboard.json` (the `{ID_CHECK}` code
   module) and include its findings.
7. **Global kill criteria.** Mark each as hit, not hit, or not checkable, with evidence:
{chr(10).join('   ' + ln for ln in kill_lines())}
8. **Production-independent story tests.** You cannot answer these for viewers. List them as the next step: a rough
   animatic shown to a few people unfamiliar with the pitch, without explaining the intended answers.
9. **Verdict**, exactly one of:
   - `revise story`: any MISSING contract sentence, any kill criterion hit, or an "and then" link in the middle;
   - `ready for a rough animatic test`: the contract is complete and no kill criterion is hit on paper;
   - `blocked`: facts, rights or required sources are unresolved (learning premises: claims stay unverified until a
     claim-level check; an evidence class is not verification).
   Never write "approved", "accepted" or a prediction of views or retention. Keep the draft's recorded status; do not
   upgrade it.

## Output

```
## Story doctor: <title>  (draft status: <as recorded>)
### Contract            table: sentence | draft evidence (quote + location) | MISSING?
### Causal chain        beat -> because/therefore -> beat ... ; "and then" links marked
### Escalation          attempt | what changed | reset/repeat?
### Mechanisms          mechanism | how it plays | failure-to-reject check
### Storyboard gate     1-10 with evidence or "not answerable"
### Kill criteria       hit / not hit / not checkable, with evidence
### Suggested revisions proposals only, each tied to a contract gap or kill criterion
### Not checked         everything you could not assess (viewer tests, listening, rendering)
### Verdict             revise story | ready for a rough animatic test | blocked
```

Preserve the owner's wording for premises and questions; suggest changes separately rather than rewriting the
premise's meaning. Keep proposal and implementation apart, and editorial judgement and audience evidence apart.
"""

COMMAND_BODY = f"""
Gate this story before any substantial render: $ARGUMENTS
(a catalogue premise identity or `premise.json`, a `storyboard.json`, or a draft script).

The rule behind this command ({GUIDE_TITLE}): evaluate the topic and storyboard before spending time on a full
render. A technically clean render does not rescue a story that fails its gate.

1. **Load the draft.** For a catalogue premise, keep its id, gate, evidence class and status (idea). If a treatment
   is chosen, resolve its address with `python3 treatment_address_resolver.py R-...` and carry its format and
   approach gates.
2. **Story contract.** Write `story_contract.json` (`{ID_CONTRACT_SCHEMA}` contract schema): want, stakes,
   constraint, choice, escalation, knowledge (viewer / character / uncertain), plant, reversal, consequence. Validate
   it. Stop here if any sentence cannot be written from the story; revise the story, not the polish.
3. **Timed board.** Write or update `storyboard.json` (`{ID_BOARD_SCHEMA}` schema, board_type `timed`): every shot
   with composition, start and end seconds, action, new information, decision, sound and the story reason for the
   cut. Validate it and run `python3 timed_storyboard_check.py storyboard.json`; fix every ERROR. Print the review
   sheet with `--sheet`.
4. **Editorial pass.** Run the `{ID_DOCTOR}` subagent on the contract and the board. Apply its findings to the
   story. A "revise story" verdict ends this run.
5. **Gate and kill criteria.** Answer the ten storyboard-gate questions with shot evidence. Check the seven global
   kill criteria and the board's own kill criteria.
6. **Cheapest real review.** Propose a table read, a silent animatic or an owner storyboard choice. These are
   proposed review methods, not proof that a fresh audience approved the premise. Run the seven production-
   independent story tests only with people unfamiliar with the pitch, without explaining the intended answers,
   and record their answers verbatim.
7. **Render only after the gate.** Proceed to a bounded proof of the hardest shot, then the full render, only when
   the owner has chosen the board (record who and when) and no kill criterion is hit.

Report: what passed, what failed, what was not checked, and the board status (proposed, owner-selected,
animatic-reviewed ...). Never render first and judge later, extend a thin premise with polish or runtime, call a
renamed obstacle a new story, or upgrade any status.
"""


# ============================================================================= code module payloads

def storyboard_rules_json() -> dict:
    return {
        "source": {"document": GUIDE_REL, "sections": ["Storyboard gate before a full render",
                                                       "Production-independent story tests"]},
        "storyboard_gate": {"intro": " ".join(SQ["storyboard_gate"]["intro"]), "questions": GATE_QUESTIONS,
                            "after": " ".join(SQ["storyboard_gate"]["after"])},
        "story_tests": {"intro": " ".join(STORY_TESTS["intro"]), "questions": STORY_TESTS["questions"],
                        "after": " ".join(STORY_TESTS["after"])},
        "global_kill_criteria": KILL,
        "global_kill_criteria_closing": KILL_CLOSING,
    }


def catalogue_tables_json() -> dict:
    return {
        "source": {"document": GUIDE_REL, "section": "Appendix C Creative banks and exact treatment addressing",
                   "catalogue_library_identity": CAT["library_identity"], "catalogue_sha256": CAT["sha256"]},
        "count_contract": APPC["count_contract"]["paragraphs"][0],
        "groups": [{"group": g["group"], "stories": g["stories"], "rows": g["rows"]} for g in ADDRESS_GROUPS],
        "stories": {p["id"]: {"title": p["title"], "family": p["family"], "category": p["category"],
                              "premise_identity": PREMISE_ID[p["id"]]} for p in PREMISES},
        "formats": {k: {kk: vv for kk, vv in v.items() if kk != "id"} for k, v in FORMATS.items()},
        "approaches": {k: {kk: vv for kk, vv in v.items() if kk != "id"} for k, v in APPROACHES.items()},
        "intros": {k: {kk: vv for kk, vv in v.items() if kk != "id"} for k, v in INTROS.items()},
        "motions": {k: {kk: vv for kk, vv in v.items() if kk != "id"} for k, v in MOTIONS.items()},
        "editorial_rules": EDITORIAL_RULES,
        "combination_rules": COMBINATION_RULES,
    }


def module_files(name: str) -> dict[str, str]:
    root = MODULES / name
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.py"))}


# ============================================================================= write everything

def self_check() -> None:
    """Validate generated JSON against the schemas this generator ships, and boards against the structure check."""
    try:
        import jsonschema  # type: ignore
    except ImportError:  # pragma: no cover
        print("ref_stories: jsonschema not installed; skipping self-check", file=sys.stderr)
        return
    V = jsonschema.Draft202012Validator
    for schema in (STORY_PREMISE_SCHEMA, TIMED_STORYBOARD_SCHEMA, STORY_CONTRACT_SCHEMA, TREATMENT_ADDRESS_SCHEMA):
        V.check_schema(schema)
    pv = V(STORY_PREMISE_SCHEMA)
    for p in PREMISES:
        errs = list(pv.iter_errors(premise_record(p)))
        assert not errs, f"{p['id']}: {errs[0].message}"
    bv = V(TIMED_STORYBOARD_SCHEMA)
    for rec in [board_record(b) for b in SLATE["boards"]] + [pitch_record(p) for p in SLATE["pitches"]]:
        errs = list(bv.iter_errors(rec))
        assert not errs, f"{rec['id']}: {errs[0].message}"
    assert not list(V(STORY_CONTRACT_SCHEMA).iter_errors(DECOY_CONTRACT))
    av = V(TREATMENT_ADDRESS_SCHEMA)
    for p in PREMISES:
        for t in treatments(p):
            rec = address_record(p["id"], t["format_id"], t["approach_id"])
            assert av.is_valid(rec), rec["address"]
    # The module reads storyboard_rules.json next to itself; load a temporary copy with the generated rules.
    import importlib.util
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(MODULES / ID_CHECK / f"{ID_CHECK}.py", Path(tmp) / f"{ID_CHECK}.py")
        (Path(tmp) / "storyboard_rules.json").write_text(dumps(storyboard_rules_json()), encoding="utf-8")
        spec = importlib.util.spec_from_file_location("_tsc", Path(tmp) / f"{ID_CHECK}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_tsc"] = mod
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.modules.pop("_tsc", None)
        for rec in [board_record(b) for b in SLATE["boards"]] + [pitch_record(p) for p in SLATE["pitches"]]:
            found = mod.check_board(rec)
            assert not found, f"{rec['id']}: {found}"


self_check()

COMMON_TAGS = ["story"]
NO_FX = effects()
CONSIDERED_RULE_NOTE = ("Editorial guidance from the owner's guide, written after Taylor rejected BOXED IN's story "
                        "quality. Its review methods (table read, silent animatic, owner storyboard choice) are "
                        "proposed; nothing here is validated audience research.")

with GeneratorRun(__file__, data=DATA_REL) as run:
    # --- contract schemas -------------------------------------------------------------------------------------
    edu001, ent072 = PREMISE_BY_ID["EDU001"], PREMISE_BY_ID["ENT072"]
    bad_premise = premise_record(edu001)
    bad_premise.pop("gate")
    bad_premise["evidence_class"] = "verified"
    upgraded = premise_record(ent072)
    upgraded["status"] = "rendered"
    mismatch = premise_record(edu001)
    mismatch["family"] = "fiction"
    run.component(
        "contract-schema", ID_PREMISE_SCHEMA,
        title="Story premise record",
        summary="JSON Schema for one catalogue story premise as Appendix D structures it: premise, hook, visible action, "
                "takeaway or theme, gate, evidence class, format tags, ten treatment addresses and an honest status.",
        subkind="premise", domain="story",
        files={"schema.json": dumps(STORY_PREMISE_SCHEMA),
               f"examples/{edu001['id'].lower()}.json": dumps(premise_record(edu001)),
               f"examples/{ent072['id'].lower()}.json": dumps(premise_record(ent072)),
               "examples/invalid-missing-gate-and-upgraded-evidence.json": dumps(bad_premise),
               "examples/invalid-rendered-without-evidence.json": dumps(upgraded),
               "examples/invalid-family-does-not-match-id.json": dumps(mismatch)},
        tags=COMMON_TAGS + ["premise", "schema", "catalogue", "evidence"],
        step_kinds=["plan", "write", "verify"],
        source=source(APPD["anchor"]),
        examples=["Validate a premise.json before boarding it", "Record a premise moving from idea to storyboarded with evidence"],
    )

    decoy_board = board_record(_DECOY)
    bad_board = {"id": "the-decoy-job", "title": "The Decoy Job", "board_type": "timed", "status": "audience-approved",
                 "dramatic_question": _DECOY["dramatic_question"], "shots": decoy_board["shots"][:2]}
    run.component(
        "contract-schema", ID_BOARD_SCHEMA,
        title="Timed storyboard or story pitch",
        summary="JSON Schema for a development board: timed boards need want/stakes/escalation/plants, contiguous timed "
                "shots and kill criteria; pitches need opening, question, rule, escalation, payoff and visual test.",
        subkind="storyboard", domain="story",
        files={"schema.json": dumps(TIMED_STORYBOARD_SCHEMA),
               "examples/the-decoy-job.json": dumps(decoy_board),
               "examples/front-legs-back-legs.json": dumps(pitch_record(SLATE["pitches"][0])),
               "examples/invalid-two-shots-and-claimed-approval.json": dumps(bad_board)},
        tags=COMMON_TAGS + ["storyboard", "schema", "shots", "pitch"],
        step_kinds=["plan", "write", "review"],
        source=source(SLATE["anchor"]),
    )

    bad_contract = copy.deepcopy(DECOY_CONTRACT)
    bad_contract.pop("plant")
    bad_contract.pop("reversal")
    bad_contract["knowledge"].pop("uncertain")
    run.component(
        "contract-schema", ID_CONTRACT_SCHEMA,
        title="Story contract",
        summary="JSON Schema for the nine sentences written before drawing shots: want, stakes, constraint, choice, "
                "escalation, knowledge, plant, reversal, consequence; plus comedy mechanisms and the suspense question.",
        subkind="story-template", domain="story",
        files={"schema.json": dumps(STORY_CONTRACT_SCHEMA),
               "examples/the-decoy-job.json": dumps(DECOY_CONTRACT),
               "examples/invalid-no-plant-or-reversal.json": dumps(bad_contract)},
        tags=COMMON_TAGS + ["story-contract", "schema", "comedy", "suspense"],
        step_kinds=["plan", "write", "review"],
        source=source(SQ["story_contract"]["anchor"]),
    )

    tm = APPC["treatment_map"]
    readme = ["# Treatment address", "", f"Source: {GUIDE_TITLE}, Appendix C (`{GUIDE_REL}#{tm['anchor']}`).", ""]
    readme += blocks(APPC["count_contract"]["paragraphs"]) + blocks(tm["intro"])
    readme += ["## Representation approaches", "",
               md_table(APPC["count_contract"]["approaches"]["columns"],
                        [[r[k] for k in APPC["count_contract"]["approaches"]["keys"]]
                         for r in APPC["count_contract"]["approaches"]["records"]]), ""]
    for g in ADDRESS_GROUPS:
        readme += [f"## Treatment group {g['group']} ({len(g['stories'])} stories)", "",
                   "Stories: " + ", ".join(f"`{s}`" for s in g["stories"]) + ".", "",
                   md_table(["Format", "Approach", "Intro", "Motion"],
                            [[r["format"], r["approach"], r["intro"], r["motion"]] for r in g["rows"]]), ""]
    readme += ["## Editorial treatment rules", ""] + [f"- {r}" for r in tm["editorial_rules"]] + [""]
    readme += tm["editorial_rules_after"] + ["",
               "`addresses.json` lists all 2,400 addresses. The `treatment_address_resolver` code module joins an "
               "address with its story, format, approach, intro and motion records."]
    all_addresses = [t["address"] for p in PREMISES for t in treatments(p)]
    assert len(all_addresses) == len(set(all_addresses)) == 2400
    run.component(
        "contract-schema", ID_ADDRESS_SCHEMA,
        title="Creative-catalogue treatment address",
        summary="JSON Schema for R-{story}-{format}-{approach} addresses: the four treatment groups are encoded exactly, "
                "so only the catalogue's 2,400 story/format/approach/intro/motion combinations validate.",
        subkind="treatment", domain="story",
        files={"schema.json": dumps(TREATMENT_ADDRESS_SCHEMA),
               "examples/r-edu001-f01-a01.json": dumps(address_record("EDU001", "F01", "A01")),
               "examples/r-ent072-f08-a04.json": dumps(address_record("ENT072", "F08", "A04")),
               "examples/r-edu101-f20-a02.json": dumps(address_record("EDU101", "F20", "A02")),
               "examples/invalid-group-four-with-tactile-approach.json": dumps(
                   {**address_record("ENT072", "F08", "A04"), "address": "R-ENT072-F08-A03", "approach_id": "A03"}),
               "examples/invalid-public-safety-story-with-f02.json": dumps(
                   {**address_record("EDU101", "F01", "A01"), "address": "R-EDU101-F02-A01", "format_id": "F02"}),
               "addresses.json": json.dumps(all_addresses, separators=(",", ":")) + "\n",
               "README.md": "\n".join(readme)},
        tags=COMMON_TAGS + ["treatment", "schema", "catalogue", "addressing"],
        step_kinds=["plan", "verify"],
        source=source(tm["anchor"]),
    )

    # --- code modules ------------------------------------------------------------------------------------------
    check_files = module_files(ID_CHECK)
    check_files["storyboard_rules.json"] = dumps(storyboard_rules_json())
    check_files["fixtures/the_decoy_job.json"] = dumps(decoy_board)
    check_files["fixtures/front_legs_back_legs.json"] = dumps(pitch_record(SLATE["pitches"][0]))
    run.component(
        "code-module", ID_CHECK,
        title="Timed storyboard check",
        summary="Checks a timed storyboard's structure (required story fields, contiguous shots from 0, shot count, "
                "duration) and prints the storyboard-gate review sheet with every answer starting as not checked.",
        subkind="qa-check", domain="story",
        files=check_files, entry=f"{ID_CHECK}.py",
        tags=COMMON_TAGS + ["storyboard", "qa", "python"],
        step_kinds=["verify", "review", "plan"],
        effects_=effects(filesystem="read", executes="python"),
        source=source(SQ["storyboard_gate"]["anchor"]),
        depends_on=[{"identity": ID_BOARD_SCHEMA}],
        evidence_stage="isolated-execution",
        evidence_notes="Its pytest suite (12 focused positive and negative checks, run against the guide's Decoy Job "
                       "board and Front Legs pitch) passed in the generator's container on 2026-10-10. It has not "
                       "been used on a production board. It checks structure only, never story quality.",
    )
    resolver_files = module_files(ID_RESOLVER)
    resolver_files["catalogue_tables.json"] = dumps(catalogue_tables_json())
    run.component(
        "code-module", ID_RESOLVER,
        title="Treatment address resolver",
        summary="Validates and resolves R-{story}-{format}-{approach} catalogue addresses into story, format, approach, "
                "intro and motion records; lists a story's ten addresses; confirms the catalogue's 2,400.",
        subkind="catalog-tool", domain="story",
        files=resolver_files, entry=f"{ID_RESOLVER}.py",
        tags=COMMON_TAGS + ["treatment", "catalogue", "python", "addressing"],
        step_kinds=["plan", "verify"],
        effects_=effects(filesystem="read", executes="python"),
        source=source(tm["anchor"]),
        depends_on=[{"identity": ID_ADDRESS_SCHEMA}],
        evidence_stage="isolated-execution",
        evidence_notes="Its pytest suite (8 tests: 2,400 unique addresses, ten per story, group-specific format and "
                       "approach rules, malformed input) passed in the generator's container on 2026-10-10. Resolving "
                       "an address joins proposal records; it does not make any treatment a screenplay or a render.",
    )

    # --- rules packages ----------------------------------------------------------------------------------------
    run.component(
        "rules", ID_CONTRACT_RULES,
        title="Story contract rules",
        summary="The BOXED IN lesson and the nine-sentence story contract (want, stakes, constraint, choice, escalation, "
                "knowledge, plant, reversal, consequence) to write before drawing shots, with the longer-film scaffold.",
        subkind="rule-set", domain="story",
        files={"RULES.md": contract_rules_md(),
               "rules.json": dumps({"source": {"document": GUIDE_REL, "section": SQ["heading"], "anchor": SQ["anchor"]},
                                    "boxed_in_lesson": SQ["boxed_in_lesson"]["paragraphs"],
                                    "contract_intro": SQ["story_contract"]["intro"], "contract": CONTRACT,
                                    "contract_notes": SQ["story_contract"]["after"],
                                    "longer_film_structure": {
                                        "paragraphs": SQ["longer_film_structure"]["paragraphs"],
                                        "illustrative_allocation_108s": allocation(),
                                        "note": "writing scaffold, not an empirically optimized retention formula"}}),
               "provenance.json": dumps(boxed_in_provenance())},
        tags=COMMON_TAGS + ["story-contract", "rules", "boxed-in", "structure"],
        step_kinds=["plan", "write", "review"],
        source=source(SQ["anchor"]),
        evidence_stage="considered",
        evidence_notes=CONSIDERED_RULE_NOTE + " BOXED IN itself: technically delivered, story rejected by Taylor "
                       "(provenance.json keeps MP4 libfile_4453aed6dfbc8191914eded938ece6df, SHA-256 "
                       f"{PROV['boxed_in_receipt']['sha256'][0]}).",
    )
    run.component(
        "rules", ID_GATE,
        title="Storyboard gate before a full render",
        summary="Compact board columns and the ten challenge questions a storyboard must survive before a substantial "
                "render: clear opening promise, because/therefore middle, fair plant, resolved question, no filler shots.",
        subkind="checklist", domain="story",
        files={"RULES.md": gate_md(),
               "rules.json": dumps({"source": {"document": GUIDE_REL, "section": "Storyboard gate before a full render",
                                               "anchor": SQ["storyboard_gate"]["anchor"]},
                                    "board_columns": ["shot image or clear composition description", "duration estimate",
                                                      "action", "new information", "character decision",
                                                      "dialogue or sound", "the story reason for the cut"],
                                    "intro": SQ["storyboard_gate"]["intro"], "questions": GATE_QUESTIONS,
                                    "after": SQ["storyboard_gate"]["after"]})},
        tags=COMMON_TAGS + ["storyboard", "gate", "rules", "review"],
        step_kinds=["review", "plan"],
        source=source(SQ["storyboard_gate"]["anchor"]),
        depends_on=[{"identity": ID_CHECK}],
        evidence_stage="considered", evidence_notes=CONSIDERED_RULE_NOTE,
    )
    run.component(
        "rules", ID_COMEDY,
        title="Comedy mechanisms",
        summary="Ten comedy mechanisms (status reversal, dramatic irony, overcomplicated solution ... quiet button), "
                "how to make each playable and the failure that rejects it.",
        subkind="rule-set", domain="story",
        files={"RULES.md": comedy_md(),
               "rules.json": dumps({"source": {"document": GUIDE_REL, "section": "Comedy mechanisms to develop",
                                               "anchor": SQ["comedy_mechanisms"]["anchor"]},
                                    "mechanisms": SQ["comedy_mechanisms"]["records"]})},
        tags=COMMON_TAGS + ["comedy", "rules", "gags"],
        step_kinds=["write", "review"],
        source=source(SQ["comedy_mechanisms"]["anchor"]),
        evidence_stage="considered", evidence_notes=CONSIDERED_RULE_NOTE,
    )
    run.component(
        "rules", ID_SUSPENSE,
        title="Suspense rules",
        summary="Suspense without empty delay: a concrete question, visible success and failure, narrowing choices, "
                "clocks that change decisions, escapes with a cost, legible geography and motivated sound.",
        subkind="rule-set", domain="story",
        files={"RULES.md": suspense_md(),
               "rules.json": dumps({"source": {"document": GUIDE_REL, "section": "Suspense without empty delay",
                                               "anchor": SQ["suspense"]["anchor"]},
                                    "rules": suspense_rules(),
                                    "contract_note": sentences(SQ["story_contract"]["after"][0])[-1]})},
        tags=COMMON_TAGS + ["suspense", "rules", "tension"],
        step_kinds=["write", "review"],
        source=source(SQ["suspense"]["anchor"]),
        evidence_stage="considered", evidence_notes=CONSIDERED_RULE_NOTE,
    )
    run.component(
        "rules", ID_TESTS,
        title="Production-independent story tests",
        summary="Seven clarity questions to ask people unfamiliar with a pitch after a rough animatic, plus the global "
                "kill criteria that no technically clean render can rescue.",
        subkind="checklist", domain="story",
        files={"RULES.md": story_tests_md(),
               "rules.json": dumps({"source": {"document": GUIDE_REL, "section": "Production-independent story tests",
                                               "anchor": STORY_TESTS["anchor"]},
                                    "intro": STORY_TESTS["intro"], "questions": STORY_TESTS["questions"],
                                    "after": STORY_TESTS["after"], "global_kill_criteria": KILL,
                                    "global_kill_criteria_text": STORY_TESTS["global_kill_criteria_text"]})},
        tags=COMMON_TAGS + ["story-tests", "animatic", "kill-criteria", "rules"],
        step_kinds=["review", "test"],
        source=source(STORY_TESTS["anchor"]),
        evidence_stage="considered",
        evidence_notes=CONSIDERED_RULE_NOTE + " The guide calls these clarity tests, not statistically meaningful "
                       "audience research.",
    )

    # --- subagent and command ----------------------------------------------------------------------------------
    run.component(
        "subagent", ID_DOCTOR,
        title="Story doctor",
        summary="Applies the story contract, causality and escalation checks, comedy/suspense mechanisms, storyboard gate "
                "and kill criteria to a draft and returns revise / ready-for-animatic / blocked, never approval.",
        subkind="review-lens", domain="story",
        files={"agent.md": agent_md(
            "story-doctor",
            "Use on a premise, pitch, script or storyboard before any substantial render. Applies the nine-sentence "
            "story contract, because/therefore causality, escalation, comedy and suspense mechanisms, the ten-question "
            "storyboard gate and the global kill criteria; returns evidence-cited findings and a verdict.",
            DOCTOR_BODY, tools=["Read", "Glob", "Grep", "Bash"])},
        tags=COMMON_TAGS + ["review", "subagent", "story-contract", "storyboard"],
        step_kinds=["review"],
        effects_=effects(filesystem="read", executes="shell", side_effects=["may run timed_storyboard_check.py"]),
        harnesses=["claude-code", "opencode", "baltor-harness"],
        source=source(SQ["anchor"]),
        depends_on=[{"identity": ID_CONTRACT_RULES}, {"identity": ID_GATE}, {"identity": ID_COMEDY},
                    {"identity": ID_SUSPENSE}, {"identity": ID_TESTS}, {"identity": ID_CHECK}],
        evidence_stage="considered",
        evidence_notes="New agent definition written from the guide's story rules; it has not yet been run on a real "
                       "draft. Its verdicts are editorial, not audience evidence.",
    )
    run.component(
        "command", ID_COMMAND,
        title="/storyboard-before-render",
        summary="Slash command that gates a story before rendering: story contract, timed board and structure check, "
                "story doctor pass, gate questions, kill criteria, cheapest real review, then render only if it passes.",
        subkind="workflow", domain="story",
        files={"command.md": command_md("Gate a story with a contract and timed storyboard before any substantial render",
                                        COMMAND_BODY, argument_hint="<premise identity | storyboard.json | script>")},
        tags=COMMON_TAGS + ["storyboard", "command", "workflow", "gate"],
        step_kinds=["plan", "review", "render"],
        harnesses=["claude-code", "opencode", "baltor-harness"],
        source=source(SQ["storyboard_gate"]["anchor"]),
        depends_on=[{"identity": ID_CONTRACT_SCHEMA}, {"identity": ID_BOARD_SCHEMA}, {"identity": ID_CHECK},
                    {"identity": ID_DOCTOR}, {"identity": ID_GATE}, {"identity": ID_TESTS}, {"identity": ID_RESOLVER}],
        evidence_stage="considered",
        evidence_notes="New command written from the guide's storyboard gate; not yet run on a production story.",
    )

    # --- storyboards and pitches -------------------------------------------------------------------------------
    slate_rows = []
    for b in SLATE["boards"]:
        ident = board_identity(b["title"], True)
        slate_rows.append([str(b["number"]), b["title"], "timed board", f"about {b['approx_duration_s']} s, "
                           f"{b['shot_count']} shots", b["dramatic_question"], f"`{ident}`"])
        run.component(
            "skill", ident,
            title=f"Storyboard: {b['title']}",
            summary=clip(f"Proposed, unrendered {b['approx_duration_s']}-second timed storyboard ({b['shot_count']} shots). "
                         f"{b['dramatic_question']}", 240),
            subkind="storyboard", domain="story",
            files={"SKILL.md": skill_md(
                ident.replace("_", "-"),
                clip(f"Use when developing, animatic-testing or rendering \"{b['title']}\", a proposed suspense/comedy "
                     f"film of about {b['approx_duration_s']} seconds. Opening: {b['opening_image']} Gives the full "
                     "timed storyboard, planted details, escalation chain, midpoint change, kill criteria and the "
                     "story tests to run before rendering. Status: proposed, unrendered.", 1020),
                board_skill(b)),
                "storyboard.json": dumps(board_record(b))},
            tags=COMMON_TAGS + ["storyboard", "comedy", "suspense", "timed-board", slug(b["title"]).replace("_", "-")],
            step_kinds=["plan", "write", "review"],
            source=source(b["anchor"]),
            depends_on=[{"identity": ID_BOARD_SCHEMA}, {"identity": ID_GATE}, {"identity": ID_TESTS}],
            evidence_stage="considered",
            evidence_notes="Proposed concept and unrendered timed storyboard (guide v1.1, 10 Oct 2026). Editorial "
                           "recommendation only: no table read, animatic, render, audience result or owner acceptance "
                           "is recorded. The earlier BOXED IN film's technical progress does not establish that a story works.",
        )
    for p in SLATE["pitches"]:
        ident = board_identity(p["title"], False)
        slate_rows.append([str(p["number"]), p["title"], "pitch", "not timed", p["question_and_goals"].split("?")[0] + "?",
                           f"`{ident}`"])
        run.component(
            "skill", ident,
            title=f"Story pitch: {p['title']}",
            summary=clip(f"Proposed development pitch, not a timed board. {p['opening_frame']}", 240),
            subkind="storyboard", domain="story",
            files={"SKILL.md": skill_md(
                ident.replace("_", "-"),
                clip(f"Use when deciding whether to develop \"{p['title']}\" into a timed storyboard. Opening frame: "
                     f"{p['opening_frame']} Gives the pitch's question and conflicting goals, world rule, causal "
                     "escalation, plant and payoff, and the visual test it must pass first. Status: pitch, not an "
                     "approved production.", 1020),
                pitch_skill(p)),
                "storyboard.json": dumps(pitch_record(p))},
            tags=COMMON_TAGS + ["storyboard", "pitch", "comedy", slug(p["title"]).replace("_", "-")],
            step_kinds=["plan", "write"],
            source=source(p["anchor"]),
            depends_on=[{"identity": ID_BOARD_SCHEMA}, {"identity": ID_CONTRACT_SCHEMA}],
            evidence_stage="considered",
            evidence_notes="Pitch from the eight-story development slate (guide v1.1, 10 Oct 2026): not an approved "
                           "production or timed board; to be developed only if its central visual test works.",
        )
    slate_md = ["# Suspense and comedy development slate (October 2026)", "",
                f"**Scope:** {SLATE['scope']}", "", f"**Status:** {SLATE_STATUS}", "", "## Recommendation", ""]
    slate_md += blocks(SLATE["recommendation"]) + blocks(SLATE["slate_intro"])
    slate_md += [md_table(["#", "Title", "Type", "Length", "Question", "Skill"], slate_rows), "",
                 "## Production-independent story tests", ""] + STORY_TESTS["intro"] + [""] + story_test_lines()
    slate_md += [""] + STORY_TESTS["after"] + ["", STORY_TESTS["global_kill_criteria_text"], "",
                 "## Source", "", f"{GUIDE_TITLE}, \"New suspense and comedy storyboards\" (`{GUIDE_REL}#{SLATE['anchor']}`)."]
    run.component(
        "skill", ID_SLATE,
        title="Suspense and comedy development slate",
        summary="Overview of the eight proposed development topics (three timed boards, five pitches) with the "
                "editorial recommendation to start with The Decoy Job and the story tests to run first.",
        subkind="idea-bank", domain="story",
        files={"SKILL.md": skill_md(
            ID_SLATE.replace("_", "-"),
            "Use when choosing which new suspense or comedy film to develop next. Lists the eight-topic development "
            "slate (The Decoy Job, Inventory Space, The Extra and five pitches), the editorial recommendation and its "
            "limits, and the story tests every board must pass before a render.",
            "\n".join(slate_md)),
            "slate.json": dumps({"scope": SLATE["scope"], "status": SLATE["status"],
                                 "recommendation": SLATE["recommendation"],
                                 "topics": [{"number": int(r[0]), "title": r[1], "type": r[2], "skill": r[5].strip("`")}
                                            for r in slate_rows]})},
        tags=COMMON_TAGS + ["storyboard", "slate", "comedy", "suspense", "idea-bank"],
        step_kinds=["plan"],
        source=source(SLATE["anchor"]),
        depends_on=[{"identity": board_identity(b["title"], True)} for b in SLATE["boards"]]
        + [{"identity": board_identity(p["title"], False)} for p in SLATE["pitches"]],
        evidence_stage="considered",
        evidence_notes="Proposed concepts, unrendered boards and pitches. Editorial ranking considers opening clarity, "
                       "causal escalation, agency, earned surprise, visual comedy and production risk; it does not "
                       "predict views or retention and is not owner acceptance.",
    )

    # --- creative banks ----------------------------------------------------------------------------------------
    for key, (ident, title, summary) in BANK_SPECS.items():
        body, bank = bank_skill(key)
        anchor = APPC["count_contract"]["anchor"] if key == "approaches" else BANKS[key]["anchor"]
        run.component(
            "skill", ident,
            title=title,
            summary=summary,
            subkind="idea-bank", domain="story",
            files={"SKILL.md": skill_md(
                ident.replace("_", "-"),
                clip(f"Use {BANK_USE[key]} {summary} From the October 2026 creative catalogue; every row keeps its "
                     "gate or check, and these are proposals, not tested recipes.", 1020),
                body),
                "bank.json": dumps(bank)},
            tags=COMMON_TAGS + ["idea-bank", "creative-catalogue", key.replace("_", "-")],
            step_kinds=["plan", "design"],
            source=source(anchor),
            evidence_stage="considered",
            evidence_notes=clip(f"Proposal bank materialized from the 10 Oct 2026 catalogue ({CAT_REF_PLAIN}). The guide "
                                "does not retroactively mark catalogue recipes rendered because a similarly named film "
                                "exists; no entry here is tested or used in a film by virtue of being listed.", 1000),
        )

    # --- 240 premises ------------------------------------------------------------------------------------------
    for p in PREMISES:
        ident = PREMISE_ID[p["id"]]
        tr = treatments(p)
        tags = COMMON_TAGS + ["premise", p["family"], tag(p["category"]), tag(p["evidence_class"]),
                              p["id"].lower()]
        if p["id"] in SU_BY_STORY:
            tags.append("style-application")
        if p["id"] in PICK_BY_STORY:
            tags.append("editorial-pick")
        run.component(
            "skill", ident,
            title=clip(f"Story premise {p['id']}: {p['title']}", 120),
            summary=clip(f"Idea-stage {p['family']} premise ({p['category']}). Hook: {p['hook']} "
                         f"Takeaway/theme: {p['intended_takeaway_or_theme']}", 240),
            description=p["premise"],
            subkind="premise", domain="story",
            files={"SKILL.md": skill_md(ident.replace("_", "-"), premise_description(p), premise_skill(p)),
                   "premise.json": dumps(premise_record(p))},
            tags=list(dict.fromkeys(tags)),
            step_kinds=["plan", "write"],
            source=source(p["anchor"]),
            depends_on=[{"identity": ID_PREMISE_SCHEMA}, {"identity": ID_CONTRACT_RULES}, {"identity": ID_TESTS}],
            parameters={"id": p["id"], "treatment_group": GROUP_OF[p["id"]]["group"], "guide_line": p["line"]},
            evidence_stage="considered",
            evidence_notes=clip(f"Idea from the 10 Oct 2026 creative catalogue ({CAT_REF_PLAIN}), preserved in guide "
                                f"Appendix D line {p['line']}. Not a completed script, not rendered, no audience study. "
                                f"Evidence class {p['evidence_class']} is a classification, not a completed "
                                f"check. Its ten treatment addresses ({tr[0]['address']} ...) are candidates, not "
                                "screenplays.", 1000),
        )

print(f"ref_stories: parsed {len(PREMISES)}/240 premises, {len(SLATE['boards'])} timed boards, "
      f"{len(SLATE['pitches'])} pitches, {sum(len(BANKS[k]['records']) for k in BANKS)} bank rows + 4 approaches, "
      f"{len(all_addresses)} treatment addresses")
