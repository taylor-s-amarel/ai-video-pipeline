# Platform safe-area checker

Profile-driven safe areas for vertical and landscape video (house conservative defaults, custom JSON profiles) with text-box checks and a clamped caption band.

Built-in margins are this project's own conservative defaults, not platform specifications: platform UI guidance changes and could not be verified from official sources on 2026-10-10. Load current official numbers as a custom profile.

## Use

```python
import platform_safe_areas
```

Placed by `baltor_catalog.py place platform_safe_areas <step-dir>` under `.baltor/lib/platform-safe-areas/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
