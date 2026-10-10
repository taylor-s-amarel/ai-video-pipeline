# Video RE question bank: Typography and captions

Lens `typography_captions` · 36 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-typography-captions` subagent and challenged by `video-re-challenger`.

Lifts title, caption and label styling (position, size, weight, case, colour, backing, chunking) and caption timing against speech.

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
- `distribution`: {"median": m, "p10": a, "p90": b, "n": count, "unit": "..."}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `color`: "#RRGGBB"
- `list`: array of short strings (technique names or kinds)
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- text_regions[] bbox, area_ratio, y_center_ratio (video_re_text_regions)
- captions[] (video_re_caption_track, video_re_ocr_adapter or video_re_transcribe_adapter)
- audio.speech_segments

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_text_presence_timeline`, `video_re_detect_text_position_grid`, `video_re_detect_text_color_contrast`, `video_re_detect_text_outline_stroke`, `video_re_detect_text_box_backing`, `video_re_detect_caption_line_count`, `video_re_detect_font_weight_class`, `video_re_detect_label_patterns`, `video_re_detect_emoji_sticker_overlays`, `video_re_detect_karaoke_highlight`, `video_re_detect_safe_margin_usage`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F3 crops of caption, title and label regions enlarged 2x; F9 for text and backing colours; F8 around caption changes.

## Pitfalls challengers check first

- Naming a specific font from appearance; give a font class instead
- Measuring caption sync from a transcription whose own timing error is unknown
- Treating OCR misses as 'no caption'

## Parameters this lens usually proposes

- caption_font_class
- caption_color / highlight_color
- caption_max_words
- caption_y_ratio
- label_pattern

## IR paths this lens writes

- `/generation_rules/-` (2)
- `/parameters/-` (1)
- `/typography/captions/backing` (1)
- `/typography/captions/card_s` (1)
- `/typography/captions/case` (1)
- `/typography/captions/colors` (1)
- `/typography/captions/contrast_ratio` (1)
- `/typography/captions/emoji` (1)
- `/typography/captions/emphasis` (1)
- `/typography/captions/font_class` (1)
- `/typography/captions/gap_behaviour` (1)
- `/typography/captions/lines_max` (1)
- `/typography/captions/margins` (1)
- `/typography/captions/max_area_ratio` (1)
- `/typography/captions/max_chars_per_line` (1)
- `/typography/captions/max_width_ratio` (1)
- `/typography/captions/mode` (1)
- `/typography/captions/overlaps_subject` (1)
- `/typography/captions/punctuation` (1)
- `/typography/captions/safe_area_ok` (1)
- `/typography/captions/size_ratio` (1)
- `/typography/captions/source` (1)
- `/typography/captions/stroke_ratio` (1)
- `/typography/captions/sync_offset_ms` (2)
- `/typography/captions/tracking` (1)
- `/typography/captions/weight` (1)
- `/typography/captions/y_center_ratio` (1)
- `/typography/labels/number_size_ratio` (1)
- `/typography/labels/style` (1)
- `/typography/title/case` (1)
- `/typography/title/color` (1)
- `/typography/title/font_class` (1)
- `/typography/title/y_center_ratio` (1)
- `/typography/words_on_screen_max` (1)

## Questions (36)

### typography_captions-001 · `ratio` → `/typography/captions/y_center_ratio`

**Where do captions sit vertically (median y centre as a fraction of frame height)?**

- Why it matters: Fills caption y position.
- How to answer: Median y_center_ratio of evidence.text_regions[] entries in the caption role (recurring regions that change with speech); confirm on 3 F1 frames.
- Evidence required: evidence.text_regions[].y_center_ratio; frames: F1 samples
- Challenge: Separate titles and labels from captions before taking the median; report how regions were assigned.

### typography_captions-002 · `integer` → `/typography/captions/lines_max`

**What is the maximum number of caption lines on screen at once?**

- Why it matters: Fills caption lines_max.
- How to answer: Inspect F3 crops of the caption area at 6 times; count lines.
- Evidence required: frames: F3 caption crops
- Challenge: Check the longest caption cards; maximums hide there.

### typography_captions-003 · `integer` → `/typography/words_on_screen_max`

**What is the maximum number of words on screen in one caption card?**

- Why it matters: Fills words_on_screen_max.
- How to answer: Word counts of caption cards (evidence.captions[] when burned-in OCR exists, otherwise F3 crops at 6 times); report max and median.
- Evidence required: evidence.captions[]; frames: F3
- Challenge: Word-by-word captions show one word at a time; distinguish card words from highlighted words.

### typography_captions-004 · `enum` → `/typography/captions/font_class`

