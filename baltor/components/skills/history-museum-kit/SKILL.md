---
name: "history-museum-kit"
description: "Use when a history short ('today in history', battles, ancient sites) needs props and sources. Lists Smithsonian Open Access metadata (CC0 records), the NASA Apollo LM GLB (hashed), CC0 Kenney castle and graveyard kits, Quaternius modular ruins, KayKit skeletons and CC0 textures."
---

# History and museum kit (CC0 records, ruins, castles)

Use when a history short ('today in history', battles, ancient sites) needs props and sources. Lists Smithsonian Open Access metadata (CC0 records), the NASA Apollo LM GLB (hashed), CC0 Kenney castle and graveyard kits, Quaternius modular ruins, KayKit skeletons and CC0 textures.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `smithsonian-openaccess` | [Smithsonian Open Access metadata (CC0 records)](https://github.com/Smithsonian/OpenAccess) | CC0-1.0 | optional | allowed | git | no | real object records and dates |
| `nasa-apollo-lm` | [Apollo Lunar Module](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Apollo%20Lunar%20Module) | Public domain statement (NASA) + NASA usage guidelines | optional | allowed | direct | yes | 1969 Moon landing beat |
| `kenney-castle-kit` | [Castle Kit](https://kenney.nl/assets/castle-kit) | CC0-1.0 | optional | allowed | manual-page | no | castle reconstructions |
| `quaternius-ultimate-modular-ruins` | [Ultimate Modular Ruins Pack](https://quaternius.com/packs/ultimatemodularruins.html) | CC0-1.0 | optional | allowed | manual-page | no | ancient ruins |
| `kenney-graveyard-kit` | [Graveyard Kit](https://kenney.nl/assets/graveyard-kit) | CC0-1.0 | optional | allowed | manual-page | no | graveyard scenes |
| `kaykit-skeletons-github` | [KayKit Character Pack Skeletons 1.0](https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Skeletons-1.0) | CC0-1.0 | optional | allowed | git | no | skeleton characters |
| `cgbookcase-textures` | [cgbookcase textures (pick per surface)](https://www.cgbookcase.com/textures) | CC0-1.0 | optional | allowed | manual-page | no | stone and wood surfaces |
| `polyhaven-textures` | [Poly Haven textures (pick per surface)](https://polyhaven.com/textures) | CC0-1.0 | optional | allowed | api | no | extra PBR surfaces |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/history-museum-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/history-museum-kit             # direct assets only
python3 asset_licence_checker.py assets/history-museum-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Dark warm grade, torch-like key light, slow push-in on each prop; FACT labels with dates and sources.

## Assemble

1. Query Smithsonian Open Access records for real objects and dates; cite record URLs in the description.
2. Build reconstructions from Kenney Castle Kit and Quaternius Modular Ruins; texture with CC0 stone/wood.

## Do not use

- Research scan models with unclear rights (for example the common-3d-test-models set) until their licence is confirmed.
- Sketchfab museum scans marked BY-NC for monetised videos.
