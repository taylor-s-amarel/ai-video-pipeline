---
description: "Propose sourced short-video topics from topic-mining feeds"
argument-hint: "<niche, e.g. women in science | space | history> [count, default 10]"
---

Scout short-video topics for: $ARGUMENTS

1. Use the `faceless-topic-scout` subagent with `community-topic-mining-feeds` and
   `community-reddit-story-topic-mining`, plus any feeds the niche needs.
2. Every idea needs a primary source for each number, a visuals plan with licences, and a
   rights and policy check. Drop ideas that fail.
3. Reply with the idea table and the rejected leads. Save it to `topics/<niche>-<date>.md`.
