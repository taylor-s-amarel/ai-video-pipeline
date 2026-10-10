"""Read RSS 2.0, RSS 1.0 (RDF), Atom and JSON Feed into one normalised item list.

Standard library only. The functions that parse, normalise, deduplicate and filter
never touch the network; ``fetch`` is a separate, polite HTTP helper (conditional
requests, per-host spacing, size cap, Retry-After) used only by the CLI.

Normalised item (see the ``normalized_feed_item`` contract schema)::

    {
      "id": "sha256 of the canonical url or guid",
      "guid": "the feed's own id/guid, if any",
      "title": "...",
      "url": "https://... (absolute, tracking parameters removed)",
      "published": "2026-10-09T19:28:59Z" | None,
      "updated":   "2026-10-09T19:28:59Z" | None,
      "authors": ["..."],
      "summary": "plain text, HTML removed, at most 600 characters",
      "tags": ["..."],
      "enclosures": [{"url": "...", "type": "audio/mpeg", "length": 123}],
      "source": {"feed_url": "...", "feed_title": "...", "format": "rss2|rss1|atom|jsonfeed"},
      "also_in": ["other feed urls that carried the same item"]
    }

CLI::

    python rss_atom_jsonfeed_reader.py feed1.xml https://example.org/feed --since 2026-10-01 --json
    python rss_atom_jsonfeed_reader.py --discover page.html --base https://example.org/
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

__all__ = [
    "FeedError", "parse_feed", "normalize_items", "canonical_url", "parse_date", "dedupe",
    "filter_since", "merge_feeds", "discover_feeds", "strip_html", "HostSpacer", "fetch",
]

ATOM = "http://www.w3.org/2005/Atom"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RSS1 = "http://purl.org/rss/1.0/"
DC = "http://purl.org/dc/elements/1.1/"
CONTENT = "http://purl.org/rss/1.0/modules/content/"
MEDIA = "http://search.yahoo.com/mrss/"

TRACKING_PARAMS = {
    "fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "ref_src", "ref_url", "igshid",
    "yclid", "_hsenc", "_hsmi", "mkt_tok", "si", "spm",
}
TRACKING_PREFIXES = ("utm_", "pk_", "hsa_")
SUMMARY_LIMIT = 600
DEFAULT_USER_AGENT = "baltor-feed-reader/1.0 (+https://github.com/taylor-s-amarel/ai-video-pipeline)"


class FeedError(ValueError):
    """Raised when bytes cannot be read as a supported feed."""


# --------------------------------------------------------------------------- helpers

def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def _q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


class _Stripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):  # noqa: D401
        if tag in {"script", "style"}:
            self._skip += 1
        elif tag in {"br", "p", "div", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def strip_html(value: str, limit: int | None = SUMMARY_LIMIT) -> str:
    """Return plain text from an HTML fragment, whitespace collapsed, optionally truncated on a word."""
    if not value:
        return ""
    stripper = _Stripper()
    try:
        stripper.feed(value)
        stripper.close()
        text = "".join(stripper.parts)
    except Exception:  # noqa: BLE001 - malformed HTML falls back to a crude strip
        text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    if limit and len(text) > limit:
        cut = text[: limit - 1].rsplit(" ", 1)[0]
        text = cut.rstrip(" ,.;:") + "…"
    return text


def canonical_url(url: str, base: str | None = None) -> str:
    """Absolute URL with lower-case scheme/host, no fragment, no default port, no tracking parameters,
    and query parameters sorted. Returns '' for empty input."""
    if not url:
        return ""
    url = url.strip()
    if base:
        url = urllib.parse.urljoin(base, url)
    parts = urllib.parse.urlsplit(url)
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = host
    if parts.username:
        netloc = f"{parts.username}@{netloc}"
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{netloc}:{port}"
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in TRACKING_PARAMS and not k.lower().startswith(TRACKING_PREFIXES)]
    query.sort()
    path = parts.path or ("/" if host else "")
    return urllib.parse.urlunsplit((scheme, netloc, path, urllib.parse.urlencode(query), ""))


def parse_date(value: str | None) -> datetime | None:
    """Parse RFC 822 (RSS), RFC 3339/ISO 8601 (Atom, JSON Feed) and a few common variants to aware UTC."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    iso = value.replace("Z", "+00:00").replace("z", "+00:00")
    iso = re.sub(r"(\.\d{6})\d+", r"\1", iso)  # trim sub-microsecond digits
    iso = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", iso)  # +0000 -> +00:00
    for candidate in (iso, iso.replace(" ", "T", 1)):
        try:
            dt = datetime.fromisoformat(candidate)
            return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
        except ValueError:
            continue
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", value)
    if m:
        return datetime(int(m[1]), int(m[2]), int(m[3]), tzinfo=timezone.utc)
    return None


