---
name: "top-down-maze-kit-3d"
description: "Use when the maze short should be a 3D low-poly scene seen from a high angle instead of pixel art. Swaps the tiles for KayKit Dungeon Remastered and Kenney Modular Dungeon Kit pieces and adds CC0 characters; pathfinding still runs on a grid."
---

# Top-down maze kit (3D low-poly variant)

Use when the maze short should be a 3D low-poly scene seen from a high angle instead of pixel art. Swaps the tiles for KayKit Dungeon Remastered and Kenney Modular Dungeon Kit pieces and adds CC0 characters; pathfinding still runs on a grid.

Variant of `top_down_maze_kit`: same purpose, different asset family and camera.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `kaykit-dungeon-remastered` | [KayKit Dungeon Pack Remastered (free tier)](https://kaylousberg.itch.io/kaykit-dungeon-remastered) | CC0-1.0 | optional | allowed | manual-page | no | modular dungeon walls, props and chests |
| `kenney-modular-dungeon-kit` | [Modular Dungeon Kit](https://kenney.nl/assets/modular-dungeon-kit) | CC0-1.0 | optional | allowed | manual-page | no | alternative modular rooms |
| `kaykit-skeletons-github` | [KayKit Character Pack Skeletons 1.0](https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Skeletons-1.0) | CC0-1.0 | optional | allowed | git | no | skeleton characters chasing the hero |
| `kenney-mini-characters` | [Mini Characters](https://kenney.nl/assets/mini-characters) | CC0-1.0 | optional | allowed | manual-page | no | the hero |
| `godot-demo-navigation-astar` | [Godot demo: AStarGrid2D navigation](https://github.com/godotengine/godot-demo-projects/tree/master/2d/navigation_astar) | MIT | optional | allowed-with-licence | git | no | grid pathfinding logic |
| `polyhaven-industrial-sunset-puresky` | [Industrial Sunset (Pure Sky) HDRI](https://polyhaven.com/a/industrial_sunset_puresky) | CC0-1.0 | optional | allowed | api | no | ambient lighting from above |
| `kenney-rpg-audio` | [RPG Audio](https://kenney.nl/assets/rpg-audio) | CC0-1.0 | optional | allowed | manual-page | no | footsteps and doors |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/top-down-maze-kit-3d --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/top-down-maze-kit-3d             # direct assets only
python3 asset_licence_checker.py assets/top-down-maze-kit-3d/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Orthographic or high-angle perspective camera; build walls in a GridMap so the AStarGrid2D grid matches cells.

## Assemble

1. Make a MeshLibrary from KayKit/Kenney dungeon pieces and paint the maze in a GridMap.
2. Mirror the GridMap cells into AStarGrid2D (from the Godot demo) for the solver path.

## Do not use

- GDQuest premade characters (CC-BY-NC-SA 4.0) for monetised videos.
