"""Fetch the files an agent media pack manifest points at, verify them and write CREDITS.md.

The manifest format is the ``agent_media_pack_manifest`` contract schema
(``spec: baltor.media-pack/v1``). This module never invents sources: it only
downloads assets whose ``fetch.method`` is ``direct`` and whose
``download_url`` is HTTPS on an allow-listed host. Everything else (pages that
need a human click, project-only files such as Mixamo downloads, licences that
forbid automated downloads) is reported as manual work.

Guarantees:

* HTTPS only, allow-listed hosts only, including every redirect hop.
* Each download is size-capped and hashed with SHA-256. When the manifest
  already records a hash, a mismatch is rejected and nothing is written.
  When it does not, the computed hash is recorded ("trust on first fetch").
* File names are reduced to a safe basename; nothing is written outside
  ``out_dir``.
* ``CREDITS.md`` lists every asset with its exact credit line, licence and
  source, and a separate "do not redistribute" section.

Usage::

    python media_pack_fetcher.py pack.json --out assets/ [--allow-host HOST ...]
                                 [--use-manifest-hosts] [--dry-run] [--max-mb 200]

Exit status: 0 when every direct asset was fetched and verified, 1 otherwise.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlparse

DEFAULT_ALLOWED_HOSTS: tuple[str, ...] = ("raw.githubusercontent.com", "github.com")
USER_AGENT = "baltor-media-pack-fetcher/1.0 (+https://github.com/taylor-s-amarel/ai-video-pipeline)"
SAFE_CHARS = re.compile(r"[^A-Za-z0-9._ -]+")
ATTRIBUTION_LICENCE = re.compile(r"\b(CC-BY|CC BY|OGA-BY|GPL|LGPL|OFL|Apache)", re.I)

Fetcher = Callable[[str, int], bytes]


class FetchError(RuntimeError):
    """A download was refused or failed."""


def host_allowed(url: str, allowed: Iterable[str]) -> bool:
    """True when ``url`` is HTTPS and its host is on the allow-list.

    Entries match exactly; an entry written ``*.example.org`` also matches any
    subdomain of example.org (but not example.org itself).
    """
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower().rstrip(".")
    for entry in allowed:
        entry = entry.lower().strip()
        if entry.startswith("*."):
            if host.endswith(entry[1:]) and host != entry[2:]:
                return True
        elif host == entry:
            return True
    return False


def safe_name(name: str, fallback: str = "asset.bin") -> str:
    """Reduce ``name`` to a safe basename (no directories, no traversal)."""
    base = os.path.basename(name.replace("\\", "/")).strip()
    base = SAFE_CHARS.sub("_", base).strip(" .")
    if not base or base in {".", ".."}:
        return fallback
    return base[:120]


def file_name_for(asset: dict) -> str:
    if asset.get("file_name"):
        return safe_name(asset["file_name"])
    url = asset.get("download_url") or ""
    path = urlparse(url).path
    from urllib.parse import unquote
    return safe_name(unquote(path.rsplit("/", 1)[-1]), fallback=f"{asset.get('id', 'asset')}.bin")


class UrllibFetcher:
    """Standard-library HTTPS fetcher that re-checks the allow-list on every redirect."""

    def __init__(self, allowed: Iterable[str], timeout: float = 60.0, pause_s: float = 0.5):
        self.allowed = tuple(allowed)
        self.timeout = timeout
        self.pause_s = pause_s
        fetcher = self

        class _Redirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
                fetcher.check_redirect(newurl)
                return super().redirect_request(req, fp, code, msg, headers, newurl)

        self._opener = urllib.request.build_opener(_Redirect)

    def check_redirect(self, newurl: str) -> None:
        if not host_allowed(newurl, self.allowed):
            raise FetchError(f"redirect to a host that is not allow-listed: {newurl}")

    def __call__(self, url: str, max_bytes: int) -> bytes:
        if not host_allowed(url, self.allowed):
            raise FetchError(f"host not allow-listed or not https: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with self._opener.open(req, timeout=self.timeout) as resp:  # noqa: S310 (https + allow-list checked)
            final = resp.geturl()
            if not host_allowed(final, self.allowed):
                raise FetchError(f"final URL is not allow-listed: {final}")
            chunks, total = [], 0
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise FetchError(f"{url} is larger than {max_bytes} bytes")
                chunks.append(chunk)
        if self.pause_s:
            time.sleep(self.pause_s)
        return b"".join(chunks)


@dataclass
class AssetResult:
    asset_id: str
    action: str  # fetched | verified | skipped-manual | blocked | failed | dry-run
    detail: str = ""
    path: str | None = None
    sha256: str | None = None
    bytes: int | None = None


@dataclass
class PackReport:
    pack_id: str
    results: list[AssetResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(r.action in {"blocked", "failed"} for r in self.results)

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for r in self.results:
            counts[r.action] = counts.get(r.action, 0) + 1
        return {"pack_id": self.pack_id, "ok": self.ok, "counts": counts}


def plan(manifest: dict, allowed: Iterable[str]) -> list[tuple[str, dict, str]]:
    """Return (action, asset, reason) for every asset without touching the network."""
    allowed = tuple(allowed)
    out = []
    for asset in manifest.get("assets", []):
        fetch = asset.get("fetch") or {}
        method = fetch.get("method", "manual-page")
        if asset.get("redistribution") == "forbidden" and method == "direct":
            out.append(("blocked", asset, "redistribution forbidden: download it yourself from the source page"))
        elif method != "direct":
            out.append(("skipped-manual", asset, f"fetch.method is {method}: open {asset.get('source_url')}"))
        elif not asset.get("download_url"):
            out.append(("skipped-manual", asset, "no download_url recorded"))
        elif not host_allowed(asset["download_url"], allowed):
            out.append(("blocked", asset, f"host not allow-listed: {asset['download_url']}"))
        else:
            out.append(("fetch", asset, ""))
    return out


def _write_atomic(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".part-", dir=dest.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, dest)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def fetch_pack(manifest: dict, out_dir: str | Path, fetcher: Fetcher | None = None,
               allowed: Iterable[str] = DEFAULT_ALLOWED_HOSTS, max_bytes: int = 200 * 1024 * 1024,
               dry_run: bool = False, today: str | None = None) -> tuple[dict, PackReport]:
    """Fetch every direct asset of ``manifest`` into ``out_dir/<asset id>/``.

    Returns the updated manifest (a copy, with sha256/bytes/fetch.status filled in) and a report.
    ``fetcher(url, max_bytes) -> bytes`` is injectable so tests never touch the network.
    """
    allowed = tuple(allowed)
    fetcher = fetcher or UrllibFetcher(allowed)
    out_dir = Path(out_dir)
    updated = copy.deepcopy(manifest)
    by_id = {a.get("id"): a for a in updated.get("assets", [])}
    report = PackReport(pack_id=str(manifest.get("pack_id", "pack")))
    today = today or time.strftime("%Y-%m-%d")
    for action, asset, reason in plan(manifest, allowed):
        aid = str(asset.get("id"))
        target = by_id[asset.get("id")]
        if action != "fetch":
            report.results.append(AssetResult(aid, action, reason))
            continue
        name = file_name_for(asset)
        dest = out_dir / safe_name(aid, fallback="asset") / name
        if dry_run:
            report.results.append(AssetResult(aid, "dry-run", f"would fetch {asset['download_url']}", str(dest)))
            continue
        try:
            data = fetcher(asset["download_url"], max_bytes)
            if len(data) > max_bytes:
                raise FetchError(f"{len(data)} bytes exceeds the {max_bytes}-byte cap")
        except Exception as exc:  # noqa: BLE001 - every failure is reported, none is fatal
            target.setdefault("fetch", {})["status"] = "failed"
            report.results.append(AssetResult(aid, "failed", str(exc)))
            continue
        digest = hashlib.sha256(data).hexdigest()
        expected = (asset.get("sha256") or "").lower() or None
        if expected and expected != digest:
            target.setdefault("fetch", {})["status"] = "failed"
            report.results.append(AssetResult(aid, "failed", f"sha256 mismatch: expected {expected}, got {digest}"))
            continue
        _write_atomic(dest, data)
        target["sha256"] = digest
        target["bytes"] = len(data)
        target["file_name"] = name
        target.setdefault("fetch", {})["status"] = "fetched"
        target["fetch"]["fetched_on"] = today
        report.results.append(AssetResult(aid, "verified" if expected else "fetched",
                                          "hash matched manifest" if expected else "hash recorded on first fetch",
                                          str(dest), digest, len(data)))
    statuses = [a.get("fetch", {}).get("status") for a in updated.get("assets", [])]
    if statuses and all(s == "fetched" for s in statuses):
        updated["status"] = "fetched"
    elif any(s == "fetched" for s in statuses):
        updated["status"] = "partially-fetched"
    return updated, report


def needs_attribution(asset: dict) -> bool:
    if "attribution_required" in asset:
        return bool(asset["attribution_required"])
    return bool(ATTRIBUTION_LICENCE.search(asset.get("licence", "")))


def credits_markdown(manifest: dict) -> str:
    """Render CREDITS.md: required credits first, then courtesy credits, then restrictions."""
    assets = manifest.get("assets", [])
    lines = [f"# Credits: {manifest.get('title', manifest.get('pack_id', 'media pack'))}", ""]
    lines.append(f"Pack `{manifest.get('pack_id', '')}`. Generated from the media pack manifest; "
                 "keep this file with any build, video description or repository that uses these assets.")
    lines.append("")

    def entry(a: dict) -> list[str]:
        credit = a.get("attribution") or f"{a.get('title', a.get('id'))}"
        out = [f"- **{a.get('title', a.get('id'))}**" + (f" by {a['creator']}" if a.get("creator") else "")]
        out.append(f"  - Credit line: {credit}")
        out.append(f"  - Licence: {a.get('licence', 'unknown')} ({a.get('licence_url', 'no licence URL')})")
        out.append(f"  - Source: {a.get('source_url', 'unknown')}")
        if a.get("sha256"):
            out.append(f"  - SHA-256: `{a['sha256']}`")
        return out

    required = [a for a in assets if needs_attribution(a)]
    courtesy = [a for a in assets if not needs_attribution(a)]
    if required:
        lines += ["## Attribution required", ""]
        for a in required:
            lines += entry(a)
        lines.append("")
    if courtesy:
        lines += ["## No attribution required (credited as a courtesy)", ""]
        for a in courtesy:
            lines += entry(a)
        lines.append("")
    restricted = [a for a in assets if a.get("redistribution") in {"forbidden", "project-only"}
                  or a.get("commercial_use") == "non-commercial-only" or a.get("restrictions")]
    if restricted:
        lines += ["## Restrictions", ""]
        for a in restricted:
            notes = []
            if a.get("redistribution") in {"forbidden", "project-only"}:
                notes.append("do not redistribute the raw files (use inside the finished work only)")
            if a.get("commercial_use") == "non-commercial-only":
                notes.append("non-commercial use only")
            notes += list(a.get("restrictions") or [])
            lines.append(f"- **{a.get('title', a.get('id'))}**: " + "; ".join(notes))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-host", action="append", default=[], help="extra allow-listed host (repeatable)")
    ap.add_argument("--use-manifest-hosts", action="store_true",
                    help="also allow the hosts listed in manifest.allowed_hosts (review them first)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-mb", type=float, default=200)
    ap.add_argument("--credits", default=None, help="where to write CREDITS.md (default: <out>/CREDITS.md)")
    a = ap.parse_args(argv)
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    allowed = list(DEFAULT_ALLOWED_HOSTS) + a.allow_host
    if a.use_manifest_hosts:
        allowed += list(manifest.get("allowed_hosts", []))
    updated, report = fetch_pack(manifest, a.out, allowed=allowed, max_bytes=int(a.max_mb * 1024 * 1024),
                                 dry_run=a.dry_run)
    for r in report.results:
        print(f"{r.action:<15} {r.asset_id:<32} {r.detail}")
    if not a.dry_run:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "pack.lock.json").write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
        Path(a.credits or out / "CREDITS.md").write_text(credits_markdown(updated), encoding="utf-8")
    print(json.dumps(report.summary()))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
