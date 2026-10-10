# Video RE: text-like regions without OCR

Finds titles, captions and labels by stroke-edge density, line grouping and stroke-spacing checks, then links them into on-screen tracks with position and duration.

Identity `video_re_text_regions`, version 1.0.0, MIT licence.

## What it measures and how

Heuristic (documented so analysts can judge it):

1. Frames are sampled at ``sample_fps`` (default 2) and scaled to 360 px wide, grey.
2. Horizontal and vertical grey-level gradients are computed; a pixel is a stroke edge when its
   gradient exceeds max(18, 0.35 x the frame's 99th-percentile gradient).
3. The frame is divided into 4x4-pixel cells. A cell is 'text-like' when at least 12% of its pixels
   are vertical-stroke edges (text has many short vertical strokes).
4. Text cells are grouped with a horizontal morphological closing (3 cells), 4-connected
   components are labelled on the cell grid, and components on the same line with a gap of at most
   0.8 x line height are merged (word spacing of large type).
5. A component is kept when it is 7 px to 30% of the frame tall, at least 1.5x as wide as tall,
   at least 60% of its cell columns contain stroke cells, and its middle rows cross at least 2.0
   stroke edges per text-height of width (ordinary type crosses about 4 at any size) with a median
   spacing between edges of at most 0.28 x text height (letters: about 0.1-0.2; blobs and bokeh
   circles: 0.33 and more in calibration).

Output regions carry t_s, bbox [x, y, w, h] in source pixels, area_ratio, y_center_ratio and a 0-1
score. Regions in consecutive samples that overlap (IoU >= 0.5) are linked into tracks, which show
how long a title or caption band stays on screen.

Known limits: high-contrast textures, grids, foliage and fine patterns can be proposed as text;
very large display type with few strokes, low-contrast text, vertical or curved text and text on
busy backgrounds can be missed. This is a region proposer: OCR (video_re_ocr_adapter) or a look at
the keyframe confirms it.

## Use

Command line:

```sh
python video_re_text_regions.py clip.mp4 --fps 2 --out text_regions.json
```

From Python (the package directory on `sys.path`):

```python
import video_re_text_regions
result = video_re_text_regions.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_text_regions.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_text_regions.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

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
