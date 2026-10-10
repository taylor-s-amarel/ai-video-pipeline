#!/usr/bin/env python3
"""Summarise a Terraform/OpenTofu plan and flag risky changes before anyone applies it.

Input is the JSON form of a saved plan::

    terraform plan -out plan.out && terraform show -json plan.out > plan.json
    tofu plan -out plan.out && tofu show -json plan.out > plan.json

Usage::

    python terraform_plan_risk_report.py plan.json [--format md|json] [--fail-on high]
           [--require-tags owner,environment] [--stateful-pattern REGEX ...]

Exit status: 0 when no finding reaches ``--fail-on`` (default ``high``), 1 otherwise,
2 when the file is not a plan JSON document. Standard library only.

The checks are heuristics for review, not a policy engine: a clean report means
"nothing matched these rules", never "safe to apply".
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3}

DEFAULT_STATEFUL = [
    r"^aws_(db_instance|rds_cluster|rds_cluster_instance|dynamodb_table|s3_bucket|efs_file_system|ebs_volume|"
    r"elasticache_(cluster|replication_group)|redshift_cluster|kms_key|opensearch_domain|elasticsearch_domain|"
    r"docdb_cluster|neptune_cluster|msk_cluster|backup_vault|secretsmanager_secret|route53_zone)$",
    r"^google_(sql_database_instance|sql_database|storage_bucket|compute_disk|bigquery_dataset|bigquery_table|"
    r"spanner_instance|spanner_database|kms_crypto_key|filestore_instance|redis_instance|dns_managed_zone)$",
    r"^azurerm_(storage_account|mssql_database|mssql_server|postgresql_flexible_server|mysql_flexible_server|"
    r"cosmosdb_account|managed_disk|key_vault|redis_cache|dns_zone)$",
    r"^(kubernetes_persistent_volume|kubernetes_persistent_volume_claim|kubernetes_namespace)(_v1)?$",
]

TAGGABLE_ATTRS = ("tags", "labels")
OPEN_CIDRS = {"0.0.0.0/0", "::/0"}


@dataclass
class Finding:
    severity: str
    rule: str
    address: str
    message: str


@dataclass
class Report:
    terraform_version: str = ""
    counts: dict[str, int] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    drift: list[str] = field(default_factory=list)
    output_changes: list[str] = field(default_factory=list)

    @property
    def max_severity(self) -> str:
        if not self.findings:
            return "none"
        return max((f.severity for f in self.findings), key=SEVERITY_ORDER.__getitem__)

    def to_dict(self) -> dict:
        return {
            "terraform_version": self.terraform_version,
            "counts": self.counts,
            "max_severity": self.max_severity,
            "findings": [asdict(f) for f in self.findings],
            "drift": self.drift,
            "output_changes": self.output_changes,
        }


def classify(actions: list[str]) -> str:
    """Map a plan ``actions`` list to one word."""
    a = list(actions or [])
    if a == ["no-op"] or not a:
        return "no-op"
    if a == ["create"]:
        return "create"
    if a == ["read"]:
        return "read"
    if a == ["update"]:
        return "update"
    if a == ["delete"]:
        return "delete"
    if sorted(a) == ["create", "delete"]:
        return "replace"
    if a == ["forget"]:
        return "forget"
    return "+".join(a)


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_strings(v)


def _policy_documents(after: dict) -> list[dict]:
    docs = []
    for key in ("policy", "assume_role_policy", "inline_policy"):
        raw = after.get(key)
        candidates = raw if isinstance(raw, list) else [raw]
        for c in candidates:
            if isinstance(c, dict):
                c = c.get("policy")
            if isinstance(c, str) and c.strip().startswith("{"):
                try:
                    docs.append(json.loads(c))
                except json.JSONDecodeError:
                    continue
    return docs


def _wildcard_allow(doc: dict) -> bool:
    stmts = doc.get("Statement", [])
    if isinstance(stmts, dict):
        stmts = [stmts]
    for s in stmts:
        if not isinstance(s, dict) or s.get("Effect") != "Allow":
            continue
        actions = s.get("Action", [])
        actions = [actions] if isinstance(actions, str) else actions
        resources = s.get("Resource", [])
        resources = [resources] if isinstance(resources, str) else resources
        if any(a == "*" or a.endswith(":*") for a in actions) and "*" in resources:
            return True
        if "*" in actions:
            return True
    return False


def _open_ingress(rtype: str, after: dict) -> bool:
    if rtype == "aws_security_group":
        for rule in after.get("ingress") or []:
            cidrs = set(rule.get("cidr_blocks") or []) | set(rule.get("ipv6_cidr_blocks") or [])
            if cidrs & OPEN_CIDRS:
                return True
    if rtype == "aws_security_group_rule" and after.get("type") == "ingress":
        cidrs = set(after.get("cidr_blocks") or []) | set(after.get("ipv6_cidr_blocks") or [])
        return bool(cidrs & OPEN_CIDRS)
    if rtype == "aws_vpc_security_group_ingress_rule":
        return after.get("cidr_ipv4") in OPEN_CIDRS or after.get("cidr_ipv6") in OPEN_CIDRS
    if rtype == "google_compute_firewall":
        return after.get("direction", "INGRESS") == "INGRESS" and bool(set(after.get("source_ranges") or []) & OPEN_CIDRS)
    if rtype in ("azurerm_network_security_rule",):
        return after.get("direction") == "Inbound" and after.get("access") == "Allow" and \
            after.get("source_address_prefix") in {"*", "0.0.0.0/0", "Internet", "Any"}
    return False


def analyse(plan: dict, require_tags: list[str] | None = None,
            stateful_patterns: list[str] | None = None) -> Report:
    if not isinstance(plan, dict) or "format_version" not in plan:
        raise ValueError("not a plan JSON document (missing format_version); use `terraform show -json plan.out`")
    stateful = [re.compile(p) for p in (stateful_patterns or DEFAULT_STATEFUL)]
    rep = Report(terraform_version=str(plan.get("terraform_version", "")))
    counts: dict[str, int] = {}
    require_tags = [t for t in (require_tags or []) if t]

    for rc in plan.get("resource_changes", []) or []:
        if rc.get("mode") == "data":
            continue
        address, rtype = rc.get("address", "?"), rc.get("type", "")
        change = rc.get("change") or {}
        kind = classify(change.get("actions", []))
        counts[kind] = counts.get(kind, 0) + 1
        after = change.get("after") or {}
        before = change.get("before") or {}
        is_stateful = any(p.search(rtype) for p in stateful)

        if kind == "delete":
            sev = "high" if is_stateful else "medium"
            rep.findings.append(Finding(sev, "delete", address, f"{rtype} will be destroyed"))
        elif kind == "replace":
            order = "create-before-destroy" if change.get("actions", [None])[0] == "create" else "destroy-before-create"
            sev = "high" if is_stateful else "medium"
            why = rc.get("action_reason") or ""
            paths = change.get("replace_paths") or []
            detail = f" (forced by {', '.join('.'.join(map(str, p)) for p in paths)})" if paths else ""
            rep.findings.append(Finding(sev, "replace", address,
                                        f"{rtype} will be replaced, {order}{detail}{'; reason: ' + why if why else ''}"))
        elif kind == "forget":
            rep.findings.append(Finding("low", "forget", address, f"{rtype} will be removed from state but not destroyed"))

        if kind in ("create", "update", "replace") and isinstance(after, dict):
            if any(_wildcard_allow(d) for d in _policy_documents(after)):
                rep.findings.append(Finding("high", "iam-wildcard", address,
                                            "policy allows '*' actions or '*' actions on '*' resources"))
            if _open_ingress(rtype, after):
                rep.findings.append(Finding("high", "open-ingress", address, "ingress open to 0.0.0.0/0 or ::/0"))
            if rtype == "aws_s3_bucket_public_access_block":
                off = [k for k in ("block_public_acls", "block_public_policy", "ignore_public_acls",
                                   "restrict_public_buckets") if after.get(k) is False]
                if off:
                    rep.findings.append(Finding("high", "s3-public-access", address, f"public access block disabled: {', '.join(off)}"))
            if rtype == "aws_s3_bucket_acl" and str(after.get("acl", "")).startswith("public-"):
                rep.findings.append(Finding("high", "s3-public-acl", address, f"bucket ACL {after.get('acl')}"))
            if after.get("deletion_protection") is False and before.get("deletion_protection") is True:
                rep.findings.append(Finding("high", "deletion-protection-off", address, "deletion_protection turned off"))
            if after.get("skip_final_snapshot") is True and is_stateful:
                rep.findings.append(Finding("medium", "no-final-snapshot", address, "skip_final_snapshot = true"))
            if after.get("publicly_accessible") is True:
                rep.findings.append(Finding("high", "publicly-accessible", address, "publicly_accessible = true"))
            if require_tags and any(attr in after for attr in TAGGABLE_ATTRS):
                tags: dict = {}
                for attr in ("tags_all", "tags", "labels", "effective_labels"):
                    if isinstance(after.get(attr), dict):
                        tags.update(after[attr])
                unknown = change.get("after_unknown") or {}
                if unknown.get("tags_all") is True:
                    tags.update({k: "(known after apply)" for k in require_tags})
                missing = [t for t in require_tags if t not in tags]
                if missing:
                    rep.findings.append(Finding("low", "missing-tags", address, f"missing required tags: {', '.join(missing)}"))

    for rc in plan.get("resource_drift", []) or []:
        rep.drift.append(f"{rc.get('address')} ({classify((rc.get('change') or {}).get('actions', []))} outside Terraform)")
    for name, oc in (plan.get("output_changes") or {}).items():
        kind = classify(oc.get("actions", []))
        if kind != "no-op":
            rep.output_changes.append(f"{name}: {kind}")
    if rep.drift:
        rep.findings.append(Finding("info", "drift", "(plan)", f"{len(rep.drift)} resource(s) changed outside Terraform"))
    rep.counts = dict(sorted(counts.items()))
    rep.findings.sort(key=lambda f: (-SEVERITY_ORDER[f.severity], f.address))
    return rep


def to_markdown(rep: Report) -> str:
    lines = ["### Plan risk report", ""]
    summary = ", ".join(f"{v} {k}" for k, v in rep.counts.items() if k != "no-op") or "no changes"
    lines.append(f"**Changes:** {summary}. **Highest finding:** {rep.max_severity}.")
    if rep.terraform_version:
        lines.append(f"Plan produced by version {rep.terraform_version}.")
    if rep.findings:
        lines += ["", "| Severity | Rule | Address | Detail |", "|---|---|---|---|"]
        for f in rep.findings:
            lines.append(f"| {f.severity} | {f.rule} | `{f.address}` | {f.message} |")
    if rep.drift:
        lines += ["", "**Drift detected:**"] + [f"- {d}" for d in rep.drift]
    if rep.output_changes:
        lines += ["", "**Output changes:**"] + [f"- {o}" for o in rep.output_changes]
    lines += ["", "_Heuristic review aid. A clean report does not mean the plan is safe to apply._"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("plan_json")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--fail-on", choices=["low", "medium", "high", "never"], default="high")
    ap.add_argument("--require-tags", default="", help="comma-separated tag keys every taggable resource must carry")
    ap.add_argument("--stateful-pattern", action="append", help="regex of resource types treated as stateful (repeatable)")
    a = ap.parse_args(argv)
    try:
        with open(a.plan_json, encoding="utf-8") as fh:
            rep = analyse(json.load(fh), [t.strip() for t in a.require_tags.split(",")], a.stateful_pattern)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(rep.to_dict(), indent=2) if a.format == "json" else to_markdown(rep), end="" if a.format == "md" else "\n")
    if a.fail_on == "never" or rep.max_severity == "none":
        return 0
    return 1 if SEVERITY_ORDER[rep.max_severity] >= SEVERITY_ORDER[a.fail_on] else 0


if __name__ == "__main__":
    raise SystemExit(main())
