---
name: "open-icon-sets-for-ui"
description: "Use when captions, lower thirds, explainer diagrams or Godot UI need clean interface icons. Lucide (ISC), Tabler (MIT), Phosphor (MIT) and Material Symbols (Apache-2.0) need no on-screen credit; Font Awesome Free icons are CC BY 4.0. Covers choosing a set, fetching SVGs and keeping notices."
---

# Open UI icon sets (Lucide, Tabler, Phosphor, Material Symbols, Font Awesome Free)

Use when captions, lower thirds, explainer diagrams or Godot UI need clean interface icons. Lucide (ISC), Tabler (MIT), Phosphor (MIT) and Material Symbols (Apache-2.0) need no on-screen credit; Font Awesome Free icons are CC BY 4.0. Covers choosing a set, fetching SVGs and keeping notices.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Lucide ISC; Tabler Icons MIT; Phosphor MIT; Material Symbols/Icons Apache-2.0 (attribution appreciated, not required); Font Awesome Free icons CC BY 4.0, fonts OFL 1.1, code MIT. Iconify lists each set's licence.

- `ISC`: Lucide - <https://github.com/lucide-icons/lucide>
- `MIT`: Tabler Icons - <https://github.com/tabler/tabler-icons>
- `MIT`: Phosphor - <https://github.com/phosphor-icons/core>
- `Apache-2.0`: Material Symbols and Icons - <https://github.com/google/material-design-icons>
- `CC-BY-4.0`: Font Awesome Free icons - <https://fontawesome.com/license/free>

Attribution: **per-asset**. Redistribution of the files: **allowed-with-licence**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
Icons: {set} ({licence})
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Iconify icon sets and licences](https://github.com/iconify/icon-sets)
- [Lucide](https://github.com/lucide-icons/lucide)
- [Tabler Icons](https://github.com/tabler/tabler-icons)
- [Font Awesome Free licence](https://fontawesome.com/license/free)

## How to search

Choose one set per video for a consistent stroke width. Fetch SVGs from the set's GitHub repository (raw URLs) and
record the set and licence in the manifest; no on-screen credit is needed for ISC/MIT/Apache sets.

## Import into Godot 4

- Import SVG with `ui-lossless` and a higher svg/scale for 4K-safe icons, or use Material Symbols as a font.

## Import into Blender

- Import SVG as curves for extruded 3D icons (File > Import > Scalable Vector Graphics).

## Pitfalls

- Keep the licence notice file when you redistribute icon files (MIT/ISC/Apache).
- Font Awesome Pro icons are not free; an SVG copied from the website may carry a Pro header.
- Mixing outline and filled sets in one frame looks noisy; stay in one family.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "tabler-check",
  "title": "Tabler check icon",
  "creator": "Tabler Icons",
  "source_url": "https://github.com/tabler/tabler-icons",
  "licence": "MIT",
  "licence_url": "https://github.com/tabler/tabler-icons",
  "attribution": "Icons: Tabler Icons (MIT)",
  "attribution_required": false,
  "redistribution": "allowed-with-licence",
  "format": "svg",
  "intended_use": [
    "winner tick on a comparison board"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "to-fetch"
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
