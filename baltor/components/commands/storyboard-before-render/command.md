---
description: "Gate a story with a contract and timed storyboard before any substantial render"
argument-hint: "<premise identity | storyboard.json | script>"
---

Gate this story before any substantial render: $ARGUMENTS
(a catalogue premise identity or `premise.json`, a `storyboard.json`, or a draft script).

The rule behind this command (Animation and Video Production Master Guide (v1.1, 10 October 2026)): evaluate the topic and storyboard before spending time on a full
render. A technically clean render does not rescue a story that fails its gate.

1. **Load the draft.** For a catalogue premise, keep its id, gate, evidence class and status (idea). If a treatment
   is chosen, resolve its address with `python3 treatment_address_resolver.py R-...` and carry its format and
   approach gates.
2. **Story contract.** Write `story_contract.json` (`story_contract` contract schema): want, stakes,
   constraint, choice, escalation, knowledge (viewer / character / uncertain), plant, reversal, consequence. Validate
   it. Stop here if any sentence cannot be written from the story; revise the story, not the polish.
3. **Timed board.** Write or update `storyboard.json` (`timed_storyboard` schema, board_type `timed`): every shot
   with composition, start and end seconds, action, new information, decision, sound and the story reason for the
   cut. Validate it and run `python3 timed_storyboard_check.py storyboard.json`; fix every ERROR. Print the review
   sheet with `--sheet`.
4. **Editorial pass.** Run the `story_doctor` subagent on the contract and the board. Apply its findings to the
   story. A "revise story" verdict ends this run.
5. **Gate and kill criteria.** Answer the ten storyboard-gate questions with shot evidence. Check the seven global
   kill criteria and the board's own kill criteria.
6. **Cheapest real review.** Propose a table read, a silent animatic or an owner storyboard choice. These are
   proposed review methods, not proof that a fresh audience approved the premise. Run the seven production-
   independent story tests only with people unfamiliar with the pitch, without explaining the intended answers,
   and record their answers verbatim.
7. **Render only after the gate.** Proceed to a bounded proof of the hardest shot, then the full render, only when
   the owner has chosen the board (record who and when) and no kill criterion is hit.

Report: what passed, what failed, what was not checked, and the board status (proposed, owner-selected,
animatic-reviewed ...). Never render first and judge later, extend a thin premise with polish or runtime, call a
renamed obstacle a new story, or upgrade any status.
