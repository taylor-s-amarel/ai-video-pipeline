# Detect picture-in-picture insets

Finds inset windows (facecams, reaction clips, overlaid photos) as rectangles whose outline stays put while the pictures change, with corner, margins, border, drop-shadow direction and on-screen interval.

Registry: family `geometry`, property `picture_in_picture`. Detects: Inset windows: rect, corner, border, shadow, duration.
Payload contract: `video_re_contract_picture_in_picture` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_picture_in_picture` question bank citing this envelope.

## Method

Picture-in-picture insets: rectangle, corner, border, shadow and on-screen time

(video_re_detect_picture_in_picture).

Method: frames are sampled (default 4 per second at 320 px wide) and grouped into windows of about one second.
Inside a window, an inset's outline is the only straight edge that stays put while the pictures inside and
outside it change. Two maps mark it: per-pixel edge persistence (share of frames with a strong gradient, for
bordered or contrasting insets) and the seam test shared with the split-screen detector (time-mean difference
across a boundary at least 2x that of its neighbours, for borderless insets between unrelated pictures).
Straight runs (gaps up to 8 px bridged) propose side positions; a rectangle is kept when each of its four
sides is marked along at least 60% of its length (corners excepted).
Rectangles covering 2-50% of the frame and not spanning it are kept. Rectangles nested within 12 px are one
inset: equal gaps on all sides are a border (width = gap, colour = median of the ring); gaps on two adjacent
sides only are a hard offset shadow (offset = the gaps). A soft drop shadow is reported when a 6 px band outside
two adjacent sides is consistently darker (>= 8/255) than the band on the opposite sides. Windows are linked
by overlap (IoU >= 0.6) into on-screen intervals; one missed window does not end an interval.

Limits: an inset over a static background whose own edges are also static can be confused with background
structure (support is lower); insets that move or scale are tracked only while they stay within the IoU link;
rounded insets need the corner gap allowance (see video_re_detect_rounded_corners for the radius); timing
resolution is one window.

## Command line

```sh
python3 video_re_detect_picture_in_picture.py video.mp4 --out picture_in_picture.json
python3 video_re_detect_picture_in_picture.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_picture_in_picture as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `320`
- `fps`: `4.0`
- `max_frames`: `480`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `window_s` = `1.0`
- `persist_thr` = `0.7`
- `min_area` = `0.02`
- `max_area` = `0.5`
- `max_span` = `0.9`
- `nest_px` = `12`
- `link_iou` = `0.6`
- `max_gap` = `8`
- `min_cover` = `0.6`
- `max_missed_windows` = `1`
- `shadow_band` = `6`
- `shadow_min_diff` = `8.0`
- `corner_gap` = `6`

## Limits

- Static backgrounds with rectangular structure lower the support and can produce false insets.
- Moving or scaling insets are only linked while consecutive windows overlap by IoU >= 0.6.
- Timing resolution is one window (default 1 s).

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
