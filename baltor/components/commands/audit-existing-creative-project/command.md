---
description: "Audit an existing creative project (owner's copy-ready template)"
argument-hint: "<selected project: path or name>"
---

# Audit an existing creative project

Copy-ready task template from the owner's Animation and Video Production Master Guide (10 Oct 2026), section "Copy-ready task templates". The quoted task is
the owner's text, unchanged; only the input line is added.

**Input (the selected project (path or name)):** $ARGUMENTS

Fill the input with actual project data. If an input is missing, mark it unresolved rather than inventing a source,
license, test result, or customer preference.

## Task

> “Inspect the selected project and its current outputs. Identify the latest source revision and owner correction. List the actual render route, native resolution, frame rate, asset origins, sound sources, and completed checks. Separate observed facts from README claims. Find the three most consequential visible or reproducibility defects, explain their effect on the viewer, and propose the smallest repairs. Do not install, publish, or alter unrelated files. Return an evidence-linked audit and a bounded next step.”

## What a useful result looks like (the guide's notes)

The expected output is an audit tied to actual files and frames. It should distinguish a missing resource from a poorly designed resource. A folder named ‘high quality’ is not evidence of high-quality rendering. A script that mentions bunnies but creates only ducks should be reported as a mismatch.

## Using the template (the guide's rules)

These prompts are instructions for bounded work, not magic guarantees. Fill their inputs with actual project data. If an input is missing, mark it unresolved rather than inventing a source, license, test result, or customer preference. Each prompt should result in a concrete artifact or decision that can be reviewed.

Keep the prompt, actual inputs, output, model/tool version when known, and human correction. Do not infer that a successful output can be reproduced from the prompt alone. Preserve generated assets and exact source bytes. Use the prompts selectively; running all of them for every minor revision would waste effort.
