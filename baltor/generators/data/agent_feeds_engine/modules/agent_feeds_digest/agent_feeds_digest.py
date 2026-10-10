#!/usr/bin/env python3
"""Write "what changed for this project" as an agent_feed_digest (JSON) and Markdown.

Items are scored with ``agent_feeds_relevance`` against the project watchlist, collapsed so one
announcement seen in several sources appears once ("also reported by ..."), and grouped by the
action they need:

==============  ===============================================================================
security        advisories; affected=no moves to FYI
breaking        breaking changes
deprecation     deprecations and end-of-life dates
new_capability  releases, model releases and "now supports" announcements
fyi             incidents, pricing, research and everything else that matched
==============  ===============================================================================

Within a group entries are newest first. Every entry has the reasons it matched and a concrete
``suggested_action`` ("Upgrade examplelib to 2.31.0 or later (requirements.txt pins 2.30.0).").

CLI (reads the store, writes ``digest.json`` and ``digest.md``, then advances the project cursor)::

    python3 agent_feeds_digest.py --watchlist .baltor/feeds/watchlist.json --out .baltor/feeds/digest
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["build_digest", "render_markdown", "write_digest", "group_for", "suggested_action", "GROUPS"]

SPEC = "baltor.agent-feed-digest/v1"
GROUPS = ["breaking", "deprecation", "security", "new_capability", "fyi"]
RENDER_ORDER = ["security", "breaking", "deprecation", "new_capability", "fyi"]
TITLES = {"security": "Security", "breaking": "Breaking changes", "deprecation": "Deprecations and end of life",
          "new_capability": "New capabilities", "fyi": "FYI"}
_NEW = re.compile(r"\b(adds?|added|new|introduc\w*|now supports?|launch\w*|generally available|available now|"
                  r"released?|ships?)\b", re.I)
_DATE = re.compile(r"\b(20\d\d-\d\d-\d\d|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? 20\d\d)\b")


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


relevance = _sibling("agent_feeds_relevance")


def group_for(item: dict) -> str:
    ct = set(item.get("change_types") or [])
    rel = item.get("relevance") or {}
    if "security" in ct:
        return "fyi" if rel.get("affected") == "no" else "security"
    if "breaking-change" in ct:
        return "breaking"
    if "deprecation" in ct:
        return "deprecation"
    if ct & {"release", "model-release"} or (ct & {"docs", "tutorial"} and _NEW.search(item.get("title") or "")):
        return "new_capability"
    return "fyi"


def _first_pkg(item: dict, watchlist: dict):
    idx = {(relevance._eco(p.get("ecosystem", "")), relevance.norm_name(p.get("name", ""), p.get("ecosystem", ""))): p
           for p in watchlist.get("packages") or []}
    for ap in item.get("affected_packages") or []:
        key = (relevance._eco(ap.get("ecosystem", "")), relevance.norm_name(ap.get("name", ""), ap.get("ecosystem", "")))
        if key in idx:
            return ap, idx[key]
    aps = item.get("affected_packages") or []
    return (aps[0], None) if aps else (None, None)


def _fix_for(ap: dict, pinned: str | None) -> str | None:
    fixed = sorted((f for f in ap.get("fixed") or [] if relevance.parse_version(f)), key=relevance.parse_version)
    if not fixed:
        m = re.search(r"<\s*v?([0-9][\w.\-]*)\s*$", (ap.get("version_range") or "").split("||")[-1])
        fixed = [m.group(1)] if m else []
    if pinned and relevance.parse_version(pinned):
        later = [f for f in fixed if relevance.parse_version(f) > relevance.parse_version(pinned)]
        return later[0] if later else (fixed[-1] if fixed else None)
    return fixed[-1] if fixed else None


def suggested_action(item: dict, group: str, watchlist: dict) -> str:
    rel = item.get("relevance") or {}
    product = ", ".join((item.get("products") or [])[:2]) or item.get("vendor") or "this component"
    version = (item.get("versions") or [""])[0]
    title = item.get("title") or ""
    if group == "security":
        ap, watch = _first_pkg(item, watchlist)
        if ap:
            name = (watch or {}).get("name") or ap.get("name")
            pinned = (watch or {}).get("pinned")
            fix = _fix_for(ap, pinned)
            src = (watch or {}).get("source_file")
            if rel.get("affected") == "yes" and fix:
                return f"Upgrade {name} to {fix} or later" + (f" ({src} pins {pinned})." if src and pinned else ".")
            if fix:
                return (f"Check the resolved version of {name} in your lockfile or environment; if it is in "
                        f"{ap.get('version_range')}, upgrade to {fix} or later" + (f" and tighten the range in {src}." if src else "."))
            return f"No fixed version is listed yet: check whether you use the affected code path in {name}, apply the advisory's workaround and watch for a fix."
        if "known-exploited" in (item.get("entities") or []):
            due = re.search(r"Due: (\d{4}-\d{2}-\d{2})", item.get("summary") or "")
            return f"If you run {item.get('vendor') or ''} {product}, patch it" + (f" by {due.group(1)}" if due else "") + \
                   " (actively exploited, CISA KEV)."
        return "Read the advisory and check whether the affected product is part of this project's deployment."
    if group == "breaking":
        return (f"Read the migration notes before upgrading {product}" + (f" to {version}" if version else "") +
                "; pin the current major version until the migration is done.")
    if group == "deprecation":
        when = _DATE.search(f"{title} {item.get('summary') or ''}")
        return f"Plan the move off the deprecated {product} feature or version" + (f" before {when.group(1)}" if when else "") + \
               "; add a task with the replacement named in the notice."
    if group == "new_capability":
        if "model-release" in (item.get("change_types") or []):
            return f"Evaluate it against this project's current model on a few real tasks before switching: {title}."
        if "prerelease" in (item.get("entities") or []):
            return f"Pre-release of {product}; try it in a branch only."
        return f"Optional: upgrade {product}" + (f" to {version}" if version else "") + " if the new capability helps; read the release notes first."
    ct = set(item.get("change_types") or [])
    if "security" in ct:
        return "Not affected by the installed version; no action needed."
    if "incident" in ct:
        return f"If calls to {item.get('vendor') or product} fail, check the status page before debugging this project's code."
    if "pricing" in ct:
        return "Check the cost impact on this project's usage."
    if "research" in ct:
        return "Read if it bears on the current task; no action needed."
    return "No action needed."


def _entry(item: dict, group: str, watchlist: dict, also: list[str]) -> dict:
    rel = item.get("relevance") or {"score": 0, "reasons": []}
    e = {"item_id": item["id"], "title": item.get("title", ""), "url": item.get("url", ""), "group": group,
         "published": item.get("published") or item.get("updated"), "source_id": item.get("source_id", ""),
         "vendor": item.get("vendor"), "products": list(item.get("products") or []),
         "versions": list(item.get("versions") or []), "change_types": list(item.get("change_types") or []),
         "severity": item.get("severity"), "cve_ids": list(item.get("cve_ids") or []), "score": int(rel.get("score", 0)),
         "reasons": list(rel.get("reasons") or []), "affected": rel.get("affected", "unknown"),
         "suggested_action": suggested_action(item, group, watchlist)[:400]}
    if also:
        e["also_reported_by"] = also
    return e


def build_digest(items: list[dict], watchlist: dict, *, project: str | None = None, since_cursor: str | None = None,
                 next_cursor: str | None = None, min_score: int | None = None, generated: str | None = None,
                 watchlist_ref: str | None = None, max_per_group: int = 25) -> dict:
    ranked = relevance.rank(items, watchlist, min_score=min_score)
    by_cluster: dict[str, list[dict]] = {}
    for it in ranked:  # best score first, so the first one per cluster is the representative
        by_cluster.setdefault(it.get("cluster_id") or it["id"], []).append(it)
    groups: dict[str, list[dict]] = {g: [] for g in GROUPS}
    sev_known = lambda i: 0 if i.get("severity") in (None, "unknown") else 1  # noqa: E731
    for members in by_cluster.values():
        # representative: best score, then a known severity, then the earliest (original) report
        members.sort(key=lambda i: (-i["relevance"]["score"], -sev_known(i), i.get("published") or "9999"))
        rep = members[0]
        also = sorted({m.get("source_id", "") for m in members[1:]} | set(rep.get("sources") or []) - {rep.get("source_id")})
        g = group_for(rep)
        groups[g].append(_entry(rep, g, watchlist, [a for a in also if a]))
    for g in GROUPS:
        groups[g].sort(key=lambda e: (e["published"] or "", e["score"]), reverse=True)
        groups[g] = groups[g][:max_per_group]
    counts = {g: len(groups[g]) for g in GROUPS}
    counts["total"] = sum(counts[g] for g in GROUPS)
    counts["considered"] = len(items)
    digest = {"spec": SPEC, "project": project or watchlist.get("project") or "project",
              "generated": generated or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "since_cursor": since_cursor, "next_cursor": next_cursor,
              "min_score": watchlist.get("min_score", 30) if min_score is None else min_score,
              "counts": counts, "groups": groups}
    if watchlist_ref:
        digest["watchlist"] = watchlist_ref
    return digest


def render_markdown(digest: dict) -> str:
    c = digest["counts"]
    lines = [f"# What changed for {digest['project']}", "",
             f"Generated {digest['generated']} · since {digest.get('since_cursor') or 'the beginning'} · "
             f"{c['total']} relevant of {c['considered']} new items", ""]
    if not c["total"]:
        lines += ["Nothing relevant to this project's watchlist.", ""]
    for g in RENDER_ORDER:
        entries = digest["groups"].get(g) or []
        if not entries:
            continue
        lines += [f"## {TITLES[g]} ({len(entries)})", ""]
        for e in entries:
            date = (e.get("published") or "")[:10] or "undated"
            sev = f" · {e['severity']}" if e.get("severity") and e["severity"] not in ("none", "unknown") else ""
            title = e["title"].replace("[", "(").replace("]", ")")
            lines.append(f"- **[{title}]({e['url']})** · {date} · {e['source_id']}{sev} · score {e['score']}")
            if e.get("reasons"):
                lines.append(f"  - Why: {'; '.join(e['reasons'][:3])}")
            lines.append(f"  - Action: {e['suggested_action']}")
            if e.get("also_reported_by"):
                lines.append(f"  - Also reported by: {', '.join(e['also_reported_by'][:5])}")
        lines.append("")
    lines.append(f"Next cursor: `{digest.get('next_cursor')}`")
    return "\n".join(lines).rstrip() + "\n"


def write_digest(digest: dict, out_dir: str | os.PathLike) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    j, m = out / "digest.json", out / "digest.md"
    j.write_text(json.dumps(digest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    m.write_text(render_markdown(digest), encoding="utf-8")
    return j, m


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Write the project digest from the Agent Feeds store.")
    ap.add_argument("--db", default=os.environ.get("AGENT_FEEDS_DB", ".baltor/feeds/agent-feeds.sqlite"))
    ap.add_argument("--watchlist", default=".baltor/feeds/watchlist.json")
    ap.add_argument("--since", help="cursor (seq:<n>); default: the project's saved cursor")
    ap.add_argument("--out", default=".baltor/feeds/digest")
    ap.add_argument("--min-score", type=int)
    ap.add_argument("--no-advance", action="store_true", help="do not move the project's cursor")
    ap.add_argument("--items", help="score a JSON list of items instead of reading the store")
    a = ap.parse_args(argv)
    wl = relevance.load_watchlist(a.watchlist)
    name = f"project:{wl.get('project', 'project')}"
    store = None
    if a.items:
        items, since, nxt = json.loads(Path(a.items).read_text()), None, None
    else:
        store = _sibling("agent_feeds_store").FeedStore(a.db)
        since = a.since or store.get_cursor(name) or "seq:0"
        items, nxt = [], since
        while True:
            batch, nxt2 = store.since(nxt, limit=500)
            items += batch
            if not batch:
                break
            nxt = nxt2
    digest = build_digest(items, wl, since_cursor=since, next_cursor=nxt, min_score=a.min_score, watchlist_ref=a.watchlist)
    j, m = write_digest(digest, a.out)
    if store is not None and not a.no_advance:
        store.set_cursor(name, nxt)
    print(f"wrote {j} and {m}: {digest['counts']['total']} relevant of {digest['counts']['considered']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
