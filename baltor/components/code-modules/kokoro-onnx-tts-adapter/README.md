# Kokoro ONNX TTS adapter

Adapter for Kokoro-82M speech through kokoro-onnx (lazy import, model loaded once, clear errors for missing model files) returning mono float32 samples for the TTS interface.

kokoro-onnx is MIT licensed and the Kokoro model is Apache-2.0 (per the kokoro-onnx README, checked 2026-10-10). The model files are not shipped here; download them from the kokoro-onnx releases page.

## Use

```python
import kokoro_onnx_tts_adapter
```

Placed by `baltor_catalog.py place kokoro_onnx_tts_adapter <step-dir>` under `.baltor/lib/kokoro-onnx-tts-adapter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `kokoro_onnx`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://github.com/thewh1teagle/kokoro-onnx
- https://huggingface.co/hexgrad/Kokoro-82M

## Licence

MIT. Original work for the Baltor public-good collection.
