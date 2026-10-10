# Detect corner radius of panels and photos

Measures the corner radius of cards, panels, photos and insets by fitting circles to the outline insets at each corner, from static-element masks over moving backgrounds, edge maps or given rectangles.

Registry: family `geometry`, property `rounded_corners`. Detects: Corner radius of photos/panels estimated from alpha/edge curvature.
Payload contract: `video_re_contract_rounded_corners` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_rounded_corners` question bank citing this envelope.

## Method

Corner radius of photos, cards and panels, estimated from the curvature of their outline

(video_re_detect_rounded_corners).

Method: elements are found in two ways. (1) Static elements over a moving background (cards, captions panels,
framed photos): pixels whose temporal standard deviation stays below 3/255 while the frame's median is above
6/255 form a mask; connected components covering 1-60% of the frame, not touching the frame edge, are the
elements and the mask gives their outline exactly. (2) Elements given by the caller (``--param rects=[[x,y,w,h]]``
in analysis pixels, e.g. from the picture-in-picture or frosted-panel detectors) or found as rectangles in edge
maps: their outline is the first marked pixel (edge persistence or seam) met when walking inwards from the
bounding box. For each corner the inset of the outline over the rows (and, symmetrically, columns) next to the
corner is fitted with a circle, r - sqrt(r^2 - (r - i - 0.5)^2), by grid search in 0.25 px steps. The element
radius is the median of the four corners; ``shape`` is rect (r < 1.5 px), rounded, or pill (r >= 0.45 x the short
side). Radii are in source pixels.

Limits: non-circular corners (squircles, chamfers) are reported with the best circle and a larger fit error;
antialiasing and analysis downscaling limit precision to about one analysis pixel; elements that move or
whose content blends into the background need given rectangles and clear edges.

## Command line

```sh
python3 video_re_detect_rounded_corners.py video.mp4 --out rounded_corners.json
python3 video_re_detect_rounded_corners.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_rounded_corners as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `480`
- `fps`: `2.0`
- `max_frames`: `60`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `static_tstd` = `3.0`
- `moving_min_tstd` = `6.0`
- `min_area` = `0.01`
- `max_area` = `0.6`
- `min_fill` = `0.6`
- `edge_thr` = `0.6`
- `pill_ratio` = `0.45`
- `rect_corner_gap` = `24`
- `rects` = `null`

## Limits

- Squircles and chamfers get the best-fitting circle and a larger fit error.
- Precision is about one analysis pixel (default 480 px wide) times the scale.
- Moving elements need rectangles from another detector.

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
