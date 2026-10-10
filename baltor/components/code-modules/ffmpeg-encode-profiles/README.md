# ffmpeg encode profiles

Named house encode profiles (vertical and landscape H.264 delivery with faststart and fixed GOP, small review proxy, lossless FFV1 master) that produce complete ffmpeg argv lists.

## Use

```python
import ffmpeg_encode_profiles
```

Placed by `baltor_catalog.py place ffmpeg_encode_profiles <step-dir>` under `.baltor/lib/ffmpeg-encode-profiles/`.
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
