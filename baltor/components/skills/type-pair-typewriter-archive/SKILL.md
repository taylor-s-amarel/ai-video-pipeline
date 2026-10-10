---
name: "type-pair-typewriter-archive"
description: "Use when picking fonts for a short ('Special Elite + Courier Prime'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Special Elite + Courier Prime

Worn typewriter headlines with a clean monospaced body for dates and documents.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Special Elite](https://fonts.google.com/specimen/Special+Elite) | 400 | Apache-2.0 | [SpecialElite-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/apache/specialelite/SpecialElite-Regular.ttf) | 0.557 em |
| Captions | [Courier Prime](https://fonts.google.com/specimen/Courier+Prime) | 700 | OFL-1.1 | [CourierPrime-Bold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/courierprime/CourierPrime-Bold.ttf) | 0.600 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 72 px, about 21 characters per line |
| Captions | 50 px (min 42 px), about 29 characters per line |
| Labels (FACT N, STEP N) | 48 px |
| Key numbers | 96 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/SpecialElite-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/apache/specialelite/SpecialElite-Regular.ttf"
curl -L -o "fonts/CourierPrime-Bold.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/courierprime/CourierPrime-Bold.ttf"
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/SpecialElite-Regular.ttf", 72)
# static font: nothing to set
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/SpecialElite-Regular.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Special+Elite
