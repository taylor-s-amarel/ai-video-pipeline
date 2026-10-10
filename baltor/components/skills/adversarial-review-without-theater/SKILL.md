---
name: "adversarial-review-without-theater"
description: "Use before a substantial render and again on the exact final encode of an animation or video, or after a material camera, rig, sound, caption, factual or rights change. Runs a bounded pass of the owner's 1,024-question adversarial review bank with explicit evidence states, hashed evidence and a list of what was not checked; never a rubber stamp."
---

# Adversarial review without checklist theater

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), "Adversarial review without checklist theater" and Appendix E. The guide's section is in
`references/guide-section.md` verbatim.

## What the bank is, and is not

The final bank contains 1,024 authored questions in 32 domains, with nine defined passes. It is a searchable
diagnostic resource, not 1,024 people, audience responses, completed tests, or production capabilities. Applicability
depends on the feature and evidence, not on a tag alone. Technical completeness, a long runtime, and a large question
bank do not establish watchability.

## When to run it

1. **Planning pass** on the brief, storyboard and source state. Final-pixel and listening questions remain `untested`
   or `blocked` here.
2. **Final pass** on the exact final encode: hash the delivered bytes; never review pre-encode frames in its place.
3. **Targeted pass** after a material camera, rig, sound, caption, factual or rights change: recheck the changed beat
   and neighbouring beats.
4. **Stop** after the bounded pass and necessary repairs. Do not execute every question to manufacture impressive totals.

## Choose a pass

| Pass | Purpose | Questions | Areas |
|---|---|---:|---|
| `default_32` | General triage | 32 | D001, D002, D003, D004, D005, D006, D007, D008, D009, D010, D011, D012, D013, D014, D015, D016, D017, D018, D019, D020, D021, D022, D023, D024, D025, D026, D027, D028, D029, D030, D031, D032 |
| `visual_depth_contact` | Visual depth and contact | 64 | D002, D003, D004, D005, D006, D007, D009, D015 |
| `performance_motion` | Acting, motion and weight | 64 | D005, D006, D007, D008, D013, D014, D016, D017 |
| `story_edit` | Story, pacing and transitions | 64 | D001, D005, D008, D016, D017, D018, D019, D030 |
| `sound` | Music, voice, effects and synchronization | 64 | D022, D023, D024, D025 |
| `accessible_text` | Text and accessible delivery | 50 | D002, D003, D020, D021, D029 |
| `factual_puzzle` | Facts, algorithms and fair puzzles | 60 | D004, D016, D026, D027, D030, D031 |
| `final_delivery` | Rights, encode, delivery and reopening | 56 | D015, D016, D021, D026, D028, D029, D032 |
| `longer_cardboard_32` | Longer cardboard comedy | 32 | D001, D002, D003, D004, D005, D006, D007, D008, D009, D010, D011, D012, D013, D014, D016, D017, D018, D020, D021, D023, D025 |

For a deep look at one area, use that area's lens subagent (below). The default pass takes one question per area.

## Evidence states

- `untested`: insufficient observation to answer the question; the default.
- `observed-pass`: exact evidence supports a bounded statement for this target.
- `observed-fail`: matching direct evidence shows a defect.
- `blocked`: the check applies, but required access or evidence is missing.
- `not-applicable`: the relevant feature is absent, with a stated reason.

Use `demonstrated_defect` only with an observed failure. Use `potential_improvement` for a design hypothesis that still
needs comparison.

## What evidence must carry

Real evidence includes its own hash, the target movie hash, the extraction or observation method, locator, coverage,
and limitations. These fail validation: nonfinite numbers, absent intervals, stale target hashes and unsupported
claimed coverage. Do not retarget a contact sheet to a changed movie by editing its label. Do not mark a
listening-only question passed using a waveform statistic.

The guide's own record (an `adversarial_review_result` instance):

```json
{
  "question_id": "AVQ-006-002",
  "target_artifact": "final.mp4",
  "target_sha256": "COMPUTED_FINAL_HASH",
  "status": "untested",
  "finding_type": "none",
  "review_mode": "visual",
  "scope": {
    "start_frame": null,
    "end_frame": null,
    "coverage": "not_observed"
  },
  "evidence": [],
  "rationale": "Awaiting matching encoded interval",
  "required_recheck_after": [
    "rig_change",
    "prop_attachment_change",
    "camera_change"
  ]
}
```

## No theater: the working rules

- **No rubber-stamping.** `observed-pass` needs exact evidence for this target; anything else stays `untested`,
  `blocked` or `not-applicable` with its reason.
- **Measure.** Decode the actual file, probe it, hash it; quote values and frame numbers rather than impressions.
- **Cite.** Every finding names its locator (frame range, timestamp, file) and evidence hash.
- **Say what was not checked.** The report lists every untested and blocked question and why; a count of passes is
  never the headline.
- **Rank by the viewer.** Order findings by impact on the intended viewer task; separate taste from objective error
  and from measured audience results.
