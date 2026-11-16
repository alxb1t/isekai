---
bump: patch
after: [0152-the-run-split]
---

# The hub's focus

The hub's focus, its row selection and its restored spot move out of `Hub.vue` into `useHubFocus`, and the view's ratchet row goes, with behaviour unchanged.

Reading map: [design](design.md) holds the composable's shape, how each rule is tested and the view's line count, [tasks](tasks.md) holds the phases: the module with its tests, then the view's switch.

## Why

`Hub.vue` is a listed row of the page's ratchet ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)). Its focus and selection are state and handlers, not markup, so they move without touching a class or a `data-*` hook the browser tests select. With them out the view falls under the ceiling and its row goes.

## What Changes

- `ui/src/composables/useHubFocus.ts` is new. It holds `useHubFocus`, which owns the focus and the selection and their moves `place`, `select` and `moveBy`, and the pure `spotName` and `restoredSpot`.
- `ui/src/composables/useHubFocus.test.ts` is new. Each test binds an existing scenario whose text covers the rule it holds.
- `ui/src/views/Hub.vue` calls `useHubFocus`, keeps its template refs, its one `useKeys` call with the commands in today's order, and the read of the cell a large view sent.
- `tests/test_ratchets.py` loses the `Hub.vue` row, and the table's count falls with it.

No requirement changes: no key, class, `data-*` hook, route or text changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change declares `skip_specs: true`.

## Impact

- Code: `ui/src/views/Hub.vue` loses the moved lines; `ui/src/composables/useHubFocus.ts` holds them.
- Tests: `ui/src/composables/useHubFocus.test.ts` is added and `tests/test_ratchets.py` loses a row. No existing test's assertion changes.
- Documents: none names the focus's code, so none is amended.
- No format version, no re-pin and no image-frozen file changes.

## Not in this change

- Any class, `data-*` hook or key's declaration: the view keeps its `useKeys` call.
- A child component: `PrepareBar.vue` waits for the trigger that `Hub.vue` stays over its ceiling after this change.
- The tick, the act and the Prepare handlers: they stay in the view.
- The sheet's history, the panes and the chips: later versions.
- The CSS.
