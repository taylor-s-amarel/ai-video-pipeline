# Detect letterbox and pillarbox bars

Finds solid or blurred-fill bars on each frame edge of a video and reports their size in source pixels, colour, style and the content rectangle, as a detection envelope.

Registry: family `geometry`, property `letterbox_pillarbox`. Detects: Bars top/bottom or left/right: sizes in px, colour, blurred-fill vs solid.
Payload contract: `video_re_contract_letterbox_pillarbox` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_letterbox_pillarbox` question bank citing this envelope.

## Method

Letterbox / pillarbox bars: sizes in px, colour, and blurred-fill vs solid (video_re_detect_letterbox_pillarbox).

Method: frames are sampled (default 1 per second at 480 px wide). For every frame edge, lines (rows for
top/bottom, columns for left/right) are scanned inwards. A solid bar line has at least 97% of its pixels within
12/255 of the bar colour (the median colour of the outermost line); static text or a logo inside the bar is
allowed if the bar resumes after it. Thickness is the 10th percentile of the per-frame runs so dark content
touching the bar in a few frames does not widen it. When no solid bar exists, a blurred-fill bar is a run of
lines whose mean gradient is below 0.2 x the centre's while still changing over time (the usual
"blurred copy of the video behind it" fill). Sizes are reported in source pixels (analysis px x scale).

Limits: a bar colour that also fills the content edge on every sampled frame (black background graphics
touching a black bar) is counted as bar; gradient or patterned fills are reported as static-texture when they do
not move; precision is about one analysis pixel times the scale (reported as px_precision).

## Command line

```sh
python3 video_re_detect_letterbox_pillarbox.py video.mp4 --out letterbox_pillarbox.json
python3 video_re_detect_letterbox_pillarbox.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_letterbox_pillarbox as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `480`
- `fps`: `1.0`
- `max_frames`: `90`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `tol` = `12.0`
- `pixel_frac` = `0.97`
- `frame_quorum` = `0.9`
- `blur_ratio` = `0.2`
- `min_bar_px` = `2`
- `overlay_frac` = `0.5`
- `overlay_tstd` = `3.0`

## Limits

- Content whose edge matches the bar colour in every sampled frame is counted as bar.
- Gradient or patterned fills that never move are reported as static-texture, not as a fill method.
- Sizes are measured at the analysis width (default 480 px) and scaled; px_precision gives the step.

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
