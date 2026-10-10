# Video RE question bank: Layers and compositing

Lens `layers_compositing` · 33 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-layers-compositing` subagent and challenged by `video-re-challenger`.

Reconstructs the layer stack back to front, opacity, blend, edges, masks and depth cues so the composite can be rebuilt from new assets.

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
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `layers`: array of IR layer objects (z, kind, opacity, optional blend, motion, feather_px, frame_coverage, source_slot)
- `parameter`: one IR parameter object (name, type, description, default, min/max or choices, derived_from)
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- overlay.semi_transparent_ratio (video_re_overlay_transparency_probe)
- shots[].motion_energy center vs border

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_layer_count_estimate`, `video_re_detect_semi_transparent_layers`, `video_re_detect_blend_mode_hint`, `video_re_detect_feathered_edges`, `video_re_detect_frosted_glass_panel`, `video_re_detect_drop_shadow`, `video_re_detect_vignette`, `video_re_detect_noise_grain`, `video_re_detect_light_leak_flare`, `video_re_detect_particles_overlay`, `video_re_detect_glow_bloom`, `video_re_detect_static_overlay_regions`, `video_re_detect_chromatic_aberration`, `video_re_detect_border_frame`, `video_re_detect_split_screen_layout`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F3 crops at panel and inset edges, F9 average colour inside a panel over two different backgrounds to estimate opacity, F2 bursts to see which layers move.

## Pitfalls challengers check first

- Calling a layer semi-transparent without seeing a background change through it
- Counting a texture baked into a photo as a separate layer
- Guessing blend modes; say 'unknown' unless the behaviour shows it

## Parameters this lens usually proposes

- n_layers
- max_layer_opacity
- panel_opacity
- feather_px
- overlay_set (list)

## IR paths this lens writes

- `/generation_rules/-` (7)
- `/parameters/-` (1)
- `/render_binding/mapping/margins_px` (1)
- `/visual/layers` (4)
- `/visual/layers/*/blend` (1)
- `/visual/layers/*/feather_px` (1)
- `/visual/layers/*/motion` (1)
- `/visual/layers/*/opacity` (3)
- `/visual/layers/*/source_slot` (1)
- `/visual/layers/-` (12)
- `/visual/style_family` (1)

## Questions (33)

### layers_compositing-001 · `integer` → `/visual/layers`

**How many distinct visual layers are stacked in a typical item shot?**

- Why it matters: Sets n_layers and checks a layered-look requirement.
- How to answer: On F1 frames from 3 item shots, list separable elements back to front (background, grid or texture, light, particles, photo, panel, text, vignette); confirm separate layers by different motion on an F2 burst.
- Evidence required: frames: F1 in 3 item shots; frames: F2 bursts
- Challenge: Elements that never move independently and have no transparency could be one baked image; require a motion or opacity cue per counted layer.

### layers_compositing-002 · `layers` → `/visual/layers`

**What is the layer stack from back to front, with each layer's kind?**

- Why it matters: Fills visual.layers, the core of the composite recipe.
- How to answer: Order layers by occlusion: whatever covers another is above it. Use F3 crops where elements overlap.
- Evidence required: frames: F1 samples; frames: F3 overlap crops
- Challenge: Check each ordering claim at one overlap crop; a layer above text must actually cover text.

### layers_compositing-003 · `layers` → `/visual/layers/*/opacity`

**Which layers are semi-transparent, and what is each one's estimated opacity?**

- Why it matters: Fills opacity per layer; a common rule caps every layer below 100%.
- How to answer: Sample a layer's colour (F9) at the same spot over two different underlying backgrounds; with known background colours B1, B2 and observed O1, O2, opacity a = 1 - (O1 - O2)/(B1 - B2) per channel. Report per layer.
- Evidence required: frames: F9 samples over two backgrounds; evidence.overlay.semi_transparent_ratio
- Challenge: If the background did not change under the layer, opacity cannot be measured; method must drop to observed or inferred.

### layers_compositing-004 · `ratio` → `/visual/layers/*/opacity`

