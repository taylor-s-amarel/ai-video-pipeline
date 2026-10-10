---
name: "platformer-2d-kit"
description: "Use when building a 2D side-scrolling platformer scene or short in Godot 4. Lists CC0 tiles and characters (Kenney, Pixel Frog, Ansimuz art), the MIT Godot 2D platformer demo, CC0 input-prompt glyphs, an OFL pixel font and CC0 retro sounds, with exclusions for licensed music."
---

# 2D platformer kit (pixel art)

Use when building a 2D side-scrolling platformer scene or short in Godot 4. Lists CC0 tiles and characters (Kenney, Pixel Frog, Ansimuz art), the MIT Godot 2D platformer demo, CC0 input-prompt glyphs, an OFL pixel font and CC0 retro sounds, with exclusions for licensed music.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `kenney-pixel-platformer` | [Pixel Platformer](https://kenney.nl/assets/pixel-platformer) | CC0-1.0 | optional | allowed | manual-page | no | tiles, hero and enemies |
| `pixel-adventure-1` | [Pixel Adventure 1 (itch.io copy)](https://pixelfrog-assets.itch.io/pixel-adventure-1) | CC0-1.0 | optional | allowed | manual-page | no | alternative hero and traps |
| `sunny-land-art` | [Sunny Land (art only)](https://ansimuz.itch.io/sunny-land-pixel-game-art/purchase) | CC0-1.0 | optional | allowed | manual-page | no | parallax forest backgrounds |
| `kenney-pattern-pack-pixel` | [Pattern Pack Pixel](https://kenney.nl/assets/pattern-pack-pixel) | CC0-1.0 | optional | allowed | manual-page | no | scrolling background layers |
| `godot-demo-2d-platformer` | [Godot demo: 2D platformer](https://github.com/godotengine/godot-demo-projects/tree/master/2d/platformer) | MIT | optional | allowed-with-licence | git | no | character controller reference |
| `kenney-input-prompts-pixel` | [Input Prompts Pixel](https://kenney.nl/assets/input-prompts-pixel) | CC0-1.0 | optional | allowed | manual-page | no | tutorial button glyphs |
| `font-pixelify-sans` | [Pixelify Sans](https://fonts.google.com/specimen/Pixelify%2BSans) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | pixel captions |
| `oga-512-sfx` | [512 Sound Effects (8-bit style)](https://opengameart.org/content/512-sound-effects-8-bit-style) | CC0-1.0 | optional | allowed | manual-page | no | jump, coin and hit sounds |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/platformer-2d-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/platformer-2d-kit             # direct assets only
python3 asset_licence_checker.py assets/platformer-2d-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- 18x18 (Kenney) or 16x16 (Pixel Frog) tiles; do not mix grids in one level.
- Use Kenney Pattern Pack Pixel layers for parallax so the background always moves.

## Assemble

1. Start from the Godot 2D platformer demo (MIT) and replace its art with Kenney Pixel Platformer tiles.
2. Use `pixel-art-2d` imports, Nearest filter and integer stretch (as the demo's project settings do).
3. Add input glyphs for tutorial captions; credit nothing extra (CC0), but keep the demo's music credit if you keep the music.

## Do not use

- Sunny Land's bundled music by Pascal Belisle unless credited.
- Pixel Adventure's OpenGameArt mirror (CC-BY 4.0) when the itch.io CC0 copy is available.
