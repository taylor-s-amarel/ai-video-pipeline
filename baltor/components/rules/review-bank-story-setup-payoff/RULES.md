# Adversarial review bank: D018 story setup payoff (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D018 story setup payoff". The questions below are the
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

- Severity: 21 high, 11 medium.
- Modes: 32 visual, 2 auditory, 32 human-audience.
- Need listening: 2 (none are listening-only).
- Need a human audience: 32.
- Only answerable at final encode or delivery: none.
- Limited by style filter: `AVQ-018-001` (fiction), `AVQ-018-002` (fiction), `AVQ-018-003` (fiction), `AVQ-018-004` (fiction), `AVQ-018-005` (fiction), `AVQ-018-007` (fiction), `AVQ-018-008` (fiction, puzzle), `AVQ-018-009` (fiction), `AVQ-018-010` (fiction), `AVQ-018-011` (fiction), `AVQ-018-012` (fiction), `AVQ-018-013` (fiction), `AVQ-018-014` (fiction), `AVQ-018-015` (fiction), `AVQ-018-016` (fiction), `AVQ-018-017` (fiction), `AVQ-018-018` (fiction), `AVQ-018-019` (fiction), `AVQ-018-020` (fiction), `AVQ-018-021` (fiction), `AVQ-018-022` (fiction), `AVQ-018-023` (educational), `AVQ-018-024` (educational), `AVQ-018-025` (educational), `AVQ-018-026` (educational, fiction), `AVQ-018-027` (fiction), `AVQ-018-028` (fiction), `AVQ-018-029` (fiction), `AVQ-018-031` (educational, fiction), `AVQ-018-032` (fiction).

## Named passes that draw on this area

- `default_32`: `AVQ-018-001`
- `story_edit`: `AVQ-018-001`, `AVQ-018-002`, `AVQ-018-003`, `AVQ-018-004`, `AVQ-018-005`, `AVQ-018-006`, `AVQ-018-007`, `AVQ-018-008`
- `longer_cardboard_32`: `AVQ-018-003`, `AVQ-018-011`, `AVQ-018-012`, `AVQ-018-017`

## Questions

1. **AVQ-018-001** What visible event establishes what the protagonist wants before the first obstacle appears?
   - Failure hypothesis: The plot moves before a goal gives its events meaning.
   - Check or fix: Add or clarify a goal-defining action in the opening.
   - Severity: high. Modes: visual, human-audience. Stages: concept, script, storyboard, animatic. Style filters: fiction. Passes: default_32, story_edit.
2. **AVQ-018-002** Is the obstacle caused by the established situation, or does an unexplained intervention manufacture it?
   - Failure hypothesis: Arbitrary trouble replaces causal storytelling.
   - Check or fix: Connect the obstacle to a shown condition or earlier choice.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic. Style filters: fiction. Passes: story_edit.
3. **AVQ-018-003** Does the eventual solution use a capability or resource the audience had a fair chance to notice?
   - Failure hypothesis: An unseeded resource resolves the conflict without earned setup.
   - Check or fix: Seed the resource naturally before its decisive use.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction. Passes: story_edit, longer_cardboard_32.
4. **AVQ-018-004** Can viewers tell what failure would cost the character without being told in a long caption?
   - Failure hypothesis: Stakes remain abstract and do not support the action.
   - Check or fix: Show one concrete consequence of failure before escalation.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic. Style filters: fiction. Passes: story_edit.
5. **AVQ-018-005** Does the character's final choice differ meaningfully from the choice they would have made at the start?
   - Failure hypothesis: Surface action conceals an unchanged dramatic state.
   - Check or fix: Define the changed belief or keep the piece explicitly observational.
   - Severity: medium. Modes: visual, human-audience. Stages: concept, script, storyboard. Style filters: fiction. Passes: story_edit.
6. **AVQ-018-006** Is the payoff answering the specific expectation created by the opening image or line?
   - Failure hypothesis: The film promises one question and resolves another.
   - Check or fix: Write the promise and payoff side by side and reconcile them.
   - Severity: high. Modes: visual, human-audience. Stages: concept, script, storyboard, animatic, edit. Style filters: any. Passes: story_edit.
