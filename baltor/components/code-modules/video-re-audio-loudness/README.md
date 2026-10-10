# Video RE: EBU R128 loudness, dynamics and silence

One ffmpeg pass: integrated loudness, loudness range, true peak, short-term loudness per second, RMS and silence segments of a video's soundtrack.

Identity `video_re_audio_loudness`, version 1.0.0, MIT licence.

## What it measures and how

One ffmpeg pass runs ``ebur128=peak=true:metadata=1`` (momentary/short-term loudness every 100 ms
and the R128 summary), ``astats`` (RMS and sample peak) and ``silencedetect``. Reported:

* integrated_lufs, loudness_range (LU), lra_low/lra_high (LUFS), true_peak_dbtp - the ebur128 summary
* rms_db, sample_peak_db - astats over all channels
* short_term - short-term (3 s) loudness once per second, LUFS; momentary_max_lufs
* silence - segments quieter than ``silence_db`` for at least ``silence_min_s`` and their share of
  the running time

Values are measurements of the delivered file, after any platform re-encode. For files under about
3 s the loudness range is not meaningful. A video without an audio stream returns status
'unavailable' and no numbers.

## Use

Command line:

```sh
python video_re_audio_loudness.py clip.mp4 --out loudness.json
```

From Python (the package directory on `sys.path`):

```python
import video_re_audio_loudness
result = video_re_audio_loudness.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_audio_loudness.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_audio_loudness.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`

## References

- https://ffmpeg.org/ffmpeg-filters.html#ebur128
- https://ffmpeg.org/ffmpeg-filters.html#astats
- https://ffmpeg.org/ffmpeg-filters.html#silencedetect
- https://www.itu.int/rec/R-REC-BS.1770
- https://tech.ebu.ch/docs/r/r128.pdf

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
