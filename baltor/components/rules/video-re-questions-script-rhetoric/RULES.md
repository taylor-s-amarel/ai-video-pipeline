# Video RE question bank: Script and rhetoric

Lens `script_rhetoric` · 35 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-script-rhetoric` subagent and challenged by `video-re-challenger`.

Lifts the writing technique (point of view, sentence shape, per-item templates, specificity, rhetorical devices) without keeping any of the source's words.

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
- `distribution`: {"median": m, "p10": a, "p90": b, "n": count, "unit": "..."}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `text`: one technique description, at most 300 characters, no copied content
- `pattern`: a template with {slots} in place of content words, e.g. 'FACT {n}: {number} {unit}'
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- captions[] text and timing (caption track or transcription adapter; analysis only, never copied)
- audio.speech_segments
- audio.speech_wpm (video_re_speech_rate)

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_label_patterns`, `video_re_detect_number_reveals`, `video_re_detect_silence_gaps`, `video_re_detect_voice_pitch_pace`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

Read the caption text in a scratch file only; count and classify, then delete. Use F1 frames to see on-screen wording roles.

## Pitfalls challengers check first

- Copying sentences or distinctive phrases into answers
- Classifying tone from one sentence
- Counting numbers in captions that came from OCR noise
- Computing reading level on fewer than 100 words without lowering confidence

## Parameters this lens usually proposes

- tone (enum)
- words_per_item (range)
- point_of_view (enum)
- numbers_per_item (integer)
- sources_required (boolean)

## IR paths this lens writes

- `/audio/narration/audience_address` (1)
- `/audio/narration/hedges_per_min` (1)
- `/audio/narration/intensifiers_per_min` (1)
- `/audio/narration/point_of_view` (1)
- `/audio/narration/register` (1)
- `/audio/narration/specificity_ratio` (1)
- `/audio/narration/vocabulary_complexity` (1)
- `/audio/narration/word_count` (1)
- `/audio/narration/words_per_sentence` (1)
- `/generation_rules/-` (3)
- `/parameters/-` (2)
- `/script/beat_patterns/-` (17)
- `/script/claims_need_sources` (1)
- `/script/reading_level` (1)
- `/timeline/beats` (1)
- `/typography/captions/relation_to_voice` (1)

## Questions (35)

### script_rhetoric-001 · `number` → `/script/reading_level`

**What is the approximate reading grade of the narration (Flesch-Kincaid grade computed on the caption text)?**

- Why it matters: Fills script.reading_level so new scripts can be written at the same level.
- How to answer: Concatenate evidence.captions[].text in a scratch file (never into answers); compute FK grade = 0.39 x words/sentences + 11.8 x syllables/words - 15.59 with a simple vowel-group syllable count; delete the scratch file. Report word count in the note.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Auto captions often lack punctuation, which inflates words per sentence; check sentence counting and lower confidence when punctuation is missing.

### script_rhetoric-002 · `distribution` → `/audio/narration/words_per_sentence`

**What is the median number of words per sentence (or per caption-delimited phrase when punctuation is missing)?**

- Why it matters: Sets a sentence length budget for the script writer.
- How to answer: Split the caption text on sentence punctuation (or on caption card boundaries); report median and p90.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: State which split was used; card-based splits measure caption chunking, not sentences.

### script_rhetoric-003 · `enum` → `/audio/narration/point_of_view`

**Which point of view dominates the narration: first person, second person ('you'), third person, or mixed?**

- Choices: `first-person`, `second-person`, `third-person`, `mixed`
- Why it matters: Becomes the point_of_view parameter.
- How to answer: Count pronoun families (I/we, you/your, he/she/they/it) per 100 words in the caption text; report the dominant family and its share.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: 'You' in a quoted phrase or generic 'you' in third-person facts can mislead; check its use in context in two places.

### script_rhetoric-004 · `enum` → `/script/beat_patterns/-`

**Which tense dominates: present, past, or mixed by section (for example past for history, present for explanation)?**

- Choices: `present`, `past`, `future`, `mixed-by-section`, `mixed`
- Why it matters: Becomes a tense rule for generated scripts.
- How to answer: Classify the main verb of each sentence; report shares per beat role.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Sample five sentences and check the classification by hand.

### script_rhetoric-005 · `object` → `/script/beat_patterns/-`

**Which rhetorical devices appear, and how often (rhetorical question, rule of three, contrast 'not X but Y', superlative, imperative, analogy, cliffhanger, callback)?**

