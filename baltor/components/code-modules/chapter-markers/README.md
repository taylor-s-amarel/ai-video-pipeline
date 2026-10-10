# Chapter markers (YouTube and FFMETADATA)

Renders YouTube description chapter timestamps with rule checks (00:00 start, three or more ascending, minimum length) and FFMETADATA1 chapter files that ffmpeg muxes into MP4.

## Use

```python
import chapter_markers
```

Placed by `baltor_catalog.py place chapter_markers <step-dir>` under `.baltor/lib/chapter-markers/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://support.google.com/youtube/answer/9884579
- https://ffmpeg.org/ffmpeg-formats.html#Metadata-2

## Licence

MIT. Original work for the Baltor public-good collection.
