# Adversarial review bank: D024 sfx and mix (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D024 sfx and mix". The questions below are the
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

- Severity: 15 high, 17 medium.
- Modes: 7 visual, 32 auditory, 12 machine, 12 human-audience.
- Need listening: 32 (`AVQ-024-002`, `AVQ-024-003`, `AVQ-024-006`, `AVQ-024-008`, `AVQ-024-009`, `AVQ-024-012`, `AVQ-024-013`, `AVQ-024-017`, `AVQ-024-018`, `AVQ-024-020`, `AVQ-024-024`, `AVQ-024-026`, `AVQ-024-028`, `AVQ-024-029` are listening-only).
- Need a human audience: 12.
- Only answerable at final encode or delivery: `AVQ-024-001`, `AVQ-024-006`, `AVQ-024-021`, `AVQ-024-022`, `AVQ-024-027`, `AVQ-024-031`.
- Limited by style filter: `AVQ-024-008` (live-action, fiction), `AVQ-024-025` (educational).

## Named passes that draw on this area

- `default_32`: `AVQ-024-001`
- `sound`: `AVQ-024-001`, `AVQ-024-002`, `AVQ-024-003`, `AVQ-024-004`, `AVQ-024-005`, `AVQ-024-006`, `AVQ-024-007`, `AVQ-024-008`, `AVQ-024-009`, `AVQ-024-010`, `AVQ-024-011`, `AVQ-024-012`, `AVQ-024-013`, `AVQ-024-014`, `AVQ-024-015`, `AVQ-024-016`

## Questions

1. **AVQ-024-001** Does the delivered mix contain audible distortion at impacts or other peaks despite an unclipped project meter?
   - Failure hypothesis: Encoding or intersample peaks distort the exported waveform.
   - Check or fix: Measure the final file and actually listen to its loudest events.
   - Severity: high. Modes: machine, auditory. Stages: final-encode. Style filters: any. Passes: default_32, sound.
2. **AVQ-024-002** Is dialogue intelligible under the busiest music and effects passage at ordinary listening volume?
   - Failure hypothesis: Masking peaks hide speech despite acceptable overall loudness.
   - Check or fix: Listen to the complete mix and rebalance the busiest interval.
   - Severity: high. Modes: auditory, human-audience. Stages: edit, final-encode. Style filters: any. Passes: sound.
3. **AVQ-024-003** Does dialogue ducking recover naturally after speech rather than making the music audibly surge between words?
   - Failure hypothesis: Overfast gain recovery causes distracting pumping.
   - Check or fix: Listen across short speech gaps and revise ducking timing.
   - Severity: medium. Modes: auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
4. **AVQ-024-004** Does the mix retain essential sounds when summed to mono?
   - Failure hypothesis: Phase cancellation removes cues on single-speaker playback.
   - Check or fix: Audition a mono downmix and repair phase-dependent elements.
   - Severity: high. Modes: machine, auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
5. **AVQ-024-005** Are low-frequency effects crowding out clarity or wasting headroom without an audible storytelling benefit?
   - Failure hypothesis: Sub-bass accumulation drives limiting while contributing little useful sound.
   - Check or fix: Listen full-range and on phone speakers, then trim unsupported low end.
   - Severity: medium. Modes: machine, auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
6. **AVQ-024-006** Does the soundtrack remain balanced on the actual phone or laptop speakers likely to be used?
   - Failure hypothesis: A studio-only mix depends on bass and detail small speakers cannot reproduce.
   - Check or fix: Listen on representative devices and rebalance essential cues.
   - Severity: high. Modes: auditory, human-audience. Stages: final-encode, delivery. Style filters: any. Passes: sound.
7. **AVQ-024-007** Are important off-screen sounds too far to one stereo side to be heard reliably with one earbud?
   - Failure hypothesis: Hard panning makes a narrative cue fragile in common listening conditions.
   - Check or fix: Audition each channel alone and reposition or reinforce essential cues.
   - Severity: high. Modes: machine, auditory, human-audience. Stages: edit, final-encode. Style filters: any. Passes: sound.
