#!/usr/bin/env python3
"""Parse feeds, release APIs and advisory APIs into normalised ``agent_feed_item`` dicts.

Standard library only. One entry point::

    from agent_feeds_parse import parse
    items = parse(body_bytes, url="https://github.com/astral-sh/uv/releases.atom",
                  source_id="uv-releases", collection="my-feeds")

``fmt`` is detected from the URL and the body when it is not given. Supported formats:

=================  =============================================================
rss                RSS 2.0 and RSS 1.0 (RDF)
atom               Atom 1.0
json-feed          JSON Feed 1.0 / 1.1
github-releases    https://github.com/<owner>/<repo>/releases.atom or tags.atom
statuspage-json    Atlassian Statuspage /api/v2/summary.json, incidents.json, ...
statuspage-rss     Statuspage /history.rss or /history.atom
cisa-kev           CISA Known Exploited Vulnerabilities JSON
osv                OSV vulnerability JSON (one record, a list, or {"vulns": [...]})
nvd                NVD CVE API 2.0 JSON
pypi-json          https://pypi.org/pypi/<name>/json (releases + vulnerabilities)
npm                https://registry.npmjs.org/<name> packument
endoflife          https://endoflife.date/api/v1/products/<p> and legacy /api/<p>.json
arxiv              arXiv API Atom (export.arxiv.org/api/query)
hf-papers          https://huggingface.co/api/daily_papers
goproxy-latest     https://proxy.golang.org/<module>/@latest
goproxy-list       https://proxy.golang.org/<module>/@v/list
crates-index       https://index.crates.io/<prefix>/<crate> (sparse index NDJSON)
sitemap            sitemap.xml <urlset> with <lastmod>
ical               iCalendar VEVENTs
=================  =============================================================

Items keep titles, links and short summaries only (``summary`` is cut to 400
characters); full article bodies are never stored. ``collection`` feed defaults
(vendor, products, change_types) are passed in by the caller and merged.

CLI: ``python3 agent_feeds_parse.py FILE [--url URL] [--format FMT]`` prints items as JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

__all__ = [
    "FORMATS", "parse", "detect_format", "make_item", "normalize_url", "html_to_text", "shorten",
    "parse_date", "extract_versions", "extract_cves", "infer_change_types", "cvss3_base_score",
    "severity_from_score", "ParseError",
]

FORMATS = (
    "rss", "atom", "json-feed", "github-releases", "statuspage-json", "statuspage-rss", "cisa-kev", "osv",
    "nvd", "pypi-json", "npm", "endoflife", "arxiv", "hf-papers", "goproxy-latest", "goproxy-list",
    "crates-index", "sitemap", "ical",
)
CHANGE_TYPES = (
    "release", "breaking-change", "deprecation", "security", "incident", "pricing", "model-release", "docs",
    "research", "community", "policy", "event", "tutorial", "dataset",
)
SEVERITIES = ("none", "low", "medium", "high", "critical", "unknown")
SUMMARY_LIMIT = 400
TITLE_LIMIT = 300
UTC = timezone.utc

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rss1": "http://purl.org/rss/1.0/",
    "arxiv": "http://arxiv.org/schemas/atom",
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
}


class ParseError(ValueError):
    """The body could not be parsed as the requested format."""


# --------------------------------------------------------------------------- text helpers

class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "svg", "head"}
    BLOCK = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table",
             "section", "article", "pre", "blockquote", "hr", "dd", "dt"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):  # noqa: D401
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append(" \n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.parts.append(" \n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(value: str | None) -> str:
    """Visible text of an HTML fragment on one line (scripts/styles dropped, entities decoded)."""
    if not value:
        return ""
    if "<" not in value:
        return re.sub(r"\s+", " ", html.unescape(value)).strip()
    p = _TextExtractor()
    try:
        p.feed(value)
        p.close()
    except Exception:  # noqa: BLE001 - malformed markup: fall back to tag stripping
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()
    return re.sub(r"\s+", " ", "".join(p.parts)).strip()


def shorten(text: str, limit: int = SUMMARY_LIMIT) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    space = cut.rfind(" ")
    if space > limit * 0.6:
        cut = cut[:space]
    return cut.rstrip(" ,;:.-") + "…"


def parse_date(value) -> str | None:
    """Normalise RFC 822, ISO 8601, date-only or epoch values to ``YYYY-MM-DDTHH:MM:SSZ`` (UTC)."""
    if value is None or value == "" or isinstance(value, bool):
        return None
    dt: datetime | None = None
    if isinstance(value, (int, float)):
        secs = value / 1000 if value > 1e11 else value
        dt = datetime.fromtimestamp(secs, tz=UTC)
    else:
        s = str(value).strip()
        s2 = re.sub(r"(\.\d{6})\d+", r"\1", s.replace("Z", "+00:00").replace("z", "+00:00"))
        if re.match(r"^\d{8}T\d{6}", s2):  # iCalendar basic format
            try:
                dt = datetime.strptime(s2[:15], "%Y%m%dT%H%M%S")
            except ValueError:
                dt = None
        elif re.match(r"^\d{8}$", s2):
            dt = datetime.strptime(s2, "%Y%m%d")
        if dt is None:
            try:
                dt = datetime.fromisoformat(s2)
            except ValueError:
                try:
                    dt = parsedate_to_datetime(s)
                except (TypeError, ValueError, IndexError):
                    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
                    if not m:
                        return None
                    try:
                        dt = datetime(int(m[1]), int(m[2]), int(m[3]))
                    except ValueError:
                        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dt(value: str | None) -> datetime | None:
    iso = parse_date(value)
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC) if iso else None


_TRACKING = re.compile(
    r"^(utm_.*|mc_cid|mc_eid|_hsenc|_hsmi|mkt_tok|fbclid|gclid|dclid|msclkid|yclid|igshid|ref_src|ref|"
    r"cmpid|s_cid|trk|spm|vero_.*|oly_.*|__s)$", re.I)


def normalize_url(url: str) -> str:
    """Canonical form used for deduplication: https, lower-case host without www., no fragment,
    no tracking parameters, sorted query, no trailing slash."""
    s = (url or "").strip()
    try:
        parts = urlsplit(s)
    except ValueError:
        return s
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        return s
    host = (parts.hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    try:
        port = parts.port
    except ValueError:
        port = None
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", unquote(parts.path) or "/")
    if len(path) > 1:
        path = path.rstrip("/")
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                             if not _TRACKING.match(k)))
    return urlunsplit(("https", netloc, path or "/", query, ""))


_VERSION_RE = re.compile(
    r"(?<![\w.])v?(\d+(?:\.\d+){1,3}(?:-[0-9A-Za-z][0-9A-Za-z.]*|(?:a|b|rc|\.dev|\.post)\d+)?)(?![\w.]*\d)")
_CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)


def extract_versions(text: str, limit: int = 5) -> list[str]:
    out: list[str] = []
    for m in _VERSION_RE.finditer(text or ""):
        v = m.group(1)
        if v not in out:
            out.append(v)
        if len(out) >= limit:
            break
    return out


def extract_cves(text: str) -> list[str]:
    out: list[str] = []
    for m in _CVE_RE.finditer(text or ""):
        c = m.group(0).upper()
        if c not in out:
            out.append(c)
    return out


_RULES = [
    ("breaking-change", re.compile(r"\bbreaking\b|backwards?[- ]incompatible|\bno longer (?:supported|works|accepts)|"
                                   r"\bremoved?\b (?:support|the|deprecated)|\bmigration (?:required|guide)", re.I)),
    ("deprecation", re.compile(r"\bdeprecat|\bend[- ]of[- ](?:life|support)\b|\bEOL\b|\bsunset|\bwill be removed\b|"
                               r"\bretir(?:e|ed|ing|ement)\b", re.I)),
    ("security", re.compile(r"\bCVE-\d{4}-\d+|\bGHSA-|\bsecurity (?:fix|advisory|update|release|issue)|"
                            r"\bvulnerab|\bexploit|\bRCE\b|\bXSS\b|\bSSRF\b", re.I)),
    ("pricing", re.compile(r"\bpricing\b|\bprice (?:change|increase|cut)|\bbilling change", re.I)),
]


def infer_change_types(title: str, text: str = "", defaults=None) -> list[str]:
    out = [c for c in (defaults or []) if c in CHANGE_TYPES]
    blob = f"{title}\n{text[:4000]}"
    for name, rx in _RULES:
        if name not in out and rx.search(blob):
            out.append(name)
    return out


# --------------------------------------------------------------------------- CVSS

_CVSS3 = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
    "AC": {"L": 0.77, "H": 0.44},
    "UI": {"N": 0.85, "R": 0.62},
    "CIA": {"H": 0.56, "L": 0.22, "N": 0.0},
    "PR_U": {"N": 0.85, "L": 0.62, "H": 0.27},
    "PR_C": {"N": 0.85, "L": 0.68, "H": 0.5},
}


def _roundup(x: float) -> float:
    i = round(x * 100000)
    return i / 100000.0 if i % 10000 == 0 else (math.floor(i / 10000) + 1) / 10.0


def cvss3_base_score(vector: str) -> float | None:
    """CVSS v3.0/v3.1 base score from a vector such as ``CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H``."""
    if not vector or not vector.upper().startswith("CVSS:3"):
        return None
    m = dict(p.split(":", 1) for p in vector.split("/")[1:] if ":" in p)
    try:
        scope_changed = m["S"] == "C"
        iss = 1 - (1 - _CVSS3["CIA"][m["C"]]) * (1 - _CVSS3["CIA"][m["I"]]) * (1 - _CVSS3["CIA"][m["A"]])
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15 if scope_changed else 6.42 * iss
        pr = _CVSS3["PR_C" if scope_changed else "PR_U"][m["PR"]]
        expl = 8.22 * _CVSS3["AV"][m["AV"]] * _CVSS3["AC"][m["AC"]] * pr * _CVSS3["UI"][m["UI"]]
    except KeyError:
        return None
    if impact <= 0:
        return 0.0
    return _roundup(min(1.08 * (impact + expl), 10) if scope_changed else min(impact + expl, 10))


def severity_from_score(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score == 0:
        return "none"
    if score < 4:
        return "low"
    if score < 7:
        return "medium"
    if score < 9:
        return "high"
    return "critical"


_WORD_SEVERITY = {"none": "none", "info": "low", "informational": "low", "low": "low", "minor": "low",
                  "moderate": "medium", "medium": "medium", "important": "high", "high": "high", "major": "high",
                  "critical": "critical"}


def _word_severity(word) -> str | None:
    return _WORD_SEVERITY.get(str(word or "").strip().lower())


# --------------------------------------------------------------------------- item builder

def _clean_list(values, limit: int = 20) -> list[str]:
    out: list[str] = []
    for v in values or []:
        v = str(v).strip()
        if v and v not in out:
            out.append(v)
    return out[:limit]


def make_item(*, source_id: str, collection: str = "", title: str, url: str, published=None, updated=None,
              summary: str = "", vendor: str | None = None, products=None, versions=None, change_types=None,
              severity: str | None = None, affected_packages=None, cve_ids=None, entities=None,
              guid: str | None = None, source_format: str | None = None, authors=None, links=None,
              fetched: str | None = None, infer: bool = True, cvss: float | None = None) -> dict:
    """Build one normalised agent_feed_item. Summaries are plain text, at most 400 characters."""
    title = shorten(html_to_text(title) or "(untitled)", TITLE_LIMIT)
    summary_text = html_to_text(summary)
    url = (url or "").strip()
    norm = normalize_url(url) if url else ""
    key_basis = guid or norm or title
    item_id = "afi_" + hashlib.sha256(f"{source_id}\n{key_basis}".encode()).hexdigest()[:20]
    dedupe_key = hashlib.sha256((norm or f"title:{title.lower()}").encode()).hexdigest()[:24]
    ctypes = infer_change_types(title, summary_text, change_types) if infer else _clean_list(change_types)
    ctypes = [c for c in ctypes if c in CHANGE_TYPES]
    cves = _clean_list(list(cve_ids or []) + (extract_cves(f"{title} {summary_text}") if infer else []))
    if cves and "security" not in ctypes:
        ctypes.append("security")
    vers = _clean_list(versions if versions is not None else extract_versions(title))
    item: dict = {
        "id": item_id,
        "source_id": source_id,
        "collection": collection or "",
        "title": title,
        "url": url,
        "published": parse_date(published),
        "updated": parse_date(updated) or parse_date(published),
        "summary": shorten(summary_text),
        "vendor": vendor or None,
        "products": _clean_list(products),
        "versions": vers,
        "change_types": ctypes,
        "severity": severity if severity in SEVERITIES else ("unknown" if "security" in ctypes else None),
        "affected_packages": [dict(p) for p in (affected_packages or [])][:50],
        "cve_ids": cves,
        "entities": _clean_list(entities, 30),
        "dedupe_key": dedupe_key,
        "cluster_id": None,
        "relevance": None,
    }
    if cvss is not None:
        item["cvss"] = float(cvss)
    if source_format:
        item["source_format"] = source_format
    if authors:
        item["authors"] = _clean_list(authors, 10)
    if links:
        item["links"] = _clean_list(links, 25)
    if fetched:
        item["fetched"] = parse_date(fetched)
    return item


# --------------------------------------------------------------------------- format detection

def _url_format(url: str) -> str | None:
    u = (url or "").lower()
    if re.search(r"github\.com/[^/]+/[^/]+/(releases|tags)\.atom", u):
        return "github-releases"
    if re.search(r"/history\.(rss|atom)(\?|$)", u):
        return "statuspage-rss"
    if re.search(r"/api/v2/(summary|incidents|incidents/unresolved|scheduled-maintenances[^/]*)\.json", u):
        return "statuspage-json"
    if "known_exploited_vulnerabilities" in u and u.endswith(".json"):
        return "cisa-kev"
    if "api.osv.dev/" in u or "osv-vulnerabilities" in u:
        return "osv"
    if "services.nvd.nist.gov/rest/json/cves/2.0" in u:
        return "nvd"
    if re.search(r"pypi\.org/pypi/[^/]+(/[^/]+)?/json", u):
        return "pypi-json"
    if "registry.npmjs.org/" in u:
        return "npm"
    if "endoflife.date/api/" in u:
        return "endoflife"
    if "export.arxiv.org/api/" in u:
        return "arxiv"
    if "huggingface.co/api/daily_papers" in u:
        return "hf-papers"
    if "proxy.golang.org/" in u and u.endswith("/@latest"):
        return "goproxy-latest"
    if "proxy.golang.org/" in u and u.endswith("/@v/list"):
        return "goproxy-list"
    if "index.crates.io/" in u:
        return "crates-index"
    if u.endswith((".ics", ".ical")) or "/ical" in u:
        return "ical"
    return None


def detect_format(body: bytes | str, url: str = "", content_type: str = "") -> str:
    """Pick a parser from the URL first, then from the body."""
    by_url = _url_format(url)
    if by_url:
        return by_url
    text = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body)
    head = text.lstrip("﻿ \t\r\n")[:2000]
    if head.startswith("BEGIN:VCALENDAR"):
        return "ical"
    if head.startswith(("{", "[")):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            if head.startswith("{") and '"vers"' in head:
                return "crates-index"
            raise ParseError("body looks like JSON but does not parse")
        return _json_format(data)
    if "<urlset" in head:
        return "sitemap"
    if "<feed" in head:
        return "arxiv" if "arxiv.org/api" in head else "atom"
    if "<rss" in head or "<rdf:RDF" in head or "purl.org/rss/1.0" in head:
        return "rss"
    raise ParseError(f"cannot detect feed format (content-type {content_type!r})")


def _json_format(data) -> str:
    if isinstance(data, dict):
        if "jsonfeed.org" in str(data.get("version", "")):
            return "json-feed"
        if "catalogVersion" in data and "vulnerabilities" in data:
            return "cisa-kev"
        if data.get("format") == "NVD_CVE" or ("vulnerabilities" in data and "resultsPerPage" in data):
            return "nvd"
        if "info" in data and "releases" in data:
            return "pypi-json"
        if "dist-tags" in data and "versions" in data:
            return "npm"
        if "page" in data and ("incidents" in data or "scheduled_maintenances" in data):
            return "statuspage-json"
        if "vulns" in data or ("affected" in data and "id" in data) or ("id" in data and "modified" in data):
            return "osv"
        if isinstance(data.get("result"), dict) and "releases" in data["result"]:
            return "endoflife"
        if "Version" in data and "Time" in data:
            return "goproxy-latest"
        if "vers" in data and "name" in data:
            return "crates-index"
    if isinstance(data, list) and data and isinstance(data[0], dict):
        if "paper" in data[0]:
            return "hf-papers"
        if "cycle" in data[0]:
            return "endoflife"
        if "affected" in data[0] and "id" in data[0]:
            return "osv"
    raise ParseError("unrecognised JSON document")


# --------------------------------------------------------------------------- XML helpers

def _xml_root(body: bytes | str) -> ET.Element:
    raw = body.encode("utf-8") if isinstance(body, str) else bytes(body)
    if re.search(rb"<!ENTITY", raw[:65536], re.I):
        raise ParseError("refusing XML with entity declarations")
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ParseError(f"XML does not parse: {exc}") from exc


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _child(el: ET.Element, *names: str) -> ET.Element | None:
    for c in el:
        if _local(c.tag) in names:
            return c
    return None


def _children(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if _local(c.tag) == name]


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    if len(el) and el.get("type") in ("xhtml",):
        return ET.tostring(el, encoding="unicode", method="text")
    return (el.text or "").strip()


def _child_text(el: ET.Element, *names: str) -> str:
    return _text(_child(el, *names))


# --------------------------------------------------------------------------- RSS / Atom / JSON Feed

def _ctx_defaults(ctx: dict) -> dict:
    return {"source_id": ctx["source_id"], "collection": ctx["collection"], "vendor": ctx.get("vendor"),
            "fetched": ctx.get("fetched")}


def _rss_items(root: ET.Element) -> tuple[list[ET.Element], str]:
    if _local(root.tag) == "RDF":
        channel = _child(root, "channel")
        return _children(root, "item"), _child_text(channel, "title") if channel is not None else ""
    channel = _child(root, "channel")
    if channel is None:
        raise ParseError("RSS without <channel>")
    return _children(channel, "item"), _child_text(channel, "title")


def parse_rss(body, ctx: dict) -> list[dict]:
    root = _xml_root(body)
    if _local(root.tag) == "feed":
        return parse_atom(body, ctx)
    entries, feed_title = _rss_items(root)
    out = []
    for it in entries:
        title = _child_text(it, "title")
        link = _child_text(it, "link") or (it.get(f"{{{NS['rdf']}}}about") or "")
        guid = _child_text(it, "guid") or link
        if not link and guid.startswith("http"):
            link = guid
        desc = _child_text(it, "description") or _child_text(it, "encoded")
        published = _child_text(it, "pubDate") or _child_text(it, "date")
        authors = [_text(a) for a in it if _local(a.tag) in ("author", "creator")]
        cats = [_text(c) for c in _children(it, "category")]
        out.append(_finish(ctx, title=title, url=link or ctx["url"], guid=guid, summary=desc,
                           published=published, authors=authors, entities=cats, fmt="rss"))
    return out


def _atom_link(entry: ET.Element) -> str:
    first = ""
    for link in _children(entry, "link"):
        href = link.get("href", "")
        rel = link.get("rel", "alternate")
        if rel == "alternate" and href:
            return href
        first = first or href
    return first


def parse_atom(body, ctx: dict, fmt: str = "atom") -> list[dict]:
    root = _xml_root(body)
    if _local(root.tag) != "feed":
        if _local(root.tag) in ("rss", "RDF"):
            return parse_rss(body, ctx)
        raise ParseError("Atom document without <feed>")
    out = []
    for entry in _children(root, "entry"):
        title = _child_text(entry, "title")
        content = _child(entry, "summary") if _child(entry, "summary") is not None else _child(entry, "content")
        authors = [_child_text(a, "name") for a in _children(entry, "author")]
        cats = [c.get("term", "") for c in _children(entry, "category")]
        out.append(_finish(ctx, title=title, url=_atom_link(entry) or ctx["url"], guid=_child_text(entry, "id"),
                           summary=_text(content), published=_child_text(entry, "published") or
                           _child_text(entry, "updated"), updated=_child_text(entry, "updated"),
                           authors=authors, entities=cats, fmt=fmt))
    return out


def parse_json_feed(body, ctx: dict) -> list[dict]:
    data = _json(body)
    out = []
    for it in data.get("items", []):
        url = it.get("url") or it.get("external_url") or ctx["url"]
        summary = it.get("summary") or it.get("content_text") or it.get("content_html") or ""
        authors = [a.get("name", "") for a in (it.get("authors") or ([it["author"]] if it.get("author") else []))]
        out.append(_finish(ctx, title=it.get("title") or shorten(html_to_text(summary), 90), url=url,
                           guid=str(it.get("id") or url), summary=summary, published=it.get("date_published"),
                           updated=it.get("date_modified"), authors=authors, entities=it.get("tags"),
                           fmt="json-feed"))
    return out


def _github_repo(url: str) -> tuple[str, str] | None:
    m = re.search(r"github\.com/([^/]+)/([^/]+?)(?:/releases|/tags|\.git|/?$)", url or "")
    return (m.group(1), m.group(2)) if m else None


_PRERELEASE = re.compile(r"(alpha|beta|\brc\d*\b|-rc|preview|nightly|canary|\bdev\b|\.dev\d|-pre\b|\d(?:a|b|rc)\d+\b)", re.I)


def parse_github_releases(body, ctx: dict) -> list[dict]:
    repo = _github_repo(ctx["url"])
    items = parse_atom(body, dict(ctx, change_types=list(dict.fromkeys(["release", *ctx["change_types"]]))),
                       fmt="github-releases")
    for it in items:
        tag = it["url"].rsplit("/tag/", 1)[-1] if "/tag/" in it["url"] else ""
        vers = extract_versions(unquote(tag)) or it["versions"]
        it["versions"] = vers[:3]
        if repo:
            owner, name = repo
            it["vendor"] = it["vendor"] or owner
            if name not in it["products"]:
                it["products"].insert(0, name)
        if _PRERELEASE.search(it["title"] + " " + tag) and "prerelease" not in it["entities"]:
            it["entities"].append("prerelease")
    return items


# --------------------------------------------------------------------------- Statuspage

_IMPACT = {"none": "none", "minor": "low", "major": "high", "critical": "critical", "maintenance": "low"}


def parse_statuspage_json(body, ctx: dict) -> list[dict]:
    data = _json(body)
    page = data.get("page") or {}
    page_name = page.get("name") or ctx.get("vendor") or "Status page"
    base = (page.get("url") or "").rstrip("/")
    out = []
    groups = [("incidents", "incident"), ("scheduled_maintenances", "event")]
    for key, ctype in groups:
        for inc in data.get(key) or []:
            updates = inc.get("incident_updates") or []
            latest = updates[0] if updates else {}
            url = inc.get("shortlink") or (f"{base}/incidents/{inc.get('id')}" if base and inc.get("id") else ctx["url"])
            comps = [c.get("name", "") for c in inc.get("components") or []]
            status = inc.get("status") or ""
            text = f"{status.capitalize()}: {latest.get('body', '')}" if status else latest.get("body", "")
            out.append(_finish(
                ctx, title=f"{page_name}: {inc.get('name', 'incident')}", url=url, guid=str(inc.get("id") or url),
                summary=text, published=inc.get("started_at") or inc.get("created_at"), updated=inc.get("updated_at"),
                change_types=[ctype], severity=_IMPACT.get(str(inc.get("impact", "")).lower(), "unknown"),
                entities=[f"status:{status}"] if status else [], products=comps, vendor=ctx.get("vendor") or page_name,
                fmt="statuspage-json", infer=False))
    return out


def parse_statuspage_rss(body, ctx: dict) -> list[dict]:
    ctx = dict(ctx, change_types=list(dict.fromkeys(["incident", *ctx["change_types"]])))
    items = parse_atom(body, ctx) if _local(_xml_root(body).tag) == "feed" else parse_rss(body, ctx)
    for it in items:
        it["source_format"] = "statuspage-rss"
        it["change_types"] = [c for c in it["change_types"] if c != "security"] or ["incident"]
        m = re.search(r"\b(Resolved|Monitoring|Identified|Investigating|Update|Postmortem|Completed|Scheduled|"
                      r"In progress|Verifying)\s+-\s", it["summary"][:160], re.I)
        if m:
            it["entities"].append(f"status:{m.group(1).lower()}")
        it["severity"] = it["severity"] if it["severity"] not in (None, "unknown") else "unknown"
    return items


# --------------------------------------------------------------------------- advisories

def parse_cisa_kev(body, ctx: dict) -> list[dict]:
    data = _json(body)
    vulns = sorted(data.get("vulnerabilities") or [], key=lambda v: v.get("dateAdded", ""), reverse=True)
    out = []
    for v in vulns[: ctx["max_items"]]:
        cve = str(v.get("cveID", "")).upper()
        ransomware = str(v.get("knownRansomwareCampaignUse", "")).lower() == "known"
        summary = f"{v.get('shortDescription', '')} Required action: {v.get('requiredAction', '')} " \
                  f"Due: {v.get('dueDate', '')}."
        out.append(_finish(
            ctx, title=f"{cve}: {v.get('vulnerabilityName', '')}", url=f"https://nvd.nist.gov/vuln/detail/{cve}",
            guid=cve, summary=summary, published=v.get("dateAdded"), vendor=v.get("vendorProject"),
            products=[v.get("product", "")], change_types=["security"], cve_ids=[cve],
            severity="critical" if ransomware else "high",
            entities=["known-exploited"] + (["ransomware"] if ransomware else []) + list(v.get("cwes") or []),
            fmt="cisa-kev", infer=False))
    return out


def osv_ranges(affected: dict) -> tuple[str, list[str]]:
    """Turn OSV ``ranges`` events into a specifier string ('>=1.0,<1.4.2 || >=2.0,<2.1.1') and fixed versions."""
    alts: list[str] = []
    fixed: list[str] = []
    for rng in affected.get("ranges") or []:
        if rng.get("type") not in ("ECOSYSTEM", "SEMVER"):
            continue
        lo = None
        for ev in rng.get("events") or []:
            if "introduced" in ev:
                lo = ev["introduced"]
            elif "fixed" in ev or "last_affected" in ev or "limit" in ev:
                if "fixed" in ev:
                    fixed.append(ev["fixed"])
                hi = ev.get("fixed") or ev.get("limit")
                parts = [] if lo in (None, "0") else [f">={lo}"]
                parts.append(f"<{hi}" if hi else f"<={ev['last_affected']}")
                alts.append(",".join(parts))
                lo = None
        if lo is not None:
            alts.append("*" if lo == "0" else f">={lo}")
    if not alts and affected.get("versions"):
        alts = [f"=={v}" for v in affected["versions"][:20]]
    return " || ".join(alts), fixed


def _osv_severity(rec: dict) -> tuple[str, float | None]:
    word = _word_severity((rec.get("database_specific") or {}).get("severity"))
    score = None
    for sev in list(rec.get("severity") or []) + [s for a in rec.get("affected") or [] for s in a.get("severity") or []]:
        if str(sev.get("type", "")).startswith("CVSS_V3"):
            score = cvss3_base_score(sev.get("score", ""))
            if score is not None:
                break
    if word:
        return word, score
    return severity_from_score(score), score


def parse_osv(body, ctx: dict) -> list[dict]:
    data = _json(body)
    recs = data.get("vulns", []) if isinstance(data, dict) and "vulns" in data else (
        data if isinstance(data, list) else [data])
    out = []
    for rec in recs:
        if rec.get("withdrawn"):
            continue
        affected = []
        for a in rec.get("affected") or []:
            pkg = a.get("package") or {}
            spec, fixed = osv_ranges(a)
            entry = {"ecosystem": pkg.get("ecosystem", ""), "name": pkg.get("name", ""), "version_range": spec or "*"}
            if fixed:
                entry["fixed"] = fixed
            affected.append(entry)
        cves = [x for x in [rec.get("id", "")] + list(rec.get("aliases") or []) if x.upper().startswith("CVE-")]
        severity, score = _osv_severity(rec)
        names = ", ".join(sorted({p["name"] for p in affected if p["name"]}))
        title = rec.get("summary") or f"{rec.get('id')} in {names or 'a package'}"
        refs = [r.get("url") for r in rec.get("references") or [] if r.get("url")]
        out.append(_finish(
            ctx, title=f"{rec.get('id')}: {title}" if rec.get("id") and rec["id"] not in title else title,
            url=f"https://osv.dev/vulnerability/{rec.get('id')}", guid=rec.get("id"),
            summary=rec.get("details") or rec.get("summary") or "", published=rec.get("published"),
            updated=rec.get("modified"), change_types=["security"], severity=severity, cvss=score,
            affected_packages=affected, cve_ids=cves, products=sorted({p["name"] for p in affected if p["name"]}),
            entities=list(rec.get("aliases") or []), links=refs[:10], fmt="osv", infer=False))
    return out


def _cpe_parts(criteria: str) -> tuple[str, str] | None:
    p = criteria.split(":")
    return (p[3], p[4]) if len(p) > 5 and p[0] == "cpe" else None


def parse_nvd(body, ctx: dict) -> list[dict]:
    data = _json(body)
    out = []
    for wrap in data.get("vulnerabilities") or []:
        cve = wrap.get("cve") or {}
        if str(cve.get("vulnStatus", "")).lower() == "rejected":
            continue
        desc = next((d.get("value", "") for d in cve.get("descriptions") or [] if d.get("lang") == "en"), "")
        score, severity = None, None
        metrics = cve.get("metrics") or {}
        for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if metrics.get(key):
                m = next((x for x in metrics[key] if x.get("type") == "Primary"), metrics[key][0])
                cd = m.get("cvssData") or {}
                score = cd.get("baseScore")
                severity = _word_severity(cd.get("baseSeverity") or m.get("baseSeverity")) or severity_from_score(score)
                break
        vendors, products, affected = [], [], []
        for conf in cve.get("configurations") or []:
            for node in conf.get("nodes") or []:
                for match in node.get("cpeMatch") or []:
                    if not match.get("vulnerable"):
                        continue
                    vp = _cpe_parts(match.get("criteria", ""))
                    if not vp:
                        continue
                    vendors.append(vp[0])
                    products.append(vp[1])
                    rng = []
                    for k, op in (("versionStartIncluding", ">="), ("versionStartExcluding", ">"),
                                  ("versionEndIncluding", "<="), ("versionEndExcluding", "<")):
                        if match.get(k):
                            rng.append(f"{op}{match[k]}")
                    ver = match["criteria"].split(":")[5]
                    if not rng and ver not in ("*", "-"):
                        rng.append(f"=={ver}")
                    affected.append({"ecosystem": "cpe", "name": f"{vp[0]}:{vp[1]}", "version_range": ",".join(rng) or "*"})
        cid = cve.get("id", "")
        out.append(_finish(
            ctx, title=f"{cid}: {shorten(desc, 140)}", url=f"https://nvd.nist.gov/vuln/detail/{cid}", guid=cid,
            summary=desc, published=cve.get("published"), updated=cve.get("lastModified"),
            change_types=["security"], severity=severity or "unknown", cvss=score, cve_ids=[cid],
            vendor=vendors[0] if vendors else ctx.get("vendor"), products=list(dict.fromkeys(products)),
            affected_packages=affected[:20], fmt="nvd", infer=False))
    return out


# --------------------------------------------------------------------------- package registries

def _vkey(v: str):
    """Loose sort key for version strings (numeric parts first; pre-releases sort before releases)."""
    nums = [int(x) for x in re.findall(r"\d+", v.split("+")[0])[:4]]
    pre = 0 if re.search(r"[a-z]", v.split("+")[0].lower().lstrip("v")) else 1
    return nums + [0] * (4 - len(nums)) + [pre]


def parse_pypi_json(body, ctx: dict) -> list[dict]:
    data = _json(body)
    info = data.get("info") or {}
    name = info.get("name") or ""
    releases = data.get("releases") or {}
    rows = []
    for ver, files in releases.items():
        times = [f.get("upload_time_iso_8601") or f.get("upload_time") for f in files or []]
        times = [t for t in times if t]
        yanked = bool(files) and all(f.get("yanked") for f in files)
        rows.append((min(times) if times else "", ver, yanked, next((f.get("yanked_reason") for f in files if
                                                                     f.get("yanked_reason")), None)))
    if not releases and info.get("version"):  # version-specific endpoint: files are under "urls"
        times = [f.get("upload_time_iso_8601") or f.get("upload_time") for f in data.get("urls") or []]
        times = [t for t in times if t]
        rows.append((min(times) if times else "", info["version"], bool(info.get("yanked")), info.get("yanked_reason")))
    rows.sort(key=lambda r: (r[0], _vkey(r[1])), reverse=True)
    out = []
    for when, ver, yanked, reason in rows[: ctx["release_limit"]]:
        ents = (["yanked"] if yanked else []) + (["prerelease"] if _PRERELEASE.search(ver) else [])
        text = info.get("summary") or ""
        if yanked:
            text = f"Yanked{': ' + reason if reason else ''}. {text}"
        out.append(_finish(
            ctx, title=f"{name} {ver}", url=f"https://pypi.org/project/{name}/{ver}/", guid=f"pypi:{name}:{ver}",
            summary=text, published=when or None, versions=[ver], change_types=["release"],
            affected_packages=[{"ecosystem": "PyPI", "name": name, "version_range": f"=={ver}"}],
            products=[name], entities=ents, fmt="pypi-json"))
    for v in data.get("vulnerabilities") or []:
        if v.get("withdrawn"):
            continue
        fixed = list(v.get("fixed_in") or [])
        spec = f"<{fixed[0]}" if len(fixed) == 1 else f"=={info.get('version')}"
        entry = {"ecosystem": "PyPI", "name": name, "version_range": spec}
        if fixed:
            entry["fixed"] = fixed
        aliases = list(v.get("aliases") or [])
        out.append(_finish(
            ctx, title=f"{v.get('id')}: {v.get('summary') or 'vulnerability in ' + name}",
            url=v.get("link") or f"https://osv.dev/vulnerability/{v.get('id')}", guid=v.get("id"),
            summary=v.get("details") or "", change_types=["security"], severity="unknown",
            affected_packages=[entry], cve_ids=[a for a in aliases if a.upper().startswith("CVE-")],
            products=[name], entities=aliases, fmt="pypi-json", infer=False))
    return out


def parse_npm(body, ctx: dict) -> list[dict]:
    data = _json(body)
    name = data.get("name", "")
    times = {k: v for k, v in (data.get("time") or {}).items() if k not in ("created", "modified")}
    latest = (data.get("dist-tags") or {}).get("latest")
    versions = data.get("versions") or {}
    order = sorted(times.items(), key=lambda kv: kv[1], reverse=True) or [(v, "") for v in versions]
    out = []
    for ver, when in order[: ctx["release_limit"]]:
        meta = versions.get(ver)
        if meta is None and ver not in versions and times:
            continue  # unpublished version
        meta = meta or {}
        dep = meta.get("deprecated")
        ents = (["latest"] if ver == latest else []) + (["deprecated"] if dep else []) + \
               (["prerelease"] if "-" in ver else [])
        text = f"Deprecated: {dep}. " if dep else ""
        text += meta.get("description") or data.get("description") or ""
        ctypes = ["release"] + (["deprecation"] if dep else [])
        out.append(_finish(
            ctx, title=f"{name} {ver}", url=f"https://www.npmjs.com/package/{name}/v/{ver}", guid=f"npm:{name}:{ver}",
            summary=text, published=when or None, versions=[ver], change_types=ctypes,
            affected_packages=[{"ecosystem": "npm", "name": name, "version_range": f"=={ver}"}],
            products=[name], entities=ents, fmt="npm"))
    return out


def _eol_product(url: str) -> str:
    m = re.search(r"endoflife\.date/api/(?:v1/products/)?([^/?#]+?)(?:\.json)?(?:/|$|\?)", url or "")
    return m.group(1) if m else ""


def parse_endoflife(body, ctx: dict) -> list[dict]:
    data = _json(body)
    now = ctx["now"]
    product = _eol_product(ctx["url"])
    label = product
    cycles = []
    if isinstance(data, dict) and isinstance(data.get("result"), dict):
        res = data["result"]
        product, label = res.get("name") or product, res.get("label") or label
        for r in res.get("releases") or []:
            latest = r.get("latest") or {}
            cycles.append({"cycle": r.get("name"), "label": r.get("label") or r.get("name"), "eol": r.get("eolFrom"),
                           "is_eol": r.get("isEol"), "latest": latest.get("name"), "latest_date": latest.get("date"),
                           "link": latest.get("link"), "maintained": r.get("isMaintained")})
    elif isinstance(data, list):
        for r in data:
            eol = r.get("eol")
            cycles.append({"cycle": r.get("cycle"), "label": r.get("cycle"), "eol": eol if isinstance(eol, str) else None,
                           "is_eol": eol if isinstance(eol, bool) else None, "latest": r.get("latest"),
                           "latest_date": r.get("latestReleaseDate"), "link": r.get("link"), "maintained": None})
    page = f"https://endoflife.date/{product}"
    out = []
    for c in cycles:
        eol_dt = _dt(c["eol"]) if c["eol"] else None
        if eol_dt and now - timedelta(days=ctx["eol_past_days"]) <= eol_dt <= now + timedelta(days=ctx["eol_ahead_days"]):
            when = "reached" if eol_dt <= now else "reaches"
            out.append(_finish(
                ctx, title=f"{label} {c['label']} {when} end of life on {eol_dt.date().isoformat()}",
                url=f"{page}#{c['cycle']}" if c["cycle"] else page, guid=f"eol:{product}:{c['cycle']}",
                summary=f"Release cycle {c['label']} of {label}: end of life {eol_dt.date().isoformat()}. "
                        f"Latest version in this cycle: {c['latest'] or 'unknown'}.",
                published=c["eol"] if eol_dt <= now else None, versions=[str(c["cycle"])],
                change_types=["deprecation"], products=[product], entities=["end-of-life"], fmt="endoflife",
                infer=False))
        latest_dt = _dt(c["latest_date"]) if c["latest_date"] else None
        if c["latest"] and latest_dt and latest_dt >= now - timedelta(days=ctx["release_days"]) and not c["is_eol"]:
            out.append(_finish(
                ctx, title=f"{label} {c['latest']}", url=c["link"] or page, guid=f"eol-latest:{product}:{c['latest']}",
                summary=f"Latest patch release in the {c['label']} cycle of {label}.", published=c["latest_date"],
                versions=[str(c["latest"])], change_types=["release"], products=[product], fmt="endoflife"))
    return out


def parse_goproxy_latest(body, ctx: dict) -> list[dict]:
    data = _json(body)
    origin = data.get("Origin") or {}
    module = _go_module(ctx["url"]) or re.sub(r"^https?://|\.git$", "", origin.get("URL") or "") or "unknown-module"
    ver = data.get("Version", "")
    return [_finish(ctx, title=f"{module} {ver}", url=f"https://pkg.go.dev/{module}@{ver}", guid=f"go:{module}:{ver}",
                    summary=f"Latest version of Go module {module}" + (f" from {origin.get('URL')}" if origin.get("URL") else ""),
                    published=data.get("Time"), versions=[ver.lstrip("v")], change_types=["release"],
                    affected_packages=[{"ecosystem": "Go", "name": module, "version_range": f"=={ver.lstrip('v')}"}],
                    products=[module], fmt="goproxy-latest")]


def parse_goproxy_list(body, ctx: dict) -> list[dict]:
    text = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body)
    module = _go_module(ctx["url"])
    vers = sorted({v.strip() for v in text.splitlines() if v.strip()}, key=_vkey, reverse=True)
    return [_finish(ctx, title=f"{module} {v}", url=f"https://pkg.go.dev/{module}@{v}", guid=f"go:{module}:{v}",
                    summary=f"Version {v} of Go module {module} is on the module proxy.", versions=[v.lstrip("v")],
                    change_types=["release"], products=[module],
                    affected_packages=[{"ecosystem": "Go", "name": module, "version_range": f"=={v.lstrip('v')}"}],
                    fmt="goproxy-list") for v in vers[: ctx["release_limit"]]]


def _go_module(url: str) -> str:
    m = re.search(r"proxy\.golang\.org/(.+?)/@(?:latest|v/list)", url or "")
    if not m:
        return ""
    return re.sub(r"!([a-z])", lambda x: x.group(1).upper(), unquote(m.group(1)))


def parse_crates_index(body, ctx: dict) -> list[dict]:
    text = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body)
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    rows.sort(key=lambda r: (r.get("pubtime") or "", _vkey(r.get("vers", "0"))), reverse=True)
    out = []
    for r in rows[: ctx["release_limit"]]:
        name, ver = r.get("name", ""), r.get("vers", "")
        ents = (["yanked"] if r.get("yanked") else []) + (["prerelease"] if "-" in ver else [])
        out.append(_finish(ctx, title=f"{name} {ver}", url=f"https://crates.io/crates/{name}/{ver}",
                           guid=f"crate:{name}:{ver}",
                           summary=("Yanked. " if r.get("yanked") else "") + f"Version {ver} of crate {name}"
                           + (f" (rust-version {r['rust_version']})" if r.get("rust_version") else "") + ".",
                           published=r.get("pubtime"), versions=[ver], change_types=["release"], products=[name],
                           affected_packages=[{"ecosystem": "crates.io", "name": name, "version_range": f"=={ver}"}],
                           entities=ents, fmt="crates-index"))
    return out


# --------------------------------------------------------------------------- research

def parse_arxiv(body, ctx: dict) -> list[dict]:
    ctx = dict(ctx, change_types=list(dict.fromkeys(["research", *ctx["change_types"]])))
    root = _xml_root(body)
    out = []
    for entry in _children(root, "entry"):
        abs_url = ""
        for link in _children(entry, "link"):
            if link.get("rel", "alternate") == "alternate" and link.get("type", "text/html") == "text/html":
                abs_url = link.get("href", "")
        abs_url = abs_url or _child_text(entry, "id")
        arxiv_id = re.sub(r"v\d+$", "", abs_url.rsplit("/abs/", 1)[-1])
        cats = [c.get("term", "") for c in _children(entry, "category")]
        authors = [_child_text(a, "name") for a in _children(entry, "author")]
        out.append(_finish(ctx, title=_child_text(entry, "title"), url=abs_url, guid=f"arxiv:{arxiv_id}",
                           summary=_child_text(entry, "summary"), published=_child_text(entry, "published"),
                           updated=_child_text(entry, "updated"), authors=authors,
                           entities=[f"arxiv:{arxiv_id}", *cats], versions=[], fmt="arxiv", infer=False))
    return out


def parse_hf_papers(body, ctx: dict) -> list[dict]:
    data = _json(body)
    rows = data if isinstance(data, list) else data.get("papers", [])
    out = []
    for row in rows[: ctx["max_items"]]:
        paper = row.get("paper") or {}
        pid = paper.get("id") or row.get("id") or ""
        title = row.get("title") or paper.get("title") or pid
        summary = row.get("ai_summary") or paper.get("ai_summary") or paper.get("summary") or row.get("summary") or ""
        authors = [a.get("name", "") for a in paper.get("authors") or [] if isinstance(a, dict)]
        links = [x for x in (row.get("githubRepo") or paper.get("githubRepo"), row.get("projectPage") or
                             paper.get("projectPage")) if x]
        out.append(_finish(ctx, title=title, url=f"https://huggingface.co/papers/{pid}", guid=f"hf-paper:{pid}",
                           summary=summary, published=row.get("publishedAt") or paper.get("publishedAt"),
                           change_types=["research"], authors=authors, versions=[],
                           entities=[f"arxiv:{pid}", *(row.get("ai_keywords") or paper.get("ai_keywords") or [])],
                           links=links, fmt="hf-papers", infer=False))
    return out


# --------------------------------------------------------------------------- sitemap / iCalendar

def parse_sitemap(body, ctx: dict) -> list[dict]:
    root = _xml_root(body)
    rows = []
    for u in _children(root, "url"):
        loc, lastmod = _child_text(u, "loc"), _child_text(u, "lastmod")
        if loc:
            rows.append((parse_date(lastmod) or "", loc))
    rows.sort(reverse=True)
    out = []
    for lastmod, loc in rows[: ctx["max_items"]]:
        slug = urlsplit(loc).path.rstrip("/").rsplit("/", 1)[-1] or urlsplit(loc).netloc
        title = re.sub(r"[-_]+", " ", re.sub(r"\.\w+$", "", unquote(slug))).strip().capitalize()
        out.append(_finish(ctx, title=title, url=loc, guid=f"{loc}#{lastmod}", summary=f"Page updated {lastmod or 'recently'}.",
                           published=lastmod or None, fmt="sitemap"))
    return out


def parse_ical(body, ctx: dict) -> list[dict]:
    text = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body)
    text = re.sub(r"\r?\n[ \t]", "", text)  # unfold
    out = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        fields: dict[str, str] = {}
        for line in block.strip().splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields.setdefault(key.split(";", 1)[0].upper(), value.replace("\\n", " ").replace("\\,", ",").strip())
        start = fields.get("DTSTART", "")
        out.append(_finish(ctx, title=fields.get("SUMMARY", "Event"), url=fields.get("URL") or ctx["url"],
                           guid=fields.get("UID") or f"{fields.get('SUMMARY')}@{start}",
                           summary=(f"Starts {parse_date(start) or start}. " + fields.get("DESCRIPTION", "")),
                           published=start, change_types=["event"], fmt="ical"))
    return out


# --------------------------------------------------------------------------- dispatch

def _json(body):
    try:
        return json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ParseError(f"JSON does not parse: {exc}") from exc


def _finish(ctx: dict, *, fmt: str, change_types=None, vendor=None, products=None, infer: bool = True, **kw) -> dict:
    ctypes = list(dict.fromkeys([*(change_types or []), *ctx["change_types"]]))
    prods = list(dict.fromkeys([*(products or []), *ctx["products"]]))
    return make_item(source_id=ctx["source_id"], collection=ctx["collection"], vendor=vendor or ctx.get("vendor"),
                     products=prods, change_types=ctypes, source_format=fmt, fetched=ctx.get("fetched"),
                     infer=infer, **kw)


PARSERS = {
    "rss": parse_rss, "atom": parse_atom, "json-feed": parse_json_feed, "github-releases": parse_github_releases,
    "statuspage-json": parse_statuspage_json, "statuspage-rss": parse_statuspage_rss, "cisa-kev": parse_cisa_kev,
    "osv": parse_osv, "nvd": parse_nvd, "pypi-json": parse_pypi_json, "npm": parse_npm, "endoflife": parse_endoflife,
    "arxiv": parse_arxiv, "hf-papers": parse_hf_papers, "goproxy-latest": parse_goproxy_latest,
    "goproxy-list": parse_goproxy_list, "crates-index": parse_crates_index, "sitemap": parse_sitemap,
    "ical": parse_ical,
}
# feed_format values used in baltor feed collections -> parser (None = detect from URL/body)
COLLECTION_FORMATS = {"rss": "rss", "atom": "atom", "json-feed": "json-feed", "github-releases": "github-releases",
                      "statuspage": None, "json-api": None, "sitemap": "sitemap", "ical": "ical"}


def parse(body: bytes | str, *, fmt: str | None = None, url: str = "", source_id: str = "", collection: str = "",
          content_type: str = "", vendor: str | None = None, products=None, change_types=None, now=None,
          fetched: str | None = None, max_items: int = 200, release_limit: int = 10, eol_past_days: int = 30,
          eol_ahead_days: int = 180, release_days: int = 120) -> list[dict]:
    """Parse ``body`` into agent_feed_item dicts (newest first where the source has dates)."""
    if fmt in COLLECTION_FORMATS:
        fmt = COLLECTION_FORMATS[fmt]
    if fmt == "statuspage" or fmt is None:
        fmt = detect_format(body, url, content_type)
    if fmt == "atom" and _url_format(url) == "github-releases":
        fmt = "github-releases"
    if fmt not in PARSERS:
        raise ParseError(f"unknown format {fmt!r}; known: {', '.join(FORMATS)}")
    now_dt = _dt(now) if isinstance(now, str) else (now or datetime.now(UTC))
    ctx = {"url": url, "source_id": source_id or (urlsplit(url).netloc if url else "unknown"),
           "collection": collection, "vendor": vendor, "products": list(products or []),
           "change_types": list(change_types or []), "now": now_dt, "fetched": fetched, "max_items": max_items,
           "release_limit": release_limit, "eol_past_days": eol_past_days, "eol_ahead_days": eol_ahead_days,
           "release_days": release_days}
    items = PARSERS[fmt](body, ctx)
    _enrich_from_url(items, url)
    items.sort(key=lambda i: i.get("published") or i.get("updated") or "", reverse=True)
    return items[:max_items]


def _enrich_from_url(items: list[dict], url: str) -> None:
    m = re.search(r"pypi\.org/rss/project/([^/]+)/releases\.xml", url or "")
    if not m:
        return
    name = m.group(1)
    for it in items:
        ver = it["title"].strip()
        it["title"] = f"{name} {ver}"
        it["versions"] = [ver]
        if "release" not in it["change_types"]:
            it["change_types"].insert(0, "release")
        if name not in it["products"]:
            it["products"].insert(0, name)
        it["affected_packages"] = [{"ecosystem": "PyPI", "name": name, "version_range": f"=={ver}"}]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Parse a saved feed/API response into agent_feed_item JSON.")
    ap.add_argument("file")
    ap.add_argument("--url", default="")
    ap.add_argument("--format", dest="fmt", choices=sorted(PARSERS), default=None)
    ap.add_argument("--source-id", default="")
    ap.add_argument("--limit", type=int, default=50)
    a = ap.parse_args(argv)
    with open(a.file, "rb") as fh:
        body = fh.read()
    items = parse(body, fmt=a.fmt, url=a.url, source_id=a.source_id, max_items=a.limit)
    json.dump(items, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
