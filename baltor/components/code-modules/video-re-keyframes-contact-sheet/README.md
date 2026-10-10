# Video RE: keyframes and contact sheets per shot

Picks the sharpest of three candidate frames per shot (Laplacian variance), saves keyframes and labelled contact sheets so analysts can see every shot.

Identity `video_re_keyframes_contact_sheet`, version 1.0.0, MIT licence.

## What it measures and how

For every shot it decodes candidate frames at 25%, 50% and 75% of the shot (``--candidates 1`` uses
only the middle) and keeps the sharpest one (variance of a Laplacian on the grey image), which avoids
motion-blurred frames and dissolve frames. It writes:

* ``keyframes/shot_000.jpg`` ... (default 360 px wide)
* ``contact_sheet_01.jpg`` ... grids of thumbnails labelled "#index start_s (duration)"

The frames are local analysis artefacts so an analyst (human or model) can look at every shot. They
are copies of the source's pictures: keep them out of anything published and out of a format IR.

## Use

Command line:

```sh
python video_re_keyframes_contact_sheet.py clip.mp4 --shots shots.json --out-dir evidence/
```

From Python (the package directory on `sys.path`):

```python
import video_re_keyframes_contact_sheet
result = video_re_keyframes_contact_sheet.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_keyframes_contact_sheet.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_keyframes_contact_sheet.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `numpy`
- `pillow`

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
