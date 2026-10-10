# ffmpeg filter value escaping

Two-level escaping for ffmpeg filter option values and filtergraphs, plus safe option/chain/label builders, so file names and text can never inject extra filters.

## Use

```python
import ffmpeg_filter_escaping
```

Placed by `baltor_catalog.py place ffmpeg_filter_escaping <step-dir>` under `.baltor/lib/ffmpeg-filter-escaping/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://ffmpeg.org/ffmpeg-utils.html#Quoting-and-escaping
- https://ffmpeg.org/ffmpeg-filters.html#Notes-on-filtergraph-escaping

## Licence

MIT. Original work for the Baltor public-good collection.
