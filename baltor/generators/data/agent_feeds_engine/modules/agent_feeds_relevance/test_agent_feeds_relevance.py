import json
from pathlib import Path

import pytest

import agent_feeds_relevance as r

W = json.loads((Path(__file__).resolve().parent / "fixtures" / "watchlist.json").read_text())


def item(**kw):
    base = {"id": "afi_x", "title": "", "url": "https://e.com", "summary": "", "vendor": None, "products": [],
            "versions": [], "change_types": [], "severity": None, "affected_packages": [], "cve_ids": [],
            "entities": [], "published": "2026-10-09T00:00:00Z"}
    base.update(kw)
    return base


@pytest.mark.parametrize("version,spec,eco,expected", [
    ("2.30.0", ">=2.3.0,<2.31.0", "PyPI", True),
    ("2.31.0", ">=2.3.0,<2.31.0", "PyPI", False),
    ("2.31.0rc1", "<2.31.0", "PyPI", True),
    ("1.4.5", "~=1.4.2", "PyPI", True),
    ("1.5.0", "~=1.4.2", "PyPI", False),
    ("1.9", "~=1.4", "PyPI", True),
    ("1.2.7", "==1.2.*", "PyPI", True),
    ("2.1.0", "^2.0.3", "npm", True),
    ("3.0.0", "^2.0.3", "npm", False),
    ("0.2.9", "^0.2.3", "npm", True),
    ("0.3.0", "^0.2.3", "npm", False),
    ("1.2.9", "~1.2.3", "npm", True),
    ("1.3.0", "~1.2.3", "npm", False),
    ("1.2.5", "1.2.x", "npm", True),
    ("2.3.4", "1.2.3 - 2.3.4", "npm", True),
    ("2.3.5", "1.2.3 - 2.3.4", "npm", False),
    ("1.0.0", "<1.4.2 || >=2.0.0,<2.1.1", "npm", True),
    ("2.1.0", "<1.4.2 || >=2.0.0,<2.1.1", "npm", True),
    ("1.9.9", "<1.4.2 || >=2.0.0,<2.1.1", "npm", False),
    ("1.0.200", "1.0", "crates.io", True),
    ("2.0.0", "1.0", "crates.io", False),
    ("1.0.5", "=1.0.5", "crates.io", True),
    ("1.0.6", "=1.0.5", "crates.io", False),
    ("1.9.0", "v1.9.0", "Go", True),
    ("3.0.0-beta.1", ">=3.0.0", "npm", False),
])
def test_version_in_spec(version, spec, eco, expected):
    assert r.version_in_spec(version, spec, eco) is expected


def test_unparseable_specs_are_unknown():
    assert r.spec_intervals("latest") is None
    assert r.spec_intervals("git+https://github.com/x/y.git") is None
    assert r.version_in_spec("1.0", "workspace:*") is None


def test_overlap():
    assert r.specs_overlap(">=1.0,<2", ">=1.5,<1.6", "PyPI")
    assert not r.specs_overlap(">=2.1.1", "<1.4.2 || >=2.0.0,<2.1.1", "npm")
    assert r.specs_overlap("^2.0.3", "<1.4.2 || >=2.0.0,<2.1.1", "npm")


def test_pinned_version_inside_advisory_range_scores_high():
    it = item(title="GHSA-aaaa: examplelib leaks headers", change_types=["security"], severity="medium",
              affected_packages=[{"ecosystem": "PyPI", "name": "examplelib", "version_range": ">=2.3.0,<2.31.0", "fixed": ["2.31.0"]}])
    rel = r.score_item(it, W)
    assert rel["affected"] == "yes" and rel["score"] >= 80
    assert rel["reasons"][0] == "examplelib==2.30.0 (requirements.txt) is inside the affected range >=2.3.0,<2.31.0; fixed in 2.31.0"


def test_pinned_version_outside_range_is_low():
    it = item(title="adv", change_types=["security"], severity="high",
              affected_packages=[{"ecosystem": "PyPI", "name": "safe_lib", "version_range": "<3.0.0"}])
    rel = r.score_item(it, W)
    assert rel["affected"] == "no" and rel["score"] <= 25


