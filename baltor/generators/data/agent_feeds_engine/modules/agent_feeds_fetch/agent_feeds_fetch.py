#!/usr/bin/env python3
"""Polite HTTP fetcher for Agent Feeds sources (standard library only).

What "polite" means here:

* conditional requests: ``If-None-Match`` / ``If-Modified-Since`` from the stored source state, so an
  unchanged feed costs the publisher a 304 and no body;
* one request at a time per host with a minimum interval (default 2 s; 6 s for the NVD API, as NVD
  asks), raised to the host's robots.txt ``Crawl-delay`` when that is larger;
* exponential backoff after failures (15 min, 30 min, 1 h ... capped at 48 h) and ``Retry-After`` honoured;
* HTTP 410 marks the source ``gone`` so it is not polled again until a person re-enables it;
* robots.txt is checked for HTML sources (``check_robots=True``) following RFC 9309: a 4xx robots.txt
  means no restrictions, a 5xx or network failure means "do not fetch";
* a descriptive User-Agent with a contact URL (override with ``AGENT_FEEDS_USER_AGENT``);
* size limits on the raw and the decompressed body (default 5 MB) and http/https only.

Optional credentials are read from environment variables named here, never stored:
``NVD_API_KEY`` (sent as the ``apiKey`` header to services.nvd.nist.gov) and ``GITHUB_TOKEN``
(sent as a bearer token to api.github.com only).

Usage::

    from agent_feeds_fetch import PoliteFetcher
    fetcher = PoliteFetcher()
    result = fetcher.fetch("https://github.com/astral-sh/uv/releases.atom", state)
    if result.outcome == "ok":
        parse(result.body, ...)
    save(result.state)            # agent_feed_source_state

Tests and dry runs use :class:`ReplayTransport` instead of the network.
"""

from __future__ import annotations

import email.utils
import os
import time
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Protocol
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

__all__ = ["Response", "Transport", "UrllibTransport", "ReplayTransport", "PoliteFetcher", "FetchResult",
           "DEFAULT_USER_AGENT", "new_state", "is_due"]

DEFAULT_USER_AGENT = "BaltorAgentFeeds/1.0 (+https://github.com/taylor-s-amarel/ai-video-pipeline)"
UA_TOKEN = "BaltorAgentFeeds"
DEFAULT_ACCEPT = ("application/atom+xml, application/rss+xml, application/feed+json, application/json;q=0.9, "
                  "application/xml;q=0.8, text/xml;q=0.8, text/html;q=0.7, */*;q=0.5")
HOST_MIN_INTERVAL_S = {"services.nvd.nist.gov": 6.0, "github.com": 2.0, "api.github.com": 1.0, "export.arxiv.org": 3.0}
AUTH_FROM_ENV = {  # host -> (header, prefix, ENV_VAR)
    "services.nvd.nist.gov": ("apiKey", "", "NVD_API_KEY"),
    "api.github.com": ("Authorization", "Bearer ", "GITHUB_TOKEN"),
}


@dataclass
class Response:
    status: int
    headers: dict = field(default_factory=dict)
    body: bytes = b""
    url: str = ""
    error: str | None = None

    def header(self, name: str, default: str | None = None) -> str | None:
        return {k.lower(): v for k, v in self.headers.items()}.get(name.lower(), default)


class Transport(Protocol):
    def request(self, method: str, url: str, headers: dict, timeout: float, max_bytes: int) -> Response: ...


class UrllibTransport:
    """Real network transport. Redirects are followed by urllib (at most 10)."""

    def request(self, method: str, url: str, headers: dict, timeout: float, max_bytes: int) -> Response:
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - scheme checked by caller
                length = r.headers.get("Content-Length")
                if length and length.isdigit() and int(length) > max_bytes:
                    return Response(r.status, dict(r.headers.items()), b"", r.url, error="too-large")
                return Response(r.status, dict(r.headers.items()), r.read(max_bytes + 1), r.url)
        except urllib.error.HTTPError as exc:  # includes 304 Not Modified
            body = b""
            try:
                body = exc.read(65536) if exc.fp else b""
            except OSError:
                pass
            return Response(exc.code, dict((exc.headers or {}).items()), body, url)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            return Response(0, {}, b"", url, error=f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}")


class ReplayTransport:
    """Serves canned responses by URL (a Response, a list consumed in order, or a callable) and records calls."""

    def __init__(self, responses: dict | None = None, default: Response | None = None):
        self.responses = dict(responses or {})
        self.default = default or Response(404, {}, b"not found")
        self.calls: list[tuple[str, str, dict]] = []

    def request(self, method: str, url: str, headers: dict, timeout: float, max_bytes: int) -> Response:
        self.calls.append((method, url, dict(headers)))
        r = self.responses.get(url, self.default)
        if callable(r):
            r = r(method, url, headers)
        if isinstance(r, list):
            r = r.pop(0) if len(r) > 1 else r[0]
        body = r.body[: max_bytes + 1]
        return Response(r.status, dict(r.headers), body, url, r.error)


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def new_state(source_id: str, url: str, **extra) -> dict:
    """A fresh agent_feed_source_state."""
    state = {"source_id": source_id, "url": url, "cursor": None, "etag": None, "last_modified": None,
             "last_attempt": None, "last_success": None, "last_status": None, "failures": 0, "backoff_until": None,
             "last_error": None, "items_seen": 0, "gone": False, "robots_blocked": False}
    state.update({k: v for k, v in extra.items() if v is not None})
    return state


