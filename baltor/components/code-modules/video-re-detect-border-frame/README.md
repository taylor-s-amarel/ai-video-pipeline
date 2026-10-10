# Detect a decorative border frame

Measures a static border or padding frame around moving video content - width per side in source px, solid/gradient/textured colour and the inner corner radius.

Registry: family `geometry`, property `border_frame`. Detects: Decorative borders/padding around the content: width per side, colour or gradient, inner radius.
Payload contract: `video_re_contract_border_frame` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_border_frame` question bank citing this envelope.

## Method

Decorative border / padding frame around moving content: width per side, colour or gradient, inner radius

(video_re_detect_border_frame).

Method: the border of a framed video is static while the content inside moves. Per pixel temporal standard
deviation over the sampled frames separates static pixels (std <= 3/255 by default). Each side is scanned
inwards: a line belongs to the border while at least 95% of its pixels are static. Border pixels are then
described: solid when their colour spread is within 8/255, gradient when a linear colour ramp over (x, y)
explains at least 80% of the variance, otherwise textured. The inner corner radius is fitted to the inset of
static pixels along the first rows inside each corner of the content rectangle (circle model, grid search),
and the median of the four corners is reported. Sizes are in source pixels.

Limits: needs moving content (a still image has no static/moving contrast and returns status partial); a static
title or logo touching the frame edge across a whole side can be read as border; borders thinner than one
analysis pixel are not resolved; outer rounding of the whole frame is not measured.

## Command line

```sh
python3 video_re_detect_border_frame.py video.mp4 --out border_frame.json
python3 video_re_detect_border_frame.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_border_frame as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `480`
- `fps`: `2.0`
- `max_frames`: `60`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `static_tstd` = `3.0`
- `line_static_frac` = `0.95`
- `solid_tol` = `8.0`
- `gradient_r2` = `0.8`
- `min_px` = `2`
- `max_frac` = `0.25`
- `min_sides` = `3`
- `moving_min_tstd` = `4.0`

## Limits

- Needs moving content; still images return status partial.
- A static title or logo spanning a whole side reads as border.
- Only the inner corner radius is measured, not rounding of the outer frame.

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
