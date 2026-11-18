---
bump: patch
debt: [0143·S1, 0142·S1, 0142·S2]
---

# The paydown, the page

The page's cards `0143·S1`, `0142·S1` and `0142·S2` and the render deletion's lost completion are paid: each late completion becomes a unit its component calls, and a case holds it with a deferred answer.

Reading map: [design](design.md) holds the units, their code and the red runs, [tasks](tasks.md) holds the phases.

## Why

The cards name a fix already in the source that no test reaches. Vitest mounts no component, so each case repeats the logic beside the view or tests a helper alone, and its recorded red run stops before the late completion.

Deleting a render has the same flaw the tattoo's removal had: it hears of its success through the dialog's `done`, which a dismissed dialog never sends. A patch may add a scenario under an existing requirement, so each fix gets one.

## What Changes

- `ui/src/composables/useDeletion.ts` is new: the guard `latest` moved out of `RenderLarge.vue`, and `useDeletion`, which holds what follows a deletion and reports it through the deletion's own request.
- `ui/src/composables/useRemoval.ts` is new: the picker's question about a removal, and the removal's report to the picker.
- `ui/src/composables/useCutInk.ts` is new: a cut card's loader, ended by the card's leaving.
- `RenderLarge.vue`, `TattooPicker.vue` and `CutImage.vue` call them and lose the moved code; `RenderLarge.vue` binds no `@done`.
- A case is new for each scenario added, each in an effect scope with a deferred answer; vitest edits at the end of `tests/mutants.json` each disable one guard.
- `ui:delete-render` gains `a-reload-that-lands-after-leaving-moves-nothing` and `a-dismissed-dialog-still-opens-the-hub`; `ui:picker` gains `a-dismissed-removal-still-lists-the-rest` and `a-crop-that-lands-after-leaving-is-dropped`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: *The large view deletes its render after asking, and the Hub opens on its cell* and *The picker shows the render and lists the kept tattoos, and takes an upload or a cut* each gain a scenario for the card and a scenario for the completion. Neither requirement's prose moves.

## Impact

- Product: `ui/src/views/RenderLarge.vue`, `ui/src/components/TattooPicker.vue`, `ui/src/components/CutImage.vue`, and the new composables.
- Tests: three new test files in `ui/src/composables/`, one import line of `ui/src/views/RenderLarge.test.ts`, `tests/mutants.json`.
- Behaviour: none a person sees. No format version moves, no existing case's assertion changes, and the release deletes the cards named under `debt:`.

## Not in this change

- An edit to an archived change, and a card raised after the base.
- A component mounted in vitest, or a browser test.
- A template's binding of a unit: no vitest case reaches it, and the design names each.
- The sheet's history and the review's panes, each its own version.
