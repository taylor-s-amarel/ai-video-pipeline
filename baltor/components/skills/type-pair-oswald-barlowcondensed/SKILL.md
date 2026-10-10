---
name: "type-pair-oswald-barlowcondensed"
description: "Use when picking fonts for a short ('Oswald + Barlow Condensed'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Oswald + Barlow Condensed

Condensed sports-poster feel; fits more words per line in narrow frames.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Oswald](https://fonts.google.com/specimen/Oswald) | 700 | OFL-1.1 | [Oswald[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf) | 0.475 em |
| Captions | [Barlow Condensed](https://fonts.google.com/specimen/Barlow+Condensed) | 700 | OFL-1.1 | [BarlowCondensed-Bold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-Bold.ttf) | 0.357 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 96 px, about 19 characters per line |
| Captions | 64 px (min 52 px), about 38 characters per line |
| Labels (FACT N, STEP N) | 56 px |
| Key numbers | 130 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/Oswald[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Oswald[wght].ttf" wght=700 -o fonts/Oswald-700.ttf
curl -L -o "fonts/BarlowCondensed-Bold.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-Bold.ttf"
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/Oswald[wght].ttf", 96)
font.set_variation_by_axes([700])  # axes: wght
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/Oswald-700.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Oswald
