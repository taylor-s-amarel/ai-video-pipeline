"""URL builders and response parsers for Wikipedia "On this day" and Wikimedia pageviews (top articles).

Endpoints (shapes checked on 2026-10-10 against the Wikimedia service specs on GitHub:
``wikimedia/mediawiki-services-wikifeeds`` spec.yaml and ``wikimedia/analytics-aqs`` v1/pageviews.yaml,
and the ``mediawiki-utilities/python-mwviews`` client):

* On this day:   https://{lang}.wikipedia.org/api/rest_v1/feed/onthisday/{type}/{MM}/{DD}
                 type in selected | births | deaths | holidays | events | all  (MM and DD zero-padded)
* Featured feed: https://{lang}.wikipedia.org/w/api.php?action=featuredfeed&feed=onthisday&feedformat=atom
* Top articles:  https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{project}/{access}/{YYYY}/{MM}/{DD}
                 (DD may be ``all-days`` for a whole month; up to 1000 articles)
* Per article:   https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{access}/{agent}/
                 {article}/{granularity}/{start YYYYMMDD}/{end YYYYMMDD}

Network use is limited to :func:`fetch_json`, which requires a descriptive User-Agent (Wikimedia's API rules
ask for one and for no more than 200 requests/s) and takes an injectable ``opener`` so tests stay offline.
Content from these endpoints is Wikipedia text (CC BY-SA, see each page); keep titles, links and short
facts, credit Wikipedia, and verify every claim against the cited sources before it goes in a video.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Callable, Iterable

ONTHISDAY_TYPES = ("selected", "births", "deaths", "holidays", "events", "all")
ACCESS = ("all-access", "desktop", "mobile-app", "mobile-web")
AGENTS = ("all-agents", "user", "automated", "spider")
GRANULARITY = ("daily", "monthly")
_LANG = re.compile(r"^[a-z]{2,3}(-[a-z0-9]{2,8})*$")
_PROJECT = re.compile(r"^[a-z0-9-]+\.[a-z]+$")

# Pages that dominate "top" lists but are never topics.
NOISE_PREFIXES = ("Special:", "Wikipedia:", "File:", "Portal:", "Help:", "Category:", "Template:", "Talk:",
                  "User:", "Draft:", "Module:", "MediaWiki:")
NOISE_TITLES = frozenset({"Main_Page", "Main Page", "-", "Undefined"})
# Words that mark an event as sensitive (needs a careful, respectful treatment or a different topic).
SENSITIVE = re.compile(r"\b(killed|killing|massacre|murder|bomb|bombing|shooting|terror|attack|genocide|"
                       r"suicide|execution|executed|assassinat\w*|war crime|disaster|crash|died|deaths?)\b", re.I)


@dataclass
class OnThisDayEvent:
    kind: str
    year: int | None
    text: str
    pages: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TopArticle:
    rank: int
    article: str
    views: int

    @property
    def title(self) -> str:
        return self.article.replace("_", " ")


# ----------------------------------------------------------------------------- URL builders

def _check_lang(lang: str) -> str:
    if not _LANG.match(lang):
        raise ValueError(f"bad language code {lang!r}")
    return lang


def _check_month_day(month: int, day: int) -> None:
    try:
        dt.date(2024, int(month), int(day))  # leap year so 02/29 is accepted
    except ValueError as exc:
        raise ValueError(f"bad month/day {month}/{day}") from exc


def onthisday_url(month: int, day: int, type: str = "selected", lang: str = "en") -> str:
    if type not in ONTHISDAY_TYPES:
        raise ValueError(f"type must be one of {ONTHISDAY_TYPES}")
    _check_month_day(month, day)
    return f"https://{_check_lang(lang)}.wikipedia.org/api/rest_v1/feed/onthisday/{type}/{int(month):02d}/{int(day):02d}"


def featuredfeed_onthisday_url(lang: str = "en", feedformat: str = "atom") -> str:
    if feedformat not in ("atom", "rss"):
        raise ValueError("feedformat must be atom or rss")
    q = urllib.parse.urlencode({"action": "featuredfeed", "feed": "onthisday", "feedformat": feedformat})
    return f"https://{_check_lang(lang)}.wikipedia.org/w/api.php?{q}"


def _check_project(project: str) -> str:
    project = project.removesuffix(".org")
    if not _PROJECT.match(project):
        raise ValueError(f"bad project {project!r}; use e.g. en.wikipedia")
    return project


def pageviews_top_url(date: dt.date | str, project: str = "en.wikipedia", access: str = "all-access",
                      whole_month: bool = False) -> str:
    if access not in ACCESS:
        raise ValueError(f"access must be one of {ACCESS}")
    d = dt.date.fromisoformat(date) if isinstance(date, str) else date
    day = "all-days" if whole_month else f"{d.day:02d}"
    return (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{_check_project(project)}/{access}/"
            f"{d.year:04d}/{d.month:02d}/{day}")


def pageviews_per_article_url(article: str, start: dt.date | str, end: dt.date | str,
                              project: str = "en.wikipedia", access: str = "all-access",
                              agent: str = "user", granularity: str = "daily") -> str:
    if access not in ACCESS or agent not in AGENTS or granularity not in GRANULARITY:
        raise ValueError("bad access, agent or granularity")
    s = dt.date.fromisoformat(start) if isinstance(start, str) else start
    e = dt.date.fromisoformat(end) if isinstance(end, str) else end
    if e < s:
        raise ValueError("end before start")
    title = urllib.parse.quote(article.strip().replace(" ", "_"), safe="")
    return (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{_check_project(project)}/"
            f"{access}/{agent}/{title}/{granularity}/{s:%Y%m%d}/{e:%Y%m%d}")


def article_url(title: str, lang: str = "en") -> str:
    return f"https://{_check_lang(lang)}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'), safe='()_,')}"


# ----------------------------------------------------------------------------- parsers

def _page_summary(p: dict, lang: str) -> dict:
    titles = p.get("titles") or {}
    title = titles.get("normalized") or p.get("normalizedtitle") or p.get("title", "").replace("_", " ")
    url = ((p.get("content_urls") or {}).get("desktop") or {}).get("page") or (article_url(title, lang) if title else "")
    return {"title": title, "description": p.get("description", ""), "extract": p.get("extract", ""),
            "url": url, "wikibase_item": p.get("wikibase_item")}


def parse_onthisday(payload: dict, lang: str = "en") -> list[OnThisDayEvent]:
    """Flatten an onthisday response (any type) into events, keeping the related article summaries."""
    out: list[OnThisDayEvent] = []
    for kind in ONTHISDAY_TYPES[:-1]:
        for item in payload.get(kind, []) or []:
            year = item.get("year")
            try:
                year = int(year) if year is not None else None
            except (TypeError, ValueError):
                year = None
            out.append(OnThisDayEvent(kind=kind, year=year, text=str(item.get("text", "")).strip(),
                                      pages=[_page_summary(p, lang) for p in item.get("pages", []) or []]))
    return out


def is_noise(article: str) -> bool:
    return article in NOISE_TITLES or article.startswith(NOISE_PREFIXES)


def parse_top(payload: dict, drop_noise: bool = True) -> list[TopArticle]:
    items = payload.get("items") or []
    if not items:
        return []
    arts = [TopArticle(int(a.get("rank", 0)), str(a.get("article", "")), int(a.get("views", 0)))
            for a in items[0].get("articles", [])]
    if drop_noise:
        arts = [a for a in arts if not is_noise(a.article)]
    return sorted(arts, key=lambda a: (a.rank, a.article))


def parse_per_article(payload: dict) -> list[tuple[str, int]]:
    """[(YYYYMMDDHH timestamp, views), ...] in time order."""
    rows = [(str(i.get("timestamp", "")), int(i.get("views", 0))) for i in payload.get("items", [])]
    return sorted(rows)


# ----------------------------------------------------------------------------- topic helpers

def years_since(year: int | None, on: dt.date) -> int | None:
    return None if year is None else on.year - year


def anniversary_weight(years: int | None) -> float:
    """1.0 for centuries, 0.8 for 50/75 years, 0.6 for 25, 0.4 for decades, else 0."""
    if not years or years <= 0:
        return 0.0
    if years % 100 == 0:
        return 1.0
    if years % 50 == 0 or years % 75 == 0:
        return 0.8
    if years % 25 == 0:
        return 0.6
    if years % 10 == 0:
        return 0.4
    return 0.0


def rank_events(events: Iterable[OnThisDayEvent], on: dt.date, kinds: Iterable[str] = ("selected", "events"),
                exclude_sensitive: bool = False) -> list[dict]:
    """Order candidate events for a today-in-history short: round anniversaries first, then events with
    more linked articles (more material to verify against). Sensitive events are flagged, or dropped."""
    kinds = set(kinds)
    out = []
    for ev in events:
        if ev.kind not in kinds or not ev.text:
            continue
        sensitive = bool(SENSITIVE.search(ev.text))
        if sensitive and exclude_sensitive:
            continue
        ys = years_since(ev.year, on)
        score = anniversary_weight(ys) + min(len(ev.pages), 5) * 0.05
        out.append({"year": ev.year, "years_ago": ys, "text": ev.text, "kind": ev.kind,
                    "score": round(score, 3), "sensitive": sensitive,
                    "pages": [p["url"] for p in ev.pages if p.get("url")],
                    "status": "needs-sources"})
    out.sort(key=lambda r: (-r["score"], -(r["year"] or 0), r["text"]))
    return out


def rising_articles(today: list[TopArticle], baseline: list[TopArticle], min_ratio: float = 2.0,
                    min_views: int = 10000) -> list[dict]:
    """Articles whose views today are at least ``min_ratio`` times a baseline day's (new entries count as rising)."""
    base = {a.article: a.views for a in baseline}
    out = []
    for a in today:
        if a.views < min_views:
            continue
        before = base.get(a.article)
        ratio = (a.views / before) if before else float("inf")
        if ratio >= min_ratio:
            out.append({"article": a.article, "title": a.title, "views": a.views, "baseline_views": before,
                        "ratio": None if ratio == float("inf") else round(ratio, 2)})
    return out


