# LRC lyrics format

Reads and writes LRC lyric files with metadata tags, offsets, repeated time tags and enhanced per-word timestamps for music videos and karaoke captions.

## Use

```python
import lrc_lyrics_format
```

Placed by `baltor_catalog.py place lrc_lyrics_format <step-dir>` under `.baltor/lib/lrc-lyrics-format/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
