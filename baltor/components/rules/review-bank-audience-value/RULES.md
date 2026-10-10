# Adversarial review bank: D030 audience value (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D030 audience value". The questions below are the
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
- Modes: 5 visual, 6 machine, 31 human-audience.
- Need listening: 0 (none are listening-only).
- Need a human audience: 31.
- Only answerable at final encode or delivery: none.
- Limited by style filter: `AVQ-030-003` (educational), `AVQ-030-004` (educational), `AVQ-030-006` (educational), `AVQ-030-007` (educational), `AVQ-030-008` (educational, screen-recording), `AVQ-030-009` (educational, screen-recording), `AVQ-030-010` (educational), `AVQ-030-017` (educational), `AVQ-030-018` (educational), `AVQ-030-019` (educational), `AVQ-030-020` (educational, screen-recording), `AVQ-030-021` (educational), `AVQ-030-022` (fiction), `AVQ-030-028` (educational, screen-recording), `AVQ-030-029` (educational, screen-recording), `AVQ-030-030` (fiction, puzzle), `AVQ-030-031` (educational).

## Named passes that draw on this area

- `default_32`: `AVQ-030-001`
- `story_edit`: `AVQ-030-001`, `AVQ-030-002`, `AVQ-030-003`, `AVQ-030-004`, `AVQ-030-005`, `AVQ-030-006`, `AVQ-030-007`, `AVQ-030-008`
- `factual_puzzle`: `AVQ-030-001`, `AVQ-030-002`, `AVQ-030-003`, `AVQ-030-004`, `AVQ-030-005`, `AVQ-030-006`, `AVQ-030-007`, `AVQ-030-008`, `AVQ-030-009`, `AVQ-030-010`

## Questions

1. **AVQ-030-001** What concrete thing should the intended viewer understand, feel, or be able to do after this video?
   - Failure hypothesis: A vague audience goal prevents meaningful evaluation of success.
   - Check or fix: Write one observable viewer outcome before judging the cut.
   - Severity: high. Modes: human-audience. Stages: concept. Style filters: any. Passes: default_32, story_edit, factual_puzzle.
2. **AVQ-030-002** Can first-time viewers state the video's central point without being told the creator's intention?
   - Failure hypothesis: Production familiarity is mistaken for communicated meaning.
   - Check or fix: Collect unprompted summaries after a single complete viewing.
   - Severity: high. Modes: visual, human-audience. Stages: animatic, edit. Style filters: any. Passes: story_edit, factual_puzzle.
3. **AVQ-030-003** Does the film assume background knowledge its intended audience actually lacks?
   - Failure hypothesis: Unstated prerequisites make the explanation inaccessible to novices.
   - Check or fix: Test the premise with representative novices and introduce necessary prerequisites.
   - Severity: high. Modes: human-audience. Stages: concept, script, storyboard, animatic. Style filters: educational. Passes: story_edit, factual_puzzle.
4. **AVQ-030-004** Is there enough specific value for an experienced viewer, or only an elaborate statement of the obvious?
   - Failure hypothesis: Visual polish disguises a trivial takeaway.
   - Check or fix: Ask informed viewers what new useful distinction they gained.
   - Severity: medium. Modes: human-audience. Stages: concept, script, animatic. Style filters: educational. Passes: story_edit, factual_puzzle.
5. **AVQ-030-005** Does the opening promise accurately describe the value the rest of the film delivers?
   - Failure hypothesis: A compelling hook attracts viewers to a different or weaker result.
   - Check or fix: Compare the hook with the actual demonstrated takeaway.
   - Severity: high. Modes: visual, human-audience. Stages: concept, script, animatic, edit. Style filters: any. Passes: story_edit, factual_puzzle.
6. **AVQ-030-006** Can viewers apply the lesson to a new example rather than merely repeat the shown answer?
   - Failure hypothesis: Recognition is mistaken for transferable understanding.
   - Check or fix: Present a different appropriate case after viewing.
   - Severity: high. Modes: human-audience. Stages: animatic, edit, delivery. Style filters: educational. Passes: story_edit, factual_puzzle.
7. **AVQ-030-007** Do viewers remember the essential point after a short delay without replaying the film?
   - Failure hypothesis: Immediate fluency masks fragile retention.
   - Check or fix: Use a delayed recall check matched to the intended use.
   - Severity: medium. Modes: human-audience. Stages: animatic, edit, delivery. Style filters: educational. Passes: story_edit, factual_puzzle.
