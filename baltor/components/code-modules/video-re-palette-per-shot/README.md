# Video RE: palette and tone per shot

Dominant colours per shot by k-means in CIE Lab with area shares, plus mean luma, contrast, saturation and warmth, for the colour-grade and palette lenses.

Identity `video_re_palette_per_shot`, version 1.0.0, MIT licence.

## What it measures and how

Frames are decoded at ``sample_fps`` (default 4) and 64 px wide; every shot gets the frames inside
it (or its middle frame when it is shorter than one sample interval). Pixels are clustered with
k-means in CIE L*a*b* (D65, deterministic k-means++ seeding), clusters closer than ``merge_delta_e``
(default 8) are merged, and each colour is reported as the mean sRGB of its pixels with its share of
the shot's area.

Per shot: palette (hex, largest share first), shares, mean_luma (0-255), luma_std (contrast proxy),
saturation (mean HSV saturation, 0-1), warmth ((mean R - mean B) / 255, -1..1). Plus the same for the
whole video. Colours are measured after the video's own encoding and compression, so they shift a
little from the colours the editor picked.

## Use

Command line:

```sh
python video_re_palette_per_shot.py clip.mp4 --shots shots.json --k 5
```

From Python (the package directory on `sys.path`):

```python
import video_re_palette_per_shot
result = video_re_palette_per_shot.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_palette_per_shot.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_palette_per_shot.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

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
