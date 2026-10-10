# Video RE question bank: Colour and grade

Lens `color_grade` · 32 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-color-grade` subagent and challenged by `video-re-challenger`.

Measures palette, luminance range, saturation, temperature and consistency, and turns them into a reproducible grade recipe.

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
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `color`: "#RRGGBB"
- `palette`: ["#RRGGBB", ...] ordered by area, at most 8
- `text`: one technique description, at most 300 characters, no copied content
- `list`: array of short strings (technique names or kinds)
- `segments`: [{"start_s": a, "end_s": b, "label": "..."}]
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[].palette (video_re_palette_per_shot)

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_color_temperature_tint`, `video_re_detect_saturation_contrast_profile`, `video_re_detect_grade_curve_estimate`, `video_re_detect_vignette`, `video_re_detect_duotone_monochrome`, `video_re_detect_palette_consistency`, `video_re_detect_exposure_clipping`, `video_re_detect_banding`, `video_re_detect_color_range_space`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F6 statistics per shot, F7 waveform and vectorscope on 3+ representative frames, F9 for accent colours.

## Pitfalls challengers check first

- Reporting a palette dominated by a text panel as the grade
- Comparing colours across differently compressed frames
- Calling a look 'cinematic' instead of measuring it

## Parameters this lens usually proposes

- palette (list of colors)
- accent_color (color)
- saturation_level
- grade_recipe (string)

## IR paths this lens writes

- `/generation_rules/-` (11)
- `/motion/transitions/-` (1)
- `/parameters/-` (3)
- `/visual/grade` (15)
- `/visual/layers/-` (1)
- `/visual/palette` (1)

## Questions (32)

### color_grade-001 · `palette` → `/visual/palette`

**What are the video's dominant colours, ordered by area?**

- Why it matters: Fills visual.palette.
- How to answer: Merge evidence.shots[].palette weighted by shot duration (video_re_palette_per_shot); keep up to 8 colours, merging colours within about 20 RGB units.
- Evidence required: evidence.shots[].palette; evidence.shots[].duration_s
- Challenge: Check that a persistent panel or title colour is not reported as the scene grade; F9 on two shots should contain the top colours.

### color_grade-002 · `text` → `/visual/grade`

**How would the grade be described in measurable terms (temperature, contrast, saturation, black and white points)?**

- Why it matters: Fills visual.grade as a short technique description.
- How to answer: Summarise 003-006 in one sentence with the numbers, for example 'warm (V-U +12), moderate contrast (Y 18-232), saturated (SATAVG 72)'.
- Evidence required: color_grade-003..006
- Challenge: Words like 'cinematic' or 'moody' are taste; each adjective must carry a number.

### color_grade-003 · `number` → `/visual/grade`

**What is the average saturation (signalstats SATAVG), median over shots?**

- Why it matters: Sets the saturation level parameter.
- How to answer: F6 on 1 s of each shot (or a sample of 10 shots); median of per-shot SATAVG means.
- Evidence required: F6 per shot
- Challenge: Text panels and bright titles raise SATAVG; recompute on a crop without text for 3 shots.

### color_grade-004 · `object` → `/visual/grade`

**What are the luma black and white points (median YMIN and YMAX per shot)?**

- Why it matters: Defines contrast range for the grade recipe.
- How to answer: F6 YMIN/YMAX per sampled shot; report medians.
- Evidence required: F6 per shot
- Challenge: Tiny specular highlights set YMAX; also report the 1st/99th percentile from a histogram if available.

### color_grade-005 · `enum` → `/visual/grade`

**Are blacks crushed, natural, or lifted (faded look)?**

- Choices: `crushed`, `natural`, `lifted`
- Why it matters: Fills the contrast style.
- How to answer: From YMIN medians and F7 waveforms: as a rough convention, lifted when the darkest areas stay above about 30 (8-bit, limited range 16-235) and crushed when large areas sit flat at 16. Report the values.
- Evidence required: F6 YMIN; F7 waveform
- Challenge: Check the stream colour range in A7; full-range sources shift these values.

### color_grade-006 · `enum` → `/visual/grade`

**Is the colour temperature warm, neutral or cool on average?**

