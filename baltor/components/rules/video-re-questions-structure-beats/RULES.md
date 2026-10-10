# Video RE question bank: Structure and beats

Lens `structure_beats` · 36 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-structure-beats` subagent and challenged by `video-re-challenger`.

Segments the video into beats (hook, setup, repeated items, payoff, outro), finds what repeats per item and what varies, and turns the timing into formulas so any number of items can be laid out.

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
- `seconds`: {"value": s, "unit": "s"} optionally with "min"/"max"
- `ms`: {"value": n, "unit": "ms"} optionally with "min"/"max"; signed when an offset (negative = earlier)
- `range`: {"value": typical, "min": a, "max": b, "unit": "..."}
- `distribution`: {"median": m, "p10": a, "p90": b, "n": count, "unit": "..."}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `text`: one technique description, at most 300 characters, no copied content
- `pattern`: a template with {slots} in place of content words, e.g. 'FACT {n}: {number} {unit}'
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `segments`: [{"start_s": a, "end_s": b, "label": "..."}]
- `beats`: array of IR beat objects (role, start_ratio, end_ratio, optional repeat, label_pattern, content_slot)
- `parameter`: one IR parameter object (name, type, description, default, min/max or choices, derived_from)
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[] (video_re_detect_shots)
- captions[] (video_re_caption_track or video_re_transcribe_adapter)
- audio.speech_segments (video_re_speech_segments)
- text_regions[] (video_re_text_regions)
- source.duration_s (video_re_probe_metadata)

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_beat_repetition`, `video_re_detect_intro_outro_bumpers`, `video_re_detect_cta_endcard`, `video_re_detect_label_patterns`, `video_re_classify_format_family`, `video_re_detect_silence_gaps`, `video_re_detect_loopability`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

Contact sheet (F4) for the whole video, then F1 frames at every candidate beat boundary and one burst (F2) inside each item beat.

## Pitfalls challengers check first

- Calling a run of shots a beat without a boundary cue (label, cut, music change, pause)
- Counting the hook or outro as an item
- Writing a timing formula that does not reproduce the observed beat times
- Generalising n_items limits from a single video without saying so

## Parameters this lens usually proposes

- n_items (integer, range justified by beat length limits)
- item_beat_s (derived)
- intro_s / outro_s
- item_order (enum)
- include_recap / include_cta (boolean)

## IR paths this lens writes

- `/generation_rules/-` (10)
- `/parameters/-` (4)
- `/script/beat_patterns/-` (9)
- `/timeline/beats` (7)
- `/timeline/beats/*/content_slot` (1)
- `/timeline/beats/*/end_ratio` (1)
- `/timeline/beats/*/label_pattern` (1)
- `/timeline/beats/*/shots_per_beat` (1)
- `/timeline/beats/*/start_ratio` (1)
- `/timeline/target_duration_s` (1)

## Questions (36)

### structure_beats-001 · `beats` → `/timeline/beats`

**What are the beat boundaries of the whole video (start and end seconds) and the role of each beat (hook, title, setup, item, payoff, recap, cta, outro)?**

- Why it matters: Fills timeline.beats, the skeleton every other lens hangs its answers on.
- How to answer: Start from evidence.shots[] boundaries and evidence.captions[] gaps; mark a boundary where at least two cues coincide (new label in evidence.text_regions, a cut, a speech pause over 300 ms in audio.speech_segments, a loudness change from A3). Confirm each boundary on F1 frames 0.2 s before and after. Express start/end as ratios of source.duration_s.
- Evidence required: evidence.shots[].start_s; evidence.audio.speech_segments; evidence.text_regions[].t_s; frames: F1 either side of each boundary
- Challenge: Pick two boundaries at random and check that at least two independent cues fall within 0.3 s of each; a boundary backed by one cue only must carry confidence below 0.5.

### structure_beats-002 · `parameter` → `/parameters/-`

**How many repeated item beats (facts, tips, steps, ranks) does the video contain?**

