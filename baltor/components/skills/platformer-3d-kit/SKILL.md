---
name: "platformer-3d-kit"
description: "Use when the platformer should be a 3D low-poly level. Lists Kenney's Platformer Kit and KayKit Platformer Pack (CC0), Kenney's MIT/CC0 Godot 3D platformer starter kit and the official 3D platformer demo, plus a sunset HDRI and UI sounds."
---

# 3D platformer kit (low-poly variant)

Use when the platformer should be a 3D low-poly level. Lists Kenney's Platformer Kit and KayKit Platformer Pack (CC0), Kenney's MIT/CC0 Godot 3D platformer starter kit and the official 3D platformer demo, plus a sunset HDRI and UI sounds.

Variant of `platformer_2d_kit`: same purpose, different asset family and camera.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `kenney-starter-kit-3d-platformer` | [Starter Kit 3D Platformer (Godot 4.6)](https://github.com/KenneyNL/Starter-Kit-3D-Platformer) | MIT (code), CC0-1.0 (assets) | optional | allowed-with-licence | manual-page | no | ready Godot 4.6 template |
| `kenney-platformer-kit` | [Platformer Kit (3D)](https://kenney.nl/assets/platformer-kit) | CC0-1.0 | optional | allowed | manual-page | no | level blocks and props |
| `kaykit-platformer` | [KayKit Platformer Pack (free tier)](https://kaylousberg.itch.io/kaykit-platformer) | CC0-1.0 | optional | allowed | manual-page | no | alternative stylised pieces |
| `godot-demo-3d-platformer` | [Godot demo: 3D platformer](https://github.com/godotengine/godot-demo-projects/tree/master/3d/platformer) | MIT | optional | allowed-with-licence | git | no | CharacterBody3D reference |
| `polyhaven-sunset-fairway` | [Sunset Fairway HDRI](https://polyhaven.com/a/sunset_fairway) | CC0-1.0 | optional | allowed | api | no | sky and lighting |
| `kenney-interface-sounds` | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | CC0-1.0 | optional | allowed | manual-page | no | UI and pickup sounds |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/platformer-3d-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/platformer-3d-kit             # direct assets only
python3 asset_licence_checker.py assets/platformer-3d-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Chase camera with gentle lag; bright HDRI; one kit family per level.

## Assemble

1. Clone Kenney's Starter Kit 3D Platformer (Godot 4.6) and swap or extend its CC0 pieces.
2. Compare with the official 3D platformer demo for CharacterBody3D details.

## Do not use

- GDQuest third-person controller art (CC-BY-NC-SA 4.0); its MIT code is fine.
