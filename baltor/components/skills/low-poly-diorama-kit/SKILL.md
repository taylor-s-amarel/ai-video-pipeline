---
name: "low-poly-diorama-kit"
description: "Use when a short needs a cute low-poly diorama (island, village, hex board) rendered in Godot 4 or Blender with a slow camera orbit. Lists CC0 kits from Kenney, Quaternius and KayKit plus a Poly Haven sunset HDRI, with licences and import hints, as a manifest to fetch."
---

# Low-poly diorama kit (3D, Godot/Blender)

Use when a short needs a cute low-poly diorama (island, village, hex board) rendered in Godot 4 or Blender with a slow camera orbit. Lists CC0 kits from Kenney, Quaternius and KayKit plus a Poly Haven sunset HDRI, with licences and import hints, as a manifest to fetch.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `kaykit-medieval-hexagon` | [KayKit Medieval Hexagon Pack (free tier)](https://kaylousberg.itch.io/kaykit-medieval-hexagon) | CC0-1.0 | optional | allowed | manual-page | no | hex tile base and buildings |
| `kenney-nature-kit` | [Nature Kit](https://kenney.nl/assets/nature-kit) | CC0-1.0 | optional | allowed | manual-page | no | trees, rocks and plants |
| `quaternius-ultimate-stylized-nature` | [Ultimate Stylized Nature Pack](https://quaternius.com/packs/ultimatestylizednature.html) | CC0-1.0 | optional | allowed | manual-page | no | extra stylised foliage |
| `kenney-fantasy-town-kit` | [Fantasy Town Kit](https://kenney.nl/assets/fantasy-town-kit) | CC0-1.0 | optional | allowed | manual-page | no | village buildings |
| `kenney-mini-characters` | [Mini Characters](https://kenney.nl/assets/mini-characters) | CC0-1.0 | optional | allowed | manual-page | no | tiny villagers |
| `polyhaven-rosendal-park-sunset-puresky` | [Rosendal Park Sunset (Pure Sky) HDRI](https://polyhaven.com/a/rosendal_park_sunset_puresky) | CC0-1.0 | optional | allowed | api | no | warm sky and lighting |
| `kenney-particle-pack` | [Particle Pack](https://kenney.nl/assets/particle-pack) | CC0-1.0 | optional | allowed | manual-page | no | drifting dust and sparkles |
| `font-bebas-neue` | [Bebas Neue](https://fonts.google.com/specimen/Bebas%2BNeue) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | hook title |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/low-poly-diorama-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/low-poly-diorama-kit             # direct assets only
python3 asset_licence_checker.py assets/low-poly-diorama-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Small square or hex base, soft sunset HDRI lighting, slight tilt-shift depth of field, 8-12 s orbit per beat.
- Keep one kit family per frame (Kenney with Kenney, KayKit with KayKit) so shading matches.

## Assemble

1. Lay the hex or square base with KayKit Medieval Hexagon tiles (GridMap in Godot).
2. Dress with Kenney Nature Kit and Quaternius Stylized Nature; add Fantasy Town buildings.
3. Light with the Rosendal Park sunset HDRI; add Kenney particle sprites as drifting dust.
4. Run `gltf_glb_inspector` on each model to normalise scale before placing.

## Do not use

- Synty and other paid packs that appear in Poly Pizza search results.
