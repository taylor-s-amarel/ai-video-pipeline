---
name: "type-pair-robotoslab-roboto"
description: "Use when picking fonts for a short ('Roboto Slab + Roboto'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Roboto Slab + Roboto

Slab serif headlines read as news without looking like any one outlet; Roboto captions are neutral.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Roboto Slab](https://fonts.google.com/specimen/Roboto+Slab) | 800 | Apache-2.0 | [RobotoSlab[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf) | 0.472 em |
| Captions | [Roboto](https://fonts.google.com/specimen/Roboto) | 700 | OFL-1.1 | [Roboto[wdth,wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf) | 0.444 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 80 px, about 23 characters per line |
| Captions | 54 px (min 44 px), about 36 characters per line |
| Labels (FACT N, STEP N) | 46 px |
| Key numbers | 104 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/RobotoSlab[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/RobotoSlab[wght].ttf" wght=800 -o fonts/RobotoSlab-800.ttf
curl -L -o "fonts/Roboto[wdth,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf"
python3 -m fontTools.varLib.instancer "fonts/Roboto[wdth,wght].ttf" wght=700 wdth=100 -o fonts/Roboto-700.ttf
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/RobotoSlab[wght].ttf", 80)
font.set_variation_by_axes([800])  # axes: wght
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/RobotoSlab-800.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Roboto+Slab
