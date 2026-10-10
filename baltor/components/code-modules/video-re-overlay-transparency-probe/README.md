# Video RE: overlay panel transparency probe

Finds caption boxes and title cards over moving backgrounds and estimates their opacity from how much background motion shows through; reports the semi-transparent share.

Identity `video_re_overlay_transparency_probe`, version 1.0.0, MIT licence.

## What it measures and how

Idea: a panel composited with opacity a over a moving background shows the background's changes
scaled by (1 - a). So inside every shot (at least ``min_window_s`` long; the whole clip when no shots
are given), frames are sampled at ``sample_fps`` (default 4) and 160 px wide, and the temporal
standard deviation of every 8x8-pixel cell is measured.

1. The moving-background level is the 90th percentile of cell deviations; if it is under
   ``min_motion`` (3 grey levels) the background does not move enough to test anything and the
   window is skipped.
2. Cells at most 0.8 x that level are 'attenuated'. Isolated cells are removed (a 3x3 majority
   filter); 4-connected groups covering 1-60% of the frame and filling at least 60% of their
   bounding box (panels are rectangles) are candidates.
3. For each candidate, attenuation = median deviation inside (one cell in from the edge) / median
   deviation in a 2-cell ring around it. The ring must itself move (at least 0.6 x the background
   level), otherwise the candidate is static scenery and is dropped.
4. estimated_opacity = 1 - attenuation. At least 0.98 is 'opaque' (nothing shows through);
   0.15-0.98 is 'semi-transparent'. The panel colour is estimated from the inside and ring means:
   tint = (mean_in - (1 - a) x mean_ring) / a.

semi_transparent_ratio = semi-transparent panel area / all detected panel area (summed over
windows): 1.0 means every detected panel lets the background through, 0.0 means all are solid.

Accuracy on synthetic tests (panning texture, flat panel, H.264): opacity within about 0.02 for
0.3-0.95; a 0.98 panel read 0.966 after H.264 and 0.980 lossless, so the opaque/semi class right at
the 0.98 boundary is not reliable. Limits: blur also lowers the variance, so a frosted (blurred) panel reads more opaque than its
alpha; changing text on a panel raises it; a static region of the scene bordered by motion can be
mistaken for an opaque panel (a split screen with one frozen half reads as an opaque panel); panels
smaller than about 1% or larger than 60% of the frame are ignored.

## Use

Command line:

```sh
python video_re_overlay_transparency_probe.py clip.mp4 --shots shots.json
```

From Python (the package directory on `sys.path`):

```python
import video_re_overlay_transparency_probe
result = video_re_overlay_transparency_probe.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_overlay_transparency_probe.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_overlay_transparency_probe.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

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
