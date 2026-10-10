# Video RE: safe-area check for on-screen text

Flags text regions that overlap zones where app UI or frame edges cover text; zone profiles are labelled assumptions you can replace with measured zones.

Identity `video_re_safe_area_probe`, version 1.0.0, MIT licence.

## What it measures and how

Input: text regions from video_re_text_regions (t_s, bbox in source pixels) and the frame size.
A violation is a text region with at least ``min_overlap`` (25%) of its area inside a zone.

Profiles (zones are fractions of width/height, origin top-left). The numbers are working
assumptions, not published platform specifications: app layouts differ and change, so measure the
app you target (screenshot its player) and pass your own zones with ``--zones``.

* ``vertical_ui_conservative`` - for 9:16: top-ui (top 10%), bottom-ui (bottom 20%), right-rail
  (right 14% between 40% and 80% of the height), where vertical-video apps commonly overlay
  their header, caption/handle text and action buttons
* ``margins_10`` - a 10% margin on every side, the old title-safe rule of thumb
* ``none`` - no zones
* ``auto`` - vertical_ui_conservative for portrait frames, margins_10 otherwise

## Use

Command line:

```sh
python video_re_safe_area_probe.py text_regions.json --profile auto
```

From Python (the package directory on `sys.path`):

```python
import video_re_safe_area_probe
result = video_re_safe_area_probe.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_safe_area_probe.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_safe_area_probe.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `numpy`

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
