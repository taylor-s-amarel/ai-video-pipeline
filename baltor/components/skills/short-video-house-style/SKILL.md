---
name: "short-video-house-style"
description: "Use when planning, rendering or reviewing a vertical short (Reels, Shorts, TikTok) for this project. Gives the measurable house rules for title, captions, layers, background motion, narration and music."
---

# Short-video house style

Apply every rule below unless the user changes one explicitly. Each rule has a
measurable check so a render can be verified before it is sent.

## Deliver
- Full videos only: at least 60 seconds, 1080x1920, H.264 + AAC. No short previews unless asked.
- Never resend an older video as new work.

## Title hook (first frame)
- Bold yellow (`#FFD21F`), on the first frame, placed in the **upper third and overlaid on the main photo**.
  Never shrink or move the photo to make room for it.
- Behind it: a frosted-glass panel (blurred background, 55-75% tint, feathered edges).
- The title is its own short hook (2-7 words), not a copy of the first caption.

## Captions
- One synced line at a time, at most 7 words, frosted backing, within 150 ms of the spoken words.
- A small pop on the key word (scale 1.0 -> 1.12 -> 1.0 over 180 ms).
- No progress bars, stacked label panels or repeated section labels.
- `FACT N` / `TIP N` labels pop in when a new item starts; the key number sits under the label.

## Layers and background
- At least five layers; the background visibly moves for the whole video (video loop, 2x2 motion grid, light, particles, texture).
- No visual layer is fully opaque: every layer is at most 98% opacity.
- Feathered edges; never a hard rectangular cutout.
- The main photo stays large: at least 80% of the frame width.

## Audio
- Neural narration (for example Kokoro) at 140-160 words per minute, captions timed from the speech.
- Real music (recorded or well-arranged instruments) about 18 dB under the voice. Credit CC-BY music in the post text.

## Content
- Lead with a specific, curiosity-creating hook. Use real numbers, dates and outcomes, each with a source.

## Verify before sending
Run `scripts/check_rules.py spec.json` on the render spec and the `mp4_qa_probe` module on the export.
