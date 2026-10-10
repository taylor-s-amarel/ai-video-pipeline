"""Watch web pages that have no feed (policy pages, programme pages) for meaningful text changes.

Standard library only. Extracts readable text (drops scripts, styles, navigation, headers and footers),
fingerprints it, and on change returns a short sentence-level diff so an agent can say *what* changed
and link the page. State lives in a small JSON file. Network access is limited to ``check``, which takes
an injectable ``fetcher`` so tests run offline.

    python page_change_watcher.py https://support.google.com/youtube/answer/1311392 --state pages.json

Polite by default: one request per page per run, descriptive User-Agent, conditional request with the
stored ETag/Last-Modified, and no retries. Check policy pages at most daily.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

__all__ = ["extract_text", "fingerprint", "diff_summary", "check", "http_fetcher"]

DEFAULT_USER_AGENT = "baltor-page-watch/1.0 (+https://github.com/taylor-s-amarel/ai-video-pipeline)"
SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "svg", "form", "aside", "template"}
BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "br", "section", "article", "td", "dd", "dt"}


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        elif tag in BLOCK_TAGS:
            self.chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        elif tag in BLOCK_TAGS:
            self.chunks.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.chunks.append(data)


def extract_text(html: str, selector_text: str | None = None) -> str:
    """Readable text of a page, one block per line. If ``selector_text`` is given, keep only the part of
    the page from the first line containing it (useful to skip cookie banners and menus)."""
    parser = _Text()
    parser.feed(html)
    parser.close()
    lines = [re.sub(r"\s+", " ", l).strip() for l in "".join(parser.chunks).split("\n")]
    lines = [l for l in lines if l]
    if selector_text:
        for i, l in enumerate(lines):
            if selector_text.lower() in l.lower():
                lines = lines[i:]
                break
    return "\n".join(lines)


def fingerprint(text: str) -> str:
    """SHA-256 of the text with digits-only lines and whitespace differences ignored."""
    norm = "\n".join(l for l in (re.sub(r"\s+", " ", x).strip().lower() for x in text.splitlines())
                     if l and not re.fullmatch(r"[\d\s:/.,-]+", l))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _sentences(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]
    return out


def diff_summary(old: str, new: str, max_items: int = 12) -> dict:
    """Sentences added and removed between two texts (order-preserving, capped)."""
    a, b = _sentences(old), _sentences(new)
    added, removed = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op in ("delete", "replace"):
            removed += a[i1:i2]
        if op in ("insert", "replace"):
            added += b[j1:j2]
    return {"added": added[:max_items], "removed": removed[:max_items],
            "added_total": len(added), "removed_total": len(removed)}


def http_fetcher(url: str, etag: str | None, last_modified: str | None,
                 user_agent: str = DEFAULT_USER_AGENT, timeout: float = 20.0, max_bytes: int = 3_000_000) -> dict:
    if not url.startswith(("https://", "http://")):
        raise ValueError("only http(s) URLs are fetched")
    headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as resp:
            body = resp.read(max_bytes)
            charset = resp.headers.get_content_charset() or "utf-8"
            return {"status": resp.status, "html": body.decode(charset, errors="replace"),
                    "etag": resp.headers.get("ETag"), "last_modified": resp.headers.get("Last-Modified")}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "html": None, "etag": etag, "last_modified": last_modified}


def check(url: str, state: dict, fetcher: Callable[..., dict] = http_fetcher, now: datetime | None = None,
          selector_text: str | None = None) -> dict:
    """Fetch ``url`` once and compare with ``state[url]``. Mutates ``state``; returns a result record."""
    now_s = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    prev = state.get(url, {})
    res = fetcher(url, prev.get("etag"), prev.get("last_modified"))
    record = {"url": url, "checked": now_s, "status": res["status"], "changed": False, "first_check": not prev}
    if res["status"] == 304:
        state[url] = dict(prev, last_checked=now_s)
        return record
    if res["status"] != 200 or res.get("html") is None:
        record["error"] = f"HTTP {res['status']}"
        state[url] = dict(prev, last_checked=now_s, last_error=record["error"])
        return record
    text = extract_text(res["html"], selector_text)
    fp = fingerprint(text)
    if prev and prev.get("fingerprint") != fp:
        record["changed"] = True
        record["diff"] = diff_summary(prev.get("text", ""), text)
    state[url] = {"fingerprint": fp, "text": text[:200_000], "etag": res.get("etag"),
                  "last_modified": res.get("last_modified"), "last_checked": now_s,
                  "last_changed": now_s if (record["changed"] or not prev) else prev.get("last_changed")}
    return record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Report meaningful text changes on pages without feeds.")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--state", default="page-watch.json")
    ap.add_argument("--selector-text", help="start the comparison at the first line containing this text")
    a = ap.parse_args(argv)
    path = Path(a.state)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    results = [check(u, state, selector_text=a.selector_text) for u in a.urls]
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 1 if any("error" in r for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
