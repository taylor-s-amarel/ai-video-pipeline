#!/usr/bin/env python3
"""Render Baltor showcase comparisons to Markdown and one static HTML gallery.

Inputs, under a showcases root:

* ``reports/<task>.comparison.json``  from showcase_stats
* ``tasks/<task>/spec.json``          the registered spec (prompt, inputs, licences)
* ``runs/<task>/<arm>/<trial>/run.json``  every run, including failures and exclusions
* ``reports/<task>.summary.json``     optional written summary (from the showcase_writer
  subagent): ``{"task_id", "comparison_sha256", "headline", "body", "claims": [...]}``

Every claim in a summary is checked against the comparison: its direction must
equal the metric's verdict, any numbers must match the estimate and CI, the
comparison hash must match, banned superlatives are refused, and a headline may
not imply an improvement the primary verdict does not support. A summary that
fails is withheld and the problems are shown instead.

Outputs (default ``reports/``): ``<task>.md``, ``index.md``, ``index.html`` (single
file, inline CSS and SVG, light and dark, no JavaScript) and ``report.json``
(showcase_report contract).

CLI::

    python3 showcase_report_site.py render --root showcases [--out DIR] [--title TEXT] [--now ISO] [--strict]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import math
import os
import re
import sys
from pathlib import Path

VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
VERDICT_LABEL = {
    "baltor-better": ("\u25b2", "Baltor arm better"),
    "baseline-better": ("\u25bc", "Baseline arm better"),
    "no-clear-difference": ("=", "No clear difference"),
    "insufficient-data": ("?", "Insufficient data"),
}
NC_LABEL = {"passed": "Negative control passed (no difference found)",
            "failed": "Negative control FAILED (Baltor arm 'better' where it should not help)",
            "baltor-hurt": "Negative control: Baltor arm worse",
            "inconclusive": "Negative control inconclusive (not enough data to show no difference)"}
DEFAULT_BANNED = ["prove", "proves", "proven", "guarantee", "guarantees", "always", "never fails", "best-in-class",
                  "dramatic", "dramatically", "revolutionary", "game-changing", "10x", "100x", "massively"]
IMPROVEMENT_WORDS = re.compile(r"\b(improv\w*|better|higher|faster|cheaper|stronger|superior|ahead|outperform\w*|"
                               r"outscor\w*|beats?|wins?|boost\w*|gains?)\b",
                               re.IGNORECASE)
GLOBAL_DISCLOSURES = [
    "Conflict of interest: the Baltor components, the tasks, the evaluators and this report were produced by the same "
    "team. Treat these results as vendor-run evidence until someone independent reproduces them.",
    "Every run is listed, including failures, timeouts and over-budget runs (scored with the pre-registered "
    "on_missing value). Runs excluded for baseline contamination are listed with the reason.",
    "Results from LLM judges, even blind and order-randomised, are weaker evidence than deterministic tests.",
    "Each task was pre-registered (prompt, inputs, budget, metrics, evaluator, trials, threshold) and its spec "
    "SHA-256 is repeated in every run record. Both arms used the same model, harness version, budget and starting "
    "workspace; only catalogue access differed.",
    "Differences are mean(Baltor) - mean(baseline) with percentile bootstrap 95% intervals; verdicts also need a "
    "Holm-adjusted permutation p-value below alpha. Tasks are not jointly corrected across the report.",
]


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_rules() -> dict:
    p = HERE / "fairness_rules.json"
    rules = {"banned_claim_phrases": DEFAULT_BANNED}
    if p.exists():
        rules.update(json.loads(p.read_text(encoding="utf-8")))
    return rules


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "\u2014"
    x = float(x)
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    if abs(x) >= 100:
        return f"{x:.1f}"
    if float(x).is_integer() and abs(x) < 100:
        return f"{x:.0f}" if nd == 0 else f"{x:.{min(nd, 2)}f}"
    return f"{x:.{nd}f}"


def fmt_signed(x, nd: int = 3) -> str:
    if x is None:
        return "\u2014"
    s = fmt(x, nd)
    return s if s.startswith("-") or s == "\u2014" else "+" + s


def ci_text(d: dict) -> str:
    if d.get("estimate") is None:
        return "\u2014"
    return f"{fmt_signed(d['estimate'])} [{fmt(d['ci_low'])}, {fmt(d['ci_high'])}]"


# --------------------------------------------------------------------------- claim checks

def check_summary(summary: dict, comparison: dict, comparison_sha: str, rules: dict | None = None) -> list[str]:
    rules = rules or load_rules()
    problems = []
    if summary.get("task_id") not in (None, comparison["task_id"]):
        problems.append("summary is for a different task")
    if summary.get("comparison_sha256") != comparison_sha:
        problems.append("summary does not name the SHA-256 of the current comparison file (stale or unanchored)")
    text = " ".join([summary.get("headline", ""), summary.get("body", "")] +
                    [c.get("text", "") for c in summary.get("claims", [])])
    for phrase in rules.get("banned_claim_phrases", DEFAULT_BANNED):
        if re.search(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])", text, re.IGNORECASE):
            problems.append(f"uses the phrase '{phrase}'")
    metrics = {m["name"]: m for m in comparison["metrics"]}
    for c in summary.get("claims", []):
        m = metrics.get(c.get("metric"))
        if m is None:
            problems.append(f"claim about unknown metric '{c.get('metric')}'")
            continue
        if c.get("direction") != m["verdict"]:
            problems.append(f"claim on {m['name']} says '{c.get('direction')}' but the verdict is '{m['verdict']}'")
        for key, actual in (("estimate", m["difference"]["estimate"]), ("ci_low", m["difference"]["ci_low"]),
                            ("ci_high", m["difference"]["ci_high"])):
            if key in c and actual is not None and abs(float(c[key]) - actual) > max(0.0051, 0.005 * abs(actual)):
                problems.append(f"claim on {m['name']}: {key} {c[key]} does not match the comparison ({actual})")
        if comparison.get("negative_control") and c.get("direction") == "baltor-better":
            problems.append(f"claims a Baltor advantage on {m['name']} in a negative-control task")
    overall = comparison["overall"]["verdict"]
    if overall != "baltor-better" and IMPROVEMENT_WORDS.search(summary.get("headline", "")):
        problems.append(f"headline implies an improvement but the primary verdict is '{overall}'")
    return problems


# --------------------------------------------------------------------------- loading

def load_bundle(root: Path, comparison_path: Path) -> dict:
    cmp = json.loads(comparison_path.read_text(encoding="utf-8"))
    tid = cmp["task_id"]
    spec = json.loads((root / "tasks" / tid / "spec.json").read_text(encoding="utf-8"))
    if spec["spec_sha256"] != cmp["spec_sha256"]:
        raise SystemExit(f"{comparison_path}: comparison was made for a different spec")
    runs = []
    for p in sorted((root / "runs" / tid).glob("*/*/run.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        rec["_dir"] = p.parent
        runs.append(rec)
    runs.sort(key=lambda r: (r.get("schedule_index", 0), r["arm"], r["trial"]))
    summary_path = comparison_path.with_name(f"{tid}.summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
    return {"comparison": cmp, "comparison_path": comparison_path, "comparison_sha256": sha256_file(comparison_path),
            "spec": spec, "runs": runs, "summary": summary}


def _primary_value(run: dict, name: str | None):
    for r in (run.get("evaluation") or {}).get("results", []):
        if r["metric"] == name:
            return r["value"]
    return None


def task_entry(b: dict, out_dir: Path, rules: dict) -> dict:
    cmp, spec = b["comparison"], b["spec"]
    primary = cmp["overall"]["primary_metric"]
    rows = []
    for r in b["runs"]:
        ws = Path(r["_dir"]) / r.get("workspace", "workspace")
        outs = [{"path": o["path"], "href": os.path.relpath(ws / o["path"], out_dir).replace(os.sep, "/"),
                 "size": o["size"]} for o in r.get("outputs", []) if o.get("change") != "unchanged"]
        cat = r.get("catalogue") or {}
        rows.append({
            "run_id": r["run_id"], "arm": r["arm"], "trial": r["trial"], "adapter": r.get("adapter", "?"),
            "status": r["exit"]["status"], "included": bool(r.get("included", True)),
            "exclusion_reason": r.get("exclusion_reason"),
            "success": (r.get("evaluation") or {}).get("success"),
            "primary_value": _primary_value(r, primary), "wall_s": r.get("wall_s"),
            "tool_calls": (r.get("usage") or {}).get("tool_calls"),
            "tokens_total": (r.get("usage") or {}).get("tokens_total"),
            "cost_usd": (r.get("usage") or {}).get("cost_usd"),
            "catalogue_items": [f"{i['identity']}@{i['version']}" for i in cat.get("downloaded", []) +
                                cat.get("preplaced", [])],
            "outputs": outs,
        })
    summary = None
    if b["summary"]:
        problems = check_summary(b["summary"], cmp, b["comparison_sha256"], rules)
        summary = {"headline": b["summary"].get("headline", ""), "body": b["summary"].get("body", ""),
                   "claims": [{k: c[k] for k in ("text", "metric", "direction", "estimate", "ci_low", "ci_high")
                               if k in c} for c in b["summary"].get("claims", [])],
                   "accepted": not problems, "problems": problems}
    return {
        "task_id": cmp["task_id"], "title": cmp["title"], "domain": cmp["domain"], "purpose": cmp["purpose"],
        "task_type": cmp["task_type"], "negative_control": cmp["negative_control"], "prompt": spec["prompt"],
        "spec_sha256": spec["spec_sha256"], "preregistered_on": spec["preregistered_on"],
        "comparison_path": os.path.relpath(b["comparison_path"], out_dir).replace(os.sep, "/"),
        "comparison_sha256": b["comparison_sha256"], "trials_planned": spec["trials"],
        "overall_verdict": cmp["overall"]["verdict"],
        "negative_control_status": cmp["overall"]["negative_control_status"], "primary_metric": primary,
        "metrics": [{"name": m["name"], "kind": m["kind"], "direction": m["direction"], "primary": m["primary"],
                     "baseline_mean": m["baseline"]["mean"], "baltor_mean": m["baltor"]["mean"],
                     "n_baseline": m["baseline"]["n"], "n_baltor": m["baltor"]["n"],
                     "difference": m["difference"]["estimate"], "ci_low": m["difference"]["ci_low"],
                     "ci_high": m["difference"]["ci_high"], "win_rate": m["win_rate"]["rate"],
                     "cliffs_delta": m["effect_size"]["value"], "p_holm": m["p_holm"], "verdict": m["verdict"]}
                    for m in cmp["metrics"]],
        "success": {"baseline_rate": cmp["success"]["baseline"]["rate"], "baltor_rate": cmp["success"]["baltor"]["rate"],
                    "threshold": cmp["success"]["threshold"]},
        "cost": [{"name": c["name"], "label": c["label"], "baseline_mean": c["baseline"]["mean"],
                  "baltor_mean": c["baltor"]["mean"], "difference": c["difference"]["estimate"],
                  "ci_low": c["difference"]["ci_low"], "ci_high": c["difference"]["ci_high"],
                  "relative_difference": c["relative_difference"], "missing_values": c["missing_values"]}
                 for c in cmp["cost"]],
        "runs": rows, "runs_excluded": sum(1 for r in rows if not r["included"]),
        "summary": summary, "warnings": cmp["overall"]["warnings"], "disclosures": cmp["disclosures"],
        "_cmp": cmp, "_spec": spec,
    }


def build_report(root: Path, out_dir: Path, *, title: str, now: str | None = None,
                 comparisons: list[Path] | None = None) -> dict:
    root, out_dir = Path(root), Path(out_dir)
    rules = load_rules()
    paths = comparisons or sorted((root / "reports").glob("*.comparison.json"))
    if not paths:
        raise SystemExit(f"no comparisons found under {root / 'reports'}")
    tasks = [task_entry(load_bundle(root, Path(p)), out_dir, rules) for p in paths]
    verdicts: dict[str, int] = {}
    for t in tasks:
        verdicts[t["overall_verdict"]] = verdicts.get(t["overall_verdict"], 0) + 1
    report = {
        "spec": "baltor.showcase-report/v1", "title": title, "generated_at": now or _now(),
        "generator": {"module": "showcase_report_site", "version": VERSION},
        "tasks": tasks,
        "totals": {"tasks": len(tasks), "runs": sum(len(t["runs"]) for t in tasks),
                   "runs_excluded": sum(t["runs_excluded"] for t in tasks),
                   "negative_controls": sum(1 for t in tasks if t["negative_control"]), "verdicts": verdicts},
        "disclosures": list(GLOBAL_DISCLOSURES),
    }
    return report


def public_report(report: dict) -> dict:
    out = dict(report)
    out["tasks"] = [{k: v for k, v in t.items() if not k.startswith("_")} for t in report["tasks"]]
    return out


def validate_report(report: dict) -> list[str]:
    path = HERE / "schemas" / "showcase_report.schema.json"
    if not path.exists():
        return []
    try:
        import jsonschema  # type: ignore
    except ImportError:  # pragma: no cover
        return []
    schema = json.loads(path.read_text(encoding="utf-8"))
    return [f"{'/'.join(map(str, e.absolute_path))}: {e.message}"
            for e in jsonschema.Draft202012Validator(schema).iter_errors(public_report(report))]


# --------------------------------------------------------------------------- Markdown

def _md_escape(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def task_markdown(t: dict) -> str:
    sym, label = VERDICT_LABEL[t["overall_verdict"]]
    lines = [f"# {t['title']}", ""]
    if t["purpose"] != "study":
        lines += [f"> **{t['purpose'].upper()}: not a study result.** These numbers exercise the pipeline or tune a "
                  "budget; do not cite them.", ""]
    lines += [f"- Task `{t['task_id']}` · domain {t['domain']} · {t['task_type']}"
              + (" · **negative control**" if t["negative_control"] else ""),
              f"- Pre-registered {t['preregistered_on']} · spec SHA-256 `{t['spec_sha256']}`",
              f"- Primary metric `{t['primary_metric']}` · verdict: **{sym} {label}**"]
    if t["negative_control_status"]:
        lines.append(f"- {NC_LABEL[t['negative_control_status']]}")
    lines += ["", "## Prompt (identical for both arms)", "", "```text", t["prompt"].strip(), "```", ""]
    if t["summary"]:
        if t["summary"]["accepted"]:
            lines += ["## Summary", "", f"**{t['summary']['headline']}**", "", t["summary"].get("body", ""), ""]
        else:
            lines += ["## Summary withheld", "", "The written summary failed the claim check:", ""]
            lines += [f"- {p}" for p in t["summary"]["problems"]] + [""]
    lines += ["## Quality metrics", "",
              "| Metric | Kind | Baseline mean (n) | Baltor mean (n) | Difference [95% CI] | Win rate | Cliff's δ | p (Holm) | Verdict |",
              "|---|---|---:|---:|---|---:|---:|---:|---|"]
    for m in t["metrics"]:
        name = f"**{m['name']}** (primary)" if m["primary"] else m["name"]
        arrow = "↑" if m["direction"] == "higher" else "↓"
        lines.append(f"| {name} {arrow} | {m['kind']} | {fmt(m['baseline_mean'])} ({m['n_baseline']}) | "
                     f"{fmt(m['baltor_mean'])} ({m['n_baltor']}) | "
                     f"{ci_text({'estimate': m['difference'], 'ci_low': m['ci_low'], 'ci_high': m['ci_high']})} | "
                     f"{fmt(m['win_rate'], 2)} | {fmt(m['cliffs_delta'], 2)} | {fmt(m['p_holm'])} | "
                     f"{VERDICT_LABEL[m['verdict']][1]} |")
    s = t["success"]
    thr = s.get("threshold") or {}
    lines += ["", f"Success ({thr.get('metric')} {thr.get('op')} {thr.get('value')}): baseline {fmt(s['baseline_rate'], 2)}, "
              f"Baltor {fmt(s['baltor_rate'], 2)}.", "", "## Cost", "",
              "| Measure | Baseline mean | Baltor mean | Difference [95% CI] | Relative | Missing |",
              "|---|---:|---:|---|---:|---:|"]
    for c in t["cost"]:
        rel = "\u2014" if c["relative_difference"] is None else f"{c['relative_difference'] * 100:+.0f}%"
        lines.append(f"| {c['label']} | {fmt(c['baseline_mean'])} | {fmt(c['baltor_mean'])} | "
                     f"{ci_text({'estimate': c['difference'], 'ci_low': c['ci_low'], 'ci_high': c['ci_high']})} | "
                     f"{rel} | {c['missing_values']} |")
    lines += ["", "## Every run", "",
              "| Run | Adapter | Status | Included | Success | Primary | Wall s | Tool calls | Tokens | Catalogue items | Outputs |",
              "|---|---|---|---|---|---:|---:|---:|---:|---|---|"]
    for r in t["runs"]:
        inc = "yes" if r["included"] else f"no: {_md_escape(r['exclusion_reason'] or '')}"
        outs = ", ".join(f"[{_md_escape(o['path'])}]({o['href']})" for o in r["outputs"][:5])
        if len(r["outputs"]) > 5:
            outs += f" +{len(r['outputs']) - 5} more"
        lines.append(f"| {r['run_id']} | {r['adapter']} | {r['status']} | {inc} | {r['success']} | "
                     f"{fmt(r['primary_value'])} | {fmt(r['wall_s'], 1)} | {fmt(r['tool_calls'], 0)} | "
                     f"{fmt(r['tokens_total'], 0)} | {_md_escape(', '.join(r['catalogue_items']) or '—')} | {outs or '—'} |")
    if t["warnings"]:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in t["warnings"]]
    lines += ["", "## Disclosures", ""] + [f"- {d}" for d in t["disclosures"]]
    lines += ["", f"Comparison: [{t['comparison_path']}]({t['comparison_path']}) (SHA-256 `{t['comparison_sha256']}`)", ""]
    return "\n".join(lines)


def index_markdown(report: dict) -> str:
    tot = report["totals"]
    lines = [f"# {report['title']}", "", f"Generated {report['generated_at']}. {tot['tasks']} task(s), {tot['runs']} run(s) "
             f"({tot['runs_excluded']} excluded and listed), {tot['negative_controls']} negative control(s).", ""]
    if any(t["purpose"] != "study" for t in report["tasks"]):
        lines += ["> Contains dry-run or pilot tasks. Those are not results.", ""]
    lines += ["| Task | Domain | Purpose | Primary metric | Difference [95% CI] | Verdict |", "|---|---|---|---|---|---|"]
    for t in report["tasks"]:
        pm = next((m for m in t["metrics"] if m["primary"]), t["metrics"][0])
        lines.append(f"| [{_md_escape(t['title'])}]({t['task_id']}.md) | {t['domain']} | {t['purpose']} | {pm['name']} | "
                     f"{ci_text({'estimate': pm['difference'], 'ci_low': pm['ci_low'], 'ci_high': pm['ci_high']})} | "
                     f"{VERDICT_LABEL[t['overall_verdict']][1]}"
                     + (f" ({t['negative_control_status']} control)" if t["negative_control_status"] else "") + " |")
    lines += ["", "## Disclosures", ""] + [f"- {d}" for d in report["disclosures"]] + [""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- HTML

CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#6f6d68;
--grid:#e1e0d9;--axis:#c3c2b7;--series:#2a78d6;--ring:#fcfcfb;--border:rgba(11,11,11,.10);--banner:#fff4d6;
--banner-ink:#5a4100;--chip:#f0efec}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;
--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#a3a29b;--grid:#2c2c2a;--axis:#383835;--series:#3987e5;
--ring:#1a1a19;--border:rgba(255,255,255,.10);--banner:#3a2e0b;--banner-ink:#ffe3a0;--chip:#262624}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;
--muted:#a3a29b;--grid:#2c2c2a;--axis:#383835;--series:#3987e5;--ring:#1a1a19;--border:rgba(255,255,255,.10);
--banner:#3a2e0b;--banner-ink:#ffe3a0;--chip:#262624}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:28px;line-height:1.2;margin:0 0 6px}h2{font-size:20px;margin:0 0 4px}h3{font-size:15px;margin:20px 0 8px}
p{margin:6px 0}.sub{color:var(--ink2)}
.banner{background:var(--banner);color:var(--banner-ink);border-radius:8px;padding:10px 14px;margin:14px 0;font-weight:600}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 14px}
.tile .v{font-size:24px;font-weight:600}.tile .l{color:var(--ink2);font-size:13px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px 18px 8px;margin:22px 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.chip{background:var(--chip);border:1px solid var(--border);border-radius:999px;padding:2px 10px;font-size:13px;color:var(--ink2)}
.verdict{font-weight:600;color:var(--ink)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--grid);text-align:left;vertical-align:middle;white-space:nowrap}
th{color:var(--ink2);font-weight:600}td.num,th.num{text-align:right}td.wrap{white-space:normal;min-width:180px}
details{margin:8px 0}summary{cursor:pointer;color:var(--ink2)}
pre{white-space:pre-wrap;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:10px;font-size:13px}
code{font-size:12.5px;word-break:break-all}
a{color:var(--series)}
.excluded td{color:var(--muted)}
.ci{display:block}
.ci .zero{stroke:var(--axis);stroke-width:1}.ci .bar{stroke:var(--series);stroke-width:2;stroke-linecap:round}
.ci .dot{fill:var(--series);stroke:var(--ring);stroke-width:2}.ci text{fill:var(--muted);font-size:10px}
ul.disc{padding-left:18px;color:var(--ink2)}ul.disc li{margin:4px 0}
.problems{border-left:3px solid var(--axis);padding-left:10px;color:var(--ink2)}
footer{color:var(--muted);font-size:13px;margin-top:30px}
"""


