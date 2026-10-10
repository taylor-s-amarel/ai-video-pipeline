---
description: "Re-check media pack hashes and licences and regenerate credits"
argument-hint: "[path/to/pack.json ...]"
---

Refresh credits and licence checks for the media pack(s): $ARGUMENTS (default: every pack.json in the repo)

1. For each manifest, recompute `sha256` of every fetched file on disk and compare with the lock file; report mismatches.
2. Run `python3 asset_licence_checker.py <manifest> --use monetised-video` (or the profile the project states).
3. Regenerate CREDITS.md with `media_pack_fetcher.credits_markdown` (`python3 -c` or the fetcher's lock step).
4. Produce the description credit block: every attribution-required line verbatim, then "Other assets: CC0 (Kenney, Quaternius, ...)".
5. List anything still `to-fetch` or `manual` so the next step knows what is missing.
