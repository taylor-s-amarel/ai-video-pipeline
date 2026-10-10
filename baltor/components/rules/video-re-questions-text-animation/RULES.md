# Video RE question bank: Text animation

Lens `text_animation` · 32 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-text-animation` subagent and challenged by `video-re-challenger`.

Measures how text enters, emphasises, idles and exits (pop scale, overshoot, duration, easing, stagger) frame by frame.

## Rules for every answer

1. Boundary: The swarm lifts technique and structure only. Never store, transcribe or reuse the source's footage, frames, music, voice or script text. Keyframes and spectrograms are temporary analysis files in a scratch directory and are never copied into the format IR or a variant. On-screen text may be quoted only as a locating note in evidence.note, at most 6 words, and narration is never quoted. Patterns replace content words with slots, e.g. 'FACT {n}' or '{number} {unit} {noun}'. Analysing a public video for technique is fine; republishing its content is not.
2. Do not identify, name or describe people (identity, age, gender, ethnicity, accent origin); describe size, position, pitch register and delivery only.
3. Never name the source's music track, artist, creator, channel or series in an answer.
4. Cite evidence for every answer: method, confidence, the timestamps you used, the tool or recipe for measured values, and a note with the numbers behind the answer (at most 400 characters).
5. Shape the answer by its answer type and write it to the question's ir_path exactly as given.
6. Say 'not determinable' instead of guessing. A missing measurement is null with an errors[] entry in evidence.json, never zero.
7. State observations, not taste: 'engaging' or 'cinematic' is not an answer; the measurement behind it is. Effects on viewers (retention, virality) are not observable from one video.
8. A claim about every item, shot or caption needs at least 3 checked instances (or all of them when there are fewer).

## Methods and confidence

- **measured**: A measurement tool produced the value (an evidence.json field or an ffmpeg/ffprobe filter output). Name the tool and the field.
- **observed**: You looked at extracted frames, crops, scopes, spectrograms or waveforms and saw it. Give the timestamps you looked at.
- **inferred**: Reasoned from measured or observed facts, e.g. 'synthetic voice' from flat pitch on a spectrogram. State the reasoning in the note.
- **assumed**: No direct evidence; a default or convention. Use only for gaps the format needs filled, and keep confidence at 0.3 or lower.

Confidence bands:
- 0.85-0.95: measured, the tool ran cleanly and the value is unambiguous (for example shot_stats.median_s).
- 0.65-0.85: measured but sensitive to tool settings, or observed consistently on 3 or more instances.
- 0.45-0.65: observed on 1-2 instances, or inferred from measured values with one reasoning step.
- 0.25-0.45: inferred with several steps or from weak cues.
- 0.0-0.3: assumed, or not determinable (answer the string 'not determinable').
- These bands are the swarm's calibration convention, not a statistical guarantee; challengers move answers between bands.

Not determinable: When the evidence cannot answer a question, return the answer string "not determinable" with method "assumed", confidence 0 and a note that names the missing evidence (for example 'audio.tempo_bpm is null: librosa unavailable'). Never guess to fill a slot.

## IR pointer conventions

- ir_path is a JSON Pointer (RFC 6901) into the Video format IR (contract schema video_re_format_ir).
- A final '/-' means 'append this answer to the array' (the RFC 6901 end-of-array token), e.g. /motion/transitions/- or /generation_rules/-.
- A '*' segment means 'each array element the answer is about'; the answer must say which elements (for example beats with role 'item'). The lifter resolves '*' to concrete indexes.
- Paths under free-form objects (typography.title, typography.captions, typography.labels, audio.narration, audio.music, render_binding.mapping) use the snake_case key named in the question.

## Answer types used here

- `number`: {"value": n, "unit": "..."} optionally with "min" and "max"; becomes an IR observed_number
- `integer`: {"value": n}
- `ratio`: {"value": r} with 0 <= r <= 1
- `ms`: {"value": n, "unit": "ms"} optionally with "min"/"max"; signed when an offset (negative = earlier)
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `list`: array of short strings (technique names or kinds)
- `segments`: [{"start_s": a, "end_s": b, "label": "..."}]
- `parameter`: one IR parameter object (name, type, description, default, min/max or choices, derived_from)
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- text_regions[] t_s and bbox changes
- audio.onsets_s for sound-synced pops
- source.fps

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_text_animation_type`, `video_re_detect_karaoke_highlight`, `video_re_detect_number_reveals`, `video_re_detect_easing_profile`, `video_re_detect_label_patterns`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F8 frame steps over every text entrance you measure; measure bbox height per frame on the stepped frames.

