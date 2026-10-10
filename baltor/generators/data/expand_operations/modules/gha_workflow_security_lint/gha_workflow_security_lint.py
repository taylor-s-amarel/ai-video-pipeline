#!/usr/bin/env python3
"""Security lint for GitHub Actions workflows: SHA pinning, permissions, pull_request_target, script injection.

Usage::

    python gha_workflow_security_lint.py .github/workflows/*.yml [--fail-on high] [--json]

Needs PyYAML (imported lazily). Exit 1 when a finding reaches ``--fail-on`` (default ``high``).
A focused subset of what actionlint and zizmor check; run them as well when available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any

SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3}
FULL_SHA = re.compile(r"@[0-9a-f]{40}$")
UNTRUSTED = re.compile(
    r"\$\{\{\s*(github\.head_ref|github\.event\.(issue\.(title|body)|pull_request\.(title|body|head\.ref|head\.label|head\.repo\.default_branch)"
    r"|comment\.body|review\.body|review_comment\.body|discussion\.(title|body)|pages\.[^}]*\.page_name|commits\.[^}]*\.(message|author\.(email|name))"
    r"|head_commit\.(message|author\.(email|name))|workflow_run\.(head_branch|head_commit\.message|display_title)))\s*\}\}")
PR_HEAD_REF = re.compile(r"github\.event\.pull_request\.head\.(sha|ref)|github\.head_ref|refs/pull/")
PRIVILEGED_TRIGGERS = {"pull_request_target", "workflow_run"}


@dataclass
class Finding:
    rule: str
    severity: str
    location: str
    message: str


def _load(text: str) -> dict:
    import yaml  # type: ignore  # lazy import; declared as an external dependency

    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("workflow is not a mapping")
    return data


def _triggers(wf: dict) -> set[str]:
    on = wf.get("on", wf.get(True))  # PyYAML reads the bare key `on` as boolean True
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return {str(x) for x in on}
    if isinstance(on, dict):
        return {str(k) for k in on}
    return set()


def lint_workflow(wf: dict, name: str = "workflow") -> list[Finding]:
    out: list[Finding] = []
    triggers = _triggers(wf)
    top_perms = wf.get("permissions")
    if top_perms in ("write-all",):
        out.append(Finding("GA003", "high", name, "permissions: write-all grants every scope to GITHUB_TOKEN"))
    if isinstance(top_perms, dict) and top_perms.get("id-token") == "write":
        out.append(Finding("GA010", "low", name, "id-token: write at workflow level; grant it only to the deploy job"))
    if "ACTIONS_ALLOW_UNSECURE_COMMANDS" in json.dumps(wf.get("env") or {}):
        out.append(Finding("GA012", "high", name, "ACTIONS_ALLOW_UNSECURE_COMMANDS re-enables set-env/add-path injection"))
    jobs = wf.get("jobs") or {}
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        loc = f"{name}:jobs.{job_id}"
        if top_perms is None and "permissions" not in job:
            out.append(Finding("GA002", "medium", loc, "no permissions block at workflow or job level; GITHUB_TOKEN gets the repository default"))
        if job.get("permissions") == "write-all":
            out.append(Finding("GA003", "high", loc, "permissions: write-all"))
        if "uses" in job:  # reusable workflow call
            ref = str(job["uses"])
            if not ref.startswith("./") and not FULL_SHA.search(ref):
                out.append(Finding("GA001", "medium", loc, f"reusable workflow '{ref}' not pinned to a full commit SHA"))
            if job.get("secrets") == "inherit":
                out.append(Finding("GA007", "low", loc, "secrets: inherit passes every secret; pass only the ones the callee needs"))
            continue
        if "timeout-minutes" not in job:
            out.append(Finding("GA006", "low", loc, "no timeout-minutes; a hung job burns runner minutes for up to 6 hours"))
        runs_on = json.dumps(job.get("runs-on", ""))
        if "self-hosted" in runs_on and ({"pull_request", "pull_request_target"} & triggers):
            out.append(Finding("GA008", "medium", loc, "self-hosted runner reachable from pull request events; use ephemeral, isolated runners"))
        for i, step in enumerate(job.get("steps") or []):
            if not isinstance(step, dict):
                continue
            sloc = f"{loc}.steps[{i}]" + (f" ({step['name']})" if step.get("name") else "")
            uses = str(step.get("uses", ""))
            if uses:
                if uses.startswith("docker://"):
                    if "@sha256:" not in uses:
                        out.append(Finding("GA001", "medium", sloc, f"container action '{uses}' not pinned by digest"))
                elif not uses.startswith("./") and not FULL_SHA.search(uses):
                    out.append(Finding("GA001", "medium", sloc, f"'{uses}' is pinned to a mutable ref; pin the full 40-character commit SHA (tags can be force-pushed)"))
                if uses.split("@")[0] == "actions/checkout":
                    w = step.get("with") or {}
                    if w.get("persist-credentials") not in (False, "false"):
                        out.append(Finding("GA009", "low", sloc, "checkout leaves the token in .git/config; set persist-credentials: false unless later steps push"))
                    if PRIVILEGED_TRIGGERS & triggers and PR_HEAD_REF.search(json.dumps(w)):
                        out.append(Finding("GA004", "high", sloc, "privileged trigger (pull_request_target/workflow_run) checks out untrusted PR code"))
            run = step.get("run")
            if isinstance(run, str):
                m = UNTRUSTED.search(run)
                if m:
                    out.append(Finding("GA005", "high", sloc, f"untrusted input {m.group(0)} interpolated into a shell script; pass it through env: and quote it"))
            env_text = json.dumps(step.get("env") or {})
            if "ACTIONS_ALLOW_UNSECURE_COMMANDS" in env_text:
                out.append(Finding("GA012", "high", sloc, "ACTIONS_ALLOW_UNSECURE_COMMANDS"))
    return sorted(out, key=lambda f: (-SEVERITY[f.severity], f.location))


def lint_text(text: str, name: str = "workflow") -> list[Finding]:
    return lint_workflow(_load(text), name)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--fail-on", choices=list(SEVERITY), default="high")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    findings: list[Finding] = []
    for path in a.files:
        with open(path, encoding="utf-8") as fh:
            findings += lint_text(fh.read(), path)
    if a.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.severity.upper():6} {f.rule} {f.location}: {f.message}")
        print(f"{len(findings)} finding(s)")
    return 1 if any(SEVERITY[f.severity] >= SEVERITY[a.fail_on] for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
