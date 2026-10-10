"""Shared helpers for Baltor showcase task packages (standard library only).

Every showcase task package ships this file next to ``task.json`` (the
pre-registered spec in the ``showcase_task_spec`` contract format),
``task_detail.json`` (requirements, parameters, metric scales, gates and the
hypothesis), ``setup/make_fixtures.py`` and ``evaluate.py``. It implements the
parts of the protocol that must behave the same way for every task:

* ``spec_sha256``: SHA-256 of the canonical JSON of ``task.json`` without the
  ``spec_sha256`` key (keys sorted, separators ``,`` and ``:``, UTF-8). Every
  file in the package except ``task.json`` itself is listed with its SHA-256 in
  ``task.json["files_sha256"]``, so the spec hash also covers ``task_detail.json``,
  the setup scripts and the evaluator. Every run record repeats the spec hash.
* integrity: a run is not valid when ``task.json`` or any listed file differs
  from what was pre-registered.
* per-trial fixture seeds and arm order derived from the spec hash, for runners
  that vary fixtures across trials (both arms of one trial always share a seed).
* metric normalisation, the weighted composite score and the pass rule.
* the command line shared by every setup script and evaluator:

      python3 setup/make_fixtures.py --workspace W --private P --seed N
      python3 evaluate.py --workspace W --private P [--out result.json]

  (``--hidden`` is accepted as a synonym of ``--private``.) W is what the agent
  sees; P holds ground truth and must never be readable by the agent. Neither
  may be inside the task package, and P may not be inside W.
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
DETAIL_SPEC = "baltor.showcase-task-detail/v1"
ARMS = ("baseline", "baltor")


# --------------------------------------------------------------------------- hashing and seeds

def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_spec_hash(task: dict) -> str:
    """spec_sha256 as defined by the showcase_task_spec contract."""
    return hashlib.sha256(canonical_json({k: v for k, v in task.items() if k != "spec_sha256"})).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def derive_int(spec_sha256: str, label: str, trial: int) -> int:
    return int(hashlib.sha256(f"{spec_sha256}:{label}:{trial}".encode()).hexdigest()[:8], 16)


def fixture_seed(spec_sha256: str, trial: int) -> int:
    """Seed for trial ``trial`` (1-based) when fixtures vary by trial. Both arms of a trial share it."""
    return derive_int(spec_sha256, "fixture", trial)


def arm_order(spec_sha256: str, trial: int) -> list[str]:
    """Which arm runs first in trial ``trial``; fixed by the spec hash, balanced in expectation."""
    return list(ARMS) if derive_int(spec_sha256, "order", trial) % 2 == 0 else list(reversed(ARMS))


def run_plan(task: dict) -> list[dict]:
    """The pre-registered run schedule for one task: trial, arm, fixture seed."""
    h = task.get("spec_sha256") or compute_spec_hash(task)
    plan = []
    for t in range(1, int(task["trials"]) + 1):
        for arm in arm_order(h, t):
            plan.append({"trial": t, "arm": arm, "fixture_seed": fixture_seed(h, t), "spec_sha256": h})
    return plan


# --------------------------------------------------------------------------- loading and integrity

def load_task(pkg_dir: str | Path) -> dict:
    return json.loads((Path(pkg_dir) / "task.json").read_text(encoding="utf-8"))


def load_detail(pkg_dir: str | Path) -> dict:
    return json.loads((Path(pkg_dir) / "task_detail.json").read_text(encoding="utf-8"))


def integrity_problems(task: dict, pkg_dir: str | Path) -> list[str]:
    pkg = Path(pkg_dir)
    problems = []
    if compute_spec_hash(task) != task.get("spec_sha256"):
        problems.append("task.json differs from the pre-registered spec (spec_sha256 mismatch)")
    for rel, digest in sorted(task.get("files_sha256", {}).items()):
        p = pkg / rel
        if not p.exists():
            problems.append(f"{rel} is missing")
        elif sha256_file(p) != digest:
            problems.append(f"{rel} changed since pre-registration")
    return problems


# --------------------------------------------------------------------------- workspace preparation

def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def prepare_dirs(pkg_dir: Path, workspace: str | Path, private: str | Path) -> tuple[Path, Path]:
    ws, pv = Path(workspace), Path(private)
    if _inside(ws, pkg_dir) or _inside(pv, pkg_dir):
        raise SystemExit("workspace and private directories must be outside the task package")
    if _inside(pv, ws):
        raise SystemExit("the private directory must not be inside the workspace")
    if ws.exists() and any(ws.iterdir()):
        raise SystemExit(f"workspace {ws} is not empty; every run starts from a fresh workspace")
    ws.mkdir(parents=True, exist_ok=True)
    pv.mkdir(parents=True, exist_ok=True)
    return ws, pv


def task_markdown(detail: dict) -> str:
    """TASK.md: the task text both arms receive (it is also the body of task.json's prompt)."""
    out = [f"# {detail['title']}", "", detail["prompt"].strip(), "",
           "## Requirements", "", "These are exactly the things that will be checked.", ""]
    out += [f"- {r}" for r in detail["requirements"]]
    out += ["", "## Deliverables", ""]
    out += [f"- `{d['path']}`: {d['description']}" for d in detail["deliverables"]]
    if detail.get("workspace_files"):
        out += ["", "## Inputs in this workspace", ""]
        out += [f"- `{f}`" for f in detail["workspace_files"]]
    b = detail["budget"]
    out += ["", "## Budget", "",
            f"- wall time: {b['wall_s']} s",
            f"- tool calls: {b['tool_calls']}",
            f"- tokens (input + output): {b['tokens']}",
            "", "## Ground rules", "",
            "- Work only inside this workspace. No network access.",
            "- Do not look for the evaluator, hidden labels or answer keys, and do not try to rebuild them.",
            "- Leave every deliverable at the path named above. Anything else in the workspace is ignored.",
            ]
    out += [f"- {c}" for c in detail.get("workspace_rules", [])]
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


def _add_dir_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--workspace", required=True, help="the agent's workspace")
    ap.add_argument("--private", "--hidden", dest="private", required=True,
                    help="ground-truth directory; never readable by the agent")


def setup_cli(pkg_file: str, make: Callable[..., None], argv: list[str] | None = None,
              extra: Callable[[argparse.ArgumentParser], None] | None = None) -> int:
    """Command-line entry for ``setup/make_fixtures.py``; ``pkg_file`` is that script's ``__file__``."""
    pkg = Path(pkg_file).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Create the agent workspace and the private ground truth for one run.")
    _add_dir_args(ap)
    ap.add_argument("--seed", type=int, required=True, help="fixture seed (both arms of a trial use the same one)")
    if extra:
        extra(ap)
    a = ap.parse_args(argv)
    detail = load_detail(pkg)
    ws, pv = prepare_dirs(pkg, a.workspace, a.private)
    make(task=detail, workspace=ws, hidden=pv, seed=a.seed, args=a)
    (ws / "TASK.md").write_text(task_markdown(detail), encoding="utf-8")
    task = load_task(pkg)
    write_json(pv / "fixture.json", {"task_id": task["id"], "spec_sha256": task.get("spec_sha256"), "seed": a.seed})
    print(f"workspace ready: {ws}\nprivate ground truth: {pv}")
    return 0


# --------------------------------------------------------------------------- scoring

def check(name: str, passed: bool, detail: Any = "") -> dict:
    return {"name": name, "passed": bool(passed), "detail": str(detail)[:500]}


def _bad(v: Any) -> bool:
    return v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))


