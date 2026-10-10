---
name: "nature-backgrounds-kit"
description: "Use when a short needs calm, moving nature backgrounds (panning skies, swaying foliage, drifting particles) behind photos and captions. Lists CC0 Poly Haven HDRIs, Quaternius and Kenney nature models, ambientCG and cgbookcase materials, and Kenney particles."
---

# Nature backgrounds kit (moving HDRI skies and foliage)

Use when a short needs calm, moving nature backgrounds (panning skies, swaying foliage, drifting particles) behind photos and captions. Lists CC0 Poly Haven HDRIs, Quaternius and Kenney nature models, ambientCG and cgbookcase materials, and Kenney particles.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `polyhaven-belfast-sunset-puresky` | [Belfast Sunset (Pure Sky) HDRI](https://polyhaven.com/a/belfast_sunset_puresky) | CC0-1.0 | optional | allowed | api | no | sunset over water |
| `polyhaven-grasslands-sunset` | [Grasslands Sunset HDRI](https://polyhaven.com/a/grasslands_sunset) | CC0-1.0 | optional | allowed | api | no | golden field |
| `polyhaven-rosendal-park-sunset-puresky` | [Rosendal Park Sunset (Pure Sky) HDRI](https://polyhaven.com/a/rosendal_park_sunset_puresky) | CC0-1.0 | optional | allowed | api | no | clear warm sky |
| `polyhaven-evening-road-01-puresky` | [Evening Road 01 (Pure Sky) HDRI](https://polyhaven.com/a/evening_road_01_puresky) | CC0-1.0 | optional | allowed | api | no | evening sky |
| `polyhaven-industrial-sunset-puresky` | [Industrial Sunset (Pure Sky) HDRI](https://polyhaven.com/a/industrial_sunset_puresky) | CC0-1.0 | optional | allowed | api | no | sky-only gradient |
| `quaternius-ultimate-nature` | [Ultimate Nature Pack](https://quaternius.com/packs/ultimatenature.html) | CC0-1.0 | optional | allowed | manual-page | no | foreground foliage |
| `kenney-nature-kit` | [Nature Kit](https://kenney.nl/assets/nature-kit) | CC0-1.0 | optional | allowed | manual-page | no | stylised foliage |
| `ambientcg-materials` | [ambientCG materials (pick per surface)](https://ambientcg.com/list) | CC0-1.0 | optional | allowed | api | no | ground and rock materials |
| `cgbookcase-textures` | [cgbookcase textures (pick per surface)](https://www.cgbookcase.com/textures) | CC0-1.0 | optional | allowed | manual-page | no | extra ground textures |
| `kenney-particle-pack` | [Particle Pack](https://kenney.nl/assets/particle-pack) | CC0-1.0 | optional | allowed | manual-page | no | drifting particles layer |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/nature-backgrounds-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/nature-backgrounds-kit             # direct assets only
python3 asset_licence_checker.py assets/nature-backgrounds-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Rotate the HDRI slowly (one degree per second reads as motion without distraction); keep 5+ layers moving.
- Blur the background plate slightly so the main photo and captions stay sharp.

## Assemble

1. Blender: World > Environment Texture with a Mapping node keyframed on Z rotation; render 1080x1920.
2. Godot: PanoramaSkyMaterial on a WorldEnvironment; rotate the sky via Environment.sky_rotation.

## Do not use

- Nothing specific beyond the house licence rules.
