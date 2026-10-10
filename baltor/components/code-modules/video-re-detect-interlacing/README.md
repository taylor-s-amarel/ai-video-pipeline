# Detect interlacing and field order

Detects combing from woven fields on moving pixels, decides top- or bottom-field-first from field-to-field distances, flags telecine-like patterns and adds ffmpeg idet counts and ffprobe field_order.

Registry: family `geometry`, property `interlacing`. Detects: Combing artefacts and field order.
Payload contract: `video_re_contract_interlacing` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_interlacing` question bank citing this envelope.

## Method

Interlacing: combing artefacts and field order (video_re_detect_interlacing).

Method: frames are decoded at native resolution (a centre crop of at most 720 x 480 px with even offsets, so field
parity is kept; no scaling, which would destroy combing). On pixels that move (|frame - previous| >= 6/255),
the inter-field second difference |2I(y) - I(y-1) - I(y+1)| is compared with the intra-field one
|2I(y) - I(y-2) - I(y+2)|. Progressive pictures are smooth, so the first is the smaller; woven fields of a moving
scene make it larger. A frame is combed when the ratio of their sums is >= 1.3. Field order is tested on the
fields themselves: with top field first, the bottom field of frame n is half a frame from the top field of frame
n+1 and the opposite pairing is one and a half frames apart, so mean |B(n) - T(n+1)| (bottom field resampled to
top-field lines, both fields blurred with sigma 2 px so the difference keeps growing with displacement) is the
smaller one; with bottom field first it is the reverse (decision margin 15%).
A combed share of 0.3-0.55 with two combed frames in every five is reported as telecine-like (3:2 pulldown).
The command line also runs ffmpeg's idet filter and reports its multi-frame counts, and ffprobe's field_order.

Limits: still or vertically uniform content shows no combing either way (frames without motion are not
counted); deinterlaced-then-encoded video is progressive here even if it was shot interlaced; scaled interlaced
video loses its combing pattern.

## Command line

```sh
python3 video_re_detect_interlacing.py video.mp4 --out interlacing.json
python3 video_re_detect_interlacing.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_interlacing as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `0`
- `fps`: `0`
- `max_frames`: `120`
- `crop`: `[720, 480]`
- `crop_align`: `4`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `motion_thr` = `6.0`
- `min_moving_share` = `0.01`
- `comb_ratio` = `1.3`
- `interlaced_share` = `0.3`
- `order_margin` = `0.15`
- `field_blur` = `2.0`
- `idet_frames` = `300`

## Limits

- Still or vertically uniform content cannot show combing.
- Scaled or deinterlaced video reads as progressive.

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
