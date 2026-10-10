---
name: "top-down-maze-kit"
description: "Use when making a top-down maze or dungeon escape short ('one small adjustment', 'stuck in a maze') in Godot 4 at pixel-art scale. Lists CC0 tiles and characters, the MIT AStarGrid2D pathfinding demo, a 4-colour palette, a pixel font and CC0 retro sounds, with import presets."
---

# Top-down maze kit (2D pixel art)

Use when making a top-down maze or dungeon escape short ('one small adjustment', 'stuck in a maze') in Godot 4 at pixel-art scale. Lists CC0 tiles and characters, the MIT AStarGrid2D pathfinding demo, a 4-colour palette, a pixel font and CC0 retro sounds, with import presets.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `dungeontileset-ii` | [16x16 DungeonTileset II](https://0x72.itch.io/dungeontileset-ii) | CC0-1.0 | optional | allowed | manual-page | no | dungeon walls, floors and animated heroes |
| `kenney-1-bit-pack` | [1-Bit Pack](https://kenney.nl/assets/1-bit-pack) | CC0-1.0 | optional | allowed | manual-page | no | alternative monochrome maze tiles and icons |
| `kenney-micro-roguelike` | [Micro Roguelike](https://kenney.nl/assets/micro-roguelike) | CC0-1.0 | optional | allowed | manual-page | no | 8x8 variant for very small mazes |
| `kenney-tiny-series` | [Tiny series (Tiny Dungeon, Tiny Town ...)](https://kenney.nl/assets/series:Tiny) | CC0-1.0 | optional | allowed | manual-page | no | Tiny Dungeon tiles on the shared 16x16 grid |
| `godot-demo-navigation-astar` | [Godot demo: AStarGrid2D navigation](https://github.com/godotengine/godot-demo-projects/tree/master/2d/navigation_astar) | MIT | optional | allowed-with-licence | git | no | pathfinding logic for the maze solver |
| `lospec-gb` | [Lospec GB palette (4 colours)](https://lospec.com/palette-list/lospec-gb) | No licence stated (credit the palette author) | optional | project-only | manual-page | no | optional 4-colour handheld palette |
| `font-press-start-2p` | [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | pixel captions and step counter |
| `oga-512-sfx` | [512 Sound Effects (8-bit style)](https://opengameart.org/content/512-sound-effects-8-bit-style) | CC0-1.0 | optional | allowed | manual-page | no | footsteps, pickups, door sounds |
| `kenney-interface-sounds` | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | CC0-1.0 | optional | allowed | manual-page | no | caption pops |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/top-down-maze-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/top-down-maze-kit             # direct assets only
python3 asset_licence_checker.py assets/top-down-maze-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 1 warning(s).

- lospec-gb: unrecognised licence 'No licence stated (credit the palette author)': a human must read https://lospec.com/palette-list/lospec-gb

## Look and style

- 16x16 tiles scaled by a whole number with `pixel_art_video_fit` (x4 fits a 224-px-wide maze, 14 tiles, inside the 9:16 safe area).
- Show the path being found: AStarGrid2D steps drawn as a glowing trail, one step per beat of narration.

## Assemble

1. Pick tiles from 0x72 DungeonTileset II or Kenney 1-Bit Pack (do not mix the two styles in one maze).
2. Apply `godot_texture_import_presets --preset pixel-art-2d`; slice sheets with `sprite_sheet_slicer grid --size 16x16`.
3. Copy the AStarGrid2D logic from the Godot demo; animate the hero along the path.
4. Optional: quantise everything to the Lospec GB palette for a handheld look, then `check` each frame.

## Do not use

- Bundled music in some itch.io packs (licensed separately).
