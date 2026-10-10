---
name: "story-pitch-just-hold-the-sun"
description: "Use when deciding whether to develop \"Just Hold the Sun\" into a timed storyboard. Opening frame: A tourist pretends to pinch the setting sun for a photograph. The peculiar camera clicks, and the sun actually drops into his fingers. The beach goes dark. Gives the pitch's question and conflicting goals, world rule, causal escalation, plant and payoff, and the visual test it must pass first. Status: pitch, not an approved production."
---

# Just Hold the Sun (development pitch 7 of 8)

**Status:** pitch, proposed.

From the guide's development slate: These are pitches, not approved productions or timed boards. Together with the three fully boarded films above, they make eight topics. They should be developed only if their central visual test works; a striking premise is not yet a finished film.

Slate status, from the guide: Proposed concepts and unrendered storyboards. These are editorial recommendations, not measured audience results or claims of user acceptance. The earlier BOXED IN film's technical progress does not establish that its story worked. The next production should pass a story test before final animation.

**Scope:** Eight new development topics: three complete timed storyboards and five additional pitches. They are separate from the earlier 240-premise catalogue and its 2,400 treatment candidates. Boards and pitches are not added together as eleven stories.

**Opening frame:** A tourist pretends to pinch the setting sun for a photograph. The peculiar camera clicks, and the sun actually drops into his fingers. The beach goes dark.

**Question and conflicting goals:** Can the photographer restore daylight before an approaching tour group discovers what happened? The tourist wants increasingly impressive pictures and is reluctant to surrender his new souvenir.

**Rule:** A forced-perspective illusion photographed by this camera becomes physically real. All repairs must use that same rule or straightforward handling of the already-transformed objects.

**Causal escalation:** The photographer tries to frame the tourist tossing the sun back, but the tourist insists on another impressive pose. Their disagreement leaves the tiny sun in the foreground just as a child holding an ice-cream cone photobombs them. The camera catches an apparent extra scoop. Now the sun is perched on the cone. At midpoint, the photographer must work with the child, who is much more interested in finishing the snack than posing correctly. The tourist finally gives up directing his own glamorous image and helps line up a return shot.

**Plant and payoff:** The child's cone and repeated attempts to enter the photo appear before the accident. For the final shot, the child holds the cone under the horizon as though putting the sun back into the sky. Click: daylight returns, with one bite missing from the sun. The tourist has his spectacular sunset picture and an unmistakable record of his vanity.

**Visual test:** Diagram every forced-perspective composition before boarding. If a transformation cannot be explained by the actual photograph, reject it. This is the highest-risk extra concept because an arbitrary camera effect would destroy the fairness of the ending.

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

Animation and Video Production Master Guide (v1.1, 10 October 2026), "Five more distinct topics: an eight-story development slate", line 354 (`docs/reference/Animation_and_Video_Production_Master_Guide_2026-10-10.md#7-just-hold-the-sun`).
