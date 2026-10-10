# Video RE: centre vs border motion energy

Mean grey-level frame difference in the centre box and the border per shot, a 0.5 s series and the share of 2 s windows where the background keeps moving.

Identity `video_re_motion_energy`, version 1.0.0, MIT licence.

## What it measures and how

Frames are decoded as grey, 160 px wide, at the source frame rate (capped at 30 fps with ffmpeg's fps
filter for faster sources). For each pair of consecutive frames:

    center = mean |frame_t - frame_t-1| inside the central box (60% x 60% of the frame)
    border = the same over the rest of the frame

in grey levels (0-255). Pairs that straddle a shot boundary are left out of the per-shot means.

Outputs per shot {center, border, whole}, a 0.5 s series, and a summary with
``background_moving_ratio``: the share of 2-second windows whose mean border difference is at least
``moving_threshold`` (default 0.6 grey levels), a direct check of "the background keeps moving";
``still_ratio``: share of frame pairs with whole-frame difference under 0.3 (frozen picture).
Values depend on resolution and frame rate, so compare videos measured with the same settings.

## Use

Command line:

```sh
python video_re_motion_energy.py clip.mp4 --shots shots.json --threshold 0.6
```

From Python (the package directory on `sys.path`):

```python
import video_re_motion_energy
result = video_re_motion_energy.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_motion_energy.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_motion_energy.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `numpy`

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
