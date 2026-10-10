---
name: "game-icons-net"
description: "Use when a thumbnail, caption, 'this vs that' board or game UI needs crisp single-colour SVG icons. game-icons.net icons are CC BY 3.0 per author; this skill gives the exact credit line, scripted download from GitHub, recolouring, and Godot/Blender import."
---

# game-icons.net SVG icons (CC BY 3.0)

Use when a thumbnail, caption, 'this vs that' board or game UI needs crisp single-colour SVG icons. game-icons.net icons are CC BY 3.0 per author; this skill gives the exact credit line, scripted download from GitHub, recolouring, and Godot/Blender import.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Icons are provided under Creative Commons BY 3.0; credit the original author, e.g. 'Icons made by {author}. Available on https://game-icons.net'.

- `CC-BY-3.0`: all icons - <https://game-icons.net/about.html>

Attribution: **required**. Redistribution of the files: **allowed-with-licence**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Required. Fill in the braces from each asset page and use the line verbatim:

```
Icons made by {author}. Available on https://game-icons.net (CC BY 3.0)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [About and licence](https://game-icons.net/about.html)
- [Source SVGs by author](https://github.com/game-icons/icons)
- [Iconify browser for the set](https://icon-sets.iconify.design/game-icons/)

## How to search

Search on Iconify or the site, note the author, then download `https://raw.githubusercontent.com/game-icons/icons/master/<author>/<icon>.svg`
with the `media_pack_fetcher` module. Recolour by editing the SVG fill; keep the credit line.

## Import into Godot 4

- SVGs import as textures (rasterised at import; set svg/scale for crisp large icons) with the `ui-lossless` preset.

## Import into Blender

- File > Import > Scalable Vector Graphics, or render the PNG and use Images as Planes.

## Pitfalls

- Credit per author (the GitHub folder name), not just the site.
- CC BY 3.0 forbids adding DRM that restricts the licence; fine for videos, check for locked platforms.
- A 'free icons' compilation that re-hosts game-icons without credit does not remove your duty to credit.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "crossed-swords",
  "title": "Crossed swords icon",
  "creator": "Lorc",
  "source_url": "https://game-icons.net/about.html",
  "download_url": "https://raw.githubusercontent.com/game-icons/icons/master/lorc/crossed-swords.svg",
  "licence": "CC-BY-3.0",
  "licence_url": "https://creativecommons.org/licenses/by/3.0/deed.en",
  "attribution": "Icon by Lorc. Available on https://game-icons.net (CC BY 3.0)",
  "attribution_required": true,
  "redistribution": "allowed-with-licence",
  "format": "svg",
  "file_name": "crossed-swords.svg",
  "intended_use": [
    "versus divider icon"
  ],
  "fetch": {
    "method": "direct",
    "status": "to-fetch"
  },
  "import_hints": {
    "godot": {
      "importer": "texture",
      "preset": "ui-lossless"
    },
    "video": {
      "role": "icon"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
