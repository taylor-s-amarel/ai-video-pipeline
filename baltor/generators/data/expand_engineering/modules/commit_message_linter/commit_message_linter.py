"""Lint commit message style: 50/72 lengths, blank line, imperative mood, trailers, WIP markers.

Complements a Conventional Commits check: this module looks at readability and
git conventions (see https://git-scm.com/docs/git-commit#_discussion and the
"git trailer" format in https://git-scm.com/docs/git-interpret-trailers).

Usage::

    python commit_message_linter.py .git/COMMIT_EDITMSG          # commit-msg hook
    git log -1 --format=%B | python commit_message_linter.py -   # stdin

Exit 1 when any error is found; warnings alone exit 0 (use --strict to fail on them).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass

CC_PREFIX = re.compile(r"^[A-Za-z][\w-]*(?:\([^()]+\))?!?: ")
_STEMS = ("add", "fix", "updat", "remov", "chang", "refactor", "implement", "improv", "creat", "delet",
          "renam", "mov", "bump", "merg", "correct", "clean", "introduc", "replac", "support", "handl",
          "upgrad", "migrat", "adjust", "tweak", "enabl", "disabl", "allow", "prevent", "ensur", "us")
# Past tense, gerund and third-person forms of common commit verbs ("Added", "Fixing", "Updates").
NON_IMPERATIVE = {stem + suffix for stem in _STEMS for suffix in ("ed", "es", "ing", "s")} - {"uss"}
TRAILER_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9-]*): (?P<value>.+)$")
PERSON_TRAILERS = {"signed-off-by", "co-authored-by", "reviewed-by", "acked-by", "tested-by", "reported-by"}
URL_ONLY = re.compile(r"^\s*(?:[-*]\s*)?(?:\[\d+\]:?\s*)?\S+://\S+\s*$")


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    line: int
    message: str


def lint(message: str, subject_soft: int = 50, subject_hard: int = 72, body_width: int = 72,
         require_capital: bool | None = None) -> list[Finding]:
    lines = [ln for ln in message.replace("\r\n", "\n").split("\n") if not ln.startswith("#")]
    while lines and not lines[-1].strip():
        lines.pop()
    out: list[Finding] = []
    if not lines or not lines[0].strip():
        return [Finding("error", 1, "empty subject line")]
    subject = lines[0]
    if len(subject) > subject_hard:
        out.append(Finding("error", 1, f"subject is {len(subject)} characters; keep it under {subject_hard}"))
    elif len(subject) > subject_soft:
        out.append(Finding("warning", 1, f"subject is {len(subject)} characters; aim for {subject_soft} or fewer"))
    if subject.rstrip().endswith("."):
        out.append(Finding("error", 1, "subject ends with a period"))
    if subject != subject.strip():
        out.append(Finding("warning", 1, "subject has leading or trailing whitespace"))
    if re.match(r"^(wip|fixup!|squash!|amend!|tmp|temp)\b", subject, re.I):
        out.append(Finding("warning", 1, "work-in-progress or fixup marker; squash before merging"))
    is_cc = bool(CC_PREFIX.match(subject))
    words = CC_PREFIX.sub("", subject).split()
    if words:
        first = re.sub(r"[^A-Za-z]", "", words[0]).lower()
        if first in NON_IMPERATIVE:
            out.append(Finding("warning", 1, f"use the imperative mood ('{words[0]}' -> e.g. 'Add', 'Fix', 'Update')"))
        cap = (not is_cc) if require_capital is None else require_capital
        if cap and words[0][:1].islower():
            out.append(Finding("warning", 1, "start the subject with a capital letter"))
    if len(lines) > 1 and lines[1].strip():
        out.append(Finding("error", 2, "separate subject from body with a blank line"))
    in_fence = False
    trailer_block_start = len(lines)
    for i in range(len(lines) - 1, 0, -1):
        if TRAILER_RE.match(lines[i]):
            trailer_block_start = i
        elif lines[i].strip() == "":
            break
        else:
            trailer_block_start = len(lines)
            break
    for idx, line in enumerate(lines[2:], start=3):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.startswith(("    ", "\t")) or URL_ONLY.match(line):
            continue
        if idx - 1 >= trailer_block_start:
            m = TRAILER_RE.match(line)
            if m and m.group("key").lower() in PERSON_TRAILERS and not re.search(r"<[^<>@\s]+@[^<>\s]+>", m.group("value")):
                out.append(Finding("error", idx, f"{m.group('key')} trailer needs 'Name <email>'"))
            continue
        if len(line) > body_width:
            out.append(Finding("warning", idx, f"body line is {len(line)} characters; wrap at {body_width}"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lint a git commit message")
    ap.add_argument("file", nargs="?", default="-", help="message file, or - for stdin")
    ap.add_argument("--strict", action="store_true", help="fail on warnings too")
    ap.add_argument("--subject-soft", type=int, default=50)
    ap.add_argument("--subject-hard", type=int, default=72)
    a = ap.parse_args(argv)
    text = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8").read()
    findings = lint(text, a.subject_soft, a.subject_hard)
    for f in findings:
        print(f"{f.severity}: line {f.line}: {f.message}", file=sys.stderr)
    failing = [f for f in findings if f.severity == "error" or a.strict]
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
