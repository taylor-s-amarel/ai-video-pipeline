"""Shared helpers for Baltor showcase task packages (standard library only).

Every showcase task package ships this file next to ``task.json``,
``setup/make_fixtures.py`` and ``evaluate.py``. It implements the parts of the
pre-registered protocol that must behave identically for every task:

* the spec hash: SHA-256 of the canonical JSON of ``task.json`` with the keys
  ``spec_hash`` and ``preregistration`` removed (keys sorted, no whitespace,
  UTF-8). Every run record carries it.
* integrity: the evaluator refuses to call a run valid when ``task.json`` or any
  setup/evaluator file differs from what was pre-registered.
* trial seeds and arm order, derived from the spec hash so nobody can pick
  favourable fixtures after the fact.
* metric normalisation, the weighted composite score and the pass rule.
* the command-line contract shared by every setup script and evaluator.

Setup:    python3 setup/make_fixtures.py --workspace W --hidden H --seed N
Evaluate: python3 evaluate.py --workspace W --hidden H [--out result.json]

The workspace W is what the agent sees. The hidden directory H holds ground
truth and must never be readable by the agent. Neither may sit inside the task
package, and H may not sit inside W.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable

RESULT_SPEC = "baltor.showcase-evaluation/v1"
TASK_SPEC = "baltor.showcase-task/v1"
HASH_EXCLUDED_KEYS = ("spec_hash", "preregistration")


# --------------------------------------------------------------------------- hashing and seeds

def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_spec_hash(task: dict) -> str:
    body = {k: v for k, v in task.items() if k not in HASH_EXCLUDED_KEYS}
    return hashlib.sha256(canonical_json(body)).hexdigest()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derive_int(spec_hash: str, label: str, trial: int) -> int:
    return int(hashlib.sha256(f"{spec_hash}:{label}:{trial}".encode()).hexdigest()[:8], 16)


def fixture_seed(spec_hash: str, trial: int) -> int:
    """Seed for trial ``trial`` (1-based). Both arms of a trial get the same seed."""
    return derive_int(spec_hash, "fixture", trial)


def arm_order(spec_hash: str, trial: int) -> list[str]:
    """Which arm runs first in trial ``trial``: fixed by the spec hash, balanced in expectation."""
    first = derive_int(spec_hash, "order", trial) % 2
    return ["baseline", "treatment"] if first == 0 else ["treatment", "baseline"]


def run_plan(task: dict) -> list[dict]:
    """The full pre-registered run schedule for one task."""
    h = task.get("spec_hash") or compute_spec_hash(task)
    plan = []
    for t in range(1, int(task["trials"]["per_arm"]) + 1):
        for arm in arm_order(h, t):
            plan.append({"trial": t, "arm": arm, "fixture_seed": fixture_seed(h, t), "spec_hash": h})
    return plan


# --------------------------------------------------------------------------- task loading and integrity

def load_task(pkg_dir: str | Path) -> dict:
    return json.loads((Path(pkg_dir) / "task.json").read_text(encoding="utf-8"))


def integrity_problems(task: dict, pkg_dir: str | Path) -> list[str]:
    pkg = Path(pkg_dir)
    problems = []
    if task.get("spec_hash") and compute_spec_hash(task) != task["spec_hash"]:
        problems.append("task.json differs from the pre-registered spec (spec_hash mismatch)")
    for group in ("setup", "evaluator"):
        for f in task.get(group, {}).get("files", []):
            p = pkg / f["path"]
            if not p.exists():
                problems.append(f"{group} file {f['path']} is missing")
            elif sha256_file(p) != f["sha256"]:
                problems.append(f"{group} file {f['path']} changed since pre-registration")
    return problems


# --------------------------------------------------------------------------- workspace preparation

def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def prepare_dirs(pkg_dir: Path, workspace: str | Path, hidden: str | Path) -> tuple[Path, Path]:
    ws, hd = Path(workspace), Path(hidden)
    if _inside(ws, pkg_dir) or _inside(hd, pkg_dir):
        raise SystemExit("workspace and hidden directories must be outside the task package")
    if _inside(hd, ws):
        raise SystemExit("the hidden directory must not be inside the workspace")
    if ws.exists() and any(ws.iterdir()):
        raise SystemExit(f"workspace {ws} is not empty; every run starts from a fresh workspace")
    ws.mkdir(parents=True, exist_ok=True)
    hd.mkdir(parents=True, exist_ok=True)
    return ws, hd


def task_markdown(task: dict) -> str:
    out = [f"# {task['title']}", "", task["prompt"].strip(), "",
           "## Requirements", "", "These are exactly the things the evaluator checks.", ""]
    out += [f"- {r}" for r in task["requirements"]]
    out += ["", "## Deliverables", ""]
    out += [f"- `{d['path']}`: {d['description']}" for d in task["deliverables"]]
    if task.get("inputs", {}).get("workspace_files"):
        out += ["", "## Inputs in this workspace", ""]
        out += [f"- `{f}`" for f in task["inputs"]["workspace_files"]]
    b = task["budget"]
    out += ["", "## Budget", "",
            f"- wall time: {b['wall_time_s']} s",
            f"- tool calls: {b['tool_calls']}",
            f"- tokens (input + output): {b['tokens']}",
            "", "## Ground rules", "",
            "- Work only inside this workspace. Network access: "
            + ("none." if task["inputs"].get("network", "none") == "none" else task["inputs"]["network"] + "."),
            "- Do not look for the evaluator, hidden labels or answer keys, and do not try to rebuild them.",
            "- Leave every deliverable at the path named above. Anything else in the workspace is ignored.",
            ]
    out += [f"- {c}" for c in task.get("workspace_rules", [])]
    return "\n".join(out) + "\n"


def write_json(path: str | Path, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: str | Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or (list(rows[0].keys()) if rows else [])
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(path: str | Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def setup_cli(pkg_file: str, make: Callable[..., None], argv: list[str] | None = None,
              extra: Callable[[argparse.ArgumentParser], None] | None = None) -> int:
    """Command-line entry for ``setup/make_fixtures.py``. ``pkg_file`` is that script's ``__file__``."""
    pkg = Path(pkg_file).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Create the agent workspace and the hidden ground truth for one trial.")
    ap.add_argument("--workspace", required=True, help="fresh directory the agent will work in")
    ap.add_argument("--hidden", required=True, help="directory for ground truth; never shown to the agent")
    ap.add_argument("--seed", type=int, required=True, help="fixture seed for this trial (see showcase_eval.fixture_seed)")
    if extra:
        extra(ap)
    a = ap.parse_args(argv)
    task = load_task(pkg)
    ws, hd = prepare_dirs(pkg, a.workspace, a.hidden)
    make(task=task, workspace=ws, hidden=hd, seed=a.seed, args=a)
    (ws / "TASK.md").write_text(task_markdown(task), encoding="utf-8")
    write_json(hd / "fixture.json", {"task_id": task["task_id"], "spec_hash": task.get("spec_hash"),
                                     "seed": a.seed})
    print(f"workspace ready: {ws}\nhidden ground truth: {hd}")
    return 0


