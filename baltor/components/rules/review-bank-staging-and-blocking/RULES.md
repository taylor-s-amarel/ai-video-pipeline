# Adversarial review bank: D005 staging and blocking (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D005 staging and blocking". The questions below are the
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
- Modes: 32 visual.
- Need listening: 0 (none are listening-only).
- Need a human audience: 0.
- Only answerable at final encode or delivery: none.
- Limited by style filter: none.

## Named passes that draw on this area

- `default_32`: `AVQ-005-003`
- `visual_depth_contact`: `AVQ-005-001`, `AVQ-005-002`, `AVQ-005-003`, `AVQ-005-004`, `AVQ-005-005`, `AVQ-005-006`, `AVQ-005-007`, `AVQ-005-008`
- `performance_motion`: `AVQ-005-001`, `AVQ-005-002`, `AVQ-005-003`, `AVQ-005-004`, `AVQ-005-005`, `AVQ-005-006`, `AVQ-005-007`, `AVQ-005-008`
- `story_edit`: `AVQ-005-001`, `AVQ-005-002`, `AVQ-005-003`, `AVQ-005-004`, `AVQ-005-005`, `AVQ-005-006`, `AVQ-005-007`, `AVQ-005-008`
- `longer_cardboard_32`: `AVQ-005-016`

## Questions

1. **AVQ-005-001** Is the character's immediate goal visible in the staging?
   - Failure hypothesis: Movement has no readable target.
   - Check or fix: Place goal and actor in a clear spatial relationship.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, story_edit.
2. **AVQ-005-002** Does the actor face the important event when it occurs?
   - Failure hypothesis: Blocking hides attention and response.
   - Check or fix: Align gaze and torso with the attended event.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, story_edit.
3. **AVQ-005-003** Are cause and consequence visible in the same beat?
   - Failure hypothesis: Staging separates the action from its result.
   - Check or fix: Reframe or add a motivated reaction cut.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32, visual_depth_contact, performance_motion, story_edit.
4. **AVQ-005-004** Does a supporting character accidentally steal the scene?
   - Failure hypothesis: Secondary action is larger or earlier than the main action.
   - Check or fix: Reduce its motion during the decisive beat.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, story_edit.
5. **AVQ-005-005** Can characters reach their props without implausible stretching?
   - Failure hypothesis: Prop placement exceeds the rig's natural reach.
   - Check or fix: Check reach envelopes before animation.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, story_edit.
6. **AVQ-005-006** Is a crucial exchange hidden behind another body?
   - Failure hypothesis: Blocking conceals possession transfer.
   - Check or fix: Open a clean sightline to the handoff.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, story_edit.
7. **AVQ-005-007** Does each character have a distinct action rather than generic motion?
   - Failure hypothesis: Busy movement substitutes for intention.
   - Check or fix: Assign one playable objective per beat.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, story_edit.
8. **AVQ-005-008** Are entrances timed to establish identity before interaction?
   - Failure hypothesis: New actors arrive and act before recognition.
   - Check or fix: Allow an orienting pose or entrance cue.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, story_edit.
9. **AVQ-005-009** Does the exit direction preserve the established geography?
   - Failure hypothesis: A character leaves toward an impossible destination.
   - Check or fix: Track screen and world directions together.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
10. **AVQ-005-010** Is the obstacle positioned where it can genuinely impede the goal?
   - Failure hypothesis: Conflict is asserted without spatial support.
   - Check or fix: Show the blocked route and available alternatives.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
11. **AVQ-005-011** Do characters queue in a visually traceable order?
   - Failure hypothesis: Crowd staging implies multiple conflicting lines.
   - Check or fix: Trace the queue path through turns and overlaps.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-005-012** Is a reaction staged where viewers are already looking?
   - Failure hypothesis: Important response occurs outside the attention region.
   - Check or fix: Move the reaction or guide attention before it.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-005-013** Does the hero turn away during the most expressive pose?
   - Failure hypothesis: Blocking hides the emotional information.
   - Check or fix: Use a readable three-quarter orientation.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-005-014** Are characters standing too close to read as separate agents?
   - Failure hypothesis: Bodies merge into an ambiguous group.
   - Check or fix: Create meaningful spacing or stagger depth.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-005-015** Does the staging support the intended power relationship?
   - Failure hypothesis: Height and distance contradict the dramatic roles.
   - Check or fix: Compare status cues with the scene's intention.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-005-016** Can the viewer see the object before it becomes important?
   - Failure hypothesis: A prop appears only at the solution.
   - Check or fix: Plant the prop naturally in an earlier composition.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: longer_cardboard_32.
17. **AVQ-005-017** Does the solution require an unestablished route or opening?
   - Failure hypothesis: Blocking invents space at the climax.
   - Check or fix: Establish usable pathways before the payoff.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-005-018** Are pauses placed where bodies can actually balance?
   - Failure hypothesis: A held pose would topple without support.
   - Check or fix: Shift weight or add a justified contact point.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-005-019** Does simultaneous action overload the viewer's attention?
   - Failure hypothesis: Several causal events compete within one interval.
   - Check or fix: Sequence actions or establish a deliberate hierarchy.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-005-020** Are paired characters differentiated by behavior and position?
   - Failure hypothesis: Symmetric blocking makes identities interchangeable.
   - Check or fix: Give each a distinct stance and objective.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-005-021** Does the actor's path cross readable text at the wrong time?
   - Failure hypothesis: Action occludes information during its reading interval.
   - Check or fix: Separate path and text regions or retime them.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-005-022** Are the most important hands visible from the chosen angle?
   - Failure hypothesis: Torso or costume hides the acting instrument.
   - Check or fix: Adjust elbows, prop position or camera.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-005-023** Does the crowd leave enough room for the hero's performance?
   - Failure hypothesis: Population fills the gesture envelope.
   - Check or fix: Reserve a clear acting pocket.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-005-024** Is the destination introduced before a long traversal?
   - Failure hypothesis: Travel feels arbitrary until the endpoint appears.
   - Check or fix: Show a destination cue at departure.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-005-025** Does the blocking explain who initiates cooperation?
   - Failure hypothesis: Joint action lacks a readable decision.
   - Check or fix: Stage an initiating gesture and acknowledgment.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-005-026** Are background actors reacting to the same event time?
   - Failure hypothesis: Crowd responses imply conflicting causes.
   - Check or fix: Align reactions to the shared event clock.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-005-027** Does repeated staging make escalation feel unchanged?
   - Failure hypothesis: New attempts look like copies of the first.
   - Check or fix: Change spatial stakes or action strategy meaningfully.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-005-028** Is the final tableau readable as a resolved relationship?
   - Failure hypothesis: Ending poses do not show what changed.
   - Check or fix: Stage the new ownership, distance or shared goal.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-005-029** Can a viewer follow the hero through a crowd crossing?
   - Failure hypothesis: Identifying features are hidden during a critical transition.
   - Check or fix: Preserve a visible marker or isolate the path.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-005-030** Does the staging accidentally imply aggression or danger?
   - Failure hypothesis: Friendly interaction uses threatening proximity or angles.
   - Check or fix: Review body orientation and interpersonal distance.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-005-031** Are offscreen actions sufficiently established to be believable?
   - Failure hypothesis: Plot depends on unseen unexplained activity.
   - Check or fix: Provide a clear setup or bounded evidence insert.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-005-032** Would a single repositioning remove the need for explanatory dialogue?
   - Failure hypothesis: Language compensates for unclear spatial relationships.
   - Check or fix: Try a clearer blocking solution first.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
