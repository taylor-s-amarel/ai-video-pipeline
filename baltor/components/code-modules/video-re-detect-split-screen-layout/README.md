# Detect split-screen and grid layouts

Finds split-screen and grid layouts (1x2, 2x1, 2x2, 3-up, custom) and their panel rectangles, gutter width and colour from seams where neighbouring pixels belong to different pictures over time.

Registry: family `geometry`, property `split_screen_layout`. Detects: Grid and split layouts: 1x2, 2x1, 2x2, 3-up, with panel rects.
Payload contract: `video_re_contract_split_screen_layout` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_split_screen_layout` question bank citing this envelope.

## Method

Split-screen and grid layouts (1x2, 2x1, 2x2, 3-up ...) with panel rectangles

(video_re_detect_split_screen_layout).

Method: a seam between two panels is a line where neighbouring pixels belong to different pictures. Over sampled
frames the time-mean absolute difference across each column boundary (and row boundary) is compared with the
same quantity two to four pixels away on both sides; a seam pixel is at least 2x its neighbourhood and at least
3/255. A seam must cover at least 80% of the region it splits. The frame is split recursively (guillotine
cuts, at most 3 levels): the strongest seam splits a region, a second seam within 4% of the size is read as
the other side of a gutter, and both halves are searched again. Regions narrower than 12% of the frame are not
split further. More than 3 seams of similar strength on one axis at the top level means a striped texture,
not a layout, and the frame is left whole. Panels are classified as a grid (rows x columns) when the cuts line
up, otherwise as 3-up arrangements or custom-N.

Layout names are rows x columns: 1x2 = two panels side by side, 2x1 = two panels stacked.
Limits: panels whose content is identical across the seam (mirrored or duplicated video) leave no seam; a static
scene with a straight full-height edge (a door frame, a horizon) can be read as a seam when the camera never
moves; picture-in-picture insets are left to video_re_detect_picture_in_picture.

## Command line

```sh
python3 video_re_detect_split_screen_layout.py video.mp4 --out split_screen_layout.json
python3 video_re_detect_split_screen_layout.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_split_screen_layout as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `320`
- `fps`: `2.0`
- `max_frames`: `60`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `ratio_thr` = `2.0`
- `abs_min` = `3.0`
- `span_thr` = `0.8`
- `max_gutter_frac` = `0.04`
- `min_panel_frac` = `0.12`
- `max_depth` = `3`
- `texture_guard` = `3`
- `edge_margin_frac` = `0.06`

## Limits

- Duplicated or mirrored panels leave no seam.
- A static scene with a straight full-height edge can be read as a seam.
- Insets that do not span the frame are picture-in-picture, measured by another detector.

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
