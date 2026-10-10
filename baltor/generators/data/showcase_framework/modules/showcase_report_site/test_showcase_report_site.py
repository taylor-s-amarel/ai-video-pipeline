import json
import re
from pathlib import Path

import pytest

import showcase_report_site as rs

SHA = "ab" * 32


def metric(name, verdict="baltor-better", primary=True, est=0.2, lo=0.1, hi=0.3, direction="higher", kind="deterministic"):
    return {"name": name, "kind": kind, "direction": direction, "weight": 1, "primary": primary, "derived": False,
            "baseline": {"n": 5, "mean": 0.5, "median": 0.5, "sd": 0.1, "min": 0.3, "max": 0.6},
            "baltor": {"n": 5, "mean": 0.7, "median": 0.7, "sd": 0.1, "min": 0.6, "max": 0.8},
            "difference": {"estimate": est, "ci_low": lo, "ci_high": hi, "ci_level": 0.95},
            "win_rate": {"baltor_wins": 22, "baseline_wins": 2, "ties": 1, "pairs": 25, "rate": 0.9},
            "effect_size": {"name": "cliffs_delta", "value": 0.8, "magnitude": "large"},
            "p_value": 0.008, "p_holm": 0.016, "verdict": verdict, "evidence": kind}


def comparison(task_id="tiny", verdict="baltor-better", negative=False, purpose="dry-run"):
    return {
        "spec": "baltor.showcase-comparison/v1", "task_id": task_id, "title": "Tiny task", "domain": "data-cleaning",
        "purpose": purpose, "task_type": "capability", "negative_control": negative, "spec_sha256": SHA,
        "generated_at": "2026-10-10T00:00:00Z", "generator": {"module": "showcase_stats", "version": "1"},
        "metrics": [metric("pair_f1", verdict), metric("wall_quality", "no-clear-difference", primary=False,
                                                       direction="lower", est=-1.0, lo=-2.0, hi=0.5)],
        "success": {"threshold": {"metric": "pair_f1", "op": ">=", "value": 0.8},
                    "baseline": {"successes": 1, "n": 5, "rate": 0.2}, "baltor": {"successes": 4, "n": 5, "rate": 0.8},
                    "difference": {"estimate": 0.6, "ci_low": 0.2, "ci_high": 1.0, "ci_level": 0.95}, "p_value": 0.2},
        "cost": [{"name": "wall_s", "label": "Wall time (s)", "direction": "lower", "missing_values": 0,
                  "baseline": {"n": 5, "mean": 100.0}, "baltor": {"n": 5, "mean": 120.0},
                  "difference": {"estimate": 20.0, "ci_low": 10.0, "ci_high": 30.0, "ci_level": 0.95},
                  "relative_difference": 0.2}],
        "overall": {"primary_metric": "pair_f1", "verdict": verdict,
                    "negative_control_status": ("passed" if verdict == "no-clear-difference" else "failed") if negative else None,
                    "warnings": ["fewer than 5 runs"]},
        "verdict_rules": ["rule one is here.", "rule two is here.", "rule three is here."],
        "disclosures": ["Same team wrote everything; vendor-run evidence."],
    }


def make_root(tmp_path, **kw):
    root = tmp_path / "showcases"
    cmp = comparison(**kw)
    tid = cmp["task_id"]
    (root / "tasks" / tid).mkdir(parents=True)
    (root / "tasks" / tid / "spec.json").write_text(json.dumps({
        "id": tid, "spec_sha256": SHA, "prompt": "Deduplicate contacts.csv <and> write clusters.csv.",
        "preregistered_on": "2026-10-10", "trials": 5}))
    for arm in ("baseline", "baltor"):
        for t in (1, 2):
            d = root / "runs" / tid / arm / str(t)
            (d / "workspace").mkdir(parents=True)
            (d / "workspace" / "clusters.csv").write_text("id,cluster\n")
            (d / "run.json").write_text(json.dumps({
                "run_id": f"{tid}/{arm}/{t}", "arm": arm, "trial": t, "schedule_index": t, "adapter": "manual",
                "exit": {"status": "imported"}, "included": not (arm == "baseline" and t == 2),
                "exclusion_reason": None if not (arm == "baseline" and t == 2) else "baseline contamination: x",
                "wall_s": 12.5, "usage": {"tool_calls": 7, "tokens_total": 12000, "cost_usd": None},
                "catalogue": {"downloaded": [{"identity": "dedupe_skill", "version": "1.0.0"}] if arm == "baltor" else [],
                              "preplaced": []},
                "outputs": [{"path": "clusters.csv", "size": 11, "sha256": "c" * 64, "change": "new"}],
                "evaluation": {"status": "done", "success": arm == "baltor",
                               "results": [{"metric": "pair_f1", "value": 0.5}]},
                "workspace": "workspace"}))
    (root / "reports").mkdir()
    cpath = root / "reports" / f"{tid}.comparison.json"
    cpath.write_text(json.dumps(cmp))
    return root, cpath


