---
description: "Verify a final media file (owner's copy-ready template)"
argument-hint: "<exact final MP4 path>"
---

# Verify a final media file

Copy-ready task template from the owner's Animation and Video Production Master Guide (10 Oct 2026), section "Copy-ready task templates". The quoted task is
the owner's text, unchanged; only the input line is added.

**Input (the exact final MP4):** $ARGUMENTS

Fill the input with actual project data. If an input is missing, mark it unresolved rather than inventing a source,
license, test result, or customer preference.

## Task

> “Test the exact final MP4 bytes. Verify stream metadata, full video and audio decode, expected frame count and duration, native versus delivery resolution, audio presence, clipping/silence, and output hash. Inspect encoded frames at scene boundaries and the most difficult target/character poses. Check continuous motion, title readability, puzzle answer visibility, reveal alignment, and loop seams. State which checks are automated, which are sampled visual review, and which require owner or audience feedback.”

## What a useful result looks like (the guide's notes)

The report must not substitute a check against pre-encode frames for a check against the delivered file. If the file changes after QA, rerun the relevant checks and update the hash.

## Using the template (the guide's rules)

These prompts are instructions for bounded work, not magic guarantees. Fill their inputs with actual project data. If an input is missing, mark it unresolved rather than inventing a source, license, test result, or customer preference. Each prompt should result in a concrete artifact or decision that can be reviewed.

Keep the prompt, actual inputs, output, model/tool version when known, and human correction. Do not infer that a successful output can be reproduced from the prompt alone. Preserve generated assets and exact source bytes. Use the prompts selectively; running all of them for every minor revision would waste effort.