**What font class do captions use (geometric sans, grotesque sans, condensed sans, rounded sans, serif, slab, handwritten, display)?**

- Choices: `geometric-sans`, `grotesque-sans`, `condensed-sans`, `rounded-sans`, `serif`, `slab`, `handwritten`, `display`
- Why it matters: Gives a font class the renderer can map to an open font.
- How to answer: Enlarged F3 crops: check letter shapes (round 'o' and 'e' for geometric; narrow letters for condensed; serifs).
- Evidence required: frames: F3 enlarged
- Challenge: Never name a specific commercial font as fact; a named font must be marked inferred.

### typography_captions-005 · `enum` → `/typography/captions/weight`

**What weight are captions (regular, medium, bold, black)?**

- Choices: `regular`, `medium`, `bold`, `black`
- Why it matters: Fills caption weight.
- How to answer: Stroke thickness relative to letter height on F3 crops: stem width / cap height above about 0.18 is bold, above 0.24 black.
- Evidence required: frames: F3 enlarged
- Challenge: Outline strokes add apparent weight; measure the fill only.

### typography_captions-006 · `enum` → `/typography/captions/case`

**What case do captions use (all caps, sentence case, title case, lower case)?**

- Choices: `all-caps`, `sentence`, `title`, `lower`, `mixed`
- Why it matters: Fills caption case.
- How to answer: F3 crops at 6 times.
- Evidence required: frames: F3
- Challenge: Check at least one caption with a proper noun.

### typography_captions-007 · `object` → `/typography/captions/colors`

**What colour is caption text, and what colour marks highlighted or key words?**

- Why it matters: Fills caption colour and highlight colour.
- How to answer: F9 average colour inside thick strokes (3x3 px) of normal and highlighted words.
- Evidence required: frames: F9
- Challenge: Sample three letters for each and report the spread.

### typography_captions-008 · `enum` → `/typography/captions/backing`

**What backing do captions have (none, stroke, drop shadow, solid box, frosted panel)?**

- Choices: `none`, `stroke`, `shadow`, `solid-box`, `frosted-panel`, `stroke-and-shadow`
- Why it matters: Fills caption backing.
- How to answer: F3 crops around letters and panel edges over busy and calm backgrounds.
- Evidence required: frames: F3
- Challenge: Compare two frames with different backgrounds to tell a frosted panel from a solid box.

### typography_captions-009 · `ratio` → `/typography/captions/stroke_ratio`

**If captions have an outline stroke, how thick is it relative to letter height?**

- Why it matters: Fills stroke width ratio.
- How to answer: On an enlarged F3 crop, measure the stroke width in px / cap height in px.
- Evidence required: frames: F3 at 4x
- Challenge: Anti-aliasing adds a pixel; report the measurement method.

### typography_captions-010 · `ratio` → `/typography/captions/size_ratio`

**How tall are caption letters as a fraction of frame height (cap height)?**

- Why it matters: Fills caption size.
- How to answer: Measure the cap height of an upper-case letter in px on an F3 crop / source.height.
- Evidence required: frames: F3; evidence.source.height
- Challenge: Text bboxes include descenders and padding; use letter measurements.

### typography_captions-011 · `ms` → `/typography/captions/sync_offset_ms`

**What is the mean offset between caption appearance and the matching spoken word (ms; negative = caption early)?**

- Why it matters: Fills caption sync; a common house rule is within 150 ms.
- How to answer: For 10 caption cards, compare the on-screen appearance time (F8 at caption changes, or text_regions t_s) with the speech onset of the first word (A1 spectrogram or speech_segments).
- Evidence required: frames: F8 at caption changes; evidence.audio.speech_segments; A1
- Challenge: Transcribed captions are not on-screen timings; only burned-in text can measure on-screen sync. Report n and spread.

### typography_captions-012 · `enum` → `/typography/captions/sync_offset_ms`

**Do captions appear before, on, or after the spoken word?**

- Choices: `before`, `on`, `after`, `varies`
- Why it matters: Summarises sync behaviour for the caption timing rule.
- How to answer: From 011: 'on' when the mean is within +/-100 ms and the spread is under 150 ms.
- Evidence required: sync offsets
- Challenge: Must agree with the numbers in 011.

### typography_captions-013 · `enum` → `/typography/captions/mode`

**Are captions shown as phrase cards, word-by-word reveals, or karaoke-style highlighting within a card?**

- Choices: `phrase-cards`, `word-by-word`, `karaoke-highlight`, `none`
- Why it matters: Fills caption mode.
- How to answer: F8 frame steps across a caption: watch whether words appear one at a time or highlights move.
- Evidence required: frames: F8
- Challenge: Check two cards; mixed behaviour must be reported.

