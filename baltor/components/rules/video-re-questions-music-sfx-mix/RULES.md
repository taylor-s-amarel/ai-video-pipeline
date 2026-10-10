# Video RE question bank: Music, sound effects and mix

Lens `music_sfx_mix` · 30 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-music-sfx-mix` subagent and challenged by `video-re-challenger`.

Measures music presence, tempo, level under the voice, ducking, sound effects and loudness, and writes a mix recipe and a licence-safe music brief.

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
- `ratio`: {"value": r} with 0 <= r <= 1
- `seconds`: {"value": s, "unit": "s"} optionally with "min"/"max"
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `text`: one technique description, at most 300 characters, no copied content
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `segments`: [{"start_s": a, "end_s": b, "label": "..."}]
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- audio.integrated_lufs, audio.loudness_range (video_re_audio_loudness)
- audio.onsets_s, audio.tempo_bpm (video_re_onsets_beats)
- audio.speech_segments

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_music_presence`, `video_re_detect_ducking`, `video_re_detect_sfx_hits`, `video_re_detect_dynamics_compression`, `video_re_detect_stereo_width`, `video_re_detect_tempo_changes`, `video_re_detect_silence_gaps`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

A1 spectrograms (full band and highpassed), A3 momentary loudness, A5 side vs mid loudness for music under voice (stereo only), A6 RMS in speech gaps.

## Pitfalls challengers check first

- Naming a commercial track; never identify or reuse it
- Using side-channel loudness on a mono source
- Calling every onset a sound effect

## Parameters this lens usually proposes

- music_track (asset with licence)
- music_bpm (range)
- music_under_voice_db
- duck_db
- sfx_set (list)
- target_lufs

## IR paths this lens writes

- `/audio/integrated_lufs` (1)
- `/audio/music/coverage_ratio` (1)
- `/audio/music/duck_db` (1)
- `/audio/music/ending` (1)
- `/audio/music/fades` (1)
- `/audio/music/instrumentation` (1)
- `/audio/music/licence_status` (1)
- `/audio/music/loop_s` (1)
- `/audio/music/loudness_range` (1)
- `/audio/music/low_end_db` (1)
- `/audio/music/mood` (1)
- `/audio/music/per_beat_change` (1)
- `/audio/music/stereo_width` (1)
- `/audio/music/structure` (1)
- `/audio/music/tempo_bpm` (1)
- `/audio/music/true_peak_dbtp` (1)
- `/audio/music_under_voice_db` (1)
- `/audio/sfx/-` (5)
- `/generation_rules/-` (6)
- `/parameters/-` (1)
- `/render_binding/mapping/audio_format` (1)

## Questions (30)

### music_sfx_mix-001 · `ratio` → `/audio/music/coverage_ratio`

**Is there music, and what share of the runtime does it cover?**

- Why it matters: Fills music coverage.
- How to answer: A1 spectrograms in 5 s windows across the video (sustained tonal or rhythmic content); for stereo sources A5 side loudness above -50 LUFS also indicates music.
- Evidence required: A1 per window; A5
- Challenge: Ambience and room tone are not music; require tonal or rhythmic structure.

### music_sfx_mix-002 · `number` → `/audio/music/tempo_bpm`

**What is the music tempo in BPM?**

- Why it matters: Fills music tempo for beat-synced edits.
- How to answer: Read evidence.audio.tempo_bpm (video_re_onsets_beats); verify by counting onsets on an A1 spectrogram over 10 s.
- Evidence required: evidence.audio.tempo_bpm; A1
- Challenge: Tempo estimators often double or halve; check the manual count.

### music_sfx_mix-003 · `list` → `/audio/music/instrumentation`

**What is the instrumentation class (piano, acoustic guitar, strings or orchestral, synth pads, electronic beat, lo-fi, percussion only)?**

- Why it matters: Fills the music brief for licensed or original replacement music; never identifies the track.
- How to answer: Describe from A1 spectrograms (harmonic patterns, percussion transients) and frame-independent listening cues; method inferred.
- Evidence required: A1
- Challenge: Answers that name the track, artist or album are rejected.

### music_sfx_mix-004 · `number` → `/audio/music_under_voice_db`

**How many dB below the voice does the music sit during speech?**

- Why it matters: Fills music_under_voice_db (a common house target is about 18 dB).
- How to answer: Stereo: A5 side loudness versus mid loudness during speech segments (approximation). Otherwise compare A6 RMS in speech gaps (music only) with RMS during speech, noting the music level may change (ducking).
- Evidence required: A5; A6; evidence.audio.speech_segments
- Challenge: State the method; ducking makes the gap method overestimate music under voice.

### music_sfx_mix-005 · `number` → `/audio/music/duck_db`

**Is the music ducked under speech, and by how many dB?**

