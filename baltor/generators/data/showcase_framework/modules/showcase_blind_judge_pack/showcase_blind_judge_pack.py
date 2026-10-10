#!/usr/bin/env python3
"""Blind A/B judging packets for subjective showcase metrics, and merging the judgements.

``build`` pairs every included baseline run with every included Baltor run (or a
seeded sample), randomises which one is shown as A, copies only the declared
output files, redacts text that names Baltor or the catalogue items either arm
used, and writes one directory per packet::

    <packets-out>/README.md                instructions + output format for judges
    <packets-out>/<packet_id>/packet.json  shared prompt, rubric, criteria, scale, file lists
    <packets-out>/<packet_id>/A/...        outputs of one run
    <packets-out>/<packet_id>/B/...        outputs of the other run

The key that maps A and B back to runs is written separately to
``runs/<task>/_judging/key.json``. Give judges a copy of the packets directory
only, somewhere the key is not readable.

``merge`` checks every judgement (packet exists, scores on the scale, a
justification of at least 40 characters), unblinds them with the key, and writes
``runs/<task>/_judging/merged.json``: per run, the mean normalised rubric score
and the win share; overall, Baltor-preferred / baseline-preferred / tie counts,
position bias and inter-judge agreement. The ``blind_judge`` evaluator in
showcase_evaluators turns that file into metric values.

CLI::

    python3 showcase_blind_judge_pack.py build --root showcases --task ID [--metric NAME] [--both-orders] [--max-packets N]
    python3 showcase_blind_judge_pack.py merge --root showcases --task ID [--judgements DIR]
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
EXCLUDED_PARTS = {".baltor", ".claude", ".agents", ".opencode", ".codex", ".showcase", ".git", "__pycache__",
                  "node_modules", ".venv"}
EXCLUDED_NAMES = {"CLAUDE.md", "AGENTS.md", ".mcp.json", "opencode.json", "step.lock.json"}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv", ".py", ".js", ".ts", ".html", ".css", ".svg", ".yaml", ".yml",
                 ".toml", ".srt", ".vtt", ".gd", ".tscn", ".scad", ".sql", ".sh", ".xml", ".ipynb"}
JUDGE_README = """# Blind judging packets

You are judging pairs of outputs produced for the same task. You do not know, and
must not try to find out, how either output was made. Each packet directory has:

- `packet.json`: the task prompt, the rubric, the criteria and the score scale;
- `A/` and `B/`: the two outputs (some words may read `[redacted]`; ignore that).

For each packet, write one JSON file (any name ending in `.json`) to the judgements
directory you were given, in this shape:

```json
{{
  "spec": "baltor.showcase-judgement/v1",
  "packet_id": "<packet id>",
  "task_id": "{task_id}",
  "judge": {{"id": "<your id>", "type": "llm|human", "model": "<model, if llm>"}},
  "preference": "A|B|tie",
  "scores": {{{score_example}}},
  "justification": "At least 40 characters citing concrete things you saw in A and B.",
  "confidence": "low|medium|high",
  "flags": []
}}
```

