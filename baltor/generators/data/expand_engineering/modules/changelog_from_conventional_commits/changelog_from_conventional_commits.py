"""Turn Conventional Commits into a Keep a Changelog 1.1.0 section and the next SemVer version.

Reads ``git log`` between two refs (or a JSON list of messages), groups commits into
Added / Changed / Deprecated / Removed / Fixed / Security, flags breaking changes, and
can insert the section into CHANGELOG.md directly under ``## [Unreleased]``.

Usage::

    python changelog_from_conventional_commits.py --from v1.4.0 --to HEAD --version auto --current 1.4.0
    python changelog_from_conventional_commits.py --messages commits.json --version 2.0.0 --write CHANGELOG.md

Standard library only; runs ``git log`` when --from/--to are given.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
from dataclasses import dataclass

HEADER_RE = re.compile(r"^(?P<type>[A-Za-z][\w-]*)(?:\((?P<scope>[^()\r\n]+)\))?(?P<bang>!)?: (?P<desc>\S.*)$")
SECTION_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
TYPE_TO_SECTION = {"feat": "Added", "fix": "Fixed", "perf": "Changed", "revert": "Removed",
                   "deprecate": "Deprecated", "security": "Security", "sec": "Security"}
HIDDEN_TYPES = {"docs", "chore", "ci", "test", "style", "build", "refactor"}
SEP_FIELD, SEP_RECORD = "\x1f", "\x1e"


@dataclass
class Entry:
    section: str
    text: str
    breaking: bool
    sha: str = ""


def classify(message: str, sha: str = "", include_hidden: bool = False) -> Entry | None:
    lines = message.strip().splitlines()
    if not lines:
        return None
    m = HEADER_RE.match(lines[0])
    if not m:
        return None
    ctype = m.group("type").lower()
    body = "\n".join(lines[1:])
    breaking_footer = re.search(r"^BREAKING[ -]CHANGE: (.+)$", body, re.M)
    breaking = bool(m.group("bang") or breaking_footer)
    scope = (m.group("scope") or "").lower()
    section = TYPE_TO_SECTION.get(ctype)
    if scope == "security" or re.search(r"^(CVE|GHSA)-", body, re.M):
        section = "Security"
    if re.search(r"^Deprecated: ", body, re.M) and section is None:
        section = "Deprecated"
    if section is None:
        if breaking:
            section = "Changed"
        elif include_hidden and ctype in HIDDEN_TYPES:
            section = "Changed"
        else:
            return None
    text = m.group("desc").strip()
    if m.group("scope"):
        text = f"**{m.group('scope')}:** {text}"
    if breaking:
        detail = breaking_footer.group(1).strip() if breaking_footer else None
        text = "**BREAKING:** " + text + (f" ({detail})" if detail and detail not in text else "")
    return Entry(section, text, breaking, sha)


def bump_for(entries: list[Entry]) -> str:
    if any(e.breaking for e in entries):
        return "major"
    if any(e.section == "Added" for e in entries):
        return "minor"
    if entries:
        return "patch"
    return "none"


def next_version(current: str, bump: str, pre_major_minor: bool = True) -> str:
    major, minor, patch = (int(x) for x in re.match(r"^v?(\d+)\.(\d+)\.(\d+)", current).groups())
    if bump == "major" and major == 0 and pre_major_minor:
        bump = "minor"
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return f"{major}.{minor}.{patch}"


def render(version: str, entries: list[Entry], date: str | None = None, link_sha: str | None = None) -> str:
    date = date or _dt.date.today().isoformat()
    out = [f"## [{version}] - {date}", ""]
    for section in SECTION_ORDER:
        items = [e for e in entries if e.section == section]
        if not items:
            continue
        out.append(f"### {section}")
        out.append("")
        for e in sorted(items, key=lambda e: (not e.breaking,)):
            suffix = f" ([{e.sha[:7]}]({link_sha.format(sha=e.sha)}))" if link_sha and e.sha else ""
            out.append(f"- {e.text}{suffix}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def insert_into_changelog(changelog: str, section: str) -> str:
    """Insert below '## [Unreleased]' (kept, emptied) or above the first release heading."""
    m = re.search(r"^## \[Unreleased\][^\n]*\n", changelog, re.M | re.I)
    if m:
        nxt = re.search(r"^## \[", changelog[m.end():], re.M)
        end = m.end() + (nxt.start() if nxt else len(changelog) - m.end())
        return changelog[:m.end()] + "\n" + section + "\n" + changelog[end:].lstrip("\n")
    m = re.search(r"^## ", changelog, re.M)
    if m:
        return changelog[:m.start()] + section + "\n" + changelog[m.start():]
    return changelog.rstrip("\n") + "\n\n" + section


def git_messages(rev_from: str | None, rev_to: str = "HEAD", cwd: str | None = None) -> list[tuple[str, str]]:
    rng = f"{rev_from}..{rev_to}" if rev_from else rev_to
    out = subprocess.run(["git", "log", "--no-merges", f"--format=%H{SEP_FIELD}%B{SEP_RECORD}", rng],
                         capture_output=True, text=True, check=True, cwd=cwd).stdout
    pairs = []
    for rec in out.split(SEP_RECORD):
        rec = rec.strip("\n")
        if SEP_FIELD in rec:
            sha, msg = rec.split(SEP_FIELD, 1)
            pairs.append((sha.strip(), msg))
    return pairs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="rev_from")
    ap.add_argument("--to", dest="rev_to", default="HEAD")
    ap.add_argument("--messages", help="JSON file: list of messages or of {sha, message}")
    ap.add_argument("--version", default="auto", help="release version, or 'auto' to compute from --current")
    ap.add_argument("--current", default="0.0.0", help="current version when --version auto")
    ap.add_argument("--date")
    ap.add_argument("--include-hidden", action="store_true")
    ap.add_argument("--commit-url", help="e.g. https://github.com/o/r/commit/{sha}")
    ap.add_argument("--write", help="insert the section into this CHANGELOG.md")
    a = ap.parse_args(argv)
    if a.messages:
        raw = json.load(open(a.messages, encoding="utf-8"))
        pairs = [(r.get("sha", ""), r["message"]) if isinstance(r, dict) else ("", r) for r in raw]
    else:
        pairs = git_messages(a.rev_from, a.rev_to)
    entries = [e for sha, msg in pairs if (e := classify(msg, sha, a.include_hidden))]
    version = next_version(a.current, bump_for(entries)) if a.version == "auto" else a.version
    section = render(version, entries, a.date, a.commit_url)
    if a.write:
        try:
            existing = open(a.write, encoding="utf-8").read()
        except FileNotFoundError:
            existing = "# Changelog\n\nAll notable changes to this project are documented in this file.\n\n## [Unreleased]\n"
        open(a.write, "w", encoding="utf-8").write(insert_into_changelog(existing, section))
    print(section, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
