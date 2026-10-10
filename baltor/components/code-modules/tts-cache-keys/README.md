# TTS content-addressed cache

Caches synthesized speech under SHA-256 keys of engine, model, voice, speed and exact text, with atomic writes so crashed renders never leave reusable half files.

## Use

```python
import tts_cache_keys
```

Placed by `baltor_catalog.py place tts_cache_keys <step-dir>` under `.baltor/lib/tts-cache-keys/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
