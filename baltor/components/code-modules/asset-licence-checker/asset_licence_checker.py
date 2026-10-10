"""Check a media pack manifest against how you intend to use it.

Reads an ``agent_media_pack_manifest`` (``spec: baltor.media-pack/v1``) and a
use profile, and reports each asset that would break its licence. It encodes
the rules that most often go wrong with free assets:

* NonCommercial (``-NC-``) assets in monetised videos or client work.
* NoDerivatives (``-ND-``) assets that you plan to recolour, retexture,
  re-rig or crop into something new.
* Raw files whose licence forbids redistribution (Mixamo, store EULAs,
  BlenderKit Royalty Free, Fab) committed to a public repo or a package.
* Attribution licences (CC-BY*, OGA-BY, ...) with no credit line recorded.
* ShareAlike / GPL obligations when you ship modified assets.
* CC-BY 3.0 / CC-BY-SA / GPL art on DRM platforms (OpenGameArt's FAQ warns
  that these forbid technical restrictions; OGA-BY was made to allow them).
* AI-training use when the terms forbid it or say nothing.
* Unknown or custom licences that need a human to read the terms.

This is a checklist, not legal advice: a PASS means none of these rules fired.

Usage::

    python asset_licence_checker.py pack.json --use monetised-video [--modified asset-id ...] [--json]

Profiles: monetised-video, client-work, open-source-repo, baltor-package, drm-platform-game, ai-training,
personal-study. Exit status 1 when any finding is an error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PROFILES = {
    "monetised-video": {"commercial": True, "redistributes_files": False, "modifies": False, "drm": False, "ai_training": False},
    "client-work": {"commercial": True, "redistributes_files": False, "modifies": True, "drm": False, "ai_training": False},
    "open-source-repo": {"commercial": False, "redistributes_files": True, "modifies": True, "drm": False, "ai_training": False},
    "baltor-package": {"commercial": True, "redistributes_files": True, "modifies": False, "drm": False, "ai_training": False},
    "drm-platform-game": {"commercial": True, "redistributes_files": True, "modifies": True, "drm": True, "ai_training": False},
    "ai-training": {"commercial": True, "redistributes_files": False, "modifies": True, "drm": False, "ai_training": True},
    "personal-study": {"commercial": False, "redistributes_files": False, "modifies": True, "drm": False, "ai_training": False},
}

PUBLIC_DOMAIN = re.compile(r"\b(CC0|CC-PDDC|Public[- ]domain|Unlicense|without copyright)\b", re.I)
PERMISSIVE_CODE = re.compile(r"^(MIT|ISC|BSD-[23]-Clause|Zlib|Apache-2\.0)\b", re.I)
ATTRIBUTION = re.compile(r"\b(CC-BY|CC BY|OGA-BY|GPL|LGPL|AGPL)\b", re.I)
SHARE_ALIKE = re.compile(r"(-SA\b|BY-SA|\bGPL|\bAGPL|\bLGPL|Lottie Simple License)", re.I)
NON_COMMERCIAL = re.compile(r"(-NC\b|-NC-|NonCommercial|non-commercial)", re.I)
NO_DERIVS = re.compile(r"(-ND\b|-ND-|NoDerivatives)", re.I)
NO_DRM = re.compile(r"(CC-BY-3\.0|CC BY 3\.0|CC-BY-SA|CC BY-SA|\bGPL)", re.I)
FONT_LICENCE = re.compile(r"\b(OFL|UFL)\b", re.I)
CUSTOM = re.compile(r"(EULA|Adobe|Mixamo|Royalty Free|Fab Standard|Custom|terms|Spine|Lottie Simple)", re.I)


@dataclass
class Finding:
    level: str  # error | warning | info
    asset_id: str
    rule: str
    message: str


def licence_flags(licence: str) -> dict:
    lic = licence or ""
    return {
        "public_domain": bool(PUBLIC_DOMAIN.search(lic)),
        "permissive_code": bool(PERMISSIVE_CODE.search(lic)),
        "attribution": bool(ATTRIBUTION.search(lic)),
        "share_alike": bool(SHARE_ALIKE.search(lic)),
        "non_commercial": bool(NON_COMMERCIAL.search(lic)),
        "no_derivatives": bool(NO_DERIVS.search(lic)),
        "no_drm": bool(NO_DRM.search(lic)) and not re.search(r"OGA-BY", lic, re.I),
        "font": bool(FONT_LICENCE.search(lic)),
        "custom": bool(CUSTOM.search(lic)),
    }


def check_asset(asset: dict, profile: dict, modified: bool) -> list[Finding]:
    aid = str(asset.get("id", "?"))
    lic = str(asset.get("licence", ""))
    f = licence_flags(lic)
    out: list[Finding] = []
    known = f["public_domain"] or f["permissive_code"] or f["attribution"] or f["font"] or f["custom"]
    if not lic or not asset.get("licence_url"):
        out.append(Finding("error", aid, "licence-recorded", "licence or licence_url missing: find the terms before use"))
    elif not known:
        out.append(Finding("warning", aid, "licence-known", f"unrecognised licence {lic!r}: a human must read {asset.get('licence_url')}"))
    if f["custom"] and not f["public_domain"]:
        out.append(Finding("warning", aid, "custom-terms", f"custom terms ({lic}): re-read {asset.get('licence_url')} for this use"))
    commercial_flag = asset.get("commercial_use")
    if profile["commercial"] and (f["non_commercial"] or commercial_flag == "non-commercial-only"):
        out.append(Finding("error", aid, "non-commercial", "non-commercial licence in a commercial/monetised use"))
    if modified and f["no_derivatives"]:
        out.append(Finding("error", aid, "no-derivatives", "NoDerivatives licence but the asset will be modified"))
    redistribution = asset.get("redistribution", "allowed")
    if profile["redistributes_files"] and redistribution in {"forbidden", "project-only"}:
        out.append(Finding("error", aid, "redistribution", "raw files may not be redistributed: keep them out of repos and packages; ship the manifest only"))
    needs_credit = asset.get("attribution_required", f["attribution"])
    if needs_credit and not str(asset.get("attribution", "")).strip():
        out.append(Finding("error", aid, "attribution", "attribution required but no credit line recorded"))
    if f["share_alike"] and (modified or profile["redistributes_files"]):
        out.append(Finding("warning", aid, "share-alike", "share-alike/copyleft: modified versions must use the same licence"))
    if profile["drm"] and f["no_drm"]:
        out.append(Finding("error", aid, "no-drm", f"{lic} forbids technical restrictions (DRM); find an OGA-BY/CC0 alternative or a DRM-free channel"))
    if profile["ai_training"]:
        ai = asset.get("ai_training", "unspecified")
        if ai == "forbidden":
            out.append(Finding("error", aid, "ai-training", "terms forbid use for training machine-learning models"))
        elif ai != "allowed" and not f["public_domain"]:
            out.append(Finding("warning", aid, "ai-training", "terms do not address AI training: get permission or exclude"))
    for r in asset.get("restrictions") or []:
        out.append(Finding("info", aid, "restriction", str(r)))
    return out


def check_manifest(manifest: dict, use: str, modified_ids: set[str] | None = None) -> list[Finding]:
    if use not in PROFILES:
        raise KeyError(f"unknown use profile {use!r}; choose from {sorted(PROFILES)}")
    profile = PROFILES[use]
    findings: list[Finding] = []
    if manifest.get("spec") != "baltor.media-pack/v1":
        findings.append(Finding("warning", "-", "spec", "manifest spec is not baltor.media-pack/v1"))
    modified_ids = modified_ids or set()
    for asset in manifest.get("assets", []):
        modified = asset.get("id") in modified_ids or bool(asset.get("will_modify"))
        findings += check_asset(asset, profile, modified)
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--use", required=True, choices=sorted(PROFILES))
    ap.add_argument("--modified", nargs="*", default=[], help="asset ids you will modify")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    findings = check_manifest(manifest, a.use, set(a.modified))
    errors = [x for x in findings if x.level == "error"]
    if a.json:
        print(json.dumps({"use": a.use, "errors": len(errors), "findings": [asdict(x) for x in findings]}, indent=2))
    else:
        for x in findings:
            print(f"{x.level.upper():<8} {x.asset_id:<28} {x.rule:<18} {x.message}")
        print(f"{len(errors)} error(s), {sum(x.level == 'warning' for x in findings)} warning(s) for use '{a.use}'")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
