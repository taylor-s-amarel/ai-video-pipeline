---
name: "caption-frosted-keyword-pop"
description: "Use when adding synced captions to a vertical short and you want the 'Frosted glass captions with keyword pop (house)' look: exact font, size, colours, backing, safe-area position, keyword emphasis and timing, with WCAG contrast already computed and an ffmpeg/Pillow recipe."
---

# Frosted glass captions with keyword pop (house)

Caption style for Vertical 9:16 (generic) (1080x1920). Palette `palette_house_yellow_night`. One synced line at a time. The key word (a number, name or outcome) turns keyword colour and pops 1.0 -> 1.12 -> 1.0 over 180 ms. No progress bars, stacked label panels or repeated section labels.

## When to use
- Any house-style short
- Facts and explainers with narration
- Footage or photos with busy detail behind the text

## Avoid when
- Silent videos where viewers read long sentences
- Comic looks that want outlined lettering

**House rules:** no progress bars, no stacked label panels, no repeated section labels.

## Parameters

| Parameter | Value |
|---|---|
| Font | Inter 800, 60 px (shrink to 48 px before wrapping), as-written |
| Fill | `#FFFFFF` |
| Backing | frosted glass: tint `#0B1220` at 62%, blur sigma 28 px, radius 28 px, padding 22/36 px, feather 16 px |
| Outline | none |
| Position | centre at 76% of the height, max width 88%, aligned center |
| Safe area | top 8%, bottom 20%, left 6%, right 6% |
| Lines | 1 line(s), at most 7 words and about 30 characters per line |
| Keyword | keyword-pop: colour `#FFD21F`, scale to 1.12x and back over 180 ms (ease-out-back) |
| Timing | within 150 ms of the spoken word; on screen 700-3200 ms |
| Entry | `text_anim_fade_up_soft`; keyword `text_anim_keyword_pop_house` |

All numbers are in `preset.json`. Sizes are pixels at 1080x1920.

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| text | `#FFFFFF` | panel `#0B1220` at 62%, worst case over any video | 5.26:1 | 3:1 (>= 24 px bold) |
| keyword | `#FFD21F` | panel `#0B1220` at 62%, worst case over any video | 3.63:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases: the panel colour is computed over pure black and pure white video, so no
frame underneath can make the text less readable than this. Thresholds: 4.5:1, or 3:1 only for text that
is at least 24 px and weight 700 (stricter than WCAG's large-text rule). See https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.

## Render it

### 1. Fonts (OFL-1.1)

```bash
mkdir -p fonts
curl -L -o "fonts/Inter[opsz,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Inter[opsz,wght].ttf" wght=800 -o fonts/Inter-800.ttf
```

### 2. One static line with ffmpeg

Draws the panel and line from 0.5 s to 2.5 s over `in.mp4` (1080x1920). Replace the text and times
per caption (one `enable` window per line), or generate the graph per line from `preset.json`.

```bash
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=802:122:138:1396,gblur=sigma=28,drawbox=x=0:y=0:w=iw:h=ih:color=0x0B1220@0.62:t=fill,format=yuva420p[glass];color=c=black:s=802x122:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(28-X,X-(W-1-28)),0)*gt(max(28-Y,Y-(H-1-28)),0),(28-hypot(max(max(28-X,X-(W-1-28)),0),max(max(28-Y,Y-(H-1-28)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/16,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=138:1396:shortest=1:enable='between(t,0.5,2.5)',drawtext=fontfile=fonts/Inter-800.ttf:text='One synced line at a time':fontsize=60:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=1457-text_h/2:enable='between(t,0.5,2.5)'[v]" \
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
                                 font_path="fonts/Inter-800.ttf", margins=style["target"]["safe_margins"])
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
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/inter/OFL.txt