def ci_svg(est, lo, hi, direction: str, label: str) -> str:
    """Oriented interval: right of zero favours the Baltor arm whatever the metric's direction."""
    if est is None or lo is None or hi is None:
        return '<span class="sub">\u2014</span>'
    s = 1 if direction == "higher" else -1
    e, a, b = s * est, *sorted((s * lo, s * hi))
    m = max(abs(a), abs(b), abs(e), 1e-12) * 1.15
    w, h, pad = 168, 30, 8

    def x(v):
        return pad + (v + m) / (2 * m) * (w - 2 * pad)
    desc = (f"{label}: difference {fmt_signed(est)}, 95% CI {fmt(lo)} to {fmt(hi)}; "
            "plotted so that right of zero favours the Baltor arm")
    return (f'<svg class="ci" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(desc)}">'
            f'<title>{html.escape(desc)}</title>'
            f'<line class="zero" x1="{x(0):.1f}" y1="3" x2="{x(0):.1f}" y2="21"/>'
            f'<line class="bar" x1="{x(a):.1f}" y1="12" x2="{x(b):.1f}" y2="12"/>'
            f'<line class="bar" x1="{x(a):.1f}" y1="8" x2="{x(a):.1f}" y2="16"/>'
            f'<line class="bar" x1="{x(b):.1f}" y1="8" x2="{x(b):.1f}" y2="16"/>'
            f'<circle class="dot" cx="{x(e):.1f}" cy="12" r="4.5"/>'
            f'<text x="{pad}" y="29">baseline</text><text x="{w - pad}" y="29" text-anchor="end">Baltor</text></svg>')


