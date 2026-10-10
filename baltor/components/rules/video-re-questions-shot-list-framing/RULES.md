# Video RE question bank: Shot list and framing

Lens `shot_list_framing` · 33 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-shot-list-framing` subagent and challenged by `video-re-challenger`.

Describes what kinds of shots and visual assets appear, how large the subject is, where negative space is left for text, and what an author must supply per item.

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
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[].keyframe (video_re_keyframes_contact_sheet)
- shots[].palette
- text_regions[]

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_classify_shot_scale`, `video_re_classify_flat_vs_photographic`, `video_re_classify_face_presence`, `video_re_classify_map_chart_graphics`, `video_re_detect_foreground_subject_mask`, `video_re_detect_aspect_reframe`, `video_re_detect_picture_in_picture`, `video_re_detect_split_screen_layout`, `video_re_detect_true_resolution`, `video_re_detect_rounded_corners`, `video_re_similarity_perceptual_hash`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

One F1 frame per shot (or the keyframe), F3 crops to judge sharpness, F10 to find reused images.

## Pitfalls challengers check first

- Labelling shot scale on a still graphic with no subject
- Assuming a source is stock footage from look alone
- Missing reused images because they are zoomed differently

## Parameters this lens usually proposes

- assets_per_item (integer)
- hero_asset_aspect (enum)
- min_asset_px (integer)
- shot_scale_sequence (list)

## IR paths this lens writes

- `/generation_rules/-` (10)
- `/motion/transitions/-` (1)
- `/parameters/-` (2)
- `/render_binding/mapping/layout_grid` (1)
- `/timeline/beats/*/content_slot` (2)
- `/visual/layers/*/frame_coverage` (1)
- `/visual/layers/-` (5)
- `/visual/style_family` (2)
- `/visual/subject_framing` (9)

## Questions (33)

### shot_list_framing-001 · `object` → `/visual/subject_framing`

**What is the distribution of shot types (extreme close-up, close-up, medium, wide, insert/detail, screen capture, graphic-only card)?**

- Why it matters: Fills subject_framing and the shot mix the renderer plans.
- How to answer: Classify each shot keyframe (evidence.shots[].keyframe or F4 sheet) into one type; report counts and shares.
- Evidence required: evidence.shots[].keyframe; frames: F4
- Challenge: Re-classify 6 random shots blind; disagreements over one step of scale are tolerable, two steps are not.

### shot_list_framing-002 · `ratio` → `/visual/subject_framing`

**How large is the main subject as a fraction of frame height, median across shots?**

- Why it matters: Sets subject scale for asset placement.
- How to answer: On 8 sampled keyframes measure the subject's bounding box height in pixels / source.height.
- Evidence required: evidence.shots[].keyframe; evidence.source.height
- Challenge: Shots without a clear subject must be excluded and counted in the note.

### shot_list_framing-003 · `enum` → `/visual/subject_framing`

**Is the subject placed centrally, on a rule-of-thirds line, or offset toward one side?**

- Choices: `centre`, `thirds`, `offset-left`, `offset-right`, `varies`
- Why it matters: Becomes the subject placement rule.
- How to answer: Measure the subject centre x/width ratio on sampled keyframes.
- Evidence required: evidence.shots[].keyframe
- Challenge: Report the measured x ratios; 'centre' needs most within 0.42-0.58.

### shot_list_framing-004 · `distribution` → `/visual/subject_framing`

**How much headroom is left above faces or main subjects (gap above as a fraction of frame height)?**

- Why it matters: Reveals where space is left for titles in vertical framing.
- How to answer: On keyframes with a face or subject, measure top of subject to top of frame / height.
- Evidence required: evidence.shots[].keyframe
- Challenge: Check whether headroom is consistently occupied by the title; if so, say so.

### shot_list_framing-005 · `enum` → `/generation_rules/-`

**Are source images and clips shown full-bleed, inset with margins, letterboxed, or on a blurred fill?**

- Choices: `full-bleed`, `inset-margins`, `letterboxed`, `blurred-fill`, `mixed`
- Why it matters: Decides how assets of the wrong aspect are placed.
- How to answer: Inspect F1 frames per shot type; look for bars, margins or a blurred copy around the media.
- Evidence required: frames: F1 samples
- Challenge: A blurred fill can look like a background video; check whether it mirrors the foreground.

