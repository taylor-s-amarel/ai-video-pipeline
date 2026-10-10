# Detect true (effective) resolution and upscaling

Estimates how much detail a video really holds versus its container size from the high-frequency power spectrum, per axis and per tile, and flags upscaled footage or native graphics over upscaled footage.

Registry: family `geometry`, property `true_resolution`. Detects: Effective detail resolution vs container resolution (upscale detection via high-frequency energy).
Payload contract: `video_re_contract_true_resolution` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_true_resolution` question bank citing this envelope.

## Method

Effective detail resolution versus container resolution: upscale detection from the high-frequency

spectrum (video_re_detect_true_resolution).

Method: frames are decoded at native resolution (a centre crop of at most 1280 x 1280 px, no scaling). For each
axis the mean power spectrum of Hann-windowed rows (horizontal) and columns (vertical) is computed, per 128 px
tile and over all textured tiles. A power law fitted on 0.015-0.07 cycles/px predicts what a natively sharp image
would hold at higher frequencies. The cut-off is the lowest frequency above which at least 90% of the smoothed
spectrum lies 10 dB or more below that prediction (a missing band). An image upscaled by s has nothing above
0.5/s cycles/px, so upscale_factor = 0.5 / cut-off and effective size = container / factor. Tiles are
classified individually too, which reveals native-resolution overlays (captions, graphics) over upscaled footage
(verdict "mixed").

Limits: calibrated on 1/f-spectrum test images resampled with bicubic and Lanczos (median error about 5%,
90th percentile about 16%); bilinear upscales leak imaged energy above the cut-off and are estimated less
precisely. Heavy denoising, defocus or low-bitrate encoding also remove the top band and read as a lower
effective resolution, which is what the number means: detail actually present, not how it was lost.
Sharpening halos after upscaling can hide a cut-off. Flat tiles (sky, bars) are skipped.

## Command line

```sh
python3 video_re_detect_true_resolution.py video.mp4 --out true_resolution.json
python3 video_re_detect_true_resolution.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_true_resolution as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `0`
- `fps`: `0.5`
- `max_frames`: `8`
- `crop`: `[1280, 1280]`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `tile` = `128`
- `fit_band` = `[0.015, 0.07]`
- `drop_db` = `10.0`
- `band_frac` = `0.9`
- `min_tile_std` = `6.0`
- `upscaled_factor` = `1.15`
- `mixed_share` = `[0.25, 0.75]`

## Limits

- Bicubic and Lanczos upscales are estimated within about 5% (median) on test images; bilinear less precisely.
- Denoising, defocus and low-bitrate encoding also lower the effective resolution.
- Sharpening after upscaling can hide the cut-off.

## References

- Power-law (1/f^a) amplitude spectra of natural images: Field, D. J. (1987), J. Opt. Soc. Am. A 4(12).

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