- Why it matters: Lists the devices the writer should reuse, with frequency.
- How to answer: Scan sentences for each device; record counts and the timestamps of each instance; never copy the sentence.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Each device count needs at least one timestamp; spot-check two instances against the audio.

### script_rhetoric-006 · `pattern` → `/script/beat_patterns/-`

**What is the sentence template used inside an item (slots for subject, number, unit, consequence)?**

- Why it matters: Gives the per-item script pattern the generator fills.
- How to answer: Compare the first sentence of three items; keep the shared structure and replace content with typed slots, for example '{subject} {verb} {number} {unit}, {consequence}'.
- Evidence required: evidence.captions[] per item (analysis only)
- Challenge: Test the template against a fourth item; if it does not fit, list the variants instead of forcing one.

### script_rhetoric-007 · `integer` → `/parameters/-`

**How many specific numbers (counts, dates, measurements, percentages) are stated per item, median?**

- Why it matters: Becomes numbers_per_item and a constraint for content research.
- How to answer: Count digit groups and number words per item in captions; also check key-number overlays (F3 crops).
- Evidence required: evidence.captions[] (analysis only); frames: F3 key-number crops
- Challenge: Exclude label ordinals (FACT 2) and OCR noise; recount one item manually.

### script_rhetoric-008 · `boolean` → `/script/claims_need_sources`

**Are claims attributed to sources in the narration or on screen ('according to', source captions, citations)?**

- Why it matters: Sets claims_need_sources and whether the format shows sources.
- How to answer: Search caption text for attribution phrases and scan F1 frames at item starts for small source text.
- Evidence required: evidence.captions[] (analysis only); frames: F1 at item starts
- Challenge: Absence of attribution in the source does not mean variants may skip sources; note it, but the IR default stays true for factual formats.

### script_rhetoric-009 · `ratio` → `/audio/narration/specificity_ratio`

**What share of sentences contain a concrete specific (number, named place, date, named object) rather than a general statement?**

- Why it matters: Captures specificity, which this project treats as a quality constraint.
- How to answer: Classify each sentence as specific or general; report the share. Do not copy sentences.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Re-classify a random 20% sample; disagreement above 20% means low confidence.

### script_rhetoric-010 · `boolean` → `/script/beat_patterns/-`

**Does each item end with a consequence or 'so what' line that says why the fact matters?**

- Why it matters: Becomes a per-item closing slot.
- How to answer: Inspect the last sentence of each item; mark whether it states an implication, outcome or comparison.
- Evidence required: evidence.captions[] per item (analysis only)
- Challenge: Require the share of items with such a line; 'true' needs at least two thirds.

### script_rhetoric-011 · `pattern` → `/script/beat_patterns/-`

**What connective pattern links items (number callout, 'but', 'next', a question, no connective)?**

- Why it matters: Becomes the transition phrase slot between items.
- How to answer: Look at the first two words of each item's first sentence and abstract them to a type, for example '{ordinal} callout' or 'contrast word'.
- Evidence required: evidence.captions[] item starts (analysis only)
- Challenge: If items start differently each time, answer 'no fixed connective' rather than inventing a pattern.

### script_rhetoric-012 · `timestamps` → `/script/beat_patterns/-`

**Where does the script call back to the hook or an earlier item (timestamps)?**

- Why it matters: Adds a callback rule (for example payoff references the hook).
- How to answer: Find later sentences that repeat a key noun or number from the hook; list timestamps.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: A repeated topic word is not a callback unless it explicitly refers back.

### script_rhetoric-013 · `enum` → `/audio/narration/register`

**What register is the language in: casual or slang, neutral conversational, formal, or technical?**

- Choices: `casual`, `conversational`, `formal`, `technical`
- Why it matters: Becomes the tone/register parameter.
- How to answer: Look at contractions, slang, jargon density and sentence complexity across the whole script.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Register judged from the hook alone is over-generalised; check the middle and end.

### script_rhetoric-014 · `number` → `/audio/narration/intensifiers_per_min`

**How many intensifiers or emphasis words (very, insane, literally, actually, huge) occur per minute of speech?**

- Why it matters: Sets an intensity budget; high values read as hype.
- How to answer: Count words from a fixed intensifier list in captions; divide by total speech minutes from audio.speech_segments.
- Evidence required: evidence.captions[] (analysis only); evidence.audio.speech_segments
- Challenge: Report the word list used; counts depend on it.

### script_rhetoric-015 · `object` → `/audio/narration/word_count`

**How many words does the whole narration contain, and how many words per second of runtime?**

