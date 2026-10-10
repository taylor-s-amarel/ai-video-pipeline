---
name: "type-pair-anton-inter"
description: "Use when picking fonts for a short ('Anton + Inter'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Anton + Inter

Anton is a heavy condensed display face (one regular-weight style, so pair it with an outline or a 4.5:1 background) that fits long hooks in the upper third; Inter at 800 stays crisp at caption size.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Anton](https://fonts.google.com/specimen/Anton) | 400 | OFL-1.1 | [Anton-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf) | 0.419 em |
| Captions | [Inter](https://fonts.google.com/specimen/Inter) | 800 | OFL-1.1 | [Inter[opsz,wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf) | 0.487 em |
| Numbers | [Anton](https://fonts.google.com/specimen/Anton) | 400 | OFL-1.1 | [Anton-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf) | 0.399 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 96 px, about 21 characters per line |
| Captions | 60 px (min 48 px), about 30 characters per line |
| Labels (FACT N, STEP N) | 54 px |
| Key numbers | 120 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/Anton-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf"
curl -L -o "fonts/Inter[opsz,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Inter[opsz,wght].ttf" wght=800 -o fonts/Inter-800.ttf
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/Anton-Regular.ttf", 96)
# static font: nothing to set
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/Anton-Regular.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Anton
