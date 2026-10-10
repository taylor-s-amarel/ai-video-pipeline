---
name: "camera-parallax-dolly"
description: "Use when animating a still photo or layered image with the 'Parallax dolly (2.5D)' camera move: zoom and centre path, easing and a tested ffmpeg zoompan, Pillow or overlay command."
---

# Parallax dolly (2.5D)

Camera move for stills and layered images, 1080x1920.

## When to use
- Photos cut into layers: sky, middle, subject
- Layered 2.5D animation style

## Parameters

| Parameter | Value |
|---|---|
| Duration | 6 s |
| Zoom | 1.0 -> 1.06 |
| Centre | [0.47, 0.5] -> [0.53, 0.5] (fractions of the photo) |
| Easing | sine-in-out |
| Renderer | overlay-expr |
| Output | 1080x1920 at 30 fps |
| Intensity | standard |

## Render it

Cut the photo into layers saved as PNGs with transparency (background first). Each layer slides by
`speed x 65 px` with sine easing:

```bash
ffmpeg -y -loop 1 -t 6 -i background.png -loop 1 -t 6 -i midground.png -loop 1 -t 6 -i subject.png -filter_complex \
  "[0:v]scale=1188:2112[l0];[1:v]scale=1208:2150[l1];[2:v]scale=1230:2188[l2];color=c=black:s=1080x1920:r=30:d=6[c0];[c0][l0]overlay=x='(W-w)/2-20*(0.5-0.5*cos(PI*min(t,6)/6))':y='(H-h)/2':eval=frame:shortest=1[c1];[c1][l1]overlay=x='(W-w)/2-39*(0.5-0.5*cos(PI*min(t,6)/6))':y='(H-h)/2':eval=frame:shortest=1[c2];[c2][l2]overlay=x='(W-w)/2-65*(0.5-0.5*cos(PI*min(t,6)/6))':y='(H-h)/2':eval=frame:shortest=1[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p camera-parallax-dolly.mp4
```

Layers are scaled 8% (plus their zoom_extra) beyond the frame so the slide never reveals an edge.

Alternate moves between consecutive photos (in/out, left/right) so a slideshow never repeats the same motion.

The `short_style_preset_kit` code module has the maths used here (contrast, easing, springs, zoompan, xfade chains, grids, layer stacks, Pillow frosted panels). Place it with `python3 baltor/tools/baltor_catalog.py place short_style_preset_kit <step-dir>`; it lands in `.baltor/lib/short-style-preset-kit/`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `camera_move_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg zoompan, overlay and tmix filters: https://ffmpeg.org/ffmpeg-filters.html
