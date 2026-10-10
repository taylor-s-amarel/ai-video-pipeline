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

HASH_METHOD = ("spec_sha256 = sha256 of the canonical JSON of task.json without the key spec_sha256 (keys sorted, "
               "separators ',' ':', UTF-8, ensure_ascii false); task.json lists every other package file in files_sha256")
CONTENT_METHOD = ("content_sha256 = sha256 of the canonical JSON of task.json without spec_sha256, version, preregistered_on "
                  "and the SKILL.md entry of files_sha256; used only to detect whether a spec changed")

FRAMEWORK_SCHEMA = HERE / "data" / "showcase_framework" / "schemas" / "showcase_task_spec" / "schema.json"

BUDGETS = {
    "xs": {"wall_s": 600, "tool_calls": 30, "tokens": 120_000},
    "s": {"wall_s": 1200, "tool_calls": 60, "tokens": 300_000},
    "m": {"wall_s": 2400, "tool_calls": 120, "tokens": 700_000},
    "l": {"wall_s": 3600, "tool_calls": 200, "tokens": 1_200_000},
    "xl": {"wall_s": 5400, "tool_calls": 300, "tokens": 2_000_000},
}

# Study-level choices recorded in every spec. Changing any of them changes every spec hash and
# creates a new ledger revision dated the day of the change.
STUDY = {
    "harness": "claude-code",
    "harness_version": "2.",
    "model": "claude-sonnet-4-5",
    "allowed_tools": ["Bash", "Read", "Write", "Edit", "Glob", "Grep"],
    "transcript_format": "stream-json",
    "isolation": "home",
    "registered_by": "Baltor showcase task library (generators/showcase_tasks.py)",
}

SHARED_PREAMBLE = ("You are working in a fresh workspace. The full task is below and in TASK.md. Before you finish, "
                   "check your deliverables against every requirement.")
BALTOR_ADDENDUM = ("A command named `baltor` is on your PATH. `baltor search \"<words>\"` lists components in the Baltor "
                   "catalogue (skills, rules, code modules, schemas and more), `baltor read IDENTITY --out DIR` downloads "
                   "one into your workspace, and `baltor place IDENTITY` installs it where this harness reads it. Using "
                   "it is optional.")

CATALOGUE_EXCLUSIONS = {
    "identity_prefixes": ["showcase_task_", "showcase_preregistration_ledger"],
    "tags": ["showcase-task"],
    "reason": "Task packages contain evaluators, reference outputs and fixture generators; an agent that reads them is not solving the task.",
    "rule": "The catalogue served to the baltor arm must omit these items; a run whose catalogue log shows one of them is contaminated and counts as a failure for the baltor arm.",
}

ANALYSIS_TEXT = {
    "primary": "task_pass (1 when evaluate.py reports passed): baltor minus baseline pass rate with a 95% percentile bootstrap interval over paired trials (10,000 resamples), plus the win rate",
    "secondary": ["composite_score and each task metric: difference with a 95% bootstrap interval and Cliff's delta",
                  "cost per run and per passing run: tokens, wall time, tool calls, catalogue calls, USD",
                  "blind pairwise judge scores where the task has them (secondary evidence only)"],
    "missing_or_failed_runs": "Crashed, timed-out, over-budget and contaminated runs count as failures for their arm; nothing is dropped or selectively re-run. A whole trial may be re-run only for an infrastructure fault, which is reported.",
    "pooling": "Negative controls are reported separately. A pooled effect weights tasks equally and is shown next to every per-task result.",
}

COI = ("The tasks, the evaluators, the Baltor catalogue components available to the baltor arm and any report built from "
       "these runs come from the same team. Treat results as vendor-run evidence until an independent party reproduces them; "
       "every input needed to reproduce a run is in this package.")
