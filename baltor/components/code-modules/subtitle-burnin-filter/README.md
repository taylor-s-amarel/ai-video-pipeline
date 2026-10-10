# Subtitle burn-in filter builder

Builds ffmpeg ass/subtitles burn-in filters with force_style overrides and two-level escaping that is safe against filter injection through file names or style values.

## Use

```python
import subtitle_burnin_filter
```

Placed by `baltor_catalog.py place subtitle_burnin_filter <step-dir>` under `.baltor/lib/subtitle-burnin-filter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://ffmpeg.org/ffmpeg-filters.html#subtitles-1

## Licence

MIT. Original work for the Baltor public-good collection.
