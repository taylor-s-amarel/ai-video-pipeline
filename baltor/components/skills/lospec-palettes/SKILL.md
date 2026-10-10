---
name: "lospec-palettes"
description: "Use when a pixel-art scene, thumbnail or mixed asset kit needs one coherent palette. Lospec hosts 2,500+ palettes downloadable as HEX, GPL, PAL, ASE, TXT and PNG; pages credit an author but state no licence. Covers choosing a palette, crediting its author and enforcing it with the quantiser module."
---

# Lospec pixel-art palettes

Use when a pixel-art scene, thumbnail or mixed asset kit needs one coherent palette. Lospec hosts 2,500+ palettes downloadable as HEX, GPL, PAL, ASE, TXT and PNG; pages credit an author but state no licence. Covers choosing a palette, crediting its author and enforcing it with the quantiser module.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Palette pages name an author and offer downloads but state no licence. Credit the palette author by convention; the palette is a list of colours, the artwork you make with it is yours.

- `No licence stated`: palette pages - <https://lospec.com/palette-list>

Attribution: **optional**. Redistribution of the files: **per-asset**.
Commercial use: **allowed**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
Palette: {palette} by {author} (lospec.com)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Palette list](https://lospec.com/palette-list)
- [Endesga 32](https://lospec.com/palette-list/endesga-32)
- [Resurrect 64](https://lospec.com/palette-list/resurrect-64)
- [Sweetie 16](https://lospec.com/palette-list/sweetie-16)
- [Lospec GB (4 colours)](https://lospec.com/palette-list/lospec-gb)

## How to search

Filter by colour count (4 for a handheld look, 16 or 32 for most kits). Download the .hex file and run
`lospec_palette_quantiser quantise art.png --palette endesga-32.hex --out art_e32.png`, then `check` every
exported frame so off-palette pixels from mixed packs are caught.

## Import into Godot 4

- Keep palette-quantised textures lossless (`pixel-art-2d`); VRAM compression shifts colours off-palette.

## Import into Blender

- Use the palette PNG as a 1-pixel-high gradient texture for flat-shaded low-poly materials.

## Pitfalls

- No licence is stated: do not redistribute palette files as your own product; credit the author.
- Dithering looks noisy when scaled for video; prefer no dither or Bayer 4x4 at low strength.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "endesga-32",
  "title": "Endesga 32 palette",
  "creator": "ENDESGA",
  "source_url": "https://lospec.com/palette-list/endesga-32",
  "licence": "No licence stated (credit author)",
  "licence_url": "https://lospec.com/palette-list/endesga-32",
  "attribution": "Palette: Endesga 32 by ENDESGA (lospec.com)",
  "attribution_required": false,
  "redistribution": "project-only",
  "format": "hex",
  "intended_use": [
    "palette for the whole pixel kit"
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