**What does the overlay transparency probe report, and does frame inspection agree?**

- Why it matters: Ties the measured semi_transparent_ratio to specific layers.
- How to answer: Read evidence.overlay.semi_transparent_ratio (video_re_overlay_transparency_probe); compare with the layers judged semi-transparent in 003.
- Evidence required: evidence.overlay.semi_transparent_ratio
- Challenge: Read the probe's definition before interpreting the ratio; never treat it as an opacity value.

### layers_compositing-005 · `layers` → `/visual/layers/*/blend`

**Which blend modes are visible (screen-like brightening, multiply-like darkening, overlay contrast, plain alpha)?**

- Why it matters: Fills blend per layer.
- How to answer: For light, haze and texture layers, check whether dark areas stay dark under them (screen/add) or light areas stay light (multiply), on F3 crops.
- Evidence required: frames: F3 crops of light and texture layers
- Challenge: Anything not demonstrated by such a test must be 'unknown'.

### layers_compositing-006 · `list` → `/generation_rules/-`

**How is depth implied (blur on far layers, scale difference, parallax, drop shadows, haze, overlap)?**

- Why it matters: Becomes depth rules for the compositor.
- How to answer: List cues seen on F1 frames and F2 bursts, each with a timestamp.
- Evidence required: frames: F1 and F2
- Challenge: Each cue needs a timestamp where it is visible.

### layers_compositing-007 · `enum` → `/generation_rules/-`

**How are the edges of inset media treated (feathered, hard, rounded, stroked, shadowed)?**

- Choices: `feathered`, `hard`, `rounded`, `stroked`, `shadowed`, `mixed`
- Why it matters: Fills edge treatment; hard rectangular cut-outs are a known failure in this project.
- How to answer: F3 enlarged crops at the edges of the main photo in 3 shots.
- Evidence required: frames: F3 edge crops
- Challenge: Check all four edges in one shot; feathering only at the bottom is a gradient mask, not a feather.

### layers_compositing-008 · `number` → `/visual/layers/*/feather_px`

**How wide is the feather (soft edge) in pixels at full resolution?**

- Why it matters: Fills feather_px.
- How to answer: On an F3 crop across an edge, count pixels from where the photo starts to fade to where the background is fully visible.
- Evidence required: frames: F3 edge crops at full resolution
- Challenge: Measure on two edges; report both values.

### layers_compositing-009 · `object` → `/visual/layers/-`

**Is there a frosted or blurred panel behind text, and how strong are its blur and tint?**

- Why it matters: Adds a frosted-panel layer with parameters.
- How to answer: F3 crop of the panel: blurred background detail visible through it indicates frosted glass; estimate tint opacity with the method from 003.
- Evidence required: frames: F3 panel crops; frames: F9
- Challenge: A solid plate has no visible background detail; check over a busy background.

### layers_compositing-010 · `enum` → `/visual/layers/-`

**How is the frame filled when media does not cover it (blurred copy, gradient, solid colour, pattern)?**

- Choices: `blurred-copy`, `gradient`, `solid`, `pattern`, `video`, `not-needed`
- Why it matters: Becomes the fill strategy.
- How to answer: Inspect the areas outside the main media on F1 frames.
- Evidence required: frames: F1 samples
- Challenge: Make sure the fill is not a separate background system (answered by that lens).

### layers_compositing-011 · `number` → `/visual/layers/-`

**Is there a vignette, and how much darker are the corners than the centre?**

- Why it matters: Adds a vignette layer with strength.
- How to answer: F9 average colour of a 5% corner crop versus the central 20% on a frame with even content; report the luma ratio.
- Evidence required: frames: F9 corner and centre
- Challenge: Content that is naturally dark at the edges can fake a vignette; check two different shots.

### layers_compositing-012 · `object` → `/visual/layers/-`

**Is there a grain or noise overlay, and is it static or animated?**