- Why it matters: Becomes the n_items parameter and the repeat count in the beat list.
- How to answer: Count beats from structure_beats-001 whose role is item/fact/tip/step. Cross-check against distinct label numbers seen in evidence.text_regions (F3 crops of the label area) and against the number of times the per-item sub-pattern restarts.
- Evidence required: timeline beats from structure_beats-001; frames: F3 crop of each label
- Challenge: Recount using only the label crops; if labels are absent, recount using the sub-pattern restarts. Disagreement between the two counts means the answer is inferred, not measured.

### structure_beats-003 · `distribution` → `/timeline/beats`

**How long is each item beat in seconds, and how uniform are they (median, min, max, coefficient of variation)?**

- Why it matters: Decides whether item length is a fixed formula or content-driven, and sets the item_beat_s range.
- How to answer: From the item beats in structure_beats-001 compute end_s - start_s for each; report median, min, max and stdev/mean. Use the shot boundaries from evidence.shots[] to snap beat edges to cuts when they are within 0.2 s.
- Evidence required: evidence.shots[].start_s; item beat boundaries
- Challenge: Recompute from the listed boundaries; check that the first and last items were not trimmed by the hook or outro. A CV above 0.35 contradicts any claim of fixed-length items.

### structure_beats-004 · `rule` → `/generation_rules/-`

**How many seconds of the runtime are NOT item beats (hook + intro + recap + outro), so that item length can be written as (duration - fixed) / n_items?**

- Why it matters: Gives the fixed overhead term in the item timing generation rule.
- How to answer: Sum durations of all non-item beats from structure_beats-001. Report the hook/intro part and the outro part separately in the note.
- Evidence required: timeline beats from structure_beats-001; evidence.source.duration_s
- Challenge: Plug the observed n_items and duration into the proposed rule; the predicted item length must be within 15% of the observed median item length, otherwise the rule is wrong.

### structure_beats-005 · `ratio` → `/timeline/beats/*/end_ratio`

**At what fraction of the runtime does the first item begin?**

- Why it matters: Sets the hook length as a ratio, which transfers to other target durations.
- How to answer: Take start_s of the first item beat divided by evidence.source.duration_s. Confirm with F1 frames that the first label or first item visual appears at that time.
- Evidence required: evidence.source.duration_s; frames: F1 at the first item start
- Challenge: Check whether a teaser or cold open before the title was mistaken for the first item.

### structure_beats-006 · `seconds` → `/timeline/beats`

**Is there a separate title beat (a held title card or title-over-photo moment) distinct from the spoken hook, and how long does it last?**

- Why it matters: Decides whether the format needs a title beat and its hold time.
- How to answer: Look for a text region with large area_ratio in evidence.text_regions during the first 5 s; measure from its first to last t_s. Inspect F1 frames at 0, 1, 2, 3 s.
- Evidence required: evidence.text_regions[] with t_s < 5; frames: F1 at 0-3 s
- Challenge: Confirm the text is a title and not the first caption: a title persists across at least one caption change or speech pause.

### structure_beats-007 · `enum` → `/script/beat_patterns/-`

**In what order are the items arranged (countdown, count-up, chronological, ascending magnitude, descending magnitude, best saved for last, no visible rule)?**

- Choices: `countdown`, `count-up`, `chronological`, `ascending-magnitude`, `descending-magnitude`, `best-last`, `no-visible-rule`
- Why it matters: Becomes the item_order parameter and a generation rule for sorting new content.
- How to answer: Read label numbers from F3 crops (count direction), dates or key numbers per item from on-screen text, and note which item gets the longest beat or a special treatment.
- Evidence required: frames: F3 crops of labels and key numbers per item
- Challenge: If the order is called 'ascending magnitude', list the magnitudes in order; a single inversion means 'no-visible-rule' or lower confidence.

### structure_beats-008 · `text` → `/script/beat_patterns/-`

**Is the final item structurally different from the others (longer beat, different transition, music change, extra effect)?**

- Why it matters: Tells the generator whether to give the last item special treatment.
- How to answer: Compare the last item beat's duration, number of shots (evidence.shots[]), transitions (F8 at its start) and momentary loudness (A3) with the median of the other items.
- Evidence required: evidence.shots[]; frames: F8 at item starts; A3 loudness
- Challenge: A difference below 20% in duration with no other change is noise, not a structural rule.

### structure_beats-009 · `boolean` → `/parameters/-`

