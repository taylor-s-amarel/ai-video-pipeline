#!/usr/bin/env python3
"""Score agent_feed_items against a project watchlist and explain why (standard library only).

Signals, strongest first:

1. **Exact package + version range.** An advisory or breaking change that names a package the project
   uses is checked against the project's pinned version or allowed range: "examplelib==2.30.0
   (requirements.txt) is inside the affected range >=2.3.0,<2.31.0; fixed in 2.31.0". Ranges are
   understood for PyPI (PEP 440 subset), npm (semver ranges: ^ ~ x-ranges, hyphen ranges, ||),
   crates.io (Cargo caret default), Go (v-prefixed pins), OSV event ranges and NVD CPE bounds.
2. **Product / MCP server / harness match** (item products or title).
3. **Vendor match.**
4. **Topic keywords** from the watchlist; excluded topics drop an item.
5. Change-type and severity weighting: security, breaking and deprecation items rank higher; security
   items below the watchlist's ``min_severity`` are pushed down; known-exploited advisories go up.

Every score comes with ``reasons`` (plain sentences) and ``affected`` = yes | maybe | no | unknown.

Usage::

    from agent_feeds_relevance import rank, load_watchlist
    ranked = rank(items, load_watchlist(".baltor/feeds/watchlist.json"), min_score=30)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

__all__ = ["parse_version", "spec_intervals", "version_in_spec", "specs_overlap", "score_item", "rank",
           "load_watchlist", "norm_name", "SEVERITY_ORDER"]

SEVERITY_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
HARNESS_NAMES = {
    "claude-code": ["claude-code", "claude code", "claude-agent-sdk"],
    "codex": ["codex", "codex cli", "openai/codex"],
    "opencode": ["opencode"],
    "pi": ["pi-mono", "pi coding agent", "pi-coding-agent"],
    "gemini-cli": ["gemini-cli", "gemini cli"],
    "cursor": ["cursor"],
}
ACTION_TYPES = {"security", "breaking-change", "deprecation"}

# --------------------------------------------------------------------------- versions

_PRE = {"dev": -4, "alpha": -3, "a": -3, "beta": -2, "b": -2, "pre": -1, "preview": -1, "rc": -1, "c": -1}


def parse_version(v) -> tuple | None:
    """Comparable key for a version string; None when it has no leading number."""
    s = str(v or "").strip().lower()
    s = re.sub(r"^[=v\s]+", "", s).split("+", 1)[0]
    m = re.match(r"^(\d+(?:\.\d+)*)(.*)$", s)
    if not m:
        return None
    rel = [int(x) for x in m.group(1).split(".")][:6]
    rest = m.group(2)
    post = re.match(r"^[.-]?post[.-]?(\d*)", rest)
    pre = re.match(r"^[.-]?(dev|alpha|beta|preview|pre|rc|a|b|c)[.-]?(\d*)(?:$|[.-])", rest)
    if post:
        tail = (1, int(post.group(1) or 0))
    elif pre:
        tail = (-1, _PRE[pre.group(1)], int(pre.group(2) or 0))
    else:
        tail = (0,)
    return tuple(rel + [0] * (6 - len(rel))), tail


def _bump(v: str, index: int) -> tuple:
    """Key of the version with component ``index`` incremented and the rest zeroed (exclusive upper bound)."""
    nums = [int(x) for x in re.findall(r"\d+", v)[:6]] or [0]
    nums = nums + [0] * (6 - len(nums))
    nums[index] += 1
    for i in range(index + 1, 6):
        nums[i] = 0
    return tuple(nums), (-1, -5, 0)  # below any pre-release of that version


def _parts(v: str) -> int:
    return len([x for x in re.split(r"[.]", re.sub(r"[-+].*$", "", v)) if x not in ("", "*", "x", "X")])


FULL = [(None, False, None, False)]


def _interval(op: str, v: str, ecosystem: str) -> list[tuple]:
    v = v.strip().lstrip("vV")
    wildcard = bool(re.search(r"(^|\.)[*xX](\.|$)", v))
    base = re.sub(r"(\.[*xX])+$", "", v) if wildcard else v
    if base in ("*", "x", "X", ""):
        return list(FULL)
    key = parse_version(base)
    if key is None:
        return list(FULL)
    n = _parts(base)
    if op == "" and ecosystem == "crates.io" and not wildcard:
        op = "^"
    if op in ("", "=", "==", "===") and (wildcard or (op == "" and ecosystem == "npm" and n < 3)):
        return [(key, True, _bump(base, max(n - 1, 0)), False)]
    if op in ("", "=", "==", "==="):
        return [(key, True, key, True)]
    if op == ">=":
        return [(key, True, None, False)]
    if op == ">":
        return [(key, False, None, False)]
    if op == "<=":
        if ecosystem == "npm" and n < 3:  # npm x-range: <=1.2 means <1.3.0
            return [(None, False, _bump(base, n - 1), False)]
        return [(None, False, key, True)]
    if op == "<":
        return [(None, False, key, False)]
    if op == "~=":  # PEP 440 compatible release: ~=1.4.2 -> >=1.4.2,<1.5 ; ~=1.4 -> >=1.4,<2
        return [(key, True, _bump(base, max(n - 2, 0)), False)]
    if op == "~":  # npm/cargo tilde: ~1.2.3 -> <1.3.0 ; ~1 -> <2
        return [(key, True, _bump(base, 1 if n >= 2 else 0), False)]
    if op == "^":  # caret: first non-zero component is fixed
        nums = [int(x) for x in re.findall(r"\d+", base)[:3]] + [0, 0, 0]
        idx = next((i for i in range(min(n, 3)) if nums[i] != 0), min(n, 3) - 1)
        return [(key, True, _bump(base, max(idx, 0)), False)]
    return list(FULL)


def _intersect(a: tuple, b: tuple) -> tuple | None:
    lo, lo_inc = a[0], a[1]
    if b[0] is not None and (lo is None or b[0] > lo or (b[0] == lo and not b[1])):
        lo, lo_inc = b[0], b[1]
    hi, hi_inc = a[2], a[3]
    if b[2] is not None and (hi is None or b[2] < hi or (b[2] == hi and not b[3])):
        hi, hi_inc = b[2], b[3]
    if lo is not None and hi is not None and (lo > hi or (lo == hi and not (lo_inc and hi_inc))):
        return None
    return lo, lo_inc, hi, hi_inc


_TOKEN = re.compile(r"(===|==|!=|~=|>=|<=|>|<|=|\^|~)?\s*(v?[0-9*xX][0-9A-Za-z.*+\-]*)")


def spec_intervals(spec, ecosystem: str = "") -> list[tuple] | None:
    """Union of intervals allowed by a version specifier; None when the spec cannot be understood
    (git URLs, dist-tags such as 'latest', workspace refs)."""
    s = str(spec or "").strip()
    if s in ("", "*", "x", "X"):
        return list(FULL)
    if re.match(r"^(git|http|file:|link:|workspace:|npm:|github:)", s) or re.fullmatch(r"[A-Za-z][\w-]*", s):
        return None
    out: list[tuple] = []
    for alt in s.split("||"):
        alt = alt.strip()
        hy = re.fullmatch(r"v?([0-9][\w.\-]*)\s+-\s+v?([0-9][\w.\-]*)", alt)
        if hy:
            lo, hi = hy.groups()
            upper = (None, False, parse_version(hi), True) if _parts(hi) >= 3 else \
                    (None, False, _bump(hi, _parts(hi) - 1), False)
            iv = _intersect((parse_version(lo), True, None, False), upper)
            if iv:
                out.append(iv)
            continue
        current = [(None, False, None, False)]
        tokens = [t for t in re.split(r"[,\s]+", alt.replace(", ", ",")) if t]
        merged: list[str] = []
        for t in tokens:  # re-attach operators separated by a space: ">= 1.2"
            if merged and re.fullmatch(r"(===|==|!=|~=|>=|<=|>|<|=|\^|~)", merged[-1]):
                merged[-1] += t
            else:
                merged.append(t)
        for t in merged:
            m = _TOKEN.fullmatch(t)
            if not m:
                return None
            op, ver = m.group(1) or "", m.group(2)
            if op == "!=":
                continue  # exclusions do not change overlap answers enough to matter here
            nxt = []
            for a in current:
                for b in _interval(op, ver, ecosystem):
                    iv = _intersect(a, b)
                    if iv:
                        nxt.append(iv)
            current = nxt
        out.extend(current)
    return out


def _contains(intervals: list[tuple], key: tuple) -> bool:
    return any(_intersect(iv, (key, True, key, True)) for iv in intervals)


def version_in_spec(version: str, spec: str, ecosystem: str = "") -> bool | None:
    key = parse_version(version)
    ivs = spec_intervals(spec, ecosystem)
    if key is None or ivs is None:
        return None
    return _contains(ivs, key)


def specs_overlap(a: str, b: str, ecosystem: str = "") -> bool | None:
    ia, ib = spec_intervals(a, ecosystem), spec_intervals(b, ecosystem)
    if ia is None or ib is None:
        return None
    return any(_intersect(x, y) for x in ia for y in ib)


# --------------------------------------------------------------------------- matching

def norm_name(name: str, ecosystem: str = "") -> str:
    n = str(name or "").strip().lower()
    if ecosystem.lower() == "pypi":
        n = re.sub(r"[-_.]+", "-", n)
    return n


def _eco(e: str) -> str:
    e = (e or "").lower()
    return {"pip": "pypi", "python": "pypi", "node": "npm", "cargo": "crates.io", "crates": "crates.io",
            "golang": "go", "go": "go"}.get(e, e)


def load_watchlist(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _watch_index(w: dict) -> dict:
    pkgs: dict[tuple[str, str], dict] = {}
    for p in w.get("packages") or []:
        pkgs.setdefault((_eco(p.get("ecosystem", "")), norm_name(p.get("name", ""), p.get("ecosystem", ""))), p)
    names = {norm_name(p.get("name", "")).rsplit("/", 1)[-1] for p in w.get("packages") or []}
    products = {str(x).lower() for x in w.get("products") or []}
    for s in w.get("mcp_servers") or []:
        products.add(str(s.get("name", "")).lower())
        if s.get("package"):
            products.add(str(s["package"]).lower())
    harness_terms = {t for h in w.get("harnesses") or [] for t in HARNESS_NAMES.get(h, [h])}
    return {"pkgs": pkgs, "names": names, "products": products - {""}, "harness": harness_terms,
            "vendors": {str(v).lower() for v in w.get("vendors") or []}}


def _word_in(term: str, text: str) -> bool:
    return bool(re.search(r"(?<![\w-])" + re.escape(term.lower()) + r"(?![\w-])", text))


def _fixed_note(pkg: dict) -> str:
    return f"; fixed in {', '.join(pkg['fixed'])}" if pkg.get("fixed") else ""


def score_item(item: dict, watchlist: dict, _index: dict | None = None) -> dict:
    """Return {"score": 0-100, "reasons": [...], "matched_packages": [...], "affected": ...}."""
    idx = _index or _watch_index(watchlist)
    title = item.get("title") or ""
    text = " ".join([title, item.get("summary") or "", " ".join(item.get("entities") or []),
                     " ".join(item.get("products") or [])]).lower()
    ctypes = set(item.get("change_types") or [])
    reasons: list[str] = []
    matched: list[str] = []

    for topic in watchlist.get("excluded_topics") or []:
        if _word_in(str(topic), text):
            return {"score": 0, "reasons": [f"excluded topic '{topic}'"], "matched_packages": [], "affected": "unknown"}
    wanted = set(watchlist.get("change_types") or [])
    if wanted and not wanted & ctypes:
        return {"score": 0, "reasons": ["change type not in the watchlist's change_types"], "matched_packages": [],
                "affected": "unknown"}

    score = 0
    affected = "unknown"
    rank_aff = {"unknown": 0, "no": 1, "maybe": 2, "yes": 3}
    is_release_only = not ctypes & ACTION_TYPES

    for ap in item.get("affected_packages") or []:
        eco = _eco(ap.get("ecosystem", ""))
        name = ap.get("name", "")
        rng = ap.get("version_range") or "*"
        if eco == "cpe":
            flat = lambda x: re.sub(r"[-_.]+", "-", x.lower())  # noqa: E731
            product = flat(name.split(":", 1)[-1])
            hit = next((p for (e, n), p in idx["pkgs"].items() if flat(n.rsplit("/", 1)[-1]) == product), None)
            if hit is None and product not in {flat(x) for x in idx["products"]}:
                continue
            key = (_eco(hit["ecosystem"]), norm_name(hit["name"], hit["ecosystem"])) if hit else None
            eco = key[0] if key else eco
            watch = hit
        else:
            watch = idx["pkgs"].get((eco, norm_name(name, eco)))
            if watch is None:
                continue
        label = f"{watch['name'] if watch else name}"
        src = f" ({watch['source_file']})" if watch and watch.get("source_file") else ""
        matched.append(f"{ap.get('ecosystem')}:{name}")
        pinned = (watch or {}).get("pinned")
        spec = (watch or {}).get("version")
        release_of = re.fullmatch(r"==\s*v?(.+)", rng)
        if release_of and is_release_only:
            ver = release_of.group(1)
            score = max(score, 40)
            note = f"new release {name} {ver} of a dependency{src}"
            inside = version_in_spec(ver, spec, eco) if spec else None
            if pinned and parse_version(ver) and parse_version(pinned) and parse_version(ver) <= parse_version(pinned):
                note += f" (you already pin {pinned})"
                score = max(score - 25, 15)
            elif inside is False:
                note += f"; outside your allowed range {spec}, so upgrading needs a manifest change"
            reasons.append(note)
            continue
        if pinned:
            inside = version_in_spec(pinned, rng, eco)
            if inside:
                score = max(score, 70)
                aff = "yes"
                reasons.append(f"{label}=={pinned}{src} is inside the affected range {rng}{_fixed_note(ap)}")
            elif inside is False:
                score = max(score, 20)
                aff = "no"
                reasons.append(f"{label}=={pinned}{src} is outside the affected range {rng}")
            else:
                score = max(score, 45)
                aff = "maybe"
                reasons.append(f"{label}{src} matches; could not compare version {pinned} with {rng}")
        elif spec:
            overlap = specs_overlap(spec, rng, eco)
            if overlap:
                score = max(score, 55)
                aff = "maybe"
                reasons.append(f"{label} {spec}{src} allows versions in the affected range {rng}{_fixed_note(ap)}")
            elif overlap is False:
                score = max(score, 20)
                aff = "no"
                reasons.append(f"{label} {spec}{src} excludes the affected range {rng}")
            else:
                score = max(score, 45)
                aff = "maybe"
                reasons.append(f"{label}{src} matches; range {spec} not comparable with {rng}")
        else:
            score = max(score, 50)
            aff = "maybe"
            reasons.append(f"{label}{src} is a dependency with no version constraint; affected range {rng}")
        if rank_aff[aff] > rank_aff[affected]:
            affected = aff

    prods = {str(p).lower() for p in item.get("products") or []}
    prod_hits = sorted((prods & idx["products"]) | {p for p in prods if p.rsplit("/", 1)[-1] in idx["names"]})
    if not matched:
        prod_hits += sorted(t for t in idx["products"] if len(t) > 3 and t not in prod_hits and _word_in(t, title.lower()))
    if prod_hits and not matched:
        score = max(score, 35)
        reasons.append(f"product {', '.join(prod_hits[:3])} is on the watchlist")
    harness_hits = sorted(t for t in idx["harness"] if _word_in(t, text))
    if harness_hits:
        score = max(score, 35) + (5 if score >= 35 else 0)
        reasons.append(f"mentions harness {harness_hits[0]} used by this project")
    vendor = (item.get("vendor") or "").lower()
    if vendor and vendor in idx["vendors"]:
        score = score + 10 if score else 30
        reasons.append(f"vendor {item.get('vendor')} is on the watchlist")
    topics = [t for t in watchlist.get("topics") or [] if _word_in(str(t), text)]
    if topics:
        score += min(24, 8 * len(topics)) if score else min(30, 15 + 5 * (len(topics) - 1))
        reasons.append(f"topic {', '.join(topics[:3])}")

    if score == 0:
        return {"score": 0, "reasons": ["no watchlist match"], "matched_packages": [], "affected": "unknown"}

    if "security" in ctypes:
        score += 10
        sev = item.get("severity")
        floor = SEVERITY_ORDER.get(watchlist.get("min_severity", "low"), 1)
        if sev in SEVERITY_ORDER and SEVERITY_ORDER[sev] < floor:
            score = min(score, 15)
            reasons.append(f"severity {sev} is below the watchlist minimum {watchlist.get('min_severity')}")
        elif sev in ("high", "critical"):
            score += 5
            reasons.append(f"severity {sev}")
        if "known-exploited" in (item.get("entities") or []):
            score += 10
            reasons.append("listed as known exploited (CISA KEV)")
    if "breaking-change" in ctypes:
        score += 10
        reasons.append("marked as a breaking change")
    if "deprecation" in ctypes:
        score += 8
        reasons.append("announces a deprecation or end of life")
    if affected == "no":
        score = min(score, 25)
    if "prerelease" in (item.get("entities") or []) and not watchlist.get("include_prereleases"):
        score = max(0, score - 25)
        reasons.append("pre-release (lowered; set include_prereleases to keep)")
    return {"score": int(max(0, min(100, score))), "reasons": reasons, "matched_packages": matched, "affected": affected}


def rank(items: list[dict], watchlist: dict, *, min_score: int | None = None) -> list[dict]:
    """Copies of ``items`` with ``relevance`` filled, filtered by min_score, best first."""
    threshold = watchlist.get("min_score", 30) if min_score is None else min_score
    idx = _watch_index(watchlist)
    out = []
    for it in items:
        rel = score_item(it, watchlist, idx)
        if rel["score"] >= threshold:
            out.append(dict(it, relevance=rel))
    out.sort(key=lambda i: (i["relevance"]["score"], i.get("published") or ""), reverse=True)
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Score items (JSON list) against a watchlist.")
    ap.add_argument("items")
    ap.add_argument("watchlist")
    ap.add_argument("--min-score", type=int)
    a = ap.parse_args(argv)
    items = json.loads(Path(a.items).read_text())
    json.dump(rank(items, load_watchlist(a.watchlist), min_score=a.min_score), sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
