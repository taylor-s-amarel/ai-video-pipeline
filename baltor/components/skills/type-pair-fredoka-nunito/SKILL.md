---
name: "type-pair-fredoka-nunito"
description: "Use when picking fonts for a short ('Fredoka + Nunito'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Fredoka + Nunito

Rounded terminals feel friendly for pets, feelings and kids topics.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Fredoka](https://fonts.google.com/specimen/Fredoka) | 600 | OFL-1.1 | [Fredoka[wdth,wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/fredoka/Fredoka%5Bwdth%2Cwght%5D.ttf) | 0.440 em |
| Captions | [Nunito](https://fonts.google.com/specimen/Nunito) | 800 | OFL-1.1 | [Nunito[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/nunito/Nunito%5Bwght%5D.ttf) | 0.473 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 88 px, about 22 characters per line |
| Captions | 58 px (min 46 px), about 32 characters per line |
| Labels (FACT N, STEP N) | 52 px |
| Key numbers | 110 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/Fredoka[wdth,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/fredoka/Fredoka%5Bwdth%2Cwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Fredoka[wdth,wght].ttf" wght=600 wdth=100 -o fonts/Fredoka-600.ttf
curl -L -o "fonts/Nunito[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/nunito/Nunito%5Bwght%5D.ttf"
python3 -m fontTools.varLib.instancer "fonts/Nunito[wght].ttf" wght=800 -o fonts/Nunito-800.ttf
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/Fredoka[wdth,wght].ttf", 88)
font.set_variation_by_axes([100.0, 600])  # axes: wdth, wght
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/Fredoka-600.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Fredoka
