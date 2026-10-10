---
description: "Lift a format IR from an existing evidence bundle"
argument-hint: "<evidence.json> [answers dir] [--src VIDEO] [--out DIR]"
---

Lift a reusable format from an existing evidence bundle: $ARGUMENTS

Arguments: `evidence.json` (required); optional answers directory with `<lens>.json` files already produced;
`--src VIDEO` for analysts that need frame extraction; `--out DIR` (default: next to evidence.json).

Boundary: The swarm lifts technique and structure only. Never store, transcribe or reuse the source's footage, frames, music, voice or script text. Keyframes and spectrograms are temporary analysis files in a scratch directory and are never copied into the format IR or a variant. On-screen text may be quoted only as a locating note in evidence.note, at most 6 words, and narration is never quoted. Patterns replace content words with slots, e.g. 'FACT {n}' or '{number} {unit} {noun}'. Analysing a public video for technique is fine; republishing its content is not.

1. Read evidence.json and its `errors[]`. Without `--src`, tell each analyst that recipes needing the video are
   unavailable, so those questions become "not determinable" rather than guesses.
2. Run the analysts whose answer files are missing (`video-re-analyst-structure-beats`, `video-re-analyst-hook-first-seconds`, `video-re-analyst-script-rhetoric`, `video-re-analyst-pacing-cut-rhythm`, `video-re-analyst-shot-list-framing`, `video-re-analyst-camera-motion`, `video-re-analyst-layers-compositing`, `video-re-analyst-background-system`, `video-re-analyst-typography-captions`, `video-re-analyst-text-animation`, `video-re-analyst-color-grade`, `video-re-analyst-characters-animation-style`, `video-re-analyst-transitions-effects`, `video-re-analyst-narration-voice`, `video-re-analyst-music-sfx-mix`, `video-re-analyst-retention-cta`, `video-re-analyst-platform-fit-safe-areas`, `video-re-analyst-rights-originality-boundary`), in parallel.
3. Run `video-re-challenger` per lens, then the cross-lens pass.
4. Run `video-re-lifter`, then `video-re-parameteriser`; validate with `video_re_ir_validate`.
5. Report what changed against any earlier `format_ir.json` in `--out` (parameters, rules, open questions).
