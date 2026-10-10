---
name: "type-pair-marker-patrickhand"
description: "Use when picking fonts for a short ('Permanent Marker + Patrick Hand'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Permanent Marker + Patrick Hand

Hand-made look for stick-figure, doodle and whiteboard stories.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Permanent Marker](https://fonts.google.com/specimen/Permanent+Marker) | 400 | Apache-2.0 | [PermanentMarker-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/apache/permanentmarker/PermanentMarker-Regular.ttf) | 0.494 em |
| Captions | [Patrick Hand](https://fonts.google.com/specimen/Patrick+Hand) | 400 | OFL-1.1 | [PatrickHand-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/patrickhand/PatrickHand-Regular.ttf) | 0.350 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 84 px, about 20 characters per line |
| Captions | 64 px (min 52 px), about 39 characters per line |
| Labels (FACT N, STEP N) | 56 px |
| Key numbers | 110 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/PermanentMarker-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/apache/permanentmarker/PermanentMarker-Regular.ttf"
curl -L -o "fonts/PatrickHand-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/patrickhand/PatrickHand-Regular.ttf"
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/PermanentMarker-Regular.ttf", 84)
# static font: nothing to set
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/PermanentMarker-Regular.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Permanent+Marker
