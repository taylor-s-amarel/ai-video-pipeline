# Video RE: shot-length statistics and cut rhythm

Cut rhythm as numbers: median/mean shot length, cuts per minute, regularity, acceleration trend, hook-window cuts, per-third rates and the dominant template shot length.

Identity `video_re_shot_stats`, version 1.0.0, MIT licence.

## What it measures and how

Input is the output of video_re_detect_shots (or an evidence.json, or a bare list of shots with
start_s/end_s). Output:

* count, mean_s, median_s, std_s, min_s, max_s, p10_s, p90_s of shot durations
* cut_rate_per_min = (count - 1) transitions per minute of video
* cv = std/mean (0 = perfectly regular cutting)
* trend_s_per_min: least-squares slope of shot length against shot start time (negative = cutting
  speeds up as the video goes on)
* hook_cuts_first_3s: transitions inside the first 3 seconds
* thirds: cut rate and median shot length in each third of the running time
* histogram: shot counts in duration bins (s): <0.5, 0.5-1, 1-2, 2-4, 4-8, >=8
* dominant_s and share_near_dominant: the most common shot length (0.1 s resolution) and the share of
  shots within +-10% of it; a high share suggests a fixed beat or template timing
* transitions: counts by type (cut, gradual)

## Use

Command line:

```sh
python video_re_shot_stats.py shots.json --duration 61.2
```

From Python (the package directory on `sys.path`):

```python
import video_re_shot_stats
result = video_re_shot_stats.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_shot_stats.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_shot_stats.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `numpy`

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
