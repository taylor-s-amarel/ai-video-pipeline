---
name: "ui-caption-kit"
description: "Use when styling hook titles, one-line captions, FACT labels, lower thirds and reaction stickers for 1080x1920 shorts or Godot UI. Lists OFL fonts (Bebas Neue, Anton, Montserrat, Inter), Kenney UI Pack, Lucide/Tabler icons, Twemoji (credit) and Kenney Interface Sounds."
---

# UI and caption kit (fonts, panels, icons, pops)

Use when styling hook titles, one-line captions, FACT labels, lower thirds and reaction stickers for 1080x1920 shorts or Godot UI. Lists OFL fonts (Bebas Neue, Anton, Montserrat, Inter), Kenney UI Pack, Lucide/Tabler icons, Twemoji (credit) and Kenney Interface Sounds.

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `font-bebas-neue` | [Bebas Neue](https://fonts.google.com/specimen/Bebas%2BNeue) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | hook titles |
| `font-anton` | [Anton](https://fonts.google.com/specimen/Anton?preview.text=Bebas+Neue+Regular&preview.text_type=custom) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | alternative heavy title |
| `font-montserrat` | [Montserrat](https://fonts.google.com/specimen/Montserrat/license) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | captions |
| `font-inter` | [Inter](https://fonts.google.com/specimen/Inter) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | small labels and sources line |
| `kenney-ui-pack` | [UI Pack 2.0](https://kenney.nl/assets/ui-pack) | CC0-1.0 | optional | allowed | manual-page | no | panels and arrows |
| `lucide-icons` | [Lucide icons](https://github.com/lucide-icons/lucide) | ISC | optional | allowed-with-licence | git | no | inline caption icons |
| `tabler-icons` | [Tabler Icons](https://github.com/tabler/tabler-icons) | MIT | optional | allowed-with-licence | git | no | check and cross marks |
| `twemoji` | [Twemoji graphics](https://github.com/jdecked/twemoji) | CC-BY-4.0 | required | allowed-with-licence | git | no | reaction stickers |
| `kenney-particle-pack` | [Particle Pack](https://kenney.nl/assets/particle-pack) | CC0-1.0 | optional | allowed | manual-page | no | keyword sparkle |
| `kenney-interface-sounds` | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | CC0-1.0 | optional | allowed | manual-page | no | pop and click |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/ui-caption-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/ui-caption-kit             # direct assets only
python3 asset_licence_checker.py assets/ui-caption-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Title: Bebas Neue or Anton, bold yellow #FFD21F, upper third over the photo, frosted backing.
- Captions: Montserrat Bold, max 7 words, one line, keyword pop 1.0 -> 1.12 -> 1.0 over 180 ms with a click.

## Assemble

1. Install fonts locally (keep OFL.txt); point the subtitle renderer at the font directory.
2. Use Kenney UI Pack shapes as frosted panel masks; never a hard rectangular cutout.

## Do not use

- Font Awesome Pro icons; platform emoji screenshots.
