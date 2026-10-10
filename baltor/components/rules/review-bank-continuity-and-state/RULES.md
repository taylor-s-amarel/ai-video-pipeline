# Adversarial review bank: D016 continuity and state (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D016 continuity and state". The questions below are the
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

- Severity: 32 medium.
- Modes: 32 visual, 32 machine.
- Need listening: 0 (none are listening-only).
- Need a human audience: 0.
- Only answerable at final encode or delivery: none.
- Limited by style filter: `AVQ-016-022` (puzzle, educational).

## Named passes that draw on this area

- `default_32`: `AVQ-016-027`
- `performance_motion`: `AVQ-016-001`, `AVQ-016-002`, `AVQ-016-003`, `AVQ-016-004`, `AVQ-016-005`, `AVQ-016-006`, `AVQ-016-007`, `AVQ-016-008`
- `story_edit`: `AVQ-016-001`, `AVQ-016-002`, `AVQ-016-003`, `AVQ-016-004`, `AVQ-016-005`, `AVQ-016-006`, `AVQ-016-007`, `AVQ-016-008`
- `factual_puzzle`: `AVQ-016-001`, `AVQ-016-002`, `AVQ-016-003`, `AVQ-016-004`, `AVQ-016-005`, `AVQ-016-006`, `AVQ-016-007`, `AVQ-016-008`, `AVQ-016-009`, `AVQ-016-010`
- `final_delivery`: `AVQ-016-001`, `AVQ-016-002`, `AVQ-016-003`, `AVQ-016-004`, `AVQ-016-005`, `AVQ-016-006`, `AVQ-016-007`, `AVQ-016-008`
- `longer_cardboard_32`: `AVQ-016-003`

## Questions

1. **AVQ-016-001** Does the important object keep the same owner across the cut?
   - Failure hypothesis: Possession changes without an exchange.
   - Check or fix: Compare ownership immediately before and after edits.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, story_edit, factual_puzzle, final_delivery.
2. **AVQ-016-002** Are character screen directions consistent through continuous travel?
   - Failure hypothesis: Cut reverses the apparent route.
   - Check or fix: Track world path and projected direction.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, story_edit, factual_puzzle, final_delivery.
3. **AVQ-016-003** Does the costume retain meaningful details between shots?
   - Failure hypothesis: Character identity changes unintentionally.
   - Check or fix: Compare distinctive features across adjacent views.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, story_edit, factual_puzzle, final_delivery, longer_cardboard_32.
4. **AVQ-016-004** Are persistent props present in the correct locations after reframing?
   - Failure hypothesis: Set objects vanish or teleport.
   - Check or fix: Use a scene-state ledger and frame comparison.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, story_edit, factual_puzzle, final_delivery.
5. **AVQ-016-005** Does elapsed story time match visible environmental change?
   - Failure hypothesis: Lighting or wear changes too quickly.
   - Check or fix: Audit chronology against state changes.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, story_edit, factual_puzzle, final_delivery.
6. **AVQ-016-006** Are actions matched at the same phase across an edit?
   - Failure hypothesis: Motion jumps backward or repeats.
   - Check or fix: Compare pose and velocity around the cut.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, story_edit, factual_puzzle, final_delivery.
7. **AVQ-016-007** Does a consumed or broken object remain changed afterward?
   - Failure hypothesis: State resets undermine consequence.
   - Check or fix: Track irreversible state transitions explicitly.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, story_edit, factual_puzzle, final_delivery.
8. **AVQ-016-008** Are crowds preserving entity identity through occlusion and return?
   - Failure hypothesis: Duplicate or missing actors alter the story.
   - Check or fix: Audit persistent IDs rather than visible count alone.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, story_edit, factual_puzzle, final_delivery.
9. **AVQ-016-009** Does the timeline preserve the order of cause and effect?
   - Failure hypothesis: Result appears before its enabling event.
   - Check or fix: Check event dependencies against frame times.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: factual_puzzle.
10. **AVQ-016-010** Are labels describing the current state rather than the previous shot?
   - Failure hypothesis: Overlay update lags the scene.
   - Check or fix: Join label state to the same event clock.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: factual_puzzle.
