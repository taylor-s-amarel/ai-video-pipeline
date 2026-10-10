# Video RE: camera pan, tilt and zoom per shot

Global pan/tilt/zoom rates per shot from block phase correlation and a RANSAC zoom+translation fit that outvotes static titles and captions; labels Ken Burns moves.

Identity `video_re_camera_motion`, version 1.0.0, MIT licence.

## What it measures and how

Method: frames are decoded grey at 192 px wide and sampled every ``stride_s``/2 (default 0.1 s).
Inside each shot, frames ``stride_s`` apart (default 0.2 s; half that when the longer pair fails)
are compared block by block: every textured 64x64 block (step 32) is phase-correlated (Hann
window, normalised cross-power spectrum, parabolic sub-pixel peak). The block displacements are
fitted with a RANSAC-seeded least-squares model d = t + k x p (translation t, zoom k about the
frame centre): the motion most blocks agree with most closely (MSAC, 0.75 px) wins, and blocks that disagree - static titles, captions, logos, panel edges, moving subjects - are
dropped as outliers, so overlays do not pin the estimate to zero. Frames with too few textured
blocks fall back to a whole-frame estimate (phase correlation plus a scale search). Off-centre zooms
show up as zoom plus a small pan.

Conventions (per second, robust median over the shot's pairs):

* pan_x: frame widths per second, positive = camera moves right (content travels left)
* pan_y: frame heights per second, positive = camera moves down (content travels up)
* zoom: natural log of the scale change per second, positive = zoom in (content grows);
  0.0953 per second means 10% bigger every second
* jitter: mean absolute deviation of per-pair translation rate from the shot median (frame widths
  per second); high values mean handheld shake or noisy estimates
* label: static / pan-left / pan-right / tilt-up / tilt-down / zoom-in / zoom-out (joined with '+'),
  using |rate| >= 0.02 as the threshold

Pairs on flat frames (grey std < 2), with fewer than 40% inlier blocks or a correlation peak under
``min_peak`` (default 0.08) are skipped; a shot with no reliable pair gets nulls. ``mean_inliers``
is the share of textured blocks that agreed with the fitted motion. Block matching covers shifts up
to a quarter block (16 px at 192 px wide) per pair: about 0.4 frame widths per second at the
default stride, 0.8 with the short pair; faster whip pans read as unknown or wrong. Rotation, parallax and independently moving
subjects are not modelled: a large moving subject can be reported as camera motion.

## Use

Command line:

```sh
python video_re_camera_motion.py clip.mp4 --shots shots.json --stride 0.2
```

From Python (the package directory on `sys.path`):

```python
import video_re_camera_motion
result = video_re_camera_motion.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_camera_motion.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_camera_motion.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `numpy`

## References

- C. D. Kuglin, D. C. Hines, The phase correlation image alignment method, IEEE Conf. Cybernetics and Society, 1975
- M. A. Fischler, R. C. Bolles, Random sample consensus, Communications of the ACM 24(6), 1981
- P. H. S. Torr, A. Zisserman, MLESAC: a new robust estimator, CVIU 78(1), 2000 (MSAC scoring)

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
