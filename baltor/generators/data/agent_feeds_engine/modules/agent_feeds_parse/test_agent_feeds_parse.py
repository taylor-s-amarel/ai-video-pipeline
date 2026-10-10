from pathlib import Path

import pytest

import agent_feeds_parse as p

FIX = Path(__file__).resolve().parent / "fixtures"
NOW = "2026-10-10T12:00:00Z"


def load(name: str) -> bytes:
    return (FIX / name).read_bytes()


def run(name, url="", **kw):
    return p.parse(load(name), url=url, source_id="test-src", collection="test", now=NOW, **kw)


def check_item(it):
    for key in ("id", "source_id", "title", "url", "summary", "change_types", "dedupe_key", "products",
                "versions", "affected_packages", "cve_ids", "entities"):
        assert key in it, key
    assert it["id"].startswith("afi_")
    assert len(it["summary"]) <= 400
    assert it["url"]


def test_rss2_strips_html_tracking_and_detects_deprecation():
    items = run("rss2.xml", url="https://example.com/changelog/rss")
    assert len(items) == 2
    first = items[0]
    check_item(first)
    assert first["published"] == "2026-10-08T16:00:00Z"
    assert "deprecation" in first["change_types"]
    assert "<" not in first["summary"] and "alert" not in first["summary"]
    assert first["entities"] == ["api"]
    assert p.normalize_url(first["url"]) == "https://example.com/changelog/legacy-completions"
    assert items[1]["versions"] == ["4.2.0"]


def test_rss1_rdf():
    items = run("rss1.rdf")
    assert items[0]["title"] == "Dataset v2 released"
    assert items[0]["published"] == "2026-10-01T12:00:00Z"


def test_atom_security_entry_gets_cve_and_short_summary():
    items = run("atom.xml")
    sec = items[0]
    assert sec["title"].startswith("Security update: fix for CVE-2099-0101")
    assert sec["cve_ids"] == ["CVE-2099-0101"]
    assert "security" in sec["change_types"]
    assert sec["url"] == "https://example.net/blog/gateway-security-update/"
    assert items[1]["summary"].startswith("A long article body")


def test_json_feed():
    items = run("feed.json")
    assert [i["title"] for i in items] == ["Model X 2 is generally available", "Pricing update for batch requests"]
    assert items[0]["published"] == "2026-10-07T21:00:00Z"
    assert items[1]["url"] == "https://models.example.ai/posts/pricing-update"
    assert "pricing" in items[1]["change_types"]


def test_github_releases_versions_vendor_breaking_and_prerelease():
    items = run("github_releases.atom", url="https://github.com/example-org/example-cli/releases.atom")
    rc, major = items
    assert major["versions"] == ["3.0.0"]
    assert major["vendor"] == "example-org" and major["products"][0] == "example-cli"
    assert "breaking-change" in major["change_types"] and "release" in major["change_types"]
    assert "prerelease" in rc["entities"]
    assert all(i["source_format"] == "github-releases" for i in items)


def test_statuspage_json_incident_and_maintenance():
    items = run("statuspage_summary.json", url="https://status.example.ai/api/v2/summary.json")
    inc = next(i for i in items if "incident" in i["change_types"])
    assert inc["severity"] == "high"
    assert inc["url"] == "https://stspg.io/example1"
    assert inc["summary"].startswith("Monitoring: A fix has been implemented")
    assert "status:monitoring" in inc["entities"]
    assert inc["vendor"] == "Example AI"
    maint = next(i for i in items if "event" in i["change_types"])
    assert maint["severity"] == "low"


def test_statuspage_history_rss():
    items = run("statuspage_history.rss", url="https://status.example.ai/history.rss")
    assert items[0]["change_types"] == ["incident"]
    assert "status:resolved" in items[0]["entities"]