## Pitfalls challengers check first

- Measuring durations in frames without converting by the real fps
- Generalising one animation to all text
- Confusing a camera zoom with a text scale animation

## Parameters this lens usually proposes

- pop_scale_peak
- pop_ms
- entrance_kind (enum)
- stagger_ms
- easing (enum)

## IR paths this lens writes

- `/audio/sfx/-` (1)
- `/generation_rules/-` (6)
- `/motion/easing` (1)
- `/motion/text_animations/-` (22)
- `/parameters/-` (1)
- `/visual/style_family` (1)

## Questions (32)

### text_animation-001 · `enum` → `/motion/text_animations/-`

**How do captions enter (scale pop, fade, slide, typewriter, mask wipe, no animation)?**

- Choices: `scale-pop`, `fade`, `slide`, `typewriter`, `mask-wipe`, `none`, `mixed`
- Why it matters: Adds the caption entrance to motion.text_animations.
- How to answer: F8 frame steps over the first 0.3 s of 4 caption cards; look at size, opacity and position per frame.
- Evidence required: frames: F8 at 4 caption starts
- Challenge: Check at least 4 cards; one dramatic card is not the rule.

### text_animation-002 · `ms` → `/motion/text_animations/-`

**How long does a caption entrance take (ms from first visible frame to settled)?**

- Why it matters: Fills the entrance duration parameter.
- How to answer: Count frames on F8 steps from first visible to stable size/position; ms = frames x 1000 / fps.
- Evidence required: frames: F8; evidence.source.fps
- Challenge: Use the real fps from A7; report frames and ms.

### text_animation-003 · `number` → `/motion/text_animations/-`

**Does the entrance overshoot (scale above final size, then settle), and what is the peak scale?**

- Why it matters: Fills pop_scale_peak; springy overshoot was a liked reference trait in this project.
- How to answer: Measure text block height on each F8 frame; peak scale = max height / settled height.
- Evidence required: frames: F8
- Challenge: Report the height series; camera zoom during the same frames would contaminate it.

### text_animation-004 · `object` → `/motion/text_animations/-`

**How do captions exit (cut, fade, scale down, slide out), and how long does it take?**

- Why it matters: Fills the exit animation.
- How to answer: F8 steps over the last 0.3 s before 4 caption changes.
- Evidence required: frames: F8 at caption ends
- Challenge: If the next caption replaces the old one on the same frame, the exit is a cut.

### text_animation-005 · `ms` → `/motion/text_animations/-`

**When a key word pops, how many ms after (or before) the spoken word does the pop start?**

- Why it matters: Sets the keyword pop sync offset.
- How to answer: F8 at emphasised words versus the word onset on A1 spectrogram.
- Evidence required: frames: F8; A1
- Challenge: Report n and spread; the word onset must be read from audio, not caption timing.

### text_animation-006 · `object` → `/motion/text_animations/-`

**How does the title enter and how long does its entrance take?**

- Why it matters: Adds title entrance details.
- How to answer: F8 at the title's first appearance.
- Evidence required: frames: F8
- Challenge: Compare with hook_first_seconds-015; disagreements must be explained.

### text_animation-007 · `enum` → `/motion/text_animations/-`

**How do item labels (for example FACT N) enter (slam with scale-down, slide, flip, pop, fade)?**

- Choices: `slam`, `slide`, `flip`, `pop`, `fade`, `none`
- Why it matters: Adds label entrance.
- How to answer: F8 at 3 label appearances.
- Evidence required: frames: F8
- Challenge: Check all 3 match.

### text_animation-008 · `enum` → `/motion/text_animations/-`

**How are key numbers revealed (count-up, flip, scale pop, typewriter, static)?**