- Why it matters: Adds a grain layer.
- How to answer: F3 crop of a flat area enlarged 4x on two consecutive frames (F8); animated grain changes per frame.
- Evidence required: frames: F3 and F8 on a flat region
- Challenge: Compression noise is blocky and follows macroblocks; true grain is fine and uniform.

### layers_compositing-013 · `timestamps` → `/visual/layers/-`

**Are light leaks, flares or light sweeps overlaid, and how often?**

- Why it matters: Adds a light layer with frequency.
- How to answer: Find warm or bright moving patches not tied to scene content on F2 bursts; list timestamps.
- Evidence required: frames: F2 bursts
- Challenge: A real sun flare in footage is not an overlay; it must also cover graphics or text-only frames.

### layers_compositing-014 · `object` → `/visual/layers/-`

**Is there a particle, dust or bokeh layer, and how dense and fast is it?**

- Why it matters: Adds a particles layer.
- How to answer: F2 bursts on a darker region; count particles per frame and estimate drift speed.
- Evidence required: frames: F2 bursts
- Challenge: Report a count; 'some particles' is not an answer.

### layers_compositing-015 · `boolean` → `/generation_rules/-`

**Is any visual layer fully opaque over the whole frame for more than a second?**

- Why it matters: Checks the opacity cap rule; full-frame opaque layers hide the background system.
- How to answer: Look for frames where nothing from the background shows through (F1); check border motion (F5) during those times.
- Evidence required: frames: F1; F5 on borders
- Challenge: Full-bleed photos are opaque by nature; say whether the format places them full-frame.

### layers_compositing-016 · `object` → `/generation_rules/-`

**Do cut-out subjects or panels cast drop shadows, and what are the offset and blur?**

- Why it matters: Adds shadow parameters.
- How to answer: F3 crop under a cut-out; measure shadow offset and blur radius in px.
- Evidence required: frames: F3 shadow crops
- Challenge: Report px values; a 'soft shadow' alone is incomplete.

### layers_compositing-017 · `enum` → `/visual/layers/*/source_slot`

**Are subjects cut out from their backgrounds or shown as rectangular images?**

- Choices: `cut-out`, `rectangular`, `both`
- Why it matters: Decides whether background removal is part of the pipeline.
- How to answer: Inspect subject edges on F3 crops.
- Evidence required: frames: F3
- Challenge: Feathered rectangles are not cut-outs; cut-outs follow the subject's outline.

### layers_compositing-018 · `list` → `/visual/layers/-`

**What mask shapes are used (circle, rounded rectangle, gradient fade, custom shape)?**

- Why it matters: Adds mask types to the layer recipe.
- How to answer: Inspect inset media and reveals on F1 and F3.
- Evidence required: frames: F1 and F3
- Challenge: List one timestamp per mask type.

### layers_compositing-019 · `object` → `/generation_rules/-`

**Does the number or type of layers change between beats (for example more overlays in the hook)?**

- Why it matters: Becomes a per-beat layer rule.
- How to answer: Repeat the layer count (001) on hook, item and outro frames.
- Evidence required: frames: F1 per beat role
- Challenge: Count per beat role, not per shot.

### layers_compositing-020 · `object` → `/visual/layers/-`

**Are there colour tint overlays (a solid colour at low opacity over everything)?**

- Why it matters: Adds a tint layer and its colour.
- How to answer: Compare neutral elements (white text, grey areas) for a uniform colour shift using F9.
- Evidence required: frames: F9 on neutral elements
- Challenge: A grade and a tint overlay look similar; a tint also affects text drawn above the grade only if it sits above the text.

### layers_compositing-021 · `object` → `/visual/layers/-`

**Is there a grid of moving panels (for example 2x2) behind or around the main visual?**

- Why it matters: Adds a grid-2x2 layer kind.
- How to answer: Look for repeated rectangles with independent motion on F2 bursts.
- Evidence required: frames: F2 bursts
- Challenge: Static grid lines belong to a grid layer, not a panel grid; check that panels move independently.

### layers_compositing-022 · `boolean` → `/visual/layers/-`

**Is there glow or bloom around bright elements or text?**

