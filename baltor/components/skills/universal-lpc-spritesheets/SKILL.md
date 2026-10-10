---
name: "universal-lpc-spritesheets"
description: "Use when a top-down RPG or explainer needs layered 2D characters with walk, slash, cast and shoot animations from the Universal LPC Spritesheet Character Generator. Every layer has its own licence; this skill shows how to export the credits, meet share-alike/GPL duties and import into Godot."
---

# Universal LPC sprite sheets (CC0 / CC-BY / CC-BY-SA / OGA-BY / GPL per layer)

Use when a top-down RPG or explainer needs layered 2D characters with walk, slash, cast and shoot animations from the Universal LPC Spritesheet Character Generator. Every layer has its own licence; this skill shows how to export the credits, meet share-alike/GPL duties and import into Godot.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Each image is available under one or more of CC0, CC-BY, CC-BY-SA, OGA-BY or GPL. Credit all authors except for CC0 art; CC-BY-SA derivatives must be CC-BY-SA 4.0+, GPL derivatives GPL 3.0+; CC-BY/CC-BY-SA may not be DRM-protected, OGA-BY may.

- `per-asset`: every layer, listed in CREDITS.csv - <https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator>

Attribution: **required**. Redistribution of the files: **allowed-with-licence**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Required. Fill in the braces from each asset page and use the line verbatim:

```
Sprites contributed as part of the Liberated Pixel Cup project from OpenGameArt.org; authors: {authors from the exported credits}
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Generator repository (README, CREDITS.csv)](https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator)
- [LPC collection on OpenGameArt](https://opengameart.org/content/liberated-pixel-cup-0)
- [LPC style guide](https://lpc.opengameart.org/static/LPC-Style-Guide/build/styleguide.html)

## How to search

Build the character in the generator (hosted from the repository's GitHub Pages), export the sprite sheet and the
licence/credits file for exactly the layers you used, and paste the authors into the manifest's attribution.

## Import into Godot 4

- Import with `pixel-art-2d`; LPC frames are 64x64 on a grid: `sprite_sheet_slicer grid sheet.png --size 64x64`
  then build one SpriteFrames animation per row (walk up/left/down/right ...).

## Import into Blender

- Use Images as Planes with Closest interpolation for 2.5D scenes.

## Pitfalls

- Ship the exported credits (or CREDITS.csv) where users can find them, e.g. a credits screen or the video description link.
- Share-alike layers make derived sprites share-alike too; keep them out of packages with other licences.
- Older forks state different licences (GPL 3.0 and CC-BY-SA 3.0 only); use the upstream credits for the copy you used.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "lpc-hero",
  "title": "LPC hero sprite sheet",
  "creator": "Liberated Pixel Cup contributors (see credits)",
  "source_url": "https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator",
  "licence": "CC-BY-SA-4.0 / GPL-3.0 (per exported credits)",
  "licence_url": "https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator",
  "attribution": "Sprites contributed as part of the Liberated Pixel Cup project from OpenGameArt.org; authors listed in CREDITS-lpc.txt",
  "attribution_required": true,
  "redistribution": "allowed-with-licence",
  "format": "png",
  "intended_use": [
    "top-down narrator character"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "to-fetch"
  },
  "import_hints": {
    "godot": {
      "importer": "texture",
      "preset": "pixel-art-2d"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
