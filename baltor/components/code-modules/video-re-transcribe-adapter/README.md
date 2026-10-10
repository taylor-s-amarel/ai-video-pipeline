# Video RE: speech-recognition adapter with word times

Transcribes with faster-whisper, openai-whisper or whisper.cpp if installed (no model downloads unless allowed), or reads an existing transcript; words can be masked.

Identity `video_re_transcribe_adapter`, version 1.0.0, MIT licence.

## What it measures and how

Engines, tried in this order by ``--engine auto`` (all optional, all imported lazily):

* ``faster-whisper`` (``pip install faster-whisper``) - word timestamps; CPU int8
* ``openai-whisper`` (``pip install openai-whisper``) - word timestamps
* ``whisper.cpp`` - the ``whisper-cli`` program with a ggml model named by ``WHISPER_CPP_MODEL``

Models are not downloaded unless ``--allow-download`` is given: faster-whisper runs with
``local_files_only`` and openai-whisper is only used when its model file is already in the cache.
Without a usable engine the result is ``{"status": "unavailable"}`` and nothing is guessed.

The transcript is the analysed video's script. It is local evidence for measuring structure
(speech rate, hook length, sentence rhythm, where numbers are said) and must never be copied into a
format IR or republished. ``--text-mode masked`` keeps word timings but replaces each word with its
shape ('Word', 'word', 'WORD', '{n}'); ``none`` drops the text.

## Use

Command line:

```sh
python video_re_transcribe_adapter.py clip.mp4 --engine faster-whisper --model small --text-mode masked
python video_re_transcribe_adapter.py clip.mp4 --from-file subs.srt
```

From Python (the package directory on `sys.path`):

```python
import video_re_transcribe_adapter
result = video_re_transcribe_adapter.run(...)  # returns a JSON-ready dict with a 'status' field
```

Every result has `status`: `ok`, `unavailable` (a tool, engine or stream is missing; `reason` says which) or `error`. Missing measurements are never estimated in their place.

## Files

- `video_re_transcribe_adapter.py` - the module (CLI and importable functions)
- `video_re_common.py` - shared ffmpeg/ffprobe/numpy helpers (identical copy in every video_re package)
- `video_re_synth.py` - synthetic media with known ground truth, used by the tests

## Test

```sh
python3 -m pytest -q .
```

Tests: `test_video_re_transcribe_adapter.py`. They build synthetic media with ffmpeg and numpy (hard cuts at known frames, pans and zooms of known speed, clicks at known times, panels of known opacity) and check the measurement against it; tests that need ffmpeg or an optional engine are skipped when it is absent.

## Dependencies

- `ffmpeg`
- `ffprobe`
- `faster_whisper` (optional, imported or run only when present)
- `openai_whisper` (optional, imported or run only when present)
- `whisper_cpp` (optional, imported or run only when present)

Network: only with --allow-download: faster-whisper fetches models from Hugging Face, openai-whisper from its model host.

## References

- https://github.com/SYSTRAN/faster-whisper
- https://github.com/openai/whisper
- https://github.com/ggml-org/whisper.cpp

## Analysis boundary

Analysis boundary: this module measures technique and structure (timing, layout, motion, colour, loudness, rhythm). Analysing a public video for technique is fine; republishing its content is not. Its outputs are local working evidence: keyframes, OCR text, captions and transcripts of the analysed video stay out of anything published and out of a format IR, which keeps only technique, structure and parameters - never the source's footage, frames, music, voice or script text (at most a short on-screen label quoted as an evidence note, no transcripts).

## Swarm

Part of the video reverse-engineering swarm, stage 1 (LOAD/DISASSEMBLE): measurement tools turn a video into evidence.json; lens analysts answer question banks citing it (stage 2), challengers try to refute them (3), the lifter and parameteriser build the format IR (4), a renderer recompiles it with new content (5), and the same measurements on the variant score fidelity (6).

## Licence

MIT. Original work for the Baltor public-good collection.