- Why it matters: Fills ducking depth.
- How to answer: A5 side loudness (or music band energy on A1) just before and during speech onsets at 4 points.
- Evidence required: A5; A1
- Challenge: Musical dynamics change on their own; check that drops align with speech onsets in most cases.

### music_sfx_mix-006 · `number` → `/audio/integrated_lufs`

**What is the integrated loudness of the whole mix?**

- Why it matters: Fills audio.integrated_lufs.
- How to answer: Read evidence.audio.integrated_lufs (video_re_audio_loudness).
- Evidence required: evidence.audio.integrated_lufs
- Challenge: Recompute with ffmpeg ebur128 summary if the value looks implausible.

### music_sfx_mix-007 · `number` → `/audio/music/loudness_range`

**What is the loudness range (LRA)?**

- Why it matters: Sets dynamic range target.
- How to answer: Read evidence.audio.loudness_range.
- Evidence required: evidence.audio.loudness_range
- Challenge: Recompute with ebur128 if missing.

### music_sfx_mix-008 · `number` → `/audio/music/true_peak_dbtp`

**What is the true peak, and is there clipping?**

- Why it matters: Sets a peak limit in the mix recipe.
- How to answer: ffmpeg -i SRC -af ebur128=peak=true -f null - (summary true peak); A2 waveform for flat tops.
- Evidence required: ebur128 true peak; A2
- Challenge: Lossy encoding can push true peak above 0; report the codec.

### music_sfx_mix-009 · `segments` → `/audio/music/structure`

**How does the music evolve (intro, build, drop at the hook or payoff, steady loop)?**

- Why it matters: Becomes a music structure rule aligned with beats.
- How to answer: A3 momentary loudness of the side channel (or full mix in gaps) over time; mark rises and drops with timestamps.
- Evidence required: A3; A5
- Challenge: Separate voice-driven loudness from music changes.

### music_sfx_mix-010 · `boolean` → `/audio/music/per_beat_change`

**Does the music change between beats (new track or section per item)?**

- Why it matters: Becomes a per-beat music rule.
- How to answer: A1 spectrograms at beat boundaries: changes in key, instrumentation or tempo.
- Evidence required: A1 at boundaries
- Challenge: Check 3 boundaries.

### music_sfx_mix-011 · `object` → `/audio/sfx/-`

**Which sound effect types occur (whoosh, pop, click, ding, riser, impact, typewriter, camera shutter, swoosh-up), with counts?**

- Why it matters: Fills audio.sfx.
- How to answer: A1 spectrograms with highpass=f=3000 at visual events (cuts, text pops); onsets not explained by music or speech.
- Evidence required: A1 highpassed; evidence.audio.onsets_s
- Challenge: Each type needs at least one timestamp; music percussion is not sfx.

### music_sfx_mix-012 · `number` → `/audio/sfx/-`

**How many sound effects per minute are used?**

- Why it matters: Sets sfx density.
- How to answer: Count from 011 / duration x 60.
- Evidence required: sfx timestamps
- Challenge: Report total count and duration.

### music_sfx_mix-013 · `ratio` → `/generation_rules/-`

**What share of sound effects align with a visual event (within 80 ms)?**

- Why it matters: Becomes an sfx sync rule.
- How to answer: Match sfx timestamps with cuts, text entrances and transitions.
- Evidence required: sfx timestamps; visual event times
- Challenge: Report the matching tolerance and chance rate.

### music_sfx_mix-014 · `enum` → `/audio/music/ending`

**How does the music end (ends on a final hit with the video, fades out, cut mid-phrase)?**

- Choices: `button-ending`, `fade-out`, `cut-mid-phrase`, `no-music-at-end`
- Why it matters: Fills music ending.
- How to answer: A1 and A3 over the last 3 s.
- Evidence required: A1; A3
- Challenge: Check whether the fade is in the music itself or applied in the mix (fade starts before content ends).

### music_sfx_mix-015 · `text` → `/audio/music/mood`

**What mood does the music support, described by measurable features (tempo, mode if apparent, density)?**

- Why it matters: Fills the music brief for replacement music.
- How to answer: Combine tempo (002), instrumentation (003) and loudness (009); mode (major/minor) only if clearly audible from harmonic content; method inferred.
- Evidence required: music answers
- Challenge: Mood words must be tied to features; 'epic' alone is taste.

### music_sfx_mix-016 · `timestamps` → `/generation_rules/-`

**Is silence used as emphasis (music cut out right before a reveal)?**

- Why it matters: Adds a pre-reveal silence rule.
- How to answer: A3 drops of over 10 LU lasting 0.2-1 s before payoff moments.
- Evidence required: A3; timeline beats
- Challenge: Each drop must be followed by a reveal within 1.5 s.

