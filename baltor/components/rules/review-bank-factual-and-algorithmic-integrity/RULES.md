# Adversarial review bank: D027 factual and algorithmic integrity (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D027 factual and algorithmic integrity". The questions below are the
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

- Severity: 1 critical, 31 high.
- Modes: 12 visual, 2 auditory, 31 machine, 15 human-audience.
- Need listening: 2; listening-only (no visual or machine route): none.
- Need a human audience: 15.
- Only answerable at final encode or delivery: none.
- Limited by style filter: `AVQ-027-001` (educational), `AVQ-027-002` (educational), `AVQ-027-003` (educational, live-action), `AVQ-027-004` (educational), `AVQ-027-005` (educational), `AVQ-027-006` (educational), `AVQ-027-007` (educational), `AVQ-027-008` (educational), `AVQ-027-009` (educational), `AVQ-027-010` (educational, 3d, vector), `AVQ-027-011` (educational), `AVQ-027-012` (educational), `AVQ-027-013` (educational), `AVQ-027-014` (educational, 3d), `AVQ-027-015` (educational, puzzle), `AVQ-027-016` (educational, screen-recording), `AVQ-027-017` (educational), `AVQ-027-018` (educational, puzzle), `AVQ-027-019` (educational), `AVQ-027-020` (educational, puzzle), `AVQ-027-021` (educational), `AVQ-027-022` (educational, screen-recording), `AVQ-027-026` (educational, screen-recording), `AVQ-027-027` (educational, screen-recording), `AVQ-027-028` (educational), `AVQ-027-029` (educational), `AVQ-027-030` (educational), `AVQ-027-031` (educational, live-action, 3d), `AVQ-027-032` (puzzle, screen-recording).

## Named passes that draw on this area

- `default_32`: `AVQ-027-001`
- `factual_puzzle`: `AVQ-027-001`, `AVQ-027-002`, `AVQ-027-003`, `AVQ-027-004`, `AVQ-027-005`, `AVQ-027-006`, `AVQ-027-007`, `AVQ-027-008`, `AVQ-027-009`, `AVQ-027-010`

## Questions

1. **AVQ-027-001** Can each factual sentence be matched to a source that supports its exact scope rather than merely the general topic?
   - Failure hypothesis: Broad source relevance is mistaken for support of a specific claim.
   - Check or fix: Build a claim-to-source ledger with exact supporting passages.
   - Severity: high. Modes: machine, human-audience. Stages: concept, script. Style filters: educational. Passes: default_32, factual_puzzle.
2. **AVQ-027-002** Are time-sensitive facts still valid at the date the video will be delivered?
   - Failure hypothesis: A formerly accurate script becomes misleading through age.
   - Check or fix: Recheck unstable claims against current authoritative sources before release.
   - Severity: high. Modes: machine. Stages: script, final-encode, delivery. Style filters: educational. Passes: factual_puzzle.
3. **AVQ-027-003** Does a historical claim match the exact locality, period, and object depicted?
   - Failure hypothesis: A generally plausible prop is used as evidence for an overly specific claim.
   - Check or fix: Verify the depicted variant and narrow unsupported specificity.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, production. Style filters: educational, live-action. Passes: factual_puzzle.
4. **AVQ-027-004** Are measurements and labels using consistent units and conversion assumptions throughout the film?
   - Failure hypothesis: Numerically plausible values mix incompatible units.
   - Check or fix: Independently recompute conversions and audit visible and spoken units.
   - Severity: high. Modes: machine, visual, auditory. Stages: script, production, edit. Style filters: educational. Passes: factual_puzzle.
5. **AVQ-027-005** Does a percentage state its denominator and comparison baseline clearly enough to reproduce it?
   - Failure hypothesis: A favorable percentage hides a changed denominator or base period.
   - Check or fix: Show the relevant counts and recompute the displayed percentage.
   - Severity: high. Modes: machine, visual. Stages: script, storyboard, production. Style filters: educational. Passes: factual_puzzle.
6. **AVQ-027-006** Are averages concealing variation that materially changes the lesson?
   - Failure hypothesis: A central value is presented as typical despite a wide or skewed distribution.
   - Check or fix: Inspect the distribution and add a relevant range or counterexample.
   - Severity: high. Modes: machine, visual, human-audience. Stages: concept, script, storyboard. Style filters: educational. Passes: factual_puzzle.
