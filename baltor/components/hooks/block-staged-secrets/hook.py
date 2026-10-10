#!/usr/bin/env python3
"""PreToolUse hook: refuse a `git commit` when staged changes contain something that looks like a credential.

Claude Code passes the tool call as JSON on stdin. Exit code 2 blocks the call and shows stderr to the agent.
Works for any harness that can run a command before a shell call and read JSON from stdin.
"""

import json
import re
import subprocess
import sys

PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{24,}"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
]


def staged_additions() -> str:
    proc = subprocess.run(["git", "diff", "--cached", "--unified=0", "--no-color"],
                          capture_output=True, text=True)
    return "\n".join(line[1:] for line in proc.stdout.splitlines()
                     if line.startswith("+") and not line.startswith("+++"))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    if not re.search(r"\bgit\b[^|;&]*\bcommit\b", command):
        return 0
    added = staged_additions()
    hits = [p.pattern for p in PATTERNS if p.search(added)]
    if hits:
        print("Blocked: staged changes contain what looks like a credential "
              f"({len(hits)} pattern(s)). Remove it, rotate the key, and stage again.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
