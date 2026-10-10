---
name: "camera-alternating-zoom-pair"
description: "Use when animating a still photo or layered image with the 'Alternating zoom pair' camera move: zoom and centre path, easing and a tested ffmpeg zoompan, Pillow or overlay command."
---

# Alternating zoom pair

Camera move for stills and layered images, 1080x1920.

## When to use
- Quick cuts where consecutive shots alternate in and out
- Keeping stills alive without repetition

## Parameters

| Parameter | Value |
|---|---|
| Duration | 3 s |
| Zoom | 1.0 -> 1.08 |
| Centre | [0.5, 0.5] -> [0.5, 0.46] (fractions of the photo) |
| Easing | sine-in-out |
| Renderer | zoompan |
| Output | 1080x1920 at 30 fps |
| Intensity | standard |

## Render it

```bash
ffmpeg -y -i photo.jpg -vf "scale=4320:7680:force_original_aspect_ratio=increase,crop=4320:7680,zoompan=z='1+(0.08)*(0.5-0.5*cos(PI*((on/89))))':x='max(0,min(iw-iw/zoom,(0.5+(0)*(0.5-0.5*cos(PI*((on/89)))))*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,(0.5+(-0.04)*(0.5-0.5*cos(PI*((on/89)))))*ih-ih/zoom/2))':d=90:s=1080x1920:fps=30,setsar=1" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p camera-alternating-zoom-pair.mp4
```

The filter first covers the 1080x1920 frame, then upscales 4x before `zoompan` so its whole-pixel steps are a
quarter of an output pixel (less jitter). Use it on a still image (no `-loop`); it outputs exactly
90 frames.

The second shot of the pair reverses the move:

```bash
ffmpeg -y -i photo2.jpg -vf "scale=4320:7680:force_original_aspect_ratio=increase,crop=4320:7680,zoompan=z='1.08+(-0.08)*(0.5-0.5*cos(PI*((on/89))))':x='max(0,min(iw-iw/zoom,(0.5+(0)*(0.5-0.5*cos(PI*((on/89)))))*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,(0.46+(0.04)*(0.5-0.5*cos(PI*((on/89)))))*ih-ih/zoom/2))':d=90:s=1080x1920:fps=30,setsar=1" -c:v libx264 -crf 18 -pix_fmt yuv420p camera-alternating-zoom-pair-b.mp4
```

Alternate moves between consecutive photos (in/out, left/right) so a slideshow never repeats the same motion.

The `short_style_preset_kit` code module has the maths used here (contrast, easing, springs, zoompan, xfade chains, grids, layer stacks, Pillow frosted panels). Place it with `python3 baltor/tools/baltor_catalog.py place short_style_preset_kit <step-dir>`; it lands in `.baltor/lib/short-style-preset-kit/`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `camera_move_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg zoompan, overlay and tmix filters: https://ffmpeg.org/ffmpeg-filters.html