- Why it matters: Adds a glow effect.
- How to answer: F3 crop around bright text; a halo of raised brightness beyond the stroke indicates glow.
- Evidence required: frames: F3
- Challenge: Compression ringing produces thin halos; glow is wider (several px) and smooth.

### layers_compositing-023 · `list` → `/generation_rules/-`

**What compositing artefacts appear (halo edges, aliasing, hard rectangular patches, banding) that a rebuild must avoid?**

- Why it matters: Becomes negative rules (things the compositor must not do).
- How to answer: Inspect F3 crops at edges and gradients; list artefacts with timestamps.
- Evidence required: frames: F3
- Challenge: Every artefact needs a timestamp and region.

### layers_compositing-024 · `layers` → `/visual/layers/*/motion`

**Which layers move during a shot and which are static?**

- Why it matters: Fills motion per layer.
- How to answer: Compare F2 burst frames: elements whose position or content changes move.
- Evidence required: frames: F2 bursts
- Challenge: Camera moves move everything; describe per-layer motion relative to the frame.

### layers_compositing-025 · `boolean` → `/visual/layers`

**Does any text sit behind a subject (subject occludes text) for a depth effect?**

- Why it matters: Adds an occlusion option to the layer order.
- How to answer: Look for frames where part of the title or label is covered by a subject's outline (F3).
- Evidence required: frames: F3
- Challenge: Text cropped by a panel edge is not occlusion by a subject.

### layers_compositing-026 · `object` → `/visual/layers/-`

**Are there border or frame layers (film frame, polaroid, phone mock-up, outline)?**

- Why it matters: Adds a border layer.
- How to answer: Inspect frame edges and inset media on F1.
- Evidence required: frames: F1
- Challenge: Say whether the frame is constant or changes per item.

### layers_compositing-027 · `object` → `/generation_rules/-`

**Which layers are fixed for the whole video and which change per item (slots)?**

- Why it matters: Separates template layers from content layers for the parameteriser.
- How to answer: Compare the layer list (002) across items.
- Evidence required: layer lists per item
- Challenge: A layer whose asset changes but whose style stays is a slot, not fixed.

### layers_compositing-028 · `parameter` → `/parameters/-`

**What should max_layer_opacity and n_layers be as parameters, with ranges from the evidence?**

- Why it matters: Turns observed values into parameters.
- How to answer: Use the maximum observed opacity (003) and the layer count range across beats (019).
- Evidence required: layer answers
- Challenge: The parameter default must equal an observed value.

### layers_compositing-029 · `ratio` → `/visual/layers/*/opacity`

**What is the estimated opacity of text backing panels?**

- Why it matters: Fills panel opacity for captions and titles.
- How to answer: Apply the two-background method from 003 to the caption panel at two times with different underlying images.
- Evidence required: frames: F9 panel samples at two times
- Challenge: If the panel is blurred (frosted), the blur changes the underlying colour; sample flat areas.

### layers_compositing-030 · `object` → `/render_binding/mapping/margins_px`

**Do layers align to consistent margins (for example all insets 64 px from the frame edge)?**

- Why it matters: Adds margin constants to the render binding.
- How to answer: Measure insets' distances to the frame edges on 4 frames.
- Evidence required: frames: F1
- Challenge: Report measured px; consistency needs at most 2% spread.

### layers_compositing-031 · `boolean` → `/visual/style_family`

**Is the composite built as 2.5D (layers separated in depth with perspective or scale by depth)?**

- Why it matters: Selects a 2.5D compositor or plain 2D stacking.
- How to answer: Look for layers that scale or shift differently during moves (F1 start/end) and for perspective distortion.
- Evidence required: frames: F1 start/end
- Challenge: Independent animations are not depth; depth needs a consistent relation between scale and motion.

### layers_compositing-032 · `timestamps` → `/visual/layers/-`

**Are chromatic aberration, RGB split or scanline overlays used, and where?**

