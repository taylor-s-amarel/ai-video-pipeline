---
name: "caption-handwritten-note"
description: "Use when adding synced captions to a vertical short and you want the 'Handwritten note captions' look: exact font, size, colours, backing, safe-area position, keyword emphasis and timing, with WCAG contrast already computed and an ffmpeg/Pillow recipe."
---

# Handwritten note captions

Caption style for Vertical 9:16 (generic) (1080x1920). Palette `palette_meadow_morning`. Patrick Hand has one weight; its contrast check uses the regular-weight threshold (4.5:1).

## When to use
- Stick-figure and doodle stories
- Personal tips

## Avoid when
- Serious or formal topics

## Parameters

| Parameter | Value |
|---|---|
| Font | Patrick Hand 400, 64 px (shrink to 52 px before wrapping), as-written |
| Fill | `#10230F` |
| Backing | soft scrim: tint `#FFFFFF` at 80%, radius 18 px, padding 14/28 px, feather 22 px |
| Outline | none |
| Position | centre at 76% of the height, max width 86%, aligned center |
| Safe area | top 8%, bottom 20%, left 6%, right 6% |
| Lines | 1 line(s), at most 7 words and about 38 characters per line |
| Keyword | underline: colour `#1E5E12` |
| Timing | within 150 ms of the spoken word; on screen 800-3200 ms |
| Entry | `text_anim_mask_reveal_up` |

All numbers are in `preset.json`. Sizes are pixels at 1080x1920.

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| text | `#10230F` | panel `#FFFFFF` at 80%, worst case over any video | 10.30:1 | 4.5:1 |
| underline | `#1E5E12` | panel `#FFFFFF` at 80%, worst case over any video | 4.90:1 | 3:1 (non-text graphic) |

Panel ratios are worst cases: the panel colour is computed over pure black and pure white video, so no
frame underneath can make the text less readable than this. Thresholds: 4.5:1, or 3:1 only for text that
is at least 24 px and weight 700 (stricter than WCAG's large-text rule). See https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.

## Render it

### 1. Fonts (OFL-1.1)

```bash
mkdir -p fonts
curl -L -o "fonts/PatrickHand-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/patrickhand/PatrickHand-Regular.ttf"
```

### 2. One static line with ffmpeg

Draws the panel and line from 0.5 s to 2.5 s over `in.mp4` (1080x1920). Replace the text and times
per caption (one `enable` window per line), or generate the graph per line from `preset.json`.

```bash
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=616:110:232:1408,drawbox=x=0:y=0:w=iw:h=ih:color=0xFFFFFF@0.8:t=fill,format=yuva420p[glass];color=c=black:s=616x110:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(18-X,X-(W-1-18)),0)*gt(max(18-Y,Y-(H-1-18)),0),(18-hypot(max(max(18-X,X-(W-1-18)),0),max(max(18-Y,Y-(H-1-18)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/22,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=232:1408:shortest=1:enable='between(t,0.5,2.5)',drawtext=fontfile=fonts/PatrickHand-Regular.ttf:text='One synced line at a time':fontsize=64:fontcolor=0x10230F:x=(w-text_w)/2:y=1463-text_h/2:enable='between(t,0.5,2.5)'[v]" \
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
words = "One synced line at a time".split()
out = kit.render_caption_preview(frame, words, style, keyword_index=1, t_ms=90,
                                 font_path="fonts/PatrickHand-Regular.ttf", margins=style["target"]["safe_margins"])
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
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/patrickhand/OFL.txt
