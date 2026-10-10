#!/usr/bin/env python3
"""Check showcase task packages against the pre-registration ledger.

Usage: python3 verify_ledger.py PACKAGE_DIR [PACKAGE_DIR ...]
Exit 0 when every package's task.json hashes to the ledger entry and every setup and
evaluator file matches the hash recorded in task.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXCLUDED = ("spec_hash", "preregistration")


def spec_hash(task: dict) -> str:
    body = {k: v for k, v in task.items() if k not in EXCLUDED}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def check_package(pkg: Path, ledger: dict) -> list[str]:
    problems = []
    task = json.loads((pkg / "task.json").read_text(encoding="utf-8"))
    h = spec_hash(task)
    entry = ledger.get(task["task_id"])
    if entry is None:
        problems.append(f"{task['task_id']}: not in the ledger")
    elif entry["spec_hash"] != h:
        problems.append(f"{task['task_id']}: spec hash {h[:12]} does not match ledger {entry['spec_hash'][:12]}")
    if task.get("spec_hash") != h:
        problems.append(f"{task['task_id']}: task.json spec_hash field does not match its content")
    for group in ("setup", "evaluator"):
        for f in task[group]["files"]:
            p = pkg / f["path"]
            if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
                problems.append(f"{task['task_id']}: {f['path']} differs from the pre-registered file")
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
