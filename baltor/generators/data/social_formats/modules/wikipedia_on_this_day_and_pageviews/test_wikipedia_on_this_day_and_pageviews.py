import datetime as dt
import io
import json
from pathlib import Path

import pytest

import wikipedia_on_this_day_and_pageviews as m

FX = Path(__file__).parent / "fixtures"
TODAY = dt.date(2026, 10, 10)


def load(name):
    return json.loads((FX / name).read_text())


def test_onthisday_url_pads_and_validates():
    assert m.onthisday_url(1, 5) == "https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/01/05"
    assert m.onthisday_url(2, 29, "births", "de") == "https://de.wikipedia.org/api/rest_v1/feed/onthisday/births/02/29"
    with pytest.raises(ValueError):
        m.onthisday_url(2, 30)
    with pytest.raises(ValueError):
        m.onthisday_url(1, 1, "battles")
    with pytest.raises(ValueError):
        m.onthisday_url(1, 1, lang="en.evil.com/")


def test_featuredfeed_url():
    assert m.featuredfeed_onthisday_url() == \
        "https://en.wikipedia.org/w/api.php?action=featuredfeed&feed=onthisday&feedformat=atom"


def test_pageviews_urls():
    assert m.pageviews_top_url("2026-10-09") == \
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/10/09"
    assert m.pageviews_top_url(dt.date(2026, 9, 1), "en.wikipedia.org", "mobile-web", whole_month=True) == \
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/mobile-web/2026/09/all-days"
    url = m.pageviews_per_article_url("Are You the One?", "2026-10-01", "2026-10-09")
    assert url.endswith("/per-article/en.wikipedia/all-access/user/Are_You_the_One%3F/daily/20261001/20261009")
    with pytest.raises(ValueError):
        m.pageviews_per_article_url("X", "2026-10-09", "2026-10-01")
    with pytest.raises(ValueError):
        m.pageviews_top_url("2026-10-09", access="tablet")


def test_parse_onthisday_flattens_all_kinds():
    evs = m.parse_onthisday(load("onthisday_all_10_10.json"))
    kinds = {e.kind for e in evs}
    assert kinds == {"selected", "births", "deaths", "events", "holidays"}
    first = evs[0]
    assert first.year == 1926 and first.pages[0]["title"] == "Exampleton Bridge"
    assert first.pages[0]["url"] == "https://en.wikipedia.org/wiki/Exampleton_Bridge"
    assert first.pages[1]["url"] == "https://en.wikipedia.org/wiki/Exampleton"
    assert any(e.year is None for e in evs)


def test_rank_events_prefers_round_anniversaries_and_flags_sensitive():
    ranked = m.rank_events(m.parse_onthisday(load("onthisday_all_10_10.json")), TODAY)
    assert ranked[0]["year"] == 1926 and ranked[0]["years_ago"] == 100
    assert ranked[1]["year"] == 1976
    crash = [r for r in ranked if "ferry" in r["text"]][0]
    assert crash["sensitive"] is True
    assert all(r["status"] == "needs-sources" for r in ranked)
    safe = m.rank_events(m.parse_onthisday(load("onthisday_all_10_10.json")), TODAY, exclude_sensitive=True)
    assert not any("ferry" in r["text"] for r in safe)


def test_anniversary_weights():
    assert m.anniversary_weight(100) == 1.0
    assert m.anniversary_weight(75) == 0.8
    assert m.anniversary_weight(25) == 0.6
    assert m.anniversary_weight(30) == 0.4
    assert m.anniversary_weight(37) == 0.0
    assert m.anniversary_weight(None) == 0.0


def test_parse_top_drops_noise_and_rising():
    today = m.parse_top(load("pageviews_top_2026_10_09.json"))
    assert [a.article for a in today] == ["Example_Comet", "Fixture_Film_(2026)", "Sample_City", "Old_Favourite"]
    assert today[0].title == "Example Comet"
    base = m.parse_top(load("pageviews_top_2026_10_02.json"))
    rising = m.rising_articles(today, base, min_ratio=2.0, min_views=20000)
    names = [r["article"] for r in rising]
    assert "Example_Comet" in names and "Sample_City" in names and "Old_Favourite" not in names
    assert [r for r in rising if r["article"] == "Example_Comet"][0]["ratio"] is None


def test_parse_per_article_sorted():
    rows = m.parse_per_article(load("per_article.json"))
    assert rows == [("2026100800", 1200), ("2026100900", 250000)]


def test_fetch_json_uses_user_agent_and_refuses_other_hosts():
    seen = {}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def opener(req, timeout):
        seen["ua"] = req.get_header("User-agent")
        seen["url"] = req.full_url
        return Resp(json.dumps({"selected": []}).encode())

    out = m.fetch_json(m.onthisday_url(10, 10), "shorts-topic-bot/1.0 (ops@example.org)", opener=opener)
    assert out == {"selected": []} and seen["ua"].startswith("shorts-topic-bot/1.0")
    with pytest.raises(ValueError):
        m.fetch_json("https://example.com/x", "a/1", opener=opener)
    with pytest.raises(ValueError):
        m.fetch_json(m.onthisday_url(10, 10), "python", opener=opener)
