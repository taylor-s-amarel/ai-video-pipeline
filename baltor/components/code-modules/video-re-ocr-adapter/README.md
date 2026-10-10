# Video RE: OCR adapter for text regions

Reads proposed text regions with Tesseract, pytesseract or EasyOCR when installed; turns 'FACT 3' into the pattern 'FACT {n}'; masks words on request; unavailable otherwise.

Identity `video_re_ocr_adapter`, version 1.0.0, MIT licence.

## What it measures and how

Engines, tried in this order by ``--engine auto``:

* ``tesseract`` - the Tesseract command-line program (``tesseract img stdout --psm 7 tsv``)
* ``pytesseract`` - the Python wrapper around the same program
* ``easyocr`` - EasyOCR on CPU; models are only downloaded when ``--allow-download`` is given

None of them is required: without one the result is ``{"status": "unavailable", ...}`` and the
evidence bundle records the gap instead of guessing text.

Each region (from video_re_text_regions) is cropped from a frame decoded at its time stamp (up to
1280 px wide), padded by 15%, enlarged to at least 64 px tall, converted to grey and sent to the
engine. Regions at the same time stamp share one decoded frame.

Text handling (the analysis boundary): OCR text is local evidence for structure, never content to
reuse. ``text_mode`` 'full' keeps the words (default, local files only), 'masked' keeps only their
shape ("WORD {n}: {n} word word"), 'none' drops them. ``label_pattern`` turns "FACT 3" into
"FACT {n}" so the parameteriser can lift a numbered-label pattern without copying wording.

## Use

Command line:

```sh
python video_re_ocr_adapter.py clip.mp4 --regions text_regions.json --text-mode masked
```

From Python (the package directory on `sys.path`):

```python
import video_re_ocr_adapter
result = video_re_ocr_adapter.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_ocr_adapter.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_ocr_adapter.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `numpy`
- `pillow`
- `tesseract` (optional, imported or run only when present)
- `pytesseract` (optional, imported or run only when present)
- `easyocr` (optional, imported or run only when present)

Network: only with --allow-download: EasyOCR may fetch its model weights; Tesseract never uses the network.

## References

- https://github.com/tesseract-ocr/tesseract
- https://github.com/madmaze/pytesseract
- https://github.com/JaidedAI/EasyOCR

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