- **Listen for real.** Listening questions need an actual listening pass of the final audio. Synthetic critique is
  not audience validation.
- **Respect the viewer's verdict.** A viewer may dislike a story despite all measured technical gates passing; this
  is meaningful feedback and should guide the next story, not be dismissed by the checklist.

## Tools in this catalogue

| Id | Area | Question bank (rules) | Lens (subagent) |
|---|---|---|---|
| D001 | concept and design | `review_bank_concept_and_design` | `review_lens_concept_and_design` |
| D002 | composition and hierarchy | `review_bank_composition_and_hierarchy` | `review_lens_composition_and_hierarchy` |
| D003 | foreground background separation | `review_bank_foreground_background_separation` | `review_lens_foreground_background_separation` |
| D004 | depth and occlusion | `review_bank_depth_and_occlusion` | `review_lens_depth_and_occlusion` |
| D005 | staging and blocking | `review_bank_staging_and_blocking` | `review_lens_staging_and_blocking` |
| D006 | contact and props | `review_bank_contact_and_props` | `review_lens_contact_and_props` |
| D007 | silhouette and anatomy | `review_bank_silhouette_and_anatomy` | `review_lens_silhouette_and_anatomy` |
| D008 | acting and expression | `review_bank_acting_and_expression` | `review_lens_acting_and_expression` |
| D009 | camera and projection | `review_bank_camera_and_projection` | `review_lens_camera_and_projection` |
| D010 | lighting and shadows | `review_bank_lighting_and_shadows` | `review_lens_lighting_and_shadows` |
| D011 | color and materials | `review_bank_color_and_materials` | `review_lens_color_and_materials` |
| D012 | texture and detail | `review_bank_texture_and_detail` | `review_lens_texture_and_detail` |
| D013 | motion and easing | `review_bank_motion_and_easing` | `review_lens_motion_and_easing` |
| D014 | physics and weight | `review_bank_physics_and_weight` | `review_lens_physics_and_weight` |
| D015 | layers and compositing | `review_bank_layers_and_compositing` | `review_lens_layers_and_compositing` |
| D016 | continuity and state | `review_bank_continuity_and_state` | `review_lens_continuity_and_state` |
| D017 | pacing and holds | `review_bank_pacing_and_holds` | `review_lens_pacing_and_holds` |
| D018 | story setup payoff | `review_bank_story_setup_payoff` | `review_lens_story_setup_payoff` |
| D019 | transitions and editing | `review_bank_transitions_and_editing` | `review_lens_transitions_and_editing` |
| D020 | text typography | `review_bank_text_typography` | `review_lens_text_typography` |
| D021 | captions and accessibility | `review_bank_captions_and_accessibility` | `review_lens_captions_and_accessibility` |
| D022 | music composition | `review_bank_music_composition` | `review_lens_music_composition` |
| D023 | voice and dialogue | `review_bank_voice_and_dialogue` | `review_lens_voice_and_dialogue` |
| D024 | sfx and mix | `review_bank_sfx_and_mix` | `review_lens_sfx_and_mix` |
| D025 | audio visual timing | `review_bank_audio_visual_timing` | `review_lens_audio_visual_timing` |
| D026 | rights and asset provenance | `review_bank_rights_and_asset_provenance` | `review_lens_rights_and_asset_provenance` |
| D027 | factual and algorithmic integrity | `review_bank_factual_and_algorithmic_integrity` | `review_lens_factual_and_algorithmic_integrity` |
| D028 | rendering and export | `review_bank_rendering_and_export` | `review_lens_rendering_and_export` |
| D029 | decoding and delivery | `review_bank_decoding_and_delivery` | `review_lens_decoding_and_delivery` |
| D030 | audience value | `review_bank_audience_value` | `review_lens_audience_value` |
| D031 | puzzles and fairness | `review_bank_puzzles_and_fairness` | `review_lens_puzzles_and_fairness` |
| D032 | reproducibility and maintenance | `review_bank_reproducibility_and_maintenance` | `review_lens_reproducibility_and_maintenance` |

- `review_bank_index`: areas, counts and the nine passes with exact ordered ids.
- `adversarial_question` and `adversarial_review_result`: the record contracts.
- `adversarial_review_kit`: `select` a pass, `plan` honest starting records, `validate` results against the target
  hash, `summary` of statuses and what was not checked.

```bash
python3 adversarial_review_kit.py plan --bank .baltor/rules --pass default_32 --target final.mp4 \
  --stage final-encode --modes visual,machine > review.json
# ...observe, then update records with evidence...
python3 adversarial_review_kit.py validate review.json --bank .baltor/rules --target final.mp4
```

## What has been observed with this method (the guide's record; do not generalise)

The earlier focused film application contains 17 scoped records: eleven observed passes, four untested potential
improvements, and two audio blockers. The validator suite reports 39 passing regression tests. Three contact-sheet
lineages were reproduced from exact MP4s, with matching byte or pixel evidence. Those results protect the review
contract; they do not establish that the whole films were watched continuously or listened to independently.
