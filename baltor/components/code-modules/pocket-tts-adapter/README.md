# Pocket TTS adapter

Adapter for Kyutai Pocket TTS (lazy import, model loaded once, voice states cached) returning mono float32 audio; lists the English built-in voice names.

Pocket TTS code is MIT per its repository (checked 2026-10-10); the README links model and voice licences separately and they were not verified here. Check them before publishing.

## Use

```python
import pocket_tts_adapter
```

Placed by `baltor_catalog.py place pocket_tts_adapter <step-dir>` under `.baltor/lib/pocket-tts-adapter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `pocket_tts`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://github.com/kyutai-labs/pocket-tts

## Licence

MIT. Original work for the Baltor public-good collection.
