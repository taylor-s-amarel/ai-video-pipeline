#!/usr/bin/env python3
"""PreToolUse guard for showcase trials: in the baseline arm, refuse any tool call that reaches a Baltor catalogue.

showcase_runner installs it for BOTH arms (``--guard-hook``) with ``--arm baseline`` or ``--arm baltor`` so the
harness configuration has the same shape in both; it only ever blocks in the baseline arm. The harness passes the
tool call as JSON on stdin; exit code 2 blocks the call and shows stderr to the agent.

Blocked in the baseline arm: MCP tools whose name starts with ``mcp__baltor``, and any tool input that mentions the
catalogue tool, the ``baltor`` shim, the hosted endpoint, a component or catalogue directory, a placed ``.baltor/``
folder or a step lock.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

PATTERNS = [
    r"baltor_catalog\.py",
    r"(?:^|[\s;&|(`'\"])baltor\s+(?:search|read|place)\b",
    r"baltor\.ai",
    r"/baltor/(?:components|catalog|tools)/",
    r"(?:^|[\s/'\"])\.baltor(?:/|\b)",
    r"step\.lock\.json",
    r"intelligence_search",
    r"provisioning_read",
    r"showcase_catalogue_gateway",
]
COMPILED = [re.compile(p, re.IGNORECASE) for p in PATTERNS]


def blocked(event: dict, arm: str) -> str | None:
    if arm != "baseline":
        return None
    name = str(event.get("tool_name", ""))
    if name.lower().startswith("mcp__baltor"):
        return f"tool {name} belongs to the Baltor catalogue"
    blob = json.dumps(event.get("tool_input") or {}, ensure_ascii=False)
    for pat in COMPILED:
        if pat.search(blob):
            return f"tool input matches {pat.pattern!r}"
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["baseline", "baltor"], required=True)
    a = ap.parse_args(argv)
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    reason = blocked(event if isinstance(event, dict) else {}, a.arm)
    if reason:
        print(f"Blocked: this is the baseline arm of a showcase comparison and must not use the Baltor catalogue "
              f"({reason}). Solve the task with the tools you have.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