def test_cisa_kev_newest_first_with_ransomware_flag():
    items = run("cisa_kev.json", url="https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
    assert [i["cve_ids"][0] for i in items] == ["CVE-2099-0002", "CVE-2099-0001"]
    assert items[0]["severity"] == "critical" and "ransomware" in items[0]["entities"]
    assert items[1]["severity"] == "high" and items[1]["vendor"] == "Examplesoft"
    assert items[1]["url"] == "https://nvd.nist.gov/vuln/detail/CVE-2099-0001"


def test_osv_single_record_ranges_and_severity():
    items = run("osv_vuln.json")
    it = items[0]
    assert it["affected_packages"] == [{"ecosystem": "PyPI", "name": "examplelib",
                                        "version_range": ">=2.3.0,<2.31.0", "fixed": ["2.31.0"]}]
    assert it["severity"] == "medium" and it["cve_ids"] == ["CVE-2099-0100"]
    assert it["cvss"] == 5.3


def test_osv_query_result_multiple_ranges_skips_withdrawn():
    items = run("osv_query.json", url="https://api.osv.dev/v1/query")
    assert len(items) == 1
    assert items[0]["affected_packages"][0]["version_range"] == "<1.4.2 || >=2.0.0,<2.1.1"
    assert items[0]["severity"] == "critical"


def test_nvd_cpe_ranges_and_rejected_skipped():
    items = run("nvd.json", url="https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate=x")
    assert len(items) == 1
    it = items[0]
    assert it["severity"] == "high" and it["cvss"] == 8.8
    assert it["vendor"] == "example" and it["products"] == ["image_library"]
    assert it["affected_packages"][0] == {"ecosystem": "cpe", "name": "example:image_library", "version_range": "<9.1.4"}


def test_pypi_json_releases_yanked_prerelease_and_vulns():
    items = run("pypi.json", url="https://pypi.org/pypi/examplelib/json")
    rel = {i["versions"][0]: i for i in items if "release" in i["change_types"]}
    assert set(rel) == {"2.30.0", "2.30.1", "2.31.0", "2.32.0rc1"}
    assert "yanked" in rel["2.30.1"]["entities"] and rel["2.30.1"]["summary"].startswith("Yanked: Broken")
    assert "prerelease" in rel["2.32.0rc1"]["entities"]
    vuln = next(i for i in items if "security" in i["change_types"])
    assert vuln["affected_packages"][0]["version_range"] == "<2.31.0"
    assert vuln["cve_ids"] == ["CVE-2099-0100"]


def test_pypi_release_rss_enriched_from_url():
    items = run("pypi_releases.xml", url="https://pypi.org/rss/project/examplelib/releases.xml")
    assert items[0]["title"] == "examplelib 2.31.0"
    assert items[0]["affected_packages"] == [{"ecosystem": "PyPI", "name": "examplelib", "version_range": "==2.31.0"}]


def test_npm_versions_deprecation_and_latest():
    items = run("npm.json", url="https://registry.npmjs.org/@example%2fsdk")
    by_ver = {i["versions"][0]: i for i in items}
    assert "latest" in by_ver["5.1.0"]["entities"]
    assert "deprecation" in by_ver["4.9.9"]["change_types"]
    assert by_ver["5.1.0"]["url"] == "https://www.npmjs.com/package/@example/sdk/v/5.1.0"
    assert items[0]["versions"] == ["5.1.0"]


def test_endoflife_v1_window():
    items = run("endoflife_v1.json", url="https://endoflife.date/api/v1/products/examplelang")
    titles = [i["title"] for i in items]
    assert "ExampleLang 3.10 reaches end of life on 2026-10-31" in titles
    assert "ExampleLang 3.14.3" in titles
    assert not any("3.9" in t for t in titles)  # EOL a year ago, outside the 30 day window
    eol = next(i for i in items if "deprecation" in i["change_types"])
    assert eol["published"] is None  # future date is not a publish date


def test_endoflife_legacy():
    items = run("endoflife_legacy.json", url="https://endoflife.date/api/nodejs.json")
    assert any(i["title"] == "nodejs 20 reaches end of life on 2026-10-20" for i in items)
    assert any(i["title"] == "nodejs 22.20.0" for i in items)


def test_arxiv():
    items = run("arxiv.atom", url="https://export.arxiv.org/api/query?search_query=cat:cs.AI")
    it = items[0]
    assert it["title"] == "Tool-Use Agents That Read Their Own Changelogs"
    assert it["url"] == "http://arxiv.org/abs/2610.01234v1"
    assert "arxiv:2610.01234" in it["entities"] and "cs.SE" in it["entities"]
    assert it["change_types"] == ["research"] and it["authors"] == ["A. Researcher", "B. Scientist"]


def test_hf_daily_papers():
    items = run("hf_daily_papers.json", url="https://huggingface.co/api/daily_papers")
    it = items[0]
    assert it["url"] == "https://huggingface.co/papers/2610.01234"
    assert it["summary"] == "Agents that read release notes break fewer upgrades."
    assert "coding agents" in it["entities"] and it["links"] == ["https://github.com/example/changelog-agents"]


def test_go_proxy_latest_and_list_with_escaped_path():
    items = run("goproxy_latest.json", url="https://proxy.golang.org/github.com/example/!cobra/@latest")
    assert items[0]["title"] == "github.com/example/Cobra v1.10.2"
    assert items[0]["affected_packages"][0] == {"ecosystem": "Go", "name": "github.com/example/Cobra",
                                                "version_range": "==1.10.2"}
    lst = run("goproxy_list.txt", url="https://proxy.golang.org/github.com/example/!cobra/@v/list")
    assert [i["versions"][0] for i in lst][:2] == ["1.10.2", "1.10.1"]


def test_crates_index():
    items = run("crates_index.ndjson", url="https://index.crates.io/ex/am/example-serde")
    assert items[0]["versions"] == ["1.0.227"]
    assert "yanked" in items[1]["entities"]


def test_sitemap_and_ical():
    items = run("sitemap.xml")
    assert items[0]["title"] == "2026 10 api updates" and items[0]["published"] == "2026-10-09T00:00:00Z"
    ev = run("events.ics")[0]
    assert ev["title"] == "Example DevDay: agents and tools"
    assert ev["change_types"] == ["event"] and ev["published"] == "2026-11-05T17:00:00Z"


def test_detection_from_body():
    assert p.detect_format(load("feed.json")) == "json-feed"
    assert p.detect_format(load("cisa_kev.json")) == "cisa-kev"
    assert p.detect_format(load("nvd.json")) == "nvd"
    assert p.detect_format(load("pypi.json")) == "pypi-json"
    assert p.detect_format(load("npm.json")) == "npm"
    assert p.detect_format(load("statuspage_summary.json")) == "statuspage-json"
    assert p.detect_format(load("osv_vuln.json")) == "osv"
    assert p.detect_format(load("hf_daily_papers.json")) == "hf-papers"
    assert p.detect_format(load("endoflife_legacy.json")) == "endoflife"
    assert p.detect_format(load("atom.xml")) == "atom"
    assert p.detect_format(load("rss1.rdf")) == "rss"
    assert p.detect_format(load("arxiv.atom")) == "arxiv"
    assert p.detect_format(load("events.ics")) == "ical"


def test_collection_feed_format_mapping():
    assert run("statuspage_summary.json", fmt="statuspage")[0]["source_format"] == "statuspage-json"
    assert run("osv_vuln.json", fmt="json-api")[0]["source_format"] == "osv"


def test_entity_declarations_refused():
    with pytest.raises(p.ParseError):
        run("evil_entity.xml", fmt="rss")


def test_ids_are_stable_and_dedupe_key_ignores_tracking():
    a = run("rss2.xml")
    b = run("rss2.xml")
    assert [i["id"] for i in a] == [i["id"] for i in b]
    x = p.make_item(source_id="s", title="t", url="https://www.Example.com/a/?utm_source=x&b=2&a=1#frag")
    y = p.make_item(source_id="s2", title="t", url="http://example.com/a?a=1&b=2")
    assert x["dedupe_key"] == y["dedupe_key"]


@pytest.mark.parametrize("vector,score", [
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", 9.8),
    ("CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:N/A:N", 5.3),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", 6.1),
    ("CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:N", 0.0),
])
def test_cvss3(vector, score):
    assert p.cvss3_base_score(vector) == score


def test_dates():
    assert p.parse_date("Thu, 08 Oct 2026 16:00:00 GMT") == "2026-10-08T16:00:00Z"
    assert p.parse_date("2026-10-09T15:44:11.865123456Z") == "2026-10-09T15:44:11Z"
    assert p.parse_date("2026-10-09") == "2026-10-09T00:00:00Z"
    assert p.parse_date(1760000000) == "2025-10-09T08:53:20Z"
    assert p.parse_date("not a date") is None


def test_summary_is_short():
    it = p.make_item(source_id="s", title="x", url="https://e.com", summary="word " * 500)
    assert len(it["summary"]) <= 400 and it["summary"].endswith("…")