### music_sfx_mix-017 · `number` → `/audio/music/stereo_width`

**How wide is the music's stereo image (side/mid loudness ratio)?**

- Why it matters: Fills stereo width guidance.
- How to answer: A5 side versus mid loudness in music-only gaps.
- Evidence required: A5
- Challenge: Mono sources make this 0; check A7 channels.

### music_sfx_mix-018 · `number` → `/audio/music/low_end_db`

**How heavy is the low end (energy below 150 Hz relative to the full band)?**

- Why it matters: Guides music selection and EQ.
- How to answer: A6 RMS with lowpass=f=150 versus unfiltered, in music-only gaps.
- Evidence required: A6 filtered
- Challenge: Report both RMS values.

### music_sfx_mix-019 · `object` → `/audio/sfx/-`

**Are risers used before reveals, and how long are they?**

- Why it matters: Adds risers to the sfx plan.
- How to answer: A1: rising pitch or noise sweeps ending at reveals.
- Evidence required: A1
- Challenge: Report timestamps and lengths.

### music_sfx_mix-020 · `list` → `/audio/sfx/-`

**Are ambience beds used (ocean, crowd, wind, room) under the music or voice?**

- Why it matters: Adds an ambience layer.
- How to answer: A1: broadband noise textures consistent with the scene; F1 frames for the matching visual.
- Evidence required: A1; frames: F1
- Challenge: Encoder noise is not ambience.

### music_sfx_mix-021 · `seconds` → `/audio/music/loop_s`

**Does the music loop, and what is the loop length?**

- Why it matters: Fills loop length for music editing.
- How to answer: Compare A1 spectrogram patterns in successive windows for repetition.
- Evidence required: A1
- Challenge: Report the repeat points.

### music_sfx_mix-022 · `boolean` → `/generation_rules/-`

**Does the music mask the voice's intelligibility band (about 1-4 kHz) during speech?**

- Why it matters: Becomes an EQ rule (dip music in the voice band).
- How to answer: A1 during speech: music energy in 1-4 kHz relative to voice harmonics.
- Evidence required: A1
- Challenge: Inferred from images; confidence under 0.6.

### music_sfx_mix-023 · `rule` → `/generation_rules/-`

**Write the mix recipe (music level under voice, ducking, sfx level, target loudness, peak limit).**

- Why it matters: Gives the compiler a reproducible mix.
- How to answer: Combine 004, 005, 006 and 008, for example 'music -18 dB under voice; duck 6 dB with 150 ms attack; sfx peaks 6 dB under voice; master to {target_lufs} LUFS integrated, -1 dBTP'.
- Evidence required: mix answers
- Challenge: Every number must come from a measurement or be marked as a default.

### music_sfx_mix-024 · `list` → `/parameters/-`

**Which audio parameters should a new video set (music track asset with licence, bpm range, music under voice, sfx set, target LUFS)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect 002, 004, 006 and 011; the track is an asset slot that requires a licence field.
- Evidence required: mix answers
- Challenge: No parameter may point to the source's music.

### music_sfx_mix-025 · `object` → `/audio/music/fades`

**How long are audio fade-ins and fade-outs at the start and end?**

- Why it matters: Fills fade lengths.
- How to answer: A3 at the first and last 3 s.
- Evidence required: A3
- Challenge: Report ms for both.

### music_sfx_mix-026 · `ratio` → `/generation_rules/-`

**Do music downbeats or section changes coincide with item boundaries?**

- Why it matters: Becomes a music-to-structure alignment rule.
- How to answer: Compare A3 or onset clusters with beat boundaries; share within 1/8 beat.
- Evidence required: evidence.audio.onsets_s; timeline beats
- Challenge: Compare with chance.

### music_sfx_mix-027 · `object` → `/render_binding/mapping/audio_format`

**What are the audio stream facts (codec, sample rate, channels, bitrate)?**

- Why it matters: Fills render audio settings.
- How to answer: A7 stream info.
- Evidence required: A7
- Challenge: Copy values exactly from ffprobe.

### music_sfx_mix-028 · `boolean` → `/generation_rules/-`

**Do any sound effects peak louder than the voice?**

- Why it matters: Becomes an sfx level limit.
- How to answer: A6 RMS at sfx moments versus median speech RMS.
- Evidence required: A6
- Challenge: Report the levels.

### music_sfx_mix-029 · `boolean` → `/audio/sfx/-`

**Is there a sonic logo or jingle at the start or end?**

- Why it matters: Adds a sonic-logo slot a new series fills with its own sound.
- How to answer: A1 at the first and last 3 s for a short distinctive motif.
- Evidence required: A1
- Challenge: Never reuse the source's motif; the slot must be new.

### music_sfx_mix-030 · `enum` → `/audio/music/licence_status`

