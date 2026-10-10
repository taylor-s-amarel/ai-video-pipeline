# Video RE question bank: Rights and originality boundary

Lens `rights_originality_boundary` · 30 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-rights-originality-boundary` subagent and challenged by `video-re-challenger`.

Separates reusable technique from protected content, lists the asset slots that need new licensed material, and blocks anything that should not be lifted.

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

- `integer`: {"value": n}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `text`: one technique description, at most 300 characters, no copied content
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- source.reference
- text_regions[] (watermarks, logos)
- captions[] (analysis only)
- all other analysts' answers

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_static_overlay_regions`, `video_re_classify_face_presence`, `video_re_similarity_reuse_risk`, `video_re_similarity_perceptual_hash`, `video_re_similarity_audio_fingerprint`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F1 frames at corners for watermarks and broadcaster marks; F4 sheet for logos, faces and characters; read the other lenses' answers for copied text.

## Pitfalls challengers check first

- Giving legal conclusions; flag risks and say what needs a human or licence check
- Identifying people or tracks by name
- Letting a distinctive series name or character into the reusable format

## Parameters this lens usually proposes

- asset slots with licence fields
- series_name (string, must be new)
- music_track (asset)
- voice (licensed or synthetic, never cloned)

## IR paths this lens writes

- `/audio/music/replacement_brief` (1)
- `/audio/music/slot_requirements` (1)
- `/audio/narration/clone_forbidden` (1)
- `/generation_rules/-` (4)
- `/open_questions/-` (17)
- `/parameters/-` (1)
- `/script/claims_need_sources` (1)
- `/source/platform` (1)
- `/source/reference` (1)
- `/source/rights_note` (1)
- `/typography/title/font_licence_check` (1)

## Questions (30)

### rights_originality_boundary-001 · `text` → `/source/rights_note`

**What exactly may be reused from this video (techniques and structure) and what must not be (footage, frames, music, voice, script text, characters, series identity)?**

- Why it matters: Fills source.rights_note, which every downstream step reads.
- How to answer: Write one note listing reusable technique categories found by the other lenses and the excluded content categories present in this video.
- Evidence required: all lens answers; frames: F4
- Challenge: The note must exclude every content category actually present; check against the contact sheet.

### rights_originality_boundary-002 · `timestamps` → `/open_questions/-`

