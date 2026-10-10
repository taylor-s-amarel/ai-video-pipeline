#!/usr/bin/env python3
"""Check that Markdown runbooks are usable at 3 a.m.: required sections, verifiable steps, owner, freshness.

Usage::

    python runbook_lint.py runbooks/*.md [--max-age-days 180] [--today 2026-10-10] [--json]

A runbook passes when it has the required sections (by heading text, case-insensitive), an owner and
a last-reviewed date in front matter or a "Owner:" / "Last reviewed:" line, at least one fenced command
block, a rollback or escalation path, and no placeholder text (TODO, TBD, FIXME, XXX). Exit 1 on any error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys

REQUIRED = {
    "summary": ("summary", "overview", "purpose", "when to use"),
    "symptoms": ("symptoms", "alert", "triggers", "signals"),
    "diagnosis": ("diagnosis", "investigate", "triage", "checks"),
    "mitigation": ("mitigation", "remediation", "fix", "resolution", "steps"),
    "rollback": ("rollback", "roll back", "revert", "undo"),
    "escalation": ("escalation", "escalate", "contacts", "who to call"),
}
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b|<\s*(fill|insert)[^>]*>", re.I)
DANGEROUS = re.compile(r"\b(rm\s+-rf\s+/(\s|$)|kubectl\s+delete\s+(ns|namespace)\b|terraform\s+destroy|DROP\s+(TABLE|DATABASE)|--force\b)", re.I)


def headings(text: str) -> list[str]:
    return [h.strip().lower() for h in re.findall(r"^#{1,6}\s+(.+)$", text, re.M)]


def meta_value(text: str, key: str) -> str | None:
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    pattern = re.compile(rf"^\s*\**{key}\**\s*:\s*\**\s*(.+?)\s*$", re.I | re.M)
    for block in ([fm.group(1)] if fm else []) + [text]:
        m = pattern.search(block)
        if m:
            return m.group(1).strip().strip("'\"*")
    return None


def lint(text: str, today: _dt.date, max_age_days: int = 180) -> dict:
    errors, warnings = [], []
    hs = headings(text)
    for section, words in REQUIRED.items():
        if not any(any(w in h for w in words) for h in hs):
            errors.append(f"missing section: {section} (one heading containing {' / '.join(words)})")
    owner = meta_value(text, "owner")
    if not owner:
        errors.append("no owner (front matter `owner:` or an 'Owner:' line)")
    reviewed = meta_value(text, "last[ _-]?reviewed")
    if not reviewed:
        errors.append("no last-reviewed date")
    else:
        try:
            age = (today - _dt.date.fromisoformat(reviewed[:10])).days
            if age > max_age_days:
                errors.append(f"last reviewed {age} days ago (limit {max_age_days})")
        except ValueError:
            errors.append(f"last-reviewed date '{reviewed}' is not YYYY-MM-DD")
    blocks = re.findall(r"```[^\n]*\n(.*?)```", text, re.S)
    if not blocks:
        errors.append("no fenced command blocks; steps should be copy-pasteable")
    for m in PLACEHOLDER.finditer(text):
        errors.append(f"placeholder text '{m.group(0)}'")
    if not re.search(r"\b(expect(ed)?|should (see|show|return)|verify|confirm)\b", text, re.I):
        warnings.append("no verification language; say what output means the step worked")
    for b in blocks:
        for m in DANGEROUS.finditer(b):
            if not re.search(r"(confirm|approval|warning|danger|irreversible)", text, re.I):
                warnings.append(f"destructive command '{m.group(0).strip()}' without a confirmation/approval note")
    if not re.search(r"https?://\S*(dashboard|grafana|d/|logs|console)", text, re.I):
        warnings.append("no dashboard or log link")
    return {"errors": errors, "warnings": warnings, "owner": owner, "last_reviewed": reviewed}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--max-age-days", type=int, default=180)
    ap.add_argument("--today", help="YYYY-MM-DD (default: today, UTC)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    today = _dt.date.fromisoformat(a.today) if a.today else _dt.datetime.now(_dt.timezone.utc).date()
    results = {}
    for path in a.files:
        with open(path, encoding="utf-8") as fh:
            results[path] = lint(fh.read(), today, a.max_age_days)
    if a.json:
        print(json.dumps(results, indent=2))
    else:
        for path, r in results.items():
            for e in r["errors"]:
                print(f"{path}: ERROR {e}")
            for w in r["warnings"]:
                print(f"{path}: warn  {w}")
    return 1 if any(r["errors"] for r in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
