# ASS subtitle writer

Writes complete libass-ready .ass scripts (PlayRes, styles, events) with #RRGGBB+opacity colour conversion and text escaping that stops caption text from injecting override tags.

## Use

```python
import ass_subtitle_writer
```

Placed by `baltor_catalog.py place ass_subtitle_writer <step-dir>` under `.baltor/lib/ass-subtitle-writer/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## Licence

MIT. Original work for the Baltor public-good collection.