7. **AVQ-027-007** Does the edit distinguish correlation from a demonstrated causal mechanism?
   - Failure hypothesis: Associated events are narrated as cause and effect.
   - Check or fix: Audit causal wording against the study or demonstration design.
   - Severity: high. Modes: machine, human-audience. Stages: concept, script, storyboard, edit. Style filters: educational. Passes: factual_puzzle.
8. **AVQ-027-008** Is a counterfactual comparison supported by a valid method rather than an invented alternate outcome?
   - Failure hypothesis: The film fabricates what would have happened without the intervention.
   - Check or fix: State the method and assumptions or replace it with a verified worked case.
   - Severity: high. Modes: machine, human-audience. Stages: concept, script. Style filters: educational. Passes: factual_puzzle.
9. **AVQ-027-009** Are uncertainty and limitations visible at the point where the audience forms the conclusion?
   - Failure hypothesis: Caveats arrive too late to constrain an authoritative impression.
   - Check or fix: Place material uncertainty beside the claim and test interpretation.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, edit. Style filters: educational. Passes: factual_puzzle.
10. **AVQ-027-010** Are a diagram's idealizations clearly distinguished from measured or physically exact behavior?
   - Failure hypothesis: Clean animation is mistaken for observational evidence.
   - Check or fix: Label the model assumptions and identify where realism is intentionally omitted.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, production. Style filters: educational, 3d, vector. Passes: factual_puzzle.
11. **AVQ-027-011** Does a conserved quantity remain consistent across every displayed step when the lesson depends on conservation?
   - Failure hypothesis: Attractive animation creates or destroys the quantity it claims to track.
   - Check or fix: Reconcile a stepwise ledger with every relevant frame state.
   - Severity: high. Modes: machine, visual. Stages: storyboard, production. Style filters: educational.
12. **AVQ-027-012** Are interpolation and extrapolation visually distinguishable from actual observed data?
   - Failure hypothesis: Smooth curves imply measurements or predictions beyond the evidence.
   - Check or fix: Mark observed points and clearly identify modeled extensions.
   - Severity: high. Modes: machine, visual. Stages: script, storyboard, production. Style filters: educational.
13. **AVQ-027-013** Does the graph's axis choice preserve the comparison the narration claims?
   - Failure hypothesis: Truncation or nonlinear scaling exaggerates the apparent effect.
   - Check or fix: Replot with disclosed alternatives and review the claimed interpretation.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, production. Style filters: educational.
14. **AVQ-027-014** Is any simulated motion being described as a validated physical result without a suitable model check?
   - Failure hypothesis: Visual plausibility is treated as evidence of physical accuracy.
   - Check or fix: Separate illustrative animation from validated simulation claims.
   - Severity: high. Modes: machine, human-audience. Stages: concept, production. Style filters: educational, 3d.
15. **AVQ-027-015** Does a mathematically correct example rely on assumptions absent from the on-screen problem?
   - Failure hypothesis: The calculation solves a different problem than the viewer is given.
   - Check or fix: List assumptions and reconcile them with the stated setup.
   - Severity: high. Modes: machine, visual. Stages: script, storyboard, production. Style filters: educational, puzzle.
16. **AVQ-027-016** Do all displayed algorithm outputs come from the exact algorithm version being described?
   - Failure hypothesis: Explanatory graphics show hand-edited or stale results.
   - Check or fix: Regenerate outputs from the pinned implementation and compare them.
   - Severity: high. Modes: machine. Stages: production, final-encode. Style filters: educational, screen-recording.
17. **AVQ-027-017** Has the algorithm been checked on boundary inputs rather than only the attractive demonstration case?
   - Failure hypothesis: Empty, singleton, extreme, or invalid inputs expose unmentioned failure behavior.
   - Check or fix: Define the valid domain and test its meaningful boundaries.
   - Severity: high. Modes: machine. Stages: concept, production. Style filters: educational.
18. **AVQ-027-018** Are tie-breaking and ordering rules explicit when they can change the visible result?
   - Failure hypothesis: An apparently unique answer depends on an unstated arbitrary order.
   - Check or fix: Declare the rule and test tied or permuted inputs.
   - Severity: high. Modes: machine. Stages: script, storyboard, production. Style filters: educational, puzzle.
19. **AVQ-027-019** Can numerical rounding or tolerance choices flip a displayed classification or comparison?
   - Failure hypothesis: Near-boundary values produce unstable or misleading decisions.
   - Check or fix: Test values around thresholds and expose relevant tolerance rules.
   - Severity: high. Modes: machine. Stages: production. Style filters: educational.
