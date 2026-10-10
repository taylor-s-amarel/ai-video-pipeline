---
name: "type-pair-montserrat-black"
description: "Use when picking fonts for a short ('Montserrat Black + Montserrat Bold'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Montserrat Black + Montserrat Bold

One geometric family keeps the look tidy; the 900 weight gives hooks punch without a second font.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Montserrat](https://fonts.google.com/specimen/Montserrat) | 900 | OFL-1.1 | [Montserrat[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf) | 0.648 em |
| Captions | [Montserrat](https://fonts.google.com/specimen/Montserrat) | 700 | OFL-1.1 | [Montserrat[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf) | 0.525 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 84 px, about 15 characters per line |
| Captions | 58 px (min 46 px), about 28 characters per line |
| Labels (FACT N, STEP N) | 52 px |
| Key numbers | 110 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/Montserrat[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Montserrat[wght].ttf" wght=900 -o fonts/Montserrat-900.ttf
python3 -m fontTools.varLib.instancer "fonts/Montserrat[wght].ttf" wght=700 -o fonts/Montserrat-700.ttf
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/Montserrat[wght].ttf", 84)
font.set_variation_by_axes([900])  # axes: wght
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/Montserrat-900.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Montserrat