**Is there a recap beat that revisits earlier items before the end?**

- Why it matters: Becomes an optional include_recap parameter.
- How to answer: Look in the last 20% of runtime for on-screen repetition of earlier labels or visuals (F10 SSIM against earlier keyframes above 0.7) or a fast montage of earlier shots.
- Evidence required: evidence.shots[].keyframe; frames: F10 comparisons
- Challenge: Check that matched frames are actually reused shots and not a shared background.

### structure_beats-010 · `seconds` → `/timeline/beats`

**How many seconds of the file come after the last meaningful content (end card, silence, black, logo)?**

- Why it matters: Sets the outro_s parameter and stops dead tails from being copied by accident.
- How to answer: Find the last speech segment end (audio.speech_segments) and the last text change; compare with source.duration_s. Use F12 for black frames and A4 for trailing silence.
- Evidence required: evidence.audio.speech_segments; evidence.source.duration_s; F12 black frames; A4 silences
- Challenge: Check that a silent visual payoff is not mistaken for a dead tail.

### structure_beats-011 · `range` → `/timeline/beats/*/shots_per_beat`

**How many shots does a typical item beat contain (median and range)?**

- Why it matters: Fills shots_per_beat and lets the renderer plan asset counts per item.
- How to answer: Count evidence.shots[] whose start_s falls inside each item beat; report median, min and max.
- Evidence required: evidence.shots[]; item beat boundaries
- Challenge: Spot-check one item with F11 scene scores for missed dissolves or false cuts that would change the count.

### structure_beats-012 · `pattern` → `/script/beat_patterns/-`

**What is the internal sub-structure of one item beat (for example label reveal, number reveal, explanation, visual proof, transition) with each step's offset from the beat start?**

- Why it matters: Becomes the per-item template the generator repeats.
- How to answer: For three different items, list events with offsets: label appearance (text_regions t_s), key-number appearance, first speech onset, cuts, last caption. Keep events that recur in all three with offsets within 0.3 s.
- Evidence required: evidence.text_regions[]; evidence.audio.speech_segments; evidence.shots[]; frames: F8 at each item start
- Challenge: Test the template on a fourth item not used to build it; any step missing there must be marked optional.

### structure_beats-013 · `object` → `/generation_rules/-`

**Which elements repeat identically in every item beat and which vary from item to item?**

- Why it matters: Separates fixed format elements from content slots; the core of parameterisation.
- How to answer: Compare F1 frames at the same offset in three items: layout, label position and style, transition, sound cue (A1 at item starts) versus image, number and caption content. Answer as {repeats: [...], varies: [...]}.
- Evidence required: frames: F1 at equal offsets in 3 items; A1 spectrogram at item starts
- Challenge: For each 'repeats' entry, find one item where it differs; if found, move it to 'varies' or mark it optional.

### structure_beats-014 · `pattern` → `/timeline/beats/*/label_pattern`

**What is the label pattern for item beats (for example 'FACT {n}', '#{n}', 'STEP {n} OF {total}') and does the number count up or down?**

- Why it matters: Fills label_pattern for repeated beats.
- How to answer: Crop the label region (F3, enlarged) at each item start and transcribe only the label form, replacing the number with {n}. Note where the label sits.
- Evidence required: frames: F3 crops of labels
- Challenge: Confirm the same form appears on every item; a label shown on only some items is optional, not the pattern.

### structure_beats-015 · `object` → `/generation_rules/-`

**Do beat boundaries coincide with a cut, a music change, a text change, a speech pause, or several of these at once?**

- Why it matters: Becomes a boundary-alignment rule the renderer follows.
- How to answer: For each boundary, list which of these fall within 0.25 s: cut (shots[]), onset or loudness step (audio.onsets_s, A3), text change (text_regions), pause (speech_segments gap). Report the share of boundaries for each cue.
- Evidence required: evidence.shots[]; evidence.audio.onsets_s; evidence.text_regions[]; evidence.audio.speech_segments
- Challenge: Recheck the tolerance: with cuts every 1-2 s, a 0.25 s window will often match by chance; report the chance rate (window x cuts per second) alongside.

### structure_beats-016 · `ratio` → `/timeline/beats/*/start_ratio`

