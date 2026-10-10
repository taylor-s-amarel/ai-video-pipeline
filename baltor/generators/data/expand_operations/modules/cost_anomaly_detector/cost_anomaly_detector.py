#!/usr/bin/env python3
"""Find daily cloud-cost spikes per service with a robust (median/MAD) baseline.

Input CSV with a date column, a group column and a cost column (names configurable)::

    date,service,cost
    2026-10-01,AmazonEC2,412.10
    ...

Usage::

    python cost_anomaly_detector.py costs.csv [--date-col date] [--group-col service] [--cost-col cost]
        [--window 14] [--z 4] [--min-delta 25] [--min-ratio 1.3] [--weekday] [--json]

A day is anomalous when its cost exceeds the trailing-window median by at least ``--z`` robust
standard deviations (1.4826 * MAD), by at least ``--min-delta`` currency units AND by at least
``--min-ratio`` times the median, so tiny services do not page anyone. ``--weekday`` compares each day
only with the same weekday (for weekly-seasonal workloads). Exit 1 when anomalies are found.
Standard library only; works on FOCUS exports (``ChargePeriodStart``, ``ServiceName``, ``EffectiveCost``).
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass


@dataclass
class Anomaly:
    group: str
    date: str
    cost: float
    baseline: float
    delta: float
    ratio: float
    robust_z: float


def load(path_or_rows, date_col: str, group_col: str, cost_col: str) -> dict[str, dict[_dt.date, float]]:
    rows = path_or_rows
    if isinstance(path_or_rows, str):
        with open(path_or_rows, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    series: dict[str, dict[_dt.date, float]] = defaultdict(lambda: defaultdict(float))
    for r in rows:
        day = _dt.date.fromisoformat(str(r[date_col])[:10])
        series[r.get(group_col) or "(none)"][day] += float(r[cost_col] or 0)
    return series


def detect(series: dict[str, dict[_dt.date, float]], window: int = 14, z: float = 4.0, min_delta: float = 25.0,
           min_ratio: float = 1.3, weekday: bool = False, min_history: int = 7) -> list[Anomaly]:
    out: list[Anomaly] = []
    for group, days in series.items():
        if not days:
            continue
        start, end = min(days), max(days)
        filled = {start + _dt.timedelta(d): days.get(start + _dt.timedelta(d), 0.0) for d in range((end - start).days + 1)}
        ordered = sorted(filled)
        for i, day in enumerate(ordered):
            history = [filled[d] for d in ordered[max(0, i - (window * 7 if weekday else window)):i]
                       if not weekday or d.weekday() == day.weekday()]
            if len(history) < (max(2, min_history // 7) if weekday else min_history):
                continue
            med = statistics.median(history)
            mad = statistics.median(abs(x - med) for x in history)
            sigma = 1.4826 * mad
            cost = filled[day]
            delta = cost - med
            rz = delta / sigma if sigma > 0 else (float("inf") if delta > 0 else 0.0)
            ratio = cost / med if med > 0 else float("inf")
            if rz >= z and delta >= min_delta and ratio >= min_ratio:
                out.append(Anomaly(group, day.isoformat(), round(cost, 2), round(med, 2), round(delta, 2),
                                   round(ratio, 2) if ratio != float("inf") else ratio, round(rz, 1) if rz != float("inf") else rz))
    return sorted(out, key=lambda a: (-a.delta, a.date))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv")
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--group-col", default="service")
    ap.add_argument("--cost-col", default="cost")
    ap.add_argument("--window", type=int, default=14)
    ap.add_argument("--z", type=float, default=4.0)
    ap.add_argument("--min-delta", type=float, default=25.0)
    ap.add_argument("--min-ratio", type=float, default=1.3)
    ap.add_argument("--weekday", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    anomalies = detect(load(a.csv, a.date_col, a.group_col, a.cost_col), a.window, a.z, a.min_delta, a.min_ratio, a.weekday)
    if a.json:
        print(json.dumps([asdict(x) for x in anomalies], indent=2, default=str))
    else:
        for x in anomalies:
            print(f"{x.date} {x.group}: {x.cost:.2f} vs baseline {x.baseline:.2f} (+{x.delta:.2f}, x{x.ratio}, z={x.robust_z})")
        print(f"{len(anomalies)} anomaly(ies)")
    return 1 if anomalies else 0


if __name__ == "__main__":
    sys.exit(main())
