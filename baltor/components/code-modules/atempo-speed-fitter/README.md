# atempo speed fitter

Computes the tempo factor that fits narration to a target length (refusing audible over-stretching) and builds pitch-preserving ffmpeg atempo chains within 0.5-2.0 per stage.

## Use

```python
import atempo_speed_fitter
```

Placed by `baltor_catalog.py place atempo_speed_fitter <step-dir>` under `.baltor/lib/atempo-speed-fitter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://ffmpeg.org/ffmpeg-filters.html#atempo

## Licence

MIT. Original work for the Baltor public-good collection.
