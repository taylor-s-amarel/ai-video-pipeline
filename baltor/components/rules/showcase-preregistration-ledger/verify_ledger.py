#!/usr/bin/env python3
"""Check showcase task packages against the pre-registration ledger.

Usage: python3 verify_ledger.py PACKAGE_DIR [PACKAGE_DIR ...]
Exit 0 when every package's task.json hashes to its ledger entry and every file listed in
files_sha256 is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def spec_hash(task: dict) -> str:
    body = {k: v for k, v in task.items() if k != "spec_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def check_package(pkg: Path, ledger: dict) -> list[str]:
    problems = []
    task = json.loads((pkg / "task.json").read_text(encoding="utf-8"))
    h = spec_hash(task)
    entry = ledger.get(task["id"])
    if entry is None:
        problems.append(f"{task['id']}: not in the ledger")
    elif entry["spec_sha256"] != h:
        problems.append(f"{task['id']}: spec hash {h[:12]} does not match the ledger's {entry['spec_sha256'][:12]}")
    if task.get("spec_sha256") != h:
        problems.append(f"{task['id']}: task.json spec_sha256 does not match its content")
    for rel, digest in sorted(task.get("files_sha256", {}).items()):
        p = pkg / rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            problems.append(f"{task['id']}: {rel} differs from the pre-registered file")
    return problems


def main(argv: list[str]) -> int:
    rules = json.loads((HERE / "rules.json").read_text(encoding="utf-8"))
    ledger = {r["task_id"]: r for r in rules["tasks"]}
    problems = []
    for arg in argv:
        problems += check_package(Path(arg), ledger)
    for p in problems:
        print("PROBLEM", p)
    print(f"{len(argv)} package(s) checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
