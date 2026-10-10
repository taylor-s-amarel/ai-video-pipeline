# Measure how close overlays get to the frame edges

Measures the closest approach of captions, titles, logos and other static overlays to each frame edge (px, share of frame, time), from static-detail masks or text boxes from evidence.json.

Registry: family `geometry`, property `safe_margin_usage`. Detects: How close important content and text get to platform UI zones.
Payload contract: `video_re_contract_safe_margin_usage` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_safe_margin_usage` question bank citing this envelope.

## Method

How close text, logos and other overlays get to the frame edges, where platform UI sits

(video_re_detect_safe_margin_usage).

Method: overlays (captions, titles, stickers, logos) are detailed but hold still while the picture under them
changes. Frames are sampled (default 2 per second at 360 px wide) and grouped into 2-second windows. In each
window a pixel is overlay detail when its time-mean gradient magnitude is at least 8/255 and 2.5x the frame's
median, and its temporal standard deviation is at most 8/255; pixels are kept only inside 8x8 blocks where at
least 10% of pixels qualify (removes speckle). The extreme overlay pixels give that window's distance to each
frame edge. The payload reports the closest approach per side over the whole video (and when it happened),
the 10th-percentile margin, and margins as a share of the frame size. Caller-supplied text boxes
(``--param regions=evidence.json`` with ``text_regions``, or a JSON list of [x, y, w, h] in source pixels) are
used instead when given. Platform UI zones differ by app and change over time, so none are assumed here;
compare these margins with a zone map (video_re_safe_area_probe) to judge violations.

Limits: overlays that move (scrolling tickers, bouncing stickers) are missed unless regions are given; a static
detailed background (screen recording, still photo) reads as overlay everywhere and is flagged with
``static_background``; hairline graphics under 8/255 contrast are ignored.

## Command line

```sh
python3 video_re_detect_safe_margin_usage.py video.mp4 --out safe_margin_usage.json
python3 video_re_detect_safe_margin_usage.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_safe_margin_usage as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `360`
- `fps`: `2.0`
- `max_frames`: `240`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `window_s` = `2.0`
- `grad_abs` = `8.0`
- `grad_rel` = `2.5`
- `static_tstd` = `8.0`
- `block` = `8`
- `block_frac` = `0.1`
- `static_bg_share` = `0.5`
- `regions` = `null`

## Limits

- Moving overlays are missed unless text boxes are given.
- A static detailed background (screen recording, still photo) is flagged and not measured.

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
