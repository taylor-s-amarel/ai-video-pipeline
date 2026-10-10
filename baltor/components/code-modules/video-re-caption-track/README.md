# Video RE: caption track and caption density

Caption events from a sidecar, an embedded subtitle stream or OCR of the caption band, with words per caption, reading speed, coverage and gaps; text can be masked.

Identity `video_re_caption_track`, version 1.0.0, MIT licence.

## What it measures and how

Sources, first match wins:

1. ``sidecar`` - an .srt or .vtt file you were given with the video
2. ``embedded`` - the first subtitle stream in the container, converted to SRT by ffmpeg
3. ``ocr`` - burned-in captions rebuilt from video_re_ocr_adapter results in the caption band
   (``band``, default y_center_ratio 0.55-1.0): consecutive samples with near-identical text
   (difflib ratio >= 0.8) become one caption event from its first sample to its last sample plus
   one sample interval, so OCR timing is only as fine as the OCR sampling (default 0.5 s)
4. ``none`` - no caption text could be measured; an empty list, never invented text

Stats: count, words per caption (mean, max), characters per second (reading speed), caption
duration (mean, median), gaps between captions, coverage (share of the running time with a caption
on screen), share of words in capitals, and the first caption's start time.

Captions are the analysed video's words. ``text_mode`` 'masked' replaces words by their shape
('WORD {n} word') and 'none' empties them; use either before sharing results. Nothing here may be
copied into a format IR except the measured timing and density.

## Use

Command line:

```sh
python video_re_caption_track.py clip.mp4 --ocr ocr.json --text-mode masked
```

From Python (the package directory on `sys.path`):

```python
import video_re_caption_track
result = video_re_caption_track.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_caption_track.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_caption_track.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

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
