---
name: "godot-official-demos"
description: "Use when you need a working Godot 4 reference for a mechanic (2D/3D platformer, isometric sorting, AStarGrid2D navigation, voxel terrain, RPG dialogue) to copy into a short's scene. Demo code is MIT; some demos bundle CC-BY/CC-BY-SA art and music credited in their READMEs."
---

# Godot official demo projects and TPS demo

Use when you need a working Godot 4 reference for a mechanic (2D/3D platformer, isometric sorting, AStarGrid2D navigation, voxel terrain, RPG dialogue) to copy into a short's scene. Demo code is MIT; some demos bundle CC-BY/CC-BY-SA art and music credited in their READMEs.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

godot-demo-projects is MIT. Bundled third-party textures, fonts and music keep their own licences (e.g. the voxel demo's Minetest textures are CC BY-SA 3.0/CC0). The TPS demo's code is MIT and its assets and music CC-BY 3.0.

- `MIT`: demo code - <https://github.com/godotengine/godot-demo-projects/blob/master/LICENSE.md>
- `CC-BY-3.0`: TPS demo assets and music - <https://raw.githubusercontent.com/godotengine/tps-demo/master/LICENSE.md>

Attribution: **per-asset**. Redistribution of the files: **allowed-with-licence**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
Based on Godot demo projects (MIT); assets per demo README
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Demo repository](https://github.com/godotengine/godot-demo-projects)
- [2D platformer](https://github.com/godotengine/godot-demo-projects/tree/master/2d/platformer)
- [Isometric](https://github.com/godotengine/godot-demo-projects/tree/master/2d/isometric)
- [AStarGrid2D navigation](https://github.com/godotengine/godot-demo-projects/tree/master/2d/navigation_astar)
- [TPS demo](https://github.com/godotengine/tps-demo)

## How to search

Clone the repo (or sparse-checkout one folder), open the demo in the matching Godot version, and copy only the
scripts you need. Replace bundled art with CC0 kit art when the demo's art licence does not fit.

## Import into Godot 4

- The 2D platformer demo's project settings (default_texture_filter=0, integer stretch scale) are the reference
  pixel-art setup that the `godot_texture_import_presets` module writes.

## Import into Blender

- Not applicable.

## Pitfalls

- Read each demo's README credits before reusing its art or music.
- Demos track the current stable Godot; older engine versions need the matching branch.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "godot-navigation-astar",
  "title": "AStarGrid2D navigation demo",
  "creator": "Godot Engine contributors",
  "source_url": "https://github.com/godotengine/godot-demo-projects/tree/master/2d/navigation_astar",
  "licence": "MIT",
  "licence_url": "https://github.com/godotengine/godot-demo-projects/blob/master/LICENSE.md",
  "attribution": "Based on the Godot AStarGrid2D demo (MIT)",
  "attribution_required": false,
  "redistribution": "allowed-with-licence",
  "format": "zip",
  "intended_use": [
    "maze pathfinding for the top-down maze kit"
  ],
  "fetch": {
    "method": "git",
    "status": "to-fetch"
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
