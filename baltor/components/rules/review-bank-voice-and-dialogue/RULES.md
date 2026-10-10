# Adversarial review bank: D023 voice and dialogue (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D023 voice and dialogue". The questions below are the
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

- Severity: 18 high, 14 medium.
- Modes: 2 visual, 32 auditory, 1 machine, 23 human-audience.
- Need listening: 32 (`AVQ-023-001`, `AVQ-023-002`, `AVQ-023-003`, `AVQ-023-004`, `AVQ-023-005`, `AVQ-023-006`, `AVQ-023-007`, `AVQ-023-008`, `AVQ-023-009`, `AVQ-023-010`, `AVQ-023-011`, `AVQ-023-012`, `AVQ-023-013`, `AVQ-023-014`, `AVQ-023-015`, `AVQ-023-016`, `AVQ-023-017`, `AVQ-023-019`, `AVQ-023-020`, `AVQ-023-021`, `AVQ-023-022`, `AVQ-023-023`, `AVQ-023-024`, `AVQ-023-025`, `AVQ-023-026`, `AVQ-023-027`, `AVQ-023-028`, `AVQ-023-029`, `AVQ-023-031` are listening-only).
- Need a human audience: 23.
- Only answerable at final encode or delivery: `AVQ-023-032`.
- Limited by style filter: `AVQ-023-002` (educational), `AVQ-023-004` (educational), `AVQ-023-007` (educational), `AVQ-023-008` (fiction), `AVQ-023-009` (fiction), `AVQ-023-010` (fiction), `AVQ-023-016` (fiction), `AVQ-023-017` (fiction), `AVQ-023-018` (fiction), `AVQ-023-019` (educational), `AVQ-023-020` (educational), `AVQ-023-022` (fiction), `AVQ-023-023` (educational, live-action), `AVQ-023-024` (live-action), `AVQ-023-028` (fiction), `AVQ-023-029` (live-action, fiction), `AVQ-023-030` (fiction), `AVQ-023-031` (educational).

## Named passes that draw on this area

- `default_32`: `AVQ-023-001`
- `sound`: `AVQ-023-001`, `AVQ-023-002`, `AVQ-023-003`, `AVQ-023-004`, `AVQ-023-005`, `AVQ-023-006`, `AVQ-023-007`, `AVQ-023-008`, `AVQ-023-009`, `AVQ-023-010`, `AVQ-023-011`, `AVQ-023-012`, `AVQ-023-013`, `AVQ-023-014`, `AVQ-023-015`, `AVQ-023-016`
- `longer_cardboard_32`: `AVQ-023-001`

## Questions

1. **AVQ-023-001** Can an unbriefed listener transcribe the sentence containing the film's main claim correctly?
   - Failure hypothesis: Familiarity with the script masks unclear speech.
   - Check or fix: Play the final voice track to new listeners and compare their transcriptions.
   - Severity: high. Modes: auditory, human-audience. Stages: production, edit, final-encode. Style filters: any. Passes: default_32, sound, longer_cardboard_32.
2. **AVQ-023-002** Is vocal stress placed on the word that carries the intended contrast?
   - Failure hypothesis: Incorrect emphasis changes which alternative the sentence rejects.
   - Check or fix: Listen without reading the script and reperform ambiguous stress.
   - Severity: high. Modes: auditory, human-audience. Stages: script, production, edit. Style filters: educational. Passes: sound.
3. **AVQ-023-003** Are proper names and specialist terms pronounced accurately for the subject and audience?
   - Failure hypothesis: Synthetic or unfamiliar pronunciation undermines meaning and credibility.
   - Check or fix: Listen with a knowledgeable speaker and correct the specific pronunciation.
   - Severity: high. Modes: auditory, human-audience. Stages: script, production, edit. Style filters: any. Passes: sound.
4. **AVQ-023-004** Do numbers, ranges, and units remain distinguishable when spoken at the final pace?
   - Failure hypothesis: Similar-sounding quantities merge into an ambiguous instruction.
   - Check or fix: Have listeners write down the quantities and re-record errors.
   - Severity: high. Modes: auditory, human-audience. Stages: production, edit, final-encode. Style filters: educational. Passes: sound.
5. **AVQ-023-005** Does the narration sound as though it understands the sentence rather than reading punctuation mechanically?
   - Failure hypothesis: Prosodic breaks interrupt the sentence's logical structure.
   - Check or fix: Listen phrase by phrase and revise punctuation or performance.
   - Severity: medium. Modes: auditory, human-audience. Stages: production, edit. Style filters: any. Passes: sound.
6. **AVQ-023-006** Are breath pauses placed where a human speaker could plausibly breathe without splitting essential phrases?
   - Failure hypothesis: Generated or edited speech has unnatural respiration and phrasing.
   - Check or fix: Listen through full sentences and restore plausible breath placement.
   - Severity: medium. Modes: auditory. Stages: production, edit. Style filters: any. Passes: sound.