Score every criterion for both A and B on the scale {lo}..{hi}. Judge each packet on its own;
do not compare across packets. Add the flag `arm-identifiable` if anything in a packet tells you
how an output was produced, `outputs-missing` if a side is empty.
"""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_hash(spec: dict) -> str:
    body = {k: v for k, v in spec.items() if k != "spec_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def load(root: Path, task_id: str) -> tuple[dict, list[dict]]:
    spec = json.loads((root / "tasks" / task_id / "spec.json").read_text(encoding="utf-8"))
    if canonical_hash(spec) != spec.get("spec_sha256"):
        raise SystemExit(f"{task_id}: spec.json was edited after registration")
    runs = []
    for p in sorted((root / "runs" / task_id).glob("*/*/run.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        rec["_dir"] = str(p.parent)
        runs.append(rec)
    return spec, runs


def judge_metric(spec: dict, name: str | None = None) -> dict:
    ms = [m for m in spec["metrics"] if m["evaluator"]["type"] == "blind_judge" and (name is None or m["name"] == name)]
    if not ms:
        raise SystemExit("the spec has no blind_judge metric" + (f" named {name}" if name else ""))
    return ms[0]


def _criteria(params: dict) -> list[dict]:
    out = []
    for c in params.get("criteria") or [{"name": "overall", "description": "Overall quality against the prompt."}]:
        out.append(c if isinstance(c, dict) else {"name": str(c), "description": ""})
    return out


def _markers(runs: list[dict]) -> list[str]:
    words = {"baltor"}
    for r in runs:
        cat = r.get("catalogue") or {}
        for it in cat.get("downloaded", []) + cat.get("preplaced", []):
            words.add(it["identity"])
            words.add(it["identity"].replace("_", "-"))
    return sorted(words, key=len, reverse=True)


def _redact(text: str, markers: list[str]) -> tuple[str, int]:
    n = 0
    for m in markers:
        text, k = re.subn(re.escape(m), "[redacted]", text, flags=re.IGNORECASE)
        n += k
    return text, n


def _select_files(ws: Path, globs: list[str], max_files: int, max_bytes: int) -> list[Path]:
    out = []
    for p in sorted(ws.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ws)
        if EXCLUDED_PARTS.intersection(rel.parts) or p.name in EXCLUDED_NAMES:
            continue
        if globs and not any(fnmatch.fnmatch(rel.as_posix(), g) for g in globs):
            continue
        if p.stat().st_size > max_bytes:
            continue
        out.append(p)
        if len(out) >= max_files:
            break
    return out


def _copy_side(run: dict, dest: Path, globs: list[str], markers: list[str], max_files: int,
               max_bytes: int) -> tuple[list[str], int]:
    ws = Path(run["_dir"]) / run.get("workspace", "workspace")
    files, redactions = [], 0
    for p in _select_files(ws, globs, max_files, max_bytes):
        rel = p.relative_to(ws).as_posix()
        safe_rel, k = _redact(rel, markers)
        redactions += k
        target = dest / safe_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix.lower() in TEXT_SUFFIXES:
            try:
                text, k = _redact(p.read_text(encoding="utf-8"), markers)
                redactions += k
                target.write_text(text, encoding="utf-8")
            except UnicodeDecodeError:
                shutil.copy2(p, target)
        else:
            shutil.copy2(p, target)
        files.append(safe_rel)
    return files, redactions


def build_packets(root: Path, task_id: str, *, metric: str | None = None, packets_out: Path | None = None,
                  both_orders: bool = False, max_packets: int | None = None, now: str | None = None) -> dict:
    root = Path(root)
    spec, runs = load(root, task_id)
    m = judge_metric(spec, metric)
    params = m["evaluator"].get("params") or {}
    included = [r for r in runs if r.get("included", True)]
    base = [r for r in included if r["arm"] == "baseline"]
    treat = [r for r in included if r["arm"] == "baltor"]
    if not base or not treat:
        raise SystemExit("need at least one included run in each arm")
    seed = int(params.get("seed", int(spec["spec_sha256"][8:16], 16) ^ int(spec["analysis"]["seed"])))
    rng = random.Random(seed)
    pairs = [(b, t) for b in base for t in treat]
    rng.shuffle(pairs)
    if max_packets:
        pairs = pairs[:max_packets]
    rubric = params.get("rubric", "Judge how well each output fulfils the prompt.")
    if isinstance(rubric, str) and rubric.startswith("task:"):
        rubric = (root / "tasks" / task_id / rubric[len("task:"):]).read_text(encoding="utf-8")
    criteria = _criteria(params)
    lo, hi = params.get("scale", [1, 5])
    globs = params.get("files") or [o["path"] for o in spec.get("outputs", [])]
    markers = _markers(included)
    out = Path(packets_out or root / "judging" / task_id / "packets")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    key = {"task_id": task_id, "spec_sha256": spec["spec_sha256"], "metric": m["name"], "seed": seed,
           "built_at": now or _now(), "both_orders": both_orders, "scale": [lo, hi],
           "criteria": [c["name"] for c in criteria], "packets": {}}
    used_ids = set()
    for b, t in pairs:
        orders = [(b, t), (t, b)] if both_orders else [(b, t) if rng.random() < 0.5 else (t, b)]
        for a_run, b_run in orders:
            pid = f"p{rng.getrandbits(40):010x}"
            while pid in used_ids:
                pid = f"p{rng.getrandbits(40):010x}"
            used_ids.add(pid)
            pdir = out / pid
            files_a, red_a = _copy_side(a_run, pdir / "A", globs, markers, int(params.get("max_files", 20)),
                                        int(params.get("max_file_bytes", 2_000_000)))
            files_b, red_b = _copy_side(b_run, pdir / "B", globs, markers, int(params.get("max_files", 20)),
                                        int(params.get("max_file_bytes", 2_000_000)))
            (pdir / "A").mkdir(exist_ok=True)
            (pdir / "B").mkdir(exist_ok=True)
            packet = {"packet_id": pid, "task_id": task_id, "prompt": spec["prompt"], "rubric": rubric,
                      "criteria": criteria, "scale": [lo, hi], "files": {"A": files_a, "B": files_b}}
            (pdir / "packet.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8")
            key["packets"][pid] = {"A": a_run["run_id"], "B": b_run["run_id"],
                                   "redactions": {"A": red_a, "B": red_b}}
    example = ", ".join(f'"{c["name"]}": {{"A": {lo}, "B": {hi}}}' for c in criteria)
    (out / "README.md").write_text(JUDGE_README.format(task_id=task_id, score_example=example, lo=lo, hi=hi),
                                   encoding="utf-8")
    key_path = root / "runs" / task_id / "_judging" / "key.json"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    return {"packets": len(key["packets"]), "packets_dir": str(out), "key": str(key_path)}


def _check_judgement(j: dict, key: dict) -> str | None:
    if j.get("spec") != "baltor.showcase-judgement/v1":
        return "spec must be baltor.showcase-judgement/v1"
    if j.get("packet_id") not in key["packets"]:
        return f"unknown packet {j.get('packet_id')}"
    if j.get("task_id") != key["task_id"]:
        return "task_id does not match"
    if j.get("preference") not in ("A", "B", "tie"):
        return "preference must be A, B or tie"
    if len(str(j.get("justification", ""))) < 40:
        return "justification shorter than 40 characters"
    if not isinstance(j.get("judge"), dict) or not j["judge"].get("id"):
        return "judge.id missing"
    lo, hi = key["scale"]
    scores = j.get("scores") or {}
    for c in key["criteria"]:
        s = scores.get(c)
        if not isinstance(s, dict) or any(not isinstance(s.get(side), (int, float)) or not lo <= s[side] <= hi
                                          for side in ("A", "B")):
            return f"criterion '{c}' needs A and B scores in {lo}..{hi}"
    return None


def merge(root: Path, task_id: str, judgements_dir: Path | None = None, now: str | None = None) -> dict:
    root = Path(root)
    key_path = root / "runs" / task_id / "_judging" / "key.json"
    key = json.loads(key_path.read_text(encoding="utf-8"))
    jdir = Path(judgements_dir or root / "judging" / task_id / "judgements")
    raw = []
    for p in sorted(jdir.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for j in data if isinstance(data, list) else [data]:
            raw.append((p.name, j))
    lo, hi = key["scale"]
    accepted, rejected, seen = [], [], set()
    for src, j in raw:
        problem = _check_judgement(j, key)
        ident = (j.get("packet_id"), (j.get("judge") or {}).get("id"))
        if problem is None and ident in seen:
            problem = "duplicate judgement for this packet by this judge"
        if problem:
            rejected.append({"file": src, "packet_id": j.get("packet_id"), "reason": problem})
            continue
        seen.add(ident)
        accepted.append(j)
    per_run = defaultdict(lambda: {"scores": [], "wins": 0, "losses": 0, "ties": 0})
    arm_pref = Counter()
    position = Counter()
    per_packet = defaultdict(list)
    flags = Counter()
    for j in accepted:
        k = key["packets"][j["packet_id"]]
        for side in ("A", "B"):
            norm = sum((j["scores"][c][side] - lo) / (hi - lo) for c in key["criteria"]) / len(key["criteria"])
            per_run[k[side]]["scores"].append(norm)
        pref = j["preference"]
        position[pref] += 1
        per_packet[j["packet_id"]].append(pref)
        for f in j.get("flags", []):
            flags[f] += 1
        if pref == "tie":
            per_run[k["A"]]["ties"] += 1
            per_run[k["B"]]["ties"] += 1
            arm_pref["tie"] += 1
        else:
            win, lose = (k["A"], k["B"]) if pref == "A" else (k["B"], k["A"])
            per_run[win]["wins"] += 1
            per_run[lose]["losses"] += 1
            arm_pref["baltor" if "/baltor/" in win else "baseline"] += 1
    runs = {}
    for rid, d in sorted(per_run.items()):
        n = d["wins"] + d["losses"] + d["ties"]
        runs[rid] = {"appearances": n, "wins": d["wins"], "losses": d["losses"], "ties": d["ties"],
                     "score": round(sum(d["scores"]) / len(d["scores"]), 6) if d["scores"] else None,
                     "win_share": round((d["wins"] + 0.5 * d["ties"]) / n, 6) if n else None}
    decided = position["A"] + position["B"]
    multi = {pid: prefs for pid, prefs in per_packet.items() if len(prefs) > 1}
    agreement = (sum(1 for prefs in multi.values() if len(set(prefs)) == 1) / len(multi)) if multi else None
    warnings = []
    if decided >= 10 and not 0.35 <= position["A"] / decided <= 0.65:
        warnings.append(f"position bias: A preferred in {position['A']}/{decided} decided judgements")
    if flags["arm-identifiable"]:
        warnings.append(f"{flags['arm-identifiable']} judgement(s) flagged the arm as identifiable")
    if rejected:
        warnings.append(f"{len(rejected)} judgement(s) rejected")
    judges = sorted({(j["judge"]["id"], j["judge"].get("type", "?"), j["judge"].get("model")) for j in accepted})
    merged = {
        "task_id": key["task_id"], "spec_sha256": key["spec_sha256"], "metric": key["metric"],
        "merged_at": now or _now(), "packets": len(key["packets"]), "judgements": len(accepted),
        "rejected": rejected,
        "judges": [{"id": a, "type": b, "model": c} for a, b, c in judges],
        "pairwise": {"baltor_preferred": arm_pref["baltor"], "baseline_preferred": arm_pref["baseline"],
                     "ties": arm_pref["tie"]},
        "position": {"A": position["A"], "B": position["B"], "tie": position["tie"]},
        "inter_judge_agreement": agreement,
        "flags": dict(flags),
        "warnings": warnings,
        "runs": runs,
        "note": "Blind, order-randomised LLM or human judgements are weaker evidence than deterministic tests.",
    }
    out = key_path.parent / "merged.json"
    out.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return merged


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", type=Path, default=Path("showcases"))
    b.add_argument("--task", required=True)
    b.add_argument("--metric")
    b.add_argument("--packets-out", type=Path)
    b.add_argument("--both-orders", action="store_true", help="judge every pair twice, once in each order")
    b.add_argument("--max-packets", type=int)
    b.add_argument("--now")
    m = sub.add_parser("merge")
    m.add_argument("--root", type=Path, default=Path("showcases"))
    m.add_argument("--task", required=True)
    m.add_argument("--judgements", type=Path)
    m.add_argument("--now")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        res = build_packets(a.root, a.task, metric=a.metric, packets_out=a.packets_out, both_orders=a.both_orders,
                            max_packets=a.max_packets, now=a.now)
        print(f"{res['packets']} packet(s) in {res['packets_dir']}; key kept at {res['key']} (do not share it)")
        return 0
    res = merge(a.root, a.task, a.judgements, a.now)
    print(f"{res['judgements']} judgement(s) merged over {res['packets']} packet(s); "
          f"baltor preferred {res['pairwise']['baltor_preferred']}, baseline preferred "
          f"{res['pairwise']['baseline_preferred']}, ties {res['pairwise']['ties']}")
    for w in res["warnings"]:
        print("WARN", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
