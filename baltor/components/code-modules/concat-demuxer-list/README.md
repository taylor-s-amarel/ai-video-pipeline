# Concat demuxer list writer

Writes ffmpeg concat-demuxer lists with correct quote escaping and in/out points, adds -safe 0 only when needed and checks clip compatibility before stream-copy joins.

## Use

```python
import concat_demuxer_list
```

Placed by `baltor_catalog.py place concat_demuxer_list <step-dir>` under `.baltor/lib/concat-demuxer-list/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://ffmpeg.org/ffmpeg-formats.html#concat-1

## Licence

MIT. Original work for the Baltor public-good collection.
