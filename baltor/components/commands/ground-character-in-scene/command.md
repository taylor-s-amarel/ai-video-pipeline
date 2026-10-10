---
description: "Ground a character in the scene (owner's copy-ready template)"
argument-hint: "<exact background file> <character asset>"
---

# Ground a character in the scene

Copy-ready task template from the owner's Animation and Video Production Master Guide (10 Oct 2026), section "Copy-ready task templates". The quoted task is
the owner's text, unchanged; only the input line is added.

**Input (the exact background and character asset):** $ARGUMENTS

Fill the input with actual project data. If an input is missing, mark it unresolved rather than inventing a source,
license, test result, or customer preference.

## Task

> “Using the exact background and character asset, define the support surface, contact point, scale, orientation, depth order, and camera transform. Keep the character's feet attached to the visible support during planted phases. Add a contact shadow consistent with the scene and an occlusion mask where foreground objects overlap. Test motion extremes, turns, and camera extrema. Return before/after previews and measured anchor drift, while distinguishing composited shadows from physical shadow catching.”

## What a useful result looks like (the guide's notes)

The agent should not solve grounding by simply moving the character downward until it looks plausible in one frame. It must verify the complete pose range and the final camera path.

## Using the template (the guide's rules)

These prompts are instructions for bounded work, not magic guarantees. Fill their inputs with actual project data. If an input is missing, mark it unresolved rather than inventing a source, license, test result, or customer preference. Each prompt should result in a concrete artifact or decision that can be reviewed.

Keep the prompt, actual inputs, output, model/tool version when known, and human correction. Do not infer that a successful output can be reproduced from the prompt alone. Preserve generated assets and exact source bytes. Use the prompts selectively; running all of them for every minor revision would waste effort.
