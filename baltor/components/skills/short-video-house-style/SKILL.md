---
name: "short-video-house-style"
description: "Use when planning, rendering or reviewing a vertical short (Reels, Shorts, TikTok) for this project. Gives the measurable house rules for title, captions, layers, background motion, narration and music."
---

# Short-video house style (photographic contract v8)

Apply every rule below unless the user changes one explicitly. Each rule has a
measurable check so a render can be verified before it is sent. Source: the
Creative Media and Game Production Reference (10 Oct 2026), sections 4-7 and 11.

## Deliver
- Complete films only: at least 60 seconds with a complete arc (hook, context, turn, payoff),
  1080x1920, H.264 + AAC. A loop, sampler or 6-second test is labelled as such, never sent as a film.
- Never resend an older video as new work. Keep the master; check a compact copy separately.

## Imagery and geometry
- Realistic, large photography is the default. Illustrated treatments only when explicitly chosen.
- Photo bounds are exactly (54,96) to (1026,1824): 972x1728, a 5% inset per side, 90% of width and height.
- The exposed 5% border keeps moving from the first frame to the last.
- Never shrink or move the photo to make room for text. Keep faces, eyes, hands and props clear in every crop state.

## Title hook (first frame)
- Short, bold yellow (`#FFD21F`) editorial title overlaid on the upper photograph, glyph centre near y=320
  (about 72 px bold, dark outline, controlled shadow), held about 3.5-4 s.
- The title is its own hook, distinct from the faithful narration captions.

## Genuine frosted glass (title, captions, music credits)
1. Measure the real glyph rectangle without moving the text; pad and clamp it inside the composition.
2. Sample the current composite underneath with a 48 px margin; Gaussian blur radius 18 px.
3. Crop back, add a restrained dark/cool tint and a small pearl lift.
4. Rounded mask with 2.2 px feather, then apply the layer opacity cap; faint softened rim; sharp text on top.
A translucent solid rectangle is not frosted glass.

## Captions
- Faithful to every spoken phrase, phrase-aligned from measured narration; onset within 3 frames,
  trailing hold at most 0.5 s (project limits, not an accessibility standard).
- A small pop on the key word. No progress bars, stacked label panels or repeated section labels;
  do not restart a numbered badge during a continuation phrase.
- `FACT N` / `TIP N` labels pop in when a new item starts; the key number sits under the label.

## Layers and background
- Every authored layer stays at or below 98% opacity (8-bit cap 249/255).
- Five-layer foundation, back to front: full-frame moving background movie (alpha <= 247), blurred moving layer (<= 51),
  animated perspective grid (<= 31), slow colour haze (<= 31), drifting particles (<= 63).
- Four independent 2x2 panels below the photo with 28 px feathered seams and panel alpha <= 122: wave field
  (clock 0.64), depth grid (0.91, +3.7 s), defocused lights (0.53, +8.4 s, seed 509), ribbons and particles (1.07, +13.2 s).
- Clocks are seekable and independent: rendering frame 100 before frame 10 changes neither frame.
- Feathered edges; never a hard rectangular cutout.

## Audio
- Kokoro `af_heart` at native speed 1.0, separate measured phrases, never time-stretched to fit.
- Real recorded music or an original score about 18 dB under the voice; credit track, creator, licence and edits,
  and follow the creator's usage guidance (for Scott Buckley: description credit, no isolated redistribution or Content ID).
- Say whether a listening pass was performed; numeric checks do not replace listening.

## Content
- Specific, curiosity-creating hook; real numbers, dates and outcomes, each with a source in a claim ledger.
- Concrete observable actions over universal claims about genders or diagnoses.

## Verify before sending
Run `scripts/check_rules.py spec.json` on the render spec and the `mp4_qa_probe` module on the export.
Decode the actual encoded file; check first and last frames, every caption transition, the brightest background,
the largest title line and the ending. Record what was and was not checked.