**Is the music a recognisable commercial track that cannot be reused?**

- Choices: `likely-commercial`, `likely-library`, `original-or-unknown`, `no-music`
- Why it matters: Sets the rights flag on the music slot.
- How to answer: Do not identify the track. Classify only by cues (vocals with lyrics, high production with distinctive hook) and mark inferred; in all cases the variant uses separately licensed or original music.
- Evidence required: A1
- Challenge: Any track name or artist in the answer is rejected.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"
- **A2** Waveform image: ffmpeg -v error -i "$SRC" -filter_complex "aformat=channel_layouts=mono,showwavespic=s=1800x300" -frames:v 1 "$WORK/wave.png"
- **A3** Momentary loudness every 100 ms (LUFS): ffmpeg -v error -i "$SRC" -af "ebur128=metadata=1,ametadata=mode=print:key=lavfi.r128.M:file=$WORK/lufs_m.txt" -f null -
- **A5** Side (L-R) channel loudness, which removes centre-panned voice and leaves most stereo music: replace the A3 filter with "pan=mono|c0=0.5*c0-0.5*c1,ebur128=metadata=1,ametadata=mode=print:key=lavfi.r128.M:file=$WORK/side_m.txt"; mid channel uses 0.5*c0+0.5*c1. Only meaningful for stereo sources.
- **A6** RMS level per 100 ms at 48 kHz: ffmpeg -v error -i "$SRC" -af "aresample=48000,asetnsamples=n=4800,astats=metadata=1:reset=1,ametadata=mode=print:key=lavfi.astats.Overall.RMS_level:file=$WORK/rms.txt" -f null -
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "music_sfx_mix-001", "ir_path": "/audio/music/coverage_ratio", "answer_type": "ratio"}, {"id": "music_sfx_mix-002", "ir_path": "/audio/music/tempo_bpm", "answer_type": "number"}, {"id": "music_sfx_mix-003", "ir_path": "/audio/music/instrumentation", "answer_type": "list"}, {"id": "music_sfx_mix-004", "ir_path": "/audio/music_under_voice_db", "answer_type": "number"}, {"id": "music_sfx_mix-005", "ir_path": "/audio/music/duck_db", "answer_type": "number"}, {"id": "music_sfx_mix-006", "ir_path": "/audio/integrated_lufs", "answer_type": "number"}, {"id": "music_sfx_mix-007", "ir_path": "/audio/music/loudness_range", "answer_type": "number"}, {"id": "music_sfx_mix-008", "ir_path": "/audio/music/true_peak_dbtp", "answer_type": "number"}, {"id": "music_sfx_mix-009", "ir_path": "/audio/music/structure", "answer_type": "segments"}, {"id": "music_sfx_mix-010", "ir_path": "/audio/music/per_beat_change", "answer_type": "boolean"}, {"id": "music_sfx_mix-011", "ir_path": "/audio/sfx/-", "answer_type": "object"}, {"id": "music_sfx_mix-012", "ir_path": "/audio/sfx/-", "answer_type": "number"}, {"id": "music_sfx_mix-013", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "music_sfx_mix-014", "ir_path": "/audio/music/ending", "answer_type": "enum", "choices": ["button-ending", "fade-out", "cut-mid-phrase", "no-music-at-end"]}, {"id": "music_sfx_mix-015", "ir_path": "/audio/music/mood", "answer_type": "text"}, {"id": "music_sfx_mix-016", "ir_path": "/generation_rules/-", "answer_type": "timestamps"}, {"id": "music_sfx_mix-017", "ir_path": "/audio/music/stereo_width", "answer_type": "number"}, {"id": "music_sfx_mix-018", "ir_path": "/audio/music/low_end_db", "answer_type": "number"}, {"id": "music_sfx_mix-019", "ir_path": "/audio/sfx/-", "answer_type": "object"}, {"id": "music_sfx_mix-020", "ir_path": "/audio/sfx/-", "answer_type": "list"}, {"id": "music_sfx_mix-021", "ir_path": "/audio/music/loop_s", "answer_type": "seconds"}, {"id": "music_sfx_mix-022", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "music_sfx_mix-023", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "music_sfx_mix-024", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "music_sfx_mix-025", "ir_path": "/audio/music/fades", "answer_type": "object"}, {"id": "music_sfx_mix-026", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "music_sfx_mix-027", "ir_path": "/render_binding/mapping/audio_format", "answer_type": "object"}, {"id": "music_sfx_mix-028", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "music_sfx_mix-029", "ir_path": "/audio/sfx/-", "answer_type": "boolean"}, {"id": "music_sfx_mix-030", "ir_path": "/audio/music/licence_status", "answer_type": "enum", "choices": ["likely-commercial", "likely-library", "original-or-unknown", "no-music"]}]
```
