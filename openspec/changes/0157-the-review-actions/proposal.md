---
bump: patch
---

# The review's actions

Review's actions leave `ui/src/views/Review.vue` for `ui/src/composables/useReviewActions.ts`, with its test written before the view switches to it; the file falls under the page's ceiling and its ratchet row goes.

Reading map: [design](design.md) holds the composable's shape, what it reads of the page and the tests, [tasks](tasks.md) its phases.

## Why

`Review.vue` is past the page's ceiling, a listed row of the ratchet ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)). Its `<script setup>` holds the actions an operator takes on a sheet — read it again, approve, cancel the approval, discard the draft — with the refusal they share and the watchers that read an approved sheet again when a render moves. vitest cannot import a view's setup locals, so none of it is held by a test that runs on the unit layer.

The series takes this view in steps. Its rules left in an earlier version, and this one takes its actions.

## What Changes

- `ui/src/composables/useReviewActions.ts` is new: `reread`, `discard`, `approve` and `cancelApprove`, the `refused` and `cancelling` refs, the joined `refusal`, and the rereads' watchers.
- `ui/src/composables/useReviewActions.test.ts` is new and written before the view switches: a test for each unit scenario that already covers a rule the actions hold, run in an effect scope with `fetch` stubbed.
- `ui/src/views/Review.vue` calls the composable where its `rereads` line stands, and loses the moved code, `live` and the imports of the moved names; it keeps its `useKeys` call with its commands in today's order.
- `tests/test_ratchets.py` loses the row of `ui/src/views/Review.vue` and the table's count falls to the rows left.
- No requirement is touched, so the change carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The tests bind scenarios of the `ui` spec as they stand.

## Impact

- Product: `ui/src/views/Review.vue`, `ui/src/composables/useReviewActions.ts`.
- Tests: `ui/src/composables/useReviewActions.test.ts`, `tests/test_ratchets.py`.- Behaviour: none. Every class, `data-*` hook and key stays as it is, and no existing test's assertion changes.

## Not in this change

- The sheet's history, the panes, the lens' DOM code and the chips: later versions of the page.
- A child component, a key's declaration, any class or `data-*` hook, the CSS.
- `ui/src/cancel.ts`, `useSheet.ts` and `useApproval.ts`: the composable reads them as they are.
- A test of Cancel approve's and Discard's own bodies on the unit layer: their scenarios are `e2e`, held by the browser tests.