- Why it matters: Gives the script length budget for a target duration.
- How to answer: Word count of captions; divide by source.duration_s.
- Evidence required: evidence.captions[] (analysis only); evidence.source.duration_s
- Challenge: Check that captions cover the whole speech (compare caption span with speech_segments span).

### script_rhetoric-016 · `ratio` → `/timeline/beats`

**Is there a reversal or twist sentence, and at what fraction of the runtime?**

- Why it matters: Places a reversal beat in the format.
- How to answer: Find a sentence that contradicts an expectation set earlier (contrast word plus new information); give its start ratio.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: A contrast word alone is not a twist; the claim must invert something earlier.

### script_rhetoric-017 · `timestamps` → `/script/beat_patterns/-`

**Does the script ask the viewer to predict or guess before a reveal?**

- Why it matters: Adds a predict-then-reveal pattern (a known learning technique) to the format.
- How to answer: Look for a question followed by a pause (speech_segments gap) and then an answer; list timestamps.
- Evidence required: evidence.captions[] (analysis only); evidence.audio.speech_segments
- Challenge: Rhetorical questions answered immediately are not prediction prompts; require a gap of at least 0.5 s or an explicit prompt.

### script_rhetoric-018 · `enum` → `/script/beat_patterns/-`

**How is jargon handled: defined inline, replaced by plain words, used without definition, or absent?**

- Choices: `defined-inline`, `plain-words`, `undefined-jargon`, `no-jargon`
- Why it matters: Becomes a writing rule for technical topics.
- How to answer: Find technical terms in captions; check whether a definition clause follows within the same or next sentence.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: List how many terms were checked; one term is not enough for a rule.

### script_rhetoric-019 · `enum` → `/script/beat_patterns/-`

**Do sentences put the key information first (number or claim up front) or build to it at the end?**

- Choices: `front-loaded`, `end-loaded`, `mixed`
- Why it matters: Becomes a sentence construction rule.
- How to answer: For sentences containing a number, note whether the number appears in the first or last third of the sentence.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Report the counts behind the choice; a 55/45 split is 'mixed'.

### script_rhetoric-020 · `timestamps` → `/script/beat_patterns/-`

**How many direct questions to the viewer does the script contain, and where?**

- Why it matters: Sets the question count and placement rule.
- How to answer: Count sentences ending in a question mark (or interrogative structure when punctuation is missing); list timestamps.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Auto captions may drop question marks; check intonation on an A1 spectrogram for two instances.

### script_rhetoric-021 · `enum` → `/script/beat_patterns/-`

**What does the closing line do: summarise, provoke a thought, ask a question, instruct (call to action), or tease another video?**

- Choices: `summarise`, `provoke`, `question`, `call-to-action`, `tease-next`, `none`
- Why it matters: Fills the outro line slot.
- How to answer: Classify the last sentence of the narration.
- Evidence required: evidence.captions[] last sentence (analysis only)
- Challenge: Check that the 'last sentence' is not end-card boilerplate added after the content.

### script_rhetoric-022 · `pattern` → `/script/beat_patterns/-`

**Is there a recurring refrain or catchphrase structure (same phrase shape repeated across items)?**

- Why it matters: Adds a refrain slot that a new series fills with its own wording.
- How to answer: Look for repeated n-grams of 3+ words across items; describe only the shape (for example '{ordinal} reason: {claim}'), never the words.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: A repeated distinctive phrase belongs to the source; the pattern must not let it through.

### script_rhetoric-023 · `enum` → `/typography/captions/relation_to_voice`

**Does the on-screen text duplicate the narration word for word, summarise it, or add information the voice does not say?**

- Choices: `verbatim`, `summary`, `adds-information`, `no-on-screen-text`
- Why it matters: Decides how caption and label text are generated from the script.
- How to answer: Compare F3 crops of on-screen text in three items with the caption text at the same time.
- Evidence required: frames: F3 text crops; evidence.captions[] (analysis only)
- Challenge: If captions came from OCR, verbatim is circular; use the transcription adapter output or say not determinable.

### script_rhetoric-024 · `text` → `/script/beat_patterns/-`

**What emotional arc does the script follow (for example curiosity to surprise to satisfaction, fear to relief, problem to solution)?**

- Why it matters: Gives the writer an arc to follow; recorded as an observed pattern, not a judgement of quality.
- How to answer: Classify the dominant function of each beat (question, tension, reveal, resolution) and write the sequence.
- Evidence required: timeline beats; evidence.captions[] (analysis only)
- Challenge: Emotional labels are interpretive; method must be 'inferred' and each step must cite a beat.