### shot_list_framing-006 · `ratio` → `/visual/layers/*/frame_coverage`

**What fraction of the frame width does the main photo or clip occupy?**

- Why it matters: Fills frame_coverage of the main visual layer (a common house constraint is at least 80%).
- How to answer: Measure the main media's left and right edges on F1 frames in 5 shots; width / source.width.
- Evidence required: frames: F1 in 5 shots; evidence.source.width
- Challenge: Feathered edges make the boundary soft; measure where opacity visibly reaches half.

### shot_list_framing-007 · `list` → `/visual/style_family`

**What kinds of visual material appear (filmed footage, photographs, screen recordings, illustrations, 3D renders, generated images, charts, maps)?**

- Why it matters: Fills style_family and the asset types an author must source.
- How to answer: Classify each keyframe; list kinds with counts.
- Evidence required: evidence.shots[].keyframe
- Challenge: Label 'generated images' only with a visible cue and mark it inferred; never as fact from style alone.

### shot_list_framing-008 · `integer` → `/timeline/beats/*/content_slot`

**How many distinct visual assets are used per item beat (median)?**

- Why it matters: Sets assets_per_item for the content slot.
- How to answer: Within each item, group shots whose keyframes have SSIM above 0.7 (F10) as one asset; count groups.
- Evidence required: evidence.shots[].keyframe; frames: F10; item beat boundaries
- Challenge: A zoomed crop of the same photo is one asset; check grouping by eye on one item.

### shot_list_framing-009 · `ratio` → `/visual/layers/-`

**Is there an on-camera presenter or talking head, and what share of runtime is it on screen?**

- Why it matters: Decides whether the format needs a presenter slot or a character layer.
- How to answer: Mark shots showing a person speaking to camera (mouth movement on F2 bursts aligned with speech); sum their durations / duration.
- Evidence required: evidence.shots[]; frames: F2 bursts; evidence.audio.speech_segments
- Challenge: Do not identify the person; answers containing identity are rejected.

### shot_list_framing-010 · `ratio` → `/generation_rules/-`

**Does shot scale alternate between consecutive shots (wide then close, close then wide)?**

- Why it matters: Becomes a scale alternation rule.
- How to answer: Using the shot types from 001, count consecutive pairs that change scale by at least one step.
- Evidence required: shot type sequence
- Challenge: Graphic cards have no scale; exclude them from pairs.

### shot_list_framing-011 · `ratio` → `/generation_rules/-`

**What share of factual claims are illustrated by a dedicated visual (B-roll that shows the thing being said)?**

- Why it matters: Sets how literally visuals follow the script.
- How to answer: For 10 sampled caption cards, check whether the concurrent frame (F1) depicts the claim's subject.
- Evidence required: evidence.captions[] (analysis only); frames: F1 at sampled captions
- Challenge: This is a judgement; method must be observed with the sample listed.

### shot_list_framing-012 · `enum` → `/visual/subject_framing`

**Where does the framing leave negative space for text (top band, bottom band, side, none)?**

- Choices: `top`, `bottom`, `top-and-bottom`, `side`, `none`
- Why it matters: Couples framing with typography placement.
- How to answer: Overlay evidence.text_regions[] bboxes on sampled frames mentally or with drawbox; check if text sits on low-detail areas.
- Evidence required: evidence.text_regions[]; frames: F1 samples
- Challenge: If text sits over the subject (a deliberate style), the answer is 'none'.

### shot_list_framing-013 · `enum` → `/generation_rules/-`

**Does the subject's gaze or direction of movement point toward the text or away from it?**

- Choices: `toward-text`, `away-from-text`, `neutral`, `mixed`
- Why it matters: A layout rule for composing subject and text.
- How to answer: On keyframes with faces or moving subjects, compare gaze or motion direction with the text position.
- Evidence required: evidence.shots[].keyframe; evidence.text_regions[]
- Challenge: Fewer than 4 qualifying shots means not determinable.

### shot_list_framing-014 · `integer` → `/generation_rules/-`

**How many images or clips are reused in more than one beat?**

