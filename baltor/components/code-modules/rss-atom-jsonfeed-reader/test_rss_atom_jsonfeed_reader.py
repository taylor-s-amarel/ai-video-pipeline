import io
import json
import urllib.error
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path

import pytest

import rss_atom_jsonfeed_reader as r

FIX = Path(__file__).resolve().parent / "fixtures"


def load(name):
    return (FIX / name).read_bytes()


def test_rss2_items_are_normalised():
    feed = r.parse_feed(load("rss2.xml"), "https://news.example.org/rss.xml")
    assert feed["format"] == "rss2" and feed["title"] == "Example Godot News"
    first = feed["items"][0]
    assert first["title"] == "Godot 4.7 & the new tile editor"
    # tracking parameters and fragment removed, remaining query sorted
    assert first["url"] == "https://news.example.org/posts/godot-47?a=1&b=2"
    assert first["published"] == "2026-10-09T19:28:59Z"
    assert first["authors"] == ["Ada Example"]
    assert first["tags"] == ["godot", "release"]
    assert "alert" not in first["summary"] and first["summary"] == "The tile editor got faster. Read more."
    assert first["source"] == {"feed_url": "https://news.example.org/rss.xml", "feed_title": "Example Godot News",
                               "format": "rss2"}


def test_rss2_relative_links_timezones_enclosures_and_guid_permalinks():
    items = r.parse_feed(load("rss2.xml"), "https://news.example.org/rss.xml")["items"]
    rel = items[1]
    assert rel["url"] == "https://news.example.org/posts/relative"
    assert rel["published"] == "2026-09-29T12:00:00Z"  # -0400 converted to UTC
    assert rel["enclosures"] == [{"url": "https://cdn.example.org/ep1.mp3", "type": "audio/mpeg", "length": 12345}]
    undated = items[2]
    assert undated["url"] == "https://news.example.org/notes/undated" and undated["published"] is None


def test_atom_github_style_releases():
    feed = r.parse_feed(load("atom.xml"), "https://github.com/example/tool/releases.atom")
    assert feed["format"] == "atom" and feed["title"] == "Release notes from tool"
    rel = feed["items"][0]
    assert rel["title"] == "v2.1.0"
    assert rel["url"] == "https://github.com/example/tool/releases/tag/v2.1.0"
    assert rel["published"] == "2026-10-09T19:28:59Z"  # falls back to <updated>
    assert rel["summary"] == "Added hooks" and rel["authors"] == ["octocat"]
    old = feed["items"][2]
    assert old["updated"] == "2026-09-20T08:00:00Z"  # nanoseconds trimmed, +02:00 converted
    assert old["enclosures"][0]["length"] == 42
    assert feed["items"][1]["tags"] == ["Godot"]


def test_json_feed_items_and_attachments():
    feed = r.parse_feed(load("feed.json"), "https://json.example.org/feed.json")
    assert feed["format"] == "jsonfeed"
    a, b = feed["items"]
    assert a["url"] == "https://json.example.org/a" and a["authors"] == ["Feed Author"]
    assert a["enclosures"][0]["url"] == "https://json.example.org/audio/sample.wav"
    assert a["tags"] == ["kokoro", "tts"]
    assert b["url"] == "https://elsewhere.example.com/b" and b["authors"] == ["Guest"]
    assert b["title"].startswith("No title, only text")
    assert b["published"] == "2026-09-01T08:30:00Z"


def test_rss1_rdf():
    feed = r.parse_feed(load("rss1.rdf"), "https://arxiv.example.org/rss/cs.SE")
    assert feed["format"] == "rss1"
    item = feed["items"][0]
    assert item["title"] == "Agents That Repair Builds" and item["published"] == "2026-10-10T00:00:00Z"
    assert item["tags"] == ["cs.SE"]


def test_entity_declarations_are_refused():
    with pytest.raises(r.FeedError):
        r.parse_feed(load("evil.xml"))


def test_garbage_is_a_feed_error():
    for bad in (b"not a feed", b"{\"title\": \"no version\"}", b"<html><body/></html>", b"[1, 2]"):
        with pytest.raises(r.FeedError):
            r.parse_feed(bad)


def test_dedupe_across_feeds_keeps_newest_and_records_other_sources():
    docs = [("https://news.example.org/rss.xml", load("rss2.xml")),
            ("https://github.com/example/tool/releases.atom", load("atom.xml"))]
    items, errors = r.merge_feeds(docs)
    assert errors == []
    godot = [i for i in items if i["url"] == "https://news.example.org/posts/godot-47?a=1&b=2"]
    assert len(godot) == 1
    assert godot[0]["source"]["feed_url"] == "https://news.example.org/rss.xml"  # 19:28 beats 18:30
    assert godot[0]["also_in"] == ["https://github.com/example/tool/releases.atom"]
    dated = [i["published"] for i in items if i["published"]]
    assert dated == sorted(dated, reverse=True)
    assert items[-1]["published"] is None  # undated last