def test_range_overlap_is_maybe_and_name_normalisation():
    it = item(title="adv", change_types=["security"], severity="high",
              affected_packages=[{"ecosystem": "PyPI", "name": "example-tools", "version_range": ">=1.5,<1.6"}])
    rel = r.score_item(it, W)
    assert rel["affected"] == "maybe" and rel["score"] >= 60


def test_npm_multi_range_advisory():
    it = item(title="Prototype pollution", change_types=["security"], severity="critical",
              affected_packages=[{"ecosystem": "npm", "name": "example-merge", "version_range": "<1.4.2 || >=2.0.0,<2.1.1"}])
    rel = r.score_item(it, W)
    assert rel["affected"] == "maybe" and "severity critical" in rel["reasons"]


def test_low_severity_below_minimum_pushed_down():
    it = item(title="adv", change_types=["security"], severity="low",
              affected_packages=[{"ecosystem": "PyPI", "name": "examplelib", "version_range": "<2.31.0"}])
    assert r.score_item(it, W)["score"] <= 15


def test_release_of_dependency_outside_allowed_range():
    it = item(title="@example/sdk 6.0.0", change_types=["release"], products=["@example/sdk"],
              affected_packages=[{"ecosystem": "npm", "name": "@example/sdk", "version_range": "==6.0.0"}])
    rel = r.score_item(it, W)
    assert rel["score"] >= 30 and "outside your allowed range ^5.0.0" in rel["reasons"][0]


def test_prerelease_lowered():
    it = item(title="@example/sdk 6.0.0-beta.1", change_types=["release"], entities=["prerelease"],
              affected_packages=[{"ecosystem": "npm", "name": "@example/sdk", "version_range": "==6.0.0-beta.1"}])
    assert r.score_item(it, W)["score"] < 30


def test_nvd_cpe_matches_package_name():
    it = item(title="CVE-2099-0300", change_types=["security"], severity="high",
              affected_packages=[{"ecosystem": "cpe", "name": "example:image_library", "version_range": "<9.1.4"}])
    rel = r.score_item(it, W)
    assert rel["affected"] == "yes"


def test_go_module_and_crate():
    go = item(title="GO-2099-1", change_types=["security"], severity="high",
              affected_packages=[{"ecosystem": "Go", "name": "github.com/example/Cobra", "version_range": "<1.10.0"}])
    assert r.score_item(go, W)["affected"] == "yes"
    crate = item(title="RUSTSEC", change_types=["security"], severity="high",
                 affected_packages=[{"ecosystem": "crates.io", "name": "example-serde", "version_range": "<1.0.100"}])
    assert r.score_item(crate, W)["affected"] == "maybe"


def test_product_vendor_harness_topic_and_exclusion():
    assert r.score_item(item(title="example-cli v3.0.0", products=["example-cli"], change_types=["release", "breaking-change"]), W)["score"] >= 45
    v = r.score_item(item(title="New model", vendor="Example AI", change_types=["model-release"]), W)
    assert v["score"] >= 30 and "vendor Example AI is on the watchlist" in v["reasons"]
    h = r.score_item(item(title="Claude Code 2.2 adds hook events", change_types=["release"]), W)
    assert h["score"] >= 30
    t = r.score_item(item(title="A new open text-to-speech model"), W)
    assert t["score"] >= 15 and t["reasons"] == ["topic text-to-speech"]
    x = r.score_item(item(title="MCP server for crypto trading"), W)
    assert x["score"] == 0 and x["reasons"] == ["excluded topic 'crypto'"]
    assert r.score_item(item(title="Unrelated news"), W)["reasons"] == ["no watchlist match"]


def test_mcp_server_product_match():
    it = item(title="server-filesystem 2026.10.1 fixes path traversal", products=["@modelcontextprotocol/server-filesystem"],
              change_types=["release", "security"], severity="high")
    assert r.score_item(it, W)["score"] >= 45


def test_rank_filters_and_orders():
    items = [item(id="a", title="Unrelated"),
             item(id="b", title="adv", change_types=["security"], severity="high",
                  affected_packages=[{"ecosystem": "PyPI", "name": "examplelib", "version_range": "<2.31.0"}]),
             item(id="c", title="New model", vendor="Example AI")]
    ranked = r.rank(items, W)
    assert [i["id"] for i in ranked] == ["b", "c"]
    assert ranked[0]["relevance"]["affected"] == "yes"