**At what fraction of the runtime is the promise made in the hook paid off?**

- Why it matters: Places the payoff beat as a ratio for any target duration.
- How to answer: Identify the hook's promise type (what is withheld) from hook_first_seconds answers or captions, then find the beat where it is resolved. Divide its start_s by source.duration_s.
- Evidence required: timeline beats; captions timing (analysis only)
- Challenge: If the hook makes no explicit promise, the answer must be 'not determinable' rather than the last item.

### structure_beats-017 · `seconds` → `/timeline/beats`

**Are there transition beats or bumpers between items (a short stinger, a number card, a whoosh with no content) and how long are they?**

- Why it matters: Adds or removes a transition beat in the item loop.
- How to answer: Look for sub-1.5 s segments between items with no speech (speech_segments gap) and a distinctive graphic. Use F8 across each item boundary.
- Evidence required: evidence.audio.speech_segments; frames: F8 across item boundaries
- Challenge: Make sure the 'bumper' is not just the label-reveal step of the next item.

### structure_beats-018 · `seconds` → `/timeline/target_duration_s`

**What is the total duration in seconds, and which band does it fall in (under 30 s, 30-60 s, 60-90 s, 90-180 s, longer; band in the note)?**

- Why it matters: Sets target_duration_s and the default range for the duration parameter.
- How to answer: Read evidence.source.duration_s (video_re_probe_metadata). Subtract any dead tail from structure_beats-010 in the note.
- Evidence required: evidence.source.duration_s
- Challenge: Compare container duration with the last video frame time (A7 stream duration); a long audio tail can inflate it.

### structure_beats-019 · `number` → `/generation_rules/-`

**Do item beats get shorter, longer or stay level as the video goes on (slope of item length against item index)?**

- Why it matters: Becomes an escalation rule (for example each item 10% shorter) or confirms flat pacing.
- How to answer: Fit a line to item beat durations against item index; report the slope in seconds per item and the first-to-last ratio.
- Evidence required: item beat durations
- Challenge: With fewer than 5 items a slope is weak evidence; confidence must stay under 0.5.

### structure_beats-020 · `object` → `/script/beat_patterns/-`

**What share of each beat is covered by speech (talk density per beat role)?**

- Why it matters: Tells the script generator how much narration each beat role needs.
- How to answer: Intersect evidence.audio.speech_segments with each beat; report the median coverage for hook, item and outro beats.
- Evidence required: evidence.audio.speech_segments; timeline beats
- Challenge: Check speech segmentation on one beat with A4 silences; music-only passages are often detected as speech.

### structure_beats-021 · `segments` → `/timeline/beats`

**Where are the stretches longer than 1.5 s with no speech, and what structural role do they play (reveal, breathing room, transition, ending)?**

- Why it matters: Becomes planned silence slots in the timeline.
- How to answer: List gaps between evidence.audio.speech_segments over 1.5 s with timestamps; inspect F1 frames inside each to classify.
- Evidence required: evidence.audio.speech_segments; frames: F1 inside each gap
- Challenge: Confirm each gap with A4 silencedetect; a gap filled by a sound effect is still a 'no speech' slot but not silence.

### structure_beats-022 · `enum` → `/generation_rules/-`

**Does narration run across item boundaries (sentence started before the cut, L or J cut) or does each item start with a fresh sentence on the cut?**

- Choices: `fresh-sentence-on-cut`, `voice-leads-cut`, `picture-leads-voice`, `mixed`
- Why it matters: Becomes a boundary rule for the editor.
- How to answer: For each item boundary compare the cut time with the nearest speech segment start; voice-leads-cut when speech starts more than 150 ms before the cut, picture-leads when after.
- Evidence required: evidence.shots[]; evidence.audio.speech_segments
- Challenge: Speech-segment start times can be 100-200 ms late; recheck two boundaries on an A1 spectrogram.

### structure_beats-023 · `range` → `/parameters/-`

**What range of n_items can this structure support while keeping each item beat at least as long as the shortest observed item?**