def normalise(metric: dict, value: float | None) -> float:
    if _bad(value):
        return 0.0
    worst, best = metric["scale"]
    if best == worst:
        return 1.0 if value == best else 0.0
    return max(0.0, min(1.0, (float(value) - worst) / (best - worst)))


def gate_passes(metric: dict, value: float | None) -> bool:
    if "threshold" not in metric:
        return True
    if _bad(value):
        return False
    return value >= metric["threshold"] if metric["direction"] == "maximize" else value <= metric["threshold"]


def _clean(v: Any) -> Any:
    if isinstance(v, bool):
        return v
    if isinstance(v, float):
        return None if (math.isnan(v) or math.isinf(v)) else round(v, 6)
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def summarise(detail: dict, task: dict, pkg_dir: Path, metrics: dict, checks: list[dict], flags: list[str],
              details: dict, errors: list[str]) -> dict:
    metrics = {k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v) for k, v in metrics.items()}
    if "checks_pass_rate" not in metrics:
        metrics["checks_pass_rate"] = sum(c["passed"] for c in checks) / len(checks) if checks else 0.0
    normalised, gates, total_w, score = {}, [], 0.0, 0.0
    for m in detail["metrics"]:
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
    req = [{"check": r, "passed": bool(by_name.get(r, {}).get("passed"))}
           for r in detail["success"].get("required_checks", [])]
    problems = integrity_problems(task, pkg_dir)
    valid = not problems
    passed = (valid and not errors and all(g["passed"] for g in gates) and all(r["passed"] for r in req)
              and score >= detail["success"].get("min_score", 0.0))
    metrics["task_pass"] = 1.0 if passed else 0.0
    metrics["composite_score"] = score
    return _clean({
        "spec": RESULT_SPEC,
        "task_id": task["id"],
        "spec_sha256": task.get("spec_sha256"),
        "evaluator_sha256": sha256_file(pkg_dir / "evaluate.py"),
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

    ``evaluate(detail, workspace, private)`` returns ``(metrics, checks, flags, details)``.
    An exception inside it is reported as an evaluation error and the run fails; the
    evaluator still exits 0 so the harness records the result. Exit 2 only on bad usage.
    """
    pkg = Path(pkg_file).resolve().parent
    ap = argparse.ArgumentParser(description="Score one run of this showcase task. Prints JSON.")
    _add_dir_args(ap)
    ap.add_argument("--out", help="also write the result JSON here")
    a = ap.parse_args(argv)
    task, detail = load_task(pkg), load_detail(pkg)
    ws, pv = Path(a.workspace), Path(a.private)
    metrics, checks, flags, details, errors = {}, [], [], {}, []
    t0 = time.monotonic()
    try:
        metrics, checks, flags, details = evaluate(detail, ws, pv)
    except Exception as exc:  # noqa: BLE001 - every failure is reported, never hidden
        errors.append(f"{type(exc).__name__}: {exc}")
        details = {"traceback": traceback.format_exc()[-2000:]}
    result = summarise(detail, task, pkg, metrics, checks, flags, details, errors)
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
    full_env["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
                              env=full_env, input=stdin)
        return {"returncode": proc.returncode, "stdout": proc.stdout[-200000:], "stderr": proc.stderr[-20000:],
                "timed_out": False, "seconds": round(time.monotonic() - t0, 3)}
    except subprocess.TimeoutExpired:
        return {"returncode": None, "stdout": "", "stderr": "timed out", "timed_out": True,
                "seconds": round(time.monotonic() - t0, 3)}
    except OSError as exc:
        return {"returncode": None, "stdout": "", "stderr": str(exc), "timed_out": False,
                "seconds": round(time.monotonic() - t0, 3)}


CODE_SUFFIXES = (".py", ".ipynb", ".sh", ".sql", ".r", ".js", ".ts")


def leakage_scan(workspace: str | Path, patterns: list[str], suffixes: tuple = CODE_SUFFIXES) -> list[str]:
    """``path: pattern`` for every agent-written code file that matches a forbidden pattern."""
    hits = []
    regs = [re.compile(p) for p in patterns]
    for p in sorted(Path(workspace).rglob("*")):
        if not p.is_file() or p.suffix.lower() not in suffixes or p.stat().st_size > 2_000_000:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for r in regs:
            if r.search(text):
                hits.append(f"{p.relative_to(workspace).as_posix()}: {r.pattern}")
    return hits


def load_json_file(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def prf(predicted, truth) -> dict:
    """Precision, recall and F1 for two collections of hashable items."""
    p, t = set(predicted), set(truth)
    tp = len(p & t)
    precision = tp / len(p) if p else 0.0
    recall = tp / len(t) if t else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": len(p - t), "fn": len(t - p)}


if __name__ == "__main__":  # pragma: no cover - operator helper: python3 showcase_eval.py [PACKAGE_DIR]
    pkg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    t = load_task(pkg)
    print(json.dumps({"task_id": t["id"], "spec_sha256": compute_spec_hash(t),
                      "integrity_problems": integrity_problems(t, pkg), "plan": run_plan(t)}, indent=2))
