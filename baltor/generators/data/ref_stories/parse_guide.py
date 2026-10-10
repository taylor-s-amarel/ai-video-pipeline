#!/usr/bin/env python3
"""Parse the story parts of the Animation and Video Production Master Guide.

Sections are located by their headings, never by fixed line numbers, and every
record keeps the guide line it came from. Running this file directly rewrites
``extracted/*.json`` next to it; ``ref_stories.py`` imports the same functions.

Parsed sections (guide version 1.1, 10 October 2026):

* "Story quality comes before production scale" (BOXED IN lesson, story contract,
  comedy mechanisms, suspense, storyboard gate, longer-film structure)
* "New suspense and comedy storyboards" (scope, recommendation, three timed
  boards, five pitches, production-independent story tests, global kill criteria)
* "Appendix C Creative banks and exact treatment addressing"
* "Appendix D All 240 story premises"
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
GUIDE_NAME = "Animation_and_Video_Production_Master_Guide_2026-10-10.md"
GUIDE_REL = f"docs/reference/{GUIDE_NAME}"
GUIDE = REPO_ROOT / GUIDE_REL
EXTRACTED = HERE / "extracted"

BOLD_FIELD = re.compile(r"^\*\*([^*]+?):\*\*\s*(.*)$")


def github_anchor(heading: str) -> str:
    """GitHub-style heading anchor: lower case, punctuation dropped, spaces to hyphens."""
    text = heading.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


class Guide:
    def __init__(self, path: Path = GUIDE):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines()

    def find(self, heading: str, start: int = 0) -> int:
        """0-based index of the first line equal to ``heading`` at or after ``start``."""
        for i in range(start, len(self.lines)):
            if self.lines[i].strip() == heading:
                return i
        raise KeyError(f"heading not found: {heading!r}")

    def section(self, heading: str, start: int = 0) -> tuple[int, int]:
        """(first, end) 0-based half-open range of a section, ending at the next heading of equal or higher level."""
        i = self.find(heading, start)
        level = len(heading) - len(heading.lstrip("#"))
        j = i + 1
        while j < len(self.lines):
            m = re.match(r"^(#+) ", self.lines[j])
            if m and len(m.group(1)) <= level:
                break
            j += 1
        return i, j

    def text(self, a: int, b: int) -> str:
        return "\n".join(self.lines[a:b]).strip()


def paragraphs(lines: list[str]) -> list[str]:
    out, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln.strip())
        elif cur:
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def parse_table(lines: list[str], start: int) -> tuple[list[str], list[list[str]], int]:
    """Parse a pipe table whose header row is at or after ``start`` (blank lines between rows are tolerated)."""
    i = start
    while not lines[i].startswith("|"):
        i += 1
    header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    rows: list[list[str]] = []
    j = i + 1
    while j < len(lines):
        ln = lines[j]
        if not ln.strip():
            # a blank line ends the table unless another table row follows immediately
            if j + 1 < len(lines) and lines[j + 1].startswith("|"):
                j += 1
                continue
            break
        if not ln.startswith("|"):
            break
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            j += 1
            continue
        if len(cells) != len(header):
            raise ValueError(f"table row at line {j + 1} has {len(cells)} cells, header has {len(header)}")
        rows.append(cells)
        j += 1
    return header, rows, j


def snake_key(label: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return key


def table_records(guide: Guide, heading: str, start: int = 0) -> dict:
    a, b = guide.section(heading, start)
    first = _first_table_line(guide.lines, a + 1)
    if first >= b:
        raise ValueError(f"no table under {heading!r}")
    header, rows, end = parse_table(guide.lines, first)
    keys = [snake_key(h) for h in header]
    return {"heading": heading.lstrip("# ").strip(), "anchor": github_anchor(heading.lstrip("# ")),
            "line": a + 1, "columns": header, "keys": keys,
            "intro": paragraphs(guide.lines[a + 1:first]), "after": paragraphs(guide.lines[end:b]),
            "records": [dict(zip(keys, r)) for r in rows]}


def _first_table_line(lines: list[str], start: int) -> int:
    i = start
    while not lines[i].startswith("|"):
        i += 1
    return i


def numbered_items(lines: list[str]) -> list[str]:
    items, cur = [], None
    for ln in lines:
        m = re.match(r"^\d+\.\s+(.*)$", ln)
        if m:
            if cur is not None:
                items.append(cur)
            cur = m.group(1).strip()
        elif cur is not None and ln.strip() and not ln.startswith(("#", "|", "- ")):
            cur += " " + ln.strip()
        elif cur is not None and not ln.strip():
            items.append(cur)
            cur = None
    if cur is not None:
        items.append(cur)
    return items


def bullet_items(lines: list[str]) -> list[str]:
    return [ln[2:].strip() for ln in lines if ln.startswith("- ")]


# --------------------------------------------------------------------------- story quality section

def parse_story_quality(g: Guide) -> dict:
    top = "## Story quality comes before production scale"
    a, b = g.section(top)
    out: dict = {"heading": top[3:], "anchor": github_anchor(top[3:]), "line": a + 1}

    s, e = g.section("### The lesson from BOXED IN", a)
    out["boxed_in_lesson"] = {"line": s + 1, "anchor": github_anchor("The lesson from BOXED IN"),
                              "paragraphs": paragraphs(g.lines[s + 1:e])}

    s, e = g.section("### A useful story contract", a)
    body = g.lines[s + 1:e]
    contract = []
    for ln in bullet_items(body):
        m = re.match(r"^\*\*([^*]+?):\*\*\s*(.*)$", ln)
        contract.append({"key": snake_key(m.group(1)), "label": m.group(1), "question": m.group(2)})
    out["story_contract"] = {"line": s + 1, "anchor": github_anchor("A useful story contract"),
                             "intro": paragraphs([x for x in body if not x.startswith("- ")])[0],
                             "sentences": contract,
                             "after": paragraphs([x for x in body if not x.startswith("- ")])[1:]}

    out["comedy_mechanisms"] = table_records(g, "### Comedy mechanisms to develop", a)

    s, e = g.section("### Suspense without empty delay", a)
    out["suspense"] = {"line": s + 1, "anchor": github_anchor("Suspense without empty delay"),
                       "paragraphs": paragraphs(g.lines[s + 1:e])}

    s, e = g.section("### Storyboard gate before a full render", a)
    body = g.lines[s + 1:e]
    first_num = next(i for i, ln in enumerate(body) if re.match(r"^\d+\. ", ln))
    last_num = max(i for i, ln in enumerate(body) if re.match(r"^\d+\. ", ln))
    out["storyboard_gate"] = {"line": s + 1, "anchor": github_anchor("Storyboard gate before a full render"),
                              "intro": paragraphs(body[:first_num]),
                              "questions": numbered_items(body[first_num:last_num + 1]),
                              "after": paragraphs(body[last_num + 1:])}

    s, e = g.section("### A flexible longer-film structure", a)
    out["longer_film_structure"] = {"line": s + 1, "anchor": github_anchor("A flexible longer-film structure"),
                                    "paragraphs": paragraphs(g.lines[s + 1:e])}
    return out


# --------------------------------------------------------------------------- slate

BOARD_FIELDS = {
    "Format": "format_text",
    "Opening image": "opening_image",
    "Dramatic question": "dramatic_question",
    "Characters and conflicting goals": "characters_and_goals",
    "World rule": "world_rule",
    "One world rule": "world_rule",
    "Stakes": "stakes",
    "Escalation chain": "escalation_chain_text",
    "Planted details": "planted_details",
    "Midpoint change": "midpoint_change",
    "Why watch the next beat": "why_watch_next_beat",
    "Alternate ending": "alternate_ending",
    "Obvious weakness to test": "obvious_weakness",
    "Kill criteria before rendering": "kill_criteria",
}
PITCH_FIELDS = {
    "Opening frame": "opening_frame",
    "Question and conflicting goals": "question_and_goals",
    "Rule": "rule",
    "Causal escalation": "causal_escalation",
    "Plant and payoff": "plant_and_payoff",
    "Visual test": "visual_test",
}
SHOT = re.compile(r"^\*\*(\d+)–(\d+) seconds\. (.+?)\*\*\s+(.*)$")


def _fields(lines: list[str], mapping: dict, start_line: int) -> tuple[dict, dict]:
    out, labels = {}, {}
    for i, ln in enumerate(lines):
        m = BOLD_FIELD.match(ln)
        if m and m.group(1) in mapping:
            key = mapping[m.group(1)]
            if key in out:
                raise ValueError(f"duplicate field {m.group(1)} at line {start_line + i}")
            out[key] = m.group(2).strip()
            labels[key] = m.group(1)
    return out, labels


def parse_slate(g: Guide) -> dict:
    top = "## New suspense and comedy storyboards"
    a, b = g.section(top)
    body = g.lines[a + 1:b]
    out: dict = {"heading": top[3:], "anchor": github_anchor(top[3:]), "line": a + 1}
    head_paras = paragraphs(body[: next(i for i, ln in enumerate(body) if ln.startswith("### "))])
    out["scope"] = re.sub(r"^\*\*Scope:\*\*\s*", "", head_paras[0])
    out["status"] = head_paras[1]
    s, e = g.section("### Recommendation", a)
    out["recommendation"] = paragraphs(g.lines[s + 1:e])

    boards = []
    for heading in ("### 1. The Decoy Job", "### 2. Inventory Space", "### 3. The Extra"):
        s, e = g.section(heading, a)
        lines = g.lines[s + 1:e]
        # the board's own section contains a "#### Timed storyboard" subsection; take fields from whole range
        e2 = s + 1
        while e2 < b and not (g.lines[e2].startswith("### ") or g.lines[e2].startswith("## ")):
            e2 += 1
        lines = g.lines[s + 1:e2]
        fields, labels = _fields(lines, BOARD_FIELDS, s + 2)
        ts = next(i for i, ln in enumerate(lines) if ln.strip() == "#### Timed storyboard")
        shots = []
        for k, item in enumerate(numbered_items(lines[ts + 1:])):
            m = SHOT.match(item)
            if not m:
                continue
            shots.append({"index": len(shots) + 1, "start_s": int(m.group(1)), "end_s": int(m.group(2)),
                          "title": m.group(3).rstrip("."), "action": m.group(4).strip()})
        number, title = heading[4:].split(". ", 1)
        fmt = fields["format_text"]
        dur = re.search(r"approximately (\d+) seconds", fmt)
        nshots = re.search(r"; (\w+) shots;", fmt)
        words = {"ten": 10, "nine": 9, "eight": 8, "eleven": 11, "twelve": 12}
        cast = fmt.split("shots;", 1)[1].strip().rstrip(".") if "shots;" in fmt else ""
        board = {"number": int(number), "title": title, "anchor": github_anchor(heading[4:]), "line": s + 1,
                 "board_type": "timed", **fields, "field_labels": labels,
                 "approx_duration_s": int(dur.group(1)), "shot_count": words[nshots.group(1)], "cast": cast,
                 "escalation_chain": [x.strip().rstrip(".") for x in fields["escalation_chain_text"].split("→")],
                 "shots": shots}
        boards.append(board)
    out["boards"] = boards

    s, e = g.section("### Five more distinct topics: an eight-story development slate", a)
    out["slate_intro"] = paragraphs(g.lines[s + 1:g.find("#### 4. Front Legs, Back Legs", s)])
    pitches = []
    for i in range(s + 1, e):
        m = re.match(r"^#### (\d+)\. (.+)$", g.lines[i])
        if not m:
            continue
        ps, pe = g.section(g.lines[i], s)
        fields, labels = _fields(g.lines[ps + 1:pe], PITCH_FIELDS, ps + 2)
        pitches.append({"number": int(m.group(1)), "title": m.group(2), "anchor": github_anchor(f"{m.group(1)}. {m.group(2)}"),
                        "line": ps + 1, "board_type": "pitch", **fields, "field_labels": labels})
    out["pitches"] = pitches

    s, e = g.section("### Production-independent story tests", a)
    body = g.lines[s + 1:e]
    first_num = next(i for i, ln in enumerate(body) if re.match(r"^\d+\. ", ln))
    last_num = max(i for i, ln in enumerate(body) if re.match(r"^\d+\. ", ln))
    after = paragraphs(body[last_num + 1:])
    kill = next(p for p in after if p.startswith("Global kill criteria:"))
    out["story_tests"] = {"line": s + 1, "anchor": github_anchor("Production-independent story tests"),
                          "intro": paragraphs(body[:first_num]), "questions": numbered_items(body[first_num:last_num + 1]),
                          "after": [p for p in after if p is not kill], "global_kill_criteria_text": kill,
                          "global_kill_criteria": _split_kill(kill)}
    return out


def _split_kill(text: str) -> list[str]:
    body = text.split(":", 1)[1].strip()
    first, _, tail = body.partition(". ")
    items = [x.strip() for x in first.split(";")]
    items = [re.sub(r"^or ", "", x) for x in items]
    return items


# --------------------------------------------------------------------------- appendix C

def parse_appendix_c(g: Guide) -> dict:
    top = "## Appendix C Creative banks and exact treatment addressing"
    a, b = g.section(top)
    out: dict = {"heading": top[3:], "anchor": github_anchor(top[3:]), "line": a + 1,
                 "intro": paragraphs(g.lines[a + 1:g.find("### Count and assembly contract", a)])}
    s, e = g.section("### Count and assembly contract", a)
    approaches = table_records(g, "### Count and assembly contract", a)
    out["count_contract"] = {"line": s + 1, "anchor": github_anchor("Count and assembly contract"),
                             "paragraphs": approaches["intro"], "approaches": approaches}

    s, e = g.section("### Exact 2400 treatment address map", a)
    intro = paragraphs(g.lines[s + 1:g.find("#### Treatment group 1", s)])
    groups = []
    for n in range(1, 5):
        gs, ge = g.section(f"#### Treatment group {n}", s)
        stories_line = next(ln for ln in g.lines[gs:ge] if ln.startswith("Stories:"))
        stories = re.findall(r"`((?:EDU|ENT)\d{3})`", stories_line)
        header, rows, _ = parse_table(g.lines, gs + 1)
        groups.append({"group": n, "line": gs + 1, "stories": stories,
                       "rows": [dict(zip([snake_key(h) for h in header], r)) for r in rows]})
    rs, re_ = g.section("#### Editorial treatment rules", s)
    body = g.lines[rs + 1:re_]
    rules = bullet_items(body)
    out["treatment_map"] = {"line": s + 1, "anchor": github_anchor("Exact 2400 treatment address map"),
                            "intro": intro, "groups": groups,
                            "editorial_rules": rules,
                            "editorial_rules_after": paragraphs([x for x in body if not x.startswith("- ")])}

    banks = {}
    for key, heading in (("hooks", "### Sixty hook patterns"), ("intros", "### Thirty visual intros"),
                         ("styles", "### Forty visual styles"), ("motions", "### Thirty motion patterns"),
                         ("formats", "### Twenty editorial formats"), ("axes", "### Twenty five independent visual axes"),
                         ("style_applications", "### Eighteen concrete style applications"),
                         ("top_picks", "### Original top twenty editorial picks")):
        banks[key] = table_records(g, heading, a)
    out["banks"] = banks
    return out


# --------------------------------------------------------------------------- appendix D

PREMISE_HEAD = re.compile(r"^#### ((?:EDU|ENT)\d{3}) (.+)$")
EVIDENCE = re.compile(r"^\*\*Evidence class:\*\* `([a-z_]+)`\. \*\*Original format tags:\*\* (.+?)\.?$")


def parse_appendix_d(g: Guide) -> dict:
    top = "## Appendix D All 240 story premises"
    a, b = g.section(top)
    intro = paragraphs(g.lines[a + 1:next(i for i in range(a + 1, b) if g.lines[i].startswith("### "))])
    premises = []
    category_heading = None
    i = a + 1
    while i < b:
        ln = g.lines[i]
        if ln.startswith("### "):
            category_heading = ln[4:].strip()
        m = PREMISE_HEAD.match(ln)
        if m:
            j = i + 1
            while j < b and not g.lines[j].startswith(("#### ", "### ")):
                j += 1
            body = g.lines[i + 1:j]
            paras = paragraphs(body)
            rec: dict = {"id": m.group(1), "title": m.group(2).strip(), "line": i + 1,
                         "anchor": github_anchor(ln[5:])}
            family, _, category = category_heading.partition(" ")
            rec["family"] = {"Learning": "learning", "Fiction": "fiction"}[family]
            rec["category"] = category
            rec["category_heading"] = category_heading
            plain = [p for p in paras if not p.startswith("**")]
            if len(plain) != 1:
                raise ValueError(f"{rec['id']}: expected one premise paragraph, found {len(plain)}")
            rec["premise"] = plain[0]
            for p in paras:
                fm = BOLD_FIELD.match(p)
                if not fm:
                    continue
                label = fm.group(1)
                if label == "Evidence class":
                    em = EVIDENCE.match(p)
                    if not em:
                        raise ValueError(f"{rec['id']}: cannot parse evidence line {p!r}")
                    rec["evidence_class"] = em.group(1)
                    rec["original_format_tags"] = [t.strip() for t in em.group(2).split(",")]
                else:
                    rec[{"Hook": "hook", "Visible action": "visible_action",
                         "Intended takeaway or theme": "intended_takeaway_or_theme",
                         "Gate": "gate"}[label]] = fm.group(2).strip()
            for k in ("hook", "visible_action", "intended_takeaway_or_theme", "gate", "evidence_class"):
                if k not in rec:
                    raise ValueError(f"{rec['id']}: missing {k}")
            premises.append(rec)
            i = j
            continue
        i += 1
    return {"heading": top[3:], "anchor": github_anchor(top[3:]), "line": a + 1, "intro": intro,
            "premises": premises}


# --------------------------------------------------------------------------- provenance rows (outside the story sections)

def parse_provenance(g: Guide) -> dict:
    """Library identities and SHA-256 values the guide records for the sources these components cite."""
    out = {}
    for ln_no, ln in enumerate(g.lines, 1):
        if ln.startswith("| Creative Catalogue JSON Bundle 2026-10-10 |"):
            cells = [c.strip().strip("`") for c in ln.strip().strip("|").split("|")]
            out["creative_catalogue_bundle"] = {"artifact": cells[0], "library_identity": cells[1], "version_read": cells[2],
                                                "bytes": cells[3], "sha256": cells[4], "guide_line": ln_no,
                                                "guide_section": "Appendix G Source inventory and refresh conditions"}
        if ln.startswith("| Creative Production Factory and Harness Technical Handoff |"):
            cells = [c.strip().strip("`") for c in ln.strip().strip("|").split("|")]
            out["technical_handoff"] = {"artifact": cells[0], "library_identity": cells[1], "version_read": cells[2],
                                        "bytes": cells[3], "sha256": cells[4], "guide_line": ln_no,
                                        "guide_section": "Appendix G Source inventory and refresh conditions"}
        if ln.startswith("| BOXED IN |"):
            out["boxed_in_row"] = {"text": ln, "guide_line": ln_no, "guide_section": "Completed films and what they demonstrate"}
        if ln.startswith("The *BOXED IN* MP4 is"):
            out["boxed_in_receipt"] = {"text": ln, "guide_line": ln_no, "guide_section": "Completed films and what they demonstrate"}
    if "creative_catalogue_bundle" not in out or "boxed_in_row" not in out:
        raise ValueError("provenance rows not found in the guide")
    row = out["boxed_in_row"]["text"]
    out["boxed_in_row"]["library_identities"] = re.findall(r"(MP4|source|QA) `(libfile_[0-9a-f]+)` (v\d+)", row)
    out["boxed_in_receipt"]["sha256"] = re.findall(r"`([0-9a-f]{64})`", out["boxed_in_receipt"]["text"])
    return out


def parse_all(path: Path = GUIDE) -> dict:
    g = Guide(path)
    header = g.lines[2] if len(g.lines) > 2 else ""
    return {
        "guide": {"path": GUIDE_REL, "title": g.lines[0].lstrip("# ").strip(), "prepared": header.strip("*"),
                  "lines": len(g.lines)},
        "story_quality": parse_story_quality(g),
        "slate": parse_slate(g),
        "appendix_c": parse_appendix_c(g),
        "appendix_d": parse_appendix_d(g),
        "provenance": parse_provenance(g),
    }


def write_extracted(data: dict) -> None:
    EXTRACTED.mkdir(exist_ok=True)
    for key in ("story_quality", "slate", "appendix_c", "appendix_d", "provenance"):
        (EXTRACTED / f"{key}.json").write_text(json.dumps(data[key], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (EXTRACTED / "guide.json").write_text(json.dumps(data["guide"], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def load_extracted() -> dict:
    out = {}
    for key in ("guide", "story_quality", "slate", "appendix_c", "appendix_d", "provenance"):
        out[key] = json.loads((EXTRACTED / f"{key}.json").read_text(encoding="utf-8"))
    return out


if __name__ == "__main__":
    d = parse_all(Path(sys.argv[1]) if len(sys.argv) > 1 else GUIDE)
    write_extracted(d)
    print(f"premises: {len(d['appendix_d']['premises'])}; boards: {len(d['slate']['boards'])}; "
          f"pitches: {len(d['slate']['pitches'])}; banks: {', '.join(f'{k}={len(v['records'])}' for k, v in d['appendix_c']['banks'].items())}")
