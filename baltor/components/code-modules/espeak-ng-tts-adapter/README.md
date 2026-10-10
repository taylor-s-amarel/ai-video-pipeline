# espeak-ng TTS adapter

Runs espeak-ng without a shell (text on stdin, validated voice, speed, pitch, amplitude, optional SSML) as a dependable fallback voice, returning float32 samples.

## Use

```python
import espeak_ng_tts_adapter
```

Placed by `baltor_catalog.py place espeak_ng_tts_adapter <step-dir>` under `.baltor/lib/espeak-ng-tts-adapter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `espeak_ng`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://github.com/espeak-ng/espeak-ng

## Licence

MIT. Original work for the Baltor public-good collection.
