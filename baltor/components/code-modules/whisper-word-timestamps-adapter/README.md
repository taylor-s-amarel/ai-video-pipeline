# Whisper word timestamps adapter

Normalises word timestamps from faster-whisper (run locally, lazily imported) and openai-whisper results into one monotonic word list for caption timing.

## Use

```python
import whisper_word_timestamps_adapter
```

Placed by `baltor_catalog.py place whisper_word_timestamps_adapter <step-dir>` under `.baltor/lib/whisper-word-timestamps-adapter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `faster_whisper`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://github.com/SYSTRAN/faster-whisper
- https://github.com/openai/whisper

## Licence

MIT. Original work for the Baltor public-good collection.
