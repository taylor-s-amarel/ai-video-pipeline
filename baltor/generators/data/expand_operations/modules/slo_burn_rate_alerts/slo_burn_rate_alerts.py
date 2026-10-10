#!/usr/bin/env python3
"""SLO error-budget arithmetic and multiwindow, multi-burn-rate alert generation.

    from slo_burn_rate_alerts import allowed_downtime, burn_rate, evaluate, prometheus_rules
    allowed_downtime(0.999, days=30)          # -> 0:43:12
    burn_rate(error_ratio=0.0144, target=0.999) # -> 14.4

The default policy is the starting point published in the Google SRE Workbook chapter "Alerting on SLOs"
for a 30-day window: page at burn rate 14.4 over 1h (short window 5m, 2% of budget), page at 6 over 6h
(30m, 5%), ticket at 1 over 3d (6h, 10%). Short windows are 1/12 of the long window.

CLI::

    python slo_burn_rate_alerts.py table --target 0.999 --days 30
    python slo_burn_rate_alerts.py rules --name checkout-availability --target 0.999 \
        --errors 'sum(rate(http_requests_total{job="checkout",code=~"5.."}[{w}]))' \
        --total  'sum(rate(http_requests_total{job="checkout"}[{w}]))' > slo-rules.yml
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from dataclasses import dataclass

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_duration(text: str) -> _dt.timedelta:
    """Parse Prometheus-style durations such as 5m, 1h, 3d, 1h30m."""
    parts = re.findall(r"(\d+)([smhdw])", text)
    if not parts or "".join(n + u for n, u in parts) != text:
        raise ValueError(f"bad duration {text!r}")
    return _dt.timedelta(seconds=sum(int(n) * _UNITS[u] for n, u in parts))


def format_duration(td: _dt.timedelta) -> str:
    secs = int(td.total_seconds())
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if secs % size == 0 and secs >= size:
            return f"{secs // size}{unit}"
    return f"{secs}s"


def _check_target(target: float) -> None:
    if not 0 < target < 1:
        raise ValueError("target must be a fraction strictly between 0 and 1, e.g. 0.999")


def allowed_downtime(target: float, days: float = 30) -> _dt.timedelta:
    """Time-based budget: how long the service may be fully down in the window."""
    _check_target(target)
    return _dt.timedelta(seconds=round((1 - target) * days * 86400))


def burn_rate(error_ratio: float, target: float) -> float:
    """How fast the budget is being spent: 1.0 spends exactly the whole budget over the SLO window."""
    _check_target(target)
    return error_ratio / (1 - target)


def budget_status(good: int, total: int, target: float) -> dict:
    """Event-based budget for the window so far."""
    _check_target(target)
    if total <= 0:
        return {"error_ratio": 0.0, "allowed_bad": 0.0, "bad": 0, "consumed": 0.0, "remaining": 1.0}
    bad = total - good
    allowed = (1 - target) * total
    consumed = bad / allowed if allowed else float("inf")
    return {"error_ratio": bad / total, "allowed_bad": allowed, "bad": bad,
            "consumed": consumed, "remaining": 1 - consumed}


@dataclass(frozen=True)
class AlertWindow:
    severity: str
    long: str
    short: str
    burn_rate: float

    def budget_fraction(self, slo_days: float = 30) -> float:
        return self.burn_rate * parse_duration(self.long).total_seconds() / (slo_days * 86400)


DEFAULT_POLICY = (
    AlertWindow("page", "1h", "5m", 14.4),
    AlertWindow("page", "6h", "30m", 6.0),
    AlertWindow("ticket", "3d", "6h", 1.0),
)


def threshold_for_budget(budget_fraction: float, long_window: str, slo_days: float = 30) -> float:
    """Burn rate that spends ``budget_fraction`` of the budget within ``long_window``."""
    return budget_fraction * slo_days * 86400 / parse_duration(long_window).total_seconds()


def evaluate(error_ratios: dict[str, float], target: float, policy=DEFAULT_POLICY) -> list[AlertWindow]:
    """Return the alert windows that fire: both long and short window burn rates exceed the threshold."""
    firing = []
    for w in policy:
        if w.long not in error_ratios or w.short not in error_ratios:
            raise KeyError(f"need error ratios for {w.long} and {w.short}")
        if burn_rate(error_ratios[w.long], target) > w.burn_rate and burn_rate(error_ratios[w.short], target) > w.burn_rate:
            firing.append(w)
    return firing


def _q(s: str) -> str:
    return json.dumps(s)  # JSON strings are valid YAML double-quoted scalars


def prometheus_rules(name: str, target: float, errors_expr: str, total_expr: str,
                     policy=DEFAULT_POLICY, labels: dict | None = None, runbook_url: str | None = None,
                     slo_days: float = 30) -> str:
    """Prometheus rule file (YAML) with one recording rule per window and one alert per policy row.

    ``errors_expr``/``total_expr`` contain ``{w}`` where the range goes, e.g. ``rate(x[{w}])``.
    """
    _check_target(target)
    if "{w}" not in errors_expr or "{w}" not in total_expr:
        raise ValueError("expressions must contain {w} for the range selector")
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    windows = sorted({w.long for w in policy} | {w.short for w in policy}, key=lambda d: parse_duration(d))
    labels = {"slo": name, **(labels or {})}
    lab = "".join(f"\n          {k}: {_q(str(v))}" for k, v in labels.items())
    out = ["groups:", f"  - name: {_q('slo-' + name + '-recording')}", "    rules:"]
    for w in windows:
        expr = f"({errors_expr.replace('{w}', w)}) / ({total_expr.replace('{w}', w)})"
        out += [f"      - record: slo:{slug}:error_ratio_rate{w}", f"        expr: {_q(expr)}",
                f"        labels:{lab}"]
    out += [f"  - name: {_q('slo-' + name + '-alerts')}", "    rules:"]
    budget = 1 - target
    for w in policy:
        thr = w.burn_rate * budget
        expr = (f"slo:{slug}:error_ratio_rate{w.long} > {w.burn_rate:g} * {budget:.6g}"
                f" and slo:{slug}:error_ratio_rate{w.short} > {w.burn_rate:g} * {budget:.6g}")
        pct = w.budget_fraction(slo_days) * 100
        out += [
            f"      - alert: {_q(f'SLOBurnRate_{slug}_{w.long}')}",
            f"        expr: {_q(expr)}",
            "        for: 2m" if w.severity == "page" else "        for: 15m",
            f"        labels:{lab}",
            f"          severity: {_q(w.severity)}",
            f"          long_window: {_q(w.long)}",
            "        annotations:",
            f"          summary: {_q(f'{name}: burning error budget at >{w.burn_rate:g}x over {w.long} (error ratio > {thr:.4%})')}",
            f"          description: {_q(f'At this rate {pct:.1f}% of the {slo_days:g}-day budget is gone in {w.long}. Target {target:.4%}.')}",
        ]
        if runbook_url:
            out.append(f"          runbook_url: {_q(runbook_url)}")
    return "\n".join(out) + "\n"


def table(target: float, days: float = 30) -> str:
    rows = [f"SLO target {target:.4%} over {days:g} days: allowed downtime {allowed_downtime(target, days)}",
            "severity  long  short  burn-rate  error-ratio>  budget-spent-in-long-window"]
    for w in DEFAULT_POLICY:
        rows.append(f"{w.severity:<9} {w.long:<5} {w.short:<6} {w.burn_rate:<10g} {w.burn_rate * (1 - target):<13.5%} {w.budget_fraction(days):.1%}")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("table")
    t.add_argument("--target", type=float, required=True)
    t.add_argument("--days", type=float, default=30)
    r = sub.add_parser("rules")
    r.add_argument("--name", required=True)
    r.add_argument("--target", type=float, required=True)
    r.add_argument("--errors", required=True)
    r.add_argument("--total", required=True)
    r.add_argument("--runbook-url")
    a = ap.parse_args(argv)
    if a.cmd == "table":
        print(table(a.target, a.days))
    else:
        sys.stdout.write(prometheus_rules(a.name, a.target, a.errors, a.total, runbook_url=a.runbook_url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
