# Video RE: evidence bundle (writes evidence.json)

Runs all 18 video_re measurements on one video and writes evidence.json (baltor.video-evidence/v1) with details, keyframes, tool versions and an error per missing value.

Identity `video_re_evidence_bundle`, version 1.0.0, MIT licence.

## What it measures and how

Writes:

* ``evidence.json`` - exactly the shape in ``evidence.schema.json`` (spec baltor.video-evidence/v1):
  source, shots (with keyframe, palette, motion energy, camera move), shot_stats, text_regions,
  captions, audio (loudness, speech segments, onsets, tempo, speech rate, cut-beat alignment),
  overlay, safe_area, tools (name -> version) and errors
* ``details/<module>.json`` - each module's full output, for analysts who need more than the summary
* ``keyframes/`` and ``contact_sheet_NN.jpg`` - one representative frame per shot
* ``details/_run.json`` - timings and the options used

Every module is optional. A module that is missing, unavailable (no OCR engine, no speech
recogniser, no audio stream) or fails leaves its fields null and adds an ``errors`` entry naming the
module and the fields; nothing is estimated in its place. The other video_re_* packages are found
next to this package (catalogue or ``.baltor/lib`` layout), on ``sys.path``, or under
``VIDEO_RE_LIB``.

Boundary: evidence.json and its folder are local working files. They can hold caption text,
transcripts and frames of the analysed video. Analysts cite them; a format IR keeps only technique
and structure, never the source's footage, frames, music, voice or script. Use ``--text-mode
masked`` (or ``share_safe()``) before giving evidence to anyone else.

## Use

Command line:

```sh
python video_re_evidence_bundle.py clip.mp4 --out-dir evidence/ --reference "<public URL of the video>"
python video_re_evidence_bundle.py clip.mp4 --out-dir evidence/ --fast --text-mode masked --share-safe
```

From Python (the package directory on `sys.path`):

```python
import video_re_evidence_bundle
result = video_re_evidence_bundle.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## evidence.json

`evidence.schema.json` in this package is the JSON Schema of the file this module writes (spec `baltor.video-evidence/v1`); every write is validated against it and problems are recorded in `errors` and `details/_run.json`. The sibling `video_re_*` packages are found next to this one (catalogue layout or `.baltor/lib/`), on `sys.path`, or under `VIDEO_RE_LIB`.

## Files

- `video_re_evidence_bundle.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests
- `evidence.schema.json` - JSON Schema of evidence.json

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_evidence_bundle.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `numpy`
- `pillow`
- `jsonschema`
- `tesseract` (optional, imported or run only when present)
- `pytesseract` (optional, imported or run only when present)
- `easyocr` (optional, imported or run only when present)
- `faster_whisper` (optional, imported or run only when present)
- `openai_whisper` (optional, imported or run only when present)
- `whisper_cpp` (optional, imported or run only when present)

Network: only with --allow-download, passed to the OCR and speech-recognition adapters.

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