- Why it matters: Justifies the min and max of the n_items parameter instead of copying the single observed value.
- How to answer: Using the fixed overhead (structure_beats-004) and the shortest and longest observed item beats: max_items = floor((duration - fixed) / shortest_item_s), min_items = ceil((duration - fixed) / longest_item_s). Report both for the source duration and note they scale with target duration.
- Evidence required: item beat durations; fixed overhead
- Challenge: Check the arithmetic and that the range is described as derived (inferred), not observed.

### structure_beats-024 · `list` → `/parameters/-`

**Which beats could be removed without breaking the format (optional beats)?**

- Why it matters: Becomes boolean include_* parameters.
- How to answer: A beat is optional when nothing later refers to it: no callback in captions, no visual reuse (F10), and the structure still has hook, items and ending without it.
- Evidence required: timeline beats; frames: F10 comparisons
- Challenge: Mark any beat that carries the payoff or the hook as required regardless of length.

### structure_beats-025 · `enum` → `/script/beat_patterns/-`

**Which known structural archetype fits best (listicle, countdown, story arc, problem-solution, before-after, myth-vs-fact, tutorial steps, comparison, timeline-history)?**

- Choices: `listicle`, `countdown`, `story-arc`, `problem-solution`, `before-after`, `myth-vs-fact`, `tutorial-steps`, `comparison`, `timeline-history`, `other`
- Why it matters: Names the format family so the library can group lifted formats.
- How to answer: Decide from the beat roles and label pattern: numbered repeated items suggest listicle or countdown; a single protagonist with escalation suggests story-arc; paired states suggest before-after.
- Evidence required: timeline beats; label pattern
- Challenge: Ask whether a second archetype fits as well; if so confidence must be below 0.6 and the note must name the alternative.

### structure_beats-026 · `ms` → `/generation_rules/-`

**How many seconds pass between the start of an item beat and the appearance of its label (label lead-in)?**

- Why it matters: Becomes a per-item timing constant in the generation rules.
- How to answer: For each item, subtract the beat start_s from the first evidence.text_regions[].t_s in the label area; confirm with F8 frame steps on two items.
- Evidence required: evidence.text_regions[]; frames: F8 at item starts
- Challenge: text_regions sampling interval limits precision; the answer's precision must not be finer than that interval unless F8 was used.

### structure_beats-027 · `timestamps` → `/script/beat_patterns/-`

**Are any beats built as a side-by-side or before/after comparison (two panels, split screen, A then B)?**

- Why it matters: Adds a comparison beat type to the format.
- How to answer: Look for frames with two similar-size visual regions (F1) or paired consecutive shots with mirrored text; list timestamps.
- Evidence required: frames: F1 at suspected comparisons
- Challenge: A 2x2 decorative grid is a background layer, not a comparison beat.

### structure_beats-028 · `range` → `/generation_rules/-`

**Is there a regular interval at which something drastically different happens (layout change, colour flash, new scene type), and what is that interval?**

- Why it matters: Becomes a pattern-interrupt rule (for example 'change scene type every 8-12 s').
- How to answer: From the contact sheet (F4) mark layout changes; compute intervals between them; report median and range.
- Evidence required: frames: F4 contact sheet; evidence.shots[].palette
- Challenge: Check the interval is not just the item beat length restated.

### structure_beats-029 · `object` → `/script/beat_patterns/-`

**What is the ratio of the longest to the shortest item beat, and where in the order is the longest one?**

- Why it matters: Shows whether one item is privileged (usually the payoff) and bounds per-item flexibility.
- How to answer: From item durations compute max/min and give the index of the longest.
- Evidence required: item beat durations
- Challenge: Make sure the longest item does not absorb an outro or CTA that should be its own beat.

### structure_beats-030 · `pattern` → `/script/beat_patterns/-`

**How many distinct scene layouts appear (for example full-bleed photo, photo plus label, grid, text-only card) and in what sequence do they occur?**

- Why it matters: Becomes the layout cycle the renderer follows (A B A B or A B C).
- How to answer: Classify each shot keyframe (F4 sheet or evidence.shots[].keyframe) by layout; write the sequence with letters and report the repeating unit.
- Evidence required: evidence.shots[].keyframe; frames: F4
- Challenge: Ask a second classification pass on 5 random shots; layout labels that flip were not distinct.

### structure_beats-031 · `enum` → `/timeline/beats`

