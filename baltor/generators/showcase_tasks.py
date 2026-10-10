#!/usr/bin/env python3
"""Pre-registered showcase task library: same task with and without Baltor.

Each task becomes one ``skill`` package (subkind ``evaluator``) named
``showcase_task_<slug>`` that ships:

* ``task.json``           the pre-registered spec (prompt, inputs, budget, metrics, pass
                          rule, trials, arms, analysis, setup/evaluator file hashes) and
                          its ``spec_hash``
* ``setup/``              deterministic fixture scripts (synthetic data, bundled
                          scikit-learn datasets, or a local split of the user's own
                          Kaggle download; never copies of third-party data)
* ``evaluate.py``         deterministic evaluator that prints JSON metrics
* ``showcase_eval.py``    shared protocol code (hashing, seeds, scoring, CLI)
* ``test_<identity>.py``  proves the evaluator passes a known-good output and fails a
                          known-bad one
* ``SKILL.md``            what the task tests, why Baltor might or might not help, how to run it

It also writes the ``showcase_preregistration_ledger`` rules package: every task
id, its spec hash and the date that hash was first registered. The ledger history
lives in ``data/showcase_tasks/ledger.json`` and is append-only: a changed spec
gets a new revision with the date it changed; a removed task is marked withdrawn.

Data layout (``data/showcase_tasks/``):

* ``common/showcase_eval.py``      copied into every package
* ``families/<family>/``           evaluator, setup scripts and ``test_template.py`` shared by a family
* ``tasks/<group>.yaml``           task definitions (``defaults`` merged into each of ``tasks``)
* ``schemas/``                     task spec and evaluation result JSON Schemas
* ``tests/``                       library-level pytest suite

Run: ``cd baltor/generators && python3 showcase_tasks.py``
Set ``SHOWCASE_PREREG_DATE=YYYY-MM-DD`` to pin the date written for new or changed specs.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import os
import sys
from pathlib import Path

import yaml

from _lib import COMPONENTS_DIR, GeneratorRun, dumps, effects, skill_md

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "showcase_tasks"
FAMILIES = DATA / "families"
TASKS = DATA / "tasks"
SCHEMAS = DATA / "schemas"
LEDGER = DATA / "ledger.json"
DATA_REL = "generators/data/showcase_tasks"
LEDGER_IDENTITY = "showcase_preregistration_ledger"

sys.path.insert(0, str(DATA / "common"))
import showcase_eval as se  # noqa: E402

HASH_METHOD = ("sha256 of the canonical JSON of task.json without the keys spec_hash and preregistration "
               "(keys sorted, separators ',' ':', UTF-8, ensure_ascii false); see showcase_eval.compute_spec_hash")

BUDGETS = {
    "xs": {"wall_time_s": 600, "tool_calls": 30, "tokens": 120_000},
    "s": {"wall_time_s": 1200, "tool_calls": 60, "tokens": 300_000},
    "m": {"wall_time_s": 2400, "tool_calls": 120, "tokens": 700_000},
    "l": {"wall_time_s": 3600, "tool_calls": 200, "tokens": 1_200_000},
    "xl": {"wall_time_s": 5400, "tool_calls": 300, "tokens": 2_000_000},
}

BASE_PREAMBLE = ("You are working in a fresh workspace. Read TASK.md first. Before you finish, check your "
                 "deliverables against every requirement in TASK.md.")
CATALOGUE_SENTENCE = ("You can also search the Baltor component catalogue (intelligence_search, or "
                      "`python3 baltor_catalog.py search`) and download items (provisioning_read, or "
                      "`baltor_catalog.py read/place`) if you think something there would help. Using it is optional.")

ARMS = {
    "baseline": {
        "description": "Harness and model alone.",
        "catalogue_access": "none",
        "preamble": BASE_PREAMBLE,
        "preplaced": [],
    },
    "treatment": {
        "description": "The same harness and model plus access to the Baltor catalogue. Nothing is pre-placed: the agent decides whether to search, what to read and what to place.",
        "catalogue_access": "search-read-place",
        "tools": ["intelligence_search", "provisioning_read", "baltor_catalog.py search", "baltor_catalog.py read",
                  "baltor_catalog.py place"],
        "preamble": BASE_PREAMBLE + " " + CATALOGUE_SENTENCE,
        "preplaced": [],
        "catalogue_exclusions": {
            "identity_prefixes": ["showcase_task_", LEDGER_IDENTITY],
            "tags": ["showcase-task"],
            "reason": "The task packages contain evaluators, reference outputs and fixture generators; an agent that reads them is not solving the task.",
        },
        "catalogue_release": "recorded per run (catalog/release.json 'release'); one release for the whole study",
    },
    "held_constant": ["model and sampling settings", "harness and harness version", "budget", "starting workspace (same fixture seed per trial)",
                      "network policy", "machine type", "prompt text apart from the one catalogue sentence",
                      "evaluator version (spec hash)"],
    "contamination_rule": "A treatment run whose transcript or step lock shows it read an excluded identity is marked contaminated and counted as a failure for the treatment arm.",
}

TRIALS_ORDER = ("paired: in trial k both arms start from the same fixture seed; which arm runs first is "
                "showcase_eval.arm_order(spec_hash, k); arms never share a workspace")
TRIALS_SEED = "showcase_eval.fixture_seed(spec_hash, k) = int(sha256(f'{spec_hash}:fixture:{k}')[:8], 16)"

ANALYSIS = {
    "unit": "paired trial (one baseline run and one treatment run with the same fixture seed)",
    "primary_outcome": "passed (boolean) as printed by evaluate.py",
    "primary_effect": "treatment pass rate minus baseline pass rate, with a 95% percentile bootstrap interval over paired trials (10,000 resamples, resampling seed derived from the spec hash)",
    "secondary": [
        "mean composite score difference (treatment minus baseline) with a 95% bootstrap interval",
        "win rate: share of paired trials where the treatment score is higher (ties count one half)",
        "cost per run and per passing run: input and output tokens, wall time, tool calls, estimated USD",
        "blind pairwise preference where judging.pairwise is set (secondary evidence only)",
    ],
    "report_all_runs": True,
    "missing_or_failed_runs": "A run that crashes, times out, exceeds its budget or is contaminated counts as not passed with score 0 for its arm. Nothing is dropped or re-run selectively; a whole trial may be re-run only for an infrastructure fault, and the fault is reported.",
    "pooling": "Negative controls are analysed and reported separately. A pooled effect across tasks weights each task equally and is reported alongside every per-task result.",
}

COST_METRICS = ["input_tokens", "output_tokens", "cached_input_tokens", "wall_time_s", "tool_calls",
                "catalogue_calls", "usd_estimate"]

DISCLOSURES = [
    "Conflict of interest: the tasks, evaluators and the Baltor catalogue components were written by the same team. Treat results as the team's own evaluation, not an independent study; independent replication is invited and every input needed to replicate is in this package.",
    "Deterministic evaluator results are the primary evidence. Blind pairwise and LLM-judge preferences, where collected, are weaker evidence and are reported separately.",
    "The task library and this ledger are excluded from the treatment arm's catalogue view so neither arm can read evaluators or reference outputs.",
]

COMMON_TEST_HEADER = '''"""Self-test for this showcase task's evaluator.

