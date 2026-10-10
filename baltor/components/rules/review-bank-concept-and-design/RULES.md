# Adversarial review bank: D001 concept and design (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D001 concept and design". The questions below are the
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
- Modes: 32 visual, 1 human-audience.
- Need listening: 0 (none are listening-only).
- Need a human audience: 1.
- Only answerable at final encode or delivery: none.
- Limited by style filter: none.

## Named passes that draw on this area

- `default_32`: `AVQ-001-001`
- `story_edit`: `AVQ-001-001`, `AVQ-001-002`, `AVQ-001-003`, `AVQ-001-004`, `AVQ-001-005`, `AVQ-001-006`, `AVQ-001-007`, `AVQ-001-008`
- `longer_cardboard_32`: `AVQ-001-003`, `AVQ-001-026`

## Questions

1. **AVQ-001-001** Can the first image communicate the film's central promise?
   - Failure hypothesis: Opening conceals the viewing purpose.
   - Check or fix: Show opening without its title to a fresh viewer.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: default_32, story_edit.
2. **AVQ-001-002** Does the chosen visual style make the subject easier to understand?
   - Failure hypothesis: Style adds decoration without explanatory value.
   - Check or fix: Compare one beat in the proposed and simpler styles.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: story_edit.
3. **AVQ-001-003** Is the visual metaphor consistent with the actual mechanism?
   - Failure hypothesis: Metaphor teaches a false relationship.
   - Check or fix: Map each metaphor element to its intended meaning.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: story_edit, longer_cardboard_32.
4. **AVQ-001-004** Would removing the hero character improve the explanation?
   - Failure hypothesis: Host competes with the information.
   - Check or fix: Test a host-free version of one dense beat.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: story_edit.
5. **AVQ-001-005** Does every recurring graphic have a stable meaning?
   - Failure hypothesis: Decorative reuse changes semantic meaning.
   - Check or fix: Audit recurring symbols against a single legend.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: story_edit.
6. **AVQ-001-006** Is the design distinctive without depending on a borrowed character?
   - Failure hypothesis: Identity relies on recognizable protected features.
   - Check or fix: Replace signature borrowed features with original design logic.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: story_edit.
7. **AVQ-001-007** Does the visual grammar permit the required emotional range?
   - Failure hypothesis: Chosen abstraction cannot express the turning point.
   - Check or fix: Thumbnail both the quietest and strongest reaction.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: story_edit.
8. **AVQ-001-008** Is complexity concentrated where the viewer needs information?
   - Failure hypothesis: Detail budget is spent on irrelevant scenery.
   - Check or fix: Rank scene elements by narrative necessity.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: story_edit.
9. **AVQ-001-009** Can the premise survive without explanatory labels everywhere?
   - Failure hypothesis: Labels compensate for unreadable action.
   - Check or fix: Review a label-free storyboard before refining captions.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
10. **AVQ-001-010** Does the world establish which impossible actions are allowed?
   - Failure hypothesis: Fictional rules change only to resolve the plot.
   - Check or fix: List impossible events and seed their rules early.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
11. **AVQ-001-011** Are style shifts motivated by story or information changes?
   - Failure hypothesis: Unmotivated shifts break the film's identity.
   - Check or fix: Attach a purpose to each style boundary.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
12. **AVQ-001-012** Does the palette distinguish functions before decorating them?
   - Failure hypothesis: Aesthetic palette erases important categories.
   - Check or fix: Assign functional roles before choosing accent colors.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
13. **AVQ-001-013** Can the design scale to the most crowded required scene?
   - Failure hypothesis: Hero design collapses when multiplied.
   - Check or fix: Test the largest crowd at delivery resolution.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
14. **AVQ-001-014** Is the hero recognizable through its most extreme pose?
   - Failure hypothesis: Design identity depends on one front-facing portrait.
   - Check or fix: Compare key poses as small unlabeled thumbnails.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