def test_render_writes_everything(tmp_path):
    root, _ = make_root(tmp_path)
    rep = rs.render(root, now="2026-10-10T00:00:00Z")
    out = root / "reports"
    page = (out / "index.html").read_text()
    assert "<script" not in page.lower()
    assert not re.search(r'(src|href)="https?://', page)
    assert "prefers-color-scheme:dark" in page and 'data-theme="dark"' in page
    for arm in ("baseline", "baltor"):
        for t in (1, 2):
            assert f"tiny/{arm}/{t}" in page
    assert "baseline contamination" in page and "DRY-RUN: not a study result" in page
    assert "Deduplicate contacts.csv &lt;and&gt;" in page
    assert '<a href="../runs/tiny/baltor/1/workspace/clusters.csv">' in page
    md = (out / "tiny.md").read_text()
    assert "| **pair_f1** (primary) ↑ |" in md and "Every run" in md
    assert rep["totals"] == {"tasks": 1, "runs": 4, "runs_excluded": 1, "negative_controls": 0,
                             "verdicts": {"baltor-better": 1}}
    data = json.loads((out / "report.json").read_text())
    assert data["spec"] == "baltor.showcase-report/v1" and len(data["disclosures"]) >= 3
    assert rs.validate_report(rs.build_report(root, out, title="t", now="2026-10-10T00:00:00Z")) == []


def _summary(cpath, **kw):
    s = {"task_id": "tiny", "comparison_sha256": rs.sha256_file(cpath),
         "headline": "On this dry-run task the Baltor arm scored higher pair F1.",
         "body": "Five runs per arm.",
         "claims": [{"text": "Pair F1 was 0.20 higher [0.10, 0.30].", "metric": "pair_f1",
                     "direction": "baltor-better", "estimate": 0.2, "ci_low": 0.1, "ci_high": 0.3}]}
    s.update(kw)
    return s


def test_claim_checks(tmp_path):
    root, cpath = make_root(tmp_path)
    cmp = json.loads(cpath.read_text())
    sha = rs.sha256_file(cpath)
    assert rs.check_summary(_summary(cpath), cmp, sha) == []
    wrong = _summary(cpath, claims=[{"text": "Wall quality improved a lot overall.", "metric": "wall_quality",
                                     "direction": "baltor-better"}])
    assert any("verdict is 'no-clear-difference'" in p for p in rs.check_summary(wrong, cmp, sha))
    hype = _summary(cpath, headline="Baltor dramatically improves deduplication")
    assert any("dramatically" in p for p in rs.check_summary(hype, cmp, sha))
    numbers = _summary(cpath, claims=[dict(_summary(cpath)["claims"][0], estimate=0.35)])
    assert any("does not match" in p for p in rs.check_summary(numbers, cmp, sha))
    stale = _summary(cpath, comparison_sha256="0" * 64)
    assert any("stale" in p for p in rs.check_summary(stale, cmp, sha))
    flat = comparison(verdict="no-clear-difference")
    assert any("headline implies" in p for p in rs.check_summary(_summary(cpath, claims=[]), flat, sha))


def test_rejected_summary_is_withheld(tmp_path):
    root, cpath = make_root(tmp_path)
    (root / "reports" / "tiny.summary.json").write_text(json.dumps(_summary(cpath, headline="Baltor always wins")))
    rs.render(root, now="2026-10-10T00:00:00Z")
    page = (root / "reports" / "index.html").read_text()
    assert "Summary withheld" in page and "Baltor always wins" not in page
    with pytest.raises(SystemExit):
        rs.render(root, now="2026-10-10T00:00:00Z", strict=True)
    (root / "reports" / "tiny.summary.json").write_text(json.dumps(_summary(cpath)))
    rs.render(root, now="2026-10-10T00:00:00Z", strict=True)
    assert "scored higher pair F1" in (root / "reports" / "index.html").read_text()


def test_negative_control_claims(tmp_path):
    root, cpath = make_root(tmp_path, negative=True)
    cmp = json.loads(cpath.read_text())
    problems = rs.check_summary(_summary(cpath), cmp, rs.sha256_file(cpath))
    assert any("negative-control" in p for p in problems)
    rs.render(root, now="2026-10-10T00:00:00Z")
    assert "Negative control FAILED" in (root / "reports" / "index.html").read_text()


def test_ci_svg_orientation():
    up = rs.ci_svg(0.2, 0.1, 0.3, "higher", "m")
    down = rs.ci_svg(-0.2, -0.3, -0.1, "lower", "m")
    cx = lambda s: float(re.search(r'<circle class="dot" cx="([0-9.]+)"', s).group(1))  # noqa: E731
    zero = lambda s: float(re.search(r'<line class="zero" x1="([0-9.]+)"', s).group(1))  # noqa: E731
    assert cx(up) > zero(up) and cx(down) > zero(down)  # both favour the Baltor arm, so both sit right of zero
    assert rs.ci_svg(None, None, None, "higher", "m").startswith("<span")
