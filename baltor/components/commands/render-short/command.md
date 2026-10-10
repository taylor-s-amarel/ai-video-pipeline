---
description: "Make a full house-style vertical short from a topic"
argument-hint: "<topic>"
---

Make one complete short about: $ARGUMENTS

1. Research 4-10 specific facts with numbers and dates. Keep the source URL for each.
2. Write the hook title (2-7 words) and a 140-160 wpm narration script that runs 60-90 seconds.
3. Write `spec.json` that validates against the `short_video_spec` contract schema.
4. Generate narration, time captions from the speech, render with at least five moving layers.
5. Run the `short-video-rules-reviewer` subagent. Fix every FAIL and re-render.
6. Deliver the full MP4 with a posting caption and any music credit. Never deliver a preview instead.
