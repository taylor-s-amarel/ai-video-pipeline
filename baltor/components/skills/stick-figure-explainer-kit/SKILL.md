---
name: "stick-figure-explainer-kit"
description: "Use when building a faceless stick-figure or flat-character explainer short (1080x1920). Lists CC0/OFL/MIT sources for characters, a narrator avatar, concept icons, caption and title fonts, UI panels, particles and pop sounds, with licences and credit lines, as a manifest to fetch (no files included)."
---

# Stick-figure explainer kit (faceless 2D)

Use when building a faceless stick-figure or flat-character explainer short (1080x1920). Lists CC0/OFL/MIT sources for characters, a narrator avatar, concept icons, caption and title fonts, UI panels, particles and pop sounds, with licences and credit lines, as a manifest to fetch (no files included).

**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
| `kenney-modular-characters` | [Modular Characters (2D)](https://kenney.nl/assets/modular-characters) | CC0-1.0 | optional | allowed | manual-page | no | flat explainer characters |
| `notion-avatar` | [Notion Avatar assets](https://github.com/Mayandev/notion-avatar) | CC0-1.0 | optional | allowed | git | no | narrator portrait card |
| `tabler-icons` | [Tabler Icons](https://github.com/tabler/tabler-icons) | MIT | optional | allowed-with-licence | git | no | concept icons for steps and facts |
| `lucide-icons` | [Lucide icons](https://github.com/lucide-icons/lucide) | ISC | optional | allowed-with-licence | git | no | UI-style icons for apps and devices |
| `game-icons-crossed-swords` | [Crossed swords icon](https://game-icons.net/about.html) | CC-BY-3.0 | required | allowed-with-licence | direct | no | conflict or versus beat icon |
| `font-bebas-neue` | [Bebas Neue](https://fonts.google.com/specimen/Bebas%2BNeue) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | hook title on the first frame |
| `font-montserrat` | [Montserrat](https://fonts.google.com/specimen/Montserrat/license) | OFL-1.1 | optional | allowed-with-licence | manual-page | no | one-line synced captions |
| `kenney-ui-pack` | [UI Pack 2.0](https://kenney.nl/assets/ui-pack) | CC0-1.0 | optional | allowed | manual-page | no | frosted caption panel shapes and arrows |
| `kenney-particle-pack` | [Particle Pack](https://kenney.nl/assets/particle-pack) | CC0-1.0 | optional | allowed | manual-page | no | sparkles behind keyword pops |
| `kenney-interface-sounds` | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | CC0-1.0 | optional | allowed | manual-page | no | caption pop and click sounds |

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/stick-figure-explainer-kit --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/stick-figure-explainer-kit             # direct assets only
python3 asset_licence_checker.py assets/stick-figure-explainer-kit/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

`asset_licence_checker --use monetised-video` on 2026-10-10: 0 error(s), 0 warning(s).

## Look and style

- Thick-outline flat characters on a moving gradient or patterned background (never a static slide).
- One concept icon per beat, popping in with the caption keyword; keep icons from one family.
- Title in Bebas Neue (bold yellow #FFD21F per house style), captions in Montserrat Bold, one line at a time.

## Assemble

1. Build characters from Kenney Modular Characters parts (or draw stick figures as Line2D in Godot so they are original).
2. Narrator portrait: Notion Avatar (CC0 assets) in a corner card.
3. Icons: Tabler/Lucide for UI concepts, game-icons for action concepts (credit the author).
4. Pops: Kenney Interface Sounds under each keyword pop.

## Do not use

- xkcd font (ipython/xkcd-font): CC BY-NC 3.0, not for monetised videos.
- Platform emoji screenshots (Apple, Samsung): not openly licensed.
