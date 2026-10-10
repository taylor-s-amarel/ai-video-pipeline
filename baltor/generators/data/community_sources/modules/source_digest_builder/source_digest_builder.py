"""Rank normalised feed items against a watchlist and write a cited digest plus a trend scan.

Standard library only; no network. Input items come from ``rss_atom_jsonfeed_reader``
(``{"items": [...]}``); the watchlist follows the ``source_watchlist`` contract schema; the output
follows the ``source_digest_report`` contract schema and renders to Markdown in which every line
carries its source link.

    python source_digest_builder.py items.json --watchlist watchlist.json --window 7d \
        --out digest.md --json digest.json

Scoring = sum of matched keyword weights x source weight x recency factor (half-life in days).
Trends compare term frequency in the current window with the previous window of equal length and
only report a term when at least ``min_sources`` different feeds mention it, each one cited.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

__all__ = ["parse_window", "score_item", "select_items", "trend_terms", "build_digest", "render_markdown"]

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because been before being below between
both but by can could did do does doing down during each few for from further had has have having he her here
hers him his how i if in into is it its itself just me more most my no nor not now of off on once only or other
our ours out over own same she should so some such than that the their theirs them then there these they this
those through to too under until up very was we were what when where which while who whom why will with would
you your yours new how-to via vs using use used get got make made one two first last week today year years day
days show ask hn reddit release releases released version update updates v update notes rc beta alpha nightly
""".split())
TOKEN = re.compile(r"[a-z0-9][a-z0-9+.#-]*[a-z0-9+#]|[a-z0-9]")


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_window(value: str | int | float) -> timedelta:
    """'7d', '36h', or a number of days."""
    if isinstance(value, (int, float)):
        return timedelta(days=float(value))
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([dh])\s*", str(value))
    if not m:
        raise ValueError(f"window must look like 7d or 36h, got {value!r}")
    n = float(m[1])
    return timedelta(days=n) if m[2] == "d" else timedelta(hours=n)


def _text_of(item: dict) -> str:
    return " ".join([item.get("title", ""), item.get("summary", ""), " ".join(item.get("tags", []))]).lower()


def _term_regex(term: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])")


def _source_weight(item: dict, watchlist: dict) -> float:
    feed = item.get("source", {}).get("feed_url", "")
    weight = 1.0
    for src in watchlist.get("sources", []):
        if src.get("url") and src["url"] == feed:
            weight = float(src.get("weight", 1.0))
    return weight


def score_item(item: dict, watchlist: dict, now: datetime) -> tuple[float, list[str]]:
    """Return (score, matched terms). Score 0 means: no keyword matched or an excluded term matched."""
    text = _text_of(item)
    for term in watchlist.get("exclude_terms", []):
        if _term_regex(term).search(text):
            return 0.0, []
    matched, total = [], 0.0
    for kw in watchlist.get("keywords", []):
        term, weight = (kw, 1.0) if isinstance(kw, str) else (kw["term"], float(kw.get("weight", 1.0)))
        if _term_regex(term).search(text):
            matched.append(term)
            total += weight
    if not matched and watchlist.get("keywords"):
        return 0.0, []
    if not watchlist.get("keywords"):
        total = 1.0
    half_life = float(watchlist.get("recency_half_life_days", 3.0))
    published = _dt(item.get("published")) or _dt(item.get("updated"))
    age_days = max(0.0, (now - published).total_seconds() / 86400) if published else half_life * 2
    recency = 0.5 ** (age_days / half_life) if half_life > 0 else 1.0
    return round(total * _source_weight(item, watchlist) * recency, 4), matched


def _in_window(item: dict, since: datetime, until: datetime) -> bool:
    published = _dt(item.get("published")) or _dt(item.get("updated"))
    return published is not None and since <= published <= until


def _group_for(item: dict, groups: list[dict]) -> str:
    text = _text_of(item)
    feed = item.get("source", {}).get("feed_url", "")
    for g in groups:
        match = g.get("match", {})
        if any(t.lower() in [x.lower() for x in item.get("tags", [])] for t in match.get("tags_any", [])):
            return g["title"]
        if any(s in feed for s in match.get("feed_url_contains", [])):
            return g["title"]
        if any(_term_regex(t).search(text) for t in match.get("terms_any", [])):
            return g["title"]
    return item.get("source", {}).get("feed_title") or "Other sources"


def select_items(items: Iterable[dict], watchlist: dict, now: datetime, window: timedelta) -> list[dict]:
    since = now - window
    per_source_cap = int(watchlist.get("max_items_per_source", 5))
    scored = []
    for item in items:
        if not item.get("url") or not _in_window(item, since, now):
            continue
        score, matched = score_item(item, watchlist, now)
        if score > 0:
            scored.append(dict(item, score=score, matched=matched))
    scored.sort(key=lambda i: (-i["score"], i.get("published") or ""))
    counts: dict[str, int] = defaultdict(int)
    kept = []
    for item in scored:
        feed = item.get("source", {}).get("feed_url", "")
        if counts[feed] >= per_source_cap:
            continue
        counts[feed] += 1
        kept.append(item)
    return kept[: int(watchlist.get("max_items", 40))]


def _terms(title: str) -> set[str]:
    words = [w for w in TOKEN.findall(title.lower()) if w not in STOPWORDS and not w.isdigit() and len(w) > 2]
    grams = set(words)
    grams.update(f"{a} {b}" for a, b in zip(words, words[1:]))
    return grams