**How does the video end: hard cut at the last word, fade to black, end card, loop back to the opening frame, or logo sting?**

- Choices: `hard-cut`, `fade-to-black`, `end-card`, `loop-to-start`, `logo-sting`, `other`
- Why it matters: Fills the outro beat role and its default length.
- How to answer: Inspect F8 frames over the last 1 s and F12 black frames; compare the last frame to the first with F10 for loop endings.
- Evidence required: frames: F8 last 1 s; F12; F10 first vs last frame
- Challenge: A fade that starts in the last 3 frames may be an encoder artefact; require at least 6 frames of fade.

### structure_beats-032 · `object` → `/timeline/beats/*/content_slot`

**What does an author have to supply for each item (for example one hero image, one key number, one 12-20 word line, one source URL)?**

- Why it matters: Defines the content_slot schema of the repeated beat.
- How to answer: From structure_beats-012 and -013 list the varying elements per item with their observed size limits (words per caption, number of images per item from shots).
- Evidence required: per-item template; repeats/varies split
- Challenge: Each slot must be backed by an element that varied in at least two items; slots that never vary are fixed elements.

### structure_beats-033 · `ratio` → `/generation_rules/-`

**Do beat boundaries fall on musical phrase boundaries (multiples of 4 or 8 beats at the detected tempo)?**

- Why it matters: Becomes a rule to snap beat lengths to musical phrases.
- How to answer: Using evidence.audio.tempo_bpm, compute beat period; for each beat boundary compute the offset from the nearest 4-beat grid line. Report the share within 1/8 of a beat.
- Evidence required: evidence.audio.tempo_bpm; evidence.audio.onsets_s; timeline beats
- Challenge: If tempo_bpm is null or the music is beatless, the answer is 'not determinable'; also compare against the chance rate for that tolerance.

### structure_beats-034 · `integer` → `/script/beat_patterns/-`

**Does each item contain exactly one claim or idea, or several?**

- Why it matters: Sets the per-item content budget the script writer follows.
- How to answer: Count distinct sentences or caption cards per item (captions[], analysis only) and how many carry a separate number or fact; report median per item without copying any text.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Check two items manually; restatements of the same idea count as one claim.

### structure_beats-035 · `rule` → `/generation_rules/-`

**Write the timing generation rule for the whole timeline in terms of parameters (target_duration_s, n_items, intro_s, outro_s).**

- Why it matters: Gives the compiler a procedural timeline instead of fixed timestamps.
- How to answer: Combine structure_beats-004, -005, -010 and -026, for example 'intro_s = 0.12 x duration; outro_s = 3; item_s = (duration - intro_s - outro_s) / n_items; label at item_start + 0.2 s'. Recompute the observed beat times from the rule and report the largest error.
- Evidence required: all structure answers
- Challenge: Re-derive every observed beat start from the rule; an error above 1 s on any beat means the rule needs another term.

### structure_beats-036 · `seconds` → `/generation_rules/-`

**What is the shortest beat of any kind, and does it look deliberate (stinger, flash) or accidental (trim)?**

