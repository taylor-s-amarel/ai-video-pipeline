---
name: "type-pair-bebas-barlow"
description: "Use when picking fonts for a short ('Bebas Neue + Barlow SemiBold'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Bebas Neue + Barlow SemiBold

Bebas Neue is tall and narrow (all caps); Barlow's slightly rounded grotesque balances it in captions.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Bebas Neue](https://fonts.google.com/specimen/Bebas+Neue) | 400 | OFL-1.1 | [BebasNeue-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf) | 0.348 em |
| Captions | [Barlow](https://fonts.google.com/specimen/Barlow) | 600 | OFL-1.1 | [Barlow-SemiBold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/barlow/Barlow-SemiBold.ttf) | 0.428 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 110 px, about 22 characters per line |
| Captions | 60 px (min 48 px), about 34 characters per line |
| Labels (FACT N, STEP N) | 60 px |
| Key numbers | 140 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/BebasNeue-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf"
curl -L -o "fonts/Barlow-SemiBold.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/barlow/Barlow-SemiBold.ttf"
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/BebasNeue-Regular.ttf", 110)
# static font: nothing to set
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/BebasNeue-Regular.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Bebas+Neue
