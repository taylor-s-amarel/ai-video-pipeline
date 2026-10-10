import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import pytest

import feed_collection_opml as m

COLLECTION = {
    "spec": "baltor.feed-collection/v1",
    "id": "community-test",
    "title": "Test & <Demo> collection",
    "description": "fixture",
    "updated": "2026-10-10",
    "items": [
        {"id": "r-godot", "title": "r/godot", "url": "https://www.reddit.com/r/godot/.rss", "kind": "service",
         "summary": "Official \"Godot\" subreddit & news", "verified_on": "2026-10-10",
         "verification": "search-result", "tags": ["subreddit", "godot"]},
        {"id": "gh-godot", "title": "Godot releases", "url": "https://github.com/godotengine/godot/releases.atom",
         "kind": "repository", "summary": "Releases", "verified_on": "2026-10-10", "verification": "fetched",
         "tags": ["github"]},
        {"id": "policy", "title": "YouTube policy", "url": "https://support.google.com/youtube/answer/1311392",
         "kind": "guidance", "summary": "Policy page", "verified_on": "2026-10-10"},
        {"id": "yt", "title": "Channel", "kind": "service", "summary": "", "verified_on": "2026-10-10",
         "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCxboW7x0jZqFdvMdCFKTMsQ"},
    ],
}
NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("url,expected", [
    ("https://www.reddit.com/r/godot/.rss", True),
    ("https://github.com/x/y/releases.atom", True),
    ("https://rss.arxiv.org/rss/cs.AI", True),
    ("https://forum.godotengine.org/latest.rss", True),
    ("https://hnrss.org/newest?q=godot+OR+blender", True),
    ("https://www.ben-evans.com/benedictevans?format=rss", True),
    ("https://en.wikipedia.org/w/api.php?action=featuredfeed&feed=potd&feedformat=atom", True),
    ("https://www.cisa.gov/cybersecurity-advisories/all.xml", True),
    ("https://example.org/sitemap.xml", False),
    ("https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/01/15", False),
    ("https://support.google.com/youtube/answer/1311392", False),
    ("https://www.latent.space/", False),
])
def test_is_feed_url(url, expected):
    assert m.is_feed_url(url) is expected


def test_html_url_for_known_shapes():
    assert m.html_url_for("https://www.reddit.com/r/godot/.rss") == "https://www.reddit.com/r/godot/"
    assert m.html_url_for("https://github.com/a/b/releases.atom") == "https://github.com/a/b/releases"
    assert m.html_url_for("https://github.com/a/b/commits/main.atom") == "https://github.com/a/b/commits"
    assert m.html_url_for("https://www.youtube.com/feeds/videos.xml?channel_id=UC1") == \
        "https://www.youtube.com/channel/UC1"
    assert m.html_url_for("https://rss.arxiv.org/rss/cs.SE") == "https://arxiv.org/list/cs.SE/new"
    assert m.html_url_for("https://forum.godotengine.org/latest.rss") == "https://forum.godotengine.org/latest"
    assert m.html_url_for("https://example.org/feed") is None