11. **AVQ-016-011** Does a map remain geometrically consistent across zooms?
   - Failure hypothesis: Local views contradict the overview.
   - Check or fix: Compare landmarks in shared world coordinates.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-016-012** Are the hero's handedness and held items stable?
   - Failure hypothesis: Mirrored shots swap meaningful hands.
   - Check or fix: Audit left-right semantics at each camera change.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-016-013** Does a door or obstacle remain open after being moved?
   - Failure hypothesis: Environment resets without narrative explanation.
   - Check or fix: Retain state across scene boundaries.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-016-014** Are marks, damage and dirt consistent with prior events?
   - Failure hypothesis: Evidence of action disappears.
   - Check or fix: Track material changes as persistent states.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-016-015** Does a returning character enter from a plausible location?
   - Failure hypothesis: Reentry contradicts the established exit.
   - Check or fix: Map offscreen travel and available time.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-016-016** Are numerical counters updated at the event they claim to count?
   - Failure hypothesis: Display increments early or twice.
   - Check or fix: Bind counters to unique event IDs.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-016-017** Does a clock distinguish story time from playback time clearly?
   - Failure hypothesis: Timer implies an inaccurate duration.
   - Check or fix: Document timer semantics and check displayed values.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-016-018** Are alternative viewpoints synchronized to the same object state?
   - Failure hypothesis: Comparison panels show incompatible moments.
   - Check or fix: Use one authoritative state sample per frame.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-016-019** Does a repeated flashback look distinct from current action?
   - Failure hypothesis: Temporal structure is ambiguous.
   - Check or fix: Use a consistent bounded flashback cue.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-016-020** Are object scale changes motivated by camera or story events?
   - Failure hypothesis: Props resize between shots unnoticed by the script.
   - Check or fix: Compare world dimensions and projection separately.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-016-021** Does a loop return to a compatible starting state?
   - Failure hypothesis: Ending creates a discontinuity on replay.
   - Check or fix: Inspect seam pose, ownership and environment.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-016-022** Are hidden objects still accounted for in the state model?
   - Failure hypothesis: Occlusion is mistaken for deletion.
   - Check or fix: Separate visibility from existence.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: puzzle, educational.
23. **AVQ-016-023** Does the final count refer to entities rather than repeated appearances?
   - Failure hypothesis: Reentry inflates the claimed population.
   - Check or fix: Count unique IDs under the declared rule.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-016-024** Are scene resets labeled when demonstrating alternatives?
   - Failure hypothesis: Viewer interprets a comparison as continuous action.
   - Check or fix: Mark resets or maintain a clear split-screen structure.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-016-025** Does the narrative preserve information characters have learned?
   - Failure hypothesis: Actor forgets the solution to prolong the plot.
   - Check or fix: Track knowledge state alongside physical state.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-016-026** Are shadows and reflections consistent with object existence?
   - Failure hypothesis: Removed objects leave visual evidence behind.
   - Check or fix: Check secondary passes after state changes.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-016-027** Does the final artifact correspond to the cited source revision?
   - Failure hypothesis: Review evidence describes an older movie.
   - Check or fix: Match hashes and version identifiers before approval.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32.
28. **AVQ-016-028** Are title, captions and narration using the same names and numbers?
   - Failure hypothesis: Parallel text sources drift apart.
   - Check or fix: Compare against one approved script ledger.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-016-029** Does a repaired shot retain compatibility with neighboring shots?
   - Failure hypothesis: Local fix introduces a new continuity break.
   - Check or fix: Review both boundaries after replacement.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-016-030** Are transition overlaps creating a brief duplicate of a unique object?
   - Failure hypothesis: Crossfade looks like two simultaneous copies.
   - Check or fix: Inspect mixed frames at peak overlap.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-016-031** Does the ending retain the unresolved constraint needed for the joke?
   - Failure hypothesis: Final state accidentally removes the comic problem.
   - Check or fix: Compare payoff requirements with the actual tableau.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-016-032** Would a small continuity cue prevent a major viewer misreading?
   - Failure hypothesis: State change is correct but visually unannounced.
   - Check or fix: Add one clear possession, location or time cue.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
