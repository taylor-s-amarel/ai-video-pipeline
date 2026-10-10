#!/usr/bin/env python3
"""Resolve and validate creative-catalogue treatment addresses ``R-{story_id}-{format_id}-{approach_id}``.

The 10 October 2026 creative catalogue gives each of its 240 premises exactly
ten treatment rows (2,400 addresses). Four treatment groups fix which format,
representation approach, intro and motion pattern each story may use. This
module joins an address with those records, exactly as Appendix C of the
Animation and Video Production Master Guide describes. A compatible
combination is still not a screenplay: the catalogue held zero independently
written treatment scripts, zero recipe renders and zero audience studies.

Usage:
    python3 treatment_address_resolver.py R-ENT072-F08-A04      # joined record as JSON
    python3 treatment_address_resolver.py --story EDU101         # the story's ten addresses
    python3 treatment_address_resolver.py --check R-EDU101-F02-A01   # exit 1 with reasons
    python3 treatment_address_resolver.py --count                # 2400

Tables come from ``catalogue_tables.json`` next to this file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

ADDRESS = re.compile(r"^R-((?:EDU|ENT)\d{3})-(F\d{2})-(A0[1-4])$")
TABLES = json.loads(Path(__file__).with_name("catalogue_tables.json").read_text(encoding="utf-8"))
NOT_A_SCREENPLAY = "A compatible combination is still not a screenplay."


@lru_cache(maxsize=None)
def _story_group() -> dict[str, dict]:
    out = {}
    for group in TABLES["groups"]:
        for story in group["stories"]:
            out[story] = group
    return out


def parse(address: str) -> tuple[str, str, str]:
    """Split an address into (story_id, format_id, approach_id); raise ValueError when malformed."""
    m = ADDRESS.match(address.strip())
    if not m:
        raise ValueError(f"{address!r} is not of the form R-{{EDU|ENT}}NNN-FNN-ANN")
    return m.group(1), m.group(2), m.group(3)


def problems(address: str) -> list[str]:
    """Why an address is not one of the 2,400 catalogue rows (empty list when it is)."""
    try:
        story, fmt, approach = parse(address)
    except ValueError as exc:
        return [str(exc)]
    group = _story_group().get(story)
    if group is None:
        return [f"story {story} is not one of the 240 catalogue premises"]
    rows = group["rows"]
    if not any(r["format"] == fmt for r in rows):
        allowed = sorted({r["format"] for r in rows})
        return [f"treatment group {group['group']} ({story}) does not use format {fmt}; allowed: {', '.join(allowed)}"]
    if not any(r["format"] == fmt and r["approach"] == approach for r in rows):
        allowed = sorted({r["approach"] for r in rows if r["format"] == fmt})
        return [f"treatment group {group['group']} pairs {fmt} only with {', '.join(allowed)}, not {approach}"]
    return []


def is_valid(address: str) -> bool:
    return not problems(address)


def resolve(address: str) -> dict:
    """Join an address with its story, format, approach, intro and motion records."""
    errs = problems(address)
    if errs:
        raise ValueError(errs[0])
    story, fmt, approach = parse(address)
    group = _story_group()[story]
    row = next(r for r in group["rows"] if r["format"] == fmt and r["approach"] == approach)
    return {
        "address": address,
        "treatment_group": group["group"],
        "story": {"id": story, **TABLES["stories"][story]},
        "format": {"id": fmt, **TABLES["formats"][fmt]},
        "approach": {"id": approach, **TABLES["approaches"][approach]},
        "intro": {"id": row["intro"], **TABLES["intros"][row["intro"]]},
        "motion": {"id": row["motion"], **TABLES["motions"][row["motion"]]},
        "editorial_rule": TABLES["editorial_rules"].get(fmt),
        "combination_rule": TABLES["combination_rules"][TABLES["stories"][story]["family"]],
        "inherits": TABLES["combination_rules"]["every"],
        "status": "addressable candidate; " + NOT_A_SCREENPLAY,
    }


def addresses_for(story_id: str) -> list[str]:
    group = _story_group().get(story_id)
    if group is None:
        raise KeyError(f"story {story_id} is not one of the 240 catalogue premises")
    return [f"R-{story_id}-{r['format']}-{r['approach']}" for r in group["rows"]]


def all_addresses() -> list[str]:
    return [a for group in TABLES["groups"] for story in group["stories"] for a in addresses_for(story)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("address", nargs="?")
    ap.add_argument("--story", help="list the ten addresses of a story id, e.g. ENT072")
    ap.add_argument("--check", action="store_true", help="only validate the address")
    ap.add_argument("--count", action="store_true", help="print how many addresses the catalogue defines")
    a = ap.parse_args(argv)
    if a.count:
        print(len(all_addresses()))
        return 0
    if a.story:
        print("\n".join(addresses_for(a.story)))
        return 0
    if not a.address:
        ap.error("give an address, --story or --count")
    errs = problems(a.address)
    if errs:
        for e in errs:
            print(f"INVALID {a.address}: {e}", file=sys.stderr)
        return 1
    if a.check:
        print(f"VALID {a.address}")
        return 0
    print(json.dumps(resolve(a.address), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
