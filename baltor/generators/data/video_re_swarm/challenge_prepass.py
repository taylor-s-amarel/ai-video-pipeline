#!/usr/bin/env python3
"""Mechanical pre-pass for the video RE challenger: checks analyst answers before the semantic challenge.

Usage:
    python3 challenge_prepass.py answers.json --evidence evidence.json [--bank RULES.md|questions.json|DIR ...] [--out report.json]

answers.json is a JSON array of analyst answers (contract video_re_analyst_answer), or an object with an
"answers" or "surviving" array. --bank accepts the lens RULES.md files (their machine-readable block),
questions.json files, or directories containing either. Standard library only.

Each answer gets verdict "reject" (must be removed), "flag" (challenge it) or "pass" (still challenge a
sample), the list of issues, and the highest confidence its method allows.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

METHOD_CAP = {"measured": 0.95, "observed": 0.85, "inferred": 0.65, "assumed": 0.3}
TASTE = re.compile(r"\b(beautiful|stunning|gorgeous|engaging|captivating|compelling|viral|cinematic|amazing|"
                   r"professional|high[- ]quality|perfect|works well|ugly|boring|catchy|"
                   r"eye[- ]catching|polished|premium|aesthetic)\b", re.I)
ABSOLUTE = re.compile(r"\b(always|every|never|all)\b", re.I)
IDENTITY = re.compile(r"\b(male|female|man's|woman's|boy|girl|years? old|ethnic\w*|accent|nationality|"
                      r"race|celebrity|famous)\b", re.I)
QUOTE = re.compile(r"\"([^\"]+)\"|“([^”]+)”|'([^']{12,})'")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
NUMERIC_TYPES = {"number", "integer", "ratio", "seconds", "ms", "range"}


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_answers(path: str) -> list[dict]:
    data = load_json(path)
    if isinstance(data, dict):
        data = data.get("answers") or data.get("surviving") or []
    return [a for a in data if isinstance(a, dict)]


def load_bank(paths: list[str]) -> dict[str, dict]:
    bank: dict[str, dict] = {}
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files += sorted(p.rglob("questions.json")) + sorted(p.rglob("*.md"))
        elif p.exists():
            files.append(p)
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        items = []
        try:
            if f.suffix == ".json":
                data = json.loads(text)
                if isinstance(data, dict) and data.get("spec") == "baltor.video-re-questions/v1":
                    items = data.get("questions", [])
            else:
                m = re.search(r"<!-- machine-readable bank -->\s*```json\s*(.*?)```", text, re.S)
                if m:
                    items = json.loads(m.group(1))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue  # not a question bank
        for q in items:
            if isinstance(q, dict) and re.fullmatch(r"[a-z_]+-[0-9]{3}", str(q.get("id", ""))):
                bank[q["id"]] = {"ir_path": q.get("ir_path"), "answer_type": q.get("answer_type"),
                                 "choices": q.get("choices")}
    return bank


def caption_ngrams(evidence: dict, n: int = 7) -> set[tuple[str, ...]]:
    grams: set[tuple[str, ...]] = set()
    for c in evidence.get("captions") or []:
        words = re.findall(r"[a-z0-9']+", str(c.get("text", "")).lower())
        if set(words) <= {"word", "n"}:
            continue  # masked ('Word {n} word') or empty captions carry no source words
        grams.update(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
    return grams


def text_of(answer: dict) -> str:
    ev = answer.get("evidence") or {}
    return json.dumps(answer.get("answer"), ensure_ascii=False) + " " + str(ev.get("note", ""))


def type_problem(value, atype: str | None, choices) -> str | None:
    if atype is None or (isinstance(value, str) and value.strip().lower() == "not determinable"):
        return None
    num = value.get("value") if isinstance(value, dict) else None
    if atype in NUMERIC_TYPES and not isinstance(num, (int, float)):
        return f"answer_type {atype} needs an object with a numeric 'value'"
    if atype == "ratio" and isinstance(num, (int, float)) and not 0 <= num <= 1:
        return "ratio outside 0..1"
    if atype == "distribution" and not (isinstance(value, dict) and isinstance(value.get("median"), (int, float))):
        return "distribution needs a numeric 'median'"
    if atype == "boolean" and not isinstance(value, bool):
        return "boolean answer is not true/false"
    if atype == "enum" and choices and value not in choices:
        return f"enum answer not in choices {choices}"
    if atype == "color" and not (isinstance(value, str) and HEX.match(value)):
        return "color must be #RRGGBB"
    if atype == "palette" and not (isinstance(value, list) and value and all(isinstance(v, str) and HEX.match(v) for v in value)):
        return "palette must be a non-empty list of #RRGGBB"
    if atype in {"timestamps", "list", "segments", "beats", "layers"} and not isinstance(value, list):
        return f"{atype} must be a JSON array"
    if atype in {"text", "pattern", "rule"} and not isinstance(value, str):
        return f"{atype} must be a string"
    if atype == "rule" and isinstance(value, str) and len(value) > 400:
        return "rule longer than 400 characters"
    if atype == "pattern" and isinstance(value, str) and "{" not in value:
        return "pattern has no {slot}"
    return None


def check(answer: dict, duration: float | None, bank: dict, grams: set) -> dict:
    issues: list[str] = []
    reject = False
    qid = answer.get("question_id", "?")
    ev = answer.get("evidence") or {}
    for key in ("lens", "question_id", "answer", "ir_path"):
        if key not in answer:
            issues.append(f"missing field {key}")
            reject = True
    method, conf = ev.get("method"), ev.get("confidence")
    if method not in METHOD_CAP:
        issues.append(f"unknown method {method!r}")
        reject = True
    if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
        issues.append("confidence missing or outside 0..1")
        reject = True
    cap = METHOD_CAP.get(method, 0.3)
    if isinstance(conf, (int, float)) and conf > cap:
        issues.append(f"confidence {conf} above the {method} band cap {cap}")
    if answer.get("lens") and not str(qid).startswith(f"{answer['lens']}-"):
        issues.append("question_id does not belong to the lens")
        reject = True
    if method == "measured" and not ev.get("tool"):
        issues.append("measured answer names no tool")
    nd = isinstance(answer.get("answer"), str) and answer["answer"].strip().lower() == "not determinable"
    if nd and isinstance(conf, (int, float)) and conf > 0.3:
        issues.append("'not determinable' with confidence above 0.3")
    ts = ev.get("timestamps_s") or []
    if duration is not None:
        bad = [t for t in ts if not isinstance(t, (int, float)) or t < 0 or t > duration + 0.05]
        if bad:
            issues.append(f"timestamps outside 0..{duration:.2f} s: {bad[:5]}")
            reject = True
    if method in {"observed", "measured"} and not ts and not nd:
        issues.append("no timestamps_s (fine only for whole-video measurements)")
    q = bank.get(qid)
    if q:
        if q["ir_path"] and answer.get("ir_path") != q["ir_path"]:
            issues.append(f"ir_path {answer.get('ir_path')} differs from the bank's {q['ir_path']}")
        tp = type_problem(answer.get("answer"), q["answer_type"], q["choices"])
        if tp:
            issues.append(tp)
    elif bank:
        issues.append("question_id not found in the bank")
    text = text_of(answer)
    for m in QUOTE.finditer(text):
        quoted = next(g for g in m.groups() if g)
        if len(quoted.split()) > 6:
            issues.append(f"quotes {len(quoted.split())} words of text (limit 6, never narration)")
            reject = True
    words = re.findall(r"[a-z0-9']+", text.lower())
    if any(tuple(words[i:i + 7]) in grams for i in range(len(words) - 6)):
        issues.append("contains 7+ consecutive words from the source captions")
        reject = True
    if TASTE.search(text):
        issues.append(f"taste word '{TASTE.search(text).group(0)}': restate as something measurable")
    if ABSOLUTE.search(text) and len(ts) < 3 and method in {"observed", "inferred"}:
        issues.append("absolute claim (all/every/never) backed by fewer than 3 timestamps")
    if IDENTITY.search(text):
        issues.append(f"possible identity or demographic description ('{IDENTITY.search(text).group(0)}'); check and remove")
    verdict = "reject" if reject else ("flag" if issues else "pass")
    return {"question_id": qid, "lens": answer.get("lens"), "verdict": verdict, "issues": issues,
            "confidence_cap": cap}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("answers")
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--bank", nargs="*", default=[])
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    evidence = load_json(a.evidence)
    duration = (evidence.get("source") or {}).get("duration_s")
    bank = load_bank(a.bank)
    grams = caption_ngrams(evidence)
    rows = [check(x, duration, bank, grams) for x in load_answers(a.answers)]
    seen: dict[str, int] = {}
    for r in rows:
        seen[r["question_id"]] = seen.get(r["question_id"], 0) + 1
    for r in rows:
        if seen[r["question_id"]] > 1:
            r["issues"].append("question answered more than once")
            r["verdict"] = "flag" if r["verdict"] == "pass" else r["verdict"]
    report = {"spec": "baltor.video-re-prepass/v1", "answers": len(rows),
              "counts": {v: sum(r["verdict"] == v for r in rows) for v in ("pass", "flag", "reject")},
              "bank_questions": len(bank), "rows": rows}
    out = json.dumps(report, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(out + "\n", encoding="utf-8")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