# --------------------------------------------------------------------------- scoring

def check(name: str, passed: bool, detail: Any = "") -> dict:
    return {"name": name, "passed": bool(passed), "detail": str(detail)[:500]}


def normalise(metric: dict, value: float | None) -> float:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return 0.0
    worst, best = metric["scale"]
    if best == worst:
        return 1.0 if value == best else 0.0
    return max(0.0, min(1.0, (value - worst) / (best - worst)))


def gate_passes(metric: dict, value: float | None) -> bool:
    if "threshold" not in metric:
        return True
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return False
    return value >= metric["threshold"] if metric["direction"] == "maximize" else value <= metric["threshold"]


def _clean(v: Any) -> Any:
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 6)
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def summarise(task: dict, pkg_dir: Path, metrics: dict, checks: list[dict], flags: list[str],
              details: dict, errors: list[str]) -> dict:
    metrics = dict(metrics)
    if checks and "checks_pass_rate" not in metrics:
        metrics["checks_pass_rate"] = sum(c["passed"] for c in checks) / len(checks)
    normalised, gates, total_w, score = {}, [], 0.0, 0.0
    for m in task["metrics"]:
        v = metrics.get(m["name"])
        n = normalise(m, v)
        normalised[m["name"]] = n
        total_w += m["weight"]
        score += m["weight"] * n
        if m.get("gate"):
            gates.append({"metric": m["name"], "op": ">=" if m["direction"] == "maximize" else "<=",
                          "threshold": m["threshold"], "value": v, "passed": gate_passes(m, v)})
    score = score / total_w if total_w else 0.0
    by_name = {c["name"]: c for c in checks}
    required = task["success"].get("required_checks", [])
    req = [{"check": r, "passed": bool(by_name.get(r, {}).get("passed"))} for r in required]
    problems = integrity_problems(task, pkg_dir)
    valid = not problems
    passed = (valid and not errors and all(g["passed"] for g in gates) and all(r["passed"] for r in req)
              and score >= task["success"].get("min_score", 0.0))
    return _clean({
        "spec": RESULT_SPEC,
        "task_id": task["task_id"],
        "spec_hash": task.get("spec_hash") or compute_spec_hash(task),
        "evaluator_sha256": sha256_file(pkg_dir / task["evaluator"]["entry"]),
        "valid": valid,
        "integrity_problems": problems,
        "passed": passed,
        "score": score,
        "metrics": metrics,
        "normalised": normalised,
        "gates": gates,
        "required_checks": req,
        "checks": checks,
        "flags": flags,
        "errors": errors,
        "details": details,
    })


