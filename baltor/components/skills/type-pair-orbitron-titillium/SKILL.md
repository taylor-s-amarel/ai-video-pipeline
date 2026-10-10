---
name: "type-pair-orbitron-titillium"
description: "Use when picking fonts for a short ('Orbitron + Titillium Web'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Orbitron + Titillium Web

Wide geometric display for space and sci-fi hooks; Titillium is compact enough for captions.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Orbitron](https://fonts.google.com/specimen/Orbitron) | 800 | OFL-1.1 | [Orbitron[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf) | 0.711 em |
| Captions | [Titillium Web](https://fonts.google.com/specimen/Titillium+Web) | 700 | OFL-1.1 | [TitilliumWeb-Bold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/titilliumweb/TitilliumWeb-Bold.ttf) | 0.432 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 76 px, about 16 characters per line |
| Captions | 58 px (min 46 px), about 35 characters per line |
| Labels (FACT N, STEP N) | 44 px |
| Key numbers | 100 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/Orbitron[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Orbitron[wght].ttf" wght=800 -o fonts/Orbitron-800.ttf
curl -L -o "fonts/TitilliumWeb-Bold.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/titilliumweb/TitilliumWeb-Bold.ttf"
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/Orbitron[wght].ttf", 76)
font.set_variation_by_axes([800])  # axes: wght
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/Orbitron-800.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Orbitron
