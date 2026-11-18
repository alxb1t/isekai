# The sheet's history — tasks

The sheet's history is pinned by a case on today's `useSheet`, moved into `ui/src/edits.ts` with its own case, and `useSheet` is switched to call it.

## Progress

- [x] 1 — The pin · moderate
- [ ] 2 — The module · moderate
- [ ] 3 — The switch · moderate

## 1 — The pin

- [x] 1.1 In `ui/src/composables/useSheet.test.ts` add, at the file's end, `spec('ui:save:an-edit-is-undone-and-redone', …)` as [D5](design.md#d5) gives it: a read of `hair` and `eyes`, the steps of its table each saved and read from `calls`, then the sheet opened again.
  Verify: `git grep -c -h -F "ui:save:an-edit-is-undone-and-redone" -- ui/src/composables/useSheet.test.ts` prints `1`.
- [x] 1.2 **HALT CHECK** Run the case on the code as it stands: it passes with `ui/src/composables/useSheet.ts` unedited. A failure means the history of [D1](design.md#d1) is not today's.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useSheet.test.ts` exits 0.
- [x] 1.3 Hold the key's binding against the delta.
  Verify: `uv run pytest tests/test_spec_bindings.py` exits 0.

## 2 — The module

- [ ] 2.1 Create `ui/src/edits.ts` as [D1](design.md#d1) gives it, opened by the comment moved from `useSheet.ts`'s docstring.
  Verify: `grep -c -E "^export function (held|reloaded|committed|removed|undone|redone)\(" ui/src/edits.ts` prints `6`.
- [ ] 2.2 Create `ui/src/edits.test.ts` with the case of [D6](design.md#d6): a block for each function and each edge of [D3](design.md#d3).
  Verify: `uv run python -m tools.test_ui ui/src/edits.test.ts` exits 0.
- [ ] 2.3 Hold the types and the binding of [D6](design.md#d6).
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
  Verify: `grep -c -F "ui:save:an-edit-is-undone-and-redone" ui/src/edits.test.ts` prints `1`.

## 3 — The switch

- [ ] 3.1 In `ui/src/composables/useSheet.ts` import the module, hold `edits` in place of the stacks as [D4](design.md#d4) gives it, and in `open` clear the history with `held` and land the read with `reloaded` as [D7](design.md#d7) gives them, leaving the failed read's lines and `DEBOUNCE` as they are.
  Verify: `git grep -c -h -E "edits = (held\(edits\.fields\)|reloaded\(edits, body\.fields\))" -- ui/src/composables/useSheet.ts` prints `2`.
  Verify: `git grep -c -h -F "'../edits'" -- ui/src/composables/useSheet.ts` prints `2`.
- [ ] 3.2 In `ui/src/composables/useSheet.ts` replace `interface Edit`, `apply`, `record` and the bodies of `commit`, `remove`, `undo` and `redo` with `take` and the calls of [D4](design.md#d4).
  Verify: `git grep -n -E "(done|undone)\.(push|pop)|^interface Edit|function (apply|record)\(" -- ui/src/composables/useSheet.ts` prints nothing.
- [ ] 3.3 Shorten `useSheet`'s docstring to one sentence on the history, which now lives in `ui/src/edits.ts`.
  Verify: `git grep -c -h -F "ui/src/edits.ts" -- ui/src/composables/useSheet.ts` prints `1`.
- [ ] 3.4 Run every browser unit case: each passes with no assertion changed.
  Verify: `uv run python -m tools.test_ui` exits 0.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 3.5 Hold the bindings, the ratchets, the view and the mutants' file.
  Verify: `uv run pytest tests/test_spec_bindings.py tests/test_ratchets.py` exits 0.
  Verify: `git log --format=%h main..HEAD -- ui/src/views/Review.vue tests/mutants.json` prints nothing.
- [ ] 3.6 Replay the mutants: those that name `useSheet.ts` stay red and no edit survives.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