def test_opml_is_valid_escaped_and_skips_pages_by_default():
    text = m.collection_to_opml(COLLECTION, now=NOW)
    root = ET.fromstring(text)
    assert root.tag == "opml" and root.get("version") == "2.0"
    assert root.find("head/title").text == "Test & <Demo> collection"
    assert root.find("head/dateCreated").text == "Sat, 10 Oct 2026 12:00:00 GMT"
    folder = root.find("body/outline")
    assert folder.get("baltorCollection") == "community-test"
    feeds = folder.findall("outline")
    assert [f.get("xmlUrl") for f in feeds] == [
        "https://www.reddit.com/r/godot/.rss", "https://github.com/godotengine/godot/releases.atom",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCxboW7x0jZqFdvMdCFKTMsQ"]
    assert feeds[0].get("description") == 'Official "Godot" subreddit & news'
    assert feeds[0].get("category") == "subreddit,godot"
    assert feeds[0].get("htmlUrl") == "https://www.reddit.com/r/godot/"
    assert feeds[1].get("baltorVerification") == "fetched"
    assert "description" not in feeds[2].attrib


def test_include_pages_adds_link_outlines():
    root = ET.fromstring(m.collection_to_opml(COLLECTION, include_pages=True, now=NOW))
    links = [o for o in root.iter("outline") if o.get("type") == "link"]
    assert [o.get("url") for o in links] == ["https://support.google.com/youtube/answer/1311392"]


def test_group_by_kind_creates_subfolders():
    root = ET.fromstring(m.collection_to_opml(COLLECTION, group_by="kind", now=NOW))
    folder = root.find("body/outline")
    assert sorted(o.get("text") for o in folder.findall("outline")) == ["repository", "service"]


def test_roundtrip_parse_opml_and_multiple_collections():
    other = dict(COLLECTION, id="community-other", title="Other",
                 items=[{"id": "a", "title": "A", "url": "https://a.example/feed.xml", "kind": "article",
                         "summary": "", "verified_on": "2026-10-10"}])
    text = m.collections_to_opml([COLLECTION, other], title="Both", now=NOW)
    feeds = m.parse_opml(text)
    assert len(feeds) == 4
    assert feeds[-1] == {"title": "A", "xml_url": "https://a.example/feed.xml", "html_url": None,
                         "folder": "Other", "category": []}
    assert feeds[0]["folder"] == "Test & <Demo> collection"


def test_empty_collections_are_dropped():
    only_pages = dict(COLLECTION, items=[COLLECTION["items"][2]])
    root = ET.fromstring(m.collection_to_opml(only_pages, now=NOW))
    assert root.find("body/outline") is None


def test_parse_opml_refuses_entities():
    with pytest.raises(ValueError):
        m.parse_opml('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><opml><body/></opml>')


def test_load_collection_and_cli(tmp_path, capsys):
    src = tmp_path / "community-test.json"
    src.write_text(json.dumps(COLLECTION), encoding="utf-8")
    out = tmp_path / "out.opml"
    assert m.main([str(src), "-o", str(out), "--group-by", "tags"]) == 0
    assert len(m.parse_opml(out.read_text(encoding="utf-8"))) == 3
    assert m.main(["--list", str(out)]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert {f["xml_url"] for f in listed} >= {"https://www.reddit.com/r/godot/.rss"}
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        m.load_collection(bad)


def test_expand_watchlist_resolves_collections_items_urls_and_pages(tmp_path, capsys):
    (tmp_path / "community-test.json").write_text(json.dumps(COLLECTION), encoding="utf-8")
    watch = {"sources": [
        {"collection": "community-test", "weight": 1.0},
        {"collection": "community-test", "item_ids": ["gh-godot", "nope"], "weight": 2.5},
        {"url": "https://hnrss.org/newest?q=godot", "weight": 0.5},
        {"url": "https://www.latent.space/"},
        {"collection": "community-absent"},
    ]}
    res = m.expand_watchlist(watch, tmp_path)
    by_url = {f["url"]: f for f in res["feeds"]}
    assert set(by_url) == {"https://www.reddit.com/r/godot/.rss", "https://github.com/godotengine/godot/releases.atom",
                           "https://www.youtube.com/feeds/videos.xml?channel_id=UCxboW7x0jZqFdvMdCFKTMsQ",
                           "https://hnrss.org/newest?q=godot"}
    assert by_url["https://github.com/godotengine/godot/releases.atom"]["weight"] == 2.5  # highest weight wins
    assert [p["url"] for p in res["pages"]] == ["https://support.google.com/youtube/answer/1311392",
                                               "https://www.latent.space/"]
    assert res["missing"] == ["community-test#nope", "community-absent"]
    wl = tmp_path / "watch.json"
    wl.write_text(json.dumps(watch), encoding="utf-8")
    assert m.main(["--watchlist-urls", str(wl), "--feeds-dir", str(tmp_path)]) == 0
    out = capsys.readouterr()
    assert "https://www.reddit.com/r/godot/.rss" in out.out.splitlines()
    assert "missing: community-absent" in out.err
