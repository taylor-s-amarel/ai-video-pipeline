# Detect frame-rate cadence and duplicate frames

Compares nominal and effective frame rate from repeated frames, names the cadence (on ones/twos/threes or a hold pattern such as 1-1-1-2 for 24-in-30) and flags variable frame rate from timestamps.

Registry: family `geometry`, property `frame_rate_cadence`. Detects: Nominal vs effective fps, duplicate frames, pulldown, variable frame rate.
Payload contract: `video_re_contract_frame_rate_cadence` (copied here as `payload.schema.json`). Analysts answer the `video_re_qbank_frame_rate_cadence` question bank citing this envelope.

## Method

Nominal versus effective frame rate: duplicate frames, animation on twos/threes, pulldown-like hold patterns

and variable frame rate (video_re_detect_frame_rate_cadence).

Method: every frame of the first 20 seconds (default, up to 600 frames) is decoded at 160 px wide with its
presentation timestamp (ffmpeg showinfo). The mean absolute luma difference d between consecutive frames is
compared with a local reference (median of the upper half of d over 12 transitions): in active stretches
(reference >= 1.0/255) a transition with d below 0.2 x the reference is a repeat of the previous image. Hold lengths (how many frames each image
stays) give the cadence: "on ones/twos/threes/fours" when at least 90% of holds share one length; otherwise the
shortest repeating hold pattern that matches at least 85% of holds (e.g. 1-1-1-2 = 24 fps material in 30 fps,
2-3 = 12 fps material in 30 fps); otherwise "on N" when 70% share one length; otherwise irregular. Effective fps = nominal fps x images / frames.
Variable frame rate: the frame intervals from timestamps vary by more than 10% of their median for at least
1% of frames.

Limits: frame-blended conversions (no exact repeats) read as on ones; still stretches carry no cadence
information and are excluded (active_share); heavy encoder noise on repeated frames can hide repeats below the
0.2 ratio; only the decoded window is analysed.

## Command line

```sh
python3 video_re_detect_frame_rate_cadence.py video.mp4 --out frame_rate_cadence.json
python3 video_re_detect_frame_rate_cadence.py video.mp4 --param key=value   # override a default below
```

Prints the `baltor.video-detection/v1` envelope (see `envelope.schema.json`). Exit status: 0 ok or partial, 2 unavailable (ffmpeg/ffprobe missing), 1 error.

## Library use

```python
import video_re_detect_frame_rate_cadence as det
res = det.analyse(frames, times, info={}, params=dict(det.DEFAULTS))  # frames: (N,H,W,3) uint8
```

## Decoding (defaults)

- `width`: `160`
- `fps`: `0`
- `max_frames`: `600`
- `duration_s`: `20.0`

Flags `--width`, `--fps`, `--max-frames`, `--start`, `--duration` override them (`--width 0`/`--fps 0` = native size / every frame).

## Parameters (defaults)

- `dup_rel` = `0.2`
- `active_thr` = `1.0`
- `local_window` = `12`
- `on_n_share` = `0.7`
- `pattern_match` = `0.85`
- `max_period` = `8`
- `vfr_dev` = `0.1`
- `vfr_share` = `0.01`

## Limits

- Frame-blended conversions have no exact repeats and read as on ones.
- Still stretches carry no cadence information (active_share).

## Test

```sh
python3 -m pytest -q .
```

Tests use synthetic numpy fixtures with known ground truth; command-line tests encode a lossless FFV1 clip with ffmpeg and are skipped when ffmpeg is absent.

## Rights

Measures technique and structure only. Decoded frames are held in memory for the measurement and never written, stored or republished; the envelope carries numbers, colours and boxes, not footage. Detecting an overlay never means removing it: nothing here removes watermarks or logos.

## Licence

MIT.
