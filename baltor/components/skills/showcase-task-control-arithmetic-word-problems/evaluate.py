#!/usr/bin/env python3
"""Deterministic evaluator for the negative-control tasks. Prints JSON (see showcase_eval)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import showcase_eval as se  # noqa: E402


def _lines(path: Path) -> list[str]:
    return [l.rstrip() for l in path.read_text(encoding="utf-8").rstrip("\n").split("\n")]


def eval_fizzbuzz(p, ws, hd):
    out = ws / "output.txt"
    if not out.exists():
        return {"correct_fraction": 0.0}, [se.check("output_exists", False, "output.txt missing")], [], {}
    got, exp = _lines(out), _lines(hd / "expected.txt")
    right = sum(1 for a, b in zip(got, exp) if a == b)
    checks = [se.check("output_exists", True), se.check("line_count", len(got) == len(exp), f"{len(got)} vs {len(exp)}")]
    return {"correct_fraction": right / len(exp) if len(got) == len(exp) else right / max(len(exp), len(got))}, checks, [], {}


def eval_arithmetic(p, ws, hd):
    exp = se.load_json_file(hd / "expected.json")
    try:
        got = se.load_json_file(ws / "answers.json")
    except (OSError, ValueError) as exc:
        return {"correct_fraction": 0.0}, [se.check("answers_parse", False, exc)], [], {}
    wrong = []
    for k, v in exp.items():
        g = got.get(k) if isinstance(got, dict) else None
        try:
            ok = g is not None and float(g) == float(v)
        except (TypeError, ValueError):
            ok = False
        if not ok:
            wrong.append(k)
    return ({"correct_fraction": 1 - len(wrong) / len(exp)}, [se.check("answers_parse", True)], [],
            {"wrong_ids": wrong})


def eval_typo_fix(p, ws, hd):
    exp = _lines(hd / "expected.md")
    typos = se.load_json_file(hd / "typos.json")
    if not (ws / "README.md").exists():
        return {"typos_fixed_fraction": 0.0, "lines_matching_fraction": 0.0}, [], [], {}
    got = _lines(ws / "README.md")
    fixed = sum(1 for t in typos if t["line"] - 1 < len(got) and t["correct"] in got[t["line"] - 1]
                and t["typo"] not in got[t["line"] - 1])
    matching = sum(1 for a, b in zip(got, exp) if a == b) / max(len(exp), len(got))
    return ({"typos_fixed_fraction": fixed / len(typos), "lines_matching_fraction": matching},
            [se.check("same_line_count", len(got) == len(exp), f"{len(got)} vs {len(exp)}")], [], {})


def eval_csv_sort(p, ws, hd):
    exp = se.read_csv(hd / "expected.csv")
    try:
        got = se.read_csv(ws / "sorted.csv")
    except OSError as exc:
        return {"correct_fraction": 0.0}, [se.check("sorted_exists", False, exc)], [], {}
    header_ok = bool(got) and list(got[0].keys()) == list(exp[0].keys())
    right = sum(1 for a, b in zip(got, exp) if a == b)
    frac = right / max(len(exp), len(got)) if header_ok else 0.0
    return {"correct_fraction": frac}, [se.check("header", header_ok)], [], {}


def eval_unit_conversion(p, ws, hd):
    exp = se.load_json_file(hd / "expected.json")
    try:
        rows = se.read_csv(ws / "conversions.csv")
    except OSError as exc:
        return {"correct_fraction": 0.0}, [se.check("csv_exists", False, exc)], [], {}
    right, bad = 0, []
    for i, e in enumerate(exp):
        try:
            ok = i < len(rows) and abs(float(rows[i]["result"]) - e) <= p["tolerance"]
        except (KeyError, TypeError, ValueError):
            ok = False
        right += ok
        if not ok:
            bad.append(i + 1)
    return {"correct_fraction": right / len(exp)}, [se.check("row_count", len(rows) == len(exp))], [], {"wrong_rows": bad}


RENAME_PROBE = r'''
import json, sys
sys.path.insert(0, ".")
from shop import {new}
from shop.cart import Cart
from shop.invoice import invoice_line
spec = json.loads(sys.argv[1])
out = []
for case in spec["cases"]:
    items = [tuple(x) for x in case]
    c = Cart()
    for q, pr in items:
        c.add(q, pr)
    out.append([{new}(items, spec["tax"]), c.total(spec["tax"]), invoice_line(items, spec["tax"])])
print(json.dumps(out))
'''


def eval_rename(p, ws, hd):
    old, new = p["old_name"], p["new_name"]
    spec = se.load_json_file(hd / "expected.json")
    leftovers = []
    for f in sorted(ws.rglob("*.py")):
        if re.search(rf"\b{old}\b", f.read_text(encoding="utf-8", errors="ignore")):
            leftovers.append(f.relative_to(ws).as_posix())
    run = se.run_script([sys.executable, "-c", RENAME_PROBE.replace("{new}", new), json.dumps(spec)], ws, timeout=30)
    expected = []
    for case in spec["cases"]:
        sub = sum(q * pr for q, pr in case)
        t = round(sub * (1 + spec["tax"]), 2)
        expected.append([t, t, f"TOTAL {t:.2f}"])
    try:
        got = json.loads(run["stdout"]) if run["returncode"] == 0 else None
    except ValueError:
        got = None
    behaviour = got == expected
    tests = se.run_script([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], ws, timeout=60)
    checks = [se.check("no_old_name", not leftovers, ", ".join(leftovers) or "none"),
              se.check("behaviour_unchanged", behaviour, run["stderr"][-300:]),
              se.check("visible_tests_pass", tests["returncode"] == 0, tests["stdout"][-300:])]
    return {"correct_fraction": sum(c["passed"] for c in checks) / len(checks)}, checks, [], {}


LEAP_PROBE = r'''
import json, sys
sys.path.insert(0, ".")
from leap import is_leap_year
print(json.dumps({y: bool(is_leap_year(int(y))) for y in json.loads(sys.argv[1])}))
'''


def eval_leap(p, ws, hd):
    exp = se.load_json_file(hd / "expected.json")
    run = se.run_script([sys.executable, "-c", LEAP_PROBE, json.dumps(list(exp))], ws, timeout=30)
    try:
        got = json.loads(run["stdout"]) if run["returncode"] == 0 else {}
    except ValueError:
        got = {}
    right = sum(1 for k, v in exp.items() if got.get(k) == v)
    return ({"correct_fraction": right / len(exp)}, [se.check("imports", run["returncode"] == 0, run["stderr"][-300:])],
            [], {"wrong_years": [k for k, v in exp.items() if got.get(k) != v][:20]})


def eval_yaml_to_json(p, ws, hd):
    exp = se.load_json_file(hd / "expected.json")
    try:
        got = se.load_json_file(ws / "config.json")
    except (OSError, ValueError) as exc:
        return {"correct_fraction": 0.0}, [se.check("json_parses", False, exc)], [], {}
    keys = list(exp)
    right = sum(1 for k in keys if isinstance(got, dict) and got.get(k) == exp[k])
    return {"correct_fraction": right / len(keys)}, [se.check("json_parses", True), se.check("exact", got == exp)], [], {}


def eval_word_freq(p, ws, hd):
    exp = se.load_json_file(hd / "expected.json")
    try:
        got = se.load_json_file(ws / "freq.json")
    except (OSError, ValueError) as exc:
        return {"correct_fraction": 0.0}, [se.check("json_parses", False, exc)], [], {}
    got = [list(x) for x in got] if isinstance(got, list) else []
    right = sum(1 for a, b in zip(got, exp) if a == b)
    return {"correct_fraction": right / len(exp) if len(got) == len(exp) else right / max(len(exp), len(got))}, \
        [se.check("json_parses", True)], [], {}


EVALUATORS = {
    "fizzbuzz": eval_fizzbuzz, "arithmetic": eval_arithmetic, "typo_fix": eval_typo_fix, "csv_sort": eval_csv_sort,
    "unit_conversion": eval_unit_conversion, "rename": eval_rename, "leap_year": eval_leap,
    "yaml_to_json": eval_yaml_to_json, "word_freq": eval_word_freq,
}


def evaluate(task, ws, hd):
    p = task["params"]
    return EVALUATORS[p["kind"]](p, ws, hd)


if __name__ == "__main__":
    raise SystemExit(se.evaluate_cli(__file__, evaluate))
