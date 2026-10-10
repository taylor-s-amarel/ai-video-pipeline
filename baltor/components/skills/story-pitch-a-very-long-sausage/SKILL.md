---
name: "story-pitch-a-very-long-sausage"
description: "Use when deciding whether to develop \"A Very Long Sausage\" into a timed storyboard. Opening frame: Two rival dogs grip opposite ends of one enormous sausage. A pigeon eyes its undefended center. Gives the pitch's question and conflicting goals, world rule, causal escalation, plant and payoff, and the visual test it must pass first. Status: pitch, not an approved production."
---

# A Very Long Sausage (development pitch 6 of 8)

**Status:** pitch, proposed.

From the guide's development slate: These are pitches, not approved productions or timed boards. Together with the three fully boarded films above, they make eight topics. They should be developed only if their central visual test works; a striking premise is not yet a finished film.

Slate status, from the guide: Proposed concepts and unrendered storyboards. These are editorial recommendations, not measured audience results or claims of user acceptance. The earlier BOXED IN film's technical progress does not establish that its story worked. The next production should pass a story test before final animation.

**Scope:** Eight new development topics: three complete timed storyboards and five additional pitches. They are separate from the earlier 240-premise catalogue and its 2,400 treatment candidates. Boards and pitches are not added together as eleven stories.

**Opening frame:** Two rival dogs grip opposite ends of one enormous sausage. A pigeon eyes its undefended center.

**Question and conflicting goals:** Will either dog get lunch before the pigeon takes it? Each dog wants the entire sausage; their owner wants to continue walking; the pigeon wants the easiest possible bite.

**Rule:** Neither dog will voluntarily release its end. Every tactic therefore moves or stretches the same connected object and pulls on their leads.

**Causal escalation:** One dog backs away to claim more; the other circles a bollard to gain leverage. Their owner gets caught between the crossed leads. The pigeon advances each time both dogs focus on each other. At midpoint, they see the common threat and stop pulling against one another. They stretch the elastic cartoon sausage across the already-established bollards, wait for the pigeon to land in the center, and release tension together. The pigeon lands safely on a nearby bench, indignant and empty-beaked.

**Plant and payoff:** The sausage's ridiculous stretch and the bollards must be shown before they become a slingshot. The dogs then choose to break and share the sausage. The owner gives a relieved smile, tries to step forward, and discovers that the newly cooperative dogs have left him neatly gift-wrapped in their leads. End there; no multiplying flock or repeat of the earlier dog-fetch film.

**Visual test:** This is the smallest-stakes pitch, so it should be short and almost entirely physical. It fails if the dog behavior is merely three interchangeable tugs or the owner seems genuinely injured.

## Developing this pitch

This is a pitch, not a timed board. Develop it only if its visual test works. Next steps, in order:

1. Write the story contract (`story_contract` schema):

   - **Want:** What does the protagonist actively want before the film ends?
   - **Stakes:** What visibly changes if they fail, and why should this particular character care?
   - **Constraint:** What prevents the obvious solution? Establish it early enough to feel fair.
   - **Choice:** What does the character do that causes the next complication?
   - **Escalation:** How does each attempt change the situation rather than reset it?
   - **Knowledge:** What does the viewer know, what does the character know, and what is still uncertain?
   - **Plant:** Which visible detail will matter later? The viewer must have a fair chance to notice it.
   - **Reversal:** How does the final action use established information in a surprising way?
   - **Consequence:** What final image shows that the character or situation has changed?

2. Draft a timed board (`timed_storyboard` schema, board_type `timed`) and run `timed_storyboard_check` on it.
3. Answer the storyboard gate:

   1. Can the opening promise be understood without an explanatory paragraph?
   2. Does something consequential happen before the viewer has merely watched a character travel?
   3. Can every middle beat be connected by “because” or “therefore,” rather than only “and then”?
   4. Does each attempt change the options, risk, relationship, or knowledge?
   5. Is there a fair plant for the solution and a reason the character did not use it immediately?
   6. Does the ending resolve the question raised at the beginning?
   7. Is at least one surprise specific to this premise rather than a generic stumble or shrug?
   8. Would removing a shot improve the film? Remove or rewrite shots with no new action, information, emotion, or rhythm.
   9. Does the premise sustain the intended duration? Shorten it or deepen the conflict rather than adding filler.
   10. Is the intended reaction evidenced by review, or merely hoped for? Keep that distinction visible.

4. Test a rough animatic with the seven production-independent story tests (`story_tests`), then apply the global kill criteria: no concrete uncertainty in the opening; interchangeable failed attempts; a midpoint that only increases noise; an unplanted new rule solving the climax; an ending that is merely an object reveal; an achievement erased by an arbitrary reset; a punch line requiring narration to explain why it is funny. A technically clean render does not rescue any of these.

## Source

Animation and Video Production Master Guide (v1.1, 10 October 2026), "Five more distinct topics: an eight-story development slate", line 340 (`docs/reference/Animation_and_Video_Production_Master_Guide_2026-10-10.md#6-a-very-long-sausage`).
