import json
from pathlib import Path

import pytest

import agent_feeds_store as st

mk = st._parse.make_item
FIX = Path(__file__).resolve().parent / "fixtures"


def osv_item():
    return mk(source_id="osv-pypi", title="GHSA-aaaa-bbbb-cccc: examplelib leaks Proxy-Authorization headers",
              url="https://osv.dev/vulnerability/GHSA-aaaa-bbbb-cccc", published="2026-10-08T18:00:00Z",
              summary="examplelib before 2.31.0 forwards the Proxy-Authorization header.", change_types=["security"],
              severity="medium", cve_ids=["CVE-2099-0100"], entities=["CVE-2099-0100"],
              affected_packages=[{"ecosystem": "PyPI", "name": "examplelib", "version_range": ">=2.3.0,<2.31.0"}],
              products=["examplelib"], infer=False)


def kev_item():
    return mk(source_id="cisa-kev", title="CVE-2099-0100: examplelib credential leak", url="https://nvd.nist.gov/vuln/detail/CVE-2099-0100",
              published="2026-10-09T00:00:00Z", change_types=["security"], severity="high", cve_ids=["CVE-2099-0100"],
              entities=["known-exploited"], infer=False)


@pytest.fixture()
def store(tmp_path):
    s = st.FeedStore(tmp_path / "feeds.sqlite")
    yield s
    s.close()


def test_insert_and_cursor(store):
    items = json.loads((FIX / "items.json").read_text())
    report = store.upsert_items(items)
    assert report["inserted"] == len(items)
    got, cur = store.since(None, limit=100)
    assert [i["title"] for i in got][0] == "Old release 1.0.0"  # oldest first
    assert cur == f"seq:{store.max_seq()}"
    again, cur2 = store.since(cur)
    assert again == [] and cur2 == cur


def test_duplicate_url_from_other_source_is_recorded_not_inserted(store):
    a = mk(source_id="blog", title="Model X 2 is generally available", url="https://models.example.ai/posts/model-x-2",
           published="2026-10-07T21:00:00Z", vendor="Example AI")
    b = mk(source_id="newsletter", title="Model X 2 GA!", url="https://www.models.example.ai/posts/model-x-2/?utm_source=nl",
           published="2026-10-08T07:00:00Z", vendor="Example AI")
    assert store.upsert_items([a])["inserted"] == 1
    assert store.upsert_items([b])["duplicate"] == 1
    stored = store.get(a["id"])
    assert stored["sources"] == ["newsletter"]


def test_unchanged_and_updated_items(store):
    item = osv_item()
    store.upsert_items([item])
    _, cur = store.since(None)
    assert store.upsert_items([item])["unchanged"] == 1
    changed = dict(item, severity="high", summary="Severity raised after review.")
    assert store.upsert_items([changed])["updated"] == 1
    resurfaced, _ = store.since(cur)
    assert [i["id"] for i in resurfaced] == [item["id"]] and resurfaced[0]["severity"] == "high"


def test_cluster_by_shared_cve(store):
    osv, kev = osv_item(), kev_item()
    store.upsert_items([osv])
    rep = store.upsert_items([kev])
    assert rep["clustered"] == 1
    assert store.get(kev["id"])["cluster_id"] == osv["id"]
    assert len(store.cluster(osv["id"])) == 2


def test_cluster_by_product_version_and_title_similarity(store):
    gh = mk(source_id="gh", title="v3.0.0", url="https://github.com/example-org/example-cli/releases/tag/v3.0.0",
            published="2026-10-09T19:28:59Z", vendor="example-org", products=["example-cli"], versions=["3.0.0"])
    npm = mk(source_id="npm", title="example-cli 3.0.0", url="https://www.npmjs.com/package/example-cli/v/3.0.0",
             published="2026-10-09T19:40:00Z", products=["example-cli"], versions=["3.0.0"],
             affected_packages=[{"ecosystem": "npm", "name": "example-cli", "version_range": "==3.0.0"}])
    blog = mk(source_id="blog", title="Introducing Model X 2", url="https://models.example.ai/a", vendor="Example AI",
              published="2026-10-07T00:00:00Z")
    post = mk(source_id="news", title="Introducing Model X 2!", url="https://news.example.org/b", vendor="Example AI",
              published="2026-10-08T00:00:00Z")
    unrelated = mk(source_id="news", title="Introducing Model X 2!", url="https://other.example/c", vendor="Other Corp",
                   published="2026-10-08T00:00:00Z")
    store.upsert_items([gh, blog])
    store.upsert_items([npm, post, unrelated])
    assert store.get(npm["id"])["cluster_id"] == gh["id"]
    assert store.get(post["id"])["cluster_id"] == blog["id"]
    assert store.get(unrelated["id"])["cluster_id"] == unrelated["id"]


def test_search_filters_and_collapses_clusters(store):
    store.upsert_items([osv_item(), kev_item()] + json.loads((FIX / "items.json").read_text()))
    hits = store.search("proxy authorization")
    assert hits and hits[0]["source_id"] == "osv-pypi"
    assert len(store.search("CVE-2099-0100")) == 1  # two items, one cluster
    assert len(store.search("CVE-2099-0100", collapse_clusters=False)) == 2
    sec = store.search("", change_types=["security"], limit=50)
    assert all("security" in i["change_types"] for i in sec)
    recent = store.search("", since="2026-10-01", limit=50)
    assert all((i["published"] or "") >= "2026-10-01" for i in recent)
    assert store.search("", since="seq:2", limit=50, collapse_clusters=False)
    assert all(i["seq"] > 2 for i in store.search("", since="seq:2", limit=50, collapse_clusters=False))


def test_for_packages(store):
    store.upsert_items([osv_item(), kev_item()])
    hits = store.for_packages([("PyPI", "ExampleLib")], change_types=["security"])
    assert [h["source_id"] for h in hits] == ["osv-pypi"]


def test_state_and_named_cursors_persist(tmp_path):
    path = tmp_path / "s.sqlite"
    with st.FeedStore(path) as s:
        s.set_state({"source_id": "gh", "url": "https://github.com/a/b/releases.atom", "failures": 0, "etag": '"x"'})
        s.upsert_items([osv_item()])
        s.set_cursor("project:demo", "seq:1")
    with st.FeedStore(path, readonly=True) as ro:
        assert ro.get_state("gh")["etag"] == '"x"'
        assert ro.get_cursor("project:demo") == "seq:1"
        assert ro.search("examplelib")
        assert ro.stats()["items"] == 1


def test_bad_cursor_rejected(store):
    with pytest.raises(ValueError):
        store.since("2026-10-01")


def test_prune_keeps_high_severity(store):
    old = mk(source_id="x", title="Ancient post", url="https://e.com/old", published="2020-01-01T00:00:00Z")
    old_sec = mk(source_id="x", title="Ancient critical CVE-2099-0001", url="https://e.com/oldsec",
                 published="2020-01-01T00:00:00Z", severity="critical", change_types=["security"])
    store.upsert_items([old, old_sec])
    assert store.prune(365) == 1
    assert store.get(old_sec["id"])


def test_title_similarity():
    assert st.title_similarity("Claude Code v2.1.0 released", "Claude Code 2.1.0 released") == 1.0
    assert st.title_similarity("Python 3.14 is out", "Rust 1.90 is out") < 0.85
