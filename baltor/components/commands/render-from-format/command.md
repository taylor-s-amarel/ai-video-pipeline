---
description: "Render a new video from a lifted format IR and new content"
argument-hint: "<format_ir.json> <content.json | topic> [--out DIR]"
---

Render a new video from a lifted format: $ARGUMENTS

Arguments: `format_ir.json` (required) and either `content.json` (values for the IR's content parameters) or a
topic; optional `--out DIR`.

Boundary: The swarm lifts technique and structure only. Never store, transcribe or reuse the source's footage, frames, music, voice or script text. Keyframes and spectrograms are temporary analysis files in a scratch directory and are never copied into the format IR or a variant. On-screen text may be quoted only as a locating note in evidence.note, at most 6 words, and narration is never quoted. Patterns replace content words with slots, e.g. 'FACT {n}' or '{number} {unit} {noun}'. Analysing a public video for technique is fine; republishing its content is not. The render uses only new or licensed assets.

1. Read the IR: parameters, beats with their `content_slot`, generation rules and `render_binding`. List the
   content parameters that need values.
2. Content. With `content.json`, check every required content parameter is filled. With a topic, research
   facts with numbers and a source URL for each (the IR's `script.claims_need_sources`), write the script to
   the IR's word budgets and patterns, and pick licensed or original images, music and a local TTS voice.
   Never reuse the source's assets, words or voice.
3. Compile with `video_re_ir_compile_render_plan` (`.baltor/lib/video-re-ir-compile-render-plan/`, `--help` first) into a render plan bound to
   the `short_video_spec` contract schema; validate the plan against that schema.
4. Check the plan with the house-style skill's `scripts/check_rules.py` when the project uses it.
5. Render with the project's renderer (ffmpeg or the pipeline's composer), time captions from the narration's
   word timings and never time-stretch speech to fit.
6. QA the export with the `mp4_qa_probe` code module and fix failures before delivering.
7. Deliver the full MP4 with its render plan, sources and credits. Next: `/compare-formats` for the round trip.