def _iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _item_id(url: str, guid: str, title: str, feed_url: str) -> str:
    basis = url or (f"{feed_url}#{guid}" if guid else f"{feed_url}#{title}")
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- XML parsing

def _safe_xml(data: bytes) -> ET.Element:
    """Parse XML but refuse documents that declare entities or an internal DTD subset
    (billion-laughs and external-entity tricks have no place in a feed)."""
    head = data[:65536].lower()
    if b"<!entity" in head:
        raise FeedError("refusing XML with entity declarations")
    doctype = head.find(b"<!doctype")
    if doctype != -1 and b"[" in head[doctype:head.find(b">", doctype) + 1 or None]:
        raise FeedError("refusing XML with an internal DTD subset")
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise FeedError(f"not well-formed XML: {exc}") from exc


def _rss2(root: ET.Element, feed_url: str) -> tuple[str, list[dict]]:
    channel = root.find("channel")
    if channel is None:
        raise FeedError("RSS without <channel>")
    base = canonical_url(_text(channel.find("link")) or feed_url)
    feed_title = _text(channel.find("title"))
    items = []
    for it in channel.findall("item"):
        guid_el = it.find("guid")
        guid = _text(guid_el)
        link = _text(it.find("link"))
        if not link and guid_el is not None and guid.startswith("http") and \
                guid_el.get("isPermaLink", "true").lower() != "false":
            link = guid
        body = _text(it.find(_q(CONTENT, "encoded"))) or _text(it.find("description"))
        authors = [a for a in (_text(it.find("author")), _text(it.find(_q(DC, "creator")))) if a]
        enclosures = []
        for enc in it.findall("enclosure") + it.findall(_q(MEDIA, "content")):
            if enc.get("url"):
                length = enc.get("length") or enc.get("fileSize")
                enclosures.append({"url": canonical_url(enc.get("url"), base), "type": enc.get("type", ""),
                                   "length": int(length) if length and length.isdigit() else None})
        items.append({
            "guid": guid, "title": strip_html(_text(it.find("title")), None), "link": link,
            "published": _text(it.find("pubDate")) or _text(it.find(_q(DC, "date"))),
            "updated": "", "authors": authors, "body": body,
            "tags": [_text(c) for c in it.findall("category") if _text(c)],
            "enclosures": enclosures, "base": base,
        })
    return feed_title, items


def _rss1(root: ET.Element, feed_url: str) -> tuple[str, list[dict]]:
    channel = root.find(_q(RSS1, "channel"))
    feed_title = _text(channel.find(_q(RSS1, "title"))) if channel is not None else ""
    base = canonical_url(_text(channel.find(_q(RSS1, "link"))) if channel is not None else feed_url) or feed_url
    items = []
    for it in root.findall(_q(RSS1, "item")):
        link = _text(it.find(_q(RSS1, "link")))
        items.append({
            "guid": it.get(_q(RDF, "about"), ""), "title": strip_html(_text(it.find(_q(RSS1, "title"))), None),
            "link": link, "published": _text(it.find(_q(DC, "date"))), "updated": "",
            "authors": [a for a in [_text(it.find(_q(DC, "creator")))] if a],
            "body": _text(it.find(_q(CONTENT, "encoded"))) or _text(it.find(_q(RSS1, "description"))),
            "tags": [_text(s) for s in it.findall(_q(DC, "subject")) if _text(s)], "enclosures": [], "base": base,
        })
    return feed_title, items


