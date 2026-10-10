---
name: "story-pitch-front-legs-back-legs"
description: "Use when deciding whether to develop \"Front Legs, Back Legs\" into a timed storyboard. Opening frame: The front half of a pantomime horse kneels heroically while its back legs begin an unwanted tap solo. Gives the pitch's question and conflicting goals, world rule, causal escalation, plant and payoff, and the visual test it must pass first. Status: pitch, not an approved production."
---

# Front Legs, Back Legs (development pitch 4 of 8)

**Status:** These are pitches, not approved productions or timed boards. Together with the three fully boarded films above, they make eight topics. They should be developed only if their central visual test works; a striking premise is not yet a finished film. Status: proposed concepts and unrendered storyboards. These are editorial recommendations, not measured audience results or claims of user acceptance. The earlier BOXED IN film's technical progress does not establish that its story worked. The next production should pass a story test before final animation.

**Scope:** Eight new development topics: three complete timed storyboards and five additional pitches. They are separate from the earlier 240-premise catalogue and its 2,400 treatment candidates. Boards and pitches are not added together as eleven stories.

**Opening frame:** The front half of a pantomime horse kneels heroically while its back legs begin an unwanted tap solo.

**Question and conflicting goals:** Can two performers finish the children's show without exposing the people inside? The front performer wants to deliver his magnificent heroic scene; the rear performer wants the visiting talent scout to notice his dance skill. Their jobs depend on keeping the illusion through the final curtain.

**Rule:** The costume must remain intact during the show. Their disagreement has to happen through the horse's movements.

**Causal escalation:** The front tries to plant all four feet for his dramatic speech; the rear keeps the body moving. The front counters with a gallop, accidentally giving the rear a faster dance rhythm. A planned rescue becomes a bucking, moonwalking duel, and both performers must cooperate to keep the child-sized actor playing the princess safely seated on the costume's padded back.

**Plant and payoff:** The talent scout's pencil follows the feet, not the speech. Once the curtain falls, the front performer rushes out to claim the applause. The audience calls for the dancing back legs instead. The rear performer gets his own bow, then invites the front performer to supply the back legs of his encore. Their hierarchy has literally reversed.

**Visual test:** The front and rear must read as separate personalities without dialogue or a cutaway inside the costume. Keep the physical comedy grounded; do not escalate to an unexplained airborne battle.

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

Animation and Video Production Master Guide (v1.1, 10 October 2026), "Five more distinct topics: an eight-story development slate", line 312 (`docs/reference/Animation_and_Video_Production_Master_Guide_2026-10-10.md#4-front-legs-back-legs`).