- Why it matters: Adds stylised overlay effects.
- How to answer: F3 crops at high-contrast edges for colour fringes; F2 bursts for flicker.
- Evidence required: frames: F3; frames: F2
- Challenge: Lens fringing in footage is not an effect; it must also appear on graphics.

### layers_compositing-033 · `enum` → `/visual/layers`

**Do overlays (light, particles, grain) sit above or below the text?**

- Choices: `above-text`, `below-text`, `mixed`
- Why it matters: Fixes the z-order of overlays relative to text.
- How to answer: Check whether overlay elements cross over letters on F3 crops.
- Evidence required: frames: F3 text crops
- Challenge: Find one frame where an overlay element and a letter overlap; without it the answer is not determinable.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F5** Per-frame motion in a region (mean absolute frame difference, 0-255): ffmpeg -v error -i "$SRC" -vf "crop=iw:ih*0.15:0:0,tblend=all_mode=difference,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=$WORK/diff.txt" -an -f null -  (drop the crop for the full frame)
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F9** Average colour of a region: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y,scale=1:1:flags=area,format=rgb24" -f rawvideo - | od -An -tu1

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "layers_compositing-001", "ir_path": "/visual/layers", "answer_type": "integer"}, {"id": "layers_compositing-002", "ir_path": "/visual/layers", "answer_type": "layers"}, {"id": "layers_compositing-003", "ir_path": "/visual/layers/*/opacity", "answer_type": "layers"}, {"id": "layers_compositing-004", "ir_path": "/visual/layers/*/opacity", "answer_type": "ratio"}, {"id": "layers_compositing-005", "ir_path": "/visual/layers/*/blend", "answer_type": "layers"}, {"id": "layers_compositing-006", "ir_path": "/generation_rules/-", "answer_type": "list"}, {"id": "layers_compositing-007", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["feathered", "hard", "rounded", "stroked", "shadowed", "mixed"]}, {"id": "layers_compositing-008", "ir_path": "/visual/layers/*/feather_px", "answer_type": "number"}, {"id": "layers_compositing-009", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "layers_compositing-010", "ir_path": "/visual/layers/-", "answer_type": "enum", "choices": ["blurred-copy", "gradient", "solid", "pattern", "video", "not-needed"]}, {"id": "layers_compositing-011", "ir_path": "/visual/layers/-", "answer_type": "number"}, {"id": "layers_compositing-012", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "layers_compositing-013", "ir_path": "/visual/layers/-", "answer_type": "timestamps"}, {"id": "layers_compositing-014", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "layers_compositing-015", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "layers_compositing-016", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "layers_compositing-017", "ir_path": "/visual/layers/*/source_slot", "answer_type": "enum", "choices": ["cut-out", "rectangular", "both"]}, {"id": "layers_compositing-018", "ir_path": "/visual/layers/-", "answer_type": "list"}, {"id": "layers_compositing-019", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "layers_compositing-020", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "layers_compositing-021", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "layers_compositing-022", "ir_path": "/visual/layers/-", "answer_type": "boolean"}, {"id": "layers_compositing-023", "ir_path": "/generation_rules/-", "answer_type": "list"}, {"id": "layers_compositing-024", "ir_path": "/visual/layers/*/motion", "answer_type": "layers"}, {"id": "layers_compositing-025", "ir_path": "/visual/layers", "answer_type": "boolean"}, {"id": "layers_compositing-026", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "layers_compositing-027", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "layers_compositing-028", "ir_path": "/parameters/-", "answer_type": "parameter"}, {"id": "layers_compositing-029", "ir_path": "/visual/layers/*/opacity", "answer_type": "ratio"}, {"id": "layers_compositing-030", "ir_path": "/render_binding/mapping/margins_px", "answer_type": "object"}, {"id": "layers_compositing-031", "ir_path": "/visual/style_family", "answer_type": "boolean"}, {"id": "layers_compositing-032", "ir_path": "/visual/layers/-", "answer_type": "timestamps"}, {"id": "layers_compositing-033", "ir_path": "/visual/layers", "answer_type": "enum", "choices": ["above-text", "below-text", "mixed"]}]
```