7. **AVQ-018-007** Does an early background detail actually matter later, or merely imitate the look of foreshadowing?
   - Failure hypothesis: Decorative setup attracts attention without narrative return.
   - Check or fix: Pay off, downweight, or remove the conspicuous detail.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction. Passes: story_edit.
8. **AVQ-018-008** Can viewers distinguish a deliberate misdirection from information the film simply withheld unfairly?
   - Failure hypothesis: Surprise depends on hiding facts the chosen viewpoint should reveal.
   - Check or fix: Audit viewpoint access and plant an honest alternative interpretation.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic. Style filters: fiction, puzzle. Passes: story_edit.
9. **AVQ-018-009** Does the protagonist cause the resolution through an understandable action?
   - Failure hypothesis: Coincidence completes the story while the protagonist watches.
   - Check or fix: Link the resolution to a choice, effort, or purposeful nonaction.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic. Style filters: fiction.
10. **AVQ-018-010** Is the helper's intervention motivated before it becomes essential?
   - Failure hypothesis: A convenient helper enters solely to repair the plot.
   - Check or fix: Establish the helper's motive or prior relationship.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard. Style filters: fiction.
11. **AVQ-018-011** Do repeated failed attempts change the character's understanding or the audience's expectation?
   - Failure hypothesis: Escalation is padded with interchangeable failures.
   - Check or fix: Give each attempt a distinct lesson, cost, or strategy change.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, animatic. Style filters: fiction. Passes: longer_cardboard_32.
12. **AVQ-018-012** Does the middle contain a meaningful change in circumstances rather than a longer version of the opening problem?
   - Failure hypothesis: The story stalls between premise and ending.
   - Check or fix: Introduce a consequence that forces a different approach.
   - Severity: high. Modes: visual, human-audience. Stages: concept, script, storyboard, animatic. Style filters: fiction. Passes: longer_cardboard_32.
13. **AVQ-018-013** Is a comic reversal grounded in a recognizable expectation that the audience actually forms?
   - Failure hypothesis: The punchline overturns an assumption viewers never made.
   - Check or fix: Test predictions immediately before the reversal and adjust setup.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction.
14. **AVQ-018-014** Can the central relationship be inferred from behavior instead of unexplained symbolic labels?
   - Failure hypothesis: Relationship stakes depend on exposition the film never supplies.
   - Check or fix: Add an interaction that demonstrates the relevant bond or tension.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, animatic. Style filters: fiction.
15. **AVQ-018-015** Does a flashback explain the present action without introducing a second unresolved story?
   - Failure hypothesis: Backstory competes with the current goal and creates stray promises.
   - Check or fix: Limit the flashback to the fact needed for the present decision.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction.
16. **AVQ-018-016** Is the audience supposed to know more than the character, and is that knowledge difference consistently maintained?
   - Failure hypothesis: Inconsistent dramatic irony makes reactions look irrational.
   - Check or fix: Track audience and character knowledge at every reveal.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction.
17. **AVQ-018-017** Does the ending show the consequence of the solution, rather than cutting immediately after the successful action?
   - Failure hypothesis: Resolution is asserted without a visible changed state.
   - Check or fix: Add a concise consequence or reaction that confirms the result.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction. Passes: longer_cardboard_32.
18. **AVQ-018-018** Is an ambiguous ending intentionally bounded to a small set of interpretations?
   - Failure hypothesis: Missing information is mistaken for purposeful ambiguity.
   - Check or fix: State the intended open question and test plausible readings.
   - Severity: medium. Modes: visual, human-audience. Stages: concept, script, storyboard, animatic, edit. Style filters: fiction.
19. **AVQ-018-019** Does an emotional reversal have a visible trigger that belongs to this character?
   - Failure hypothesis: Music or narration substitutes for motivated emotional change.
   - Check or fix: Show the triggering observation or decision in performance.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction.
