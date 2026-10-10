---
name: "type-pair-pixel-pair"
description: "Use when picking fonts for a short ('Press Start 2P + Pixelify Sans'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Press Start 2P + Pixelify Sans

Press Start 2P is very wide (about 1 em per character) so keep hooks to 2-3 short words; Pixelify Sans is easier to read in captions.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P) | 400 | OFL-1.1 | [PressStart2P-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/pressstart2p/PressStart2P-Regular.ttf) | 1.000 em |
| Captions | [Pixelify Sans](https://fonts.google.com/specimen/Pixelify+Sans) | 700 | OFL-1.1 | [PixelifySans[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/pixelifysans/PixelifySans%5Bwght%5D.ttf) | 0.501 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 56 px, about 15 characters per line |
| Captions | 56 px (min 44 px), about 31 characters per line |
| Labels (FACT N, STEP N) | 40 px |
| Key numbers | 72 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/PressStart2P-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/pressstart2p/PressStart2P-Regular.ttf"
curl -L -o "fonts/PixelifySans[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/pixelifysans/PixelifySans%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/PixelifySans[wght].ttf" wght=700 -o fonts/PixelifySans-700.ttf
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/PressStart2P-Regular.ttf", 56)
# static font: nothing to set
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/PressStart2P-Regular.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Press+Start+2P