def trend_terms(current: list[dict], previous: list[dict], min_sources: int = 2, top: int = 10,
                min_count: int = 2) -> list[dict]:
    """Terms (unigrams/bigrams from titles) rising from the previous window to the current one.

    A term qualifies when it appears in at least ``min_count`` items from at least ``min_sources``
    (never fewer than two) different feeds in the current window, with at least two distinct URLs.
    Each trend lists the item URLs that support it.
    """
    min_sources = max(2, int(min_sources))  # a trend from a single feed is an anecdote, not a trend
    cur_items: dict[str, list[dict]] = defaultdict(list)
    for item in current:
        for term in _terms(item.get("title", "")):
            cur_items[term].append(item)
    prev_count: dict[str, int] = defaultdict(int)
    for item in previous:
        for term in _terms(item.get("title", "")):
            prev_count[term] += 1
    trends = []
    for term, its in cur_items.items():
        sources = {i.get("source", {}).get("feed_url", "") for i in its}
        if len(its) < min_count or len(sources) < min_sources:
            continue
        p = prev_count.get(term, 0)
        ratio = (len(its) + 1) / (p + 1)
        if ratio <= 1.0:
            continue
        citations = []
        for i in sorted(its, key=lambda x: x.get("published") or "", reverse=True):
            if i.get("url") and i["url"] not in citations:
                citations.append(i["url"])
        if len(citations) < 2:
            continue
        trends.append({"term": term, "count": len(its), "previous_count": p, "change": round(ratio, 2),
                       "sources": len(sources), "citations": citations[:5]})
    # Prefer bigrams over the unigrams they contain when the counts are equal.
    trends.sort(key=lambda t: (-t["change"], -t["count"], -len(t["term"].split()), t["term"]))
    out: list[dict] = []
    for t in trends:
        if any(t["term"] in o["term"].split() and o["count"] == t["count"] for o in out):
            continue
        out.append(t)
        if len(out) >= top:
            break
    return out


def build_digest(items: list[dict], watchlist: dict, now: datetime | None = None,
                 window: str | timedelta = "7d", errors: list[dict] | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    win = window if isinstance(window, timedelta) else parse_window(window)
    since, prev_since = now - win, now - 2 * win
    selected = select_items(items, watchlist, now, win)
    sections: dict[str, list[dict]] = defaultdict(list)
    for item in selected:
        sections[_group_for(item, watchlist.get("groups", []))].append({
            "title": item["title"], "url": item["url"],
            "source": item.get("source", {}).get("feed_title") or item.get("source", {}).get("feed_url", ""),
            "published": item.get("published"), "score": item["score"], "matched": item["matched"],
            "also_in": item.get("also_in", []),
        })
    order = [g["title"] for g in watchlist.get("groups", [])]
    ordered = sorted(sections.items(), key=lambda kv: (order.index(kv[0]) if kv[0] in order else len(order), kv[0]))
    current = [i for i in items if _in_window(i, since, now)]
    previous = [i for i in items if _in_window(i, prev_since, since)]
    return {
        "spec": "baltor.source-digest/v1",
        "watchlist_id": watchlist.get("id", "adhoc"),
        "generated_at": _iso(now),
        "window": {"since": _iso(since), "until": _iso(now)},
        "counts": {"items_in": len(items), "items_in_window": len(current), "items_selected": len(selected),
                   "sources": len({i.get("source", {}).get("feed_url") for i in items})},
        "sections": [{"title": title, "items": its} for title, its in ordered],
        "trends": trend_terms(current, previous, int(watchlist.get("trend_min_sources", 2))),
        "errors": errors or [],
    }


def render_markdown(digest: dict) -> str:
    lines = [f"# Source digest: {digest['watchlist_id']}", "",
             f"Window {digest['window']['since'][:10]} to {digest['window']['until'][:10]} · "
             f"{digest['counts']['items_selected']} of {digest['counts']['items_in_window']} items in window "
             f"from {digest['counts']['sources']} sources.", ""]
    for section in digest["sections"]:
        lines += [f"## {section['title']}", ""]
        for it in section["items"]:
            date = (it.get("published") or "")[:10]
            extra = f" (also in {len(it['also_in'])} other feed{'s' if len(it['also_in']) != 1 else ''})" \
                if it.get("also_in") else ""
            lines.append(f"- [{it['title']}]({it['url']}) — {it['source']}, {date}{extra}")
        lines.append("")
    if digest["trends"]:
        lines += ["## Rising terms", ""]
        for t in digest["trends"]:
            refs = " ".join(f"[{n}]({u})" for n, u in enumerate(t["citations"], 1))
            lines.append(f"- **{t['term']}**: {t['count']} items from {t['sources']} feeds "
                         f"(previous window {t['previous_count']}) {refs}")
        lines.append("")
    if digest.get("errors"):
        lines += ["## Feeds that failed", ""]
        lines += [f"- {e.get('feed_url')}: {e.get('error')}" for e in digest["errors"]]
        lines.append("")
    lines.append("Every line links to its source. Treat titles as leads: open the source before repeating a claim.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build a cited digest and trend scan from normalised feed items.")
    ap.add_argument("items", help="JSON from rss_atom_jsonfeed_reader --json ({'items': [...], 'errors': [...]})")
    ap.add_argument("--watchlist", required=True, help="watchlist JSON (source_watchlist schema)")
    ap.add_argument("--window", default="7d")
    ap.add_argument("--now", help="ISO timestamp to treat as now (for reproducible runs)")
    ap.add_argument("--out", help="write Markdown here (default stdout)")
    ap.add_argument("--json", dest="json_out", help="also write the digest JSON here")
    a = ap.parse_args(argv)
    data = json.loads(Path(a.items).read_text(encoding="utf-8"))
    watchlist = json.loads(Path(a.watchlist).read_text(encoding="utf-8"))
    now = _dt(a.now) if a.now else None
    digest = build_digest(data.get("items", []), watchlist, now, a.window, data.get("errors"))
    md = render_markdown(digest)
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(digest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
