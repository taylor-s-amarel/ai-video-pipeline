#!/usr/bin/env python3
"""Turn rough incident notes into a sorted UTC timeline with detection/mitigation/resolution durations.

Input lines (one event per line; '#' comments ignored)::

    2026-10-10 14:02 UTC [detected] HighErrorRate fired for checkout
    14:05 [acknowledged] on-call acked
    13:52 [started] deploy v1.4.2 rolled out (impact start, found later)
    14:20 [mitigated] rolled back to v1.4.1
    2026-10-10T15:00:00Z [resolved] error rate at baseline for 30 min

Bare ``HH:MM`` times use the date of the nearest preceding full timestamp (or ``--date``) and roll
over midnight when a time jumps back by more than 12 hours. Recognised tags: started, detected,
acknowledged, declared, escalated, mitigated, resolved; anything else is kept as a note.

Usage::

    python incident_timeline_builder.py notes.txt [--date 2026-10-10] [--json]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from dataclasses import dataclass

UTC = _dt.timezone.utc
MILESTONES = ("started", "detected", "acknowledged", "declared", "escalated", "mitigated", "resolved")
ALIASES = {"start": "started", "impact": "started", "detect": "detected", "alert": "detected", "ack": "acknowledged",
           "acked": "acknowledged", "declare": "declared", "escalate": "escalated", "mitigate": "mitigated",
           "fixed": "mitigated", "resolve": "resolved", "closed": "resolved"}
FULL = re.compile(r"^(\d{4}-\d{2}-\d{2})[T ](\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?\s*(Z|UTC|[+-]\d{2}:?\d{2})?\s*")
SHORT = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(Z|UTC)?\s*")
TAG = re.compile(r"^\[([A-Za-z-]+)\]\s*")


@dataclass
class Event:
    at: _dt.datetime
    tag: str
    text: str
    line: int


def _tz(token: str | None) -> _dt.tzinfo:
    if not token or token in {"Z", "UTC"}:
        return UTC
    sign = 1 if token[0] == "+" else -1
    digits = token[1:].replace(":", "")
    return _dt.timezone(sign * _dt.timedelta(hours=int(digits[:2]), minutes=int(digits[2:])))


def parse(text: str, base_date: _dt.date | None = None) -> list[Event]:
    events: list[Event] = []
    current_date = base_date
    last: _dt.datetime | None = None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = FULL.match(line)
        if m:
            d, hh, mm, ss, tz = m.groups()
            at = _dt.datetime.fromisoformat(f"{d}T{int(hh):02d}:{mm}:{ss or '00'}").replace(tzinfo=_tz(tz)).astimezone(UTC)
            current_date = at.date()
        else:
            m = SHORT.match(line)
            if not m:
                raise ValueError(f"line {n}: no timestamp at start: {raw!r}")
            if current_date is None:
                raise ValueError(f"line {n}: bare time before any date; pass --date or start with a full timestamp")
            hh, mm, ss, _ = m.groups()
            at = _dt.datetime.combine(current_date, _dt.time(int(hh), int(mm), int(ss or 0)), tzinfo=UTC)
            if last is not None and (last - at) > _dt.timedelta(hours=12):
                at += _dt.timedelta(days=1)
                current_date = at.date()
        rest = line[m.end():]
        tag = "note"
        t = TAG.match(rest)
        if t:
            word = t.group(1).lower()
            tag = ALIASES.get(word, word)
            rest = rest[t.end():]
        events.append(Event(at, tag, rest.strip(), n))
        last = at
    return sorted(events, key=lambda e: (e.at, e.line))


def first(events: list[Event], tag: str) -> _dt.datetime | None:
    return next((e.at for e in events if e.tag == tag), None)


def metrics(events: list[Event]) -> dict[str, float | None]:
    """Durations in minutes; None when a milestone is missing."""
    s, d, a, mi, r = (first(events, t) for t in ("started", "detected", "acknowledged", "mitigated", "resolved"))

    def mins(x, y):
        return round((y - x).total_seconds() / 60, 1) if x and y else None

    return {
        "time_to_detect_min": mins(s, d),
        "time_to_acknowledge_min": mins(d, a),
        "time_to_mitigate_min": mins(s or d, mi),
        "time_to_resolve_min": mins(s or d, r),
        "customer_impact_min": mins(s or d, mi or r),
    }


def problems(events: list[Event]) -> list[str]:
    out = []
    for tag in ("detected", "mitigated", "resolved"):
        if first(events, tag) is None:
            out.append(f"no [{tag}] event")
    order = [t for t in ("started", "detected", "mitigated", "resolved") if first(events, t)]
    for x, y in zip(order, order[1:]):
        if first(events, x) > first(events, y):
            out.append(f"[{x}] is after [{y}]; check the clock or timezone")
    return out


def to_markdown(events: list[Event]) -> str:
    rows = ["| Time (UTC) | Event | Detail |", "|---|---|---|"]
    rows += [f"| {e.at:%Y-%m-%d %H:%M:%S} | {e.tag} | {e.text.replace('|', '/')} |" for e in events]
    m = metrics(events)
    rows += ["", "| Measure | Minutes |", "|---|---|"]
    rows += [f"| {k.replace('_min', '').replace('_', ' ')} | {'n/a' if v is None else v} |" for k, v in m.items()]
    issues = problems(events)
    if issues:
        rows += ["", "**Gaps:** " + "; ".join(issues)]
    return "\n".join(rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("notes")
    ap.add_argument("--date", help="date for bare HH:MM lines before any full timestamp (YYYY-MM-DD, UTC)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    text = sys.stdin.read() if a.notes == "-" else open(a.notes, encoding="utf-8").read()
    events = parse(text, _dt.date.fromisoformat(a.date) if a.date else None)
    if a.json:
        print(json.dumps({"events": [{"at": e.at.isoformat().replace("+00:00", "Z"), "tag": e.tag, "text": e.text} for e in events],
                          "metrics": metrics(events), "problems": problems(events)}, indent=2))
    else:
        print(to_markdown(events), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
