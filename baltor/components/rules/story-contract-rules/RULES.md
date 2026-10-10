# Story contract rules

Source: Animation and Video Production Master Guide (v1.1, 10 October 2026), "Story quality comes before production scale". Status: editorial guidance; the review methods it names are proposed, not validated audience research.

## The lesson from BOXED IN

A modest task can support excellent comedy, but it needs character behavior, surprising decisions, escalating consequences, and a satisfying reversal. Repeated unsuccessful attempts are not automatically an arc. Extending one small joke with polished textures and technically correct falls can make its thinness more obvious. The latest correction therefore changes the admission gate for a new film: evaluate the topic and storyboard before spending time on a full render.

The rejected film still demonstrates a complete 108-second pipeline, cardboard cutaway design, an authored character, narration and score, and a tested three-prop physics sequence. Preserve those reusable techniques without inheriting its premise as the standard for future stories. Do not rename a revised obstacle, swap the prop, and call the same repetition a new story.

Evidence: BOXED IN (108 s) was technically delivered and Taylor rejected its story quality. `provenance.json` keeps its Library identities and SHA-256 values so the history stays traceable; none of its technical receipts overrides the story rejection.

## The contract

Write these sentences before drawing shots:

1. **Want:** What does the protagonist actively want before the film ends?
2. **Stakes:** What visibly changes if they fail, and why should this particular character care?
3. **Constraint:** What prevents the obvious solution? Establish it early enough to feel fair.
4. **Choice:** What does the character do that causes the next complication?
5. **Escalation:** How does each attempt change the situation rather than reset it?
6. **Knowledge:** What does the viewer know, what does the character know, and what is still uncertain?
7. **Plant:** Which visible detail will matter later? The viewer must have a fair chance to notice it.
8. **Reversal:** How does the final action use established information in a surprising way?
9. **Consequence:** What final image shows that the character or situation has changed?

Check: all nine sentences are written for this premise before any shot is drawn, each traceable to a board line or shot. The `story_contract` contract schema holds them as data.

Not every story needs a moral, a villain, dialogue, or a countdown. Small personal stakes can work if the want and cost are clear. A lesson tacked onto the ending cannot replace causality. Suspense comes from uncertainty with understandable consequences, not merely dark music or a slowly opening door.

## A flexible longer-film structure

For a proposed 90–120-second film, start with a strong event in the opening seconds, establish the want and constraint, give the protagonist a plausible first choice, let that choice worsen or transform the situation, introduce a reversal, and leave enough time for a legible climax and a concise aftermath. Do not treat these as mandatory equal-length segments.

An illustrative 108-second allocation is 0–5 seconds for the hook, 5–15 for the stakes and geography, 15–35 for the first consequential attempt, 35–60 for escalation and new information, 60–82 for reversal and commitment, 82–102 for the decisive action, and 102–108 for the final button. This is a writing scaffold, not an empirically optimized retention formula. A factual reconstruction may use different timings because evidence and explanation determine its structure.

| Seconds | Beat (illustrative 108-second allocation) |
|---|---|
| 0–5 | hook |
| 5–15 | stakes and geography |
| 15–35 | first consequential attempt |
| 35–60 | escalation and new information |
| 60–82 | reversal and commitment |
| 82–102 | decisive action |
| 102–108 | final button |

This allocation is a writing scaffold, not an empirically optimized retention formula; do not treat the segments as mandatory or equal.

## Related

`storyboard_gate`, `comedy_mechanisms`, `suspense_rules`, `story_tests`, `story_doctor`, `storyboard_before_render`.

Status language: an idea or proposal is not a script; a storyboard is not a render; a render is not a delivery; a technical delivery is not creative acceptance; an editorial review is not audience evidence. Record the strongest stage actually observed and never upgrade it.