### script_rhetoric-025 · `enum` → `/script/beat_patterns/-`

**Is the script a story (character, goal, obstacle, outcome) or a list of independent points?**

- Choices: `story`, `list`, `hybrid`
- Why it matters: Determines whether items can be reordered.
- How to answer: Check whether later items depend on earlier ones (references, continuity of a subject).
- Evidence required: evidence.captions[] (analysis only); timeline beats
- Challenge: Try mentally swapping items 2 and 3; if nothing breaks it is a list.

### script_rhetoric-026 · `number` → `/script/beat_patterns/-`

**How often are numbers made tangible with comparisons or analogies (for example 'as tall as {landmark}')?**

- Why it matters: Sets a comparison-per-item rule.
- How to answer: Count analogy or comparison constructions per item; report median.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: List the timestamps of counted instances.

### script_rhetoric-027 · `number` → `/audio/narration/hedges_per_min`

**How much hedging language is used (may, might, some say, reportedly) per minute?**

- Why it matters: Indicates claim confidence style; informs fact-check strictness for variants.
- How to answer: Count hedge words per speech minute.
- Evidence required: evidence.captions[] (analysis only); evidence.audio.speech_segments
- Challenge: Report the hedge list used.

### script_rhetoric-028 · `enum` → `/generation_rules/-`

**Are numbers spoken rounded ('about 3 million') or precise ('3,124,000')?**

- Choices: `rounded`, `precise`, `mixed`
- Why it matters: Becomes a number formatting rule for scripts and overlays.
- How to answer: Classify each spoken number by significant figures; also check on-screen numbers.
- Evidence required: evidence.captions[] (analysis only); frames: F3 key-number crops
- Challenge: Years and ordinals are neither; exclude them from the count.

### script_rhetoric-029 · `list` → `/generation_rules/-`

**What kinds of claims would a variant need to fact-check (statistics, dates, health, money, quotes, rankings)?**

- Why it matters: Tells the render pipeline which claim types require a cited source.
- How to answer: Classify each factual sentence by claim type; list the types present with counts.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Health, money and safety claims must be listed if present at all, even once.

### script_rhetoric-030 · `rule` → `/generation_rules/-`

**What is the word budget for one item beat (median words per item and the words-per-second rate it implies)?**

- Why it matters: Becomes the generation rule words_per_item = item_beat_s x words_per_s.
- How to answer: Count caption words per item beat; divide by item beat duration.
- Evidence required: evidence.captions[] (analysis only); item beat boundaries
- Challenge: Recompute for two items; the rule must predict both within 20%.

### script_rhetoric-031 · `list` → `/parameters/-`

**Which script properties should be parameters for a new topic (tone, point of view, words per item, numbers per item, sources shown)?**

- Why it matters: Feeds the parameteriser with typed script parameters.
- How to answer: Collect answers 003, 007, 013, 030 and propose parameters with defaults from the observed values and ranges from observed spread.
- Evidence required: script lens answers
- Challenge: Every proposed parameter must cite the question it comes from.

### script_rhetoric-032 · `pattern` → `/script/beat_patterns/-`

**Is there a sign-off or recurring closing formula?**

- Why it matters: Adds a closing slot that a new series fills with its own line.
- How to answer: Check the final 5 s of captions and the last text crop; describe the form only (for example '{series name} sign-off with handle').
- Evidence required: evidence.captions[] (analysis only); frames: F1 last 5 s
- Challenge: A sign-off containing the source's name or handle must not enter the format.

### script_rhetoric-033 · `object` → `/audio/narration/vocabulary_complexity`

**How complex is the vocabulary for non-native listeners (share of words outside a common 3,000-word list, idiom count)?**

- Why it matters: Sets a plain-language constraint for localisable variants.
- How to answer: If a frequency list is available locally, compute the out-of-list share; otherwise count idioms and multi-syllable words per 100 words and mark the method inferred.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: If no word list was used, the answer must say so and confidence must be under 0.4.

### script_rhetoric-034 · `pattern` → `/audio/narration/audience_address`

**Does the narration address a specific audience group or situation ('if you are a {group}', 'when your {situation}')?**

- Why it matters: Adds an audience-address slot.
- How to answer: Search caption text for conditional address patterns; describe the shape only.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Generic 'you' is not audience targeting; require an explicit group or situation.

### script_rhetoric-035 · `number` → `/script/beat_patterns/-`

**How many distinct claims or ideas does each sentence carry on average (one idea per sentence or packed sentences)?**

