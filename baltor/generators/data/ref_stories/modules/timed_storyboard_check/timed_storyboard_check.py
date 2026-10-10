#!/usr/bin/env python3
"""Structural checks and a review sheet for a timed storyboard or pitch.

Input is a JSON document shaped by the ``timed_storyboard`` contract schema
(``board_type`` "timed" with ``shots``, or "pitch"). The checks are the parts of
the storyboard gate a program can verify: required story fields are present,
shots start at 0 and run without gaps or overlaps, the last shot ends at the
declared duration, the declared shot count matches, and the escalation chain
has more than one link. They cannot judge whether the story is funny, tense or
causal; ``review_sheet`` prints the gate questions, the production-independent
story tests and the global kill criteria for a person or a reviewing agent to
answer, with every item starting as "not checked".

Usage:
    python3 timed_storyboard_check.py storyboard.json            # findings, exit 1 on errors
    python3 timed_storyboard_check.py storyboard.json --json     # findings as JSON
    python3 timed_storyboard_check.py storyboard.json --sheet    # Markdown review sheet

Wording of the questions comes from ``storyboard_rules.json`` next to this file
(Animation and Video Production Master Guide, 10 October 2026).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

RULES = json.loads(Path(__file__).with_name("storyboard_rules.json").read_text(encoding="utf-8"))

TIMED_REQUIRED = ("title", "dramatic_question", "characters_and_goals", "stakes", "escalation_chain",
                  "planted_details", "shots", "midpoint_change", "kill_criteria")
PITCH_REQUIRED = ("title", "opening_frame", "question_and_goals", "rule", "causal_escalation",
                  "plant_and_payoff", "visual_test")
MIN_ACTION_CHARS = 40


@dataclass
class Finding:
    level: str  # "error" or "warning"
    field: str
    message: str


def _empty(value) -> bool:
    return value is None or (isinstance(value, (str, list, dict)) and len(value) == 0) or \
        (isinstance(value, str) and not value.strip())


def check_board(board: dict) -> list[Finding]:
    """Return structural findings. An empty list means only that the structure is complete."""
    out: list[Finding] = []
    kind = board.get("board_type")
    if kind not in ("timed", "pitch"):
        return [Finding("error", "board_type", f"board_type must be 'timed' or 'pitch', not {kind!r}")]
    required = TIMED_REQUIRED if kind == "timed" else PITCH_REQUIRED
    for key in required:
        if _empty(board.get(key)):
            out.append(Finding("error", key, f"{key} is missing or empty"))
    if kind == "pitch":
        return out

    chain = board.get("escalation_chain") or []
    if isinstance(chain, list) and 0 < len(chain) < 3:
        out.append(Finding("warning", "escalation_chain",
                           f"only {len(chain)} link(s); each attempt should change the situation rather than reset it"))
    shots = board.get("shots") or []
    if not isinstance(shots, list):
        return out + [Finding("error", "shots", "shots must be a list")]
    expected_start = 0.0
    titles: dict[str, int] = {}
    for n, shot in enumerate(shots, 1):
        label = f"shots[{n}]"
        start, end = shot.get("start_s"), shot.get("end_s")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            out.append(Finding("error", label, "start_s and end_s must be numbers"))
            continue
        if shot.get("index") not in (None, n):
            out.append(Finding("error", label, f"index {shot.get('index')} should be {n}"))
        if end <= start:
            out.append(Finding("error", label, f"ends at {end}s, not after its start {start}s"))
        if abs(start - expected_start) > 1e-6:
            what = "gap" if start > expected_start else "overlap"
            out.append(Finding("error", label, f"{what}: starts at {start}s, previous shot ends at {expected_start}s"))
        expected_start = end
        action = str(shot.get("action", ""))
        if len(action.strip()) < MIN_ACTION_CHARS:
            out.append(Finding("warning", label, "no substantial action stated; a shot needs action, new information or a decision"))
        title = str(shot.get("title", "")).strip().lower()
        if title:
            if title in titles:
                out.append(Finding("warning", label, f"repeats the title of shot {titles[title]}"))
            titles[title] = n
    if shots:
        declared = board.get("approx_duration_s")
        if isinstance(declared, (int, float)) and abs(expected_start - declared) > 1e-6:
            out.append(Finding("warning", "approx_duration_s",
                               f"shots end at {expected_start}s but the board declares about {declared}s"))
        count = board.get("shot_count")
        if isinstance(count, int) and count != len(shots):
            out.append(Finding("error", "shot_count", f"declares {count} shots but lists {len(shots)}"))
    return out


def review_sheet(board: dict) -> str:
    """Markdown sheet: timing table, gate questions, story tests and kill criteria, all 'not checked'."""
    lines = [f"# Story review sheet: {board.get('title', 'untitled')}", ""]
    lines.append(f"Board type: {board.get('board_type')}. Status recorded on the board: {board.get('status', 'not stated')}.")
    lines.append("Every answer below starts as **not checked**. Fill an answer only from the board text or an observed "
                 "review; an editorial guess is not audience evidence.")
    lines.append("")
    findings = check_board(board)
    lines.append("## Structural findings")
    lines.append("")
    if findings:
        lines += [f"- {f.level.upper()} `{f.field}`: {f.message}" for f in findings]
    else:
        lines.append("- none (structure only; this says nothing about story quality)")
    lines.append("")
    if board.get("board_type") == "timed" and board.get("shots"):
        lines += ["## Shots", "", "| # | Time | Title | Because / therefore link to previous shot |", "|---|---|---|---|"]
        for n, s in enumerate(board["shots"], 1):
            lines.append(f"| {n} | {s.get('start_s')}–{s.get('end_s')} s | {s.get('title', '')} | not checked |")
        lines.append("")
    lines += ["## Storyboard gate", ""]
    for n, q in enumerate(RULES["storyboard_gate"]["questions"], 1):
        lines.append(f"{n}. {q}")
        lines.append("   - Answer: not checked")
        lines.append("   - Evidence (shot numbers or quoted board text): not checked")
    lines += ["", "## Production-independent story tests", "",
              RULES["story_tests"]["intro"], ""]
    for n, q in enumerate(RULES["story_tests"]["questions"], 1):
        lines.append(f"{n}. {q} — viewer answers: not collected")
    lines += ["", RULES["story_tests"]["after"], "", "## Global kill criteria", ""]
    for k in RULES["global_kill_criteria"]:
        lines.append(f"- [ ] {k} — not checked")
    if board.get("kill_criteria"):
        lines += ["", "## This board's own kill criteria", "", board["kill_criteria"]]
    lines += ["", RULES["global_kill_criteria_closing"], ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("board")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    ap.add_argument("--sheet", action="store_true", help="print a Markdown review sheet")
    a = ap.parse_args(argv)
    board = json.loads(Path(a.board).read_text(encoding="utf-8"))
    if a.sheet:
        print(review_sheet(board))
        return 0
    findings = check_board(board)
    if a.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.level.upper():7} {f.field}: {f.message}")
        print("structure complete" if not findings else f"{len(findings)} finding(s)")
    return 1 if any(f.level == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
