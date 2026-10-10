---
name: "isometric-town-kit-3d"
description: "Use when the town should be 3D under an orthographic isometric camera, for example a city growth timelapse. Lists Kenney City Kits (Suburban, Commercial, Roads), Car Kit, the Godot 4.6 city-builder starter kit and an evening HDRI."
---

# Isometric town kit (3D city-kit variant)

Use when the town should be 3D under an orthographic isometric camera, for example a city growth timelapse. Lists Kenney City Kits (Suburban, Commercial, Roads), Car Kit, the Godot 4.6 city-builder starter kit and an evening HDRI.

Variant of `isometric_town_kit`: same purpose, different asset family and camera.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `kenney-starter-kit-city-builder` | [Starter Kit City Builder (Godot 4.6)](https://github.com/KenneyNL/Starter-Kit-City-Builder) | MIT (code), CC0-1.0 (assets) | optional | allowed-with-licence | manual-page | no | Godot 4.6 city-builder template |
| `kenney-city-kit-suburban` | [City Kit (Suburban)](https://kenney.nl/assets/city-kit-suburban) | CC0-1.0 | optional | allowed | manual-page | no | houses |
| `kenney-city-kit-commercial` | [City Kit (Commercial)](https://kenney.nl/assets/city-kit-commercial) | CC0-1.0 | optional | allowed | manual-page | no | shops and towers |
| `kenney-city-kit-roads` | [City Kit (Roads)](https://kenney.nl/assets/city-kit-roads) | CC0-1.0 | optional | allowed | manual-page | no | roads, signs and lights |
| `kenney-car-kit` | [Car Kit](https://kenney.nl/assets/car-kit) | CC0-1.0 | optional | allowed | manual-page | no | traffic |
| `polyhaven-evening-road-01-puresky` | [Evening Road 01 (Pure Sky) HDRI](https://polyhaven.com/a/evening_road_01_puresky) | CC0-1.0 | optional | allowed | api | no | evening lighting |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/isometric-town-kit-3d --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/isometric-town-kit-3d             # direct assets only
python3 asset_licence_checker.py assets/isometric-town-kit-3d/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Orthographic camera at the classic isometric angle; animate buildings appearing tile by tile.

## Assemble

1. Start from Kenney's Starter Kit City Builder (dynamic MeshLibrary, save/load) and script the timelapse.

## Do not use

- Nothing specific beyond the house licence rules.
