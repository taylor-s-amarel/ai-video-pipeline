# Adversarial review bank: D031 puzzles and fairness (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D031 puzzles and fairness". The questions below are the
owner's exact text. `questions.json` holds the same 32 records in the `adversarial_question` contract.

## How to use this bank (the guide's rules)

- Use this bank as a menu, not a requirement to review every question on every film. Each entry keeps its stable ID, question, failure hypothesis, practical check/fix, severity and modality/stage filters. The evidence contract in the main guide applies to every entry. Tags are candidate filters; they cannot make an irrelevant question applicable or turn missing evidence into a pass. Detailed machine-readable records remain in the preserved source bank.
- Use the bank twice: first on the brief, storyboard and source state; then on the exact final encode. Final-pixel
  and listening questions remain untested or blocked during planning.
- After a material camera, rig, sound, caption, factual or rights change, add a targeted pass: recheck the changed
  beat and neighbouring beats. Stop after the bounded pass and necessary repairs; do not execute every question to
  manufacture impressive totals.
- Every answer is a record in the `adversarial_review_result` contract: `untested` (the default), `observed-pass`,
  `observed-fail`, `blocked` or `not-applicable` (with a stated reason). `demonstrated_defect` only with an observed
  failure; `potential_improvement` for a design hypothesis that still needs comparison.
- Do not mark a listening-only question passed using a waveform statistic. Do not retarget evidence to a changed
  movie by editing its label.

## This area at a glance

- Severity: 28 high, 4 medium.
- Modes: 23 visual, 1 auditory, 18 machine, 28 human-audience.
- Need listening: 1 (none are listening-only).
- Need a human audience: 28.
- Only answerable at final encode or delivery: `AVQ-031-002`.
- Limited by style filter: `AVQ-031-001` (puzzle), `AVQ-031-002` (puzzle), `AVQ-031-003` (puzzle), `AVQ-031-004` (puzzle), `AVQ-031-005` (puzzle), `AVQ-031-006` (puzzle), `AVQ-031-007` (puzzle), `AVQ-031-008` (puzzle), `AVQ-031-009` (puzzle), `AVQ-031-010` (puzzle), `AVQ-031-011` (puzzle), `AVQ-031-012` (puzzle), `AVQ-031-013` (puzzle), `AVQ-031-014` (puzzle), `AVQ-031-015` (puzzle), `AVQ-031-016` (puzzle), `AVQ-031-017` (puzzle), `AVQ-031-018` (puzzle), `AVQ-031-019` (puzzle), `AVQ-031-020` (puzzle), `AVQ-031-021` (puzzle), `AVQ-031-022` (puzzle), `AVQ-031-023` (puzzle), `AVQ-031-024` (puzzle), `AVQ-031-025` (puzzle), `AVQ-031-026` (puzzle), `AVQ-031-027` (puzzle), `AVQ-031-028` (puzzle), `AVQ-031-029` (puzzle), `AVQ-031-030` (puzzle), `AVQ-031-031` (puzzle), `AVQ-031-032` (puzzle).

## Named passes that draw on this area

- `default_32`: `AVQ-031-001`
- `factual_puzzle`: `AVQ-031-001`, `AVQ-031-002`, `AVQ-031-003`, `AVQ-031-004`, `AVQ-031-005`, `AVQ-031-006`, `AVQ-031-007`, `AVQ-031-008`, `AVQ-031-009`, `AVQ-031-010`

## Questions

1. **AVQ-031-001** Does the stated rule define exactly what counts as a target, including partial, stylized, or obscured examples?
   - Failure hypothesis: Solvers apply different reasonable category boundaries.
   - Check or fix: Write explicit inclusion criteria and test ambiguous instances.
   - Severity: high. Modes: visual, human-audience. Stages: concept, script, storyboard. Style filters: puzzle. Passes: default_32, factual_puzzle.
2. **AVQ-031-002** Can every counted target be identified at ordinary viewing size in the actual delivery encode?
   - Failure hypothesis: Technical degradation makes nominally present targets practically unknowable.
   - Check or fix: Test all targets at destination size without zooming.
   - Severity: high. Modes: machine, visual, human-audience. Stages: final-encode, delivery. Style filters: puzzle. Passes: factual_puzzle.
3. **AVQ-031-003** Are target-like decorations excluded, removed, or clearly distinguishable from valid targets?
   - Failure hypothesis: Incidental shapes create an equally reasonable alternate count.
   - Check or fix: Audit the whole image for unmanifested target-like forms.
   - Severity: high. Modes: visual, human-audience. Stages: storyboard, production. Style filters: puzzle. Passes: factual_puzzle.
4. **AVQ-031-004** Do reflections, shadows, pictures-within-pictures, or repeated displays have a stated counting rule?
   - Failure hypothesis: Representation layers are confused with additional physical targets.
   - Check or fix: Declare the rule before solving and apply it consistently.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard. Style filters: puzzle. Passes: factual_puzzle.
