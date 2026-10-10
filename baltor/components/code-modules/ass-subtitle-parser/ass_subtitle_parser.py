"""Read .ass/.ssa scripts: script info, styles and events as dicts.

Fields are mapped through each section's own ``Format:`` line, so files with
reordered or missing columns parse correctly. The Text field keeps commas
(it is always the last field). ``plain_text`` strips override blocks and
converts ``\\N``/``\\n``/``\\h`` to text, which is what you need for
transcripts, search and caption QA.

Usage::

    from ass_subtitle_parser import parse, plain_text, events_as_cues
    doc = parse(open("subs.ass", encoding="utf-8-sig").read())
    doc["info"]["PlayResY"], doc["styles"]["Default"]["Fontsize"]
    for start, end, text in events_as_cues(doc): ...
"""

from __future__ import annotations

import re

_TIME = re.compile(r"^(\d+):(\d{2}):(\d{2})[.:](\d{2,3})$")
_OVERRIDE = re.compile(r"(?<!\\)\{[^}]*\}")


def parse_time(t: str) -> float:
    m = _TIME.match(t.strip())
    if not m:
        raise ValueError(f"bad ASS time {t!r}")
    h, mi, s, frac = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(s) + int(frac) / (10 ** len(frac))


def parse(text: str) -> dict:
    doc: dict = {"info": {}, "styles": {}, "events": [], "other": {}}
    section = None
    fmt: dict[str, list[str]] = {}
    for raw in text.lstrip("﻿").replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if section == "script info":
            doc["info"][key] = int(value) if value.lstrip("-").isdigit() else value
        elif section in ("v4+ styles", "v4 styles"):
            if key == "Format":
                fmt["styles"] = [f.strip() for f in value.split(",")]
            elif key == "Style":
                names = fmt.get("styles")
                if not names:
                    raise ValueError("Style line before its Format line")
                parts = [p.strip() for p in value.split(",", len(names) - 1)]
                doc["styles"][parts[0]] = dict(zip(names, parts))
        elif section == "events":
            if key == "Format":
                fmt["events"] = [f.strip() for f in value.split(",")]
            elif key in ("Dialogue", "Comment"):
                names = fmt.get("events")
                if not names:
                    raise ValueError("Dialogue line before its Format line")
                parts = value.split(",", len(names) - 1)
                ev = dict(zip(names, (p.strip() if n != "Text" else p for n, p in zip(names, parts))))
                ev["type"] = key
                ev["start_s"] = parse_time(ev["Start"])
                ev["end_s"] = parse_time(ev["End"])
                doc["events"].append(ev)
        else:
            doc["other"].setdefault(section or "", []).append(line)
    return doc


def plain_text(ass_text: str) -> str:
    t = _OVERRIDE.sub("", ass_text)
    t = t.replace("\\N", "\n").replace("\\n", "\n").replace("\\h", " ")
    return t.replace("\\{", "{").replace("\\}", "}")


def events_as_cues(doc: dict, include_comments: bool = False) -> list[tuple[float, float, str]]:
    out = []
    for ev in doc["events"]:
        if ev["type"] == "Comment" and not include_comments:
            continue
        out.append((ev["start_s"], ev["end_s"], plain_text(ev.get("Text", ""))))
    return sorted(out)