def _e(s) -> str:
    return html.escape(str(s))


def task_html(t: dict) -> str:
    sym, label = VERDICT_LABEL[t["overall_verdict"]]
    out = [f'<section class="card" id="{_e(t["task_id"])}">', f'<h2>{_e(t["title"])}</h2>']
    if t["purpose"] != "study":
        out.append(f'<div class="banner">{_e(t["purpose"].upper())}: not a study result. These numbers exercise the '
                   'pipeline or tune a budget; do not cite them.</div>')
    chips = [t["domain"], t["task_type"], f"{t['trials_planned']} trials per arm planned",
             f"pre-registered {t['preregistered_on']}"]
    if t["negative_control"]:
        chips.insert(0, "negative control")
    out.append('<div class="chips">' + "".join(f'<span class="chip">{_e(c)}</span>' for c in chips) +
               f'<span class="chip verdict">{_e(sym)} {_e(label)}</span></div>')
    if t["negative_control_status"]:
        out.append(f'<p class="verdict">{_e(NC_LABEL[t["negative_control_status"]])}</p>')
    if t["summary"]:
        if t["summary"]["accepted"]:
            out.append(f'<p><strong>{_e(t["summary"]["headline"])}</strong></p>')
            if t["summary"].get("body"):
                out.append(f'<p class="sub">{_e(t["summary"]["body"])}</p>')
        else:
            out.append('<div class="problems"><strong>Summary withheld</strong>: it failed the claim check.<ul>' +
                       "".join(f"<li>{_e(p)}</li>" for p in t["summary"]["problems"]) + "</ul></div>")
    out.append(f'<details><summary>Prompt (identical for both arms)</summary><pre>{_e(t["prompt"].strip())}</pre>'
               f'<p class="sub">Spec SHA-256 <code>{_e(t["spec_sha256"])}</code></p></details>')
    out.append('<h3>Quality</h3><div class="scroll"><table><thead><tr><th>Metric</th><th>Kind</th>'
               '<th class="num">Baseline mean (n)</th><th class="num">Baltor mean (n)</th>'
               '<th>Difference [95% CI]</th><th>Interval (right favours Baltor)</th><th class="num">Win rate</th>'
               '<th class="num">Cliff\'s δ</th><th class="num">p (Holm)</th><th>Verdict</th></tr></thead><tbody>')
    for m in t["metrics"]:
        name = _e(m["name"]) + (" <em>(primary)</em>" if m["primary"] else "")
        arrow = "higher is better" if m["direction"] == "higher" else "lower is better"
        out.append(
            f'<tr><td>{name}<br><span class="sub">{arrow}</span></td><td>{_e(m["kind"])}</td>'
            f'<td class="num">{fmt(m["baseline_mean"])} ({m["n_baseline"]})</td>'
            f'<td class="num">{fmt(m["baltor_mean"])} ({m["n_baltor"]})</td>'
            f'<td>{_e(ci_text({"estimate": m["difference"], "ci_low": m["ci_low"], "ci_high": m["ci_high"]}))}</td>'
            f'<td>{ci_svg(m["difference"], m["ci_low"], m["ci_high"], m["direction"], m["name"])}</td>'
            f'<td class="num">{fmt(m["win_rate"], 2)}</td><td class="num">{fmt(m["cliffs_delta"], 2)}</td>'
            f'<td class="num">{fmt(m["p_holm"])}</td>'
            f'<td>{_e(VERDICT_LABEL[m["verdict"]][0])} {_e(VERDICT_LABEL[m["verdict"]][1])}</td></tr>')
    out.append("</tbody></table></div>")
    s = t["success"]
    thr = s.get("threshold") or {}
    out.append(f'<p class="sub">Success ({_e(thr.get("metric"))} {_e(thr.get("op"))} {_e(thr.get("value"))}): '
               f'baseline {fmt(s["baseline_rate"], 2)}, Baltor {fmt(s["baltor_rate"], 2)}.</p>')
    out.append('<h3>Cost</h3><div class="scroll"><table><thead><tr><th>Measure</th><th class="num">Baseline mean</th>'
               '<th class="num">Baltor mean</th><th>Difference [95% CI]</th><th class="num">Relative</th>'
               '<th class="num">Missing values</th></tr></thead><tbody>')
    for c in t["cost"]:
        rel = "\u2014" if c["relative_difference"] is None else f"{c['relative_difference'] * 100:+.0f}%"
        out.append(f'<tr><td>{_e(c["label"])}</td><td class="num">{fmt(c["baseline_mean"])}</td>'
                   f'<td class="num">{fmt(c["baltor_mean"])}</td>'
                   f'<td>{_e(ci_text({"estimate": c["difference"], "ci_low": c["ci_low"], "ci_high": c["ci_high"]}))}</td>'
                   f'<td class="num">{rel}</td><td class="num">{c["missing_values"]}</td></tr>')
    out.append("</tbody></table></div>")
    out.append(f'<h3>Every run ({len(t["runs"])}, {t["runs_excluded"]} excluded)</h3><div class="scroll"><table><thead><tr>'
               '<th>Run</th><th>Adapter</th><th>Status</th><th>Included</th><th>Success</th>'
               f'<th class="num">{_e(t["primary_metric"])}</th><th class="num">Wall s</th><th class="num">Tool calls</th>'
               '<th class="num">Tokens</th><th>Catalogue items</th><th>Outputs</th></tr></thead><tbody>')
    for r in t["runs"]:
        cls = "" if r["included"] else ' class="excluded"'
        inc = "yes" if r["included"] else f"no: {_e(r['exclusion_reason'] or '')}"
        links = ", ".join(f'<a href="{_e(o["href"])}">{_e(o["path"])}</a>' for o in r["outputs"][:5])
        if len(r["outputs"]) > 5:
            links += f" +{len(r['outputs']) - 5} more"
        out.append(f'<tr{cls}><td>{_e(r["run_id"])}</td><td>{_e(r["adapter"])}</td><td>{_e(r["status"])}</td>'
                   f'<td class="wrap">{inc}</td><td>{_e(r["success"])}</td><td class="num">{fmt(r["primary_value"])}</td>'
                   f'<td class="num">{fmt(r["wall_s"], 1)}</td><td class="num">{fmt(r["tool_calls"], 0)}</td>'
                   f'<td class="num">{fmt(r["tokens_total"], 0)}</td>'
                   f'<td class="wrap">{_e(", ".join(r["catalogue_items"]) or "—")}</td>'
                   f'<td class="wrap">{links or "—"}</td></tr>')
    out.append("</tbody></table></div>")
    if t["warnings"]:
        out.append("<h3>Warnings</h3><ul class=\"disc\">" + "".join(f"<li>{_e(w)}</li>" for w in t["warnings"]) + "</ul>")
    out.append("<h3>Disclosures</h3><ul class=\"disc\">" + "".join(f"<li>{_e(d)}</li>" for d in t["disclosures"]) +
               "</ul>")
    out.append(f'<p class="sub">Comparison <a href="{_e(t["comparison_path"])}">{_e(t["comparison_path"])}</a> · '
               f'SHA-256 <code>{_e(t["comparison_sha256"][:16])}…</code> · '
               f'<a href="{_e(t["task_id"])}.md">Markdown</a></p></section>')
    return "\n".join(out)