- Choices: `count-up`, `flip`, `scale-pop`, `typewriter`, `static`
- Why it matters: Adds a number reveal animation.
- How to answer: F8 over the number's first 0.6 s; a count-up shows intermediate values.
- Evidence required: frames: F8
- Challenge: Intermediate values must be visible on at least 2 frames for count-up.

### text_animation-009 · `ms` → `/motion/text_animations/-`

**Is there a stagger between words or lines entering, and how many ms apart?**

- Why it matters: Fills stagger_ms.
- How to answer: F8 steps across multi-word entrances; time between successive word appearances.
- Evidence required: frames: F8
- Challenge: Word-by-word captions timed to speech are not a stagger; a stagger is faster than speech.

### text_animation-010 · `enum` → `/motion/easing`

**What easing curve does the text motion follow (spring with overshoot, ease-out-back, ease-out, linear)?**

- Choices: `spring`, `ease-out-back`, `ease-out`, `ease-in-out`, `linear`
- Why it matters: Fills motion.easing for text.
- How to answer: Plot the scale or position series from F8 steps; overshoot then settle with oscillation = spring; single overshoot = ease-out-back.
- Evidence required: frames: F8 series
- Challenge: Report the series values; the curve name must match them.

### text_animation-011 · `object` → `/motion/text_animations/-`

**Does text move while it is on screen (idle float, breathing scale, wobble)?**

- Why it matters: Adds idle motion.
- How to answer: Compare text bbox across F1 frames 0.5 s apart within one card.
- Evidence required: frames: F1 within a card
- Challenge: A camera move that includes the text layer must be excluded; check if the background shifts the same way.

### text_animation-012 · `boolean` → `/motion/text_animations/-`

**Is motion blur or squash-and-stretch applied to moving text?**

- Why it matters: Adds stylistic deformation.
- How to answer: F8 frames mid-animation; look for smeared or non-uniformly scaled glyphs.
- Evidence required: frames: F8
- Challenge: Compression smear is not motion blur; it appears as blocks.

### text_animation-013 · `ratio` → `/generation_rules/-`

**What share of text entrances land within 80 ms of a music onset?**

- Why it matters: Becomes a beat-sync rule for text.
- How to answer: Compare entrance times (from F8 or text_regions) with evidence.audio.onsets_s.
- Evidence required: entrance times; evidence.audio.onsets_s
- Challenge: Compare with the chance rate given onset density.

### text_animation-014 · `ratio` → `/audio/sfx/-`

**Are text entrances accompanied by a sound effect (pop, click, whoosh)?**

- Why it matters: Couples text animation with sfx.
- How to answer: A1 spectrogram with highpass around 4 entrances.
- Evidence required: A1 highpassed
- Challenge: Speech consonants are transient; the sfx must not coincide with a word onset.

### text_animation-015 · `list` → `/motion/text_animations/-`

**Are there highlight sweeps, underlines being drawn, or boxes drawing around words?**

- Why it matters: Adds annotation animations.
- How to answer: F8 at emphasised moments.
- Evidence required: frames: F8
- Challenge: List timestamps for each.

### text_animation-016 · `boolean` → `/motion/text_animations/-`

**Are mask reveals used (text wiping in behind an edge)?**

- Why it matters: Adds a mask-reveal entrance.
- How to answer: F8 steps: partial letters cut by a straight edge.
- Evidence required: frames: F8
- Challenge: A slide from outside the frame is not a mask reveal.

### text_animation-017 · `number` → `/motion/text_animations/-`

**Is rotation used in text entrances, and by how many degrees?**

- Why it matters: Adds rotation range.
- How to answer: Measure baseline angle on F8 frames.
- Evidence required: frames: F8
- Challenge: Report the angle per frame.

### text_animation-018 · `ratio` → `/generation_rules/-`

**What share of text elements animate at all?**

- Why it matters: Tells the generator whether to animate everything or only key elements.
- How to answer: Classify 10 text appearances as animated or not.
- Evidence required: frames: F8 at 10 appearances
- Challenge: Report the sample.

### text_animation-019 · `ratio` → `/generation_rules/-`

**What fraction of a caption card's time is spent animating versus static and readable?**

