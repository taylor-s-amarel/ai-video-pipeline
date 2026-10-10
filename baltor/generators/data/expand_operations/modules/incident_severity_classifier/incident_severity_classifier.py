#!/usr/bin/env python3
"""Classify an incident's severity from observable impact facts using an editable matrix.

    python incident_severity_classifier.py --facts facts.json [--matrix severity_matrix.json]

``facts.json`` example::

    {"users_affected_pct": 30, "core_function_down": true, "data_loss": false,
     "security_exposure": false, "revenue_path_impacted": true, "workaround": false, "internal_only": false}

Rules in the matrix are checked from the most severe level down; the first level with a matching rule
wins and every matching reason is reported. Unknown facts count as "not observed"; say so in the
incident channel rather than guessing. The default matrix (``severity_matrix.json`` next to this
file) is a starting point to adapt, not an industry standard.
"""

from __future__ import annotations

import argparse
import json
import operator
import sys
from pathlib import Path

OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq, "!=": operator.ne}
DEFAULT_MATRIX = Path(__file__).with_name("severity_matrix.json")


def load_matrix(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or DEFAULT_MATRIX).read_text(encoding="utf-8"))


def _match(cond: dict, facts: dict) -> bool:
    """A condition is {"fact": name, "op": ">=", "value": 25}; all keys in "all" must hold."""
    if "all" in cond:
        return all(_match(c, facts) for c in cond["all"])
    if "any" in cond:
        return any(_match(c, facts) for c in cond["any"])
    if cond["fact"] not in facts or facts[cond["fact"]] is None:
        return False
    return OPS[cond.get("op", "==")](facts[cond["fact"]], cond.get("value", True))


def classify(facts: dict, matrix: dict | None = None) -> dict:
    matrix = matrix or load_matrix()
    unknown = sorted(set(matrix.get("facts", {})) - {k for k, v in facts.items() if v is not None})
    for level in matrix["levels"]:
        reasons = [r["reason"] for r in level["rules"] if _match(r["when"], facts)]
        if reasons or level.get("default"):
            return {"severity": level["name"], "reasons": reasons or ["no higher-severity rule matched"],
                    "response": level.get("response", {}), "unknown_facts": unknown}
    raise ValueError("matrix has no default level")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--facts", required=True, help="JSON file with impact facts, or - for stdin")
    ap.add_argument("--matrix")
    a = ap.parse_args(argv)
    facts = json.load(sys.stdin) if a.facts == "-" else json.loads(Path(a.facts).read_text())
    print(json.dumps(classify(facts, load_matrix(a.matrix)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
