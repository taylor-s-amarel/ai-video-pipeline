---
description: "Reopen the source package (owner's copy-ready template)"
argument-hint: "<source package archive path>"
---

# Reopen the source package

Copy-ready task template from the owner's Animation and Video Production Master Guide (10 Oct 2026), section "Copy-ready task templates". The quoted task is
the owner's text, unchanged; only the input line is added.

**Input (the source package):** $ARGUMENTS

Fill the input with actual project data. If an input is missing, mark it unresolved rather than inventing a source,
license, test result, or customer preference.

## Task

> “Extract the source package into a clean permitted directory. Verify archive integrity and manifest hashes. Resolve dependencies without installing unapproved software. Open the actual native project, inspect asset paths, and render a small representative sample. Confirm that the sample corresponds to the delivered revision. Record missing assets, external dependencies, font requirements, and any differences from the original environment. Do not label a ZIP CRC check as a native scene reopen.”

## What a useful result looks like (the guide's notes)

If a package depends on an external licensed asset that cannot be redistributed, preserve its source and hash and document the required acquisition step. A package can be honestly incomplete for a new consumer even when it worked in the original environment.

## Using the template (the guide's rules)

These prompts are instructions for bounded work, not magic guarantees. Fill their inputs with actual project data. If an input is missing, mark it unresolved rather than inventing a source, license, test result, or customer preference. Each prompt should result in a concrete artifact or decision that can be reviewed.

Keep the prompt, actual inputs, output, model/tool version when known, and human correction. Do not infer that a successful output can be reproduced from the prompt alone. Preserve generated assets and exact source bytes. Use the prompts selectively; running all of them for every minor revision would waste effort.
