---
name: "space-nasa-kit"
description: "Use when a space or Moon-landing short needs real spacecraft models plus stylised filler. Three NASA GLBs were downloaded and hashed on 2026-10-10 (all need Draco decoding); others are listed to fetch. Includes NASA usage rules (no insignia, no implied endorsement) and CC0 Kenney/Quaternius space kits."
---

# Space and NASA kit (real spacecraft + stylised extras)

Use when a space or Moon-landing short needs real spacecraft models plus stylised filler. Three NASA GLBs were downloaded and hashed on 2026-10-10 (all need Draco decoding); others are listed to fetch. Includes NASA usage rules (no insignia, no implied endorsement) and CC0 Kenney/Quaternius space kits.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `nasa-apollo-lm` | [Apollo Lunar Module](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Apollo%20Lunar%20Module) | Public domain statement (NASA) + NASA usage guidelines | optional | allowed | direct | yes | Moon landing hero model |
| `nasa-astronaut` | [Astronaut](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Astronaut) | Public domain statement (NASA) + NASA usage guidelines | optional | allowed | direct | yes | astronaut figure |
| `nasa-hubble-a` | [Hubble Space Telescope (A)](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Hubble%20Space%20Telescope%20(A)) | Public domain statement (NASA) + NASA usage guidelines | optional | allowed | direct | yes | telescope explainer |
| `nasa-gateway-core` | [Gateway Core](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Gateway) | Public domain statement (NASA) + NASA usage guidelines | optional | allowed | direct | no | Artemis-era station |
| `nasa-curiosity-rover` | [Curiosity Rover (MSL), Clean](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Curiosity%20Rover%20(MSL)) | Public domain statement (NASA) + NASA usage guidelines | optional | allowed | git | no | Mars rover beat |
| `kenney-space-kit` | [Space Kit](https://kenney.nl/assets/space-kit) | CC0-1.0 | optional | allowed | manual-page | no | stylised base and rockets |
| `quaternius-ultimate-space-kit` | [Ultimate Space Kit](https://quaternius.com/packs/ultimatespacekit.html) | CC0-1.0 | optional | allowed | manual-page | no | stylised astronauts, planets and enemies |
| `font-inter` | [Inter](https://fonts.google.com/specimen/Inter) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | clean data captions |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/space-nasa-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/space-nasa-kit             # direct assets only
python3 asset_licence_checker.py assets/space-nasa-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Black space background with a slow-moving starfield layer; hero model lit by one hard key light.
- Scale models before animation: the Astronaut GLB is about 74 units tall and Hubble (A) about 525 units.

## Assemble

1. `python media_pack_fetcher.py pack.json --out assets/space` fetches the NASA GLBs and verifies their hashes.
2. Import in Blender (Draco and WebP supported), normalise scale, and re-export decoded GLBs for Godot if needed.
3. Use Kenney/Quaternius space kits for stylised cutaways and diagrams.

## Do not use

- NASA logos/insignia and anything implying NASA endorsement.
