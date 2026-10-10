---
description: "Diagnose a failed render and recover safely (owner's copy-ready template)"
argument-hint: "<failed job id, log path or output directory>"
---

# Diagnose a failed render and recover safely

Copy-ready task template from the owner's Animation and Video Production Master Guide (10 Oct 2026), section "Copy-ready task templates". The quoted task is
the owner's text, unchanged; only the input line is added.

**Input (the failed job (id, logs or output directory)):** $ARGUMENTS

Fill the input with actual project data. If an input is missing, mark it unresolved rather than inventing a source,
license, test result, or customer preference.

## Task

> “Inspect the failed job's exact logs, last completed frame range, source/config hashes, and active process state. Determine whether the failure is reproducible, transient, permission-related, or caused by a changed dependency. Resume only when the checkpoint matches current inputs. Preserve partial output and avoid duplicate jobs. If a save or send has an ambiguous outcome, reconcile its actual state before retrying. Return the recovered result or a precise blocker with the next safe action.”

## What a useful result looks like (the guide's notes)

A recovery plan must preserve any outstanding authorization or rights boundary.

## Using the template (the guide's rules)

These prompts are instructions for bounded work, not magic guarantees. Fill their inputs with actual project data. If an input is missing, mark it unresolved rather than inventing a source, license, test result, or customer preference. Each prompt should result in a concrete artifact or decision that can be reviewed.

Keep the prompt, actual inputs, output, model/tool version when known, and human correction. Do not infer that a successful output can be reproduced from the prompt alone. Preserve generated assets and exact source bytes. Use the prompts selectively; running all of them for every minor revision would waste effort.
