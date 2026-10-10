# Detect content aspect and reframing method

Finds the content rectangle inside the frame, names its aspect ratio and decides how it was reframed - fit with bars, blur-pad, static pad, crop-zoom or full frame - from bars, fill correlation and upscale evidence.

Registry: family `geometry`, property `aspect_reframe`. Detects: Content aspect inside the frame and reframing method (crop, fit, blur-pad, zoom).
Payload contract: `video_re_contract_aspect_reframe` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_aspect_reframe` question bank citing this envelope.

## Method

Content aspect inside the frame and the reframing method: fit with bars, blur-pad, crop-zoom or full frame

(video_re_detect_aspect_reframe).

Method: the content rectangle comes from the edge-bar scan shared with the letterbox detector (solid bars,
blurred-fill bars, static textured fills). The method is then decided from evidence:
* fit: solid bars around the content;
* blur-pad: blurred-fill bars; the fill is compared with a blurred, stretched copy of the content itself
  (Pearson correlation of low-passed luma); a high value means the fill is the same footage blurred;
* static-pad: a non-moving textured fill (a still background graphic);
* crop-zoom: no bars but the content is upscaled (spectral cut-off; see video_re_detect_true_resolution),
  which is what cropping a wider source and scaling it up to fill the frame leaves behind;
* full-frame: no bars and native detail (native framing, or a crop of a higher-resolution source; pixels alone
  cannot tell those apart).
The content aspect is matched to common ratios within 3%.

Limits: the upscale test needs native-resolution pixels; the command line decodes a second, native centre crop
for it. Footage that was already soft looks upscaled. A crop of a higher-resolution source is indistinguishable
from native framing.

## Command line

```sh
python3 video_re_detect_aspect_reframe.py video.mp4 --out aspect_reframe.json
python3 video_re_detect_aspect_reframe.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_aspect_reframe as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `480`
- `fps`: `1.0`
- `max_frames`: `60`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `tol` = `12.0`
- `min_bar_px` = `2`
- `same_footage_corr` = `0.5`
- `zoom_factor` = `1.25`
- `ratio_tol` = `0.03`

## Limits

- A crop from a higher-resolution source looks the same as native framing.
- Soft footage can read as crop-zoom.

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
