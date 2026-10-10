import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import source_digest_builder as d

FIX = Path(__file__).resolve().parent / "fixtures"
NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def data():
    return json.loads((FIX / "items.json").read_text())


@pytest.fixture()
def watchlist():
    return json.loads((FIX / "watchlist.json").read_text())


def test_parse_window():
    assert d.parse_window("7d") == timedelta(days=7)
    assert d.parse_window("36h") == timedelta(hours=36)
    assert d.parse_window(2) == timedelta(days=2)
    with pytest.raises(ValueError):
        d.parse_window("a week")


def test_score_uses_keywords_weights_exclusions_and_recency(data, watchlist):
    by_id = {i["id"]: i for i in data["items"]}
    release, score_r = by_id["id1"], d.score_item(by_id["id1"], watchlist, NOW)
    assert score_r[1] == ["godot"] and score_r[0] > 0
    # excluded phrase wins over the 'godot' feed it came from
    assert d.score_item(by_id["id6"], watchlist, NOW) == (0.0, [])
    # word boundaries: 'hooks' matches, but 'hook' inside another word would not
    assert "hooks" in d.score_item(by_id["id5"], watchlist, NOW)[1]
    newer = dict(release, published="2026-10-10T11:00:00Z")
    assert d.score_item(newer, watchlist, NOW)[0] > score_r[0]
    assert d.score_item(dict(release, title="nothing relevant", tags=[]), watchlist, NOW) == (0.0, [])


def test_digest_sections_window_caps_and_counts(data, watchlist):
    digest = d.build_digest(data["items"], watchlist, NOW, "7d", data["errors"])
    assert digest["spec"] == "baltor.source-digest/v1"
    assert digest["window"] == {"since": "2026-10-03T12:00:00Z", "until": "2026-10-10T12:00:00Z"}
    titles = [s["title"] for s in digest["sections"]]
    assert titles == ["Releases", "Agent workflows", "Community"]
    urls = [i["url"] for s in digest["sections"] for i in s["items"]]
    assert "https://github.com/godotengine/godot/releases/tag/4.6-stable" not in urls  # outside window
    assert "https://www.reddit.com/r/godot/comments/d4/" not in urls  # excluded term
    assert "https://example.org/undated" not in urls  # undated items cannot be placed in a window
    assert digest["counts"]["items_in"] == 10 and digest["counts"]["items_selected"] == len(urls)
    assert digest["errors"] == data["errors"]
    community = next(s for s in digest["sections"] if s["title"] == "Community")
    scores = [i["score"] for i in community["items"]]
    assert scores == sorted(scores, reverse=True)


def test_per_source_cap(data, watchlist):
    watchlist["max_items_per_source"] = 1
    digest = d.build_digest(data["items"], watchlist, NOW, "7d")
    feeds = [i["url"].split("/comments/")[0] for s in digest["sections"] for i in s["items"]]
    assert feeds.count("https://www.reddit.com/r/blender") == 1


def test_trends_need_multiple_sources_and_carry_citations(data):
    current = [i for i in data["items"] if (i["published"] or "") >= "2026-10-03"]
    previous = [i for i in data["items"] if "2026-09-26" <= (i["published"] or "") < "2026-10-03"]
    trends = d.trend_terms(current, previous)
    terms = {t["term"]: t for t in trends}
    assert "gaussian splatting" in terms
    gs = terms["gaussian splatting"]
    assert gs["sources"] >= 2 and gs["count"] == 3 and gs["previous_count"] == 0
    assert gs["citations"][0] == "https://news.example.com/item?id=1"
    # 'splatting' alone is dropped in favour of the bigram with the same count
    assert "splatting" not in terms
    # every reported trend is backed by at least two different feeds
    assert all(t["sources"] >= 2 for t in trends)


def test_markdown_has_a_link_on_every_item_line(data, watchlist):
    md = d.render_markdown(d.build_digest(data["items"], watchlist, NOW, "7d", data["errors"]))
    bullet_lines = [l for l in md.splitlines() if l.startswith("- ")]
    item_lines = [l for l in bullet_lines if not l.startswith("- https://example.org/broken")]
    assert item_lines and all("](https://" in l for l in item_lines)
    assert "## Rising terms" in md and "## Feeds that failed" in md
    assert md.startswith("# Source digest: godot-blender-weekly")


def test_cli_writes_markdown_and_json(tmp_path):
    out_md, out_json = tmp_path / "d.md", tmp_path / "d.json"
    code = d.main([str(FIX / "items.json"), "--watchlist", str(FIX / "watchlist.json"), "--now",
                   "2026-10-10T12:00:00Z", "--out", str(out_md), "--json", str(out_json)])
    assert code == 0
    digest = json.loads(out_json.read_text())
    assert digest["generated_at"] == "2026-10-10T12:00:00Z"
    assert out_md.read_text().count("](https://") >= digest["counts"]["items_selected"]
