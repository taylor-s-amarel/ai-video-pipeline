---
description: "Extract a reusable component (owner's copy-ready template)"
argument-hint: "<completed episode: path>"
---

# Extract a reusable component

Copy-ready task template from the owner's Animation and Video Production Master Guide (10 Oct 2026), section "Copy-ready task templates". The quoted task is
the owner's text, unchanged; only the input line is added.

**Input (the completed episode):** $ARGUMENTS

Fill the input with actual project data. If an input is missing, mark it unresolved rather than inventing a source,
license, test result, or customer preference.

## Task

> “From the completed episode, identify one repeated task that can be isolated usefully. Check the existing component catalog and shared implementations first. Define typed inputs, outputs, effects, errors, dependencies, and limitations. Implement the smallest useful callable, add positive, boundary, and known-wrong tests, and show a minimal invocation using preserved fixtures. Keep episode-specific content in configuration. Do not claim native Baltor compatibility until the real isolated intake contract is tested.”

## What a useful result looks like (the guide's notes)

Good candidates include anchor projection, crop-bound validation, answer-mask joining, scene-local timing, motion continuity checks, or audio-fade planning. A renamed episode script is not automatically a reusable component.

## Using the template (the guide's rules)

These prompts are instructions for bounded work, not magic guarantees. Fill their inputs with actual project data. If an input is missing, mark it unresolved rather than inventing a source, license, test result, or customer preference. Each prompt should result in a concrete artifact or decision that can be reviewed.

Keep the prompt, actual inputs, output, model/tool version when known, and human correction. Do not infer that a successful output can be reproduced from the prompt alone. Preserve generated assets and exact source bytes. Use the prompts selectively; running all of them for every minor revision would waste effort.
