"""Build and recognise feed URLs for the platforms agents most often monitor.

Standard library only; no network. Each builder validates its input so an agent cannot produce a
malformed or guessed URL silently, and ``identify`` maps a URL back to (platform, parameters).
Patterns were checked on 2026-10-10 against each platform's documentation or live feeds:

- Reddit:     https://www.reddit.com/r/<name>/.rss  (also /new/.rss, /top/.rss?t=day)
- GitHub:     https://github.com/<owner>/<repo>/releases.atom | tags.atom | commits/<branch>.atom
- YouTube:    https://www.youtube.com/feeds/videos.xml?channel_id=UC... (24-character channel id)
- arXiv:      https://rss.arxiv.org/rss/<cat>[+<cat>...]   (or /atom/)
- Discourse:  https://<forum>/latest.rss | top.rss | hot.rss | c/<slug>/<id>.rss
- Mastodon:   https://<instance>/@<user>.rss   (public posts only)
- Bluesky:    https://bsky.app/profile/<handle>/rss
- hnrss:      https://hnrss.org/newest?q=a+OR+b (third-party Hacker News feeds)
- Substack:   https://<publication>/feed  (unless the publication disabled RSS)
- itch.io:    https://<user>.itch.io/<game>/devlog.rss
- Wikipedia:  https://<lang>.wikipedia.org/w/api.php?action=featuredfeed&feed=<onthisday|featured|potd>&feedformat=atom
"""

from __future__ import annotations

import re
import urllib.parse

__all__ = [
    "reddit", "github", "youtube_channel", "arxiv", "discourse", "mastodon", "bluesky", "hnrss",
    "substack", "itch_devlog", "wikipedia_featured", "identify",
]

_SUBREDDIT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_]{1,20}$")
_GH_PART = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,99})$")
_BRANCH = re.compile(r"^[A-Za-z0-9._/-]{1,200}$")
_CHANNEL = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
_ARXIV_CAT = re.compile(r"^[a-z-]+(\.[A-Za-z-]+)?$")
_HOST = re.compile(r"^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")
_HANDLE = re.compile(r"^[A-Za-z0-9_]{1,30}$")
_BSKY = re.compile(r"^(?=.{3,253}$)([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$")
_LANG = re.compile(r"^[a-z]{2,3}(-[a-z]+)?$")


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def reddit(name: str, sort: str | None = None, period: str | None = None) -> str:
    """Subreddit feed. sort: None|'new'|'top'|'hot'|'rising'; period (top only): hour|day|week|month|year|all."""
    name = name.removeprefix("r/").removeprefix("/r/").strip("/")
    _need(bool(_SUBREDDIT.match(name)), f"invalid subreddit name {name!r}")
    _need(sort in (None, "new", "top", "hot", "rising"), f"invalid sort {sort!r}")
    _need(period is None or (sort == "top" and period in {"hour", "day", "week", "month", "year", "all"}),
          "period is only valid with sort='top' and must be hour/day/week/month/year/all")
    url = f"https://www.reddit.com/r/{name}/" + (f"{sort}/" if sort else "") + ".rss"
    return url + (f"?t={period}" if period else "")


def github(repo: str, kind: str = "releases", branch: str = "main") -> str:
    """GitHub Atom feed for owner/repo. kind: releases|tags|commits."""
    parts = repo.strip("/").split("/")
    _need(len(parts) == 2 and all(_GH_PART.match(p) for p in parts), f"invalid repository {repo!r}")
    _need(kind in {"releases", "tags", "commits"}, f"invalid kind {kind!r}")
    base = f"https://github.com/{parts[0]}/{parts[1]}"
    if kind == "commits":
        _need(bool(_BRANCH.match(branch)) and ".." not in branch, f"invalid branch {branch!r}")
        return f"{base}/commits/{branch}.atom"
    return f"{base}/{kind}.atom"


def youtube_channel(channel_id: str) -> str:
    """YouTube channel uploads feed. Needs the UC... channel id, not a @handle."""
    _need(bool(_CHANNEL.match(channel_id)), "channel id must be 'UC' followed by 22 characters (resolve @handles first)")
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def arxiv(*categories: str, fmt: str = "rss") -> str:
    """arXiv listing feed for one or more categories (joined with '+')."""
    _need(bool(categories), "give at least one category")
    _need(fmt in {"rss", "atom"}, "fmt must be rss or atom")
    for c in categories:
        _need(bool(_ARXIV_CAT.match(c)), f"invalid arXiv category {c!r}")
    return f"https://rss.arxiv.org/{fmt}/" + "+".join(categories)


def discourse(host: str, view: str = "latest", category: tuple[str, int] | None = None) -> str:
    """Discourse forum feed. view: latest|top|hot; or category=(slug, id)."""
    host = host.lower().removeprefix("https://").strip("/")
    _need(bool(_HOST.match(host)), f"invalid host {host!r}")
    if category:
        slug, cid = category
        _need(bool(_SLUG.match(slug)) and int(cid) > 0, "category must be (slug, positive id)")
        return f"https://{host}/c/{slug}/{int(cid)}.rss"
    _need(view in {"latest", "top", "hot"}, f"invalid view {view!r}")
    return f"https://{host}/{view}.rss"