8. **AVQ-030-008** Does the video save a user measurable effort compared with the manual workflow it claims to improve?
   - Failure hypothesis: Claimed convenience ignores setup, corrections, and review effort.
   - Check or fix: Compare complete workflows on the same realistic task.
   - Severity: high. Modes: machine, human-audience. Stages: concept, delivery. Style filters: educational, screen-recording. Passes: story_edit, factual_puzzle.
9. **AVQ-030-009** Is the benefit still present when the user must correct the output's common errors?
   - Failure hypothesis: A fast first result creates more downstream repair work.
   - Check or fix: Include observed repair effort in the usefulness comparison.
   - Severity: high. Modes: machine, human-audience. Stages: concept, delivery. Style filters: educational, screen-recording. Passes: factual_puzzle.
10. **AVQ-030-010** Can viewers identify what remains uncertain or unproven after watching?
   - Failure hypothesis: Persuasive presentation creates confidence beyond the evidence.
   - Check or fix: Ask viewers which claims were demonstrated and which remain open.
   - Severity: high. Modes: human-audience. Stages: animatic, edit, delivery. Style filters: educational. Passes: factual_puzzle.
11. **AVQ-030-011** Does the piece respect the viewing situation, such as interruption, background noise, or a small screen?
   - Failure hypothesis: A design that works in a quiet review room fails in normal use.
   - Check or fix: Test the actual intended context and prioritize its essential information.
   - Severity: high. Modes: visual, human-audience. Stages: animatic, edit, delivery. Style filters: any.
12. **AVQ-030-012** Would a viewer choose to watch the full runtime for the value delivered, without being obliged to review it?
   - Failure hypothesis: Creator interest is mistaken for audience attention.
   - Check or fix: Observe voluntary stopping points and ask what value remained unclear.
   - Severity: medium. Modes: human-audience. Stages: animatic, edit, delivery. Style filters: any.
13. **AVQ-030-013** Does the film provide a reason to care before requesting effortful interpretation?
   - Failure hypothesis: Audience labor is demanded before a relevant benefit is established.
   - Check or fix: Introduce a concrete stake or practical question early.
   - Severity: medium. Modes: visual, human-audience. Stages: concept, script, animatic. Style filters: any.
14. **AVQ-030-014** Are emotional reactions based on the story rather than pressure from manipulative framing or exaggerated claims?
   - Failure hypothesis: Presentation extracts a response without earning trust.
   - Check or fix: Ask viewers what specifically caused their reaction and check supporting content.
   - Severity: high. Modes: human-audience. Stages: animatic, edit. Style filters: any.
15. **AVQ-030-015** Does the film's novelty come from a useful idea or experience rather than only a different visual skin?
   - Failure hypothesis: Surface variation is counted as additional audience value.
   - Check or fix: Compare takeaways and experiences across related films without style labels.
   - Severity: medium. Modes: human-audience. Stages: concept. Style filters: any.
16. **AVQ-030-016** Can a viewer distinguish the intended subject from decorative spectacle when asked what mattered?
   - Failure hypothesis: High production density competes with the actual point.
   - Check or fix: Collect salience rankings and reduce low-value dominant elements.
   - Severity: high. Modes: visual, human-audience. Stages: animatic, edit. Style filters: any.
17. **AVQ-030-017** Does the video make a difficult concept easier to reason about than a simpler static explanation would?
   - Failure hypothesis: Motion adds complexity without explanatory benefit.
   - Check or fix: Compare comprehension using the video and a concise static alternative.
   - Severity: medium. Modes: human-audience. Stages: concept, animatic. Style filters: educational.
18. **AVQ-030-018** Is the format appropriate to the viewer's task, such as learning a process versus checking a reference fact?
   - Failure hypothesis: A linear film is used for information viewers need to scan or revisit.
   - Check or fix: Observe task behavior and add a suitable companion reference if warranted.
   - Severity: medium. Modes: human-audience. Stages: concept, delivery, edit. Style filters: educational.
19. **AVQ-030-019** Does the conclusion leave the viewer with a feasible next step when action is the purpose?
   - Failure hypothesis: The film motivates action without explaining what can actually be done.
   - Check or fix: Ask viewers to name their next step and remove practical ambiguity.
   - Severity: high. Modes: human-audience. Stages: script, animatic, edit, delivery. Style filters: educational.
20. **AVQ-030-020** Are effort, tools, prerequisites, and costs disclosed when viewers are encouraged to replicate a result?
   - Failure hypothesis: A polished demonstration hides barriers that affect usefulness.
   - Check or fix: Itemize the actual replication requirements beside the demonstrated outcome.
   - Severity: high. Modes: machine, human-audience. Stages: script, delivery. Style filters: educational, screen-recording.
