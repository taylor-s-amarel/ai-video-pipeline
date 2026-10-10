# Video RE: narration speaking rate

Words per minute of speaking time, overall and articulation rate and pauses from word timestamps; otherwise a labelled syllable-count estimate from the audio.

Identity `video_re_speech_rate`, version 1.0.0, MIT licence.

## What it measures and how

Method 'transcript' (preferred) uses word time stamps:

* speech_wpm = words / speaking time, where speaking time runs from the first word's start to the
  last word's end minus pauses longer than ``long_pause_s`` (1.0 s): words per minute while talking
* overall_wpm = words / (last end - first start)
* articulation_wpm = words / sum of word durations
* pauses between words of at least ``pause_s`` (0.3 s): count, mean, longest, pause_ratio

Word times that were only spread evenly over subtitle lines (``estimated`` in the transcript) give
the same wpm but no real pause data; the result says so.

Method 'syllable-estimate' needs no transcript: syllable nuclei are counted as peaks of the
300-3000 Hz energy envelope (10 ms frames, 40 ms smoothing, at least 100 ms apart, at least 4 dB
above the surrounding dip and 12 dB above the noise floor) and

    speech_wpm ~= syllables per second of voiced time x 60 / 1.5

The 1.5 syllables per word is an assumption for English narration, so this is an estimate (expect
roughly +-25%) and is reported with method 'syllable-estimate' and confidence 0.4.

## Use

Command line:

```sh
python video_re_speech_rate.py --transcript transcript.json
python video_re_speech_rate.py clip.mp4
```

From Python (the package directory on `sys.path`):

```python
import video_re_speech_rate
result = video_re_speech_rate.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_speech_rate.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_speech_rate.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

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
