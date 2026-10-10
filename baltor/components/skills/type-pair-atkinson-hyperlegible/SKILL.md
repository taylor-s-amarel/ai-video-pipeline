---
name: "type-pair-atkinson-hyperlegible"
description: "Use when picking fonts for a short ('Atkinson Hyperlegible (bold + regular)'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Atkinson Hyperlegible (bold + regular)

Designed for readers with low vision; letters that are easy to confuse (I/l/1, O/0) are distinct.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Atkinson Hyperlegible](https://fonts.google.com/specimen/Atkinson+Hyperlegible) | 700 | OFL-1.1 | [AtkinsonHyperlegible-Bold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Bold.ttf) | 0.471 em |
| Captions | [Atkinson Hyperlegible](https://fonts.google.com/specimen/Atkinson+Hyperlegible) | 700 | OFL-1.1 | [AtkinsonHyperlegible-Bold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Bold.ttf) | 0.471 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 80 px, about 23 characters per line |
| Captions | 56 px (min 46 px), about 33 characters per line |
| Labels (FACT N, STEP N) | 50 px |
| Key numbers | 104 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/AtkinsonHyperlegible-Bold.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Bold.ttf"
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/AtkinsonHyperlegible-Bold.ttf", 80)
# static font: nothing to set
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/AtkinsonHyperlegible-Bold.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Atkinson+Hyperlegible