def index_html(report: dict) -> str:
    tot = report["totals"]
    tiles = [(tot["tasks"], "tasks"), (tot["runs"], "runs reported"), (tot["runs_excluded"], "runs excluded (listed)"),
             (tot["negative_controls"], "negative controls")]
    tiles += [(n, VERDICT_LABEL[v][1].lower()) for v, n in sorted(tot["verdicts"].items())]
    parts = ["<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f"<title>{_e(report['title'])}</title>", f"<style>{CSS}</style></head><body><main>",
             f"<h1>{_e(report['title'])}</h1>",
             f'<p class="sub">Generated {_e(report["generated_at"])}. Same task, same model, same harness, same budget: '
             "one arm without Baltor, one arm with access to the Baltor catalogue.</p>"]
    if any(t["purpose"] != "study" for t in report["tasks"]):
        parts.append('<div class="banner">This page contains dry-run or pilot tasks. Their numbers are not results.</div>')
    parts.append('<div class="tiles">' + "".join(f'<div class="tile"><div class="v">{v}</div><div class="l">{_e(l)}</div>'
                                                  "</div>" for v, l in tiles) + "</div>")
    parts.append("<h3>Disclosures</h3><ul class=\"disc\">" + "".join(f"<li>{_e(d)}</li>" for d in report["disclosures"])
                 + "</ul>")
    parts.append('<h3>Tasks</h3><div class="scroll"><table><thead><tr><th>Task</th><th>Domain</th><th>Purpose</th>'
                 "<th>Primary metric</th><th>Difference [95% CI]</th><th>Verdict</th></tr></thead><tbody>")
    for t in report["tasks"]:
        pm = next((m for m in t["metrics"] if m["primary"]), t["metrics"][0])
        nc = f" ({t['negative_control_status']} control)" if t["negative_control_status"] else ""
        parts.append(f'<tr><td><a href="#{_e(t["task_id"])}">{_e(t["title"])}</a></td><td>{_e(t["domain"])}</td>'
                     f'<td>{_e(t["purpose"])}</td><td>{_e(pm["name"])}</td>'
                     f'<td>{_e(ci_text({"estimate": pm["difference"], "ci_low": pm["ci_low"], "ci_high": pm["ci_high"]}))}</td>'
                     f'<td>{_e(VERDICT_LABEL[t["overall_verdict"]][1])}{_e(nc)}</td></tr>')
    parts.append("</tbody></table></div>")
    parts += [task_html(t) for t in report["tasks"]]
    parts.append('<footer>How verdicts are decided: ' + _e(" ".join(report["tasks"][0]["_cmp"]["verdict_rules"][:3]))
                 + f' Rendered by showcase_report_site {VERSION}. No scripts, no external resources.</footer>')
    parts.append("</main></body></html>")
    return "\n".join(parts) + "\n"


