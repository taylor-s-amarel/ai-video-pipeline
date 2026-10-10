---
name: "caption-pill-per-line"
description: "Use when adding synced captions to a vertical short and you want the 'Rounded pill captions' look: exact font, size, colours, backing, safe-area position, keyword emphasis and timing, with WCAG contrast already computed and an ffmpeg/Pillow recipe."
---

# Rounded pill captions

Caption style for Vertical 9:16 (generic) (1080x1920). Palette `palette_sunset_coral`.

## When to use
- Friendly topics: relationships, pets, lifestyle
- Rounded typefaces

## Avoid when
- Serious news and history

## Parameters

| Parameter | Value |
|---|---|
| Font | Fredoka 700, 58 px (shrink to 46 px before wrapping), as-written |
| Fill | `#FFFFFF` |
| Backing | pill: tint `#1E1230` at 70%, blur sigma 12 px, radius 999 px, padding 18/40 px, feather 6 px |
| Outline | none |
| Position | centre at 76% of the height, max width 86%, aligned center |
| Safe area | top 8%, bottom 20%, left 6%, right 6% |
| Lines | 1 line(s), at most 6 words and about 33 characters per line |
| Keyword | color: colour `#FFB4B4`, scale to 1.06x and back over 160 ms (ease-out) |
| Timing | within 150 ms of the spoken word; on screen 700-3000 ms |
| Entry | `text_anim_springy_pop_overshoot` |

All numbers are in `preset.json`. Sizes are pixels at 1080x1920.

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| text | `#FFFFFF` | panel `#1E1230` at 70%, worst case over any video | 6.62:1 | 3:1 (>= 24 px bold) |
| keyword | `#FFB4B4` | panel `#1E1230` at 70%, worst case over any video | 3.92:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases: the panel colour is computed over pure black and pure white video, so no
frame underneath can make the text less readable than this. Thresholds: 4.5:1, or 3:1 only for text that
is at least 24 px and weight 700 (stricter than WCAG's large-text rule). See https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.

## Render it

### 1. Fonts (OFL-1.1)

```bash
mkdir -p fonts
curl -L -o "fonts/Fredoka[wdth,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/fredoka/Fredoka%5Bwdth%2Cwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Fredoka[wdth,wght].ttf" wght=700 wdth=100 -o fonts/Fredoka-700.ttf
```

### 2. One static line with ffmpeg

Draws the panel and line from 0.5 s to 2.5 s over `in.mp4` (1080x1920). Replace the text and times
per caption (one `enable` window per line), or generate the graph per line from `preset.json`.

```bash
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=718:110:180:1408,drawbox=x=0:y=0:w=iw:h=ih:color=0x1E1230@0.7:t=fill,format=yuva420p[glass];color=c=black:s=718x110:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(55-X,X-(W-1-55)),0)*gt(max(55-Y,Y-(H-1-55)),0),(55-hypot(max(max(55-X,X-(W-1-55)),0),max(max(55-Y,Y-(H-1-55)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/6,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=180:1408:shortest=1:enable='between(t,0.5,2.5)',drawtext=fontfile=fonts/Fredoka-700.ttf:text='One synced line at a time':fontsize=58:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=1463-text_h/2:enable='between(t,0.5,2.5)'[v]" \
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
                                 font_path="fonts/Fredoka-700.ttf", margins=style["target"]["safe_margins"])
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
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/fredoka/OFL.txt
