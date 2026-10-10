"""Turn Baltor feed collections (feeds/<id>.json, spec baltor.feed-collection/v1) into OPML 2.0.

Standard library only. Any feed reader (and the ``rss_atom_jsonfeed_reader`` module) can import the
result. Items whose URL is not a feed (policy pages, newsletters without a confirmed feed) are left
out by default, or kept as ``type="link"`` outlines with ``--include-pages``.

    python feed_collection_opml.py baltor/feeds/community-*.json -o community.opml
    python feed_collection_opml.py baltor/feeds/community-releases-agents-ai.json --group-by tags
    python feed_collection_opml.py --list community.opml       # read an OPML back as JSON
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Iterable

__all__ = ["is_feed_url", "html_url_for", "collections_to_opml", "collection_to_opml", "parse_opml",
           "load_collection"]

FEED_PATTERNS = [
    re.compile(r"\.(rss|atom|rdf)(\?|$)", re.I),
    re.compile(r"/(rss|atom|feed|feeds)(/|\.xml|\.json|\.php)?(\?|$)", re.I),
    re.compile(r"(rss|atom|feed|index)\.xml(\?|$)", re.I),
    re.compile(r"[?&](format|feedformat)=(rss|atom)\b", re.I),
    re.compile(r"[?&]action=featuredfeed\b", re.I),
    re.compile(r"/feeds/videos\.xml\?channel_id=", re.I),
    re.compile(r"^https?://hnrss\.org/", re.I),
    re.compile(r"^https?://rss\.arxiv\.org/(rss|atom)/", re.I),
    re.compile(r"/(rss|feed)_[a-z_]+\.xml(\?|$)", re.I),
    re.compile(r"/(trending/rss)(\?|$)", re.I),
    re.compile(r"/smallweb/feed$", re.I),
    re.compile(r"(?<!sitemap)\.xml(\?|$)", re.I),
]
NOT_FEED_PATTERNS = [
    re.compile(r"/api/rest_v\d+/", re.I),  # JSON APIs such as Wikimedia REST are not feeds
    re.compile(r"sitemap[^/]*\.xml", re.I),
]


def is_feed_url(url: str) -> bool:
    """Heuristic: does this URL point at a feed document rather than a web page?"""
    url = url or ""
    if any(p.search(url) for p in NOT_FEED_PATTERNS):
        return False
    return any(p.search(url) for p in FEED_PATTERNS)


def html_url_for(feed_url: str) -> str | None:
    """Best-effort human page for well-known feed URL shapes (Reddit, GitHub, YouTube, arXiv, Discourse)."""
    u = urllib.parse.urlsplit(feed_url)
    host, path = (u.hostname or ""), u.path
    if host.endswith("reddit.com"):
        m = re.match(r"(/r/[^/]+)/", path)
        return f"https://www.reddit.com{m.group(1)}/" if m else None
    if host == "github.com":
        m = re.match(r"(/[^/]+/[^/]+)/(releases|tags|commits)", path)
        if m:
            return f"https://github.com{m.group(1)}/{'releases' if m.group(2) == 'releases' else m.group(2)}"
        return None
    if host.endswith("youtube.com") and path == "/feeds/videos.xml":
        cid = urllib.parse.parse_qs(u.query).get("channel_id", [""])[0]
        return f"https://www.youtube.com/channel/{cid}" if cid else None
    if host == "rss.arxiv.org":
        cat = path.rsplit("/", 1)[-1]
        return f"https://arxiv.org/list/{cat}/new" if cat else None
    if path.endswith("/latest.rss"):
        return urllib.parse.urlunsplit((u.scheme, u.netloc, path[: -len(".rss")], "", ""))
    return None


def load_collection(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("spec") != "baltor.feed-collection/v1" or not isinstance(data.get("items"), list):
        raise ValueError(f"{path}: not a baltor.feed-collection/v1 document")
    return data


def _outline_attrs(item: dict, as_feed: bool) -> dict:
    attrs = {"text": item.get("title") or item.get("url", ""), "title": item.get("title", "")}
    if as_feed:
        attrs["type"] = "rss"
        attrs["xmlUrl"] = item["url"]
        page = html_url_for(item["url"])
        if page:
            attrs["htmlUrl"] = page
    else:
        attrs["type"] = "link"
        attrs["url"] = item["url"]
    if item.get("summary"):
        attrs["description"] = item["summary"]
    if item.get("tags"):
        attrs["category"] = ",".join(item["tags"])
    if item.get("verification"):
        attrs["baltorVerification"] = item["verification"]
    return attrs


def _add_items(parent: ET.Element, items: Iterable[dict], include_pages: bool, group_by: str | None) -> int:
    count = 0
    groups: dict[str, ET.Element] = {}
    for item in items:
        as_feed = is_feed_url(item.get("url", ""))
        if not as_feed and not include_pages:
            continue
        target = parent
        if group_by in {"kind", "tags"}:
            key = item.get("kind", "other") if group_by == "kind" else ((item.get("tags") or ["untagged"])[0])
            if key not in groups:
                groups[key] = ET.SubElement(parent, "outline", {"text": key, "title": key})
            target = groups[key]
        ET.SubElement(target, "outline", _outline_attrs(item, as_feed))
        count += 1
    return count


def collections_to_opml(collections: list[dict], title: str | None = None, include_pages: bool = False,
                        group_by: str | None = None, now: datetime | None = None) -> str:
    """One OPML document with a top-level outline per collection. Returns the XML text."""
    now = now or datetime.now(timezone.utc)
    root = ET.Element("opml", {"version": "2.0"})
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "title").text = title or (collections[0]["title"] if len(collections) == 1 else
                                                 "Baltor agent feeds")
    ET.SubElement(head, "dateCreated").text = format_datetime(now.astimezone(timezone.utc), usegmt=True)
    ET.SubElement(head, "docs").text = "http://opml.org/spec2.opml"
    body = ET.SubElement(root, "body")
    for col in collections:
        folder = ET.SubElement(body, "outline", {"text": col.get("title", col.get("id", "")),
                                                 "title": col.get("title", ""), "baltorCollection": col.get("id", "")})
        _add_items(folder, col.get("items", []), include_pages, group_by)
        if len(folder) == 0:
            body.remove(folder)
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def collection_to_opml(collection: dict, **kwargs) -> str:
    return collections_to_opml([collection], **kwargs)


def parse_opml(text: str) -> list[dict]:
    """Read OPML back into [{"title", "xml_url", "html_url", "folder", "category"}] (feeds only)."""
    if "<!entity" in text[:65536].lower():
        raise ValueError("refusing OPML with entity declarations")
    root = ET.fromstring(text)
    out: list[dict] = []

    def walk(node: ET.Element, folder: list[str]) -> None:
        for child in node.findall("outline"):
            if child.get("xmlUrl"):
                out.append({"title": child.get("title") or child.get("text", ""), "xml_url": child.get("xmlUrl"),
                            "html_url": child.get("htmlUrl"), "folder": "/".join(folder),
                            "category": [c for c in (child.get("category") or "").split(",") if c]})
            else:
                walk(child, folder + [child.get("text", "")])

    body = root.find("body")
    if body is not None:
        walk(body, [])
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("collections", nargs="*", help="feeds/<id>.json files")
    ap.add_argument("-o", "--output", help="write OPML here (default: stdout)")
    ap.add_argument("--title")
    ap.add_argument("--include-pages", action="store_true", help="keep non-feed items as link outlines")
    ap.add_argument("--group-by", choices=["kind", "tags"], help="sub-folders inside each collection")
    ap.add_argument("--list", metavar="OPML", help="print the feeds in an OPML file as JSON")
    a = ap.parse_args(argv)
    if a.list:
        print(json.dumps(parse_opml(Path(a.list).read_text(encoding="utf-8")), indent=2))
        return 0
    if not a.collections:
        ap.error("give at least one collection file")
    cols = [load_collection(p) for p in a.collections]
    text = collections_to_opml(cols, a.title, a.include_pages, a.group_by)
    if a.output:
        Path(a.output).write_text(text, encoding="utf-8")
        print(f"wrote {sum(1 for _ in parse_opml(text))} feeds to {a.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
