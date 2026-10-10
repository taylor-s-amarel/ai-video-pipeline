---
name: "camera-slow-rotate-drift"
description: "Use when animating a still photo or layered image with the 'Slow rotate drift' camera move: zoom and centre path, easing and a tested ffmpeg zoompan, Pillow or overlay command."
---

# Slow rotate drift

Camera move for stills and layered images, 1080x1920.

## When to use
- Dreamy and relationship looks
- Paper and collage looks

## Parameters

| Parameter | Value |
|---|---|
| Duration | 6 s |
| Zoom | 1.12 -> 1.12 |
| Centre | [0.5, 0.5] -> [0.5, 0.5] (fractions of the photo) |
| Easing | sine-in-out |
| Renderer | pillow |
| Output | 1080x1920 at 30 fps |
| Intensity | standard |
| Rotation | -1.5 -> 1.5 deg |

## Render it

Rotation and shake are not expressible in `zoompan`; render frames with Pillow (bicubic, sub-pixel):

```python
import json, subprocess, sys
from PIL import Image
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

move = json.load(open("preset.json"))
enc = subprocess.Popen(["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "camera-slow-rotate-drift.mp4"], stdin=subprocess.PIPE)
for frame in kit.camera_frames(Image.open("photo.jpg"), move, (1080, 1920), fps=30):
    enc.stdin.write(frame.tobytes())
enc.stdin.close(); enc.wait()
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
