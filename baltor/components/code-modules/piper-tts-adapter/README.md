# Piper TTS adapter

Adapter for Piper speech via its Python API (speed through length_scale) or a shell-free CLI argv, with lazy import, clear voice-file errors and mono float32 output.

Piper (piper1-gpl) is GPL-3.0 per its repository (checked 2026-10-10). This MIT adapter does not include or link Piper code; it imports the separately installed package at run time.

## Use

```python
import piper_tts_adapter
```

Placed by `baltor_catalog.py place piper_tts_adapter <step-dir>` under `.baltor/lib/piper-tts-adapter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `piper_tts`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://github.com/OHF-Voice/piper1-gpl

## Licence

MIT. Original work for the Baltor public-good collection.
