---
name: "story-pitch-the-hiccup-concerto"
description: "Use when deciding whether to develop \"The Hiccup Concerto\" into a timed storyboard. Opening frame: In the expectant silence, a conductor hiccups, jerks his baton and produces one enormous orchestral blast. Gives the pitch's question and conflicting goals, world rule, causal escalation, plant and payoff, and the visual test it must pass first. Status: pitch, not an approved production."
---

# The Hiccup Concerto (development pitch 5 of 8)

**Status:** These are pitches, not approved productions or timed boards. Together with the three fully boarded films above, they make eight topics. They should be developed only if their central visual test works; a striking premise is not yet a finished film. Status: proposed concepts and unrendered storyboards. These are editorial recommendations, not measured audience results or claims of user acceptance. The earlier BOXED IN film's technical progress does not establish that its story worked. The next production should pass a story test before final animation.

**Scope:** Eight new development topics: three complete timed storyboards and five additional pitches. They are separate from the earlier 240-premise catalogue and its 2,400 treatment candidates. Boards and pitches are not added together as eleven stories.

**Opening frame:** In the expectant silence, a conductor hiccups, jerks his baton and produces one enormous orchestral blast.

**Question and conflicting goals:** Can he finish the performance without being exposed as out of control? He wants dignified precision; the first violin sees that the audience loves the accidental rhythm and wants him to embrace it.

**Rule:** The orchestra follows the baton. The music is a visible result of his movement, rather than a magical response to any noise in the room.

**Causal escalation:** He conceals a hiccup behind a sweeping gesture, which makes the brass swell. The violinist answers it as a phrase. His attempt to take water creates a tiny pause the percussionist fills. His effort to stop the emerging piece makes a dramatic silence, and the audience leans forward. At midpoint, he sees that the violinist is offering a repeatable pattern, not mocking him. He chooses to conduct the pattern deliberately.

**Plant and payoff:** A visiting composer's stern face stays fixed while one shoe starts tapping early. At the finish, that composer leads the applause and asks for an encore. The conductor no longer has hiccups. Rather than try to summon them, he confidently reproduces the once-accidental movements, with the violinist as his partner. Final visual joke: he carefully moves the fizzy water far beyond his reach before the downbeat.

**Visual test:** The first blast must be funny with almost no setup, and the music must genuinely follow the movements. Reject an ending that depends on a scare conveniently causing a hiccup.

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

Animation and Video Production Master Guide (v1.1, 10 October 2026), "Five more distinct topics: an eight-story development slate", line 326 (`docs/reference/Animation_and_Video_Production_Master_Guide_2026-10-10.md#5-the-hiccup-concerto`).
