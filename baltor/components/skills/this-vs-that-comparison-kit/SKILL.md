---
name: "this-vs-that-comparison-kit"
description: "Use when making split-screen 'this vs that' or ranking shorts. Lists CC0 Kenney props, a game-icons versus icon (CC BY 3.0 credit), MIT check/cross icons, OFL heavy title fonts, Kenney Casino Audio for reveals, Kenney UI panels and Twemoji reaction stickers (CC-BY credit)."
---

# This-vs-that comparison kit

Use when making split-screen 'this vs that' or ranking shorts. Lists CC0 Kenney props, a game-icons versus icon (CC BY 3.0 credit), MIT check/cross icons, OFL heavy title fonts, Kenney Casino Audio for reveals, Kenney UI panels and Twemoji reaction stickers (CC-BY credit).

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `kenney-food-kit` | [Food Kit](https://kenney.nl/assets/food-kit) | CC0-1.0 | optional | allowed | manual-page | no | comparison props |
| `game-icons-crossed-swords` | [Crossed swords icon](https://game-icons.net/about.html) | CC-BY-3.0 | required | allowed-with-licence | direct | no | versus divider |
| `tabler-icons` | [Tabler Icons](https://github.com/tabler/tabler-icons) | MIT | optional | allowed-with-licence | git | no | tick and cross |
| `font-anton` | [Anton](https://fonts.google.com/specimen/Anton?preview.text=Bebas+Neue+Regular&preview.text_type=custom) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | side labels |
| `font-bebas-neue` | [Bebas Neue](https://fonts.google.com/specimen/Bebas%2BNeue) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | hook title |
| `kenney-casino-audio` | [Casino Audio](https://kenney.nl/assets/casino-audio) | CC0-1.0 | optional | allowed | manual-page | no | reveal sounds |
| `kenney-ui-pack` | [UI Pack 2.0](https://kenney.nl/assets/ui-pack) | CC0-1.0 | optional | allowed | manual-page | no | score panels |
| `twemoji` | [Twemoji graphics](https://github.com/jdecked/twemoji) | CC-BY-4.0 | required | allowed-with-licence | git | no | reaction stickers |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/this-vs-that-comparison-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/this-vs-that-comparison-kit             # direct assets only
python3 asset_licence_checker.py assets/this-vs-that-comparison-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Vertical split (top vs bottom) for 9:16; each side has one hero object, one number and one icon.
- Reveal winner with a scale pop and a casino chip sound; never more than two lines of text on screen.

## Assemble

1. Render props (Kenney Food Kit or any CC0 kit) on turntables; place them in the two halves.
2. Put the crossed-swords icon on the divider; credit 'Icon by Lorc, game-icons.net, CC BY 3.0'.

## Do not use

- Brand logos and product photos you do not have rights to.