20. **AVQ-027-020** Does random generation enforce the promised constraints for every output rather than merely most seeds?
   - Failure hypothesis: A successful sample is treated as proof of a universal invariant.
   - Check or fix: Test and validate each generated instance against the explicit constraints.
   - Severity: high. Modes: machine. Stages: production. Style filters: educational, puzzle.
21. **AVQ-027-021** Is the chosen demonstration seed representative rather than selected to hide common failures?
   - Failure hypothesis: Cherry-picked outputs exaggerate reliability or quality.
   - Check or fix: Inspect a declared sample set and report failures alongside the selected case.
   - Severity: high. Modes: machine, human-audience. Stages: concept, production. Style filters: educational.
22. **AVQ-027-022** Does the on-screen algorithm explanation account for failure or nontermination conditions that matter in use?
   - Failure hypothesis: A happy-path animation conceals an unsafe or unusable edge behavior.
   - Check or fix: Identify relevant failure states and demonstrate or disclose them.
   - Severity: high. Modes: machine. Stages: concept, script, production. Style filters: educational, screen-recording.
23. **AVQ-027-023** Are test results described only as evidence for the specific assertions the tests actually evaluate?
   - Failure hypothesis: Unit-test success is inflated into factual or production approval.
   - Check or fix: Map every success claim to test scope and untested dimensions.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any.
24. **AVQ-027-024** Are proposed capabilities clearly separated from capabilities demonstrated by a retained output?
   - Failure hypothesis: Plans and documentation are reported as completed functionality.
   - Check or fix: Require a concrete artifact and check record for each demonstrated claim.
   - Severity: high. Modes: machine. Stages: concept, delivery. Style filters: any.
25. **AVQ-027-025** Are counts of recipes, styles, stories, and tested videos using distinct definitions?
   - Failure hypothesis: Combinatorial variants are presented as independent authored or tested works.
   - Check or fix: Publish separate counts with explicit counting units.
   - Severity: high. Modes: machine. Stages: concept, delivery. Style filters: any.
26. **AVQ-027-026** Does a performance claim include the actual environment, input size, and end-to-end work measured?
   - Failure hypothesis: Selective timing omits setup, review, retries, or costly stages.
   - Check or fix: Record the complete measured workflow under stated conditions.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: educational, screen-recording.
27. **AVQ-027-027** Is a cost-saving claim based on actual charges and a comparable baseline?
   - Failure hypothesis: Estimates or omitted cloud costs are presented as demonstrated savings.
   - Check or fix: Reconcile invoices and measured effort with the comparison workflow.
   - Severity: high. Modes: machine, human-audience. Stages: concept, delivery. Style filters: educational, screen-recording.
28. **AVQ-027-028** Are safety-critical instructions blocked from authoritative presentation until appropriate current sources resolve them?
   - Failure hypothesis: Plausible but unchecked advice could cause real harm.
   - Check or fix: Obtain suitable current primary-source review and hold unresolved instructions.
   - Severity: critical. Modes: machine, human-audience. Stages: concept, script. Style filters: educational.
29. **AVQ-027-029** Do conflicting reliable sources remain visible as an unresolved issue rather than being silently averaged into a claim?
   - Failure hypothesis: Source disagreement is hidden behind false certainty.
   - Check or fix: Record the conflict, scope, and dates and narrow the claim if possible.
   - Severity: high. Modes: machine, human-audience. Stages: concept, script. Style filters: educational.
30. **AVQ-027-030** Does the final voice, caption, and graphic all state the same corrected fact after a script revision?
   - Failure hypothesis: A correction updates one channel while stale variants survive elsewhere.
   - Check or fix: Reconcile all delivered channels against the corrected claim ledger.
   - Severity: high. Modes: machine, visual, auditory. Stages: edit, final-encode. Style filters: educational.
31. **AVQ-027-031** Is a reconstructed, generated, or illustrative scene clearly distinguished from documentary evidence?
   - Failure hypothesis: Synthetic imagery appears to prove an event or observation.
   - Check or fix: Label the representation and cite the actual evidence separately.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, production, delivery. Style filters: educational, live-action, 3d.
32. **AVQ-027-032** Does the claim of interactivity correspond to actual user-controllable behavior rather than a prerecorded question?
   - Failure hypothesis: A passive video is marketed as interactive software.
   - Check or fix: Demonstrate the claimed input-response path or describe the work accurately.
   - Severity: high. Modes: machine, human-audience. Stages: concept, delivery. Style filters: puzzle, screen-recording.