def render(root: Path, out_dir: Path | None = None, *, title: str = "Baltor showcases", now: str | None = None,
           strict: bool = False, comparisons: list[Path] | None = None) -> dict:
    root = Path(root)
    out_dir = Path(out_dir or root / "reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(root, out_dir, title=title, now=now, comparisons=comparisons)
    errors = validate_report(report)
    if errors:
        raise SystemExit(f"report does not match the showcase_report schema: {errors[:3]}")
    rejected = [t["task_id"] for t in report["tasks"] if t["summary"] and not t["summary"]["accepted"]]
    for t in report["tasks"]:
        (out_dir / f"{t['task_id']}.md").write_text(task_markdown(t), encoding="utf-8")
    (out_dir / "index.md").write_text(index_markdown(report), encoding="utf-8")
    (out_dir / "index.html").write_text(index_html(report), encoding="utf-8")
    (out_dir / "report.json").write_text(json.dumps(public_report(report), indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    if strict and rejected:
        raise SystemExit(f"summaries failed the claim check: {rejected}")
    return public_report(report)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--root", type=Path, default=Path("showcases"))
    r.add_argument("--out", type=Path)
    r.add_argument("--title", default="Baltor showcases")
    r.add_argument("--now")
    r.add_argument("--strict", action="store_true", help="exit non-zero when a summary fails the claim check")
    r.add_argument("--comparison", type=Path, action="append", help="render only these comparison files")
    c = sub.add_parser("check-summary")
    c.add_argument("summary", type=Path)
    c.add_argument("comparison", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "check-summary":
        problems = check_summary(json.loads(a.summary.read_text()), json.loads(a.comparison.read_text()),
                                 sha256_file(a.comparison))
        for p in problems:
            print("PROBLEM", p)
        print("summary accepted" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    rep = render(a.root, a.out, title=a.title, now=a.now, strict=a.strict, comparisons=a.comparison)
    print(f"rendered {rep['totals']['tasks']} task(s), {rep['totals']['runs']} run(s) to "
          f"{(a.out or a.root / 'reports') / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
