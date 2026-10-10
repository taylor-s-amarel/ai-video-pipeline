---
name: "itch-io-cc0-assets"
description: "Use when browsing itch.io for free game assets. The licence field and tags are set by each uploader, so this skill shows the CC0 filter pages, how to confirm a pack's terms, what to save as evidence, and creator examples (0x72, Pixel Frog, Ansimuz) with their fine print."
---

# itch.io free CC0 asset packs (per-pack terms)

Use when browsing itch.io for free game assets. The licence field and tags are set by each uploader, so this skill shows the CC0 filter pages, how to confirm a pack's terms, what to save as evidence, and creator examples (0x72, Pixel Frog, Ansimuz) with their fine print.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Terms are per pack. The 'Creative Commons Zero v1.0 Universal' licence filter and the cc0 tag are uploader-declared; read the pack page before use.

- `per-asset`: each pack's own licence field and description - <https://itch.io/game-assets/assets-cc0/free>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
{title} by {creator} (itch.io), {licence}
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Free assets, CC0 licence filter](https://itch.io/game-assets/assets-cc0/free)
- [2D + cc0 tag](https://itch.io/game-assets/tag-2d/tag-cc0)
- [New and popular CC0](https://itch.io/game-assets/new-and-popular/assets-cc0/free)
- [0x72 DungeonTileset II](https://0x72.itch.io/dungeontileset-ii)
- [Pixel Frog: Pixel Adventure](https://pixelfrog-assets.itch.io/pixel-adventure-1)

## How to search

Start from the licence-filter pages, open each pack, and copy the licence field and any extra conditions into
the manifest with the date. Save the page text (or a screenshot) alongside the download as evidence.

## Import into Godot 4

- Most itch.io packs are pixel art sheets: import with `pixel-art-2d` and slice with `sprite_sheet_slicer grid`.

## Import into Blender

- Use Images as Planes with Closest interpolation for 2.5D shots.

## Pitfalls

- Bundled music can have a different licence from the art (Sunny Land's music requires credit).
- Name-your-price packs are free to download, but paid extensions are not.
- Never assume 'free' means CC0.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "dungeontileset-ii",
  "title": "16x16 DungeonTileset II",
  "creator": "0x72",
  "source_url": "https://0x72.itch.io/dungeontileset-ii",
  "licence": "CC0-1.0",
  "licence_url": "https://creativecommons.org/publicdomain/zero/1.0/deed.en",
  "attribution": "16x16 DungeonTileset II by 0x72, CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "zip",
  "intended_use": [
    "top-down dungeon maze tiles and animated characters"
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
