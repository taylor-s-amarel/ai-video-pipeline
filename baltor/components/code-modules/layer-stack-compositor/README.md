# Layer-stack compositor (ffmpeg)

Turns a list of layers into one ffmpeg filter_complex with the 0.98 opacity cap enforced, positioned normal overlays, RGB-correct blend modes (screen, multiply, overlay...) and time windows.

## Use

```python
import layer_stack_compositor
```

Placed by `baltor_catalog.py place layer_stack_compositor <step-dir>` under `.baltor/lib/layer-stack-compositor/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://ffmpeg.org/ffmpeg-filters.html#blend-1

## Licence

MIT. Original work for the Baltor public-good collection.
