---
description: "Find rising topics with citations from two or more independent sources"
argument-hint: "<topic or watchlist> [window, default 7d]"
---

Run a trend scan for: $ARGUMENTS

1. Pick the watchlist preset that matches the topic, or build a temporary watchlist from the
   relevant `community-*` collections and the topic's keywords (`hnrss.org/newest?q=` feeds are
   useful for keyword coverage).
2. Use the `trend-scan-analyst` subagent over the current and previous window.
3. Reply with the trend table (trend, why now, linked sources, confidence, suggested action)
   and the anecdotes list. Every trend needs two independent links you opened.