7. **AVQ-023-007** Does the narrator's emotional intensity fit the evidence rather than oversell an ordinary result?
   - Failure hypothesis: Excited delivery implies certainty or significance not supported by the film.
   - Check or fix: Listen blind to the claim and moderate unsupported enthusiasm.
   - Severity: high. Modes: auditory, human-audience. Stages: script, production, edit. Style filters: educational. Passes: sound.
8. **AVQ-023-008** Can the audience distinguish recurring speakers without needing to look at the screen continuously?
   - Failure hypothesis: Similar voices make the conversation hard to follow.
   - Check or fix: Listen audio-only and differentiate delivery or add clear attribution.
   - Severity: high. Modes: auditory, human-audience. Stages: production, edit. Style filters: fiction. Passes: sound.
9. **AVQ-023-009** Is the same character's voice consistent across separately generated or recorded lines?
   - Failure hypothesis: Timbre, accent, or age changes imply a different speaker.
   - Check or fix: Audition adjacent and distant lines together and replace inconsistent takes.
   - Severity: high. Modes: auditory. Stages: production, edit. Style filters: fiction. Passes: sound.
10. **AVQ-023-010** Does a change from narration to character speech sound intentional?
   - Failure hypothesis: One delivery style blurs narrator and story-world dialogue.
   - Check or fix: Listen to entrances and establish a distinct, consistent performance convention.
   - Severity: medium. Modes: auditory, human-audience. Stages: script, production, edit. Style filters: fiction. Passes: sound.
11. **AVQ-023-011** Are plosive bursts obscuring the beginnings of important words?
   - Failure hypothesis: Low-frequency microphone blasts mask consonants and distract.
   - Check or fix: Listen on full-range playback and repair or rerecord affected words.
   - Severity: medium. Modes: auditory. Stages: production, edit, final-encode. Style filters: any. Passes: sound.
12. **AVQ-023-012** Does sibilance become piercing on actual listening even when meters show no clipping?
   - Failure hypothesis: High-frequency consonant energy causes discomfort.
   - Check or fix: Audition on representative headphones and apply selective de-essing.
   - Severity: medium. Modes: auditory. Stages: production, edit, final-encode. Style filters: any. Passes: sound.
13. **AVQ-023-013** Are mouth clicks or lip noises exposed in quiet passages enough to distract from the message?
   - Failure hypothesis: Close-miked artifacts dominate a sparse soundtrack.
   - Check or fix: Listen to quiet intervals and remove artifacts without damaging speech.
   - Severity: medium. Modes: auditory. Stages: production, edit. Style filters: any. Passes: sound.
14. **AVQ-023-014** Does noise reduction distort consonant edges or leave watery modulation around the voice?
   - Failure hypothesis: Aggressive cleanup trades background noise for speech artifacts.
   - Check or fix: Listen to original and processed takes and reduce processing where needed.
   - Severity: high. Modes: auditory. Stages: production, edit. Style filters: any. Passes: sound.
15. **AVQ-023-015** Do edits between takes change room tone, vocal distance, or vocal effort within one sentence?
   - Failure hypothesis: Spliced speech sounds physically discontinuous.
   - Check or fix: Listen across every splice and choose compatible takes or natural boundaries.
   - Severity: medium. Modes: auditory. Stages: production, edit. Style filters: any. Passes: sound.
16. **AVQ-023-016** Is a whispered or subdued line still understandable at the intended playback level?
   - Failure hypothesis: Acting choice removes words essential to the plot.
   - Check or fix: Listen at ordinary volume and improve delivery or mix without changing intent.
   - Severity: high. Modes: auditory, human-audience. Stages: edit, final-encode. Style filters: fiction. Passes: sound.
17. **AVQ-023-017** Does dialogue overlap communicate a motivated interruption rather than accidental timing congestion?
   - Failure hypothesis: Simultaneous lines obscure both intention and content.
   - Check or fix: Listen with the scene and stagger or clarify the competing turns.
   - Severity: medium. Modes: auditory, human-audience. Stages: animatic, edit. Style filters: fiction.
18. **AVQ-023-018** Do the character's words and vocal emotion agree with the visible reaction at that moment?
   - Failure hypothesis: Performance communicates an emotion the image does not support.
   - Check or fix: Listen with picture and reconcile the take with the reaction.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: production, edit. Style filters: fiction.
19. **AVQ-023-019** Can listeners hear a meaning-changing negation clearly when it falls between louder words?
   - Failure hypothesis: Reduced articulation makes 'not' or equivalent disappear.
   - Check or fix: Audition the exact phrase with new listeners and strengthen the negation.
   - Severity: high. Modes: auditory, human-audience. Stages: production, edit, final-encode. Style filters: educational.
