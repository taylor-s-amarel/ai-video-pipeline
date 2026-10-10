import gzip
from pathlib import Path

import agent_feeds_fetch as f

FIX = Path(__file__).resolve().parent / "fixtures"
FEED = "https://example.com/feed.xml"


class Clock:
    def __init__(self, t=1_791_633_600.0):  # 2026-10-10T12:00:00Z
        self.t = t
        self.slept = []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.slept.append(round(s, 3))
        self.t += s


def fetcher(responses, clock=None, **kw):
    clock = clock or Clock()
    t = f.ReplayTransport(responses)
    return f.PoliteFetcher(t, clock=clock, sleep=clock.sleep, env={}, **kw), t, clock


def ok(body=b"<rss/>", **headers):
    return f.Response(200, {"Content-Type": "application/rss+xml", **headers}, body)


def test_first_fetch_stores_validators_and_sends_user_agent():
    fx, t, _ = fetcher({FEED: ok(ETag='"abc"', **{"Last-Modified": "Fri, 09 Oct 2026 19:28:59 GMT"})})
    r = fx.fetch(FEED)
    assert r.outcome == "ok" and r.body == b"<rss/>" and r.content_type == "application/rss+xml"
    assert r.state["etag"] == '"abc"' and r.state["last_modified"].startswith("Fri, 09 Oct")
    assert r.state["last_success"] == "2026-10-10T12:00:00Z"
    sent = t.calls[0][2]
    assert sent["User-Agent"].startswith("BaltorAgentFeeds/") and "If-None-Match" not in sent


def test_conditional_request_and_304():
    fx, t, _ = fetcher({FEED: f.Response(304, {})})
    state = f.new_state("s", FEED, etag='"abc"', last_modified="Fri, 09 Oct 2026 19:28:59 GMT", failures=2)
    r = fx.fetch(FEED, state)
    assert r.outcome == "not-modified" and not r.changed
    assert t.calls[0][2]["If-None-Match"] == '"abc"'
    assert t.calls[0][2]["If-Modified-Since"] == "Fri, 09 Oct 2026 19:28:59 GMT"
    assert r.state["failures"] == 0 and r.state["backoff_until"] is None


def test_per_host_rate_limit_waits_between_requests():
    other = "https://example.com/other.xml"
    fx, t, clock = fetcher({FEED: ok(), other: ok()}, min_interval_s=5)
    fx.fetch(FEED)
    fx.fetch(other)
    assert clock.slept == [5.0]
    fx.fetch("https://another-host.org/feed")  # different host: no wait
    assert clock.slept == [5.0]


def test_nvd_gets_six_second_interval_and_api_key_from_env():
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0?lastModStartDate=x"
    clock = Clock()
    t = f.ReplayTransport({url: ok(b"{}")})
    fx = f.PoliteFetcher(t, clock=clock, sleep=clock.sleep, env={"NVD_API_KEY": "test-key-value"})
    fx.fetch(url)
    fx.fetch(url)
    assert clock.slept == [6.0]
    assert t.calls[0][2]["apiKey"] == "test-key-value"


def test_exponential_backoff_and_retry_after():
    fx, _, clock = fetcher({FEED: [f.Response(503, {}), f.Response(503, {}), f.Response(429, {"Retry-After": "86400"})]})
    r1 = fx.fetch(FEED)
    assert r1.outcome == "error" and r1.state["failures"] == 1
    assert r1.state["backoff_until"] == "2026-10-10T12:15:00Z"
    r_skip = fx.fetch(FEED, r1.state)
    assert r_skip.outcome == "backoff"
    clock.t += 3600
    r2 = fx.fetch(FEED, r1.state)
    assert r2.state["failures"] == 2 and r2.state["backoff_until"] == "2026-10-10T13:30:00Z"
    clock.t += 3600
    r3 = fx.fetch(FEED, r2.state)
    assert r3.state["failures"] == 3 and r3.state["backoff_until"] == "2026-10-11T14:00:00Z"  # Retry-After wins


def test_gone_marks_source_and_stops_polling():
    fx, t, _ = fetcher({FEED: f.Response(410, {})})
    r = fx.fetch(FEED)
    assert r.outcome == "gone" and r.state["gone"] is True
    again = fx.fetch(FEED, r.state)
    assert again.outcome == "gone" and len(t.calls) == 1


def test_robots_txt_blocks_disallowed_page_and_sets_crawl_delay():
    robots = b"User-agent: *\nDisallow: /private/\nCrawl-delay: 10\n"
    page = "https://docs.example.dev/private/changelog"
    open_page = "https://docs.example.dev/changelog"
    fx, t, clock = fetcher({"https://docs.example.dev/robots.txt": ok(robots), open_page: ok(b"<html></html>")})
    blocked = fx.fetch(page, check_robots=True)
    assert blocked.outcome == "robots-blocked" and blocked.state["robots_blocked"]
    allowed = fx.fetch(open_page, check_robots=True)
    assert allowed.outcome == "ok"
    assert clock.slept == [10.0]  # crawl-delay applied between robots.txt and the page
    assert [c[1] for c in t.calls].count("https://docs.example.dev/robots.txt") == 1  # cached


def test_robots_4xx_allows_and_5xx_disallows():
    fx, _, _ = fetcher({"https://a.example/robots.txt": f.Response(404, {}), "https://a.example/x": ok(),
                        "https://b.example/robots.txt": f.Response(503, {}), "https://b.example/x": ok()})
    assert fx.fetch("https://a.example/x", check_robots=True).outcome == "ok"
    assert fx.fetch("https://b.example/x", check_robots=True).outcome == "robots-blocked"


def test_size_limits_raw_and_gzip_bomb():
    big = b"x" * 2000
    fx, _, _ = fetcher({FEED: ok(big)}, max_bytes=1000)
    r = fx.fetch(FEED)
    assert r.outcome == "too-large" and r.state["failures"] == 1
    bomb = gzip.compress(b"a" * 50_000)
    fx2, _, _ = fetcher({FEED: ok(bomb, **{"Content-Encoding": "gzip"})}, max_bytes=10_000)
    assert fx2.fetch(FEED).outcome == "too-large"


def test_gzip_body_is_decoded():
    fx, _, _ = fetcher({FEED: ok(gzip.compress(b"<rss>hi</rss>"), **{"Content-Encoding": "gzip"})})
    assert fx.fetch(FEED).body == b"<rss>hi</rss>"


def test_non_http_scheme_refused():
    fx, t, _ = fetcher({})
    assert fx.fetch("file:///etc/passwd").outcome == "invalid-url"
    assert t.calls == []


def test_network_error_is_a_failure():
    fx, _, _ = fetcher({FEED: f.Response(0, {}, b"", error="URLError: timed out")})
    r = fx.fetch(FEED)
    assert r.outcome == "error" and "timed out" in r.state["last_error"]


def test_is_due():
    now = 1_791_633_600.0
    assert f.is_due(None, 6, now)[0]
    st = f.new_state("s", FEED, last_success="2026-10-10T08:00:00Z")
    assert not f.is_due(st, 6, now)[0]
    assert f.is_due(st, 4, now)[0]
    st["backoff_until"] = "2026-10-10T13:00:00Z"
    assert f.is_due(st, 1, now) == (False, "backing off until 2026-10-10T13:00:00Z")
    assert not f.is_due(dict(st, gone=True, backoff_until=None), 1, now)[0]


def test_fixture_feed_roundtrip():
    body = (FIX / "sample_feed.xml").read_bytes()
    fx, _, _ = fetcher({FEED: ok(body)})
    assert fx.fetch(FEED).body == body
