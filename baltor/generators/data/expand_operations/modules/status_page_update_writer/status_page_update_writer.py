#!/usr/bin/env python3
"""Draft and lint customer-facing status page updates for each incident phase.

    from status_page_update_writer import draft, lint
    text = draft("investigating", component="Checkout", impact="Some card payments fail", next_update_min=30)
    issues = lint(text, phase="investigating")

Phases follow the common status-page lifecycle: investigating -> identified -> monitoring -> resolved.
``lint`` flags things that repeatedly cause trouble in public updates: speculation about cause while
still investigating, blame, internal hostnames/IPs/jargon, promised fix times, a missing next-update
time, and length. It is a writing aid; a human approves every public message.

CLI::

    python status_page_update_writer.py draft --phase identified --component API --impact "Requests time out" \
        --next-update 30 --detail "We found a faulty configuration change and are reverting it."
    python status_page_update_writer.py lint --phase investigating update.txt
"""

from __future__ import annotations

import argparse
import re
import sys

PHASES = ("investigating", "identified", "monitoring", "resolved")
TEMPLATES = {
    "investigating": "{component}: We are investigating reports that {impact_lc}. {detail}We will post an update within {next} minutes.",
    "identified": "{component}: We have identified the cause of the issue where {impact_lc} and are working on a fix. {detail}Next update within {next} minutes.",
    "monitoring": "{component}: A fix has been applied and we are monitoring the results. {detail}Next update within {next} minutes.",
    "resolved": "{component}: This incident has been resolved. {impact_past}{detail}We are sorry for the disruption.",
}
SPECULATION = re.compile(r"\b(root cause|caused by|because of|due to|we believe|probably|likely)\b", re.I)
BLAME = re.compile(r"\b(human error|engineer|developer|intern|vendor's fault|their fault|mistake by|someone)\b", re.I)
PROMISE = re.compile(r"\b(will be (fixed|resolved|back) (by|in|within)|eta\b|guarantee)", re.I)
INTERNAL = re.compile(r"\b(\d{1,3}\.){3}\d{1,3}\b|\b[\w-]+\.(internal|corp|local|svc\.cluster\.local)\b|\b(pod|kubectl|oomkilled|"
                      r"crashloopbackoff|k8s|kubernetes|terraform|postgres|redis|kafka|5\d\d errors?|stack ?trace|null pointer|segfault)\b", re.I)


def draft(phase: str, component: str, impact: str, next_update_min: int | None = 30, detail: str = "",
          impact_past: str = "") -> str:
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}")
    if phase != "resolved" and not next_update_min:
        raise ValueError("every non-final update needs a next-update time")
    detail = (detail.strip().rstrip(".") + ". ") if detail.strip() else ""
    impact_lc = impact.strip().rstrip(".")
    impact_lc = impact_lc[:1].lower() + impact_lc[1:]
    return TEMPLATES[phase].format(component=component.strip(), impact_lc=impact_lc, detail=detail, next=next_update_min,
                                   impact_past=(impact_past.strip().rstrip(".") + ". ") if impact_past else "").strip()


def lint(text: str, phase: str, max_chars: int = 600) -> list[str]:
    issues = []
    if phase == "investigating" and SPECULATION.search(text):
        issues.append(f"speculates about cause while investigating: '{SPECULATION.search(text).group(0)}'")
    if BLAME.search(text):
        issues.append(f"assigns blame: '{BLAME.search(text).group(0)}' (describe the system, not people)")
    if PROMISE.search(text):
        issues.append(f"promises a fix time: '{PROMISE.search(text).group(0)}' (commit to the next update instead)")
    for m in INTERNAL.finditer(text):
        issues.append(f"internal detail or jargon: '{m.group(0)}'")
    if phase != "resolved" and not re.search(r"\b(next update|update (within|by|in))\b", text, re.I):
        issues.append("no next-update time")
    if len(text) > max_chars:
        issues.append(f"{len(text)} characters; keep updates under {max_chars}")
    if text.strip() and text.strip() == text.strip().upper():
        issues.append("all caps reads as alarm")
    return issues


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draft")
    d.add_argument("--phase", choices=PHASES, required=True)
    d.add_argument("--component", required=True)
    d.add_argument("--impact", required=True)
    d.add_argument("--next-update", type=int, default=30)
    d.add_argument("--detail", default="")
    l_ = sub.add_parser("lint")
    l_.add_argument("--phase", choices=PHASES, required=True)
    l_.add_argument("file")
    a = ap.parse_args(argv)
    if a.cmd == "draft":
        text = draft(a.phase, a.component, a.impact, a.next_update, a.detail)
        print(text)
        problems = lint(text, a.phase)
    else:
        problems = lint(sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8").read(), a.phase)
    for p in problems:
        print("WARN", p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
