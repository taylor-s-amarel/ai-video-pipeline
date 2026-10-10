"""Parse and validate commit messages against Conventional Commits 1.0.0.

Implements the specification at https://www.conventionalcommits.org/en/v1.0.0/:
``<type>[optional scope][!]: <description>``, an optional body one blank line
later, and optional git-trailer style footers (``Token: value`` or
``Token #value``). ``BREAKING CHANGE`` / ``BREAKING-CHANGE`` footers or ``!``
mark a breaking change.

Usage::

    python conventional_commit_parser.py --file .git/COMMIT_EDITMSG
    echo "feat(api)!: drop v1" | python conventional_commit_parser.py --json

Exit status 0 when the message is valid, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field

DEFAULT_TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
HEADER_RE = re.compile(r"^(?P<type>[A-Za-z][\w-]*)(?:\((?P<scope>[^()\r\n]+)\))?(?P<bang>!)?: (?P<description>\S.*)$")
FOOTER_RE = re.compile(r"^(?P<token>BREAKING CHANGE|BREAKING-CHANGE|[A-Za-z][\w-]*)(?P<sep>: | #)(?P<value>.*)$")
SKIP_PREFIXES = ("Merge ", "Revert \"", "fixup! ", "squash! ", "amend! ")


@dataclass
class Footer:
    token: str
    value: str


@dataclass
class Commit:
    type: str
    scope: str | None
    description: str
    body: str = ""
    footers: list[Footer] = field(default_factory=list)
    breaking: bool = False
    breaking_description: str | None = None

    def bump(self) -> str:
        """Semantic-version bump implied by this commit: major, minor, patch or none."""
        if self.breaking:
            return "major"
        if self.type == "feat":
            return "minor"
        if self.type in {"fix", "perf"}:
            return "patch"
        return "none"


class ParseError(ValueError):
    pass


def _strip_comments(message: str) -> str:
    lines = [ln for ln in message.replace("\r\n", "\n").split("\n") if not ln.startswith("#")]
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def parse(message: str) -> Commit:
    """Parse a commit message. Raises ParseError if the header is not conventional."""
    text = _strip_comments(message)
    lines = text.split("\n")
    if not lines or not lines[0].strip():
        raise ParseError("empty commit message")
    m = HEADER_RE.match(lines[0])
    if not m:
        raise ParseError("header must look like 'type(scope)!: description' (scope and ! optional)")
    if len(lines) > 1 and lines[1].strip():
        raise ParseError("the body must begin one blank line after the description")
    rest = lines[2:] if len(lines) > 2 else []
    # Footers are the trailing paragraph(s) whose first line is a footer token.
    footer_start = None
    for i, line in enumerate(rest):
        if FOOTER_RE.match(line) and (i == 0 or not rest[i - 1].strip()):
            footer_start = i
            break
    body_lines = rest if footer_start is None else rest[:footer_start]
    footers: list[Footer] = []
    if footer_start is not None:
        for line in rest[footer_start:]:
            fm = FOOTER_RE.match(line)
            if fm:
                footers.append(Footer(fm.group("token"), fm.group("value")))
            elif footers:
                footers[-1].value += "\n" + line
    for f in footers:
        f.value = f.value.rstrip()
    breaking_footer = next((f for f in footers if f.token in {"BREAKING CHANGE", "BREAKING-CHANGE"}), None)
    commit = Commit(
        type=m.group("type").lower(),
        scope=m.group("scope"),
        description=m.group("description").strip(),
        body="\n".join(body_lines).strip(),
        footers=footers,
        breaking=bool(m.group("bang")) or breaking_footer is not None,
        breaking_description=breaking_footer.value if breaking_footer else (m.group("description").strip() if m.group("bang") else None),
    )
    return commit


def validate(message: str, allowed_types: tuple[str, ...] | None = DEFAULT_TYPES, max_header: int = 100,
             allow_merge_and_fixup: bool = True) -> list[str]:
    """Return a list of problems (empty when valid)."""
    text = _strip_comments(message)
    if allow_merge_and_fixup and text.startswith(SKIP_PREFIXES):
        return []
    try:
        c = parse(message)
    except ParseError as exc:
        return [str(exc)]
    problems = []
    header = text.split("\n", 1)[0]
    if len(header) > max_header:
        problems.append(f"header is {len(header)} characters (limit {max_header})")
    if allowed_types and c.type not in allowed_types:
        problems.append(f"type '{c.type}' is not one of {', '.join(allowed_types)}")
    if c.description.endswith("."):
        problems.append("description should not end with a period")
    for f in c.footers:
        if f.token.lower() == "breaking change" and f.token != "BREAKING CHANGE":
            problems.append("BREAKING CHANGE footer token must be uppercase")
    return problems


def highest_bump(messages: list[str]) -> str:
    """Highest bump across several commits (for release tooling)."""
    order = {"none": 0, "patch": 1, "minor": 2, "major": 3}
    best = "none"
    for msg in messages:
        try:
            b = parse(msg).bump()
        except ParseError:
            continue
        if order[b] > order[best]:
            best = b
    return best


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a Conventional Commits message")
    ap.add_argument("--file", help="read the message from this file (default: stdin)")
    ap.add_argument("--types", help="comma-separated allowed types (default: the common Angular set)")
    ap.add_argument("--any-type", action="store_true", help="accept any type token")
    ap.add_argument("--max-header", type=int, default=100)
    ap.add_argument("--json", action="store_true", help="print the parsed commit as JSON")
    a = ap.parse_args(argv)
    message = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    types = None if a.any_type else (tuple(t.strip() for t in a.types.split(",")) if a.types else DEFAULT_TYPES)
    problems = validate(message, types, a.max_header)
    if a.json and not problems:
        c = parse(message)
        print(json.dumps({**asdict(c), "bump": c.bump()}, indent=2))
    for p in problems:
        print(f"commit message: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
