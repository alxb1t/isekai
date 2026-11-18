---
bump: patch
after: [0160-the-paydown-page]
---

# The sheet's history

The sheet's undo and redo move out of `useSheet.ts` into a plain module, `ui/src/edits.ts`, held by a case that exists first, on today's code; behaviour is unchanged.

Reading map: [design](design.md) holds the module's code, the edges it keeps and the tests, [tasks](tasks.md) holds the phases.

## Why

`useSheet.ts` mixes the draft's fields, their undo history, the receipt rules and the save queue. The history is the one that is pure, and no case drives it: `useSheet.test.ts` never calls `undo`, `redo` or `remove`, and no scenario names the sheet's undo, though the keys' requirement names `Mod+Z` in a field.

The pairs' and the polygon's histories are already plain modules with a test each. The sheet's gets the same shape, so its rules are read and tested without a save in flight. A patch may add a scenario under an existing requirement, and the save requirement already says an edit is saved: an undo is an edit that is saved.

## What Changes

- `ui/src/composables/useSheet.test.ts` gains a case, bound to `ui:save:an-edit-is-undone-and-redone`, written and green on the code as it stands.
- `ui/src/edits.ts` is new: one immutable state of the fields and the edit operations done and undone, and `held`, `reloaded`, `committed`, `removed`, `undone` and `redone` over it, each returning the state it was given when nothing changes.
- `ui/src/edits.test.ts` is new: a case bound to the same key, holding each function and each edge.
- `ui/src/composables/useSheet.ts` holds one state and calls the module; it marks the draft dirty and schedules a save only when the state changed. The composable's returned members are as today.
- `ui:save` gains `an-edit-is-undone-and-redone`: the delta carries the save requirement's prose and its scenarios unchanged, and the new one.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: *The page's save state is true to the requests in flight, and a pending edit is sent on leaving* gains a scenario. The requirement's prose and its other scenarios do not move.

## Impact

- Product: `ui/src/composables/useSheet.ts` and the new `ui/src/edits.ts`.
- Tests: the new case in `ui/src/composables/useSheet.test.ts`, the new `ui/src/edits.test.ts`. No existing case's assertion changes.
- Behaviour: none a person sees. `ui/src/views/Review.vue` and `tests/mutants.json` are not edited; the mutants that name `useSheet.ts` keep their text and stay red.

## Not in this change

- The receipt rules and the save queue, which stay in `useSheet.ts`, and `setRenders`.
- A chip's selection, any key's declaration, and the queue's edited mark, which the view sets.
- A new mutant, and an edit to `tests/mutants.json`.
- The review's panes, its own version.
- A component mounted in vitest, or a browser test.