8. **AVQ-024-008** Does ambience continue naturally through cuts within the same place and time?
   - Failure hypothesis: Room or environmental tone resets expose edits and break continuity.
   - Check or fix: Listen without picture across cuts and smooth justified ambience transitions.
   - Severity: medium. Modes: auditory. Stages: edit. Style filters: live-action, fiction. Passes: sound.
9. **AVQ-024-009** Do noise gates audibly chop breaths, room tone, or sustained sound tails?
   - Failure hypothesis: Threshold processing creates abrupt silence and damaged decay.
   - Check or fix: Listen to soft endings and ease gating or use manual cleanup.
   - Severity: medium. Modes: auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
10. **AVQ-024-010** Is reverberation appropriate to the apparent room size and source distance?
   - Failure hypothesis: Acoustic space contradicts the visual environment.
   - Check or fix: Listen with picture and adjust early reflections and decay contextually.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: production, edit. Style filters: any. Passes: sound.
11. **AVQ-024-011** Are footsteps, touches, and object movements giving the represented material and weight a plausible sound?
   - Failure hypothesis: Generic effects make soft, heavy, or hollow objects sound alike.
   - Check or fix: Listen with picture and replace mismatched material cues.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: production, edit. Style filters: any. Passes: sound.
12. **AVQ-024-012** Does a major impact have a distinct onset and decay rather than becoming an undifferentiated wall of effects?
   - Failure hypothesis: Layer stacking removes the event's audible shape.
   - Check or fix: Audition effect layers separately and restore a clear attack/body/tail structure.
   - Severity: medium. Modes: auditory. Stages: production, edit. Style filters: any. Passes: sound.
13. **AVQ-024-013** Are repeated effects varying in a way that avoids machine-like repetition while preserving the event's identity?
   - Failure hypothesis: Identical samples reveal the production pattern.
   - Check or fix: Listen to the entire repeated sequence and vary suitable takes or articulation.
   - Severity: medium. Modes: auditory. Stages: production, edit. Style filters: any. Passes: sound.
14. **AVQ-024-014** Does a sound continue after its source has visibly stopped for a physically or narratively justified reason?
   - Failure hypothesis: Untrimmed effects imply motion or activity no longer present.
   - Check or fix: Listen with picture and align source cessation and credible decay.
   - Severity: high. Modes: visual, auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
15. **AVQ-024-015** Are quiet atmospheric details audible enough to support the scene without making viewers raise volume dangerously before loud events?
   - Failure hypothesis: Excessive dynamic range creates an impractical listening experience.
   - Check or fix: Listen at one fixed normal level and rebalance essential quiet and loud passages.
   - Severity: high. Modes: machine, auditory, human-audience. Stages: edit, final-encode. Style filters: any. Passes: sound.
16. **AVQ-024-016** Does compression preserve the punch of intentional transients rather than flatten every action?
   - Failure hypothesis: Heavy limiting removes contrast and makes impacts feel weak.
   - Check or fix: Listen to level-matched processed and unprocessed versions.
   - Severity: medium. Modes: machine, auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
17. **AVQ-024-017** Is there a harsh resonant frequency that becomes tiring over the full runtime?
   - Failure hypothesis: Narrowband buildup is tolerable briefly but fatiguing across the film.
   - Check or fix: Listen continuously and reduce the identified resonance selectively.
   - Severity: medium. Modes: auditory. Stages: edit, final-encode. Style filters: any.
18. **AVQ-024-018** Do looped ambience beds have audible seams or repeated identifiable events?
   - Failure hypothesis: A background loop reveals itself through a recurring chirp, click, or level jump.
   - Check or fix: Listen across multiple loops and edit or vary the bed.
   - Severity: medium. Modes: auditory. Stages: production, edit, final-encode. Style filters: any.
19. **AVQ-024-019** Are source distance changes accompanied by believable changes in level, detail, and room contribution?
   - Failure hypothesis: A moving source sounds fixed next to the listener.
   - Check or fix: Listen with the movement and automate acoustic perspective deliberately.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: production, edit. Style filters: any.
20. **AVQ-024-020** Does the mix make a decorative sound more prominent than the story's causal sound?
   - Failure hypothesis: Salient ornament distracts from the event viewers must understand.
   - Check or fix: Listen without picture to identify the perceived foreground, then rebalance.
   - Severity: high. Modes: auditory, human-audience. Stages: animatic, edit. Style filters: any.