### typography_captions-014 · `list` → `/typography/captions/emphasis`

**How are key words emphasised (colour change, scale pop, weight change, underline, box)?**

- Why it matters: Fills emphasis style.
- How to answer: Compare emphasised and normal words on F3 crops and F8 steps.
- Evidence required: frames: F3; frames: F8
- Challenge: Each listed method needs one timestamp.

### typography_captions-015 · `distribution` → `/typography/captions/card_s`

**How long does a caption card stay on screen (median, min, max)?**

- Why it matters: Sets caption card duration.
- How to answer: From burned-in caption changes (text_regions in caption area) or evidence.captions[] when they represent the burned-in captions.
- Evidence required: evidence.text_regions[]; evidence.captions[]
- Challenge: Say which source the timings came from.

### typography_captions-016 · `enum` → `/typography/captions/gap_behaviour`

**Are captions on screen during speech pauses, or do they clear when nobody is speaking?**

- Choices: `clear-in-pauses`, `hold-through-pauses`, `mixed`
- Why it matters: Becomes a caption gap rule.
- How to answer: Check frames inside speech gaps over 0.5 s (speech_segments) for caption text.
- Evidence required: evidence.audio.speech_segments; frames: F1 inside gaps
- Challenge: Check at least 4 gaps.

### typography_captions-017 · `object` → `/typography/captions/max_width_ratio`

**How are captions aligned horizontally, and what is their maximum width as a fraction of the frame?**

- Why it matters: Fills alignment and max width.
- How to answer: evidence.text_regions[] bbox x and width for caption regions; report alignment and max width ratio.
- Evidence required: evidence.text_regions[].bbox
- Challenge: Left-aligned and centred look alike for one-line captions; check multi-line cards.

### typography_captions-018 · `object` → `/typography/title/font_class`

**What font class and weight does the title use, and is it the same family as captions?**

- Why it matters: Fills title font class.
- How to answer: Compare enlarged F3 crops of title and captions.
- Evidence required: frames: F3 title and caption crops
- Challenge: Same weight but different family is a common confusion; compare 'a', 'g', 'R'.

### typography_captions-019 · `color` → `/typography/title/color`

**What colour is title text across title appearances?**

- Why it matters: Fills title colour.
- How to answer: F9 inside title strokes in each title appearance.
- Evidence required: frames: F9
- Challenge: Report the spread over appearances; one sample is not enough.

### typography_captions-020 · `object` → `/typography/title/case`

**What case and letter spacing does the title use?**

- Why it matters: Fills title case and tracking.
- How to answer: F3 crops; tracking judged from gap between letters relative to stem width.
- Evidence required: frames: F3
- Challenge: Give measured gap/stem values.

### typography_captions-021 · `ratio` → `/typography/title/y_center_ratio`

**Where does the title sit when it appears (y centre ratio, alignment), across all title appearances?**

- Why it matters: Fills title placement beyond the first frame.
- How to answer: evidence.text_regions[] for the title role.
- Evidence required: evidence.text_regions[]
- Challenge: Compare with the hook lens answer for the first frame; differences must be explained.

### typography_captions-022 · `object` → `/typography/labels/style`

**How are item labels styled (font class, weight, colour, size ratio, backing, position)?**

- Why it matters: Fills typography.labels.
- How to answer: F3 and F9 on labels in 3 items; evidence.text_regions[] for position.
- Evidence required: frames: F3; frames: F9; evidence.text_regions[]
- Challenge: All fields must be consistent across the 3 items or reported as varying.

### typography_captions-023 · `number` → `/typography/labels/number_size_ratio`

**How large are key numbers compared with caption text (height ratio)?**

- Why it matters: Fills the number size ratio for reveals.
- How to answer: Number glyph height / caption cap height on F3 crops.
- Evidence required: frames: F3
- Challenge: Measure at the number's settled size, not during its entrance animation.

### typography_captions-024 · `object` → `/typography/captions/margins`

**What are the minimum text margins from the frame edges (fraction of width and height)?**

- Why it matters: Fills safe margins for text.
- How to answer: Min of bbox distances to each edge over evidence.text_regions[].
- Evidence required: evidence.text_regions[].bbox
- Challenge: Exclude watermark regions; they are not format text.

### typography_captions-025 · `ratio` → `/typography/captions/overlaps_subject`

**How often does text overlap faces or the main subject?**

- Why it matters: Becomes a placement constraint or confirms text-over-subject style.
- How to answer: For 10 frames with text and a subject, count overlaps.
- Evidence required: frames: F1 samples; evidence.text_regions[]
- Challenge: Report n; do not identify faces.