- Why it matters: Becomes a readability constraint for animation length.
- How to answer: (entrance ms + exit ms) / card duration for 5 cards.
- Evidence required: entrance and exit durations; card durations
- Challenge: Use the same cards for all terms.

### text_animation-020 · `segments` → `/visual/style_family`

**Is the text itself the main visual (kinetic typography) for any section?**

- Why it matters: Adds a kinetic-type beat option.
- How to answer: Find shots where text covers more than 30% of the frame and moves in layout (F2).
- Evidence required: evidence.text_regions[].area_ratio; frames: F2
- Challenge: A large static title card is not kinetic typography.

### text_animation-021 · `boolean` → `/generation_rules/-`

**Is the same animation used for the same element type throughout (consistency)?**

- Why it matters: Becomes a consistency rule.
- How to answer: Compare entrance type per element role across 3 instances each.
- Evidence required: frames: F8
- Challenge: Report which instances were compared.

### text_animation-022 · `enum` → `/motion/text_animations/-`

**How does one caption card give way to the next (instant replace, cross-fade, push, exit then enter with a gap)?**

- Choices: `instant-replace`, `cross-fade`, `push`, `exit-then-enter`
- Why it matters: Fills caption-to-caption transition.
- How to answer: F8 across 4 caption changes.
- Evidence required: frames: F8
- Challenge: Check 4 changes.

### text_animation-023 · `integer` → `/motion/text_animations/-`

**How many frames does a typical text entrance take at the source frame rate?**

- Why it matters: Gives a frame-exact value for renderers working in frames.
- How to answer: Frame count from F8 steps; report fps.
- Evidence required: frames: F8; A7 r_frame_rate
- Challenge: Variable frame rate sources make frame counts unreliable; check A7 for avg vs real frame rate.

### text_animation-024 · `boolean` → `/motion/text_animations/-`

**Is there a shine or glint pass across the title or labels?**

- Why it matters: Adds a shine effect.
- How to answer: F8 on the title: a bright band moving across letters.
- Evidence required: frames: F8
- Challenge: A light-leak layer over everything is not a text shine.

### text_animation-025 · `object` → `/motion/text_animations/-`

**Is text shaken or vibrated for emphasis, and with what amplitude?**

- Why it matters: Adds a shake emphasis.
- How to answer: Track text bbox position across F8 frames.
- Evidence required: frames: F8
- Challenge: Report px amplitude.

### text_animation-026 · `parameter` → `/parameters/-`

**What should pop_scale_peak and pop_ms be as parameters, with ranges from the evidence?**

- Why it matters: Turns observed animation into parameters.
- How to answer: Default = observed medians (003, 002); range = observed min/max.
- Evidence required: text animation measurements
- Challenge: Ranges wider than observed must be marked assumed.

### text_animation-027 · `rule` → `/generation_rules/-`

**Write the caption animation rule (entrance, keyword pop, exit) in terms of parameters.**

- Why it matters: Gives the compiler a procedural animation.
- How to answer: Combine 001-005, for example 'enter: scale 0.85 to pop_scale_peak to 1.0 over pop_ms with ease-out-back; key word pops 1.0 to 1.12 to 1.0 over 180 ms at word onset; exit: cut'.
- Evidence required: text animation answers
- Challenge: Every number in the rule must come from a measurement or be marked as a default.

### text_animation-028 · `object` → `/generation_rules/-`

**Do text elements enter from a consistent direction or along a consistent axis?**

- Why it matters: Becomes a direction rule.
- How to answer: From F8 steps, note entrance direction for 6 elements.
- Evidence required: frames: F8
- Challenge: Report the counts per direction.

### text_animation-029 · `ms` → `/motion/text_animations/-`

**Does the backing panel animate separately from the text (panel first, text after), and with what offset?**

- Why it matters: Adds panel/text sequencing.
- How to answer: F8 steps at caption or title starts.
- Evidence required: frames: F8
- Challenge: Report frames and ms.

### text_animation-030 · `enum` → `/motion/text_animations/-`

**Is animation applied per character, per word, or per line?**

