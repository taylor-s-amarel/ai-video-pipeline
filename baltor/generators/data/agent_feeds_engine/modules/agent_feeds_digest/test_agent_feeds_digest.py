import json
from pathlib import Path

import agent_feeds_digest as d

FIX = Path(__file__).resolve().parent / "fixtures"
ITEMS = json.loads((FIX / "items.json").read_text())
W = json.loads((FIX / "watchlist.json").read_text())
W = dict(W, products=W["products"] + ["messages-api", "Example VPN"])


def digest():
    return d.build_digest(ITEMS, W, since_cursor="seq:10", next_cursor="seq:21", generated="2026-10-10T12:00:00Z")


def titles(dg, group):
    return [e["title"] for e in dg["groups"][group]]


def test_groups_and_counts():
    dg = digest()
    assert dg["spec"] == "baltor.agent-feed-digest/v1" and dg["project"] == "demo"
    assert dg["counts"]["considered"] == len(ITEMS)
    assert titles(dg, "breaking") == ["v3.0.0"]
    assert titles(dg, "deprecation") == ["Legacy completions endpoint will be removed on 2027-01-15"]
    sec = titles(dg, "security")
    assert sec[0].startswith("CVE-2099-0002")  # newest first
    assert any(t.startswith("GHSA-aaaa") for t in sec) and any("example-merge" in t for t in sec)
    assert not any("safe-lib" in t for g in d.GROUPS for t in titles(dg, g))  # not affected: below min_score
    low = d.build_digest(ITEMS, W, min_score=10, generated="2026-10-10T12:00:00Z")
    assert "GHSA-zzzz: safe-lib issue" in titles(low, "fyi")  # shown as FYI when the threshold allows
    assert "Model X 2 is generally available" in titles(dg, "new_capability")
    assert "Example AI: Elevated errors on the Messages API" in titles(dg, "fyi")
    assert not any("crypto" in t for g in d.GROUPS for t in titles(dg, g))  # excluded topic
    assert dg["counts"]["total"] == sum(dg["counts"][g] for g in d.GROUPS)


def test_cluster_collapsed_with_also_reported_by():
    sec = digest()["groups"]["security"]
    ghsa = [e for e in sec if "examplelib" in e["title"] or "GHSA-aaaa" in e["title"]]
    assert len(ghsa) == 1 and ghsa[0]["also_reported_by"] == ["pypi-examplelib"]


def test_suggested_actions():
    dg = digest()
    by_title = {e["title"]: e for g in d.GROUPS for e in dg["groups"][g]}
    ghsa = next(e for t, e in by_title.items() if t.startswith("GHSA-aaaa"))
    assert ghsa["suggested_action"] == "Upgrade examplelib to 2.31.0 or later (requirements.txt pins 2.30.0)."
    merge = next(e for t, e in by_title.items() if "example-merge" in t)
    assert merge["suggested_action"].startswith("Check the resolved version of example-merge") and "2.1.1" in merge["suggested_action"]
    kev = next(e for t, e in by_title.items() if t.startswith("CVE-2099-0002"))
    assert "by 2026-10-30" in kev["suggested_action"]
    assert "before 2027-01-15" in by_title["Legacy completions endpoint will be removed on 2027-01-15"]["suggested_action"]
    assert by_title["v3.0.0"]["suggested_action"].startswith("Read the migration notes before upgrading example-cli to 3.0.0")
    low = d.build_digest(ITEMS, W, min_score=10, generated="2026-10-10T12:00:00Z")
    safe = next(e for e in low["groups"]["fyi"] if "safe-lib" in e["title"])
    assert safe["suggested_action"].startswith("Not affected") and safe["affected"] == "no"


def test_validates_against_contract_shape():
    dg = digest()
    for g in d.GROUPS:
        for e in dg["groups"][g]:
            assert set(["item_id", "title", "url", "group", "score", "reasons", "suggested_action"]) <= set(e)
            assert e["group"] == g and len(e["suggested_action"]) <= 400


def test_markdown(tmp_path):
    dg = digest()
    j, m = d.write_digest(dg, tmp_path)
    md = m.read_text()
    assert md.startswith("# What changed for demo")
    assert md.index("## Security") < md.index("## Breaking changes") < md.index("## FYI")
    assert "  - Action: Upgrade examplelib to 2.31.0 or later" in md
    assert "Next cursor: `seq:21`" in md
    assert json.loads(j.read_text())["next_cursor"] == "seq:21"


def test_empty_digest():
    dg = d.build_digest([], W, generated="2026-10-10T12:00:00Z")
    assert dg["counts"]["total"] == 0
    assert "Nothing relevant" in d.render_markdown(dg)
