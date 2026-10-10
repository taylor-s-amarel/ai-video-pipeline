# Video RE: detect shots, cuts and dissolves

Frame-exact hard cuts plus gradual transitions from soft colour histograms, grey differences and motion-robust thumbnails with an adaptive threshold; ffmpeg scdet cross-check.

Identity `video_re_detect_shots`, version 1.0.0, MIT licence.

## What it measures and how

Method 'frames' (default) decodes every frame at a small size (96 px wide) and scores each frame
against the previous one:

    score = 0.4 * colour-histogram distance (soft 16-bin Y, Cb, Cr histograms, mean L1/2, 0..1)
          + 0.3 * min(1, 2 * mean absolute grey difference / 255)
          + 0.3 * min(1, 3 * mean absolute difference of 16-column block-mean thumbnails / 255)

The thumbnail term barely moves under pans and zooms but changes when the picture changes, which
catches cuts between two shots with similar colours.

A frame starts a new shot (hard cut) when its score is a local maximum, is at least ``min_score``
and is at least ``adaptive_ratio`` times the median score of the surrounding ``window_s`` seconds,
and the previous shot is at least ``min_shot_s`` long. Cut times are frame-exact: the new shot
starts at frame_index / fps.

Gradual transitions are found with a long-range difference: frame t against frame t-k
(k = ``gradual_window_s``). A bump in that curve that is not explained by a hard cut, builds up over
several frames and lasts less than ``max_gradual_s`` + k is a dissolve or fade; its centre is the
boundary. Continuous camera motion produces a long plateau instead and is rejected.

Method 'scdet' runs ffmpeg's scdet filter instead (hard cuts only); useful as a cross-check.

Known limits: whip pans, strobe/flash frames and very fast motion can create false cuts; cuts between
two near-identical framings can be missed; gradual-transition boundaries are approximate (a few
frames) and marked ``type: gradual``.

## Use

Command line:

```sh
python video_re_detect_shots.py clip.mp4 --out shots.json
python video_re_detect_shots.py clip.mp4 --method scdet
```

From Python (the package directory on `sys.path`):

```python
import video_re_detect_shots
result = video_re_detect_shots.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_detect_shots.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_detect_shots.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `numpy`

## References

- https://ffmpeg.org/ffmpeg-filters.html#scdet
- https://github.com/Breakthrough/PySceneDetect (adaptive-threshold idea)
- H. J. Zhang, A. Kankanhalli, S. W. Smoliar, Automatic partitioning of full-motion video, Multimedia Systems 1(1), 1993 (twin-comparison gradual transitions)

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