21. **AVQ-030-021** Can viewers recognize the limits of the example instead of generalizing it to unsuitable situations?
   - Failure hypothesis: A memorable example becomes an overbroad rule.
   - Check or fix: Test a boundary case and make the relevant limitation explicit.
   - Severity: high. Modes: human-audience. Stages: script, animatic, edit, delivery. Style filters: educational.
22. **AVQ-030-022** Does humor rely on cultural knowledge the intended audience is likely to share?
   - Failure hypothesis: The setup is invisible to viewers outside the creator's reference group.
   - Check or fix: Test the joke with relevant audience groups and revise missing context.
   - Severity: medium. Modes: human-audience. Stages: concept, script, animatic. Style filters: fiction.
23. **AVQ-030-023** Are potentially alienating depictions necessary to the film's purpose and understood as intended?
   - Failure hypothesis: Unexamined stereotypes distract or harm trust.
   - Check or fix: Seek relevant perspective and revise unsupported representational shortcuts.
   - Severity: high. Modes: human-audience. Stages: concept, script, storyboard, animatic. Style filters: any.
24. **AVQ-030-024** Does the film reward attention with a satisfying resolution rather than an engagement bait that never pays off?
   - Failure hypothesis: A question or promise exists only to prolong viewing.
   - Check or fix: Identify the delivered payoff and test whether viewers feel the promise was met.
   - Severity: high. Modes: human-audience. Stages: concept, script, animatic, edit. Style filters: any.
25. **AVQ-030-025** Do actual audience findings remain separate from synthetic reviewer suggestions in the report?
   - Failure hypothesis: Generated opinions are presented as human research.
   - Check or fix: Label the origin of every review and report human sample details honestly.
   - Severity: high. Modes: machine. Stages: animatic, delivery. Style filters: any.
26. **AVQ-030-026** Is the audience sample relevant to the intended users rather than only the production team?
   - Failure hypothesis: Familiar or expert reviewers miss novice misunderstandings.
   - Check or fix: Document participant relevance and recruit appropriate review when authorized.
   - Severity: high. Modes: human-audience. Stages: animatic, delivery. Style filters: any.
27. **AVQ-030-027** Does the evaluation question measure the intended outcome instead of asking only whether viewers liked the video?
   - Failure hypothesis: Satisfaction is mistaken for comprehension, accuracy, or usefulness.
   - Check or fix: Match the question and task to the stated success criterion.
   - Severity: high. Modes: human-audience. Stages: concept, animatic. Style filters: any.
28. **AVQ-030-028** Are observed improvements large enough to matter in the viewer's real task?
   - Failure hypothesis: A measurable change is framed as valuable despite negligible practical effect.
   - Check or fix: Define a task-relevant benefit threshold and compare actual outcomes.
   - Severity: medium. Modes: machine, human-audience. Stages: animatic, delivery. Style filters: educational, screen-recording.
29. **AVQ-030-029** Does a polished before-and-after comparison hold task difficulty and input quality constant?
   - Failure hypothesis: Unfair conditions exaggerate the apparent value of the approach.
   - Check or fix: Match inputs and conditions and disclose unavoidable differences.
   - Severity: high. Modes: machine, human-audience. Stages: concept, animatic, delivery. Style filters: educational, screen-recording.
30. **AVQ-030-030** Is the viewer asked to do more work than the payoff justifies, such as reading dense setup for a minor joke?
   - Failure hypothesis: Participation cost exceeds the value of the experience.
   - Check or fix: Observe effort and confusion, then simplify setup or strengthen payoff.
   - Severity: medium. Modes: human-audience. Stages: concept, animatic. Style filters: fiction, puzzle.
31. **AVQ-030-031** Can skeptical viewers locate the evidence behind the video's strongest claim?
   - Failure hypothesis: Credibility depends on production authority rather than inspectable support.
   - Check or fix: Provide a clear evidence route appropriate to the delivery format.
   - Severity: high. Modes: human-audience. Stages: script, delivery. Style filters: educational.
32. **AVQ-030-032** Does repeating the viewing reveal useful detail or merely expose the lack of a clear first-view explanation?
   - Failure hypothesis: Required replay is mislabeled as replay value.
   - Check or fix: Ask what prompted replay and distinguish enrichment from repair.
   - Severity: medium. Modes: human-audience. Stages: animatic, edit, delivery. Style filters: any.
