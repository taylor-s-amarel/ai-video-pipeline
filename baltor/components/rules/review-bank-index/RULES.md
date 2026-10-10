# Adversarial review bank index: 32 areas, 1,024 questions, nine passes

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

The final bank contains 1,024 authored questions in 32 domains, with nine defined passes. It is a searchable
diagnostic resource, not 1,024 people, audience responses, completed tests, or production capabilities. A default
pass selects 32 questions. Domain-specific passes contain 50–64 questions; the longer-cardboard pass selects 32.
Applicability depends on the feature and evidence, not on a tag alone.

- Use this bank as a menu, not a requirement to review every question on every film. Each entry keeps its stable ID, question, failure hypothesis, practical check/fix, severity and modality/stage filters. The evidence contract in the main guide applies to every entry. Tags are candidate filters; they cannot make an irrelevant question applicable or turn missing evidence into a pass. Detailed machine-readable records remain in the preserved source bank.

Severity across the bank: 7 critical, 414 high, 600 medium, 3 low.

## Areas

| Id | Area | Questions | Rules package | Lens subagent | Need listening | Need audience |
|---|---|---:|---|---|---:|---:|
| D001 | concept and design | 32 | `review_bank_concept_and_design` | `review_lens_concept_and_design` | 0 | 1 |
| D002 | composition and hierarchy | 32 | `review_bank_composition_and_hierarchy` | `review_lens_composition_and_hierarchy` | 0 | 0 |
| D003 | foreground background separation | 32 | `review_bank_foreground_background_separation` | `review_lens_foreground_background_separation` | 0 | 0 |
| D004 | depth and occlusion | 32 | `review_bank_depth_and_occlusion` | `review_lens_depth_and_occlusion` | 0 | 0 |
| D005 | staging and blocking | 32 | `review_bank_staging_and_blocking` | `review_lens_staging_and_blocking` | 0 | 0 |
| D006 | contact and props | 32 | `review_bank_contact_and_props` | `review_lens_contact_and_props` | 0 | 0 |
| D007 | silhouette and anatomy | 32 | `review_bank_silhouette_and_anatomy` | `review_lens_silhouette_and_anatomy` | 0 | 0 |
| D008 | acting and expression | 32 | `review_bank_acting_and_expression` | `review_lens_acting_and_expression` | 0 | 1 |
| D009 | camera and projection | 32 | `review_bank_camera_and_projection` | `review_lens_camera_and_projection` | 0 | 0 |
| D010 | lighting and shadows | 32 | `review_bank_lighting_and_shadows` | `review_lens_lighting_and_shadows` | 0 | 0 |
| D011 | color and materials | 32 | `review_bank_color_and_materials` | `review_lens_color_and_materials` | 0 | 2 |
| D012 | texture and detail | 32 | `review_bank_texture_and_detail` | `review_lens_texture_and_detail` | 0 | 0 |
| D013 | motion and easing | 32 | `review_bank_motion_and_easing` | `review_lens_motion_and_easing` | 0 | 0 |
| D014 | physics and weight | 32 | `review_bank_physics_and_weight` | `review_lens_physics_and_weight` | 0 | 0 |
| D015 | layers and compositing | 32 | `review_bank_layers_and_compositing` | `review_lens_layers_and_compositing` | 0 | 0 |
| D016 | continuity and state | 32 | `review_bank_continuity_and_state` | `review_lens_continuity_and_state` | 0 | 0 |
| D017 | pacing and holds | 32 | `review_bank_pacing_and_holds` | `review_lens_pacing_and_holds` | 2 | 31 |
| D018 | story setup payoff | 32 | `review_bank_story_setup_payoff` | `review_lens_story_setup_payoff` | 2 | 32 |
| D019 | transitions and editing | 32 | `review_bank_transitions_and_editing` | `review_lens_transitions_and_editing` | 3 | 21 |
| D020 | text typography | 32 | `review_bank_text_typography` | `review_lens_text_typography` | 1 | 21 |
| D021 | captions and accessibility | 32 | `review_bank_captions_and_accessibility` | `review_lens_captions_and_accessibility` | 13 | 26 |
| D022 | music composition | 32 | `review_bank_music_composition` | `review_lens_music_composition` | 32 | 25 |
| D023 | voice and dialogue | 32 | `review_bank_voice_and_dialogue` | `review_lens_voice_and_dialogue` | 32 | 23 |
| D024 | sfx and mix | 32 | `review_bank_sfx_and_mix` | `review_lens_sfx_and_mix` | 32 | 12 |
| D025 | audio visual timing | 32 | `review_bank_audio_visual_timing` | `review_lens_audio_visual_timing` | 32 | 14 |
| D026 | rights and asset provenance | 32 | `review_bank_rights_and_asset_provenance` | `review_lens_rights_and_asset_provenance` | 0 | 15 |
| D027 | factual and algorithmic integrity | 32 | `review_bank_factual_and_algorithmic_integrity` | `review_lens_factual_and_algorithmic_integrity` | 2 | 15 |
| D028 | rendering and export | 32 | `review_bank_rendering_and_export` | `review_lens_rendering_and_export` | 2 | 6 |
| D029 | decoding and delivery | 32 | `review_bank_decoding_and_delivery` | `review_lens_decoding_and_delivery` | 3 | 9 |
| D030 | audience value | 32 | `review_bank_audience_value` | `review_lens_audience_value` | 0 | 31 |
| D031 | puzzles and fairness | 32 | `review_bank_puzzles_and_fairness` | `review_lens_puzzles_and_fairness` | 1 | 28 |
| D032 | reproducibility and maintenance | 32 | `review_bank_reproducibility_and_maintenance` | `review_lens_reproducibility_and_maintenance` | 2 | 2 |
| | **Total** | **1024** | | | | |

## Named review passes

| Pass | Purpose | Questions | Areas drawn on |
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

The exact ordered question ids of every pass are in `passes.json` (as listed in Appendix E). The
`adversarial_review_kit` module selects a pass across the loaded area banks.

## Provenance

`provenance.json` records the guide file hash and the Library records the guide gives for the source bank
(Appendix G). Library identities are retrieval references, not public sharing links.
