#!/usr/bin/env python3
"""Lint Prometheus alerting/recording rules and metric names against common conventions.

Usage::

    python prometheus_rules_lint.py rules/*.yml [--fail-on medium] [--json]
    curl -s localhost:8080/metrics | python prometheus_rules_lint.py --metrics -

Rule files need PyYAML (imported lazily); metric-name linting of the text exposition format is
standard library only. Conventions follow the Prometheus documentation pages "Metric and label
naming", "Recording rules" and "Alerting rules". Run ``promtool check rules`` too: it validates PromQL.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass

SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3}
RECORD_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*:[a-zA-Z_][a-zA-Z0-9_:]*:[a-zA-Z0-9_]+$")
CAMEL = re.compile(r"^[A-Z][A-Za-z0-9]*(_[A-Za-z0-9]+)*$")
RATE_ON = re.compile(r"\b(?:rate|irate|increase)\(\s*([a-zA-Z_:][a-zA-Z0-9_:]*)")
RANGE = re.compile(r"\[(\d+)([smhdwy])\]")
METRIC_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")
BAD_UNITS = {"_milliseconds": "_seconds", "_ms": "_seconds", "_microseconds": "_seconds", "_minutes": "_seconds",
             "_hours": "_seconds", "_kilobytes": "_bytes", "_kb": "_bytes", "_megabytes": "_bytes", "_mb": "_bytes",
             "_percent": "_ratio", "_percentage": "_ratio"}
DEFAULT_SEVERITIES = {"page", "ticket", "critical", "warning", "info"}


@dataclass
class Finding:
    rule: str
    severity: str
    location: str
    message: str


def lint_rules(doc: dict, name: str = "rules", allowed_severities: set[str] | None = None) -> list[Finding]:
    allowed = allowed_severities or DEFAULT_SEVERITIES
    out: list[Finding] = []
    groups = (doc or {}).get("groups")
    if not isinstance(groups, list):
        return [Finding("PR007", "high", name, "file has no 'groups' list")]
    for gi, g in enumerate(groups):
        gname = g.get("name")
        gloc = f"{name}:groups[{gi}]{'(' + gname + ')' if gname else ''}"
        if not gname:
            out.append(Finding("PR007", "high", gloc, "group has no name"))
        alerts = Counter(r.get("alert") for r in g.get("rules") or [] if r.get("alert"))
        for dup, n in alerts.items():
            if n > 1:
                out.append(Finding("PR007", "medium", gloc, f"alert '{dup}' defined {n} times in one group"))
        for ri, r in enumerate(g.get("rules") or []):
            expr = str(r.get("expr", "")).strip()
            label = r.get("alert") or r.get("record") or f"rules[{ri}]"
            loc = f"{gloc}:{label}"
            if not expr:
                out.append(Finding("PR007", "high", loc, "empty expr"))
            for metric in RATE_ON.findall(expr):
                if not re.search(r"(_total|_count|_sum|_bucket)$", metric) and ":" not in metric:
                    out.append(Finding("PR006", "low", loc, f"rate()/increase() on '{metric}', which is not named like a counter (_total)"))
            for n, unit in RANGE.findall(expr):
                if unit == "s" and int(n) < 60:
                    out.append(Finding("PR008", "low", loc, f"range [{n}s] is shorter than 4x a 15s scrape interval; rate() may return nothing"))
            if "record" in r:
                if not RECORD_NAME.match(str(r["record"])):
                    out.append(Finding("PR004", "low", loc, "recording rule name should follow level:metric:operations"))
                continue
            if "alert" not in r:
                out.append(Finding("PR007", "high", loc, "rule has neither 'alert' nor 'record'"))
                continue
            if not CAMEL.match(str(r["alert"])):
                out.append(Finding("PR005", "info", loc, "alert names are conventionally CamelCase"))
            if not r.get("for") or str(r.get("for")) in {"0", "0s", "0m"}:
                out.append(Finding("PR001", "low", loc, "no 'for' duration; a single bad scrape will page"))
            labels = r.get("labels") or {}
            sev = labels.get("severity")
            if not sev:
                out.append(Finding("PR002", "medium", loc, "missing labels.severity; routing cannot tell a page from a ticket"))
            elif str(sev) not in allowed:
                out.append(Finding("PR002", "low", loc, f"severity '{sev}' not in {sorted(allowed)}"))
            ann = r.get("annotations") or {}
            if not ann.get("summary"):
                out.append(Finding("PR003", "medium", loc, "missing annotations.summary"))
            if not ann.get("description"):
                out.append(Finding("PR003", "low", loc, "missing annotations.description (say what is broken and the impact)"))
            if str(sev) in {"page", "critical"} and not ann.get("runbook_url"):
                out.append(Finding("PR003", "medium", loc, "paging alert without annotations.runbook_url"))
    return sorted(out, key=lambda f: (-SEVERITY[f.severity], f.location))


def lint_metric_names(exposition: str) -> list[Finding]:
    """Check `# TYPE` lines of the Prometheus text exposition format."""
    out: list[Finding] = []
    for line in exposition.splitlines():
        m = re.match(r"#\s*TYPE\s+(\S+)\s+(\S+)", line)
        if not m:
            continue
        name, mtype = m.groups()
        if ":" in name:
            out.append(Finding("PM001", "medium", name, "colons are reserved for recording rules"))
        elif not METRIC_NAME.match(name):
            out.append(Finding("PM001", "low", name, "use lower snake_case metric names"))
        if mtype == "counter" and not name.endswith("_total"):
            out.append(Finding("PM002", "low", name, "counter names should end in _total"))
        if mtype != "counter" and name.endswith("_total"):
            out.append(Finding("PM002", "low", name, f"{mtype} named like a counter (_total)"))
        for bad, good in BAD_UNITS.items():
            if name.endswith(bad) or name.endswith(bad + "_total"):
                out.append(Finding("PM003", "low", name, f"use base units: {bad} -> {good}"))
        if re.search(r"_(2|4|5)\d\d(_|$)|_(get|post|put|delete)(_|$)", name):
            out.append(Finding("PM004", "low", name, "status codes / methods belong in labels, not metric names"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--metrics", action="store_true", help="inputs are /metrics text exposition, not rule files")
    ap.add_argument("--fail-on", choices=list(SEVERITY), default="medium")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    findings: list[Finding] = []
    for path in a.files:
        text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
        if a.metrics:
            findings += lint_metric_names(text)
        else:
            import yaml  # type: ignore  # lazy

            findings += lint_rules(yaml.safe_load(text), path)
    if a.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.severity.upper():6} {f.rule} {f.location}: {f.message}")
        print(f"{len(findings)} finding(s)")
    return 1 if any(SEVERITY[f.severity] >= SEVERITY[a.fail_on] for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