OTHER_DISCLOSURES = [
    "Deterministic evaluator results are the primary evidence. Blind pairwise or LLM-judge scores, where collected, are weaker evidence (position, length and style biases) and are reported separately.",
    "The showcase task packages and the pre-registration ledger are excluded from the catalogue served to the baltor arm.",
    "Third-party datasets are never copied into this package: offline tasks use data bundled with scikit-learn or seeded synthetic data; Kaggle tasks need the user's own account and rule acceptance.",
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
DETAIL = json.loads((PKG / "task_detail.json").read_text(encoding="utf-8"))
PARAMS = DETAIL["params"]
sys.path.insert(0, str(PKG))


def run_setup(tmp_path: Path, seed: int = 20261010, extra: list | None = None) -> tuple[Path, Path]:
    ws, pv = tmp_path / "workspace", tmp_path / "private"
    proc = subprocess.run([sys.executable, str(PKG / "setup" / "make_fixtures.py"), "--workspace", str(ws),
                           "--private", str(pv), "--seed", str(seed)] + (extra or []),
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert (ws / "TASK.md").exists()
    return ws, pv


def evaluate(ws: Path, pv: Path) -> dict:
    proc = subprocess.run([sys.executable, str(PKG / "evaluate.py"), "--workspace", str(ws), "--private", str(pv)],
                          capture_output=True, text=True, timeout=DETAIL["evaluator_timeout_s"] + 120)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["task_id"] == TASK["id"]
    assert result["valid"], result["integrity_problems"]
    return result


def assert_good(result: dict) -> None:
    assert not result["errors"], result["errors"]
    assert result["passed"], json.dumps({k: result[k] for k in ("gates", "required_checks", "metrics", "checks", "flags")},
                                        indent=1)[:6000]
    assert result["metrics"]["task_pass"] == 1.0


def assert_bad(result: dict, good: dict | None = None) -> None:
    assert not result["passed"]
    assert result["metrics"]["task_pass"] == 0.0
    if good is not None:
        assert result["score"] < good["score"]


def test_spec_hash_and_files_match():
    import showcase_eval as se
    assert se.compute_spec_hash(TASK) == TASK["spec_sha256"]
    assert se.integrity_problems(TASK, PKG) == []


def test_missing_deliverables_fail(tmp_path):
    ws, pv = run_setup(tmp_path)
    result = evaluate(ws, pv)
    assert not result["passed"]
    assert result["metrics"]["task_pass"] == 0.0

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
                if k in ("params", "input_source") and isinstance(v, dict):
                    merged.setdefault(k, {}).update(copy.deepcopy(v))
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


def as_written(text: str) -> bytes:
    """Bytes exactly as GeneratorRun writes a text payload file."""
    return (text if text.endswith("\n") else text + "\n").encode("utf-8")


# --------------------------------------------------------------------------- specs

def build_detail(defn: dict) -> dict:
    """task_detail.json: what the evaluator and setup read (covered by files_sha256)."""
    preset = defn.get("budget", "m")
    budget = {"preset": preset, **BUDGETS[preset]}
    metrics = []
    for m in defn["metrics"]:
        mm = {"name": m["name"], "description": m["description"], "direction": m.get("direction", "maximize"),
              "weight": float(m.get("weight", 1.0)), "scale": [float(x) for x in m.get("scale", [0, 1])],
              "gate": bool(m.get("gate", "threshold" in m))}
        if "threshold" in m:
            mm["threshold"] = float(m["threshold"])
        metrics.append(mm)
    success = defn.get("success", {})
    req_checks = list(success.get("required_checks", []))
    parts = [f"{m['name']} {'>=' if m['direction'] == 'maximize' else '<='} {m['threshold']:g}" for m in metrics if m["gate"]]
    parts += [f"check '{c}' passes" for c in req_checks]
    min_score = float(success.get("min_score", 0.0))
    if min_score:
        parts.append(f"composite score >= {min_score:g}")
    pairwise = None
    if defn.get("pairwise"):
        pairwise = {"criteria": list(defn["pairwise"]["criteria"]), "judges": list(defn["pairwise"].get("judges", ["human", "llm"])),
                    "blind": True, "order": "randomised", "scale": [1, 5], "evidence_weight": "secondary"}
    detail = {
        "spec": se.DETAIL_SPEC,
        "task_id": identity_for(defn["slug"]),
        "slug": defn["slug"],
        "title": defn["title"],
        "domain": defn["domain"],
        "category": defn["category"],
        "negative_control": bool(defn.get("negative_control", False)),
        "summary": defn["summary"],
        "tests": defn["tests"].strip(),
        "prompt": defn["prompt"].strip(),
        "requirements": list(defn["requirements"]),
        "workspace_rules": list(defn.get("workspace_rules", [])),
        "deliverables": list(defn["deliverables"]),
        "workspace_files": [i["path"] for i in defn.get("inputs", [])],
        "private_files": list(defn.get("private_files", [])),
        "budget": budget,
        "params": copy.deepcopy(defn.get("params", {})),
        "metrics": metrics,
        "success": {"rule": "pass when the evaluation ran without errors, the package is unmodified"
                            + ("" if not parts else " and " + " and ".join(parts)),
                    "min_score": min_score, "required_checks": req_checks},
        "hypothesis": {"expected_effect": defn["hypothesis"]["expected_effect"],
                       "rationale": " ".join(defn["hypothesis"]["rationale"].split())},
        "pairwise": pairwise,
        "expected_capabilities": list(defn.get("expected_capabilities", [])),
        "cautions": list(defn.get("cautions", [])),
        "external_tools": list(defn.get("external_tools", [])),
        "evaluator_timeout_s": int(defn.get("evaluator_timeout_s", 300)),
        "runs_agent_code": bool(defn.get("runs_agent_code", False)),
        "deterministic": bool(defn.get("deterministic", True)),
        "catalogue_exclusions": CATALOGUE_EXCLUSIONS,
        "analysis": ANALYSIS_TEXT,
        "fixture_seeds": ("The runner passes --seed. Both arms of a trial always use the same seed. To vary fixtures "
                          "across trials use showcase_eval.fixture_seed(spec_sha256, trial)."),
    }
    if defn.get("competition"):
        detail["competition"] = dict(defn["competition"])
    return detail


def _metric_evaluator(name: str, timeout: int) -> dict:
    return {"type": "script", "params": {
        "command": ["python3", "evaluate.py", "--workspace", "{workspace}", "--private", "{private}"],
        "cwd": "{task_dir}", "result": "stdout-json", "value_path": f"metrics.{name}", "timeout_s": timeout}}


def framework_inputs(defn: dict) -> list[dict]:
    base = defn.get("input_source", {"source": "synthetic", "licence": "MIT"})
    out = [{"name": "Task description (TASK.md, written by setup from task_detail.json)", "source": "task-dir",
            "licence": "MIT", "path_in_workspace": "TASK.md"}]
    for i in defn.get("inputs", []):
        src = {**base, **{k: v for k, v in i.items() if k != "path"}}
        entry = {"name": src.get("name") or i["path"], "source": src["source"], "licence": src["licence"],
                 "path_in_workspace": i["path"]}
        if src.get("url"):
            entry["url"] = src["url"]
        if src["source"] == "kaggle":
            entry["requires_account"] = True
            entry["requires_rule_acceptance"] = True
        if src.get("notes"):
            entry["notes"] = src["notes"]
        out.append(entry)
    return out


def build_task_json(defn: dict, detail: dict) -> dict:
    """task.json in the showcase_task_spec contract format, without version/preregistered_on/files_sha256/spec_sha256."""
    timeout = detail["evaluator_timeout_s"]
    metrics = [{
        "name": "task_pass", "description": "1 when evaluate.py reports passed (every gate and required check), else 0",
        "direction": "higher", "kind": "deterministic", "evaluator": _metric_evaluator("task_pass", timeout),
        "weight": 1.0, "primary": True, "on_missing": 0, "range": [0, 1]}]
    for m in detail["metrics"]:
        metrics.append({
            "name": m["name"], "description": m["description"][:500],
            "direction": "higher" if m["direction"] == "maximize" else "lower", "kind": "deterministic",
            "evaluator": _metric_evaluator(m["name"], timeout), "weight": m["weight"], "primary": False,
            "on_missing": m["scale"][0], "range": sorted(m["scale"])})
    if detail["pairwise"]:
        pw = detail["pairwise"]
        metrics.append({
            "name": "blind_judge_score", "description": "Blind, order-randomised pairwise judgement (1-5) on: " + "; ".join(pw["criteria"])[:400],
            "direction": "higher", "kind": "llm-judge",
            "evaluator": {"type": "blind_judge", "params": {"criteria": pw["criteria"], "scale": pw["scale"],
                                                             "judges": pw["judges"], "blind": True, "order": "randomised"}},
            "weight": 0.1, "primary": False, "on_missing": 1, "range": [1, 5]})
    arm = {"harness": STUDY["harness"], "harness_version": STUDY["harness_version"], "model": STUDY["model"],
           "allowed_tools": list(STUDY["allowed_tools"]), "transcript_format": STUDY["transcript_format"],
           "isolation": STUDY["isolation"]}
    task = {
        "spec": se.TASK_SPEC,
        "id": detail["task_id"],
        "purpose": "study",
        "task_type": "capability",
        "domain": detail["domain"],
        "title": detail["title"][:140],
        "prompt": SHARED_PREAMBLE + "\n\n" + se.task_markdown(detail),
        "inputs": framework_inputs(defn),
        "setup": {"script": "setup/make_fixtures.py", "network": False, "timeout_s": 900},
        "outputs": [{"path": d["path"], "required": True, "description": d["description"][:300]} for d in detail["deliverables"]],
        "budget": {k: detail["budget"][k] for k in ("wall_s", "tool_calls", "tokens")},
        "over_budget": "score-as-failure",
        "arms": {"baseline": {**arm, "catalogue_access": {"mode": "none"}, "prompt_addendum": ""},
                 "baltor": {**arm, "catalogue_access": {"mode": "search-read", "endpoint": "local"},
                            "prompt_addendum": BALTOR_ADDENDUM}},
        "metrics": metrics,
        "success_threshold": {"metric": "task_pass", "op": ">=", "value": 1},
        "trials": int(defn.get("trials", 5)),
        "order": "randomised",
        "negative_control": detail["negative_control"],
        "expected_components": sorted(set(defn.get("expected_components", []))),
        "analysis": {"design": "paired", "bootstrap_resamples": 10000, "ci_level": 0.95,
                     "seed": int(se.sha256_bytes(detail["task_id"].encode())[:8], 16), "alpha": 0.05},
        "disclosures": {"conflict_of_interest": COI, "other": list(OTHER_DISCLOSURES)},
        "registered_by": STUDY["registered_by"],
        "notes": ("Scoring detail (requirements, parameters, metric scales, gates, hypothesis, catalogue exclusions) is in "
                  "task_detail.json, covered by files_sha256. Setup: python3 setup/make_fixtures.py --workspace W --private P "
                  "--seed N. Evaluation: python3 evaluate.py --workspace W --private P prints one JSON object whose "
                  "metrics.<name> holds every metric above."),
    }
    if detail["negative_control"]:
        task["negative_control_rationale"] = detail["hypothesis"]["rationale"][:1000]
    return task


VOLATILE = ("version", "preregistered_on", "files_sha256", "spec_sha256")


def content_hash(task: dict, files: dict[str, str]) -> str:
    body = {"task": {k: v for k, v in task.items() if k not in VOLATILE},
            "files": {p: se.sha256_bytes(as_written(t)) for p, t in sorted(files.items()) if p != "SKILL.md"}}
    return se.sha256_bytes(se.canonical_json(body))


# --------------------------------------------------------------------------- ledger

def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"spec": "baltor.showcase-ledger/v1", "hash_method": HASH_METHOD, "content_method": CONTENT_METHOD,
            "tasks": {}}


def update_ledger(ledger: dict, current: dict[str, str], today: str) -> dict:
    """Append-only. ``current`` maps task id -> content hash. Unchanged content keeps its revision and date;
    changed content adds a revision dated today; a task no longer generated is marked withdrawn."""
    ledger = copy.deepcopy(ledger)
    tasks = ledger.setdefault("tasks", {})
    for task_id, ch in sorted(current.items()):
        hist = tasks.setdefault(task_id, [])
        if hist and hist[-1]["content_sha256"] == ch and hist[-1]["status"] == "registered":
            continue
        for old in hist:
            if old["status"] == "registered":
                old["status"] = "superseded"
                old["superseded_on"] = today
        hist.append({"revision": len(hist) + 1, "content_sha256": ch, "spec_sha256": None,
                     "preregistered": today, "status": "registered"})
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


def skill_body(detail: dict, task: dict, entry: dict) -> str:
    b = detail["budget"]
    control = " · **negative control**" if detail["negative_control"] else ""
    kaggle = ""
    if detail.get("competition"):
        c = detail["competition"]
        kaggle = f"""
## Kaggle data (your own account)

This task uses a real competition: <{c['url']}>. It needs your own Kaggle account, and you must
accept the competition rules at <{c['rules_url']}> before downloading. Nothing from the
competition is stored in this package or this repository. The setup script makes a seeded local
validation split of the files you downloaded and the evaluator scores that split with the
competition metric ({c['metric']}). Local scores are not leaderboard scores.

```
kaggle competitions download -c {c['slug']} -p ~/kaggle/{c['slug']} && unzip -o ~/kaggle/{c['slug']}/{c['slug']}.zip -d ~/kaggle/{c['slug']}
export SHOWCASE_KAGGLE_DIR=~/kaggle        # or pass --source ~/kaggle/{c['slug']} to setup
```
"""
    pairwise = ""
    if detail["pairwise"]:
        pw = detail["pairwise"]
        pairwise = ("\n## Blind pairwise judging (secondary evidence)\n\nAfter deterministic scoring, the two arms' outputs from the "
                    "same trial are shown side by side with arm labels removed and left/right order randomised. Criteria: "
                    + "; ".join(pw["criteria"]) + ". Judges: " + ", ".join(pw["judges"])
                    + ". These scores are reported separately and never change pass/fail.\n")
    metrics = "\n".join(_fmt_metric(m) for m in detail["metrics"])
    inputs = "\n".join(f"- `{i['path_in_workspace']}`: {i['name']} ({i['source']}, {i['licence']}"
                       f"{', ' + i['url'] if i.get('url') else ''}){': ' + i['notes'] if i.get('notes') else ''}"
                       for i in task["inputs"])
    cautions = "\n".join(f"- {c}" for c in detail["cautions"]) or "- none beyond the general rules"
    expected = ", ".join(f"`{c}`" for c in task["expected_components"]) or "none identified on disk yet"
    caps = "; ".join(detail["expected_capabilities"]) or "-"
    deliverables = "\n".join(f"- `{d['path']}`: {d['description']}" for d in detail["deliverables"])
    tools = ", ".join(detail["external_tools"]) or "none beyond Python 3.10+"
    return f"""
# Showcase task: {detail['title']}

{detail['summary']}

Pre-registered {entry['preregistered']} (revision {entry['revision']}) · {task['trials']} paired trials per arm ·
domain `{detail['domain']}`{control} · spec hash in `task.json` (`spec_sha256`) and in the
`showcase_preregistration_ledger` rules package.

## What this task tests

{detail['tests']}

Deliverables:

{deliverables}

## Why Baltor might help, or not

Pre-registered expectation: **{detail['hypothesis']['expected_effect']}**. {detail['hypothesis']['rationale']}

Components the authors expect could matter (for post-hoc analysis only; nothing is pre-placed): {expected}.
Capabilities: {caps}.

## Fair comparison

- Baseline arm: {STUDY['harness']} with {STUDY['model']} alone. Baltor arm: the same harness, model, tools and
  flags plus a logged `baltor` command for searching, reading and placing catalogue items. Nothing is
  pre-placed; the agent decides whether and what to look for.
- Held constant: model, harness version, allowed tools, budget ({b['wall_s']} s wall time, {b['tool_calls']} tool
  calls, {b['tokens']:,} tokens; over budget scores as failure), the starting workspace (same fixture seed in
  both arms of a trial), no network, isolated home directory. The prompts differ only by the access addendum.
- {task['trials']} paired trials, randomised order, every run reported (failures, timeouts and losses included)
  with tokens, wall time and tool calls.
- Showcase task packages and the ledger are excluded from the catalogue the Baltor arm sees; a run that reads
  one is contaminated and counts as a failure for that arm.

## Run it end to end

```
python3 showcase_eval.py .        # spec hash, integrity check and a per-trial plan (arm order, fixture seed)
python3 setup/make_fixtures.py --workspace RUN/workspace --private RUN/private --seed SEED
# run the agent in RUN/workspace with task.json "prompt" (+ "prompt_addendum" for the baltor arm)
python3 evaluate.py --workspace RUN/workspace --private RUN/private --out RUN/evaluation.json
```

Keep `RUN/private` unreadable by the agent (another user, or create it only after the agent exits by
re-running setup with the same seed into a fresh directory pair and copying just the private half).
Evaluator self-test: `python3 -m pytest -q .` (needs: {tools}).
{kaggle}
## Metrics and pass rule

| Metric | Meaning | Direction | Weight | Scale (worst → best) | Gate |
|---|---|---|---:|---|---|
{metrics}

{detail['success']['rule']}. `composite_score` is the weighted mean of the normalised metrics; `task_pass` is
the primary outcome.
{pairwise}
## Inputs and licences

{inputs}

## Cautions

{cautions}

## Disclosures

- {COI}
""" + "\n".join(f"- {d}" for d in OTHER_DISCLOSURES) + "\n"


def skill_description(detail: dict) -> str:
    d = (f"Pre-registered Baltor showcase task ({detail['domain']}): {detail['summary']} Use when running or "
         "reproducing a with-versus-without-Baltor comparison: makes seeded fixtures and scores a run with a "
         "deterministic evaluator that prints JSON.")
    return d[:1024]


# --------------------------------------------------------------------------- ledger package

def ledger_package(built: list[tuple[dict, dict, dict, dict]], ledger: dict) -> dict[str, str]:
    rows = []
    for _, detail, task, _ in sorted(built, key=lambda b: b[2]["id"]):
        e = current_entry(ledger, task["id"])
        rows.append({"task_id": task["id"], "domain": task["domain"], "negative_control": task["negative_control"],
                     "spec_sha256": task["spec_sha256"], "content_sha256": e["content_sha256"],
                     "preregistered": e["preregistered"], "revision": e["revision"], "trials_per_arm": task["trials"]})
    withdrawn = [{"task_id": k, **v[-1]} for k, v in ledger["tasks"].items() if v and v[-1]["status"] == "withdrawn"]
    rules = {
        "spec": "baltor.showcase-ledger/v1",
        "hash_method": HASH_METHOD,
        "content_method": CONTENT_METHOD,
        "task_count": len(rows),
        "negative_controls": sum(r["negative_control"] for r in rows),
        "study": STUDY,
        "tasks": rows,
        "withdrawn": withdrawn,
        "protocol": {
            "shared_preamble": SHARED_PREAMBLE,
            "baltor_addendum": BALTOR_ADDENDUM,
            "catalogue_exclusions": CATALOGUE_EXCLUSIONS,
            "analysis": ANALYSIS_TEXT,
            "conflict_of_interest": COI,
            "disclosures": OTHER_DISCLOSURES,
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
    table = "\n".join(f"| `{r['task_id']}` | {r['domain']}{' · control' if r['negative_control'] else ''} | "
                      f"`{r['spec_sha256']}` | {r['preregistered']} | {r['revision']} | {r['trials_per_arm']} |" for r in rows)
    domains = ", ".join(f"{k} {v}" for k, v in sorted(by_domain.items()))
    md = f"""
# Showcase pre-registration ledger

Every Baltor showcase task, the SHA-256 of its pre-registered spec and the date that spec was
registered. A run counts only if the `spec_sha256` in its record equals the hash listed here.
{len(rows)} tasks ({domains}); {rules['negative_controls']} negative controls. Study configuration:
{STUDY['harness']} {STUDY['harness_version']}x with {STUDY['model']}, tools {', '.join(STUDY['allowed_tools'])}.

## Rules

1. **Pre-register before any run.** Prompt, inputs, budget, metrics, evaluator, setup, trial count and pass
   rule are in `task.json` and `task_detail.json`, both covered by `spec_sha256`. Publish this ledger (a public
   commit is the timestamp) before the first run.
2. **Same everything except the catalogue.** Same model, harness version, tools, flags, budget (time, tool calls,
   tokens), starting workspace and fixture seed in both arms of a trial. The Baltor arm's prompt adds only the
   access addendum; nothing is pre-placed.
3. **At least 3 paired trials per arm (5 where affordable)**, in randomised order fixed before the first run.
4. **Deterministic local evaluators first.** Subjective outputs may add blind pairwise judging (labels hidden,
   order randomised). Judge scores are secondary evidence, reported separately; LLM-judge results are weaker
   than deterministic tests.
5. **Report every run**: failures, timeouts, over-budget and contaminated runs count as failures for their arm.
   No best-of-N, no selective re-runs.
6. **Effect sizes with uncertainty**: pass-rate and score differences with 95% bootstrap intervals over paired
   trials, plus win rates. Never a single best run.
7. **Negative controls** ({rules['negative_controls']} tasks where Baltor should not matter) use the same protocol to
   detect placebo effects and measure search overhead.
8. **Cost next to quality**: tokens, wall time, tool calls and catalogue calls for every run.
9. **No leakage**: the catalogue served to the Baltor arm omits every `showcase_task_*` package and this ledger;
   private ground truth never sits in the workspace; a run that reads an excluded item is contaminated.
10. **Amendments are visible**: a changed spec gets a new revision, hash and date; runs under an older hash are
    reported under that revision and never pooled with the new one. Withdrawn tasks stay listed.
11. **Conflict of interest**: {COI}
12. **Data licences**: no third-party dataset is copied into the repository. Kaggle tasks need the user's own
    account and rule acceptance; offline tasks use scikit-learn's bundled datasets or seeded synthetic data.

Check a placed or downloaded task package against this ledger:
`python3 verify_ledger.py path/to/showcase-task-*/` (recomputes `spec_sha256` and every file hash).

## Ledger

Hash method: {HASH_METHOD}.

| Task id | Domain | spec_sha256 | Pre-registered | Revision | Trials/arm |
|---|---|---|---|---:|---:|
{table}
"""
    verify = r'''#!/usr/bin/env python3
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
'''
    return {
        "RULES.md": md,
        "rules.json": dumps(rules),
        "ledger.json": dumps(ledger),
        "verify_ledger.py": verify,
        "schemas/showcase_task_detail.schema.json": (SCHEMAS / "showcase_task_detail.schema.json").read_text(encoding="utf-8"),
        "schemas/showcase_evaluation.schema.json": (SCHEMAS / "showcase_evaluation.schema.json").read_text(encoding="utf-8"),
    }


# --------------------------------------------------------------------------- build

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


def _schema_errors(instance: dict, schema_path: Path) -> list[str]:
    try:
        import jsonschema
    except ImportError:  # pragma: no cover
        return []
    if not schema_path.exists():
        return []
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in v.iter_errors(instance)]


def build_all(today: str | None = None, ledger: dict | None = None) -> tuple[list[tuple[dict, dict, dict, dict]], dict]:
    """Return [(defn, detail, task, files)] and the updated ledger, without writing anything."""
    today = today or os.environ.get("SHOWCASE_PREREG_DATE") or dt.date.today().isoformat()
    staged = []
    for defn in load_task_defs():
        files = assemble_files(defn)
        detail = build_detail(defn)
        files["task_detail.json"] = dumps(detail)
        task = build_task_json(defn, detail)
        staged.append((defn, detail, task, files))
    ledger = update_ledger(ledger if ledger is not None else load_ledger(),
                           {t["id"]: content_hash(t, f) for _, _, t, f in staged}, today)
    built = []
    for defn, detail, task, files in staged:
        entry = current_entry(ledger, task["id"])
        files["SKILL.md"] = skill_md(f"showcase-task-{detail['slug']}", skill_description(detail),
                                     skill_body(detail, task, entry))
        task["version"] = entry["revision"]
        task["preregistered_on"] = entry["preregistered"]
        task["files_sha256"] = {p: se.sha256_bytes(as_written(t)) for p, t in sorted(files.items())}
        task["spec_sha256"] = se.compute_spec_hash(task)
        entry["spec_sha256"] = task["spec_sha256"]
        errs = _schema_errors(task, FRAMEWORK_SCHEMA) + _schema_errors(detail, SCHEMAS / "showcase_task_detail.schema.json")
        if errs:
            raise SystemExit(f"{task['id']}: {errs[:5]}")
        built.append((defn, detail, task, files))
    return built, ledger


def main() -> None:
    built, ledger = build_all()
    known = known_identities()
    for _, _, task, _ in built:
        for ident in task["expected_components"]:
            if ident not in known:
                print(f"warning: {task['id']} expects unknown component '{ident}'", file=sys.stderr)
    LEDGER.write_text(dumps(ledger), encoding="utf-8")
    with GeneratorRun(__file__, data=DATA_REL) as run:
        for defn, detail, task, files in built:
            side = ["setup writes a fresh workspace and a private ground-truth directory"]
            if detail["runs_agent_code"]:
                side.append("evaluate.py runs agent-written code in a subprocess with a timeout")
            for tool in detail["external_tools"]:
                side.append(f"runs {tool}")
            payload = dict(files)
            payload["task.json"] = dumps(task)
            tags = ["showcase", "showcase-task", "preregistered", "evaluator", detail["domain"], detail["category"]]
            for extra in (["negative-control"] if detail["negative_control"] else []) + \
                         (["kaggle"] if detail.get("competition") else []) + list(defn.get("tags", [])):
                if extra not in tags and len(tags) < 24:
                    tags.append(extra)
            run.component(
                "skill", task["id"],
                title=f"Showcase task: {detail['title']}"[:120],
                summary=detail["summary"],
                description=(f"Pre-registered {task['preregistered_on']} (revision {task['version']}), spec_sha256 "
                             f"{task['spec_sha256']}. {task['trials']} paired trials per arm. "
                             + detail["hypothesis"]["rationale"])[:4000],
                subkind="evaluator", domain=detail["domain"],
                files=payload,
                tags=tags,
                step_kinds=["verify", "measure", "test"],
                effects_=effects(filesystem="write", executes="python", side_effects=side),
                depends_on=[{"identity": d, "external": True} for d in defn.get("depends_on", [])] or None,
                parameters={"family": defn["family"], "spec_sha256": task["spec_sha256"], "source": defn["_source"]},
                examples=[f"Set up a trial of {task['id']} and score the agent's workspace",
                          "Print the run plan for this task: python3 showcase_eval.py ."],
                review={"status": "automated-passed", "checked": task["preregistered_on"],
                        "notes": "The evaluator self-test proves a known-good output passes and a known-bad output fails."},
            )
        run.component(
            "rules", LEDGER_IDENTITY,
            title="Showcase pre-registration ledger",
            summary=f"Fairness rules for with/without-Baltor showcases and the ledger of all {len(built)} pre-registered tasks: id, spec hash, registration date, revision.",
            subkind="rule-set", domain="baltor",
            files=ledger_package(built, ledger),
            tags=["showcase", "preregistration", "ledger", "fairness", "evaluation", "rules"],
            step_kinds=["plan", "verify", "measure", "review"],
            effects_=effects(filesystem="read", executes="python"),
            parameters={"tasks": len(built), "negative_controls": sum(t["negative_control"] for _, _, t, _ in built)},
            examples=["Check that a run's spec hash matches the pre-registered one",
                      "python3 verify_ledger.py components/skills/showcase-task-*/"],
        )


if __name__ == "__main__":
    main()