- Choices: `character`, `word`, `line`, `block`
- Why it matters: Fills animation granularity.
- How to answer: F8 steps: see which units move independently.
- Evidence required: frames: F8
- Challenge: Check one long caption.

### text_animation-031 · `ms` → `/motion/text_animations/-`

**Is there a gap or overlap between one caption leaving and the next appearing (ms)?**

- Why it matters: Fills the caption gap timing.
- How to answer: F8 across 4 changes: frames with no caption (gap) or two captions (overlap).
- Evidence required: frames: F8
- Challenge: Report the sign convention and n.

### text_animation-032 · `boolean` → `/motion/text_animations/-`

**Is there anticipation before a pop (a brief scale-down before the scale-up)?**

- Why it matters: Adds anticipation to the pop curve.
- How to answer: Height series from F8 just before emphasised words.
- Evidence required: frames: F8
- Challenge: Report the height series.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "text_animation-001", "ir_path": "/motion/text_animations/-", "answer_type": "enum", "choices": ["scale-pop", "fade", "slide", "typewriter", "mask-wipe", "none", "mixed"]}, {"id": "text_animation-002", "ir_path": "/motion/text_animations/-", "answer_type": "ms"}, {"id": "text_animation-003", "ir_path": "/motion/text_animations/-", "answer_type": "number"}, {"id": "text_animation-004", "ir_path": "/motion/text_animations/-", "answer_type": "object"}, {"id": "text_animation-005", "ir_path": "/motion/text_animations/-", "answer_type": "ms"}, {"id": "text_animation-006", "ir_path": "/motion/text_animations/-", "answer_type": "object"}, {"id": "text_animation-007", "ir_path": "/motion/text_animations/-", "answer_type": "enum", "choices": ["slam", "slide", "flip", "pop", "fade", "none"]}, {"id": "text_animation-008", "ir_path": "/motion/text_animations/-", "answer_type": "enum", "choices": ["count-up", "flip", "scale-pop", "typewriter", "static"]}, {"id": "text_animation-009", "ir_path": "/motion/text_animations/-", "answer_type": "ms"}, {"id": "text_animation-010", "ir_path": "/motion/easing", "answer_type": "enum", "choices": ["spring", "ease-out-back", "ease-out", "ease-in-out", "linear"]}, {"id": "text_animation-011", "ir_path": "/motion/text_animations/-", "answer_type": "object"}, {"id": "text_animation-012", "ir_path": "/motion/text_animations/-", "answer_type": "boolean"}, {"id": "text_animation-013", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "text_animation-014", "ir_path": "/audio/sfx/-", "answer_type": "ratio"}, {"id": "text_animation-015", "ir_path": "/motion/text_animations/-", "answer_type": "list"}, {"id": "text_animation-016", "ir_path": "/motion/text_animations/-", "answer_type": "boolean"}, {"id": "text_animation-017", "ir_path": "/motion/text_animations/-", "answer_type": "number"}, {"id": "text_animation-018", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "text_animation-019", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "text_animation-020", "ir_path": "/visual/style_family", "answer_type": "segments"}, {"id": "text_animation-021", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "text_animation-022", "ir_path": "/motion/text_animations/-", "answer_type": "enum", "choices": ["instant-replace", "cross-fade", "push", "exit-then-enter"]}, {"id": "text_animation-023", "ir_path": "/motion/text_animations/-", "answer_type": "integer"}, {"id": "text_animation-024", "ir_path": "/motion/text_animations/-", "answer_type": "boolean"}, {"id": "text_animation-025", "ir_path": "/motion/text_animations/-", "answer_type": "object"}, {"id": "text_animation-026", "ir_path": "/parameters/-", "answer_type": "parameter"}, {"id": "text_animation-027", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "text_animation-028", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "text_animation-029", "ir_path": "/motion/text_animations/-", "answer_type": "ms"}, {"id": "text_animation-030", "ir_path": "/motion/text_animations/-", "answer_type": "enum", "choices": ["character", "word", "line", "block"]}, {"id": "text_animation-031", "ir_path": "/motion/text_animations/-", "answer_type": "ms"}, {"id": "text_animation-032", "ir_path": "/motion/text_animations/-", "answer_type": "boolean"}]
```
