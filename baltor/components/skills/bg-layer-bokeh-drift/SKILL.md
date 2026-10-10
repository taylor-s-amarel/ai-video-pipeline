---
name: "bg-layer-bokeh-drift"
description: "Use when a short needs the 'Bokeh drift' moving background or overlay layer: a seamless 8-second procedural ffmpeg loop (no downloads), default opacity and blend, measured motion, and how to source licensed footage instead."
---

# Bokeh drift

Large out-of-focus discs floating upward at two depths. Category: procedural-particles; usual stack role: particles.

## When to use
- Feelings
- celebrations
- dreamy looks

## Layer defaults

| Setting | Value |
|---|---|
| Opacity | 0.3 (house cap 0.98) |
| Blend | screen |
| Motion | rise, seamless every 8 s |
| Size | 1080x1920 at 30 fps |



## Render the loop (procedural, no downloads)

```bash
ffmpeg -y -filter_complex "$(cat filtergraph.txt)" -map "[out]" -t 8 -r 30 \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart bg-layer-bokeh-drift.mp4
# stretch the loop under a full-length edit
ffmpeg -y -stream_loop -1 -i bg-layer-bokeh-drift.mp4 -t 64 -c copy bg-layer-bokeh-drift-64s.mp4
```

`filtergraph.txt` builds the image with ffmpeg's `geq` (per-pixel expressions), `scroll`, `blend`, `displace`
and a `lutrgb` gradient map, at reduced working resolution where the look is soft, then scales to 1080x1920.
Every time term repeats every 8 s and every scrolled texture moves a whole tile per loop,
so the file loops without a seam. Tested with FFmpeg 6.1.1.

Colour stops (gray value -> colour): 0 `#000000`, 140 `#5C4B8A`, 220 `#F2B8C6`, 255 `#FFFFFF`.

## Put it in a stack

```bash
# [base] is everything below this layer; ffmpeg's blend uses the first input as the base
ffmpeg -i base.mp4 -i bg-layer-bokeh-drift.mp4 -filter_complex \
  "[0:v]format=gbrp[a];[1:v]format=gbrp[b];[a][b]blend=all_mode=screen:all_opacity=0.3:shortest=1,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 18 stacked.mp4
```

For `normal` blending put the layer first (`[b][a]blend=all_mode=normal`), because ffmpeg's normal mode weights
the first input by the opacity. The `short_style_preset_kit` module's `layer_stack_filter` handles both orders for whole stacks.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `background_layer_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg filters (geq, scroll, blend, displace, lutrgb): https://ffmpeg.org/ffmpeg-filters.html
