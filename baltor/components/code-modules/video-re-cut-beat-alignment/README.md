# Video RE: cut-to-beat alignment with a chance baseline

Share of cuts within 70 ms of a beat (or onset), the share expected by chance, lift, lead/lag offset and beats per shot: did the editor cut to the music?

Identity `video_re_cut_beat_alignment`, version 1.0.0, MIT licence.

## What it measures and how

Inputs are cut times (starts of shots 2..n from video_re_detect_shots) and beat times (or, when no
beats were tracked, onset times) from video_re_onsets_beats.

* cuts_on_beat_ratio: share of cuts within ``tolerance_s`` (default 70 ms, about two frames at
  30 fps) of the nearest reference time. Only cuts inside the music (first to last reference time,
  plus the tolerance) count.
* chance_ratio: the share expected if the same cuts were placed at random: for beats,
  min(1, 2 x tolerance / median beat interval); for onsets, the share of the music span covered by
  +-tolerance windows around onsets. ``lift`` = ratio / chance; values well above 1 mean the editor
  cut to the music.
* median_offset_s: median signed (cut - nearest reference); negative = cuts come just before beats.
* beats_per_shot: median shot length in beats (for example 2.0 = a cut every second beat).

## Use

Command line:

```sh
python video_re_cut_beat_alignment.py --shots shots.json --beats beats.json --tolerance 0.07
```

From Python (the package directory on `sys.path`):

```python
import video_re_cut_beat_alignment
result = video_re_cut_beat_alignment.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_cut_beat_alignment.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_cut_beat_alignment.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `numpy`

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
