---
name: "isometric-town-kit"
description: "Use when a short or Godot scene shows a town, city plan or map in 2D isometric view. Lists CC0 Kenney isometric tiles and blocks, the MIT Godot isometric demo for depth sorting, caption fonts and CC0 sounds."
---

# Isometric town kit (2D tiles)

Use when a short or Godot scene shows a town, city plan or map in 2D isometric view. Lists CC0 Kenney isometric tiles and blocks, the MIT Godot isometric demo for depth sorting, caption fonts and CC0 sounds.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `kenney-isometric-tiles-city` | [Isometric Tiles City](https://kenney.nl/assets/isometric-tiles-city) | CC0-1.0 | optional | allowed | manual-page | no | roads, buildings and parks |
| `kenney-isometric-blocks` | [Isometric Blocks](https://kenney.nl/assets/isometric-blocks) | CC0-1.0 | optional | allowed | manual-page | no | terrain blocks |
| `godot-demo-2d-isometric` | [Godot demo: 2D isometric](https://github.com/godotengine/godot-demo-projects/tree/master/2d/isometric) | MIT | optional | allowed-with-licence | git | no | depth sorting reference |
| `font-inter` | [Inter](https://fonts.google.com/specimen/Inter) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | labels above buildings |
| `kenney-interface-sounds` | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | CC0-1.0 | optional | allowed | manual-page | no | label pops |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/isometric-town-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/isometric-town-kit             # direct assets only
python3 asset_licence_checker.py assets/isometric-town-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Build the town on an isometric TileMapLayer; pan slowly across it while labels pop above buildings.

## Assemble

1. Import tiles with `smooth-2d` (these are not pixel-art sized); create an isometric TileSet.
2. Use the Godot isometric demo's Y-sort setup so characters pass behind buildings.

## Do not use

- Nothing specific beyond the house licence rules.