**Does the video contain third-party footage or images (stock, film or TV clips, news footage, other creators' clips), judging by visible cues?**

- Why it matters: Flags content that a variant must replace with its own licensed assets.
- How to answer: Look for broadcaster bugs, stock watermarks, different creators' overlays, letterboxed film frames on F1 and F3 crops; list timestamps. Method observed or inferred, never a legal conclusion.
- Evidence required: frames: F1; frames: F3 corners
- Challenge: Reject any answer that asserts infringement; it may only flag cues for a human.

### rights_originality_boundary-003 · `object` → `/audio/music/slot_requirements`

**What must the music slot require in any variant (new original or licensed music, licence field, attribution when the licence needs it, never the source track)?**

- Why it matters: Locks the music slot to new licensed or original music regardless of the source.
- How to answer: Write {source_music_reusable: false, licence_required: true, attribution_when_cc_by: true, cues: [...]} where cues lists observations from music_sfx_mix-030 (lyrics, production cues) without naming any track.
- Evidence required: music lens answers
- Challenge: Any suggestion to reuse, sample or remix the source music is rejected.

### rights_originality_boundary-004 · `boolean` → `/audio/narration/clone_forbidden`

**Is the voice a real, identifiable person's voice that must not be cloned or imitated?**

- Why it matters: Locks the voice slot to licensed or synthetic voices that do not imitate the source speaker.
- How to answer: If narration_voice-002 says human or mixed, set true. Never describe who it is.
- Evidence required: narration lens answers
- Challenge: Even if the voice sounds synthetic, cloning or imitating it is not allowed; the answer should still forbid imitation.

### rights_originality_boundary-005 · `integer` → `/open_questions/-`

**Are identifiable people shown (faces, names on screen)?**

- Why it matters: Flags that people imagery must not be reused and that variants need their own releases or licences.
- How to answer: Count shots with clearly visible faces or name captions (F4); do not identify anyone.
- Evidence required: frames: F4
- Challenge: Any identification of a person is rejected.

### rights_originality_boundary-006 · `timestamps` → `/open_questions/-`

**Are logos, brand marks or trademarks visible?**

- Why it matters: Flags marks that must not appear in variants unless the new content has rights to them.
- How to answer: F3 crops where logos appear; record position and timestamp, not the brand name unless needed to describe the risk.
- Evidence required: frames: F3
- Challenge: Product shots incidental to a fact are still flagged.

### rights_originality_boundary-007 · `list` → `/generation_rules/-`

**Does the on-screen text contain distinctive catchphrases or slogans that must not be copied?**

- Why it matters: Prevents distinctive phrasing from leaking into templates.
- How to answer: Review text crops and the pattern answers from other lenses; flag any pattern that preserves distinctive words.
- Evidence required: frames: F3; pattern answers from other lenses
- Challenge: Check every 'pattern' answer in the swarm output for surviving content words.

### rights_originality_boundary-008 · `boolean` → `/generation_rules/-`

**Are there distinctive characters or mascots whose design is the creator's own?**

- Why it matters: Prevents character designs from being copied; the format keeps only the rig type.
- How to answer: From characters_animation_style answers and F4.
- Evidence required: frames: F4; character answers
- Challenge: A generic stick figure is a technique; a named mascot with a recognisable design is not reusable.

### rights_originality_boundary-009 · `object` → `/source/platform`

**Are watermarks or creator credits burned into the video?**

- Why it matters: Records marks to exclude and helps attribute the analysis.
- How to answer: F3 corner crops at 3 times.
- Evidence required: frames: F3
- Challenge: Record position and kind only.

### rights_originality_boundary-010 · `rule` → `/generation_rules/-`

**Which elements together form the source's distinctive identity (series name, signature colour plus layout plus label, recurring character) and should be varied by default in new videos?**

- Why it matters: Becomes a rule that variants change at least some identity elements so they are not confusable with the source.
- How to answer: List combinations of title colour, layout, label pattern and naming that together identify the source; propose which parameter defaults must differ.
- Evidence required: typography, hook and structure answers
- Challenge: The rule must name parameters, and the IR defaults must actually differ from the source where the rule says so.

### rights_originality_boundary-011 · `boolean` → `/script/claims_need_sources`

**Which kinds of factual claims in the source must be re-researched (not copied) for a variant?**

- Why it matters: Sets claims_need_sources and stops facts being copied without checking.
- How to answer: From script_rhetoric-029, list claim types; facts in the source are never treated as verified.
- Evidence required: script answers
- Challenge: For any factual format, false is rejected.

### rights_originality_boundary-012 · `list` → `/open_questions/-`

**Does the topic involve health, finance, legal or safety advice that needs a higher verification bar?**

- Why it matters: Adds a verification requirement to the format.
- How to answer: Classify the topic from captions (analysis only).
- Evidence required: evidence.captions[] (analysis only)
- Challenge: If present even once, it must be listed.

### rights_originality_boundary-013 · `boolean` → `/open_questions/-`

**Does the video show minors?**

- Why it matters: Flags heightened care; minors' images are never reused and variants should avoid depicting identifiable minors without consent.
- How to answer: F4 contact sheet; count only, no descriptions.
- Evidence required: frames: F4
- Challenge: No descriptions of the people are allowed.

### rights_originality_boundary-014 · `boolean` → `/open_questions/-`

**Does the video depict dangerous activities that a variant could encourage?**

- Why it matters: Adds a safety review requirement.
- How to answer: F4 and captions.
- Evidence required: frames: F4; evidence.captions[] (analysis only)
- Challenge: Give timestamps if true.

### rights_originality_boundary-015 · `list` → `/open_questions/-`

**Will variants built from this format need an AI-content disclosure (synthetic voices, generated people or realistic generated scenes)?**

- Why it matters: Adds a disclosure check; platform rules change, so the answer points to the current policy.
- How to answer: Based on the format's slots (voice, imagery) say which would be synthetic; mark 'check the platform's current policy' rather than stating it.
- Evidence required: parameter list
- Challenge: Any policy statement without a dated source is rejected.

### rights_originality_boundary-016 · `list` → `/parameters/-`

**Which IR parameters are asset slots that need a licence field (images, footage, music, voice, fonts)?**

- Why it matters: Makes the render step demand licences for every asset.
- How to answer: Scan the proposed parameters for asset types.
- Evidence required: parameter proposals
- Challenge: Every asset parameter must be listed.

### rights_originality_boundary-017 · `list` → `/open_questions/-`

**Do any swarm answers quote more than 6 words of source text or quote narration at all?**

- Why it matters: Self-check that the IR stays free of source script text.
- How to answer: Scan all answer values and notes for quoted strings; count words; report offending answer ids.
- Evidence required: all answers
- Challenge: Run the scan again on the merged IR; any hit blocks the lift.

### rights_originality_boundary-018 · `list` → `/open_questions/-`

**Do any answers or IR fields reference source frames, clips or audio files as assets for reuse?**

- Why it matters: Ensures keyframes stay analysis-only.
- How to answer: Scan for file paths or URLs pointing at extracted frames or source media in parameter defaults and source_slot fields.
- Evidence required: all answers
- Challenge: Any hit blocks the lift until replaced with an empty asset slot.

### rights_originality_boundary-019 · `text` → `/open_questions/-`

**How was the source obtained (user-supplied file, user's own upload, public URL), and does the user confirm they may analyse it locally?**

- Why it matters: Records provenance; the swarm analyses but never republishes.
- How to answer: Read the run inputs; if unknown, add an open question for the user.
- Evidence required: run inputs; evidence.source.reference
- Challenge: Do not assume permission; if unknown, keep the open question.

### rights_originality_boundary-020 · `text` → `/source/reference`

**Is the source reference (URL or file name and analysis date) recorded?**

- Why it matters: Fills source.reference for traceability.
- How to answer: Copy evidence.source.reference and the run date.
- Evidence required: evidence.source.reference
- Challenge: Must match the evidence bundle exactly.

### rights_originality_boundary-021 · `enum` → `/open_questions/-`

**Does the format depend on other people's content (reactions, compilations, duets), so variants would need licensed sources?**

- Choices: `original-content-format`, `depends-on-third-party-content`, `mixed`
- Why it matters: Flags formats that cannot be rebuilt from original or licensed assets alone.
- How to answer: From shot_list_framing-007 and 002 above.
- Evidence required: shot list answers
- Challenge: Compilation formats must be flagged even if every clip looks freely available.

### rights_originality_boundary-022 · `timestamps` → `/open_questions/-`

**Are there quotes from people shown or read in the video?**

- Why it matters: Quotes need their own sourcing in variants and are never copied.
- How to answer: Captions and text crops with quotation marks or attribution (analysis only).
- Evidence required: evidence.captions[] (analysis only); frames: F3
- Challenge: Never reproduce the quote.

### rights_originality_boundary-023 · `timestamps` → `/open_questions/-`

**Is sensitive personal information visible (addresses, licence plates, phone numbers, private screens)?**

- Why it matters: Prevents carrying such content into notes or the IR.
- How to answer: F3 crops at suspicious frames; report only timestamps and kind.
- Evidence required: frames: F3
- Challenge: The information itself must never be written down.

### rights_originality_boundary-024 · `list` → `/open_questions/-`

**Could numbers or facts in the source be wrong or outdated?**

- Why it matters: Reinforces that variants re-research facts.
- How to answer: Flag claim types with dates or fast-changing values; method inferred.
- Evidence required: script answers
- Challenge: This lens does not fact-check; it only flags.

### rights_originality_boundary-025 · `object` → `/audio/music/replacement_brief`

**What brief should replacement music follow (tempo, instrumentation, mood, length) so it fits without copying?**

- Why it matters: Fills the music replacement brief.
- How to answer: From music lens answers; never name or describe a melody that could be reproduced.
- Evidence required: music answers
- Challenge: Reject descriptions specific enough to recreate the source melody.

### rights_originality_boundary-026 · `text` → `/typography/title/font_licence_check`

**Is the title or caption font likely a commercial font, and what open-licence font class should replace it?**

- Why it matters: Prevents unlicensed font use in renders.
- How to answer: From typography answers; propose an open font class (for example a geometric sans under the SIL Open Font License) and mark the source font as unknown.
- Evidence required: typography answers
- Challenge: Do not claim to identify the source font.

### rights_originality_boundary-027 · `boolean` → `/open_questions/-`

**Is there any reason this video should not be lifted at all (hateful, deceptive, harassing, or targeting a private person)?**

- Why it matters: A stop gate before lifting.
- How to answer: Review the contact sheet and captions (analysis only).
- Evidence required: frames: F4; evidence.captions[] (analysis only)
- Challenge: If true, the lift must stop and the reason must be reported.

### rights_originality_boundary-028 · `timestamps` → `/open_questions/-`

**Are there archival or news images with visible rights notices or agency credits?**

- Why it matters: Flags images that need licences in variants.
- How to answer: F3 crops near image edges.
- Evidence required: frames: F3
- Challenge: Record the kind of credit only.

### rights_originality_boundary-029 · `list` → `/generation_rules/-`

**Does the parameterised format still contain any source-specific value (exact title text, exact colour plus layout combination, series name) as a default?**

- Why it matters: Final check before the format is saved to the library.
- How to answer: Compare parameter defaults with observed source values flagged in 010.
- Evidence required: parameter defaults; identity elements
- Challenge: Any default equal to a source identity element must change or be justified as generic.

### rights_originality_boundary-030 · `list` → `/open_questions/-`

**Which open questions about rights must a human answer before a variant is published?**

- Why it matters: Collects the human review list.
- How to answer: Gather all open_questions from this lens into a short checklist.
- Evidence required: rights answers
- Challenge: Every flagged item above must appear.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F4** Whole-video contact sheet, 1 frame per second: ffmpeg -v error -i "$SRC" -vf "fps=1,scale=180:-2,tile=8x8" -frames:v 1 "$WORK/sheet.jpg" (or use the keyframes and contact sheet from video_re_keyframes_contact_sheet)

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "rights_originality_boundary-001", "ir_path": "/source/rights_note", "answer_type": "text"}, {"id": "rights_originality_boundary-002", "ir_path": "/open_questions/-", "answer_type": "timestamps"}, {"id": "rights_originality_boundary-003", "ir_path": "/audio/music/slot_requirements", "answer_type": "object"}, {"id": "rights_originality_boundary-004", "ir_path": "/audio/narration/clone_forbidden", "answer_type": "boolean"}, {"id": "rights_originality_boundary-005", "ir_path": "/open_questions/-", "answer_type": "integer"}, {"id": "rights_originality_boundary-006", "ir_path": "/open_questions/-", "answer_type": "timestamps"}, {"id": "rights_originality_boundary-007", "ir_path": "/generation_rules/-", "answer_type": "list"}, {"id": "rights_originality_boundary-008", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "rights_originality_boundary-009", "ir_path": "/source/platform", "answer_type": "object"}, {"id": "rights_originality_boundary-010", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "rights_originality_boundary-011", "ir_path": "/script/claims_need_sources", "answer_type": "boolean"}, {"id": "rights_originality_boundary-012", "ir_path": "/open_questions/-", "answer_type": "list"}, {"id": "rights_originality_boundary-013", "ir_path": "/open_questions/-", "answer_type": "boolean"}, {"id": "rights_originality_boundary-014", "ir_path": "/open_questions/-", "answer_type": "boolean"}, {"id": "rights_originality_boundary-015", "ir_path": "/open_questions/-", "answer_type": "list"}, {"id": "rights_originality_boundary-016", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "rights_originality_boundary-017", "ir_path": "/open_questions/-", "answer_type": "list"}, {"id": "rights_originality_boundary-018", "ir_path": "/open_questions/-", "answer_type": "list"}, {"id": "rights_originality_boundary-019", "ir_path": "/open_questions/-", "answer_type": "text"}, {"id": "rights_originality_boundary-020", "ir_path": "/source/reference", "answer_type": "text"}, {"id": "rights_originality_boundary-021", "ir_path": "/open_questions/-", "answer_type": "enum", "choices": ["original-content-format", "depends-on-third-party-content", "mixed"]}, {"id": "rights_originality_boundary-022", "ir_path": "/open_questions/-", "answer_type": "timestamps"}, {"id": "rights_originality_boundary-023", "ir_path": "/open_questions/-", "answer_type": "timestamps"}, {"id": "rights_originality_boundary-024", "ir_path": "/open_questions/-", "answer_type": "list"}, {"id": "rights_originality_boundary-025", "ir_path": "/audio/music/replacement_brief", "answer_type": "object"}, {"id": "rights_originality_boundary-026", "ir_path": "/typography/title/font_licence_check", "answer_type": "text"}, {"id": "rights_originality_boundary-027", "ir_path": "/open_questions/-", "answer_type": "boolean"}, {"id": "rights_originality_boundary-028", "ir_path": "/open_questions/-", "answer_type": "timestamps"}, {"id": "rights_originality_boundary-029", "ir_path": "/generation_rules/-", "answer_type": "list"}, {"id": "rights_originality_boundary-030", "ir_path": "/open_questions/-", "answer_type": "list"}]
```
