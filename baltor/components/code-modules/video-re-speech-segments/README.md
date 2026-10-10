# Video RE: speech segments (transparent VAD heuristic)

Where narration probably is: energy, voice-band share and flatness gating with hangover smoothing, plus a syllable-rate modulation depth per segment; silencedetect fallback.

Identity `video_re_speech_segments`, version 1.0.0, MIT licence.

## What it measures and how

Method 'energy' (default, numpy only), on mono 16 kHz audio in 25 ms frames every 10 ms:

1. frame level in dBFS, the share of energy in the 100-4000 Hz voice band, and spectral flatness
   inside that band (voiced speech is harmonic, so its flatness is low);
2. the noise floor is the 10th percentile of frame levels; a frame is active when it is at least
   ``margin_db`` (10 dB) above the floor and above ``abs_floor_db`` (-55 dBFS), with at least 50% of
   its energy in the voice band and band flatness under 0.6;
3. gaps shorter than ``merge_gap_s`` (0.3 s) are bridged, segments shorter than ``min_segment_s``
   (0.2 s) dropped, and each segment padded by 50 ms.

Each segment also gets ``syllabic_modulation`` (dB): how much its voice-band energy rises and falls
at 2-8 Hz, the syllable rate of speech (measured without the segment's first and last 100 ms).
Speech is typically well above 3 dB; a sustained sound (a held music note) stays near 1 dB or less.
It is reported, not used to filter, because sung vocals and rhythmic music also modulate.

Method 'silencedetect' inverts ffmpeg's silencedetect (``-45 dB``, 0.3 s), which only says "not
silent".

Limits: music beds under narration usually merge into one long active region; whispering and
distant speech can be missed. A neural VAD (e.g. Silero) is more accurate when available; this
module keeps the evidence pipeline dependency-free.

## Use

Command line:

```sh
python video_re_speech_segments.py clip.mp4 --out speech.json
```

From Python (the package directory on `sys.path`):

```python
import video_re_speech_segments
result = video_re_speech_segments.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_speech_segments.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_speech_segments.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `numpy`

## References

- https://ffmpeg.org/ffmpeg-filters.html#silencedetect
- https://github.com/snakers4/silero-vad (a more accurate neural alternative)

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
