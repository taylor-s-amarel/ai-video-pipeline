#!/usr/bin/env python3
"""Select, plan, validate and summarise adversarial review records without checklist theater.

Implements the evidence contract of the owner's *Animation and Video Production
Master Guide* (10 Oct 2026), section "Adversarial review without checklist
theater", over the 1,024-question bank of Appendix E (shipped as the
``review_bank_<area>`` packages, one ``questions.json`` per area).

What it enforces, each rule taken from the guide:

* ``untested`` is the default; ``observed-pass`` / ``observed-fail`` need exact
  evidence for this target; ``blocked`` and ``not-applicable`` need a stated reason.
* ``demonstrated_defect`` only with an observed failure.
* Evidence carries its own hash, the target movie hash, the extraction or
  observation method, a locator, coverage and limitations.
* Nonfinite numbers, absent intervals, stale target hashes and unsupported
  claimed coverage fail validation.
* A listening-only question is never passed on a waveform statistic.
* Tags are candidate filters; they cannot make an irrelevant question applicable.

Usage::

    python3 adversarial_review_kit.py select --bank DIR_OR_FILE... --pass default_32 [--stage edit] [--style fiction]
    python3 adversarial_review_kit.py plan --bank ... --pass sound --target final.mp4 --stage final-encode \
        --modes visual,machine     # --stage here is the target's stage; it does not drop questions
    python3 adversarial_review_kit.py validate results.json --bank ... [--target final.mp4]
    python3 adversarial_review_kit.py summary results.json

Standard library only. No network access; ``plan --target`` and ``validate --target`` read the file to hash it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

STATUSES = ("untested", "observed-pass", "observed-fail", "blocked", "not-applicable")
OBSERVED = {"observed-pass", "observed-fail"}
FINDING_TYPES = ("none", "demonstrated_defect", "potential_improvement")
MODES = ("visual", "auditory", "machine", "human-audience")
STAGES = ("concept", "script", "storyboard", "animatic", "production", "edit", "final-encode", "delivery")
PLANNING_STAGES = {"concept", "script", "storyboard", "animatic"}
FINAL_ONLY_STAGES = {"final-encode", "delivery"}
COVERAGE = ("not_observed", "sampled", "interval", "full")
COVERAGE_RANK = {c: i for i, c in enumerate(COVERAGE)}
OBSERVATIONS = ("frame-inspection", "contact-sheet", "decoded-stream", "metadata-probe", "measurement",
                "waveform-statistic", "listening", "audience-feedback", "owner-feedback", "source-inspection",
                "other")
LISTENING = {"listening", "audience-feedback", "owner-feedback"}
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
QID_RE = re.compile(r"^AVQ-\d{3}-\d{3}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_PASSES = Path(__file__).with_name("passes.json")


class BankError(ValueError):
    pass


# --------------------------------------------------------------------------- bank and passes

BANK_HEAD_RE = re.compile(r"^# Adversarial review bank: (D\d{3}) (.+?) \(\d+ questions\)[ \t]*$", re.M)
MD_QUESTION_RE = re.compile(
    r"^\d+\. \*\*(?P<id>AVQ-\d{3}-\d{3})\*\* (?P<question>.+)\n"
    r"   - Failure hypothesis: (?P<failure>.+)\n"
    r"   - Check or fix: (?P<check>.+)\n"
    r"   - Severity: (?P<severity>[a-z]+)\. Modes: (?P<modes>[^.\n]+)\. Stages: (?P<stages>[^.\n]+)\. "
    r"Style filters: (?P<styles>[^.\n]+)\.(?: Passes: (?P<passes>[^.\n]+)\.)?[ \t]*$",
    re.M,
)
COMPARED = ("question", "failure_hypothesis", "check_or_fix", "severity", "modes", "stages", "style_filters")


def _records(data: Any) -> list[dict]:
    if isinstance(data, dict) and "questions" in data:
        data = data["questions"]
    if not isinstance(data, list):
        raise BankError("a bank file holds a list of questions or {'questions': [...]}")
    return data


def _split(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def parse_bank_markdown(text: str) -> list[dict]:
    """Questions from a review_bank_<area> RULES.md (what ``place`` installs as .baltor/rules/<name>.md)."""
    head = BANK_HEAD_RE.search(text)
    if not head:
        return []
    return [{
        "id": m["id"], "domain_id": head[1], "area": head[2],
        "question": m["question"].strip(), "failure_hypothesis": m["failure"].strip(),
        "check_or_fix": m["check"].strip(), "severity": m["severity"],
        "modes": _split(m["modes"]), "stages": _split(m["stages"]), "style_filters": _split(m["styles"]),
        "passes": _split(m["passes"]),
    } for m in MD_QUESTION_RE.finditer(text)]


def _owner_bank_file(f: Path) -> list[dict]:
    if f.suffix == ".md":
        return parse_bank_markdown(f.read_text(encoding="utf-8"))
    return _records(json.loads(f.read_text(encoding="utf-8")))


def load_bank(paths: Iterable[str | Path]) -> dict[str, dict]:
    """Load the owner's questions from files or directories.

    A file may be a ``questions.json`` (list, or ``{"questions": [...]}``) or a bank ``RULES.md`` /
    placed ``review-bank-<area>.md``. A directory is searched for both; files there that hold no
    AVQ questions (other catalogue banks) are skipped, and the same question found in a package's
    JSON and Markdown counts once. Conflicting text for one id is an error.
    """
    bank: dict[str, dict] = {}
    where: dict[str, Path] = {}
    for p in paths:
        p = Path(p)
        explicit = not p.is_dir()
        files = [p] if explicit else sorted(
            [*p.rglob("questions.json"), *(f for f in p.rglob("*.md") if f.name != "SKILL.md")])
        for f in files:
            try:
                records = _owner_bank_file(f)
            except (BankError, ValueError, UnicodeDecodeError):
                if explicit:
                    raise
                continue  # another catalogue's file in a shared directory
            if not explicit and not any(isinstance(q, dict) and QID_RE.match(str(q.get("id", ""))) for q in records):
                continue
            if explicit and not records:
                raise BankError(f"{f}: no questions found")
            for q in records:
                qid = q.get("id") if isinstance(q, dict) else None
                if not isinstance(qid, str) or not QID_RE.match(qid):
                    raise BankError(f"{f}: bad question id {qid!r}")
                if qid in bank:
                    if any(bank[qid].get(k) != q.get(k) for k in COMPARED):
                        raise BankError(f"conflicting records for {qid} in {where[qid]} and {f}; "
                                        "pass the owner's bank files explicitly")
                    continue
                bank[qid] = q
                where[qid] = f
    return bank


def load_passes(path: str | Path | None = None) -> dict[str, dict]:
    return json.loads(Path(path or DEFAULT_PASSES).read_text(encoding="utf-8"))


def select(bank: dict[str, dict], pass_id: str | None = None, *, passes: dict | None = None,
           area: str | None = None, stage: str | None = None, style: str | None = None,
           min_severity: str | None = None) -> list[dict]:
    """Candidate questions. A named pass keeps the guide's order; otherwise bank order.

    Filters only narrow the candidates. Whether a candidate applies still depends on the
    feature and the evidence in front of the reviewer.
    """
    if pass_id:
        passes = passes if passes is not None else load_passes()
        if pass_id not in passes:
            raise BankError(f"unknown pass {pass_id!r}; known: {', '.join(sorted(passes))}")
        missing = [q for q in passes[pass_id]["question_ids"] if q not in bank]
        if missing:
            raise BankError(f"pass {pass_id} needs questions not loaded: {', '.join(missing[:5])}"
                            + (" ..." if len(missing) > 5 else ""))
        out = [bank[q] for q in passes[pass_id]["question_ids"]]
    else:
        out = list(bank.values())
    if area:
        out = [q for q in out if area in (q.get("domain_id"), q.get("area"))]
    if stage:
        out = [q for q in out if stage in q.get("stages", [])]
    if style:
        out = [q for q in out if "any" in q.get("style_filters", []) or style in q.get("style_filters", [])]
    if min_severity:
        floor = SEVERITY_RANK[min_severity]
        out = [q for q in out if SEVERITY_RANK.get(q.get("severity"), 0) >= floor]
    return out


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def plan_pass(questions: list[dict], target_artifact: str, target_sha256: str, stage: str,
              available_modes: Iterable[str]) -> list[dict]:
    """Starting records for a bounded pass: every question untested unless honestly blocked.

    * At a planning stage, a question that only applies at final-encode or delivery stays
      ``untested`` and says so.
    * A question whose every mode is unavailable (for example listening with no listener)
      is ``blocked`` with the missing access named. Change it once that access exists.
    """
    if stage not in STAGES:
        raise BankError(f"unknown stage {stage!r}")
    available = set(available_modes)
    unknown = available - set(MODES)
    if unknown:
        raise BankError(f"unknown modes {sorted(unknown)}")
    out = []
    for q in questions:
        modes = q.get("modes", [])
        usable = [m for m in modes if m in available]
        status, rationale = "untested", "Awaiting matching evidence for this target"
        if stage in PLANNING_STAGES and set(q.get("stages", [])) <= FINAL_ONLY_STAGES:
            rationale = "Final-pixel or delivery question; remains untested during planning"
        elif not usable:
            status = "blocked"
            rationale = f"Requires {', '.join(modes)} review; not available for this pass"
        out.append({
            "question_id": q["id"],
            "target_artifact": target_artifact,
            "target_sha256": target_sha256,
            "status": status,
            "finding_type": "none",
            "review_mode": usable[0] if usable else (modes[0] if modes else "visual"),
            "scope": {"start_frame": None, "end_frame": None, "coverage": "not_observed"},
            "evidence": [],
            "rationale": rationale,
            "required_recheck_after": [],
        })
    return out


# --------------------------------------------------------------------------- validation

def _nonfinite(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, float) and not math.isfinite(value):
        return [f"{path} is a nonfinite number"]
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in _nonfinite(v, f"{path}.{k}")]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in _nonfinite(v, f"{path}[{i}]")]
    return []


def _is_frame(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def validate_result(result: dict, question: dict | None = None, current_target_sha256: str | None = None) -> list[str]:
    """Problems with one review record; an empty list means it satisfies the evidence contract."""
    if not isinstance(result, dict):
        return ["record is not an object"]
    problems = _nonfinite(result)
    qid = result.get("question_id")
    where = qid or "?"
    if not isinstance(qid, str) or not QID_RE.match(qid):
        problems.append(f"question_id {qid!r} is not an AVQ-NNN-NNN id")
    if question is not None and question.get("id") != qid:
        problems.append(f"{where}: record is checked against question {question.get('id')}")
    status = result.get("status")
    finding = result.get("finding_type")
    if status not in STATUSES:
        problems.append(f"{where}: status {status!r} is not one of {', '.join(STATUSES)}")
    if finding not in FINDING_TYPES:
        problems.append(f"{where}: finding_type {finding!r} is not one of {', '.join(FINDING_TYPES)}")
    if finding == "demonstrated_defect" and status != "observed-fail":
        problems.append(f"{where}: demonstrated_defect is only used with an observed failure")
    if result.get("review_mode") not in MODES:
        problems.append(f"{where}: review_mode {result.get('review_mode')!r} is not one of {', '.join(MODES)}")
    rationale = result.get("rationale")
    if status in {"blocked", "not-applicable"} and not (isinstance(rationale, str) and rationale.strip()):
        problems.append(f"{where}: {status} needs a stated reason in rationale")
    target = result.get("target_sha256")
    if not isinstance(result.get("target_artifact"), str) or not result.get("target_artifact"):
        problems.append(f"{where}: target_artifact is missing")
    if status in OBSERVED:
        if not isinstance(target, str) or not SHA_RE.match(target):
            problems.append(f"{where}: {status} needs the computed SHA-256 of the exact target")
        elif current_target_sha256 and target != current_target_sha256:
            problems.append(f"{where}: stale target hash (record {target[:12]}..., current {current_target_sha256[:12]}...)")
    if not isinstance(result.get("required_recheck_after", []), list):
        problems.append(f"{where}: required_recheck_after must be a list")

    scope = result.get("scope")
    if not isinstance(scope, dict):
        problems.append(f"{where}: scope is missing")
        scope = {}
    coverage = scope.get("coverage")
    if coverage not in COVERAGE:
        problems.append(f"{where}: scope.coverage {coverage!r} is not one of {', '.join(COVERAGE)}")
    if coverage in {"interval", "full"}:
        start, end = scope.get("start_frame"), scope.get("end_frame")
        if not (_is_frame(start) and _is_frame(end)):
            problems.append(f"{where}: {coverage} coverage needs start_frame and end_frame (absent interval)")
        elif end < start:
            problems.append(f"{where}: end_frame {end} is before start_frame {start}")
    if status in OBSERVED and coverage == "not_observed":
        problems.append(f"{where}: {status} with coverage not_observed")

    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        problems.append(f"{where}: evidence must be a list")
        evidence = []
    if status in OBSERVED and not evidence:
        problems.append(f"{where}: {status} needs at least one evidence item")
    best = -1
    observations = set()
    for i, ev in enumerate(evidence):
        tag = f"{where}: evidence[{i}]"
        if not isinstance(ev, dict):
            problems.append(f"{tag} is not an object")
            continue
        if not (isinstance(ev.get("evidence_sha256"), str) and SHA_RE.match(ev["evidence_sha256"])):
            problems.append(f"{tag} needs its own evidence_sha256")
        ev_target = ev.get("target_sha256")
        if not (isinstance(ev_target, str) and SHA_RE.match(ev_target)):
            problems.append(f"{tag} needs the target movie's target_sha256")
        elif isinstance(target, str) and ev_target != target:
            problems.append(f"{tag} was made from a different target (stale or retargeted evidence)")
        for key in ("method", "locator", "limitations"):
            if not (isinstance(ev.get(key), str) and ev[key].strip()):
                problems.append(f"{tag} needs {key}")
        ev_cov = ev.get("coverage")
        if ev_cov not in COVERAGE:
            problems.append(f"{tag} coverage {ev_cov!r} is not one of {', '.join(COVERAGE)}")
        else:
            best = max(best, COVERAGE_RANK[ev_cov])
        obs = ev.get("observation")
        if obs is not None:
            if obs not in OBSERVATIONS:
                problems.append(f"{tag} observation {obs!r} is not one of {', '.join(OBSERVATIONS)}")
            observations.add(obs)
    if coverage in COVERAGE and coverage != "not_observed" and evidence and COVERAGE_RANK[coverage] > best:
        problems.append(f"{where}: claimed coverage {coverage} is not supported by the evidence")

    if question is not None and status == "observed-pass":
        modes = set(question.get("modes", []))
        if "auditory" in modes and modes <= {"auditory", "human-audience"} and not observations & LISTENING:
            problems.append(f"{where}: listening-only question passed without a recorded listening observation "
                            "(a waveform statistic is not listening)")
    return problems


def validate_results(results: list[dict], bank: dict[str, dict] | None = None,
                     current_target_sha256: str | None = None) -> list[str]:
    problems: list[str] = []
    seen: set[tuple] = set()
    for r in results:
        qid = r.get("question_id") if isinstance(r, dict) else None
        q = None
        if bank is not None:
            q = bank.get(qid)
            if q is None:
                problems.append(f"{qid}: not a question in the loaded bank")
        key = (qid, r.get("target_sha256") if isinstance(r, dict) else None)
        if key in seen:
            problems.append(f"{qid}: recorded twice for the same target")
        seen.add(key)
        problems += validate_result(r, q, current_target_sha256)
    return problems


# --------------------------------------------------------------------------- after a change, and reporting

def needs_recheck(results: list[dict], changes: Iterable[str]) -> list[str]:
    """Question ids whose records name any of ``changes`` (e.g. camera_change) in required_recheck_after."""
    changed = set(changes)
    return [r["question_id"] for r in results if changed & set(r.get("required_recheck_after", []))]


def summarise(results: list[dict]) -> dict:
    """Counts per status and the ids that were not checked. Never a score."""
    counts = {s: 0 for s in STATUSES}
    for r in results:
        counts[r.get("status", "untested")] = counts.get(r.get("status", "untested"), 0) + 1
    return {
        "records": len(results),
        "by_status": counts,
        "demonstrated_defects": [r["question_id"] for r in results if r.get("finding_type") == "demonstrated_defect"],
        "potential_improvements": [r["question_id"] for r in results if r.get("finding_type") == "potential_improvement"],
        "not_checked": [r["question_id"] for r in results if r.get("status") in {"untested", "blocked"}],
    }


# --------------------------------------------------------------------------- CLI

def _load_results(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("select", "plan"):
        p = sub.add_parser(name)
        p.add_argument("--bank", nargs="+", required=True, help="questions.json files or directories holding them")
        p.add_argument("--passes", help="passes.json (default: the one next to this module)")
        p.add_argument("--pass", dest="pass_id")
        p.add_argument("--area")
        p.add_argument("--stage", choices=STAGES,
                       help="select: keep questions listed for this stage; plan: the stage of the target under review "
                            "(questions are not dropped, final-pixel ones stay untested during planning)")
        p.add_argument("--style")
        p.add_argument("--min-severity", choices=list(SEVERITY_RANK))
        if name == "plan":
            p.add_argument("--target", required=True, help="exact artifact to review; it is hashed")
            p.add_argument("--modes", default="visual,machine",
                           help="review modes actually available, comma separated (visual,auditory,machine,human-audience)")
    v = sub.add_parser("validate")
    v.add_argument("results")
    v.add_argument("--bank", nargs="+")
    v.add_argument("--target", help="current exact target file; records hashed against another file are stale")
    s = sub.add_parser("summary")
    s.add_argument("results")
    a = ap.parse_args(argv)

    if a.cmd in {"select", "plan"}:
        bank = load_bank(a.bank)
        passes = load_passes(a.passes) if a.pass_id else None
        qs = select(bank, a.pass_id, passes=passes, area=a.area, stage=a.stage if a.cmd == "select" else None,
                    style=a.style, min_severity=a.min_severity)
        if a.cmd == "select":
            print(json.dumps([{k: q.get(k) for k in ("id", "area", "question", "severity", "modes", "stages")}
                              for q in qs], indent=2, ensure_ascii=False))
        else:
            stage = a.stage or "final-encode"
            modes = [m.strip() for m in a.modes.split(",") if m.strip()]
            print(json.dumps(plan_pass(qs, a.target, sha256_file(a.target), stage, modes), indent=2))
        return 0
    results = _load_results(a.results)
    if a.cmd == "summary":
        print(json.dumps(summarise(results), indent=2))
        return 0
    bank = load_bank(a.bank) if a.bank else None
    current = sha256_file(a.target) if a.target else None
    problems = validate_results(results, bank, current)
    for p in problems:
        print(f"FAIL  {p}")
    print(f"{len(results)} record(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