- Why it matters: Tells the generator whether reuse is allowed (asset budget).
- How to answer: Pairwise F10 SSIM between keyframes from different beats; count pairs above 0.8 that are the same asset.
- Evidence required: evidence.shots[].keyframe; frames: F10
- Challenge: Template backgrounds produce high SSIM; compare the foreground region only (F3 crop) for flagged pairs.

### shot_list_framing-015 · `enum` → `/visual/subject_framing`

**Do backgrounds behind subjects look optically or synthetically blurred (shallow depth of field)?**

- Choices: `shallow-optical`, `synthetic-blur`, `deep-focus`, `mixed`
- Why it matters: Adds a depth cue to the layer recipe.
- How to answer: F3 crops at subject edges: optical blur grows gradually with depth; synthetic blur shows a hard cut-out halo.
- Evidence required: frames: F3 edge crops
- Challenge: Compression smearing is not blur; compare with a sharp region in the same frame.

### shot_list_framing-016 · `enum` → `/visual/layers/-`

**Are horizontal sources fitted into the vertical frame by recropping, by blurred fill bars, or by stacking?**

- Choices: `recrop`, `blurred-fill`, `stacked`, `not-applicable`
- Why it matters: Defines the aspect adapter step in the render plan.
- How to answer: Find shots where content aspect differs from the frame (F1); classify the method.
- Evidence required: frames: F1 samples
- Challenge: Native vertical footage gives not-applicable; do not infer from one shot.

### shot_list_framing-017 · `object` → `/visual/layers/-`

**How many diagrams, charts or maps appear, and are they built in-video (animated) or static images?**

- Why it matters: Adds chart or map layer kinds and their build method.
- How to answer: Mark keyframes with diagrams; inspect F2 bursts to see whether elements animate on.
- Evidence required: evidence.shots[].keyframe; frames: F2 at diagram shots
- Challenge: A photo of a chart is not an animated chart; check for element-level motion.

### shot_list_framing-018 · `enum` → `/visual/subject_framing`

**What camera angle dominates (eye level, high angle, low angle, top-down, mixed)?**

- Choices: `eye-level`, `high`, `low`, `top-down`, `mixed`
- Why it matters: Becomes an angle preference for asset selection or 3D rendering.
- How to answer: Classify sampled keyframes by apparent camera angle.
- Evidence required: evidence.shots[].keyframe
- Challenge: Graphics and flat illustrations have no angle; exclude them.

### shot_list_framing-019 · `boolean` → `/generation_rules/-`

**Does each item open with a wide or establishing shot before closer shots?**

- Why it matters: Becomes an item shot-order rule.
- How to answer: Compare the scale of the first shot of each item with its later shots.
- Evidence required: shot type sequence; item beat boundaries
- Challenge: Require at least two thirds of items to follow it.

### shot_list_framing-020 · `boolean` → `/generation_rules/-`

**Are close-ups or tight crops used at the moments key numbers are revealed?**

- Why it matters: Becomes a 'tighten on reveal' rule.
- How to answer: At each key-number appearance (text_regions in the label or number area), compare shot scale with the item median.
- Evidence required: evidence.text_regions[]; shot types
- Challenge: If numbers appear on graphic cards, the question does not apply; answer not determinable.

### shot_list_framing-021 · `object` → `/visual/layers/-`

**Do inset media have borders, rounded corners, drop shadows or device frames?**

- Why it matters: Adds border or frame layers to the stack.
- How to answer: F3 crops at inset corners; measure corner radius and border width in px.
- Evidence required: frames: F3 corner crops
- Challenge: Report px measurements; 'rounded' without a radius is incomplete.

### shot_list_framing-022 · `ratio` → `/visual/layers/-`

**How often are picture-in-picture or split-screen layouts used (share of runtime)?**

- Why it matters: Decides whether the compiler needs a multi-panel layout.
- How to answer: Sum durations of shots with two or more media panels (F1); divide by duration.
- Evidence required: evidence.shots[]; frames: F1
- Challenge: Decorative background grids are not picture-in-picture.

### shot_list_framing-023 · `integer` → `/parameters/-`

**What minimum pixel width must a source asset have to fill the main visual slot without visible upscaling?**

