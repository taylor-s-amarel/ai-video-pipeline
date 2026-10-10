---
name: "type-pair-noto-multilingual"
description: "Use when picking fonts for a short ('Noto Sans + Noto Serif'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Noto Sans + Noto Serif

The Noto families aim at broad script coverage, so translated captions keep one look. Check the exact Noto family for each script you need.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Noto Sans](https://fonts.google.com/specimen/Noto+Sans) | 800 | OFL-1.1 | [NotoSans[wdth,wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf) | 0.503 em |
| Captions | [Noto Sans](https://fonts.google.com/specimen/Noto+Sans) | 700 | OFL-1.1 | [NotoSans[wdth,wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf) | 0.503 em |
| Numbers | [Noto Serif](https://fonts.google.com/specimen/Noto+Serif) | 700 | OFL-1.1 | [NotoSerif[wdth,wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/notoserif/NotoSerif%5Bwdth%2Cwght%5D.ttf) | 0.499 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 80 px, about 21 characters per line |
| Captions | 56 px (min 46 px), about 31 characters per line |
| Labels (FACT N, STEP N) | 48 px |
| Key numbers | 104 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/NotoSans[wdth,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/NotoSans[wdth,wght].ttf" wght=800 wdth=100 -o fonts/NotoSans-800.ttf
python3 -m fontTools.varLib.instancer "fonts/NotoSans[wdth,wght].ttf" wght=700 wdth=100 -o fonts/NotoSans-700.ttf
curl -L -o "fonts/NotoSerif[wdth,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserif/NotoSerif%5Bwdth%2Cwght%5D.ttf"
python3 -m fontTools.varLib.instancer "fonts/NotoSerif[wdth,wght].ttf" wght=700 wdth=100 -o fonts/NotoSerif-700.ttf
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/NotoSans[wdth,wght].ttf", 80)
font.set_variation_by_axes([100.0, 800])  # axes: wdth, wght
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/NotoSans-800.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Noto+Sans
