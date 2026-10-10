---
name: "type-pair-montserrat-inter"
description: "Use when picking fonts for a short ('Montserrat Black + Inter (house)'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Montserrat Black + Inter (house)

Montserrat 900 is a true bold for the yellow hook (so the 3:1 large-bold contrast rule applies); Inter 800 stays crisp at caption size; Anton gives tall key numbers.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Montserrat](https://fonts.google.com/specimen/Montserrat) | 900 | OFL-1.1 | [Montserrat[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf) | 0.648 em |
| Captions | [Inter](https://fonts.google.com/specimen/Inter) | 800 | OFL-1.1 | [Inter[opsz,wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf) | 0.487 em |
| Numbers | [Anton](https://fonts.google.com/specimen/Anton) | 400 | OFL-1.1 | [Anton-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf) | 0.399 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 92 px, about 14 characters per line |
| Captions | 60 px (min 48 px), about 30 characters per line |
| Labels (FACT N, STEP N) | 54 px |
| Key numbers | 120 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/Montserrat[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Montserrat[wght].ttf" wght=900 -o fonts/Montserrat-900.ttf
curl -L -o "fonts/Inter[opsz,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
python3 -m fontTools.varLib.instancer "fonts/Inter[opsz,wght].ttf" wght=800 -o fonts/Inter-800.ttf
curl -L -o "fonts/Anton-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf"
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/Montserrat[wght].ttf", 92)
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
