---
name: "camera-whip-pan"
description: "Use when animating a still photo or layered image with the 'Whip pan across the photo' camera move: zoom and centre path, easing and a tested ffmpeg zoompan, Pillow or overlay command."
---

# Whip pan across the photo

Camera move for stills and layered images, 1080x1920.

## When to use
- Bridging two shots
- Energetic edits

## Parameters

| Parameter | Value |
|---|---|
| Duration | 0.25 s |
| Zoom | 1.3 -> 1.3 |
| Centre | [0.3, 0.5] -> [0.7, 0.5] (fractions of the photo) |
| Easing | ease-in-out |
| Renderer | zoompan |
| Output | 1080x1920 at 30 fps |
| Intensity | standard |

## Render it

```bash
ffmpeg -y -i photo.jpg -vf "scale=4320:7680:force_original_aspect_ratio=increase,crop=4320:7680,zoompan=z='1.3+(0)*if(lt((on/7),0.5),4*pow((on/7),3),1-pow(-2*((on/7))+2,3)/2)':x='max(0,min(iw-iw/zoom,(0.3+(0.4)*if(lt((on/7),0.5),4*pow((on/7),3),1-pow(-2*((on/7))+2,3)/2))*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,(0.5+(0)*if(lt((on/7),0.5),4*pow((on/7),3),1-pow(-2*((on/7))+2,3)/2))*ih-ih/zoom/2))':d=8:s=1080x1920:fps=30,setsar=1,tmix=frames=3:weights='1 2 1'" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p camera-whip-pan.mp4
```

The filter first covers the 1080x1920 frame, then upscales 4x before `zoompan` so its whole-pixel steps are a
quarter of an output pixel (less jitter). Use it on a still image (no `-loop`); it outputs exactly
8 frames.

Alternate moves between consecutive photos (in/out, left/right) so a slideshow never repeats the same motion.

The `short_style_preset_kit` code module has the maths used here (contrast, easing, springs, zoompan, xfade chains, grids, layer stacks, Pillow frosted panels). Place it with `python3 baltor/tools/baltor_catalog.py place short_style_preset_kit <step-dir>`; it lands in `.baltor/lib/short-style-preset-kit/`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `camera_move_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg zoompan, overlay and tmix filters: https://ffmpeg.org/ffmpeg-filters.html