15. **AVQ-001-015** Does the setting provide useful action opportunities?
   - Failure hypothesis: Scenery cannot support the scripted interactions.
   - Check or fix: Mark every prop and surface the action uses.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
16. **AVQ-001-016** Are ornamental motifs misleading viewers about causal importance?
   - Failure hypothesis: Decorations resemble clues or controls.
   - Check or fix: Remove ornaments near the causal focus and compare.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
17. **AVQ-001-017** Is the intended genre legible before the first reversal?
   - Failure hypothesis: Comic styling makes serious claims seem unserious.
   - Check or fix: Check opening tone against the story's consequence.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
18. **AVQ-001-018** Does the visual system accommodate uncertainty honestly?
   - Failure hypothesis: Polished certainty masks incomplete evidence.
   - Check or fix: Design a clear visual treatment for qualified claims.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
19. **AVQ-001-019** Are scale exaggerations explicitly separated from measurements?
   - Failure hypothesis: Expressive proportions are read as quantitative truth.
   - Check or fix: Label illustrative scale where comparisons depend on size.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
20. **AVQ-001-020** Does the design avoid stereotypes as character shorthand?
   - Failure hypothesis: Identity traits replace individual characterization.
   - Check or fix: Give roles distinctive goals and behavior instead.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
21. **AVQ-001-021** Would an unfamiliar viewer understand the icon vocabulary?
   - Failure hypothesis: Icons require unstated cultural knowledge.
   - Check or fix: Ask viewers to name icons without a legend.
   - Severity: medium. Modes: visual, human-audience. Stages: concept, script, storyboard, animatic. Style filters: any.
22. **AVQ-001-022** Is visual richness earned by meaningful variation?
   - Failure hypothesis: Many objects repeat the same information.
   - Check or fix: Remove repeated detail that adds neither rhythm nor meaning.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
23. **AVQ-001-023** Does the film's aesthetic match its delivery context?
   - Failure hypothesis: Subtle design disappears in expected viewing conditions.
   - Check or fix: Preview under likely screen size and ambient light.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
24. **AVQ-001-024** Can the design support a clear ending state?
   - Failure hypothesis: Ending looks indistinguishable from the starting state.
   - Check or fix: Compare first and last meaningful frames side by side.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
25. **AVQ-001-025** Is the central contrast visible without narration?
   - Failure hypothesis: Key comparison exists only in spoken explanation.
   - Check or fix: Make the contrasted states visually distinguishable.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
26. **AVQ-001-026** Does the mood board contain conflicting material rules?
   - Failure hypothesis: Mixed references produce an incoherent world.
   - Check or fix: Choose explicit rules for edges, light and texture.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any. Passes: longer_cardboard_32.
27. **AVQ-001-027** Are designed imperfections intentional and repeatable?
   - Failure hypothesis: Random defects are mistaken for handmade style.
   - Check or fix: Define which imperfections belong and remove others.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
28. **AVQ-001-028** Does abstraction remove the detail needed to judge success?
   - Failure hypothesis: Simplification hides the actual result.
   - Check or fix: Restore the smallest evidence-bearing feature.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
29. **AVQ-001-029** Can the design accommodate captions without shrinking the action?
   - Failure hypothesis: Accessibility was excluded from the layout concept.
   - Check or fix: Reserve readable caption space in initial thumbnails.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
30. **AVQ-001-030** Does the film need all its branded framing?
   - Failure hypothesis: Persistent branding consumes attention and action area.
   - Check or fix: Compare a restrained framing treatment at phone size.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
31. **AVQ-001-031** Is there a coherent hierarchy between world and interface graphics?
   - Failure hypothesis: Labels and physical objects appear equally tangible.
   - Check or fix: Give annotations a consistent separate graphic grammar.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
32. **AVQ-001-032** What single design change would most strengthen the viewing promise?
   - Failure hypothesis: Many small polish changes avoid the main weakness.
   - Check or fix: Choose one premise-level improvement before surface polish.
   - Severity: medium. Modes: visual. Stages: concept, script, storyboard, animatic. Style filters: any.
