#!/usr/bin/env python3
"""SQLite store for Agent Feeds: items, cursors, source state, dedupe and clustering.

* **Dedupe.** An item whose normalised URL (``dedupe_key``) is already stored is recorded as another
  source of the existing item instead of a new row. The same item id seen again is updated in place,
  and re-surfaces (gets a new cursor position) only when its title, summary, severity, versions or
  affected packages changed.
* **Clustering.** The same announcement from different sources (a GitHub release and the npm
  version, an OSV advisory, its CVE in NVD and in CISA KEV, a blog post and the newsletter that
  links it) gets one ``cluster_id``: shared CVE/GHSA ids, the same package or product version, or
  titles at least 85% similar within seven days for the same vendor/product.
* **Cursors.** Every stored or re-surfaced item gets a monotonically increasing ``seq``; cursors are
  ``"seq:<n>"`` strings. Named cursors (one per project or per consumer) remember where a reader
  stopped, e.g. "since my last session".
* **Search.** SQLite FTS5 when the build has it, otherwise LIKE matching.

Standard library only. Depends on the ``agent_feeds_parse`` module for URL normalisation.

Usage::

    from agent_feeds_store import FeedStore
    store = FeedStore(".baltor/feeds/agent-feeds.sqlite")
    report = store.upsert_items(items)       # {"inserted": 3, "duplicates": 1, ...}
    items, cursor = store.since("seq:0")
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

__all__ = ["FeedStore", "parse_cursor", "title_similarity", "DEFAULT_DB"]

DEFAULT_DB = ".baltor/feeds/agent-feeds.sqlite"
SCHEMA_VERSION = "1"
SIMILARITY_THRESHOLD = 0.85
CLUSTER_WINDOW_DAYS = 7


def _sibling(name: str):
    """Import a sibling Baltor code module (.baltor/lib/<kebab>/ or a catalogue checkout)."""
    try:
        return importlib.import_module(name)
    except ImportError:
        pass
    here = Path(__file__).resolve().parent
    roots = [Path(p) for p in os.environ.get("AGENT_FEEDS_LIB", "").split(os.pathsep) if p] + [here.parent]
    for root in roots:
        for d in (root / name.replace("_", "-"), root / name, root):
            if (d / f"{name}.py").is_file():
                sys.path.insert(0, str(d))
                return importlib.import_module(name)
    raise ImportError(f"{name} not found: place the {name} code module next to this one or set AGENT_FEEDS_LIB")


_parse = _sibling("agent_feeds_parse")
normalize_url = _parse.normalize_url


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_cursor(cursor) -> int:
    """'seq:42' -> 42; None/'' -> 0; an ISO date is not a cursor (returns -1)."""
    if cursor in (None, "", 0):
        return 0
    if isinstance(cursor, int):
        return cursor
    m = re.fullmatch(r"(?:seq:)?(\d+)", str(cursor).strip())
    return int(m.group(1)) if m else -1


def _norm_title(title: str) -> str:
    t = re.sub(r"\bv(?=\d)", "", (title or "").lower())
    return re.sub(r"[^a-z0-9.]+", " ", t).strip()


def title_similarity(a: str, b: str) -> float:
    na, nb = _norm_title(a), _norm_title(b)
    if not na or not nb:
        return 0.0
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    return max(jaccard, SequenceMatcher(None, na, nb).ratio())


def _fingerprint(item: dict) -> str:
    keys = ("title", "summary", "severity", "versions", "affected_packages", "change_types", "cve_ids")
    return json.dumps([item.get(k) for k in keys], sort_keys=True, ensure_ascii=False)


def _keys(item: dict) -> set[str]:
    out = {f"cve:{c.upper()}" for c in item.get("cve_ids") or []}
    for e in item.get("entities") or []:
        if re.match(r"^(GHSA|PYSEC|RUSTSEC|GO)-", str(e)):
            out.add(f"adv:{e}")
    title_id = re.match(r"^((?:GHSA|PYSEC|RUSTSEC|GO)-[\w-]+):", item.get("title") or "")
    if title_id:
        out.add(f"adv:{title_id.group(1)}")
    for p in item.get("affected_packages") or []:
        out.add(f"pkg:{p.get('ecosystem', '').lower()}:{p.get('name', '').lower()}")
        m = re.fullmatch(r"==\s*v?([\w.+-]+)", p.get("version_range", ""))
        if m:
            out.add(f"pkgver:{p.get('name', '').lower()}:{m.group(1)}")
    vers = item.get("versions") or []
    for prod in item.get("products") or []:
        out.add(f"prod:{prod.lower()}")
        for v in vers[:2]:
            out.add(f"prodver:{prod.lower().rsplit('/', 1)[-1]}:{v.lstrip('v')}")
    return out


CLUSTER_PREFIXES = ("cve:", "adv:", "pkgver:", "prodver:")


class FeedStore:
    def __init__(self, path: str | os.PathLike = DEFAULT_DB, *, readonly: bool = False):
        self.path = str(path)
        if self.path != ":memory:" and not readonly:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        if readonly:
            self.db = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True, timeout=5)
        else:
            self.db = sqlite3.connect(self.path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.fts = False
        if not readonly:
            self._init()
        else:
            self.fts = bool(self.db.execute(
                "SELECT 1 FROM sqlite_master WHERE name='items_fts'").fetchone())

    # ------------------------------------------------------------------ schema
    def _init(self) -> None:
        c = self.db
        c.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS items(
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT UNIQUE NOT NULL,
            source_id TEXT, collection TEXT, title TEXT, url TEXT, norm_url TEXT,
            published TEXT, updated TEXT, first_seen TEXT, vendor TEXT, change_types TEXT,
            severity TEXT, dedupe_key TEXT, cluster_id TEXT, fingerprint TEXT, data TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS items_dedupe ON items(dedupe_key);
        CREATE INDEX IF NOT EXISTS items_cluster ON items(cluster_id);
        CREATE INDEX IF NOT EXISTS items_published ON items(published);
        CREATE TABLE IF NOT EXISTS item_sources(item_id TEXT, source_id TEXT, url TEXT, seen TEXT,
            PRIMARY KEY(item_id, source_id));
        CREATE TABLE IF NOT EXISTS item_keys(key TEXT, item_id TEXT, PRIMARY KEY(key, item_id));
        CREATE TABLE IF NOT EXISTS sources(source_id TEXT PRIMARY KEY, state TEXT NOT NULL, updated TEXT);
        CREATE TABLE IF NOT EXISTS cursors(name TEXT PRIMARY KEY, seq INTEGER NOT NULL, updated TEXT);
        """)
        try:
            c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(title, summary, tags)")
            self.fts = True
        except sqlite3.OperationalError:
            self.fts = False
        c.execute("INSERT OR IGNORE INTO meta(key, value) VALUES('schema_version', ?)", (SCHEMA_VERSION,))
        c.commit()

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ------------------------------------------------------------------ writes
    def _row_item(self, row) -> dict:
        item = json.loads(row["data"])
        item["seq"] = row["seq"]
        item["cluster_id"] = row["cluster_id"]
        srcs = [r[0] for r in self.db.execute(
            "SELECT source_id FROM item_sources WHERE item_id=? AND source_id<>? ORDER BY seen", (row["id"], row["source_id"]))]
        if srcs:
            item["sources"] = srcs
        return item

    def _index_fts(self, seq: int, item: dict) -> None:
        if not self.fts:
            return
        tags = " ".join([item.get("vendor") or "", *item.get("products", []), *item.get("versions", []),
                         *item.get("cve_ids", []), *item.get("change_types", []),
                         *[p.get("name", "") for p in item.get("affected_packages", [])]])
        self.db.execute("INSERT INTO items_fts(rowid, title, summary, tags) VALUES(?,?,?,?)",
                        (seq, item.get("title", ""), item.get("summary", ""), tags))

    def _find_cluster(self, item: dict, keys: set[str]) -> str | None:
        strong = [k for k in keys if k.startswith(CLUSTER_PREFIXES)]
        if strong:
            q = "SELECT i.cluster_id FROM item_keys k JOIN items i ON i.id=k.item_id WHERE k.key IN (%s) ORDER BY i.seq LIMIT 1" % \
                ",".join("?" * len(strong))
            row = self.db.execute(q, strong).fetchone()
            if row:
                return row[0]
        when = item.get("published") or item.get("updated") or _now()
        try:
            t = datetime.strptime(when, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            t = datetime.now(timezone.utc).replace(tzinfo=None)
        lo = (t - timedelta(days=CLUSTER_WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        hi = (t + timedelta(days=CLUSTER_WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        prods = {p.lower() for p in item.get("products") or []}
        vendor = (item.get("vendor") or "").lower()
        best, best_score = None, 0.0
        for row in self.db.execute(
                "SELECT id, cluster_id, title, vendor, data FROM items WHERE COALESCE(published, first_seen) BETWEEN ? AND ? "
                "ORDER BY seq DESC LIMIT 500", (lo, hi)):
            other = json.loads(row["data"])
            other_prods = {p.lower() for p in other.get("products") or []}
            same_scope = (vendor and vendor == (row["vendor"] or "").lower()) or (prods & other_prods) or \
                         (not vendor and not prods) or (not row["vendor"] and not other_prods)
            if not same_scope:
                continue
            score = title_similarity(item.get("title", ""), row["title"])
            if score > best_score:
                best, best_score = row["cluster_id"], score
        return best if best_score >= SIMILARITY_THRESHOLD else None

    def upsert_item(self, item: dict, *, seen: str | None = None) -> str:
        """Store one item. Returns 'inserted', 'updated', 'unchanged' or 'duplicate'."""
        seen = seen or _now()
        item = dict(item)
        item.pop("seq", None)
        item.pop("sources", None)
        norm = normalize_url(item.get("url", "")) if item.get("url") else ""
        fp = _fingerprint(item)
        existing = self.db.execute("SELECT * FROM items WHERE id=?", (item["id"],)).fetchone()
        if existing:
            if existing["fingerprint"] == fp:
                return "unchanged"
            item["cluster_id"] = existing["cluster_id"]
            self.db.execute("DELETE FROM items WHERE id=?", (item["id"],))
            if self.fts:
                self.db.execute("DELETE FROM items_fts WHERE rowid=?", (existing["seq"],))
            outcome = "updated"
            first_seen = existing["first_seen"]
        else:
            dup = self.db.execute("SELECT id FROM items WHERE dedupe_key=? AND id<>?",
                                  (item.get("dedupe_key"), item["id"])).fetchone() if item.get("dedupe_key") else None
            if dup:
                self.db.execute("INSERT OR IGNORE INTO item_sources(item_id, source_id, url, seen) VALUES(?,?,?,?)",
                                (dup["id"], item.get("source_id"), item.get("url"), seen))
                return "duplicate"
            keys = _keys(item)
            item["cluster_id"] = self._find_cluster(item, keys) or item["id"]
            outcome = "inserted"
            first_seen = seen
        cur = self.db.execute(
            "INSERT INTO items(id, source_id, collection, title, url, norm_url, published, updated, first_seen, vendor, "
            "change_types, severity, dedupe_key, cluster_id, fingerprint, data) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (item["id"], item.get("source_id"), item.get("collection"), item.get("title"), item.get("url"), norm,
             item.get("published"), item.get("updated"), first_seen, item.get("vendor"),
             ",".join(item.get("change_types") or []), item.get("severity"), item.get("dedupe_key"),
             item["cluster_id"], fp, json.dumps(item, ensure_ascii=False)))
        self._index_fts(cur.lastrowid, item)
        for k in _keys(item):
            self.db.execute("INSERT OR IGNORE INTO item_keys(key, item_id) VALUES(?,?)", (k, item["id"]))
        self.db.execute("INSERT OR IGNORE INTO item_sources(item_id, source_id, url, seen) VALUES(?,?,?,?)",
                        (item["id"], item.get("source_id"), item.get("url"), seen))
        return outcome

    def upsert_items(self, items: list[dict], *, seen: str | None = None) -> dict:
        report = {"inserted": 0, "updated": 0, "unchanged": 0, "duplicate": 0, "clustered": 0}
        # oldest first so cursor order follows publication order within one batch
        for item in sorted(items, key=lambda i: i.get("published") or i.get("updated") or ""):
            outcome = self.upsert_item(item, seen=seen)
            report[outcome] += 1
            if outcome == "inserted":
                row = self.db.execute("SELECT cluster_id FROM items WHERE id=?", (item["id"],)).fetchone()
                if row and row[0] != item["id"]:
                    report["clustered"] += 1
        self.db.commit()
        return report

    # ------------------------------------------------------------------ reads
    def max_seq(self) -> int:
        return self.db.execute("SELECT COALESCE(MAX(seq), 0) FROM items").fetchone()[0]

    def get(self, item_id: str) -> dict | None:
        row = self.db.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        return self._row_item(row) if row else None

    def cluster(self, cluster_id: str) -> list[dict]:
        return [self._row_item(r) for r in self.db.execute(
            "SELECT * FROM items WHERE cluster_id=? ORDER BY seq", (cluster_id,))]

    def since(self, cursor=None, *, limit: int = 100, change_types=None) -> tuple[list[dict], str]:
        """Items stored after ``cursor`` (oldest first) and the cursor to pass next time."""
        n = parse_cursor(cursor)
        if n < 0:
            raise ValueError(f"not a cursor: {cursor!r} (expected 'seq:<n>')")
        rows = list(self.db.execute("SELECT * FROM items WHERE seq>? ORDER BY seq LIMIT ?", (n, int(limit))))
        items = [self._row_item(r) for r in rows]
        last = rows[-1]["seq"] if rows else max(n, 0)
        if change_types:
            wanted = set(change_types)
            items = [i for i in items if wanted & set(i.get("change_types") or [])]
        return items, f"seq:{last}"

    def recent(self, *, since_date: str | None = None, limit: int = 200) -> list[dict]:
        q, args = "SELECT * FROM items", []
        if since_date:
            q += " WHERE COALESCE(published, first_seen) >= ?"
            args.append(since_date)
        q += " ORDER BY COALESCE(published, first_seen) DESC LIMIT ?"
        args.append(int(limit))
        return [self._row_item(r) for r in self.db.execute(q, args)]

    def search(self, query: str = "", *, since: str | None = None, change_types=None, limit: int = 20,
               collapse_clusters: bool = True) -> list[dict]:
        """Full-text search over title, summary, vendor, products, versions, CVEs and package names.

        ``since`` is an ISO date (``2026-10-01``) or a cursor (``seq:120``)."""
        args: list = []
        where = []
        terms = re.findall(r"[\w.-]+", query or "")
        if terms and self.fts:
            match = " ".join('"' + t.replace('"', "") + '"' for t in terms)
            where.append("i.seq IN (SELECT rowid FROM items_fts WHERE items_fts MATCH ?)")
            args.append(match)
        elif terms:
            for t in terms:
                where.append("(i.title LIKE ? OR i.data LIKE ?)")
                args += [f"%{t}%", f"%{t}%"]
        if since:
            if re.fullmatch(r"seq:\d+", str(since).strip()):
                where.append("i.seq > ?")
                args.append(parse_cursor(since))
            else:
                where.append("COALESCE(i.published, i.first_seen) >= ?")
                args.append(_iso_floor(since))
        q = "SELECT i.* FROM items i" + (" WHERE " + " AND ".join(where) if where else "") + \
            " ORDER BY COALESCE(i.published, i.first_seen) DESC, i.seq DESC LIMIT ?"
        args.append(int(limit) * 5)
        out, seen_clusters = [], set()
        wanted = set(change_types or [])
        for row in self.db.execute(q, args):
            item = self._row_item(row)
            if wanted and not wanted & set(item.get("change_types") or []):
                continue
            if collapse_clusters:
                if item["cluster_id"] in seen_clusters:
                    continue
                seen_clusters.add(item["cluster_id"])
            out.append(item)
            if len(out) >= limit:
                break
        return out

    def for_packages(self, packages: list[tuple[str, str]], *, change_types=None, limit: int = 50) -> list[dict]:
        """Items that name any of ``(ecosystem, name)`` in affected_packages."""
        keys = [f"pkg:{e.lower()}:{n.lower()}" for e, n in packages]
        if not keys:
            return []
        q = ("SELECT DISTINCT i.* FROM item_keys k JOIN items i ON i.id=k.item_id WHERE k.key IN (%s) "
             "ORDER BY COALESCE(i.published, i.first_seen) DESC LIMIT ?") % ",".join("?" * len(keys))
        items = [self._row_item(r) for r in self.db.execute(q, [*keys, int(limit)])]
        if change_types:
            wanted = set(change_types)
            items = [i for i in items if wanted & set(i.get("change_types") or [])]
        return items

    # ------------------------------------------------------------------ state and cursors
    def get_state(self, source_id: str) -> dict | None:
        row = self.db.execute("SELECT state FROM sources WHERE source_id=?", (source_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def set_state(self, state: dict) -> None:
        self.db.execute("INSERT INTO sources(source_id, state, updated) VALUES(?,?,?) "
                        "ON CONFLICT(source_id) DO UPDATE SET state=excluded.state, updated=excluded.updated",
                        (state["source_id"], json.dumps(state, ensure_ascii=False), _now()))
        self.db.commit()

    def states(self) -> list[dict]:
        return [json.loads(r[0]) for r in self.db.execute("SELECT state FROM sources ORDER BY source_id")]

    def get_cursor(self, name: str) -> str | None:
        row = self.db.execute("SELECT seq FROM cursors WHERE name=?", (name,)).fetchone()
        return f"seq:{row[0]}" if row else None

    def set_cursor(self, name: str, cursor) -> None:
        self.db.execute("INSERT INTO cursors(name, seq, updated) VALUES(?,?,?) "
                        "ON CONFLICT(name) DO UPDATE SET seq=excluded.seq, updated=excluded.updated",
                        (name, max(parse_cursor(cursor), 0), _now()))
        self.db.commit()

    # ------------------------------------------------------------------ maintenance
    def prune(self, older_than_days: int = 180) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ids = [r[0] for r in self.db.execute(
            "SELECT id FROM items WHERE COALESCE(published, first_seen) < ? AND "
            "(severity IS NULL OR severity NOT IN ('high','critical'))", (cutoff,))]
        for i in ids:
            row = self.db.execute("SELECT seq FROM items WHERE id=?", (i,)).fetchone()
            if self.fts and row:
                self.db.execute("DELETE FROM items_fts WHERE rowid=?", (row[0],))
            self.db.execute("DELETE FROM items WHERE id=?", (i,))
            self.db.execute("DELETE FROM item_keys WHERE item_id=?", (i,))
            self.db.execute("DELETE FROM item_sources WHERE item_id=?", (i,))
        self.db.commit()
        return len(ids)

    def stats(self) -> dict:
        one = lambda q: self.db.execute(q).fetchone()[0]  # noqa: E731
        return {"items": one("SELECT COUNT(*) FROM items"), "clusters": one("SELECT COUNT(DISTINCT cluster_id) FROM items"),
                "sources": one("SELECT COUNT(*) FROM sources"), "max_seq": self.max_seq(), "fts": self.fts}


def _iso_floor(value: str) -> str:
    v = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v + "T00:00:00Z"
    return _parse.parse_date(v) or v


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Inspect an Agent Feeds store.")
    ap.add_argument("--db", default=os.environ.get("AGENT_FEEDS_DB", DEFAULT_DB))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query", nargs="?", default="")
    s.add_argument("--since")
    s.add_argument("--limit", type=int, default=20)
    n = sub.add_parser("since")
    n.add_argument("cursor", nargs="?", default="seq:0")
    sub.add_parser("stats")
    sub.add_parser("sources")
    p = sub.add_parser("prune")
    p.add_argument("--days", type=int, default=180)
    a = ap.parse_args(argv)
    store = FeedStore(a.db)
    if a.cmd == "search":
        out = store.search(a.query, since=a.since, limit=a.limit)
    elif a.cmd == "since":
        items, cur = store.since(a.cursor)
        out = {"items": items, "next_cursor": cur}
    elif a.cmd == "sources":
        out = store.states()
    elif a.cmd == "prune":
        out = {"pruned": store.prune(a.days)}
    else:
        out = store.stats()
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
