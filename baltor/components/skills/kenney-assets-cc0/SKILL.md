---
name: "kenney-assets-cc0"
description: "Use when a project needs free, consistent 2D sprites, tiles, UI, 3D low-poly kits, fonts or sound effects with no attribution duty: Kenney's packs are CC0. Covers finding the right pack, the optional credit line, Godot 4 and Blender import, and pitfalls (logo use, paid All-in-1 bundle)."
---

# Kenney game assets (CC0)

Use when a project needs free, consistent 2D sprites, tiles, UI, 3D low-poly kits, fonts or sound effects with no attribution duty: Kenney's packs are CC0. Covers finding the right pack, the optional credit line, Godot 4 and Blender import, and pitfalls (logo use, paid All-in-1 bundle).

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

All game assets on Kenney's asset pages are CC0 (public domain dedication). Credit is optional. Do not use the Kenney logo, which is reserved for official projects.

- `CC0-1.0`: all asset packs on kenney.nl - <https://kenney.nl/support>
- `MIT`: code of the Godot starter kits - <https://github.com/KenneyNL/Starter-Kit-3D-Platformer>

Attribution: **optional**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
Assets by Kenney (kenney.nl), CC0
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [3D kits](https://kenney.nl/assets/category:3D)
- [Audio packs](https://kenney.nl/assets/category:Audio)
- [Tiny 16x16 series](https://kenney.nl/assets/series:Tiny)
- [Godot starter kits](https://kenney.nl/starter-kits)
- [Kenney on the Godot Asset Store](https://store.godotengine.org/publisher/kenney/)
- [KenneyNL on GitHub](https://github.com/KenneyNL)

## How to search

Open a category or series page, pick packs that share a grid (all "Tiny" packs are 16x16; Pixel Platformer is 18x18)
and download each pack's zip from its page. Packs that share a series also share a palette, so they mix cleanly.
For Godot templates, the starter kits (3D platformer, city builder, racing, FPS) are MIT code with CC0 assets.

## Import into Godot 4

- 2D pixel packs: copy PNGs under `res://art/kenney/<pack>/`, then run the `godot_texture_import_presets`
  module with `--preset pixel-art-2d` before opening the editor (Nearest filter, lossless, no mipmaps).
- Tile sheets: create a TileSet from the spritesheet PNG with the pack's tile size and spacing (read it from the
  pack's sheet or the `sprite_sheet_slicer` module's `grid` output).
- 3D kits: prefer the GLB files; drag into the scene or instance them; use the `texture-3d` preset for any
  separate textures. Most Kenney 3D kits use a shared colour-palette texture, so keep it lossless.

## Import into Blender

- `bpy.ops.import_scene.gltf(filepath="kit/Models/GLB format/tree.glb")` for GLB, `bpy.ops.import_scene.fbx` for FBX.
- Pixel-palette textures: set the Image Texture node interpolation to Closest so colours do not bleed.

## Pitfalls

- Do not use the Kenney logo or imply an official Kenney project.
- The All-in-1 bundle is a paid convenience; every pack is free from its own page.
- Input-prompt packs show console controllers: CC0 covers the art, not the platform trademarks.
- Do not rescale pixel art by non-integer factors; use `pixel_art_video_fit` for 1080x1920 frames.
- Pack versions change asset counts over time; record the version in the media pack manifest notes.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "kenney-tiny-town",
  "title": "Tiny Town",
  "creator": "Kenney",
  "source_url": "https://kenney.nl/assets/tiny-town",
  "licence": "CC0-1.0",
  "licence_url": "https://kenney.nl/support",
  "attribution": "Tiny Town by Kenney (kenney.nl), CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "zip",
  "intended_use": [
    "top-down town background",
    "maze walls"
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