### typography_captions-026 · `boolean` → `/typography/captions/emoji`

**Are emoji or icons used in captions or labels?**

- Why it matters: Becomes an emoji rule.
- How to answer: F3 crops of captions and labels.
- Evidence required: frames: F3
- Challenge: Check 6 or more cards.

### typography_captions-027 · `enum` → `/typography/captions/punctuation`

**How is punctuation handled in captions (kept, stripped, only question marks)?**

- Choices: `kept`, `stripped`, `partial`
- Why it matters: Becomes a caption text cleaning rule.
- How to answer: Inspect F3 crops of cards at sentence ends.
- Evidence required: frames: F3
- Challenge: Check at least 3 sentence-final cards.

### typography_captions-028 · `integer` → `/typography/captions/max_chars_per_line`

**What is the maximum number of characters per caption line, and are lines balanced in length?**

- Why it matters: Becomes the line-breaking rule.
- How to answer: Count characters per line on F3 crops of the 5 longest cards.
- Evidence required: frames: F3
- Challenge: Report counts per card.

### typography_captions-029 · `number` → `/typography/captions/contrast_ratio`

**What is the approximate contrast ratio between caption text and its immediate backing?**

- Why it matters: Sets a minimum contrast for generated captions.
- How to answer: WCAG ratio from F9 samples of text fill and backing (or background next to the stroke).
- Evidence required: frames: F9
- Challenge: Report the worst of 3 samples over different backgrounds.

### typography_captions-030 · `integer` → `/generation_rules/-`

**How many distinct text styles appear in the whole video (title, caption, label, number, source line, CTA)?**

- Why it matters: Bounds the style count of the type system.
- How to answer: Group F3 crops of all text roles by font class, weight, colour and size.
- Evidence required: frames: F3
- Challenge: Differences only in size count as one style.

### typography_captions-031 · `enum` → `/typography/captions/tracking`

**Is letter spacing tight, normal or wide in captions?**

- Choices: `tight`, `normal`, `wide`
- Why it matters: Fills tracking.
- How to answer: Gap between letters relative to stem width on F3 crops; tight below 0.5, wide above 1.2.
- Evidence required: frames: F3
- Challenge: Report measured ratios.

### typography_captions-032 · `boolean` → `/typography/captions/safe_area_ok`

**Do captions stay clear of the bottom 20% and the right-hand 15% of the frame where vertical-video apps often draw controls?**

- Why it matters: Becomes a placement constraint; the exact zones vary by app and must be confirmed per platform.
- How to answer: Check caption bboxes in evidence.text_regions[] against those bands; read evidence.safe_area.violations for the template used.
- Evidence required: evidence.text_regions[]; evidence.safe_area.violations
- Challenge: Name the safe-area template the probe used; percentages are a working assumption, not a platform specification.

### typography_captions-033 · `enum` → `/typography/captions/source`

**Are captions burned into the picture, supplied as a separate subtitle track, or absent?**

- Choices: `burned-in`, `subtitle-track`, `both`, `none`
- Why it matters: Tells the pipeline which caption source to emit.
- How to answer: A7 stream list for subtitle streams; F1 frames for burned-in text; evidence.captions[] source as reported by video_re_caption_track.
- Evidence required: A7 streams; frames: F1; evidence.tools
- Challenge: evidence.captions[] may come from transcription; it proves speech, not on-screen captions.

### typography_captions-034 · `list` → `/parameters/-`

**What caption style parameters should a new video set (font class, colours, highlight, max words, position)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect answers 001-014 into typed parameters with observed defaults.
- Evidence required: typography answers
- Challenge: Each parameter needs derived_from.

### typography_captions-035 · `rule` → `/generation_rules/-`

**Write the caption chunking and timing rule (max words, break points, minimum hold, sync source).**

- Why it matters: Gives the compiler a procedural caption plan.
- How to answer: From 003, 011, 015 and 028, for example 'cards of at most N words, break at punctuation, hold at least X ms, time from word timestamps, never time-stretch speech'.
- Evidence required: typography answers
- Challenge: Apply the rule to 3 observed captions; the predicted card breaks should match at least 2.

### typography_captions-036 · `ratio` → `/typography/captions/max_area_ratio`

**What is the largest share of the frame area covered by text at any moment?**