def evaluate_cli(pkg_file: str, evaluate: Callable[..., tuple], argv: list[str] | None = None) -> int:
    """Command-line entry for ``evaluate.py``.

    ``evaluate(task, workspace, hidden)`` returns ``(metrics, checks, flags, details)``.
    An exception inside it is reported as an evaluation error and the run fails;
    the evaluator itself still exits 0 so the harness records the result.
    """
    pkg = Path(pkg_file).resolve().parent
    ap = argparse.ArgumentParser(description="Score one run of this showcase task. Prints JSON.")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--hidden", required=True)
    ap.add_argument("--out", help="also write the result JSON here")
    a = ap.parse_args(argv)
    task = load_task(pkg)
    ws, hd = Path(a.workspace), Path(a.hidden)
    metrics, checks, flags, details, errors = {}, [], [], {}, []
    t0 = time.monotonic()
    try:
        metrics, checks, flags, details = evaluate(task, ws, hd)
    except Exception as exc:  # noqa: BLE001 - every failure is reported, never hidden
        errors.append(f"{type(exc).__name__}: {exc}")
        details = {"traceback": traceback.format_exc()[-2000:]}
    result = summarise(task, pkg, metrics, checks, flags, details, errors)
    result["evaluation_seconds"] = round(time.monotonic() - t0, 3)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


# --------------------------------------------------------------------------- utilities for evaluators

def run_script(args: list[str], cwd: str | Path, timeout: float = 120, env: dict | None = None,
               stdin: str | None = None) -> dict:
    """Run agent-written code in a subprocess with a timeout. Never raises on failure."""
    full_env = dict(os.environ)
    full_env.update(env or {})
    full_env.setdefault("PYTHONHASHSEED", "0")
    t0 = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
                              env=full_env, input=stdin)
        return {"returncode": proc.returncode, "stdout": proc.stdout[-20000:], "stderr": proc.stderr[-20000:],
                "timed_out": False, "seconds": round(time.monotonic() - t0, 3)}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": None, "stdout": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
                "stderr": "timed out", "timed_out": True, "seconds": round(time.monotonic() - t0, 3)}
    except OSError as exc:
        return {"returncode": None, "stdout": "", "stderr": str(exc), "timed_out": False,
                "seconds": round(time.monotonic() - t0, 3)}


CODE_SUFFIXES = (".py", ".ipynb", ".sh", ".sql", ".r", ".js", ".ts")


def leakage_scan(workspace: str | Path, patterns: list[str], suffixes: tuple = CODE_SUFFIXES) -> list[str]:
    """Return ``path: pattern`` for every agent-written file that matches a forbidden pattern."""
    hits = []
    regs = [re.compile(p) for p in patterns]
    for p in sorted(Path(workspace).rglob("*")):
        if not p.is_file() or p.suffix.lower() not in suffixes or p.stat().st_size > 2_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for r in regs:
            if r.search(text):
                hits.append(f"{p.relative_to(workspace).as_posix()}: {r.pattern}")
    return hits


def load_json_file(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pairwise_prf(predicted: list[tuple], truth: list[tuple]) -> dict:
    """Precision/recall/F1 for two sets of hashable items."""
    p, t = set(predicted), set(truth)
    tp = len(p & t)
    precision = tp / len(p) if p else 0.0
    recall = tp / len(t) if t else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": len(p - t), "fn": len(t - p)}


if __name__ == "__main__":  # pragma: no cover - helper for operators
    task = load_task(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
    print(json.dumps({"spec_hash": compute_spec_hash(task), "plan": run_plan(task)}, indent=2))