- Why it matters: Sets min_asset_px for asset sourcing.
- How to answer: Main visual width in px (006) times the maximum zoom factor seen (camera lens answers or first/last frame comparison).
- Evidence required: main visual width; camera zoom
- Challenge: Check one zoomed shot on an F3 crop for softness that shows the source was already upscaled.

### shot_list_framing-024 · `list` → `/timeline/beats/*/content_slot`

**What shot slots does one item need (for example hero image, detail crop, context wide, number card)?**

- Why it matters: Defines the per-item shot list template.
- How to answer: From items, list the recurring shot roles in order; keep roles present in at least two thirds of items.
- Evidence required: shot types per item
- Challenge: Test the list on one item not used to build it.

### shot_list_framing-025 · `number` → `/generation_rules/-`

**How consistent is subject scale across items (standard deviation of subject height ratio)?**

- Why it matters: Tells the generator whether to normalise subject size.
- How to answer: Using 002 measurements grouped by item, report the stdev of per-item medians.
- Evidence required: subject size measurements
- Challenge: Report the number of items measured.

### shot_list_framing-026 · `ratio` → `/visual/subject_framing`

**What share of shots contain people (any visible person)?**

- Why it matters: Shapes asset sourcing and rights needs (model releases).
- How to answer: Count keyframes with a visible person; divide by shot count.
- Evidence required: evidence.shots[].keyframe
- Challenge: Do not describe or identify people; count only.

### shot_list_framing-027 · `object` → `/visual/subject_framing`

**Are any shots tilted (dutch angle) or rotated in the frame?**

- Why it matters: Adds rotation as a framing device.
- How to answer: Inspect keyframes for non-level horizons or rotated insets; measure the angle on F3 crops.
- Evidence required: frames: F3
- Challenge: Rotation from a camera move belongs to the camera lens; check whether the angle changes over the shot.

### shot_list_framing-028 · `timestamps` → `/motion/transitions/-`

**Are shot changes matched on shape, colour or position (match cuts)?**

- Why it matters: Adds match cuts to the editing toolbox.
- How to answer: For each cut, compare the subject position and dominant colour of adjacent frames (F1 before/after, F9 colours); list matches.
- Evidence required: frames: F1 around cuts; F9
- Challenge: Coincidental similarity is common in template videos; require deliberate alignment of the main subject.

### shot_list_framing-029 · `enum` → `/generation_rules/-`

**Is the main subject ever cropped by the frame edge, and is that systematic (tight crops) or accidental?**

- Choices: `never`, `systematic-tight`, `occasional-accidental`
- Why it matters: Becomes a crop policy.
- How to answer: Count keyframes where the subject touches or exceeds a frame edge.
- Evidence required: evidence.shots[].keyframe
- Challenge: Report the count and total shots inspected.

### shot_list_framing-030 · `ratio` → `/visual/style_family`

**What share of shots are pure graphics (no photographic or filmed content)?**

- Why it matters: Sets the mix between sourced media and generated graphics.
- How to answer: Count graphic-only keyframes / total.
- Evidence required: evidence.shots[].keyframe
- Challenge: A photo with heavy overlays is not a pure graphic.

### shot_list_framing-031 · `list` → `/parameters/-`

**Which visual asset parameters must the author supply per item, with type and aspect (for example hero_image: asset, 9:16 or wider, at least 1600 px)?**

- Why it matters: Feeds the parameteriser with asset slots.
- How to answer: Combine 008, 023 and 024 into typed asset parameters.
- Evidence required: shot list answers
- Challenge: Every asset parameter needs a min size and aspect backed by a measurement.

### shot_list_framing-032 · `rule` → `/generation_rules/-`

