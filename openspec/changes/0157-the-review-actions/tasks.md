# The review's actions — tasks

Phase 1 writes the composable and its test beside the view, unused; phase 2 switches the view to it and removes the view's ratchet row.

## Progress

- [x] 1 — The composable and its test · moderate
- [ ] 2 — The view switches and its row goes · moderate

## 1 — The composable and its test

- [x] 1.1 **HALT CHECK** The view still holds the code [D1](design.md#d1) moves, and `tests/test_ratchets.py` still lists its row: `ui/src/views/Review.vue` declares `reread`, `discard`, `approve` and `cancelApprove`.
  Verify: `git grep -c -h -E "^async function (reread|discard|approve|cancelApprove)\(" -- ui/src/views/Review.vue` prints `4`.
  Verify: `git grep -c -h -F "\"ui/src/views/Review.vue\": 659" -- tests/test_ratchets.py` prints `1`.
- [x] 1.2 Write `ui/src/composables/useReviewActions.ts` as [D1](design.md#d1) gives it: `ReviewActionsPage`, `useReviewActions`, today's bodies of `reread`, `discard`, `approve` and `cancelApprove`, the `refused` and `cancelling` refs, the `refusal` computed, `forget`, and the `rereads` statement with its `watch` calls reading `useLiveStore()`. It declares no key ([D5](design.md#d5)).
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.3 Write the harness of `ui/src/composables/useReviewActions.test.ts`: the hand-released `fetch` of `useSheet.test.ts` (`Call`, `calls`, `answer`, `refuse`), `setActivePinia(createPinia())` and fake timers in `beforeEach`, the scope stopped and `fetch` unstubbed in `afterEach`, a `detail` builder whose `approved` option also sets `readonly: true`, and a `mount()` that runs `useSheet`, `useApproval`, a `load` stub, a `settled` stub and `useReviewActions` in one `effectScope` for the collection `b` and the flow `f`. `answer`, `refuse` and every other wait run `await vi.advanceTimersByTimeAsync(0)`, never `vi.runAllTimersAsync()`: the live store's intervals never end, so a run of all timers aborts.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.4 Add `spec('ui:save:an-approval-waits-for-a-save-in-flight', …)`: open `a`, commit twice inside one save, call `approve()`; answer each request in turn and expect the second save to state the first's receipt, the `POST` to `/api/c/b/review/a/f/approve` to state the second's, and then `load` called and the sheet read again.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useReviewActions.test.ts -t "an-approval-waits-for-a-save-in-flight"` exits 0 and its summary reads `1 passed`.
- [x] 1.5 Add `spec('ui:review:a-refused-save-is-shown', …)`: refuse the only save, expect `approve()` to send no `POST` and `refusal.value` to be the sheet's message; refuse a save again and expect `discard()` to send no `POST` to `/api/c/b/review/a/f/discard`.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useReviewActions.test.ts -t "a-refused-save-is-shown"` exits 0 and its summary reads `1 passed`.
- [x] 1.6 Add `spec('ui:review:the-cancel-follows-the-render', …)`: with an approved sheet open, set `useLiveStore().jobs` to a running render of `b` and `await vi.advanceTimersByTimeAsync(0)`, expect one read of the sheet and answer it; set a done render of `b` and expect another read; with an editable sheet open, expect none. Build the slots as `cancel.test.ts` does.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useReviewActions.test.ts -t "the-cancel-follows-the-render"` exits 0 and its summary reads `1 passed`.
- [x] 1.7 Add `spec('ui:review:a-render-that-moves-during-the-read-is-read-again', …)`: move the slot while `sheet.open('a')` is unanswered and expect no read; land it approved and expect one read more; repeat with an editable landing and expect none.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useReviewActions.test.ts -t "a-render-that-moves-during-the-read-is-read-again"` exits 0 and its summary reads `1 passed`.
- [x] 1.8 The page's whole suite holds beside the new file, with the view untouched.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 2 — The view switches and its row goes

- [ ] 2.1 In `ui/src/views/Review.vue` delete the `refused` and `cancelling` refs with the comment above `refused`, the `live` constant, the `refusal` computed with its comment, and the functions `reread`, `discard`, `approve` and `cancelApprove` with their comments.
  Verify: `git grep -c -h -E "^async function (reread|discard|approve|cancelApprove)\(" -- ui/src/views/Review.vue` prints nothing and exits 1.
- [ ] 2.2 In the same file replace the `const follow = rereads(...)` line and the `watch` calls under it with the call [D2](design.md#d2) gives, at the same place.
  Verify: `git grep -c -h -F "= useReviewActions({" -- ui/src/views/Review.vue` prints `1`.
- [ ] 2.3 In the imports of the same file drop `cancelApproval` and `discardDraft` from `'../api'`, the line `import { rereads } from '../cancel'` and the `useLiveStore` import, and add `import { useReviewActions } from '../composables/useReviewActions'` between the `useQueue` and `useSheet` imports.
  Verify: `git grep -n -F "from '../cancel'" -- ui/src/views/Review.vue` prints nothing and exits 1.
- [ ] 2.4 In `watch(current, …)` of the same file replace the lines `approval.forget()` and `refused.value = null` with one `forget()` at the place of the first.
  Verify: `git grep -n -F "refused.value" -- ui/src/views/Review.vue` prints nothing and exits 1.
- [ ] 2.5 In `tests/test_ratchets.py` set `BIG_UI_FILES: dict[str, int] = {}` and `UI_ROWS = 0` ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).
  Verify: `git grep -c -h -F "UI_ROWS = 0" -- tests/test_ratchets.py` prints `1`.
- [ ] 2.6 **HALT CHECK** The view is at or under the ceiling with its row gone, and the new bindings are counted.
  Verify: `uv run pytest tests/test_ratchets.py tests/test_spec_bindings.py` exits 0.
- [ ] 2.7 The composable declares no key ([D5](design.md#d5)) and the test binds each scenario [D6](design.md#d6) names.
  Verify: `git grep -n -F "useKeys" -- ui/src/composables/useReviewActions.ts` prints nothing and exits 1.
  Verify: `git grep -c -h -E "^spec\('ui:(save|review):" -- ui/src/composables/useReviewActions.test.ts` prints `4`.
- [ ] 2.8 The page's tests and types hold with the view switched.
  Verify: `uv run python -m tools.test_ui` exits 0.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