- Why it matters: Sets the density rule for script writing.
- How to answer: For 10 sentences, count independent clauses carrying new information; report the mean.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Recount three of the sentences; disagreement means lower confidence.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "script_rhetoric-001", "ir_path": "/script/reading_level", "answer_type": "number"}, {"id": "script_rhetoric-002", "ir_path": "/audio/narration/words_per_sentence", "answer_type": "distribution"}, {"id": "script_rhetoric-003", "ir_path": "/audio/narration/point_of_view", "answer_type": "enum", "choices": ["first-person", "second-person", "third-person", "mixed"]}, {"id": "script_rhetoric-004", "ir_path": "/script/beat_patterns/-", "answer_type": "enum", "choices": ["present", "past", "future", "mixed-by-section", "mixed"]}, {"id": "script_rhetoric-005", "ir_path": "/script/beat_patterns/-", "answer_type": "object"}, {"id": "script_rhetoric-006", "ir_path": "/script/beat_patterns/-", "answer_type": "pattern"}, {"id": "script_rhetoric-007", "ir_path": "/parameters/-", "answer_type": "integer"}, {"id": "script_rhetoric-008", "ir_path": "/script/claims_need_sources", "answer_type": "boolean"}, {"id": "script_rhetoric-009", "ir_path": "/audio/narration/specificity_ratio", "answer_type": "ratio"}, {"id": "script_rhetoric-010", "ir_path": "/script/beat_patterns/-", "answer_type": "boolean"}, {"id": "script_rhetoric-011", "ir_path": "/script/beat_patterns/-", "answer_type": "pattern"}, {"id": "script_rhetoric-012", "ir_path": "/script/beat_patterns/-", "answer_type": "timestamps"}, {"id": "script_rhetoric-013", "ir_path": "/audio/narration/register", "answer_type": "enum", "choices": ["casual", "conversational", "formal", "technical"]}, {"id": "script_rhetoric-014", "ir_path": "/audio/narration/intensifiers_per_min", "answer_type": "number"}, {"id": "script_rhetoric-015", "ir_path": "/audio/narration/word_count", "answer_type": "object"}, {"id": "script_rhetoric-016", "ir_path": "/timeline/beats", "answer_type": "ratio"}, {"id": "script_rhetoric-017", "ir_path": "/script/beat_patterns/-", "answer_type": "timestamps"}, {"id": "script_rhetoric-018", "ir_path": "/script/beat_patterns/-", "answer_type": "enum", "choices": ["defined-inline", "plain-words", "undefined-jargon", "no-jargon"]}, {"id": "script_rhetoric-019", "ir_path": "/script/beat_patterns/-", "answer_type": "enum", "choices": ["front-loaded", "end-loaded", "mixed"]}, {"id": "script_rhetoric-020", "ir_path": "/script/beat_patterns/-", "answer_type": "timestamps"}, {"id": "script_rhetoric-021", "ir_path": "/script/beat_patterns/-", "answer_type": "enum", "choices": ["summarise", "provoke", "question", "call-to-action", "tease-next", "none"]}, {"id": "script_rhetoric-022", "ir_path": "/script/beat_patterns/-", "answer_type": "pattern"}, {"id": "script_rhetoric-023", "ir_path": "/typography/captions/relation_to_voice", "answer_type": "enum", "choices": ["verbatim", "summary", "adds-information", "no-on-screen-text"]}, {"id": "script_rhetoric-024", "ir_path": "/script/beat_patterns/-", "answer_type": "text"}, {"id": "script_rhetoric-025", "ir_path": "/script/beat_patterns/-", "answer_type": "enum", "choices": ["story", "list", "hybrid"]}, {"id": "script_rhetoric-026", "ir_path": "/script/beat_patterns/-", "answer_type": "number"}, {"id": "script_rhetoric-027", "ir_path": "/audio/narration/hedges_per_min", "answer_type": "number"}, {"id": "script_rhetoric-028", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["rounded", "precise", "mixed"]}, {"id": "script_rhetoric-029", "ir_path": "/generation_rules/-", "answer_type": "list"}, {"id": "script_rhetoric-030", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "script_rhetoric-031", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "script_rhetoric-032", "ir_path": "/script/beat_patterns/-", "answer_type": "pattern"}, {"id": "script_rhetoric-033", "ir_path": "/audio/narration/vocabulary_complexity", "answer_type": "object"}, {"id": "script_rhetoric-034", "ir_path": "/audio/narration/audience_address", "answer_type": "pattern"}, {"id": "script_rhetoric-035", "ir_path": "/script/beat_patterns/-", "answer_type": "number"}]
```