def test_dedupe_by_title_can_be_disabled():
    a = {"url": "https://a.example/x", "guid": "", "title": "Exactly the same headline here",
         "published": "2026-10-01T00:00:00Z", "source": {"feed_url": "A"}}
    b = dict(a, url="https://b.example/y", source={"feed_url": "B"})
    assert len(r.dedupe([a, b])) == 1
    assert len(r.dedupe([a, b], by_title=False)) == 2


def test_filter_since_absolute_relative_and_undated():
    items = r.parse_feed(load("rss2.xml"), "f")["items"]
    recent = r.filter_since(items, "2026-10-01")
    assert [i["title"] for i in recent] == ["Godot 4.7 & the new tile editor"]
    assert len(r.filter_since(items, "2026-10-01", keep_undated=True)) == 2
    assert r.filter_since(items, None) == items
    assert r.filter_since(items, datetime(2030, 1, 1)) == []
    fresh = {"published": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    assert r.filter_since([fresh], "7d") == [fresh]
    with pytest.raises(ValueError):
        r.filter_since(items, "next tuesday")


def test_parse_date_variants():
    assert r.parse_date("Thu, 09 Oct 2026 19:28:59 GMT").isoformat() == "2026-10-09T19:28:59+00:00"
    assert r.parse_date("2026-10-09T21:28:59+0200").hour == 19
    assert r.parse_date("2026-10-09 19:28:59").minute == 28
    assert r.parse_date("2026-10-09").day == 9
    assert r.parse_date("") is None and r.parse_date("soon") is None


def test_canonical_url():
    assert r.canonical_url("HTTPS://Example.ORG:443/a?utm_source=x&z=1&a=2#top") == "https://example.org/a?a=2&z=1"
    assert r.canonical_url("http://example.org:8080") == "http://example.org:8080/"
    assert r.canonical_url("../b?gclid=1", "https://example.org/x/y/") == "https://example.org/x/b"
    assert r.canonical_url("") == ""


def test_discover_feeds_from_html():
    found = r.discover_feeds((FIX / "page.html").read_text(), "https://blog.example.org/posts/1")
    assert [f["url"] for f in found] == ["https://blog.example.org/feed.xml", "https://blog.example.org/atom.xml",
                                         "https://blog.example.org/posts/feed.json"]
    assert [f["format"] for f in found] == ["rss", "atom", "jsonfeed"]


def test_host_spacer_waits_between_requests_to_same_host():
    now = [100.0]
    slept = []
    spacer = r.HostSpacer(min_interval_s=10, clock=lambda: now[0], sleep=slept.append)
    assert spacer.wait("https://a.example/1") == 0
    now[0] = 103.0
    assert spacer.wait("https://a.example/2") == pytest.approx(7.0)
    assert spacer.wait("https://b.example/1") == 0
    assert slept == [pytest.approx(7.0)]


class FakeResponse(io.BytesIO):
    def __init__(self, body, headers=None, status=200):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_fetch_sends_conditional_headers_and_handles_304_and_429():
    seen = {}

    def ok(req, timeout):
        seen.update(dict(req.header_items()))
        return FakeResponse(b"<rss/>", {"ETag": '"v2"', "Last-Modified": "Thu, 09 Oct 2026 19:00:00 GMT"})

    res = r.fetch("https://feeds.example.org/a.xml", etag='"v1"', last_modified="x", opener=ok)
    assert res["status"] == 200 and res["etag"] == '"v2"'
    assert seen["If-none-match"] == '"v1"' and seen["User-agent"].startswith("baltor-feed-reader")

    def not_modified(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 304, "Not Modified", Message(), None)

    assert r.fetch("https://feeds.example.org/a.xml", etag='"v1"', opener=not_modified)["body"] is None

    def limited(req, timeout):
        h = Message()
        h["Retry-After"] = "120"
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", h, None)

    res = r.fetch("https://feeds.example.org/a.xml", opener=limited)
    assert res["status"] == 429 and res["retry_after"] == 120.0


def test_fetch_refuses_non_http_and_oversized_bodies():
    with pytest.raises(ValueError):
        r.fetch("file:///etc/passwd")
    with pytest.raises(r.FeedError):
        r.fetch("https://x.example/f", max_bytes=3, opener=lambda req, timeout: FakeResponse(b"123456"))


def test_cli_on_files_prints_json(capsys):
    code = r.main([str(FIX / "rss2.xml"), str(FIX / "feed.json"), "--since", "2026-09-15", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["errors"] == []
    assert {i["title"] for i in out["items"]} == {"Godot 4.7 & the new tile editor", "Relative link post",
                                                   "Kokoro voices compared"}