20. **AVQ-018-020** Are objects important to the payoff introduced with enough identity to be recognized later?
   - Failure hypothesis: The audience sees a prop but cannot connect its later appearance.
   - Check or fix: Preserve a distinctive feature and stage its first appearance clearly.
   - Severity: high. Modes: visual, human-audience. Stages: storyboard, animatic, production, edit. Style filters: fiction.
21. **AVQ-018-021** Does the resolution honor the world's established rules about ability, scale, or consequence?
   - Failure hypothesis: The film changes its own rules to obtain a convenient ending.
   - Check or fix: Compare the payoff against a short explicit world-rule sheet.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic. Style filters: fiction.
22. **AVQ-018-022** Does a supposed sacrifice actually remove something the film has shown to matter?
   - Failure hypothesis: The story asks for emotion without demonstrating a real cost.
   - Check or fix: Establish the value beforehand and show the loss afterward.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, animatic. Style filters: fiction.
23. **AVQ-018-023** Can a short explanatory story be summarized as a causal chain rather than a list of related facts?
   - Failure hypothesis: Topic coherence is mistaken for an explanatory argument.
   - Check or fix: Connect each fact to the mechanism the next beat develops.
   - Severity: high. Modes: visual, human-audience. Stages: concept, script, storyboard, animatic. Style filters: educational.
24. **AVQ-018-024** Does the opening question remain answerable from the evidence actually shown?
   - Failure hypothesis: The story drifts into a broader claim than its demonstration supports.
   - Check or fix: Narrow the question or supply the missing evidence.
   - Severity: high. Modes: visual, human-audience. Stages: concept, script, storyboard, edit. Style filters: educational.
25. **AVQ-018-025** Is the demonstration's result revealed only after the viewer has seen the relevant starting conditions?
   - Failure hypothesis: Outcome-first editing makes a causal lesson impossible to evaluate.
   - Check or fix: Show the necessary baseline before interpreting the result.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: educational.
26. **AVQ-018-026** Does a moral or takeaway emerge from the shown consequences rather than contradicting them?
   - Failure hypothesis: The closing lesson is appended despite contrary story evidence.
   - Check or fix: Rewrite the takeaway to match the events or revise those events.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: educational, fiction.
27. **AVQ-018-027** Do two parallel storylines intersect for a reason the audience can explain?
   - Failure hypothesis: Alternation suggests a relationship that never becomes meaningful.
   - Check or fix: Establish the shared cause, contrast, or eventual interaction.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction.
28. **AVQ-018-028** Is a character's misunderstanding plausible from what they actually saw and heard?
   - Failure hypothesis: The plot relies on ignorance despite available information.
   - Check or fix: Audit the character's sensory access and adjust the mistaken inference.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: script, storyboard, animatic. Style filters: fiction.
29. **AVQ-018-029** Does a callback change the meaning of the original beat rather than merely repeat it?
   - Failure hypothesis: Familiarity is used as a substitute for a payoff.
   - Check or fix: Give the repeated action a new consequence or interpretation.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, animatic, edit. Style filters: fiction.
30. **AVQ-018-030** Is a cliffhanger appropriate to the promised viewing experience, or does it withhold the only useful answer?
   - Failure hypothesis: An incomplete ending breaks the short film's central promise.
   - Check or fix: Resolve the promised unit before opening a new question.
   - Severity: high. Modes: visual, human-audience. Stages: concept, script, storyboard, animatic, edit. Style filters: any.
31. **AVQ-018-031** If the final caption were removed, would the key emotional or causal resolution still be visible?
   - Failure hypothesis: Explanatory text conceals an unstaged ending.
   - Check or fix: Test a caption-free cut and strengthen the decisive visual action.
   - Severity: high. Modes: visual, human-audience. Stages: storyboard, animatic, edit. Style filters: educational, fiction.
32. **AVQ-018-032** Could the premise survive a change of palette and rendering style because its dramatic mechanism is specific?
   - Failure hypothesis: Cosmetic variation is being counted as a genuinely new story.
   - Check or fix: Compare goals, obstacles, choices, and outcomes across related pieces.
   - Severity: medium. Modes: visual, human-audience. Stages: concept, script. Style filters: fiction.