- Why it matters: Becomes a text density limit.
- How to answer: Max over t of sum(area_ratio) from evidence.text_regions[] grouped by t_s.
- Evidence required: evidence.text_regions[].area_ratio
- Challenge: Backing panels may be included in bboxes; state whether they were.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F9** Average colour of a region: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y,scale=1:1:flags=area,format=rgb24" -f rawvideo - | od -An -tu1
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "typography_captions-001", "ir_path": "/typography/captions/y_center_ratio", "answer_type": "ratio"}, {"id": "typography_captions-002", "ir_path": "/typography/captions/lines_max", "answer_type": "integer"}, {"id": "typography_captions-003", "ir_path": "/typography/words_on_screen_max", "answer_type": "integer"}, {"id": "typography_captions-004", "ir_path": "/typography/captions/font_class", "answer_type": "enum", "choices": ["geometric-sans", "grotesque-sans", "condensed-sans", "rounded-sans", "serif", "slab", "handwritten", "display"]}, {"id": "typography_captions-005", "ir_path": "/typography/captions/weight", "answer_type": "enum", "choices": ["regular", "medium", "bold", "black"]}, {"id": "typography_captions-006", "ir_path": "/typography/captions/case", "answer_type": "enum", "choices": ["all-caps", "sentence", "title", "lower", "mixed"]}, {"id": "typography_captions-007", "ir_path": "/typography/captions/colors", "answer_type": "object"}, {"id": "typography_captions-008", "ir_path": "/typography/captions/backing", "answer_type": "enum", "choices": ["none", "stroke", "shadow", "solid-box", "frosted-panel", "stroke-and-shadow"]}, {"id": "typography_captions-009", "ir_path": "/typography/captions/stroke_ratio", "answer_type": "ratio"}, {"id": "typography_captions-010", "ir_path": "/typography/captions/size_ratio", "answer_type": "ratio"}, {"id": "typography_captions-011", "ir_path": "/typography/captions/sync_offset_ms", "answer_type": "ms"}, {"id": "typography_captions-012", "ir_path": "/typography/captions/sync_offset_ms", "answer_type": "enum", "choices": ["before", "on", "after", "varies"]}, {"id": "typography_captions-013", "ir_path": "/typography/captions/mode", "answer_type": "enum", "choices": ["phrase-cards", "word-by-word", "karaoke-highlight", "none"]}, {"id": "typography_captions-014", "ir_path": "/typography/captions/emphasis", "answer_type": "list"}, {"id": "typography_captions-015", "ir_path": "/typography/captions/card_s", "answer_type": "distribution"}, {"id": "typography_captions-016", "ir_path": "/typography/captions/gap_behaviour", "answer_type": "enum", "choices": ["clear-in-pauses", "hold-through-pauses", "mixed"]}, {"id": "typography_captions-017", "ir_path": "/typography/captions/max_width_ratio", "answer_type": "object"}, {"id": "typography_captions-018", "ir_path": "/typography/title/font_class", "answer_type": "object"}, {"id": "typography_captions-019", "ir_path": "/typography/title/color", "answer_type": "color"}, {"id": "typography_captions-020", "ir_path": "/typography/title/case", "answer_type": "object"}, {"id": "typography_captions-021", "ir_path": "/typography/title/y_center_ratio", "answer_type": "ratio"}, {"id": "typography_captions-022", "ir_path": "/typography/labels/style", "answer_type": "object"}, {"id": "typography_captions-023", "ir_path": "/typography/labels/number_size_ratio", "answer_type": "number"}, {"id": "typography_captions-024", "ir_path": "/typography/captions/margins", "answer_type": "object"}, {"id": "typography_captions-025", "ir_path": "/typography/captions/overlaps_subject", "answer_type": "ratio"}, {"id": "typography_captions-026", "ir_path": "/typography/captions/emoji", "answer_type": "boolean"}, {"id": "typography_captions-027", "ir_path": "/typography/captions/punctuation", "answer_type": "enum", "choices": ["kept", "stripped", "partial"]}, {"id": "typography_captions-028", "ir_path": "/typography/captions/max_chars_per_line", "answer_type": "integer"}, {"id": "typography_captions-029", "ir_path": "/typography/captions/contrast_ratio", "answer_type": "number"}, {"id": "typography_captions-030", "ir_path": "/generation_rules/-", "answer_type": "integer"}, {"id": "typography_captions-031", "ir_path": "/typography/captions/tracking", "answer_type": "enum", "choices": ["tight", "normal", "wide"]}, {"id": "typography_captions-032", "ir_path": "/typography/captions/safe_area_ok", "answer_type": "boolean"}, {"id": "typography_captions-033", "ir_path": "/typography/captions/source", "answer_type": "enum", "choices": ["burned-in", "subtitle-track", "both", "none"]}, {"id": "typography_captions-034", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "typography_captions-035", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "typography_captions-036", "ir_path": "/typography/captions/max_area_ratio", "answer_type": "ratio"}]
```
