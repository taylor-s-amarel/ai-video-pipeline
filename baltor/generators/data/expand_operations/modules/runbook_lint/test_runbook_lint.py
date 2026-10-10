import datetime as dt
from pathlib import Path

import runbook_lint as m

TODAY = dt.date(2026, 10, 10)
GOOD = (Path(__file__).parent / "examples" / "checkout-5xx-runbook.md").read_text()


def test_example_runbook_passes():
    r = m.lint(GOOD, TODAY)
    assert r["errors"] == [] and r["warnings"] == [], r
    assert r["owner"] == "team-payments"


def test_missing_sections_owner_and_blocks():
    r = m.lint("# Thing\nJust restart it. TODO\n", TODAY)
    joined = " ".join(r["errors"])
    for s in ("summary", "rollback", "escalation", "no owner", "no last-reviewed", "fenced", "TODO"):
        assert s in joined


def test_stale_and_bad_dates():
    stale = GOOD.replace("last_reviewed: 2026-09-01", "last_reviewed: 2025-01-01")
    assert any("days ago" in e for e in m.lint(stale, TODAY)["errors"])
    bad = GOOD.replace("last_reviewed: 2026-09-01", "last_reviewed: last spring")
    assert any("not YYYY-MM-DD" in e for e in m.lint(bad, TODAY)["errors"])


def test_inline_owner_line_and_destructive_warning():
    text = ("# Summary\nOwner: sre\nLast reviewed: 2026-10-01\n# Symptoms\nx\n# Diagnosis\nverify\n# Mitigation\n"
            "```\nkubectl delete namespace shop\n```\n# Rollback\nx\n# Escalation\nx\nhttps://grafana.example/d/abc\n")
    r = m.lint(text, TODAY)
    assert r["errors"] == []
    assert any("destructive" in w for w in r["warnings"])


def test_cli(tmp_path):
    p = tmp_path / "r.md"
    p.write_text(GOOD)
    assert m.main([str(p), "--today", "2026-10-10"]) == 0
    p.write_text("# nothing\n")
    assert m.main([str(p), "--today", "2026-10-10", "--json"]) == 1