5. **AVQ-031-005** Is the answer unique under every interpretation allowed by the written rules?
   - Failure hypothesis: The puzzle has multiple valid solutions despite a single-answer reveal.
   - Check or fix: Enumerate or independently reason through admissible solutions.
   - Severity: high. Modes: machine, human-audience. Stages: script, storyboard, production. Style filters: puzzle. Passes: factual_puzzle.
6. **AVQ-031-006** Does the reveal use the same scene and rules the solver actually saw?
   - Failure hypothesis: The answer is justified by altered evidence or a revised definition.
   - Check or fix: Compare puzzle and reveal states before adding annotations.
   - Severity: high. Modes: machine, visual. Stages: production, edit, final-encode. Style filters: puzzle. Passes: factual_puzzle.
7. **AVQ-031-007** Can the answer be proven from visible evidence without relying on hidden object IDs or creator knowledge?
   - Failure hypothesis: Internal scene metadata supplies information unavailable to viewers.
   - Check or fix: Ask an independent solver to justify the answer from the delivered video alone.
   - Severity: high. Modes: visual, human-audience. Stages: animatic, edit, final-encode. Style filters: puzzle. Passes: factual_puzzle.
8. **AVQ-031-008** Are targets that leave the frame counted consistently with the declared observation window?
   - Failure hypothesis: A moving-camera puzzle silently changes whether off-screen objects count.
   - Check or fix: Define the window and whether counting is instantaneous or cumulative.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, animatic. Style filters: puzzle. Passes: factual_puzzle.
9. **AVQ-031-009** Can solvers track a target through motion without counting it again when it reappears?
   - Failure hypothesis: Identity loss through cuts or occlusion inflates cumulative counts.
   - Check or fix: Preserve distinctive identity or redesign motion to avoid ambiguous reentry.
   - Severity: high. Modes: machine, visual, human-audience. Stages: storyboard, animatic, production, edit. Style filters: puzzle. Passes: factual_puzzle.
10. **AVQ-031-010** Does each valid target receive enough unobscured exposure to be found within the promised solving time?
   - Failure hypothesis: Brief technical visibility is mistaken for a fair observation opportunity.
   - Check or fix: Measure clear exposure and verify detection with new solvers.
   - Severity: high. Modes: machine, visual, human-audience. Stages: animatic, edit, final-encode. Style filters: puzzle. Passes: factual_puzzle.
11. **AVQ-031-011** Are the hardest targets difficult because of intended reasoning or search, rather than blur, compression, or unreadable size?
   - Failure hypothesis: The challenge depends on production defects rather than puzzle design.
   - Check or fix: Compare clean and delivered versions and remove degradation-dependent difficulty.
   - Severity: high. Modes: visual, human-audience. Stages: edit, final-encode. Style filters: puzzle.
12. **AVQ-031-012** Does an occluded target expose enough diagnostic features to justify its classification?
   - Failure hypothesis: Solvers must guess what is behind a foreground object.
   - Check or fix: Identify the visible evidence for membership or increase fair exposure.
   - Severity: high. Modes: visual, human-audience. Stages: storyboard, production. Style filters: puzzle.
13. **AVQ-031-013** Are similarly drawn species or categories distinguishable under the puzzle's actual target definition?
   - Failure hypothesis: Stylization erases the trait needed to separate valid and invalid objects.
   - Check or fix: Test category recognition independently of the counting task.
   - Severity: high. Modes: visual, human-audience. Stages: storyboard, production. Style filters: puzzle.
14. **AVQ-031-014** Does a size-ordering puzzle specify whether solvers should compare apparent image size or implied real-world size?
   - Failure hypothesis: Perspective creates two reasonable size rankings under an unstated metric.
   - Check or fix: State the comparison metric and verify the answer using that metric.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, production. Style filters: puzzle.
15. **AVQ-031-015** Does the puzzle require outside knowledge that the premise presents as a purely visual search?
   - Failure hypothesis: Hidden trivia changes the task without warning.
   - Check or fix: State the knowledge requirement or supply the needed information.
   - Severity: high. Modes: human-audience. Stages: concept, script. Style filters: puzzle.
16. **AVQ-031-016** Does the wording leak the intended answer when the task is meant to require discovery?
   - Failure hypothesis: A title, count label, or grammatical cue gives away the solution.
   - Check or fix: Read all visible text before viewing the puzzle and check for answer leakage.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard. Style filters: puzzle.
17. **AVQ-031-017** Do relational clues still identify the intended objects after mirroring or reframing for another layout?
   - Failure hypothesis: Left-right or relative-position clues become false in a transformed version.
   - Check or fix: Solve each delivered layout independently and revise directional clues where needed.
   - Severity: high. Modes: machine, visual, human-audience. Stages: edit, final-encode, delivery. Style filters: puzzle.
