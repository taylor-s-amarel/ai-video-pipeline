# HLS VOD packager

Builds ffmpeg HLS VOD commands with keyframes aligned to segments, writes multivariant master playlists and parses media playlists to check segment durations.

## Use

```python
import hls_vod_packager
```

Placed by `baltor_catalog.py place hls_vod_packager <step-dir>` under `.baltor/lib/hls-vod-packager/`.
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