# ----------------------------------------------------------------------------- network

def fetch_json(url: str, user_agent: str, opener: Callable | None = None, timeout: float = 20.0) -> dict:
    """GET ``url`` with a descriptive User-Agent (e.g. 'my-shorts-bot/1.0 (contact@example.org)')."""
    if not user_agent or "/" not in user_agent:
        raise ValueError("Wikimedia asks for a descriptive User-Agent such as 'tool/1.0 (contact)'")
    host = urllib.parse.urlsplit(url).hostname or ""
    if not (host == "wikimedia.org" or host.endswith(".wikipedia.org")):
        raise ValueError(f"refusing to fetch from {host}")
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    open_ = opener or urllib.request.urlopen
    with open_(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":  # pragma: no cover - manual use
    import argparse

    ap = argparse.ArgumentParser(description="Print today-in-history candidates or top articles.")
    ap.add_argument("what", choices=["onthisday", "top"])
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--lang", default="en")
    ap.add_argument("--user-agent", required=True)
    a = ap.parse_args()
    d = dt.date.fromisoformat(a.date)
    if a.what == "onthisday":
        evs = parse_onthisday(fetch_json(onthisday_url(d.month, d.day, "all", a.lang), a.user_agent), a.lang)
        print(json.dumps(rank_events(evs, d)[:20], indent=2, ensure_ascii=False))
    else:
        tops = parse_top(fetch_json(pageviews_top_url(d - dt.timedelta(days=1), f"{a.lang}.wikipedia"), a.user_agent))
        for t in tops[:30]:
            print(t.rank, t.views, t.title)
