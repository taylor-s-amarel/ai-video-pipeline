"""Media asset manifest: every image, clip and track with licence and credit.

A manifest entry records where an asset came from (URL), who made it, the
exact licence identifier, the credit line to publish, the local file's
SHA-256, and how it is used. ``validate`` checks entries against simple
licence rules:

* licence must be a known identifier (CC0-1.0, CC-BY-4.0, CC-BY-SA-4.0,
  Public-Domain-Mark, Pexels-License, Pixabay-Content-License, own-work,
  licensed-commercial, ...) or explicitly marked custom with a terms URL;
* CC BY / BY-SA need an author and a credit line;
* NonCommercial and NoDerivatives licences are flagged for commercial or
  edited use;
* "fair use" is not a licence and is rejected as one.

Usage::

    from media_asset_manifest import Asset, validate, credits_block
    assets = [Asset("music/with-these-hands.mp3", "audio", "CC-BY-4.0", author="Scott Buckley",
                    title="With These Hands", source_url="https://www.scottbuckley.com.au/library/with-these-hands/")]
    validate(assets, commercial=True, edited=True)
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

KNOWN = {"CC0-1.0", "CC-BY-4.0", "CC-BY-3.0", "CC-BY-SA-4.0", "CC-BY-SA-3.0", "CC-BY-NC-4.0", "CC-BY-ND-4.0",
         "CC-BY-NC-SA-4.0", "CC-BY-NC-ND-4.0", "Public-Domain-Mark", "Pexels-License", "Pixabay-Content-License",
         "Unsplash-License", "own-work", "licensed-commercial", "custom"}


@dataclass
class Asset:
    path: str
    kind: str                     # image, video, audio, font, other
    licence: str
    author: str = ""
    title: str = ""
    source_url: str = ""
    credit: str = ""
    sha256: str = ""
    terms_url: str = ""
    usage: str = ""


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cc_name(licence: str) -> str:
    """'CC-BY-SA-4.0' -> 'CC BY-SA 4.0' (the form used in credit lines)."""
    parts = licence.split("-")
    return f"CC {'-'.join(parts[1:-1])} {parts[-1]}"


def default_credit(a: Asset) -> str:
    title = a.title or a.path
    if a.licence.startswith("CC-BY"):
        src = f" ({a.source_url})" if a.source_url else ""
        return f"\u201c{title}\u201d by {a.author}{src}, licensed {cc_name(a.licence)}"
    if a.licence == "CC0-1.0":
        return f"\u201c{title}\u201d by {a.author or 'unknown'} (CC0 1.0)"
    return ""


def validate(assets: list[Asset], commercial: bool = True, edited: bool = True) -> list[str]:
    probs = []
    for a in assets:
        lic = a.licence.strip()
        if lic.lower().replace(" ", "-") in ("fair-use", "fairuse"):
            probs.append(f"{a.path}: 'fair use' is a legal defence decided case by case, not a licence")
            continue
        if lic not in KNOWN:
            probs.append(f"{a.path}: unknown licence {lic!r}")
            continue
        if lic == "custom" and not a.terms_url:
            probs.append(f"{a.path}: custom licence needs terms_url")
        if lic.startswith("CC-BY") and (not a.author or not (a.credit or a.title)):
            probs.append(f"{a.path}: {lic} requires attribution (author and title or credit line)")
        if "-NC" in lic and commercial:
            probs.append(f"{a.path}: {lic} does not allow commercial use")
        if "-ND" in lic and edited:
            probs.append(f"{a.path}: {lic} does not allow sharing edited versions")
        if lic.startswith(("CC-BY", "CC0", "Pexels", "Pixabay", "Unsplash")) and not a.source_url:
            probs.append(f"{a.path}: record the source_url")
        if "-SA" in lic and edited:
            probs.append(f"{a.path}: {lic} requires adaptations to be shared under the same licence; check the output licence")
    return probs


def credits_block(assets: list[Asset]) -> str:
    lines = []
    for a in assets:
        c = a.credit or default_credit(a)
        if c and c not in lines:
            lines.append(c)
    return "\n".join(lines)


def to_records(assets: list[Asset]) -> list[dict]:
    return [asdict(a) for a in assets]