Proves that evaluate.py passes a known-good output and fails a known-bad one,
using fixtures made by setup/make_fixtures.py. Run: python3 -m pytest -q <package dir>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parent
TASK = json.loads((PKG / "task.json").read_text(encoding="utf-8"))
PARAMS = TASK["params"]
sys.path.insert(0, str(PKG))


def run_setup(tmp_path: Path, seed: int = 20261010, extra: list | None = None) -> tuple[Path, Path]:
    ws, hd = tmp_path / "workspace", tmp_path / "hidden"
    proc = subprocess.run([sys.executable, str(PKG / "setup" / "make_fixtures.py"), "--workspace", str(ws),
                           "--hidden", str(hd), "--seed", str(seed)] + (extra or []),
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert (ws / "TASK.md").exists()
    return ws, hd


def evaluate(ws: Path, hd: Path) -> dict:
    proc = subprocess.run([sys.executable, str(PKG / "evaluate.py"), "--workspace", str(ws), "--hidden", str(hd)],
                          capture_output=True, text=True, timeout=TASK["evaluator"]["timeout_s"] + 60)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["task_id"] == TASK["task_id"]
    assert result["valid"], result["integrity_problems"]
    return result


def assert_good(result: dict) -> None:
    assert not result["errors"], result["errors"]
    assert result["passed"], json.dumps({k: result[k] for k in ("gates", "required_checks", "metrics", "checks")}, indent=1)[:4000]


def assert_bad(result: dict, good: dict | None = None) -> None:
    assert not result["passed"]
    if good is not None:
        assert result["score"] < good["score"]


def test_spec_hash_matches():
    import showcase_eval as se
    assert se.compute_spec_hash(TASK) == TASK["spec_hash"]
    assert se.integrity_problems(TASK, PKG) == []


def test_empty_workspace_fails(tmp_path):
    ws, hd = run_setup(tmp_path)
    for d in TASK["deliverables"]:
        p = ws / d["path"]
        if p.is_file():
            p.unlink()
    result = evaluate(ws, hd)
    assert not result["passed"]

'''


# --------------------------------------------------------------------------- loading definitions

def load_task_defs() -> list[dict]:
    defs = []
    for path in sorted(TASKS.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        defaults = doc.get("defaults", {})
        for t in doc.get("tasks", []):
            merged = copy.deepcopy(defaults)
            for k, v in t.items():
                if k == "params" and isinstance(v, dict):
                    merged.setdefault("params", {}).update(copy.deepcopy(v))
                else:
                    merged[k] = copy.deepcopy(v)
            merged["_source"] = path.name
            defs.append(merged)
    slugs = [d["slug"] for d in defs]
    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    if dupes:
        raise SystemExit(f"duplicate task slugs: {dupes}")
    return defs


def snake(slug: str) -> str:
    return slug.replace("-", "_")


def identity_for(slug: str) -> str:
    return "showcase_task_" + snake(slug)


def _read_tree(root: Path) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if not p.is_file() or "__pycache__" in rel.parts or ".pytest_cache" in rel.parts or p.suffix == ".pyc":
            continue
        out[rel.as_posix()] = p.read_text(encoding="utf-8")
    return out


def family_files(family: str) -> tuple[dict[str, str], str]:
    root = FAMILIES / family
    if not root.is_dir():
        raise SystemExit(f"unknown family {family}")
    files = _read_tree(root)
    test = files.pop("test_template.py", "")
    files.pop("README.md", None)
    return files, test


def assemble_files(defn: dict) -> dict[str, str]:
    files, test_body = family_files(defn["family"])
    files["showcase_eval.py"] = (DATA / "common" / "showcase_eval.py").read_text(encoding="utf-8")
    if "evaluate.py" not in files or "setup/make_fixtures.py" not in files:
        raise SystemExit(f"family {defn['family']} must provide evaluate.py and setup/make_fixtures.py")
    files[f"test_{identity_for(defn['slug'])}.py"] = COMMON_TEST_HEADER + "\n" + test_body.lstrip()
    return files


def _hashes(files: dict[str, str], paths: list[str]) -> list[dict]:
    import hashlib
    out = []
    for p in sorted(paths):
        text = files[p]
        data = (text if text.endswith("\n") else text + "\n").encode("utf-8")  # as GeneratorRun writes it
        out.append({"path": p, "sha256": hashlib.sha256(data).hexdigest()})
    return out


# --------------------------------------------------------------------------- task spec

def build_task_spec(defn: dict, files: dict[str, str]) -> dict:
    """task.json without spec_hash and preregistration."""
    budget_preset = defn.get("budget", "m")
    budget = {"preset": budget_preset, **BUDGETS[budget_preset]} if isinstance(budget_preset, str) else dict(budget_preset)
    setup_paths = [p for p in files if p.startswith("setup/") and p.endswith(".py")]
    eval_paths = [p for p in files if not p.startswith("setup/") and p.endswith(".py") and not p.startswith("test_")]
    setup_cmd = "python3 setup/make_fixtures.py --workspace {workspace} --hidden {hidden} --seed {fixture_seed}"
    if defn.get("setup_extra_args"):
        setup_cmd += " " + defn["setup_extra_args"]
    metrics = []
    for m in defn["metrics"]:
        mm = {"name": m["name"], "description": m["description"], "direction": m.get("direction", "maximize"),
              "weight": float(m.get("weight", 1.0)), "scale": [float(x) for x in m.get("scale", [0, 1])],
              "gate": bool(m.get("gate", "threshold" in m))}
        if "threshold" in m:
            mm["threshold"] = float(m["threshold"])
        metrics.append(mm)
    rule_parts = [f"{m['name']} {'>=' if m['direction'] == 'maximize' else '<='} {m['threshold']:g}"
                  for m in metrics if m["gate"]]
    success = defn.get("success", {})
    req_checks = list(success.get("required_checks", []))
    rule_parts += [f"check '{c}' passes" for c in req_checks]
    min_score = float(success.get("min_score", 0.0))
    if min_score:
        rule_parts.append(f"composite score >= {min_score:g}")
    judging_pairwise = defn.get("pairwise")
    if judging_pairwise:
        judging_pairwise = {"blind": True, "order": "randomised", "criteria": list(judging_pairwise["criteria"]),
                            "judges": list(judging_pairwise.get("judges", ["human", "llm"])),
                            "evidence_weight": "secondary"}
    task = {
        "spec": se.TASK_SPEC,
        "task_id": identity_for(defn["slug"]),
        "slug": defn["slug"],
        "title": defn["title"],
        "version": defn.get("version", "1.0.0"),
        "domain": defn["domain"],
        "category": defn["category"],
        "negative_control": bool(defn.get("negative_control", False)),
        "summary": defn["summary"],
        "prompt": defn["prompt"].strip(),
        "requirements": list(defn["requirements"]),
        "workspace_rules": list(defn.get("workspace_rules", [])),
        "deliverables": list(defn["deliverables"]),
        "inputs": {
            "workspace_files": list(defn.get("workspace_files", [])),
            "hidden_files": list(defn.get("hidden_files", [])),
            "network": defn.get("network", "none"),
            "data_sources": list(defn["data_sources"]),
        },
        "setup": {"entry": "setup/make_fixtures.py", "files": _hashes(files, setup_paths), "command": setup_cmd},
        "evaluator": {
            "entry": "evaluate.py",
            "files": _hashes(files, eval_paths),
            "command": "python3 evaluate.py --workspace {workspace} --hidden {hidden} --out {run_dir}/evaluation.json",
            "deterministic": bool(defn.get("deterministic", True)),
            "runs_agent_code": bool(defn.get("runs_agent_code", False)),
            "external_tools": list(defn.get("external_tools", [])),
            "timeout_s": int(defn.get("evaluator_timeout_s", 300)),
        },
        "metrics": metrics,
        "success": {"rule": "pass when " + (" and ".join(rule_parts) if rule_parts else "the evaluator reports no errors"),
                    "min_score": min_score, "required_checks": req_checks},
        "budget": budget,
        "arms": copy.deepcopy(ARMS),
        "trials": {"per_arm": int(defn.get("trials", 5)), "minimum_per_arm": 3, "order": TRIALS_ORDER,
                   "fixture_seed": TRIALS_SEED},
        "analysis": copy.deepcopy(ANALYSIS),
        "hypothesis": {"expected_effect": defn["hypothesis"]["expected_effect"],
                       "rationale": defn["hypothesis"]["rationale"].strip()},
        "judging": {"primary": "deterministic-evaluator", "pairwise": judging_pairwise},
        "expected_components": list(defn.get("expected_components", [])),
        "expected_capabilities": list(defn.get("expected_capabilities", [])),
        "cost_metrics": list(COST_METRICS),
        "requires_kaggle_account": bool(defn.get("requires_kaggle_account", False)),
        "cautions": list(defn.get("cautions", [])),
        "disclosures": list(DISCLOSURES),
        "params": copy.deepcopy(defn.get("params", {})),
    }
    if defn.get("competition"):
        task["competition"] = dict(defn["competition"])
    order = ["spec", "task_id", "slug", "title", "version", "domain", "category", "negative_control", "summary",
             "prompt", "requirements", "workspace_rules", "deliverables", "inputs", "setup", "evaluator", "metrics",
             "success", "budget", "arms", "trials", "analysis", "hypothesis", "judging", "expected_components",
             "expected_capabilities", "cost_metrics", "requires_kaggle_account", "competition", "cautions",
             "disclosures", "params"]
    return {k: task[k] for k in order if k in task}


# --------------------------------------------------------------------------- ledger

def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"spec": "baltor.showcase-ledger/v1", "hash_method": HASH_METHOD, "tasks": {}}


def update_ledger(ledger: dict, current: dict[str, str], today: str) -> dict:
    """Append-only: same hash keeps its date, a new hash adds a revision, a missing task is withdrawn."""
    ledger = copy.deepcopy(ledger)
    tasks = ledger.setdefault("tasks", {})
    for task_id, h in sorted(current.items()):
        hist = tasks.setdefault(task_id, [])
        if hist and hist[-1]["spec_hash"] == h and hist[-1]["status"] == "registered":
            continue
        for old in hist:
            if old["status"] == "registered":
                old["status"] = "superseded"
                old["superseded_on"] = today
        hist.append({"revision": len(hist) + 1, "spec_hash": h, "preregistered": today, "status": "registered"})
    for task_id, hist in tasks.items():
        if task_id not in current and hist and hist[-1]["status"] == "registered":
            hist[-1]["status"] = "withdrawn"
            hist[-1]["withdrawn_on"] = today
    ledger["tasks"] = dict(sorted(tasks.items()))
    return ledger


def current_entry(ledger: dict, task_id: str) -> dict:
    return ledger["tasks"][task_id][-1]


# --------------------------------------------------------------------------- SKILL.md

def _fmt_metric(m: dict) -> str:
    gate = f"{'>=' if m['direction'] == 'maximize' else '<='} {m['threshold']:g}" if m["gate"] else "-"
    return f"| `{m['name']}` | {m['description']} | {m['direction']} | {m['weight']:g} | {m['scale'][0]:g} → {m['scale'][1]:g} | {gate} |"


def skill_body(task: dict, defn: dict) -> str:
    b = task["budget"]
    pre = task["preregistration"]
    control = " · **negative control**" if task["negative_control"] else ""
    kaggle = ""
    if task["requires_kaggle_account"]:
        c = task["competition"]
        kaggle = f"""
## Kaggle data (your own account)

This task uses a real competition: <{c['url']}>. It needs your own Kaggle account and
you must accept the competition rules at <{c['rules_url']}> before downloading. Nothing from
the competition is stored in this package or this repository; the setup script makes a local,
seeded validation split of the files you downloaded, and the evaluator scores that split
with the competition metric ({c['metric']}). Local scores are not leaderboard scores.

```
{c.get('download', 'kaggle competitions download -c ' + c['slug'])}
unzip {c['slug']}.zip -d ~/kaggle/{c['slug']}
python3 setup/make_fixtures.py --workspace RUN/workspace --hidden RUN/hidden --seed SEED --source ~/kaggle/{c['slug']}
```
"""
    pairwise = ""
    if task["judging"]["pairwise"]:
        pw = task["judging"]["pairwise"]
        pairwise = ("\n## Blind pairwise judging (secondary)\n\nAfter deterministic scoring, outputs from the two arms of each trial "
                    "are shown side by side with arm labels removed and left/right order randomised. Criteria: "
                    + "; ".join(pw["criteria"]) + ". Judges: " + ", ".join(pw["judges"])
                    + ". Report these preferences separately; they never change the pass/fail result.\n")
    metrics = "\n".join(_fmt_metric(m) for m in task["metrics"])
    sources = "\n".join(f"- {s['name']} ({s['kind']}, {s['licence']}{', ' + s['url'] if s.get('url') else ''})"
                        f"{': ' + s['notes'] if s.get('notes') else ''}" for s in task["inputs"]["data_sources"])
    cautions = "\n".join(f"- {c}" for c in task["cautions"]) or "- none beyond the general rules"
    expected = ", ".join(f"`{c}`" for c in task["expected_components"]) or "none on disk yet"
    caps = "; ".join(task["expected_capabilities"]) or "-"
    deliverables = "\n".join(f"- `{d['path']}`: {d['description']}" for d in task["deliverables"])
    tools = ", ".join(task["evaluator"]["external_tools"]) or "none (Python only)"
    return f"""
# Showcase task: {task['title']}

{task['summary']}

Pre-registered {pre['date']} (revision {pre['revision']}) · spec hash `{task['spec_hash'][:16]}…` ·
{task['trials']['per_arm']} trials per arm · domain `{task['domain']}`{control}

## What this task tests

{defn['tests'].strip()}

Deliverables:

{deliverables}

## Why Baltor might help, or not

Expected effect (pre-registered): **{task['hypothesis']['expected_effect']}**. {task['hypothesis']['rationale']}

Components the authors expect could matter (post-hoc analysis only; nothing is pre-placed): {expected}.
Capabilities: {caps}.

## Fair comparison

- Baseline arm: harness and model alone. Treatment arm: the same harness and model plus access to the
  Baltor catalogue (search, read, place). Nothing is pre-placed; the agent decides what to look for.
- Held constant: model and settings, harness version, budget ({b['wall_time_s']} s wall time,
  {b['tool_calls']} tool calls, {b['tokens']:,} tokens), starting workspace (same fixture seed in both arms
  of a trial), network policy and machine. The prompts differ by one sentence that tells the treatment arm
  the catalogue exists.
- {task['trials']['per_arm']} paired trials; which arm runs first in each trial comes from the spec hash.
- Every run is reported, including crashes, timeouts and losses, with tokens, wall time and tool calls.
- This package and the ledger are excluded from the treatment arm's catalogue view; a run that reads them
  is marked contaminated and counts as a failure.

## Run it end to end

```
python3 showcase_eval.py .            # spec hash and the full run plan (trial, arm order, fixture seed)
python3 setup/make_fixtures.py --workspace RUN/workspace --hidden RUN/hidden --seed SEED
# start the agent in RUN/workspace with the arm's preamble (task.json arms.*.preamble) + task.json prompt
python3 evaluate.py --workspace RUN/workspace --hidden RUN/hidden --out RUN/evaluation.json
```

Keep `RUN/hidden` unreadable to the agent (different user, or mount it only after the agent exits).
Self-test of the evaluator: `python3 -m pytest -q .` (external tools needed: {tools}).
{kaggle}
## Metrics and pass rule

| Metric | Meaning | Direction | Weight | Scale (worst → best) | Gate |
|---|---|---|---:|---|---|
{metrics}

{task['success']['rule']}. The composite score is the weighted mean of the normalised metrics.
{pairwise}
## Data and licences

{sources}

## Cautions

{cautions}

## Disclosures

""" + "\n".join(f"- {d}" for d in task["disclosures"]) + "\n"


def skill_description(task: dict) -> str:
    d = (f"Pre-registered Baltor showcase task ({task['domain']}): {task['summary']} Use when running or "
         "reproducing a with-versus-without-Baltor comparison; creates seeded fixtures and scores a run "
         "with a deterministic evaluator that prints JSON.")
    return d[:1024]


# --------------------------------------------------------------------------- ledger package

def ledger_package(tasks: list[dict], ledger: dict) -> dict[str, str]:
    rows = []
    for t in sorted(tasks, key=lambda t: t["task_id"]):
        e = current_entry(ledger, t["task_id"])
        rows.append({"task_id": t["task_id"], "domain": t["domain"], "negative_control": t["negative_control"],
                     "spec_hash": e["spec_hash"], "preregistered": e["preregistered"], "revision": e["revision"],
                     "trials_per_arm": t["trials"]["per_arm"]})
    withdrawn = [{"task_id": k, **v[-1]} for k, v in ledger["tasks"].items() if v and v[-1]["status"] == "withdrawn"]
    rules = {
        "spec": "baltor.showcase-ledger/v1",
        "hash_method": HASH_METHOD,
        "task_count": len(rows),
        "negative_controls": sum(r["negative_control"] for r in rows),
        "tasks": rows,
        "withdrawn": withdrawn,
        "protocol": {
            "arms": ARMS,
            "trials": {"minimum_per_arm": 3, "order": TRIALS_ORDER, "fixture_seed": TRIALS_SEED},
            "analysis": ANALYSIS,
            "cost_metrics": COST_METRICS,
            "disclosures": DISCLOSURES,
            "data_rules": [
                "Never copy a third-party dataset into the repository or a package.",
                "Kaggle competitions are referenced by URL; each user downloads with their own account after accepting the rules.",
                "Offline tasks use datasets bundled with scikit-learn or synthetic data generated from the fixture seed.",
            ],
        },
    }
    by_domain: dict[str, int] = {}
    for r in rows:
        by_domain[r["domain"]] = by_domain.get(r["domain"], 0) + 1
    table = "\n".join(f"| `{r['task_id']}` | {r['domain']}{' (control)' if r['negative_control'] else ''} | "
                      f"`{r['spec_hash']}` | {r['preregistered']} | {r['revision']} | {r['trials_per_arm']} |" for r in rows)
    domains = ", ".join(f"{k} {v}" for k, v in sorted(by_domain.items()))
    md = f"""
# Showcase pre-registration ledger

Every Baltor showcase task, the SHA-256 of its pre-registered spec and the date that spec was
registered. A run record is admissible only if the `spec_hash` its evaluator printed equals the
hash listed here for that task. {len(rows)} tasks ({domains}); {rules['negative_controls']} negative controls.

## Rules

1. **Pre-register before any run.** Prompt, inputs, budget, metrics, evaluator and setup file hashes,
   trial count and pass rule live in `task.json` and are covered by its spec hash. Commit and publish this
   ledger before the first run; the public commit is the timestamp.
2. **Same everything except the catalogue.** Same model and settings, harness version, budget (time, tool
   calls, tokens), starting workspace and fixture seed in both arms. The treatment prompt adds one sentence
   saying the catalogue exists; nothing is pre-placed.
3. **At least 3 paired trials per arm (5 where affordable).** Arm order per trial and fixture seeds come
   from the spec hash (`showcase_eval.run_plan`), so nobody chooses them after seeing results.
4. **Deterministic local evaluators first.** Subjective outputs may add blind pairwise judging (labels hidden,
   order randomised); those results are secondary evidence and reported separately. LLM-judge results are
   weaker evidence than deterministic tests.
5. **Report every run**, including failures, timeouts, contaminated runs and losses. No best-of-N.
6. **Effect sizes with uncertainty.** Pass-rate and score differences with 95% bootstrap intervals over paired
   trials, and win rates. Never a single best run.
7. **Negative controls** (tasks where Baltor should not help) are run and reported with the same protocol to
   detect placebo effects and measure search overhead.
8. **Cost next to quality**: tokens, wall time, tool calls and catalogue calls for every run.
9. **No leakage.** Showcase task packages and this ledger are excluded from the treatment arm's catalogue;
   hidden ground truth stays outside the workspace; reading an excluded item marks a run contaminated.
10. **Amendments are visible.** Changing a spec creates a new revision with a new hash and date; runs recorded
    under an older hash are reported under that revision, never mixed. Withdrawn tasks stay listed.
11. **Disclose the conflict of interest**: the same team wrote the tasks, evaluators and components.
12. **Data licences.** No third-party dataset is copied into the repository. Kaggle tasks need the user's own
    account and rule acceptance; offline tasks use scikit-learn's bundled datasets or seeded synthetic data.

Verify a placed or downloaded task package against this ledger:
`python3 verify_ledger.py path/to/showcase-task-*/` (recomputes each spec hash and checks every
setup and evaluator file hash).

## Ledger

Hash method: {HASH_METHOD}.

| Task id | Domain | Spec hash | Pre-registered | Revision | Trials/arm |
|---|---|---|---|---:|---:|
{table}
"""
    verify = r'''#!/usr/bin/env python3
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
'''
    return {
        "RULES.md": md,
        "rules.json": dumps(rules),
        "ledger.json": dumps(ledger),
        "verify_ledger.py": verify,
        "schemas/showcase_task.schema.json": (SCHEMAS / "showcase_task.schema.json").read_text(encoding="utf-8"),
        "schemas/showcase_evaluation.schema.json": (SCHEMAS / "showcase_evaluation.schema.json").read_text(encoding="utf-8"),
    }


# --------------------------------------------------------------------------- main

def known_identities() -> set[str]:
    ids = set()
    for m in COMPONENTS_DIR.rglob("baltor.json"):
        try:
            ids.add(json.loads(m.read_text())["identity"])
        except Exception:  # noqa: BLE001
            pass
    for mod_dir in (HERE / "data").glob("*/modules/*"):
        if mod_dir.is_dir():
            ids.add(mod_dir.name)
    return ids


def build_all(today: str | None = None) -> tuple[list[tuple[dict, dict, dict[str, str]]], dict]:
    """Return [(defn, task, files)] and the updated ledger, without writing anything."""
    today = today or os.environ.get("SHOWCASE_PREREG_DATE") or dt.date.today().isoformat()
    built = []
    for defn in load_task_defs():
        files = assemble_files(defn)
        task = build_task_spec(defn, files)
        built.append((defn, task, files))
    ledger = update_ledger(load_ledger(), {t["task_id"]: se.compute_spec_hash(t) for _, t, _ in built}, today)
    for _, task, _ in built:
        e = current_entry(ledger, task["task_id"])
        task["spec_hash"] = se.compute_spec_hash(task)
        assert task["spec_hash"] == e["spec_hash"]
        task["preregistration"] = {"date": e["preregistered"], "revision": e["revision"],
                                   "ledger": LEDGER_IDENTITY, "hash_method": HASH_METHOD}
    return built, ledger


def main() -> None:
    built, ledger = build_all()
    known = known_identities()
    for defn, task, _ in built:
        for ident in task["expected_components"]:
            if ident not in known:
                print(f"warning: {task['task_id']} expects unknown component '{ident}'", file=sys.stderr)
    LEDGER.write_text(dumps(ledger), encoding="utf-8")
    with GeneratorRun(__file__, data=DATA_REL) as run:
        for defn, task, files in built:
            side = ["setup writes a fresh workspace and a hidden ground-truth directory"]
            if task["evaluator"]["runs_agent_code"]:
                side.append("evaluate.py runs agent-written code in a subprocess with a timeout")
            for tool in task["evaluator"]["external_tools"]:
                side.append(f"runs {tool}")
            payload = dict(files)
            payload["task.json"] = dumps(task)
            payload["SKILL.md"] = skill_md(f"showcase-task-{task['slug']}", skill_description(task),
                                           skill_body(task, defn))
            tags = ["showcase", "showcase-task", "preregistered", "evaluator", task["domain"], task["category"]]
            if task["negative_control"] and "negative-control" not in tags:
                tags.append("negative-control")
            if task["requires_kaggle_account"]:
                tags.append("kaggle")
            for t in defn.get("tags", []):
                if t not in tags and len(tags) < 24:
                    tags.append(t)
            run.component(
                "skill", task["task_id"],
                title=f"Showcase task: {task['title']}"[:120],
                summary=task["summary"],
                description=(f"Pre-registered {task['preregistration']['date']}, spec hash {task['spec_hash']}. "
                             f"{task['trials']['per_arm']} paired trials per arm. "
                             + task["hypothesis"]["rationale"])[:4000],
                subkind="evaluator", domain=task["domain"],
                files=payload,
                tags=tags,
                step_kinds=["verify", "measure", "test"],
                effects_=effects(filesystem="write", executes="python", side_effects=side),
                depends_on=[{"identity": d, "external": True} for d in defn.get("depends_on", [])] or None,
                parameters={"family": defn["family"], "spec_hash": task["spec_hash"], "source": defn["_source"]},
                examples=[f"Set up trial 1 of {task['task_id']} and score the agent's workspace",
                          "Print the run plan for this task: python3 showcase_eval.py ."],
                review={"status": "automated-passed", "checked": task["preregistration"]["date"],
                        "notes": "Evaluator self-test proves a known-good output passes and a known-bad output fails."},
            )
        tasks = [t for _, t, _ in built]
        run.component(
            "rules", LEDGER_IDENTITY,
            title="Showcase pre-registration ledger",
            summary=f"Fairness rules for with/without-Baltor showcases and the ledger of all {len(tasks)} pre-registered tasks: id, spec hash, registration date, revision.",
            subkind="rule-set", domain="baltor",
            files=ledger_package(tasks, ledger),
            tags=["showcase", "preregistration", "ledger", "fairness", "evaluation", "rules"],
            step_kinds=["plan", "verify", "measure", "review"],
            effects_=effects(filesystem="read", executes="python"),
            parameters={"tasks": len(tasks), "negative_controls": sum(t["negative_control"] for t in tasks)},
            examples=["Check that a run's spec hash matches the pre-registered one",
                      "python3 verify_ledger.py components/skills/showcase-task-*/"],
        )


if __name__ == "__main__":
    main()
