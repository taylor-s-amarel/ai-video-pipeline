---
name: "opengameart-assets"
description: "Use when searching OpenGameArt for sprites, tiles, music or sound effects. Every submission has its own licence (CC0, CC-BY, CC-BY-SA, OGA-BY, GPL); this skill explains reading it, building credits in the artist's requested format, share-alike and DRM clauses, and LPC-style collections."
---

# OpenGameArt (per-asset licences)

Use when searching OpenGameArt for sprites, tiles, music or sound effects. Every submission has its own licence (CC0, CC-BY, CC-BY-SA, OGA-BY, GPL); this skill explains reading it, building credits in the artist's requested format, share-alike and DRM clauses, and LPC-style collections.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Each OpenGameArt submission has its own licence (CC0, CC-BY, CC-BY-SA, OGA-BY, GPL ...). You may use art commercially if you follow its licence. Credit in the artist's 'Copyright/Attribution Notice' format when one is given.

- `per-asset`: every submission - <https://opengameart.org/content/faq>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
"{title}" by {creator} (opengameart.org), {licence}
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [FAQ and licences](https://opengameart.org/content/faq)
- [Liberated Pixel Cup collection](https://opengameart.org/content/liberated-pixel-cup-0)
- [512 retro sound effects (CC0)](https://opengameart.org/content/512-sound-effects-8-bit-style)

## How to search

Use the site search with a licence filter, open each result and copy the licence and the attribution notice
into the media pack manifest. Prefer CC0 for packages and repositories; CC-BY is fine for videos with credits.

## Import into Godot 4

- Pixel art: `godot_texture_import_presets` with `pixel-art-2d`; slice sheets with `sprite_sheet_slicer`.
- Audio: OGG for music loops (enable Loop in the import dock), WAV for short effects.

## Import into Blender

- 2D sprites as planes: File > Import > Images as Planes; set interpolation to Closest for pixel art.

## Pitfalls

- CC-BY 3.0 and CC-BY-SA forbid adding technical restrictions (DRM); OGA-BY exists to allow DRM platforms.
- Collections mix licences; credit every contributing author.
- Mirrors can disagree with the original (Pixel Adventure is CC0 on itch.io, CC-BY 4.0 on OGA).
- Share-alike art that you modify must be released under the same licence; keep it out of packages that use another licence.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "oga-512-sfx",
  "title": "512 Sound Effects (8-bit style)",
  "creator": "SubspaceAudio",
  "source_url": "https://opengameart.org/content/512-sound-effects-8-bit-style",
  "licence": "CC0-1.0",
  "licence_url": "https://opengameart.org/content/512-sound-effects-8-bit-style",
  "attribution": "512 Sound Effects (8-bit style) by SubspaceAudio, CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "zip",
  "intended_use": [
    "retro UI and pickup sounds"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "to-fetch"
  },
  "import_hints": {
    "video": {
      "role": "sfx"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
