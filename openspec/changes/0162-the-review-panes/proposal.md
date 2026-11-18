---
bump: patch
after: [0161-the-sheet-history]
---

# The review's panes

`paneOf` and the panes' selectors leave `Review.vue` for `panes.ts`, where a test holds them; nothing the operator sees or presses changes.

Reading map: [design](design.md) holds the table, `paneOf`, the new `entry` and the test's cost, [tasks](tasks.md) holds the phases: the rules with their test, then the switch.

## Why

`Review.vue` landed over the length the review-and-hub plan set, and much of what is left is DOM focus that vitest, running in node, cannot pin. Some of that code is pure: `paneOf`, which asks an element what it sits in, and the selectors `paneOf` and `entry` both write out. Moved into `panes.ts`, they are tested through a stub that answers `closest`, with no DOM.

## What Changes

- `ui/src/panes.ts` gains `SELECTORS`, one table of what each pane holds and where the focus enters it, and `paneOf`, which reads it.
- `ui/src/panes.test.ts` gains steps that hold `paneOf`, bound to the scenario `ui:keys:review-moves-between-its-panes`, written before the view switches.
- `ui/src/views/Review.vue` imports `paneOf` and `SELECTORS` from `panes.ts`, loses its own `paneOf`, and `entry` reads the table.
- No requirement is touched: the change adds no scenario and carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The `ui` capability's scenario `ui:keys:review-moves-between-its-panes` gains a second proof, and its text stands.

## Impact

`ui/src/panes.ts`, `ui/src/views/Review.vue` and `ui/src/panes.test.ts` change. Every class, `data-*` hook and key stays as it is, and `Review.vue`'s one `useKeys` call is untouched. `tests/test_ratchets.py` passes as it stands: the page's table is empty and the view only gets shorter. `tests/test_spec_bindings.py` passes as it stands: the steps carry a key the test already binds.

## Not in this change

- `entry`'s reading of the last field, `enter`, `remember` and `paneNow`: they read the document and the view's refs.
- The lens' DOM code and the chips.
- A browser test.
- `moveRow`'s own `input.fragment[data-field=…]` selector and `fourStops`'s `.renders-block`: they are not a pane's entry.
- A new scenario, a decision, a mutant, or any key's declaration.