def _atom_link(entry: ET.Element, rel: str = "alternate") -> str:
    fallback = ""
    for link in entry.findall(_q(ATOM, "link")):
        r = link.get("rel", "alternate")
        if r == rel and link.get("type", "text/html") in {"text/html", "application/xhtml+xml", ""}:
            return link.get("href", "")
        if r == rel and not fallback:
            fallback = link.get("href", "")
    return fallback


def _atom(root: ET.Element, feed_url: str) -> tuple[str, list[dict]]:
    feed_title = _text(root.find(_q(ATOM, "title")))
    xml_base = root.get("{http://www.w3.org/XML/1998/namespace}base")
    base = canonical_url(_atom_link(root) or xml_base or feed_url, feed_url) or feed_url
    items = []
    for e in root.findall(_q(ATOM, "entry")):
        content = e.find(_q(ATOM, "content"))
        summary = e.find(_q(ATOM, "summary"))
        body = _text(content) if content is not None and _text(content) else _text(summary)
        enclosures = [{"url": canonical_url(l.get("href", ""), base), "type": l.get("type", ""),
                       "length": int(l.get("length")) if (l.get("length") or "").isdigit() else None}
                      for l in e.findall(_q(ATOM, "link")) if l.get("rel") == "enclosure" and l.get("href")]
        items.append({
            "guid": _text(e.find(_q(ATOM, "id"))), "title": strip_html(_text(e.find(_q(ATOM, "title"))), None),
            "link": _atom_link(e), "published": _text(e.find(_q(ATOM, "published"))),
            "updated": _text(e.find(_q(ATOM, "updated"))),
            "authors": [_text(a.find(_q(ATOM, "name"))) for a in e.findall(_q(ATOM, "author"))
                        if _text(a.find(_q(ATOM, "name")))],
            "body": body, "tags": [c.get("label") or c.get("term", "") for c in e.findall(_q(ATOM, "category"))
                                   if c.get("label") or c.get("term")],
            "enclosures": enclosures, "base": base,
        })
    return feed_title, items


def _jsonfeed(doc: dict, feed_url: str) -> tuple[str, list[dict]]:
    if not str(doc.get("version", "")).startswith("https://jsonfeed.org/version/"):
        raise FeedError("JSON document is not a JSON Feed (missing version)")
    base = canonical_url(doc.get("home_page_url") or feed_url) or feed_url
    top_authors = [a.get("name", "") for a in doc.get("authors") or ([doc["author"]] if doc.get("author") else [])
                   if isinstance(a, dict) and a.get("name")]
    items = []
    for it in doc.get("items") or []:
        if not isinstance(it, dict):
            continue
        authors = [a.get("name", "") for a in it.get("authors") or ([it["author"]] if it.get("author") else [])
                   if isinstance(a, dict) and a.get("name")] or top_authors
        items.append({
            "guid": str(it.get("id", "")), "title": strip_html(it.get("title", ""), None),
            "link": it.get("url") or it.get("external_url") or "", "published": it.get("date_published", ""),
            "updated": it.get("date_modified", ""), "authors": authors,
            "body": it.get("summary") or it.get("content_html") or it.get("content_text") or "",
            "tags": [str(t) for t in it.get("tags") or []],
            "enclosures": [{"url": canonical_url(a.get("url", ""), base), "type": a.get("mime_type", ""),
                            "length": a.get("size_in_bytes")} for a in it.get("attachments") or [] if a.get("url")],
            "base": base,
        })
    return doc.get("title", ""), items