- Choices: `warm`, `neutral`, `cool`
- Why it matters: Fills temperature in the grade.
- How to answer: F6 UAVG and VAVG medians (128 is neutral in 8-bit): V clearly above U suggests warm, U above V cool (this swarm uses a difference of 4 as the cut-off; report the values); confirm on an F7 vectorscope.
- Evidence required: F6 UAVG/VAVG; F7 vectorscope
- Challenge: Content colours (a blue ocean) shift averages without any grade; check neutral elements (white text) with F9.

### color_grade-007 · `object` → `/generation_rules/-`

**How consistent is the grade across shots (standard deviation of per-shot SATAVG and HUEMED)?**

- Why it matters: Tells whether the format normalises sources to one look.
- How to answer: F6 per shot; report stdev of SATAVG and of HUEMED (circular).
- Evidence required: F6 per shot
- Challenge: Different subjects vary naturally; compare against a deliberately mixed baseline is impossible, so mark the conclusion inferred.

### color_grade-008 · `boolean` → `/visual/grade`

**Is there a teal-and-orange split (cool shadows, warm highlights)?**

- Why it matters: Adds a split-tone recipe.
- How to answer: F7 vectorscope: two lobes near orange and teal; F9 on shadow and highlight areas.
- Evidence required: F7; F9
- Challenge: Skin tones and sky alone create both lobes; check a frame without people or sky.

### color_grade-009 · `color` → `/parameters/-`

**What accent colour is used for emphasis (highlighted words, labels, arrows)?**

- Why it matters: Becomes the accent_color parameter.
- How to answer: F9 inside highlighted words and labels in 3 places.
- Evidence required: frames: F9
- Challenge: Report the spread across samples.

### color_grade-010 · `boolean` → `/generation_rules/-`

**Does each item get its own colour code (label colour, tint, background hue)?**

- Why it matters: Becomes a per-item colour rule.
- How to answer: F9 on labels and backgrounds per item.
- Evidence required: frames: F9 per item
- Challenge: Hue differences under about 20 degrees are not distinct codes.

### color_grade-011 · `enum` → `/generation_rules/-`

**Is the title colour complementary to, analogous to, or independent of the scene palette?**

- Choices: `complementary`, `analogous`, `independent`
- Why it matters: Becomes a title colour selection rule.
- How to answer: Hue of the title colour (F9) versus dominant scene hues (001).
- Evidence required: frames: F9; palette
- Challenge: Report hue angles.

### color_grade-012 · `enum` → `/visual/grade`

**Do skin tones look natural, warmed, cooled or stylised?**

- Choices: `natural`, `warmed`, `cooled`, `stylised`, `no-skin`
- Why it matters: Constrains the grade when people appear.
- How to answer: F7 vectorscope: skin falls near the skin-tone line; F9 on skin areas.
- Evidence required: F7; F9
- Challenge: Do not describe the people; only the colour position.

### color_grade-013 · `object` → `/visual/grade`

**Are shadows and highlights tinted differently (split toning), and with which hues?**

- Why it matters: Adds split-toning parameters.
- How to answer: F9 on dark and bright neutral regions; hue of each.
- Evidence required: F9
- Challenge: Report the samples and their hues.

### color_grade-014 · `number` → `/visual/grade`

**How strong is edge darkening (corner luma divided by centre luma)?**

- Why it matters: Fills vignette strength in the grade.
- How to answer: F9 luma of corner versus centre on 3 even frames.
- Evidence required: F9
- Challenge: Pick frames where the content is even.

### color_grade-015 · `object` → `/generation_rules/-`

**Does overall brightness change across the video (darker or brighter toward the end)?**

- Why it matters: Becomes a brightness arc rule or confirms a flat grade.
- How to answer: F6 YAVG per shot against time; slope.
- Evidence required: F6 per shot
- Challenge: Content-driven changes (night scenes) do not imply a grade arc.

### color_grade-016 · `boolean` → `/generation_rules/-`

**Is the hook graded differently from the body?**

- Why it matters: Becomes a hook grade option.
- How to answer: Compare F6 stats for hook shots against item shots.
- Evidence required: F6
- Challenge: Require a difference beyond the between-item spread.

### color_grade-017 · `boolean` → `/visual/grade`

**Is there film emulation (grain plus halation plus faded blacks)?**

- Why it matters: Adds a film-look recipe.
- How to answer: Combine grain (layers lens), lifted blacks (005) and red halos around highlights (F3).
- Evidence required: F3; F6
- Challenge: All three cues must be present for 'true'.

### color_grade-018 · `enum` → `/visual/grade`

