---
name: "animal-crowd-story-kit"
description: "Use when a ridiculous story needs many animals on screen (a crowd of pets, a farm stampede). Lists CC0 Quaternius animated animal packs, Kenney mini and blocky characters, nature props, a CC0 sunny HDRI, ZzFX for generated sounds and Kenney Interface Sounds."
---

# Animal crowd story kit (silly stories, many animals)

Use when a ridiculous story needs many animals on screen (a crowd of pets, a farm stampede). Lists CC0 Quaternius animated animal packs, Kenney mini and blocky characters, nature props, a CC0 sunny HDRI, ZzFX for generated sounds and Kenney Interface Sounds.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `quaternius-ultimate-animated-animals` | [Ultimate Animated Animal Pack](https://quaternius.com/packs/ultimateanimatedanimals.html) | CC0-1.0 | optional | allowed | manual-page | no | animated animal crowd |
| `quaternius-farm-animals` | [Farm Animal Pack](https://quaternius.com/packs/farmanimal.html) | CC0-1.0 | optional | allowed | manual-page | no | extra farm animals |
| `kenney-mini-characters` | [Mini Characters](https://kenney.nl/assets/mini-characters) | CC0-1.0 | optional | allowed | manual-page | no | owners and bystanders |
| `kenney-blocky-characters` | [Blocky Characters](https://kenney.nl/assets/blocky-characters) | CC0-1.0 | optional | allowed | manual-page | no | cartoon townsfolk |
| `kenney-nature-kit` | [Nature Kit](https://kenney.nl/assets/nature-kit) | CC0-1.0 | optional | allowed | manual-page | no | park setting |
| `polyhaven-sunset-fairway` | [Sunset Fairway HDRI](https://polyhaven.com/a/sunset_fairway) | CC0-1.0 | optional | allowed | api | no | grassy hill lighting |
| `zzfx` | [ZzFX sound synth (generate original effects)](https://github.com/KilledByAPixel/ZzFX) | MIT | optional | allowed-with-licence | git | no | generated boing and pop sounds |
| `kenney-interface-sounds` | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | CC0-1.0 | optional | allowed | manual-page | no | caption pops |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/animal-crowd-story-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/animal-crowd-story-kit             # direct assets only
python3 asset_licence_checker.py assets/animal-crowd-story-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Use MultiMeshInstance3D or many instanced scenes with randomised animation offsets so the crowd never moves in sync.

## Assemble

1. Check which species each animal pack actually contains before writing the script.
2. Instance hundreds of animals with random rotation, scale (0.9-1.1) and animation start time.

## Do not use

- Nothing specific beyond the house licence rules.
