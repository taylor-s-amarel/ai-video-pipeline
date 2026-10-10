---
name: "caption-outline-bold-center"
description: "Use when adding synced captions to a vertical short and you want the 'Bold outlined captions, centred' look: exact font, size, colours, backing, safe-area position, keyword emphasis and timing, with WCAG contrast already computed and an ffmpeg/Pillow recipe."
---

# Bold outlined captions, centred

Caption style for Vertical 9:16 (generic) (1080x1920). Palette `palette_house_yellow_night`. The 7 px outline carries the contrast, so the fill/outline pair is what the contrast check measures. Keep the outline at least 10% of the font size.

## When to use
- Fast talking-head or gameplay clips
- Bright footage where a panel would hide too much

## Avoid when
- Thin or detailed fonts (the outline needs a heavy weight)
- Long sentences

## Parameters

| Parameter | Value |
|---|---|
| Font | Montserrat 800, 70 px (shrink to 56 px before wrapping), upper |
| Fill | `#FFFFFF` |
| Backing | none; the outline carries the contrast |
| Outline | 7 px `#000000` |
| Position | centre at 62% of the height, max width 86%, aligned center |
| Safe area | top 8%, bottom 20%, left 6%, right 6% |
| Lines | 2 line(s), at most 4 words and about 20 characters per line |
| Keyword | color: colour `#FFD21F` |
| Timing | within 120 ms of the spoken word; on screen 500-2000 ms |
| Entry | `text_anim_springy_pop_overshoot` |

All numbers are in `preset.json`. Sizes are pixels at 1080x1920.

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| text | `#FFFFFF` | outline `#000000` (7 px) | 21.00:1 | 3:1 (>= 24 px bold) |
| keyword | `#FFD21F` | outline `#000000` (7 px) | 14.49:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases: the panel colour is computed over pure black and pure white video, so no
frame underneath can make the text less readable than this. Thresholds: 4.5:1, or 3:1 only for text that
is at least 24 px and weight 700 (stricter than WCAG's large-text rule). See https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.

## Render it

### 1. Fonts (OFL-1.1)

```bash
mkdir -p fonts
curl -L -o "fonts/Montserrat[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Montserrat[wght].ttf" wght=800 -o fonts/Montserrat-800.ttf
```

### 2. One static line with ffmpeg

Draws the line from 0.5 s to 2.5 s over `in.mp4` (1080x1920). Replace the text and times
per caption (one `enable` window per line), or generate the graph per line from `preset.json`.

```bash
ffmpeg -y -i in.mp4 -filter_complex "[0:v]drawtext=fontfile=fonts/Montserrat-800.ttf:text='BIG BOLD WORDS':fontsize=70:fontcolor=0xFFFFFF:borderw=7:bordercolor=0x000000:x=(w-text_w)/2:y=1190-text_h/2:enable='between(t,0.5,2.5)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p captioned.mp4
```

### 3. Per-word effects with Pillow

ffmpeg's drawtext cannot pop one word inside a line. Render those frames with Pillow:

```python
import json, sys
from PIL import Image
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

style = json.load(open("preset.json"))
frame = Image.open("frame.png").convert("RGB")          # a 1080x1920 frame from your video
words = "BIG BOLD WORDS".split()
out = kit.render_caption_preview(frame, words, style, keyword_index=1, t_ms=90,
                                 font_path="fonts/Montserrat-800.ttf", margins=style["target"]["safe_margins"])
out.save("caption_preview.png")
```

For a full video, extract frames (`ffmpeg -i in.mp4 frames/%06d.png`), draw each caption on the frames inside
its time window with `t_ms` measured from the keyword's start, then encode
(`ffmpeg -framerate 30 -i frames/%06d.png -i in.mp4 -map 0:v -map 1:a? -c:v libx264 -pix_fmt yuv420p out.mp4`).

The `short_style_preset_kit` code module has the maths used here (contrast, easing, springs, zoompan, xfade chains, grids, layer stacks, Pillow frosted panels). Place it with `python3 baltor/tools/baltor_catalog.py place short_style_preset_kit <step-dir>`; it lands in `.baltor/lib/short-style-preset-kit/`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `caption_style_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
- ffmpeg filters (drawtext, gblur, alphamerge, overlay): https://ffmpeg.org/ffmpeg-filters.html
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/OFL.txt