**Is the look high-key, mid-key or low-key (median YAVG)?**

- Choices: `high-key`, `mid-key`, `low-key`
- Why it matters: Fills key in the grade.
- How to answer: Median F6 YAVG; this swarm's convention is high-key above about 150 and low-key below about 80 (8-bit limited range). Report the value.
- Evidence required: F6
- Challenge: State the thresholds used and the value.

### color_grade-019 · `ratio` → `/visual/grade`

**What share of pixels are clipped at the top of the range in typical frames?**

- Why it matters: Sets a highlight protection rule.
- How to answer: F7 waveform shows a flat line at the top; or count pixels with Y at max using a histogram on 3 frames.
- Evidence required: F7
- Challenge: White text is intentionally at max; exclude text areas.

### color_grade-020 · `enum` → `/parameters/-`

**Is the palette tied to the topic (derived from the subject) or a fixed brand palette?**

- Choices: `topic-derived`, `fixed-brand`, `mixed`
- Why it matters: Becomes the palette_mode parameter.
- How to answer: Compare palettes across items: fixed colours present in all items suggest a brand palette.
- Evidence required: evidence.shots[].palette
- Challenge: A single-topic video cannot separate the two cleanly; mark inferred.

### color_grade-021 · `integer` → `/generation_rules/-`

**How many distinct dominant hues does the video use?**

- Why it matters: Bounds palette size.
- How to answer: Cluster palette colours by hue (30-degree bins); count bins holding at least 5% of area.
- Evidence required: evidence.shots[].palette
- Challenge: Greys have no hue; exclude low-saturation colours from the count.

### color_grade-022 · `segments` → `/visual/grade`

**Are there monochrome, duotone or desaturated sections, and when?**

- Why it matters: Adds a monochrome treatment option.
- How to answer: F6 SATAVG near zero over a shot.
- Evidence required: F6
- Challenge: Black-and-white archival photos are content, not grade; check whether colour graphics are also desaturated.

### color_grade-023 · `boolean` → `/visual/grade`

**Are neon or glowing colours used (very high saturation with glow)?**

- Why it matters: Adds a neon accent style.
- How to answer: F9 samples with SAT near max and a glow halo on F3.
- Evidence required: F9; F3
- Challenge: Report the saturation values.

### color_grade-024 · `rule` → `/generation_rules/-`

**What ffmpeg filter recipe approximates the observed grade (for example eq, colorbalance, curves, vignette)?**

- Why it matters: Gives a reproducible grade.
- How to answer: Choose filters and values to match 003-006; render 3 test frames from neutral test media and compare F6 statistics.
- Evidence required: grade measurements
- Challenge: Run the recipe on a test frame; stats must move in the stated direction.

### color_grade-025 · `list` → `/parameters/-`

**Which colour parameters should a new video set (palette, accent, saturation, temperature)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect 001, 003, 006 and 009 into parameters.
- Evidence required: grade answers
- Challenge: Each parameter needs derived_from.

### color_grade-026 · `object` → `/visual/layers/-`

**What colours do gradient overlays use, and in which direction do they run?**

- Why it matters: Adds gradient overlay parameters.
- How to answer: F9 at both ends of visible gradients.
- Evidence required: F9
- Challenge: Give the two end colours and the direction.

### color_grade-027 · `number` → `/generation_rules/-`

**How saturated are text colours compared with the scene (text SAT vs scene SATAVG)?**

- Why it matters: Becomes a text contrast rule.
- How to answer: F9 on text versus F6 scene averages.
- Evidence required: F9; F6
- Challenge: Report both values.

### color_grade-028 · `object` → `/generation_rules/-`

**Are archival or historical images given a special treatment (sepia, grain, frame)?**

- Why it matters: Adds a treatment for archival material.
- How to answer: Inspect shots with old photographs.
- Evidence required: frames: F1
- Challenge: If no archival material exists, answer not determinable.

### color_grade-029 · `object` → `/motion/transitions/-`

**Are there colour flashes at beats or transitions, and which colour?**

- Why it matters: Adds flash colour to the transition recipe.
- How to answer: F6 YAVG spikes over one or two frames; F9 colour on the flash frame.
- Evidence required: F6; F9
- Challenge: Check against the transitions lens.

### color_grade-030 · `enum` → `/visual/grade`

**Is extra sharpening or clarity applied (halos at edges)?**

