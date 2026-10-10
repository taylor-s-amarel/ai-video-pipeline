---
name: "type-pair-spacegrotesk-jetbrains"
description: "Use when picking fonts for a short ('Space Grotesk + JetBrains Mono'): open-licence Google Fonts (OFL/Apache) with verified download URLs, sizes, characters per line and install commands."
---

# Space Grotesk + JetBrains Mono

A slightly quirky grotesque for AI and tech explainers; monospaced numbers and labels feel like code.

Target frame: Vertical 9:16 (generic) (1080x1920).

## Fonts

| Role | Family | Weight | Licence | File | Average glyph width |
|---|---|---|---|---|---|
| Display (hooks, labels) | [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk) | 700 | OFL-1.1 | [SpaceGrotesk[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf) | 0.475 em |
| Captions | [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk) | 700 | OFL-1.1 | [SpaceGrotesk[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf) | 0.475 em |
| Numbers | [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) | 700 | OFL-1.1 | [JetBrainsMono[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf) | 0.600 em |

All families come from the Google Fonts repository under the SIL Open Font License 1.1 or Apache 2.0, which allow
use in videos and commercial work. If you redistribute the font files, include their licence; if you modify an
OFL font and redistribute it, follow the licence's naming rules. Licence, family name and file were read from
the repository on 2026-10-10; average glyph widths were measured with Pillow on a sample sentence.

## Sizes at 1080x1920

| Use | Size |
|---|---|
| Hook title | 84 px, about 21 characters per line |
| Captions | 58 px (min 46 px), about 31 characters per line |
| Labels (FACT N, STEP N) | 44 px |
| Key numbers | 100 px |

Characters per line assume 88% of the frame width minus panel padding.

## Install and use

```bash
mkdir -p fonts
curl -L -o "fonts/SpaceGrotesk[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/SpaceGrotesk[wght].ttf" wght=700 -o fonts/SpaceGrotesk-700.ttf
curl -L -o "fonts/JetBrainsMono[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"
python3 -m fontTools.varLib.instancer "fonts/JetBrainsMono[wght].ttf" wght=700 -o fonts/JetBrainsMono-700.ttf
```

```python
from PIL import ImageFont
font = ImageFont.truetype("fonts/SpaceGrotesk[wght].ttf", 84)
font.set_variation_by_axes([700])  # axes: wght
```

ffmpeg `drawtext` uses a variable font's default instance, so make a static weight first (the `fontTools`
command above) and pass `fontfile=fonts/SpaceGrotesk-700.ttf`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `typography_pairing_schema` contract schema, so the check runs without the catalogue.

## Sources
- Google Fonts repository (files and licences): https://github.com/google/fonts
- Specimens: https://fonts.google.com/specimen/Space+Grotesk
