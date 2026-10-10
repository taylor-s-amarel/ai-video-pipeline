---
name: "pa-farm-diorama-kit"
description: "Use when building a farm or rural-business 3D visualisation in Godot 4 (for example a contest showcase of a small farm's product or service). Lists CC0 Quaternius farm buildings, animals and crops, Kenney nature and car kits, Kenney's MIT/CC0 city-builder template for placement, the MIT Terrain3D addon and a CC0 HDRI."
---

# Pennsylvania farm diorama kit (Godot 3D showcase)

Use when building a farm or rural-business 3D visualisation in Godot 4 (for example a contest showcase of a small farm's product or service). Lists CC0 Quaternius farm buildings, animals and crops, Kenney nature and car kits, Kenney's MIT/CC0 city-builder template for placement, the MIT Terrain3D addon and a CC0 HDRI.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `quaternius-farm-buildings` | [Farm Buildings Pack](https://quaternius.com/packs/farmbuildings.html) | CC0-1.0 | optional | allowed | manual-page | no | barn, silo and fences |
| `quaternius-farm-animals` | [Farm Animal Pack](https://quaternius.com/packs/farmanimal.html) | CC0-1.0 | optional | allowed | manual-page | no | animated cows, pigs and chickens |
| `quaternius-ultimate-crops` | [Ultimate Crops Pack](https://quaternius.com/packs/ultimatecrops.html) | CC0-1.0 | optional | allowed | manual-page | no | crop rows |
| `kenney-nature-kit` | [Nature Kit](https://kenney.nl/assets/nature-kit) | CC0-1.0 | optional | allowed | manual-page | no | trees and rocks |
| `kenney-car-kit` | [Car Kit](https://kenney.nl/assets/car-kit) | CC0-1.0 | optional | allowed | manual-page | no | delivery vehicles |
| `kenney-starter-kit-city-builder` | [Starter Kit City Builder (Godot 4.6)](https://github.com/KenneyNL/Starter-Kit-City-Builder) | MIT (code), CC0-1.0 (assets) | optional | allowed-with-licence | manual-page | no | placement and save/load template |
| `terrain3d` | [Terrain3D addon](https://github.com/TokisanGames/Terrain3D) | MIT | optional | allowed-with-licence | git | no | editable terrain |
| `polyhaven-grasslands-sunset` | [Grasslands Sunset HDRI](https://polyhaven.com/a/grasslands_sunset) | CC0-1.0 | optional | allowed | api | no | golden-hour lighting |
| `font-inter` | [Inter](https://fonts.google.com/specimen/Inter) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | building labels |
| `kenney-interface-sounds` | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | CC0-1.0 | optional | allowed | manual-page | no | UI sounds |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/pa-farm-diorama-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/pa-farm-diorama-kit             # direct assets only
python3 asset_licence_checker.py assets/pa-farm-diorama-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Late-afternoon light (Grasslands Sunset HDRI), low-poly fields in rows, animated animals idling.
- Label each building with the product or service it represents; keep labels in Inter, max 3 words.

## Assemble

1. Start from Kenney's Starter Kit City Builder (build/remove, MeshLibrary, save/load) and swap the
   MeshLibrary for farm buildings and crop tiles.
2. Sculpt gentle terrain with Terrain3D or use flat tiles for a board-game look.
3. Record a 60-90 s fly-through; check every model with `gltf_glb_inspector` before import.

## Do not use

- GDQuest characters (non-commercial) and Mixamo raw files in the shared project.