def is_due(state: dict | None, poll_interval_h: float, now: float) -> tuple[bool, str]:
    """Whether a source should be polled now, with the reason."""
    if not state:
        return True, "never polled"
    if state.get("gone"):
        return False, "marked gone (HTTP 410)"
    until = _ts(state.get("backoff_until"))
    if until and until > now:
        return False, f"backing off until {state['backoff_until']}"
    last = _ts(state.get("last_success")) or _ts(state.get("last_attempt"))
    if last is None:
        return True, "no successful poll yet"
    due_at = last + poll_interval_h * 3600
    if due_at <= now:
        return True, f"interval {poll_interval_h:g} h elapsed"
    return False, f"next poll after {_iso(due_at)}"


@dataclass
class FetchResult:
    url: str
    outcome: str  # ok | not-modified | error | backoff | gone | robots-blocked | too-large | invalid-url
    status: int | None
    state: dict
    body: bytes = b""
    content_type: str = ""
    error: str | None = None

    @property
    def changed(self) -> bool:
        return self.outcome == "ok"


class PoliteFetcher:
    def __init__(self, transport: Transport | None = None, *, user_agent: str | None = None,
                 min_interval_s: float = 2.0, timeout_s: float = 30.0, max_bytes: int = 5_000_000,
                 backoff_base_s: float = 900.0, backoff_max_s: float = 172_800.0, robots_ttl_s: float = 86_400.0,
                 clock: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep,
                 env: dict | None = None):
        self.transport = transport or UrllibTransport()
        self.env = os.environ if env is None else env
        self.user_agent = user_agent or self.env.get("AGENT_FEEDS_USER_AGENT") or DEFAULT_USER_AGENT
        self.min_interval_s = min_interval_s
        self.timeout_s = timeout_s
        self.max_bytes = max_bytes
        self.backoff_base_s = backoff_base_s
        self.backoff_max_s = backoff_max_s
        self.robots_ttl_s = robots_ttl_s
        self.clock = clock
        self.sleep = sleep
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, tuple[float, RobotFileParser | None, bool]] = {}
        self.requests_made = 0

    # ------------------------------------------------------------------ politeness
    def _host_interval(self, host: str) -> float:
        interval = max(self.min_interval_s, HOST_MIN_INTERVAL_S.get(host, 0.0))
        cached = self._robots.get(host)
        if cached and cached[1] is not None:
            delay = cached[1].crawl_delay(self.user_agent)
            if delay:
                interval = max(interval, float(delay))
        return interval

    def _wait_turn(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            wait = last + self._host_interval(host) - self.clock()
            if wait > 0:
                self.sleep(wait)
        self._last_request[host] = self.clock()

    def _send(self, url: str, headers: dict) -> Response:
        host = urlsplit(url).hostname or ""
        self._wait_turn(host)
        self.requests_made += 1
        return self.transport.request("GET", url, headers, self.timeout_s, self.max_bytes)

    def robots_allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        host = parts.hostname or ""
        now = self.clock()
        cached = self._robots.get(host)
        if not cached or cached[0] < now:
            resp = self._send(f"{parts.scheme}://{parts.netloc}/robots.txt", {"User-Agent": self.user_agent})
            if 200 <= resp.status < 300:
                rp = RobotFileParser()
                rp.parse(resp.body[:512_000].decode("utf-8", "replace").splitlines())
                cached = (now + self.robots_ttl_s, rp, True)
            elif 400 <= resp.status < 500:  # RFC 9309 2.3.1.3: unavailable -> no restrictions
                cached = (now + self.robots_ttl_s, None, True)
            else:  # 5xx or network failure: unreachable -> assume complete disallow, retry sooner
                cached = (now + 3600, None, False)
            self._robots[host] = cached
        _, rp, allowed = cached
        if rp is None:
            return allowed
        return rp.can_fetch(self.user_agent, url)

    # ------------------------------------------------------------------ main
    def _headers(self, url: str, state: dict, accept: str | None) -> dict:
        headers = {"User-Agent": self.user_agent, "Accept": accept or DEFAULT_ACCEPT, "Accept-Encoding": "gzip"}
        if state.get("etag"):
            headers["If-None-Match"] = state["etag"]
        if state.get("last_modified"):
            headers["If-Modified-Since"] = state["last_modified"]
        host = urlsplit(url).hostname or ""
        if host in AUTH_FROM_ENV:
            header, prefix, var = AUTH_FROM_ENV[host]
            if self.env.get(var):
                headers[header] = prefix + self.env[var]
        return headers

    def _decode(self, resp: Response) -> bytes:
        body = resp.body
        if (resp.header("content-encoding") or "").lower() == "gzip" or body[:2] == b"\x1f\x8b":
            d = zlib.decompressobj(16 + zlib.MAX_WBITS)
            out = d.decompress(body, self.max_bytes + 1)
            if len(out) > self.max_bytes or d.unconsumed_tail:
                raise OverflowError("decompressed body exceeds the size limit")
            return out
        return body

    def _retry_after(self, resp: Response, now: float) -> float:
        value = (resp.header("retry-after") or "").strip()
        if not value:
            return 0.0
        if value.isdigit():
            return float(value)
        try:
            return max(0.0, email.utils.parsedate_to_datetime(value).timestamp() - now)
        except (TypeError, ValueError, IndexError):
            return 0.0

    def _fail(self, state: dict, now: float, error: str, resp: Response | None = None) -> None:
        state["failures"] = int(state.get("failures") or 0) + 1
        delay = min(self.backoff_max_s, self.backoff_base_s * 2 ** (state["failures"] - 1))
        if resp is not None:
            delay = max(delay, min(self.backoff_max_s, self._retry_after(resp, now)))
        state["backoff_until"] = _iso(now + delay)
        state["last_error"] = error[:500]

    def fetch(self, url: str, state: dict | None = None, *, check_robots: bool = False, accept: str | None = None,
              force: bool = False) -> FetchResult:
        state = dict(state or new_state(url, url))
        state.setdefault("failures", 0)
        state["url"] = url
        now = self.clock()
        scheme = urlsplit(url).scheme.lower()
        if scheme not in ("http", "https"):
            state["last_error"] = f"refusing non-http(s) URL scheme {scheme!r}"
            return FetchResult(url, "invalid-url", None, state, error=state["last_error"])
        if state.get("gone") and not force:
            return FetchResult(url, "gone", state.get("last_status"), state, error="source marked gone")
        until = _ts(state.get("backoff_until"))
        if until and until > now and not force:
            return FetchResult(url, "backoff", state.get("last_status"), state, error=f"backing off until {state['backoff_until']}")
        if check_robots and not self.robots_allowed(url):
            state["robots_blocked"] = True
            state["last_attempt"] = _iso(now)
            state["last_error"] = "disallowed by robots.txt"
            return FetchResult(url, "robots-blocked", None, state, error=state["last_error"])
        state["robots_blocked"] = False
        resp = self._send(url, self._headers(url, state, accept))
        now = self.clock()
        state["last_attempt"] = _iso(now)
        state["last_status"] = resp.status or None
        if resp.status == 304:
            state.update(failures=0, backoff_until=None, last_error=None, last_success=_iso(now))
            return FetchResult(url, "not-modified", 304, state)
        if 200 <= resp.status < 300:
            if resp.error == "too-large" or len(resp.body) > self.max_bytes:
                self._fail(state, now, f"body larger than {self.max_bytes} bytes")
                return FetchResult(url, "too-large", resp.status, state, error=state["last_error"])
            try:
                body = self._decode(resp)
            except (OverflowError, zlib.error) as exc:
                self._fail(state, now, f"decode failed: {exc}")
                return FetchResult(url, "too-large" if isinstance(exc, OverflowError) else "error", resp.status,
                                   state, error=state["last_error"])
            state.update(failures=0, backoff_until=None, last_error=None, last_success=_iso(now))
            if resp.header("etag"):
                state["etag"] = resp.header("etag")
            if resp.header("last-modified"):
                state["last_modified"] = resp.header("last-modified")
            return FetchResult(url, "ok", resp.status, state, body, (resp.header("content-type") or "").split(";")[0].strip())
        if resp.status == 410:
            state["gone"] = True
            self._fail(state, now, "HTTP 410 Gone: source removed by the publisher", resp)
            return FetchResult(url, "gone", 410, state, error=state["last_error"])
        error = resp.error or f"HTTP {resp.status}"
        self._fail(state, now, error, resp)
        return FetchResult(url, "error", resp.status or None, state, error=error)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import sys

    ap = argparse.ArgumentParser(description="Fetch one URL politely and print the outcome and new source state.")
    ap.add_argument("url")
    ap.add_argument("--state", help="JSON file with a previous agent_feed_source_state")
    ap.add_argument("--robots", action="store_true", help="check robots.txt first (HTML pages)")
    ap.add_argument("--out", help="write the body here")
    a = ap.parse_args(argv)
    state = json.load(open(a.state)) if a.state else None
    res = PoliteFetcher().fetch(a.url, state, check_robots=a.robots)
    if a.out and res.body:
        with open(a.out, "wb") as fh:
            fh.write(res.body)
    json.dump({"outcome": res.outcome, "status": res.status, "bytes": len(res.body), "content_type": res.content_type,
               "error": res.error, "state": res.state}, sys.stdout, indent=2)
    print()
    return 0 if res.outcome in ("ok", "not-modified") else 1


if __name__ == "__main__":
    raise SystemExit(main())
