"""Resolve GitHub-style CODEOWNERS for changed files, and lint the CODEOWNERS file.

Semantics follow GitHub's documentation (about-code-owners): gitignore-like
patterns, the *last* matching line wins, a line with a pattern and no owners
makes matching files explicitly unowned, ``!`` negation and ``[ ]`` ranges are
not supported, and ``\\#`` escapes a leading hash.

Usage::

    git diff --name-only origin/main... | python codeowners_resolver.py --codeowners .github/CODEOWNERS
    python codeowners_resolver.py --codeowners CODEOWNERS --lint
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

OWNER_RE = re.compile(r"^(@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:/[A-Za-z0-9._-]+)?|[^@\s]+@[^@\s]+\.[^@\s]+)$")
LOCATIONS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")


@dataclass
class Rule:
    line: int
    pattern: str
    owners: list[str]
    regex: re.Pattern


def pattern_to_regex(pattern: str) -> re.Pattern:
    p = pattern
    anchored = p.startswith("/")
    p = p.lstrip("/")
    dir_only = p.endswith("/")
    p = p.rstrip("/")
    if "/" in p:
        anchored = True
    out, i = [], 0
    while i < len(p):
        if p.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif p.startswith("/**", i) and i + 3 == len(p):
            out.append("/.*")
            i += 3
        elif p.startswith("**", i):
            out.append(".*")
            i += 2
        elif p[i] == "*":
            out.append("[^/]*")
            i += 1
        elif p[i] == "?":
            out.append("[^/]")
            i += 1
        elif p[i] == "\\" and i + 1 < len(p):
            out.append(re.escape(p[i + 1]))
            i += 2
        else:
            out.append(re.escape(p[i]))
            i += 1
    body = "".join(out)
    prefix = "" if anchored else "(?:.*/)?"
    last = p.rsplit("/", 1)[-1]
    if dir_only:
        suffix = "/.*"
    elif "/" in p and "*" in last and "**" not in last:
        suffix = ""  # GitHub: 'docs/*' matches direct children only, not nested files
    else:
        suffix = "(?:/.*)?"
    return re.compile(f"^{prefix}{body}{suffix}$")


def parse(text: str) -> tuple[list[Rule], list[str]]:
    rules, problems = [], []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.split(r"\s+#", line, maxsplit=1)[0]  # trailing comment
        parts = line.split()
        pattern, owners = parts[0], parts[1:]
        if pattern.startswith("!"):
            problems.append(f"line {n}: '!' negation is not supported in CODEOWNERS")
            continue
        if "[" in pattern and not pattern.startswith("\\["):
            problems.append(f"line {n}: character ranges '[ ]' are not supported in CODEOWNERS")
        for o in owners:
            if not OWNER_RE.match(o):
                problems.append(f"line {n}: '{o}' is not @user, @org/team or an email address")
        rules.append(Rule(n, pattern, owners, pattern_to_regex(pattern.replace("\\#", "#"))))
    return rules, problems


def owners_for(path: str, rules: list[Rule]) -> tuple[list[str], int | None]:
    path = path.lstrip("./") if path.startswith("./") else path.lstrip("/")
    match = None
    for r in rules:
        if r.regex.match(path):
            match = r
    return (list(match.owners), match.line) if match else ([], None)


def review_plan(paths: list[str], rules: list[Rule]) -> dict:
    by_owner: dict[str, list[str]] = {}
    unowned = []
    for p in paths:
        owners, _ = owners_for(p, rules)
        if not owners:
            unowned.append(p)
        for o in owners:
            by_owner.setdefault(o, []).append(p)
    return {"owners": by_owner, "unowned": unowned}


def find_codeowners(root: str = ".") -> str | None:
    import os
    for loc in LOCATIONS:
        if os.path.exists(os.path.join(root, loc)):
            return os.path.join(root, loc)
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Resolve CODEOWNERS for changed paths")
    ap.add_argument("--codeowners", help="path to CODEOWNERS (default: search .github/, root, docs/)")
    ap.add_argument("--lint", action="store_true", help="only lint the file")
    ap.add_argument("paths", nargs="*", help="paths (default: read from stdin, one per line)")
    a = ap.parse_args(argv)
    path = a.codeowners or find_codeowners()
    if not path:
        print("no CODEOWNERS file found", file=sys.stderr)
        return 2
    rules, problems = parse(open(path, encoding="utf-8").read())
    for p in problems:
        print(f"{path}: {p}", file=sys.stderr)
    if a.lint:
        return 1 if problems else 0
    paths = a.paths or [ln.strip() for ln in sys.stdin if ln.strip()]
    print(json.dumps(review_plan(paths, rules), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