**What rule picks the hero visual for an item (shows the subject named in the label, shows the key number's object, shows a person reacting)?**

- Why it matters: Gives the asset search step a selection rule.
- How to answer: For each item, compare the hero shot content with the item's label or key number (F1 plus F3 label crop).
- Evidence required: frames: F1 item heroes; frames: F3 labels
- Challenge: Check the rule against every item; exceptions must be listed.

### shot_list_framing-033 · `object` → `/render_binding/mapping/layout_grid`

**Is the frame divided by a consistent layout grid (fixed margins or columns that media and text align to)?**

- Why it matters: Adds a layout grid to the render binding.
- How to answer: Measure left and right edges of media and text across 6 frames; report repeated x positions within 1% of width.
- Evidence required: frames: F1 samples; evidence.text_regions[]
- Challenge: Centred elements always share an axis; require a shared edge, not just centring.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F4** Whole-video contact sheet, 1 frame per second: ffmpeg -v error -i "$SRC" -vf "fps=1,scale=180:-2,tile=8x8" -frames:v 1 "$WORK/sheet.jpg" (or use the keyframes and contact sheet from video_re_keyframes_contact_sheet)
- **F9** Average colour of a region: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y,scale=1:1:flags=area,format=rgb24" -f rawvideo - | od -An -tu1
- **F10** Similarity of two frames (SSIM, 1.0 = identical): ffmpeg -i a.jpg -i b.jpg -lavfi "[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "shot_list_framing-001", "ir_path": "/visual/subject_framing", "answer_type": "object"}, {"id": "shot_list_framing-002", "ir_path": "/visual/subject_framing", "answer_type": "ratio"}, {"id": "shot_list_framing-003", "ir_path": "/visual/subject_framing", "answer_type": "enum", "choices": ["centre", "thirds", "offset-left", "offset-right", "varies"]}, {"id": "shot_list_framing-004", "ir_path": "/visual/subject_framing", "answer_type": "distribution"}, {"id": "shot_list_framing-005", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["full-bleed", "inset-margins", "letterboxed", "blurred-fill", "mixed"]}, {"id": "shot_list_framing-006", "ir_path": "/visual/layers/*/frame_coverage", "answer_type": "ratio"}, {"id": "shot_list_framing-007", "ir_path": "/visual/style_family", "answer_type": "list"}, {"id": "shot_list_framing-008", "ir_path": "/timeline/beats/*/content_slot", "answer_type": "integer"}, {"id": "shot_list_framing-009", "ir_path": "/visual/layers/-", "answer_type": "ratio"}, {"id": "shot_list_framing-010", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "shot_list_framing-011", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "shot_list_framing-012", "ir_path": "/visual/subject_framing", "answer_type": "enum", "choices": ["top", "bottom", "top-and-bottom", "side", "none"]}, {"id": "shot_list_framing-013", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["toward-text", "away-from-text", "neutral", "mixed"]}, {"id": "shot_list_framing-014", "ir_path": "/generation_rules/-", "answer_type": "integer"}, {"id": "shot_list_framing-015", "ir_path": "/visual/subject_framing", "answer_type": "enum", "choices": ["shallow-optical", "synthetic-blur", "deep-focus", "mixed"]}, {"id": "shot_list_framing-016", "ir_path": "/visual/layers/-", "answer_type": "enum", "choices": ["recrop", "blurred-fill", "stacked", "not-applicable"]}, {"id": "shot_list_framing-017", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "shot_list_framing-018", "ir_path": "/visual/subject_framing", "answer_type": "enum", "choices": ["eye-level", "high", "low", "top-down", "mixed"]}, {"id": "shot_list_framing-019", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "shot_list_framing-020", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "shot_list_framing-021", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "shot_list_framing-022", "ir_path": "/visual/layers/-", "answer_type": "ratio"}, {"id": "shot_list_framing-023", "ir_path": "/parameters/-", "answer_type": "integer"}, {"id": "shot_list_framing-024", "ir_path": "/timeline/beats/*/content_slot", "answer_type": "list"}, {"id": "shot_list_framing-025", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "shot_list_framing-026", "ir_path": "/visual/subject_framing", "answer_type": "ratio"}, {"id": "shot_list_framing-027", "ir_path": "/visual/subject_framing", "answer_type": "object"}, {"id": "shot_list_framing-028", "ir_path": "/motion/transitions/-", "answer_type": "timestamps"}, {"id": "shot_list_framing-029", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["never", "systematic-tight", "occasional-accidental"]}, {"id": "shot_list_framing-030", "ir_path": "/visual/style_family", "answer_type": "ratio"}, {"id": "shot_list_framing-031", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "shot_list_framing-032", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "shot_list_framing-033", "ir_path": "/render_binding/mapping/layout_grid", "answer_type": "object"}]
```
