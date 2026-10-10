---
description: "Write this week's cited digest for a watchlist"
argument-hint: "<watchlist.json | preset name> [window, default 7d]"
---

Produce this week's source digest for: $ARGUMENTS

1. Load the watchlist (a path, or a preset from a `monitor-sources-*-watchlist` skill) and
   validate it against the `source_watchlist` schema. Stop and report if it does not validate.
2. Use the `weekly-source-digest-writer` subagent to poll, deduplicate, rank and write
   `digests/<watchlist-id>/<YYYY-MM-DD>.md` and `.json`.
3. Check that every bullet has a link (the `require-digest-citations` hook does this on Stop).
4. Reply with the three-line summary, the counts, and the path. Do not paste the whole digest.