def parse_feed(data: bytes | str, feed_url: str = "") -> dict:
    """Parse one feed document. Returns {"format", "title", "items": [normalised items]}."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    stripped = raw.lstrip(b"\xef\xbb\xbf \t\r\n")
    if stripped[:1] in (b"{", b"["):
        try:
            doc = json.loads(stripped.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FeedError(f"invalid JSON: {exc}") from exc
        if not isinstance(doc, dict):
            raise FeedError("JSON Feed must be an object")
        fmt, (title, items) = "jsonfeed", _jsonfeed(doc, feed_url)
    else:
        root = _safe_xml(stripped)
        tag = root.tag
        if tag == "rss":
            fmt, (title, items) = "rss2", _rss2(root, feed_url)
        elif tag == _q(ATOM, "feed"):
            fmt, (title, items) = "atom", _atom(root, feed_url)
        elif tag == _q(RDF, "RDF"):
            fmt, (title, items) = "rss1", _rss1(root, feed_url)
        else:
            raise FeedError(f"unsupported root element {tag!r}")
    return {"format": fmt, "title": title, "items": normalize_items(items, feed_url, title, fmt)}


def normalize_items(raw_items: Iterable[dict], feed_url: str, feed_title: str, fmt: str) -> list[dict]:
    out = []
    for r in raw_items:
        url = canonical_url(r.get("link", ""), r.get("base") or feed_url or None)
        published = parse_date(r.get("published"))
        updated = parse_date(r.get("updated"))
        if published is None and updated is not None:
            published = updated
        title = r.get("title") or strip_html(r.get("body", ""), 80) or "(untitled)"
        out.append({
            "id": _item_id(url, r.get("guid", ""), title, feed_url),
            "guid": r.get("guid", ""),
            "title": title,
            "url": url,
            "published": _iso(published),
            "updated": _iso(updated),
            "authors": [a for a in r.get("authors", []) if a],
            "summary": strip_html(r.get("body", "")),
            "tags": sorted({t.strip() for t in r.get("tags", []) if t and t.strip()}),
            "enclosures": r.get("enclosures", []),
            "source": {"feed_url": feed_url, "feed_title": feed_title, "format": fmt},
            "also_in": [],
        })
    return out


# --------------------------------------------------------------------------- list operations

def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _sort_key(item: dict) -> str:
    return item.get("published") or item.get("updated") or ""


def dedupe(items: Iterable[dict], by_title: bool = True) -> list[dict]:
    """Remove duplicates by canonical URL, then by feed guid, then (optionally) by normalised title.

    The newest copy is kept; the feed URLs of dropped copies are recorded in ``also_in``.
    Returned items are sorted newest first; undated items go last.
    """
    ordered = sorted(items, key=_sort_key, reverse=True)
    kept: list[dict] = []
    seen: dict[str, dict] = {}
    for item in ordered:
        keys = []
        if item.get("url"):
            keys.append("u:" + item["url"])
        if item.get("guid"):
            keys.append("g:" + item["guid"])
        if by_title and len(_norm_title(item.get("title", ""))) >= 12:
            keys.append("t:" + _norm_title(item["title"]))
        hit = next((seen[k] for k in keys if k in seen), None)
        if hit is not None:
            src = item.get("source", {}).get("feed_url", "")
            if src and src != hit.get("source", {}).get("feed_url") and src not in hit["also_in"]:
                hit["also_in"].append(src)
            for k in keys:
                seen.setdefault(k, hit)
            continue
        item = dict(item, also_in=list(item.get("also_in", [])))
        kept.append(item)
        for k in keys:
            seen[k] = item
    return kept


def filter_since(items: Iterable[dict], since: datetime | str | None, keep_undated: bool = False,
                 use_updated: bool = True) -> list[dict]:
    """Keep items published (or, if use_updated, updated) at or after ``since``.

    ``since`` may be a datetime, an ISO date/time string, or a relative value such as '7d' or '36h'.
    """
    if since is None:
        return list(items)
    if isinstance(since, str):
        m = re.fullmatch(r"(\d+)([dh])", since.strip())
        if m:
            delta = timedelta(days=int(m[1])) if m[2] == "d" else timedelta(hours=int(m[1]))
            cutoff = datetime.now(timezone.utc) - delta
        else:
            cutoff = parse_date(since)
            if cutoff is None:
                raise ValueError(f"cannot parse since={since!r}")
    else:
        cutoff = since if since.tzinfo else since.replace(tzinfo=timezone.utc)
    out = []
    for item in items:
        stamps = [parse_date(item.get("published"))]
        if use_updated:
            stamps.append(parse_date(item.get("updated")))
        stamps = [s for s in stamps if s]
        if not stamps:
            if keep_undated:
                out.append(item)
            continue
        if max(stamps) >= cutoff:
            out.append(item)
    return out


def merge_feeds(documents: Iterable[tuple[str, bytes | str]], since: datetime | str | None = None,
                keep_undated: bool = False) -> tuple[list[dict], list[dict]]:
    """Parse many (feed_url, bytes) pairs. Returns (items, errors) with items deduplicated and filtered."""
    items: list[dict] = []
    errors: list[dict] = []
    for feed_url, data in documents:
        try:
            items.extend(parse_feed(data, feed_url)["items"])
        except FeedError as exc:
            errors.append({"feed_url": feed_url, "error": str(exc)})
    return filter_since(dedupe(items), since, keep_undated=keep_undated), errors


# --------------------------------------------------------------------------- discovery

FEED_TYPES = {"application/rss+xml": "rss", "application/atom+xml": "atom", "application/feed+json": "jsonfeed",
              "application/json": "jsonfeed", "application/rdf+xml": "rss1"}


class _LinkFinder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict] = []

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        rels = a.get("rel", "").lower().split()
        typ = a.get("type", "").lower().split(";")[0].strip()
        if "alternate" in rels and typ in FEED_TYPES and a.get("href"):
            if typ == "application/json" and "feed" not in (a.get("title", "") + a["href"]).lower():
                return
            self.links.append({"href": a["href"], "type": FEED_TYPES[typ], "title": a.get("title", "")})


def discover_feeds(page_html: str, base_url: str) -> list[dict]:
    """Return feed links advertised with <link rel="alternate"> in an HTML page, as absolute URLs."""
    finder = _LinkFinder()
    finder.feed(page_html)
    out, seen = [], set()
    for link in finder.links:
        url = canonical_url(link["href"], base_url)
        if url not in seen:
            seen.add(url)
            out.append({"url": url, "format": link["type"], "title": link["title"]})
    return out


# --------------------------------------------------------------------------- polite fetching

@dataclass
class HostSpacer:
    """Keeps a minimum interval between requests to the same host. ``clock``/``sleep`` are injectable."""
    min_interval_s: float = 5.0
    clock: Any = time.monotonic
    sleep: Any = time.sleep
    last: dict = field(default_factory=dict)

    def wait(self, url: str) -> float:
        host = urllib.parse.urlsplit(url).hostname or ""
        now = self.clock()
        due = self.last.get(host, -1e18) + self.min_interval_s
        delay = max(0.0, due - now)
        if delay:
            self.sleep(delay)
        self.last[host] = now + delay
        return delay


def retry_after_seconds(value: str | None, default: float = 300.0) -> float:
    """Parse a Retry-After header (seconds or HTTP date). Unknown values give ``default``."""
    if not value:
        return default
    value = value.strip()
    if value.isdigit():
        return float(value)
    dt = parse_date(value)
    if dt is None:
        return default
    return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())


def fetch(url: str, etag: str | None = None, last_modified: str | None = None,
          user_agent: str = DEFAULT_USER_AGENT, timeout: float = 20.0, max_bytes: int = 5_000_000,
          spacer: HostSpacer | None = None, opener: Any = None) -> dict:
    """GET a feed politely. Returns {"status", "body", "etag", "last_modified", "retry_after"}.

    304 returns body None. 429/503 return the parsed Retry-After so callers can back off.
    ``opener`` defaults to urllib.request.urlopen and can be replaced in tests.
    """
    if not url.startswith(("https://", "http://")):
        raise ValueError("only http(s) URLs are fetched")
    if spacer is not None:
        spacer.wait(url)
    headers = {"User-Agent": user_agent, "Accept": "application/atom+xml, application/rss+xml, "
               "application/feed+json, application/xml;q=0.9, */*;q=0.5"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    req = urllib.request.Request(url, headers=headers)
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(req, timeout=timeout) as resp:
            body = resp.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise FeedError(f"feed larger than {max_bytes} bytes")
            return {"status": getattr(resp, "status", 200), "body": body, "etag": resp.headers.get("ETag"),
                    "last_modified": resp.headers.get("Last-Modified"), "retry_after": None}
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return {"status": 304, "body": None, "etag": etag, "last_modified": last_modified, "retry_after": None}
        retry = retry_after_seconds(exc.headers.get("Retry-After") if exc.headers else None) \
            if exc.code in (429, 503) else None
        return {"status": exc.code, "body": None, "etag": etag, "last_modified": last_modified, "retry_after": retry}


# --------------------------------------------------------------------------- CLI

def _load_cache(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Normalise RSS/Atom/JSON Feed files or URLs into one list.")
    ap.add_argument("sources", nargs="*", help="feed files or http(s) URLs")
    ap.add_argument("--since", help="ISO date/time or relative value such as 7d or 36h")
    ap.add_argument("--keep-undated", action="store_true")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a text list")
    ap.add_argument("--cache", default=".feed-cache.json", help="ETag/Last-Modified cache for URL sources")
    ap.add_argument("--min-interval", type=float, default=5.0, help="seconds between requests to one host")
    ap.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    ap.add_argument("--discover", help="HTML file to scan for <link rel=alternate> feeds")
    ap.add_argument("--base", default="", help="base URL for --discover")
    a = ap.parse_args(argv)

    if a.discover:
        print(json.dumps(discover_feeds(Path(a.discover).read_text(encoding="utf-8"), a.base), indent=2))
        return 0
    cache_path = Path(a.cache)
    cache = _load_cache(cache_path)
    spacer = HostSpacer(a.min_interval)
    docs, errors = [], []
    for src in a.sources:
        if src.startswith(("http://", "https://")):
            prev = cache.get(src, {})
            res = fetch(src, prev.get("etag"), prev.get("last_modified"), a.user_agent, spacer=spacer)
            if res["status"] == 200 and res["body"] is not None:
                cache[src] = {"etag": res["etag"], "last_modified": res["last_modified"],
                              "fetched": _iso(datetime.now(timezone.utc))}
                docs.append((src, res["body"]))
            elif res["status"] != 304:
                errors.append({"feed_url": src, "error": f"HTTP {res['status']}",
                               "retry_after_s": res["retry_after"]})
        else:
            docs.append((src, Path(src).read_bytes()))
    items, parse_errors = merge_feeds(docs, a.since, a.keep_undated)
    errors += parse_errors
    if any(s.startswith("http") for s in a.sources):
        cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    if a.json:
        print(json.dumps({"items": items, "errors": errors}, indent=2, ensure_ascii=False))
    else:
        for it in items:
            print(f"{(it['published'] or '----------')[:10]}  {it['title']}\n            {it['url']}")
        for e in errors:
            print(f"ERROR {e['feed_url']}: {e['error']}", file=sys.stderr)
    return 1 if errors and not items else 0


if __name__ == "__main__":
    raise SystemExit(main())
