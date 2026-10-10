"""Branch naming policy and stale-branch report for a git repository.

* ``check_name`` validates a branch name against git's ref-format rules
  (https://git-scm.com/docs/git-check-ref-format) and a team naming pattern
  such as ``feat/1234-short-slug``.
* ``report`` lists local branches that are merged into the base branch, whose
  upstream is gone, or whose last commit is older than N days, using
  ``git for-each-ref`` and ``git branch --merged``. It never deletes anything;
  it prints the commands a human (or an approved agent step) can run.

Usage::

    python branch_hygiene_report.py check feat/123-add-login
    python branch_hygiene_report.py report --base main --stale-days 30 [--json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field

DEFAULT_PATTERN = r"^(feat|fix|chore|docs|refactor|perf|test|build|ci|hotfix|release|deps)/[a-z0-9][a-z0-9._-]*(/[a-z0-9._-]+)*$"
LONG_LIVED = {"main", "master", "develop", "trunk", "gh-pages"}
RELEASE_RE = re.compile(r"^release/\d+\.\d+(\.x)?$")


def ref_format_problems(name: str) -> list[str]:
    """Subset of git check-ref-format rules that apply to branch names."""
    p = []
    if not name or name == "@":
        p.append("empty or '@'")
    if name.startswith(("-", "/")) or name.endswith(("/", ".")):
        p.append("must not start with '-' or '/' or end with '/' or '.'")
    if ".." in name or "//" in name or "@{" in name:
        p.append("must not contain '..', '//' or '@{'")
    if re.search(r"[\x00-\x20\x7f~^:?*\[\\]", name):
        p.append("must not contain spaces, control characters or any of ~ ^ : ? * [ \\")
    if any(part.startswith(".") or part.endswith(".lock") for part in name.split("/")):
        p.append("no path component may start with '.' or end with '.lock'")
    return p


def check_name(name: str, pattern: str = DEFAULT_PATTERN, max_len: int = 60) -> list[str]:
    problems = ref_format_problems(name)
    if name in LONG_LIVED or RELEASE_RE.match(name):
        return problems
    if not re.match(pattern, name):
        problems.append(f"does not match the naming pattern {pattern}")
    if len(name) > max_len:
        problems.append(f"is {len(name)} characters (limit {max_len})")
    if name != name.lower():
        problems.append("use lower case")
    return problems


@dataclass
class Branch:
    name: str
    last_commit: str
    age_days: int
    track: str = ""
    merged: bool = False
    reasons: list[str] = field(default_factory=list)


def _git(args: list[str], cwd: str | None) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=cwd).stdout


def parse_for_each_ref(output: str, now: dt.datetime) -> list[Branch]:
    out = []
    for line in output.splitlines():
        if not line.strip():
            continue
        name, date, track = (line.split("\t") + ["", ""])[:3]
        when = dt.datetime.fromisoformat(date.strip())
        out.append(Branch(name.strip(), date.strip(), (now - when).days, track.strip()))
    return out


def report(base: str = "main", stale_days: int = 30, cwd: str | None = None, now: dt.datetime | None = None) -> list[Branch]:
    now = now or dt.datetime.now(dt.timezone.utc)
    raw = _git(["for-each-ref", "--format=%(refname:short)%09%(committerdate:iso8601-strict)%09%(upstream:track)",
                "refs/heads"], cwd)
    merged = {ln.strip().lstrip("* ").strip() for ln in _git(["branch", "--merged", base], cwd).splitlines()}
    current = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd).strip()
    flagged = []
    for b in parse_for_each_ref(raw, now):
        if b.name in LONG_LIVED or b.name == base or b.name == current:
            continue
        b.merged = b.name in merged
        if b.merged:
            b.reasons.append(f"merged into {base}")
        if "[gone]" in b.track:
            b.reasons.append("upstream branch is gone")
        if b.age_days >= stale_days:
            b.reasons.append(f"no commits for {b.age_days} days")
        if b.reasons:
            flagged.append(b)
    return flagged


def cleanup_commands(branches: list[Branch]) -> list[str]:
    cmds = []
    for b in branches:
        flag = "-d" if b.merged else "-D"
        note = "" if b.merged else "   # not merged: check the work is saved elsewhere first"
        cmds.append(f"git branch {flag} {b.name}{note}")
    return cmds


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Branch naming and stale-branch report")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("name"); c.add_argument("--pattern", default=DEFAULT_PATTERN)
    r = sub.add_parser("report"); r.add_argument("--base", default="main"); r.add_argument("--stale-days", type=int, default=30)
    r.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        problems = check_name(a.name, a.pattern)
        for p in problems:
            print(f"branch '{a.name}': {p}", file=sys.stderr)
        return 1 if problems else 0
    flagged = report(a.base, a.stale_days)
    if a.json:
        print(json.dumps([asdict(b) for b in flagged], indent=2))
    else:
        for b in flagged:
            print(f"{b.name:<40} {', '.join(b.reasons)}")
        if flagged:
            print("\nSuggested cleanup (review before running):")
            print("\n".join(cleanup_commands(flagged)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