- Why it matters: Sets a lower bound for beat length in the compiler.
- How to answer: Find the minimum duration in the beat list; inspect it with F8 and note any sound cue (A1).
- Evidence required: timeline beats; frames: F8; A1
- Challenge: If the shortest beat sits at the start or end of the file, check it against encoder padding.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F4** Whole-video contact sheet, 1 frame per second: ffmpeg -v error -i "$SRC" -vf "fps=1,scale=180:-2,tile=8x8" -frames:v 1 "$WORK/sheet.jpg" (or use the keyframes and contact sheet from video_re_keyframes_contact_sheet)
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F10** Similarity of two frames (SSIM, 1.0 = identical): ffmpeg -i a.jpg -i b.jpg -lavfi "[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*"
- **F11** Per-frame scene-change score (finds dissolves and missed cuts): ffmpeg -v error -i "$SRC" -vf "select='gte(scene,0)',metadata=mode=print:key=lavfi.scene_score:file=$WORK/scene.txt" -an -f null -
- **F12** Black frames: ffmpeg -i "$SRC" -vf "blackdetect=d=0.05:pix_th=0.10" -an -f null - 2>&1 | grep black_
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"
- **A3** Momentary loudness every 100 ms (LUFS): ffmpeg -v error -i "$SRC" -af "ebur128=metadata=1,ametadata=mode=print:key=lavfi.r128.M:file=$WORK/lufs_m.txt" -f null -
- **A4** Silences: ffmpeg -i "$SRC" -af "silencedetect=noise=-35dB:d=0.25" -f null - 2>&1 | grep silence_
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "structure_beats-001", "ir_path": "/timeline/beats", "answer_type": "beats"}, {"id": "structure_beats-002", "ir_path": "/parameters/-", "answer_type": "parameter"}, {"id": "structure_beats-003", "ir_path": "/timeline/beats", "answer_type": "distribution"}, {"id": "structure_beats-004", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "structure_beats-005", "ir_path": "/timeline/beats/*/end_ratio", "answer_type": "ratio"}, {"id": "structure_beats-006", "ir_path": "/timeline/beats", "answer_type": "seconds"}, {"id": "structure_beats-007", "ir_path": "/script/beat_patterns/-", "answer_type": "enum", "choices": ["countdown", "count-up", "chronological", "ascending-magnitude", "descending-magnitude", "best-last", "no-visible-rule"]}, {"id": "structure_beats-008", "ir_path": "/script/beat_patterns/-", "answer_type": "text"}, {"id": "structure_beats-009", "ir_path": "/parameters/-", "answer_type": "boolean"}, {"id": "structure_beats-010", "ir_path": "/timeline/beats", "answer_type": "seconds"}, {"id": "structure_beats-011", "ir_path": "/timeline/beats/*/shots_per_beat", "answer_type": "range"}, {"id": "structure_beats-012", "ir_path": "/script/beat_patterns/-", "answer_type": "pattern"}, {"id": "structure_beats-013", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "structure_beats-014", "ir_path": "/timeline/beats/*/label_pattern", "answer_type": "pattern"}, {"id": "structure_beats-015", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "structure_beats-016", "ir_path": "/timeline/beats/*/start_ratio", "answer_type": "ratio"}, {"id": "structure_beats-017", "ir_path": "/timeline/beats", "answer_type": "seconds"}, {"id": "structure_beats-018", "ir_path": "/timeline/target_duration_s", "answer_type": "seconds"}, {"id": "structure_beats-019", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "structure_beats-020", "ir_path": "/script/beat_patterns/-", "answer_type": "object"}, {"id": "structure_beats-021", "ir_path": "/timeline/beats", "answer_type": "segments"}, {"id": "structure_beats-022", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["fresh-sentence-on-cut", "voice-leads-cut", "picture-leads-voice", "mixed"]}, {"id": "structure_beats-023", "ir_path": "/parameters/-", "answer_type": "range"}, {"id": "structure_beats-024", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "structure_beats-025", "ir_path": "/script/beat_patterns/-", "answer_type": "enum", "choices": ["listicle", "countdown", "story-arc", "problem-solution", "before-after", "myth-vs-fact", "tutorial-steps", "comparison", "timeline-history", "other"]}, {"id": "structure_beats-026", "ir_path": "/generation_rules/-", "answer_type": "ms"}, {"id": "structure_beats-027", "ir_path": "/script/beat_patterns/-", "answer_type": "timestamps"}, {"id": "structure_beats-028", "ir_path": "/generation_rules/-", "answer_type": "range"}, {"id": "structure_beats-029", "ir_path": "/script/beat_patterns/-", "answer_type": "object"}, {"id": "structure_beats-030", "ir_path": "/script/beat_patterns/-", "answer_type": "pattern"}, {"id": "structure_beats-031", "ir_path": "/timeline/beats", "answer_type": "enum", "choices": ["hard-cut", "fade-to-black", "end-card", "loop-to-start", "logo-sting", "other"]}, {"id": "structure_beats-032", "ir_path": "/timeline/beats/*/content_slot", "answer_type": "object"}, {"id": "structure_beats-033", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "structure_beats-034", "ir_path": "/script/beat_patterns/-", "answer_type": "integer"}, {"id": "structure_beats-035", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "structure_beats-036", "ir_path": "/generation_rules/-", "answer_type": "seconds"}]
```