18. **AVQ-031-018** Is an impossible instance allowed by the prompt, or does the wording guarantee a solution that may not exist?
   - Failure hypothesis: Contradictory constraints force solvers to search indefinitely for a nonexistent answer.
   - Check or fix: Check satisfiability and state explicitly when 'no solution' is an admissible response.
   - Severity: high. Modes: machine, human-audience. Stages: script, storyboard, production. Style filters: puzzle.
19. **AVQ-031-019** Can pausing or replaying change the challenge in a way that should be acknowledged in the instructions?
   - Failure hypothesis: A timed challenge implies control over playback it does not possess.
   - Check or fix: Describe the intended play convention without claiming enforced interactivity.
   - Severity: medium. Modes: machine, human-audience. Stages: script, delivery. Style filters: puzzle.
20. **AVQ-031-020** Are optional hints ordered so each helps without accidentally giving away the entire solution?
   - Failure hypothesis: The first hint collapses the task while later hints add nothing.
   - Check or fix: Test hint-by-hint solving and revise the information progression.
   - Severity: medium. Modes: human-audience. Stages: script, storyboard, animatic. Style filters: puzzle.
21. **AVQ-031-021** Does the answer reveal identify every counted target exactly once?
   - Failure hypothesis: Highlighting omits, duplicates, or skips targets while displaying a plausible total.
   - Check or fix: Reconcile reveal IDs and visible markers with the count manifest.
   - Severity: high. Modes: machine, visual. Stages: production, edit, final-encode. Style filters: puzzle.
22. **AVQ-031-022** Do reveal outlines remain registered to moving targets under the final camera transform?
   - Failure hypothesis: Annotations point at empty space or neighboring distractors.
   - Check or fix: Inspect marker-to-target alignment across the full reveal.
   - Severity: high. Modes: machine, visual. Stages: production, edit, final-encode. Style filters: puzzle.
23. **AVQ-031-023** Is the clean solving view free from faint reveal masks, numbering, or residual answer overlays?
   - Failure hypothesis: Hidden or partially transparent solution layers leak assistance.
   - Check or fix: Inspect exported solving frames with the intended contrast and brightness.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: puzzle.
24. **AVQ-031-024** Can a target enter or leave the valid set during animation without an explicit rule for that state change?
   - Failure hypothesis: Morphing, opening, or orientation changes make the answer time-dependent.
   - Check or fix: Freeze membership or define when and how it changes.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, production. Style filters: puzzle.
25. **AVQ-031-025** Does random layout generation preserve solution uniqueness and fair spacing for this specific instance?
   - Failure hypothesis: Generic generator constraints fail on the selected arrangement.
   - Check or fix: Validate the delivered instance and independently solve it.
   - Severity: high. Modes: machine, human-audience. Stages: production. Style filters: puzzle.
26. **AVQ-031-026** Are distractors wrong for a visible reason rather than an arbitrary creator-only exception?
   - Failure hypothesis: The answer depends on an unstated special case.
   - Check or fix: Require an observable exclusion reason for each close distractor.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, production. Style filters: puzzle.
27. **AVQ-031-027** Does a visual pattern have a defensible next step rather than several equally simple continuations?
   - Failure hypothesis: A preferred pattern is presented as mathematically compelled.
   - Check or fix: Compare alternative rules and narrow the prompt where necessary.
   - Severity: high. Modes: machine, human-audience. Stages: concept, script, storyboard. Style filters: puzzle.
28. **AVQ-031-028** Are number puzzles robust to rounding, operation-order, and notation conventions used by the audience?
   - Failure hypothesis: Different standard conventions yield different answers.
   - Check or fix: State conventions and independently solve the displayed notation.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, production. Style filters: puzzle.
29. **AVQ-031-029** If an audio clue is essential, is that requirement clear before muted viewers begin solving?
   - Failure hypothesis: A seemingly visual puzzle quietly depends on unheard information.
   - Check or fix: Listen to identify essential audio clues and label the required modality.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: script, storyboard, animatic. Style filters: puzzle.
30. **AVQ-031-030** Are example solutions consistent with the actual rules rather than teaching an exception that never returns?
   - Failure hypothesis: The tutorial primes a strategy the main puzzle rejects.
   - Check or fix: Apply every example's reasoning to the final instance.
   - Severity: high. Modes: machine, human-audience. Stages: script, storyboard, animatic. Style filters: puzzle.
31. **AVQ-031-031** Does the difficulty claim reflect actual cold solving rather than the creator's familiarity with the answer?
   - Failure hypothesis: Insider knowledge distorts both estimated difficulty and allotted time.
   - Check or fix: Test with unbriefed relevant solvers and report the limited sample honestly.
   - Severity: medium. Modes: human-audience. Stages: animatic, delivery. Style filters: puzzle.
32. **AVQ-031-032** Does the reveal explain why plausible alternative answers fail, rather than merely displaying the preferred number?
   - Failure hypothesis: A declarative answer leaves legitimate ambiguity unresolved.
   - Check or fix: Address the strongest alternate interpretation with visible evidence.
   - Severity: high. Modes: visual, human-audience. Stages: script, animatic, edit. Style filters: puzzle.