- Choices: `heavy-sharpening`, `mild`, `none`
- Why it matters: Adds or rules out a sharpen step.
- How to answer: F3 enlarged crops at high-contrast edges; bright or dark halos 1-3 px wide indicate sharpening.
- Evidence required: F3
- Challenge: Compression ringing looks similar; check a smooth gradient region too.

### color_grade-031 · `boolean` → `/generation_rules/-`

**Are different source images colour-matched (white balance consistent across shots)?**

- Why it matters: Becomes a colour-matching step in the render plan.
- How to answer: F9 on neutral (white or grey) areas across 5 shots; compare U/V.
- Evidence required: F9
- Challenge: Report the U/V values per shot.

### color_grade-032 · `boolean` → `/generation_rules/-`

**Is there visible banding in gradients (8-bit steps), and should the rebuild add dither or grain?**

- Why it matters: A quality rule for generated gradients.
- How to answer: F3 enlarged crop of a smooth gradient; count visible steps.
- Evidence required: F3
- Challenge: Banding from the platform's re-encode is not the creator's technique; note the uncertainty.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F6** Per-frame colour statistics (YMIN, YAVG, YMAX, SATAVG, HUEMED, UAVG, VAVG): ffmpeg -v error -ss T -t D -i "$SRC" -vf "signalstats,metadata=mode=print:file=$WORK/stats.txt" -an -f null -
- **F7** Scopes: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "format=yuv444p,waveform=display=overlay" "$WORK/wave_T.png"; vectorscope with -vf "format=yuv444p,vectorscope=mode=color3"
- **F9** Average colour of a region: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y,scale=1:1:flags=area,format=rgb24" -f rawvideo - | od -An -tu1
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "color_grade-001", "ir_path": "/visual/palette", "answer_type": "palette"}, {"id": "color_grade-002", "ir_path": "/visual/grade", "answer_type": "text"}, {"id": "color_grade-003", "ir_path": "/visual/grade", "answer_type": "number"}, {"id": "color_grade-004", "ir_path": "/visual/grade", "answer_type": "object"}, {"id": "color_grade-005", "ir_path": "/visual/grade", "answer_type": "enum", "choices": ["crushed", "natural", "lifted"]}, {"id": "color_grade-006", "ir_path": "/visual/grade", "answer_type": "enum", "choices": ["warm", "neutral", "cool"]}, {"id": "color_grade-007", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "color_grade-008", "ir_path": "/visual/grade", "answer_type": "boolean"}, {"id": "color_grade-009", "ir_path": "/parameters/-", "answer_type": "color"}, {"id": "color_grade-010", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "color_grade-011", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["complementary", "analogous", "independent"]}, {"id": "color_grade-012", "ir_path": "/visual/grade", "answer_type": "enum", "choices": ["natural", "warmed", "cooled", "stylised", "no-skin"]}, {"id": "color_grade-013", "ir_path": "/visual/grade", "answer_type": "object"}, {"id": "color_grade-014", "ir_path": "/visual/grade", "answer_type": "number"}, {"id": "color_grade-015", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "color_grade-016", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "color_grade-017", "ir_path": "/visual/grade", "answer_type": "boolean"}, {"id": "color_grade-018", "ir_path": "/visual/grade", "answer_type": "enum", "choices": ["high-key", "mid-key", "low-key"]}, {"id": "color_grade-019", "ir_path": "/visual/grade", "answer_type": "ratio"}, {"id": "color_grade-020", "ir_path": "/parameters/-", "answer_type": "enum", "choices": ["topic-derived", "fixed-brand", "mixed"]}, {"id": "color_grade-021", "ir_path": "/generation_rules/-", "answer_type": "integer"}, {"id": "color_grade-022", "ir_path": "/visual/grade", "answer_type": "segments"}, {"id": "color_grade-023", "ir_path": "/visual/grade", "answer_type": "boolean"}, {"id": "color_grade-024", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "color_grade-025", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "color_grade-026", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "color_grade-027", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "color_grade-028", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "color_grade-029", "ir_path": "/motion/transitions/-", "answer_type": "object"}, {"id": "color_grade-030", "ir_path": "/visual/grade", "answer_type": "enum", "choices": ["heavy-sharpening", "mild", "none"]}, {"id": "color_grade-031", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "color_grade-032", "ir_path": "/generation_rules/-", "answer_type": "boolean"}]
```