20. **AVQ-023-020** Are acronyms expanded, spoken, or spelled consistently with how the intended audience recognizes them?
   - Failure hypothesis: The voice invents an unfamiliar reading of a technical abbreviation.
   - Check or fix: Listen with domain users and standardize the acronym treatment.
   - Severity: medium. Modes: auditory, human-audience. Stages: script, production, edit. Style filters: educational.
21. **AVQ-023-021** Does switching languages preserve a credible pronunciation and speaking rhythm in each language?
   - Failure hypothesis: Multilingual delivery distorts one language while sounding fluent in another.
   - Check or fix: Obtain fluent listening review for every language segment.
   - Severity: high. Modes: auditory, human-audience. Stages: production, edit. Style filters: any.
22. **AVQ-023-022** Is an accent being performed intelligibly without caricature or arbitrary inconsistency?
   - Failure hypothesis: Exaggerated accent cues distract or stereotype the character.
   - Check or fix: Listen with informed speakers and revise unsupported performance choices.
   - Severity: high. Modes: auditory, human-audience. Stages: script, production, edit. Style filters: fiction.
23. **AVQ-023-023** Do pauses around a quote make its beginning and end audible without visual punctuation?
   - Failure hypothesis: Listeners misattribute quoted words to the narrator.
   - Check or fix: Listen audio-only and add natural attribution or clear vocal framing.
   - Severity: high. Modes: auditory, human-audience. Stages: script, production, edit. Style filters: educational, live-action.
24. **AVQ-023-024** Does removing filler words accidentally make a hesitant or uncertain speaker sound more confident than they were?
   - Failure hypothesis: Cleanup changes the meaning of an authentic statement.
   - Check or fix: Listen to source and edited context and preserve consequential hesitation.
   - Severity: high. Modes: auditory, human-audience. Stages: edit. Style filters: live-action.
25. **AVQ-023-025** Is speech sped up enough to sound strained or erase the narrator's natural cadence?
   - Failure hypothesis: Duration fitting sacrifices intelligibility and believable delivery.
   - Check or fix: Listen at final speed and shorten the script instead of overcompressing speech.
   - Severity: high. Modes: auditory, human-audience. Stages: edit, final-encode. Style filters: any.
26. **AVQ-023-026** Does the narrator address the intended audience with an appropriate level of familiarity and authority?
   - Failure hypothesis: Delivery assumes expertise, age, or intimacy the audience does not share.
   - Check or fix: Listen with representative viewers and adjust register rather than only vocabulary.
   - Severity: medium. Modes: auditory, human-audience. Stages: script, animatic, edit. Style filters: any.
27. **AVQ-023-027** Are sentence endings audible rather than trailing below the noise floor or music bed?
   - Failure hypothesis: Important qualifiers are lost in fading vocal energy.
   - Check or fix: Listen to endings in the full mix and repair delivery or automation.
   - Severity: high. Modes: auditory, human-audience. Stages: edit, final-encode. Style filters: any.
28. **AVQ-023-028** Does the dialogue give each character a distinct objective instead of making every line explain the plot?
   - Failure hypothesis: Exposition replaces interaction and weakens performance.
   - Check or fix: Read aloud and listen for lines no character would need to say.
   - Severity: medium. Modes: auditory, human-audience. Stages: script, storyboard, animatic. Style filters: fiction.
29. **AVQ-023-029** Does the voice's apparent microphone perspective remain compatible with a supposedly continuous scene?
   - Failure hypothesis: Dry close speech abruptly becomes distant without a scene change.
   - Check or fix: Listen consecutively and align recording or processing perspective.
   - Severity: medium. Modes: auditory. Stages: production, edit. Style filters: live-action, fiction.
30. **AVQ-023-030** Are generated breaths, laughs, or emotional interjections convincing in their immediate context?
   - Failure hypothesis: Synthetic nonverbal sounds break character believability.
   - Check or fix: Listen with picture and replace or remove implausible interjections.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: production, edit. Style filters: fiction.
31. **AVQ-023-031** Does a long narration segment develop vocal energy naturally instead of resetting to the same opening cadence each sentence?
   - Failure hypothesis: Sentence-by-sentence generation produces a repetitive presentation pattern.
   - Check or fix: Listen to the complete paragraph and reperform it as a coherent thought.
   - Severity: medium. Modes: auditory, human-audience. Stages: production, edit. Style filters: educational.
32. **AVQ-023-032** Is there any spoken instruction or claim in the delivered voice that is absent from the approved script?
   - Failure hypothesis: Ad-libs or generation artifacts introduce unreviewed content.
   - Check or fix: Listen end to end while reconciling the delivered transcript to the script.
   - Severity: high. Modes: machine, auditory. Stages: final-encode. Style filters: any.
