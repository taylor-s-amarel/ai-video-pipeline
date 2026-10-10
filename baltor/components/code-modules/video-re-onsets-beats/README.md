# Video RE: onsets, tempo and beats with numpy

Spectral-flux onsets (within 30 ms on test clicks), autocorrelation tempo with a 120 BPM prior and a dynamic-programming beat tracker, without librosa.

Identity `video_re_onsets_beats`, version 1.0.0, MIT licence.

## What it measures and how

* Onset envelope: spectral flux. Mono audio at 22.05 kHz, centred STFT (1024-sample Hann window,
  256-sample hop = 11.6 ms), magnitudes summed into 40 log-spaced bands (60 Hz - 10 kHz), log
  compressed (log1p(100 x)), and the half-wave-rectified frame-to-frame increase summed over bands.
* Onsets: peaks of the normalised envelope that are the maximum within 30 ms before, exceed the
  local mean (100 ms either side) by ``delta`` (0.07) and come at least ``wait_s`` (50 ms) after
  the previous onset. Time = frame centre plus one hop: on sharp clicks the flux peak arrives one
  hop before the attack, so this correction centres the error on zero; soft attacks read later.
* Tempo: autocorrelation of the (lightly smoothed) onset envelope over 30-300 BPM, weighted by a log-normal prior
  centred on 120 BPM with a one-octave spread (the same idea librosa uses), parabolic refinement.
  ``tempo_confidence`` is the weighted autocorrelation peak relative to lag 0; tempo is null when
  there are fewer than 4 onsets or the confidence is under 0.05.
* Beats: dynamic-programming beat tracker (Ellis 2007, tightness 100) on the onset envelope,
  kept between the first and last onset (half a beat of margin).

Accuracy on synthetic clicks: onset times within 30 ms, tempo within 2 BPM (see the tests). Real
music with soft attacks, rubato or no percussion gives weaker results; octave errors (half or double
tempo) are the typical failure. Speech-only soundtracks produce onsets at syllables and usually no
stable tempo.

## Use

Command line:

```sh
python video_re_onsets_beats.py clip.mp4 --out beats.json
```

From Python (the package directory on `sys.path`):

```python
import video_re_onsets_beats
result = video_re_onsets_beats.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_onsets_beats.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_onsets_beats.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `numpy`

## References

- D. P. W. Ellis, Beat tracking by dynamic programming, Journal of New Music Research 36(1), 2007
- S. Boeck, F. Krebs, M. Schedl, Evaluating the online capabilities of onset detection methods, ISMIR 2012
- https://github.com/librosa/librosa (same ideas, heavier dependency)

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