21. **AVQ-024-021** Are left and right channels mapped correctly for directional cues?
   - Failure hypothesis: A routing swap contradicts on-screen movement.
   - Check or fix: Listen to a known directional sequence in the delivered file.
   - Severity: high. Modes: machine, visual, auditory. Stages: final-encode. Style filters: any.
22. **AVQ-024-022** Does a surround or multichannel mix downmix without losing center dialogue or overemphasizing effects?
   - Failure hypothesis: Unverified downmix rules alter the intended hierarchy.
   - Check or fix: Audition destination downmixes and correct channel assignment or levels.
   - Severity: high. Modes: machine, auditory. Stages: final-encode, delivery. Style filters: any.
23. **AVQ-024-023** Are accidental clicks introduced at edits, fades, or sample boundaries?
   - Failure hypothesis: Discontinuous waveforms create transient artifacts.
   - Check or fix: Listen to edit boundaries closely and repair fades or zero crossings.
   - Severity: medium. Modes: machine, auditory. Stages: edit, final-encode. Style filters: any.
24. **AVQ-024-024** Does hiss, hum, or electrical buzz emerge during sparse sections where it was previously masked?
   - Failure hypothesis: Background contamination becomes audible when the arrangement thins.
   - Check or fix: Listen to quiet full-mix passages and remove the specific contamination.
   - Severity: medium. Modes: auditory. Stages: edit, final-encode. Style filters: any.
25. **AVQ-024-025** Is an effect being used to imply a real mechanism the image does not demonstrate?
   - Failure hypothesis: Sound supplies false evidence of contact, locking, charging, or completion.
   - Check or fix: Listen with picture and verify the physical event behind each causal cue.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: educational.
26. **AVQ-024-026** Does an abrupt loud sound startle the audience beyond what the scene or audience context warrants?
   - Failure hypothesis: Unmotivated level contrast creates avoidable distress or discomfort.
   - Check or fix: Listen at ordinary volume and soften or prepare the cue where appropriate.
   - Severity: high. Modes: auditory, human-audience. Stages: animatic, edit. Style filters: any.
27. **AVQ-024-027** Is the soundtrack's loudness being judged on the final encode rather than solely on a premaster?
   - Failure hypothesis: Later encoding, normalization, or replacement changes the delivered balance.
   - Check or fix: Measure and listen to the exact delivered version.
   - Severity: high. Modes: machine, auditory. Stages: final-encode, delivery. Style filters: any.
28. **AVQ-024-028** Do effect layers occupy complementary spectral regions instead of multiplying the same muddy band?
   - Failure hypothesis: Layering increases density without adding perceptual detail.
   - Check or fix: Listen to isolated and combined layers and remove redundant material.
   - Severity: medium. Modes: auditory. Stages: production, edit. Style filters: any.
29. **AVQ-024-029** Are intentional periods of silence clean and shaped, rather than revealing sudden residual noise or truncated tails?
   - Failure hypothesis: Mute automation creates conspicuous technical gaps.
   - Check or fix: Listen through silence entries and exits and shape the transitions.
   - Severity: medium. Modes: auditory. Stages: edit, final-encode. Style filters: any.
30. **AVQ-024-030** Can listeners tell when a sound belongs to the scene versus a nonliteral editorial accent?
   - Failure hypothesis: Sound design confuses real-world events with commentary.
   - Check or fix: Listen with picture and establish a consistent sonic distinction.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: script, animatic, edit. Style filters: any.
31. **AVQ-024-031** Does the final audio contain unintended preview tags, spoken watermarks, or test tones?
   - Failure hypothesis: Temporary or uncleared production audio survives into delivery.
   - Check or fix: Listen end to end and reconcile every audible element to the final asset list.
   - Severity: high. Modes: machine, auditory. Stages: final-encode. Style filters: any.
32. **AVQ-024-032** Does normalizing a short clip hide a problematic internal jump between adjacent scenes?
   - Failure hypothesis: Whole-file loudness compliance masks local imbalance.
   - Check or fix: Listen across every scene boundary and adjust local balance.
   - Severity: high. Modes: machine, auditory, human-audience. Stages: edit, final-encode. Style filters: any.
