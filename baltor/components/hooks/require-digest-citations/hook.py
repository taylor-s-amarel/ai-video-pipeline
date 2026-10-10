#!/usr/bin/env python3
"""Stop hook: refuse to finish while a recently written digest has a bullet without a source link.

Checks Markdown files under $BALTOR_DIGEST_DIR (default: digests/) modified in the last
$BALTOR_DIGEST_MAX_AGE_MIN minutes (default 120). Every bullet ("- " or "* ") outside the
"Feeds that failed" section must contain a Markdown link to an http(s) URL.

Claude Code passes the event as JSON on stdin. Exit code 2 blocks the stop and shows stderr to the
agent; when the event says a stop hook is already active, the hook allows the stop to avoid loops.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

LINK = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")
BULLET = re.compile(r"^\s*[-*]\s+\S")
EXEMPT_HEADINGS = ("feeds that failed", "errors", "rejected leads")


def problems_in(text: str) -> list[str]:
    out, exempt = [], False
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("#"):
            exempt = any(h in line.lower() for h in EXEMPT_HEADINGS)
            continue
        if exempt or not BULLET.match(line):
            continue
        if not LINK.search(line):
            out.append(f"line {n}: {line.strip()[:100]}")
    return out


def recent_digests(root: Path, max_age_s: float, now: float | None = None) -> list[Path]:
    now = now or time.time()
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.md") if now - p.stat().st_mtime <= max_age_s)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        event = {}
    if event.get("stop_hook_active"):
        return 0
    root = Path(os.environ.get("BALTOR_DIGEST_DIR", "digests"))
    max_age = float(os.environ.get("BALTOR_DIGEST_MAX_AGE_MIN", "120")) * 60
    report = []
    for path in recent_digests(root, max_age):
        bad = problems_in(path.read_text(encoding="utf-8", errors="replace"))
        if bad:
            report.append(f"{path}: {len(bad)} bullet(s) without a source link\n  " + "\n  ".join(bad[:10]))
    if report:
        print("Digest lines must each link to their source. Add the link or remove the claim:\n"
              + "\n".join(report), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
