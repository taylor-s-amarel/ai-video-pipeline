# TTS engine interface and fallback chain

Common Speech/TTSEngine interface for local TTS adapters, a fallback chain that reports which engine was used and why others failed, and 16-bit WAV read/write.

## Use

```python
import tts_engine_interface
```

Placed by `baltor_catalog.py place tts_engine_interface <step-dir>` under `.baltor/lib/tts-engine-interface/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
