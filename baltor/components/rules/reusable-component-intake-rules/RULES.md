# Reusable components and actual intake

Source: Animation and Video Production Master Guide (10 Oct 2026), "Reusable components and actual intake". Rules are the owner's sentences, lightly numbered.

## Extract

1. Extract the smallest task that saved effort in a completed episode: crop planning, text fit, anchor projection,
   two-bone contact, prop ownership, timeline validation, mask-to-answer joins, audio ducking, chunk verification, or
   final-stream inspection.
2. Keep episode content in data. A renamed whole-film script is not automatically a reusable library.

## Define

3. Define each component's inputs, outputs, errors, dependencies, time/resource limits, deterministic behavior and
   effects.
4. A crop planner should not access the network; a renderer should not publish; a source check should not create
   accounts.

## Test

5. Test positive cases, boundaries, known-wrong consumers and failure behavior.
6. Keep the real failed fixture when it teaches a useful boundary.

## Keep the states separate

7. Keep these states separate: authored, rights-reviewed, focused-tested, source-reopened, minimally invoked by a consumer, actual isolated intake-qualified, admitted, published, and used successfully. One never implies the next.
8. Neutral packages stay neutral until the real current target contract is inspected and tested.
9. Do not invent producer/source bindings, write directly to a production database, bypass admission, or infer
   publication from a private Library save.

## Recorded examples (status as the guide gives it)

- The earlier original `motion_helpers` candidate is retained as Library `libfile_9da84ebd1d808191ae0300c7c98199bb`;
  its catalogue record reports 48 tests. That record does not establish native intake, final-film adoption for every
  helper, or universal compatibility.
- The Pymunk recovery package is `libfile_98caae390d188191a2e432cf29728cff` v0; its single props-only trace capability
  has its own test scope.

## The guide's text

> Extract the smallest task that saved effort in a completed episode: crop planning, text fit, anchor projection, two-bone contact, prop ownership, timeline validation, mask-to-answer joins, audio ducking, chunk verification, or final-stream inspection. Keep episode content in data. A renamed whole-film script is not automatically a reusable library.
>
> Define each component's inputs, outputs, errors, dependencies, time/resource limits, deterministic behavior and effects. A crop planner should not access the network; a renderer should not publish; a source check should not create accounts. Test positive cases, boundaries, known-wrong consumers and failure behavior. Keep the real failed fixture when it teaches a useful boundary.
>
> The earlier original `motion_helpers` candidate is retained as Library `libfile_9da84ebd1d808191ae0300c7c98199bb`; its catalogue record reports 48 tests. That record does not establish native intake, final-film adoption for every helper, or universal compatibility. The Pymunk recovery package is `libfile_98caae390d188191a2e432cf29728cff` v0; its single props-only trace capability has its own test scope.
>
> Keep these states separate: authored, rights-reviewed, focused-tested, source-reopened, minimally invoked by a consumer, actual isolated intake-qualified, admitted, published, and used successfully. Neutral packages stay neutral until the real current target contract is inspected and tested. Do not invent producer/source bindings, write directly to a production database, bypass admission, or infer publication from a private Library save.