def mastodon(instance: str, user: str) -> str:
    """Public posts of a Mastodon account on its home instance."""
    instance = instance.lower().removeprefix("https://").strip("/")
    user = user.lstrip("@").split("@")[0]
    _need(bool(_HOST.match(instance)), f"invalid instance {instance!r}")
    _need(bool(_HANDLE.match(user)), f"invalid user {user!r}")
    return f"https://{instance}/@{user}.rss"


def bluesky(handle: str) -> str:
    handle = handle.lstrip("@")
    _need(bool(_BSKY.match(handle)), f"invalid Bluesky handle {handle!r}")
    return f"https://bsky.app/profile/{handle}/rss"


def hnrss(*keywords: str, endpoint: str = "newest", points: int | None = None) -> str:
    """Third-party hnrss.org feed: newest|frontpage|show|ask, optional OR-joined keyword query and points floor."""
    _need(endpoint in {"newest", "frontpage", "show", "ask", "best"}, f"invalid endpoint {endpoint!r}")
    params = []
    if keywords:
        _need(all(k.strip() for k in keywords), "empty keyword")
        params.append(("q", " OR ".join(k.strip() for k in keywords)))
    if points is not None:
        _need(points >= 0, "points must be >= 0")
        params.append(("points", str(points)))
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote_plus)
    return f"https://hnrss.org/{endpoint}" + (f"?{query}" if query else "")


def substack(publication: str) -> str:
    """Feed of a Substack publication (subdomain or custom domain). Confirm it is enabled before polling."""
    host = publication.lower().removeprefix("https://").removeprefix("http://").split("/")[0]
    if "." not in host:
        host = f"{host}.substack.com"
    _need(bool(_HOST.match(host)), f"invalid publication {publication!r}")
    return f"https://{host}/feed"


def itch_devlog(user: str, game: str) -> str:
    _need(bool(_SLUG.match(user.lower())) and bool(_SLUG.match(game.lower())), "invalid itch.io user or game slug")
    return f"https://{user.lower()}.itch.io/{game.lower()}/devlog.rss"


def wikipedia_featured(feed: str = "onthisday", lang: str = "en", fmt: str = "atom") -> str:
    _need(feed in {"onthisday", "featured", "potd"}, f"invalid featured feed {feed!r}")
    _need(bool(_LANG.match(lang)), f"invalid language {lang!r}")
    _need(fmt in {"atom", "rss"}, "fmt must be atom or rss")
    return f"https://{lang}.wikipedia.org/w/api.php?action=featuredfeed&feed={feed}&feedformat={fmt}"


def identify(url: str) -> tuple[str, dict]:
    """Return (platform, params) for a known feed URL, or ('unknown', {})."""
    u = urllib.parse.urlsplit(url)
    host, path, qs = (u.hostname or "").lower(), u.path, urllib.parse.parse_qs(u.query)
    m = re.match(r"^/r/([^/]+)/(?:(new|top|hot|rising)/)?\.rss$", path)
    if host.endswith("reddit.com") and m:
        return "reddit", {"name": m[1], "sort": m[2], "period": qs.get("t", [None])[0]}
    if host == "github.com":
        m = re.match(r"^/([^/]+)/([^/]+)/(releases|tags)\.atom$", path)
        if m:
            return "github", {"repo": f"{m[1]}/{m[2]}", "kind": m[3]}
        m = re.match(r"^/([^/]+)/([^/]+)/commits/(.+)\.atom$", path)
        if m:
            return "github", {"repo": f"{m[1]}/{m[2]}", "kind": "commits", "branch": m[3]}
    if host.endswith("youtube.com") and path == "/feeds/videos.xml" and "channel_id" in qs:
        return "youtube", {"channel_id": qs["channel_id"][0]}
    if host == "rss.arxiv.org":
        m = re.match(r"^/(rss|atom)/(.+)$", path)
        if m:
            return "arxiv", {"fmt": m[1], "categories": m[2].split("+")}
    if host == "hnrss.org":
        return "hnrss", {"endpoint": path.strip("/"), "q": qs.get("q", [None])[0]}
    if host == "bsky.app":
        m = re.match(r"^/profile/([^/]+)/rss$", path)
        if m:
            return "bluesky", {"handle": m[1]}
    m = re.match(r"^/@([A-Za-z0-9_]+)\.rss$", path)
    if m:
        return "mastodon", {"instance": host, "user": m[1]}
    m = re.match(r"^/(latest|top|hot)\.rss$", path) or re.match(r"^/c/([a-z0-9-]+)/(\d+)\.rss$", path)
    if m:
        return "discourse", {"host": host, "path": path}
    if host.endswith(".itch.io") and path.endswith("/devlog.rss"):
        return "itch", {"user": host.split(".")[0], "game": path.strip("/").split("/")[0]}
    if host.endswith("wikipedia.org") and qs.get("action") == ["featuredfeed"]:
        return "wikipedia", {"lang": host.split(".")[0], "feed": qs.get("feed", [None])[0]}
    if path.rstrip("/") == "/feed" and (host.endswith("substack.com")):
        return "substack", {"host": host}
    return "unknown", {}
