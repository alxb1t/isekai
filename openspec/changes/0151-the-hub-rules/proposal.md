---
bump: patch
after: [0150-the-server-seams]
---

# The hub's rules

The hub's pure rules leave `ui/src/views/Hub.vue` for `bars.ts` and `cells.ts`, each with its test first where a scenario covers it, and the view switches to them.

Reading map: [design](design.md) holds where each rule lands and what tests it, [tasks](tasks.md) its phases.

## Why

`Hub.vue`'s script holds the Prepare bar's words, the stage track, the cell's word and hint and the changes rule. Vitest cannot import a view's setup locals, so a plain script block exists only to let a test reach its functions, and the other rules have no test at all. Moving the rules to plain modules puts them where a test can read them and takes them out of the file that the ratchet lists ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).

## What Changes

- `ui/src/bars.ts` gains `toPrepare` and `prepareButton`; `ui/src/bars.test.ts` takes the one case of `ui/src/views/Hub.test.ts`, assertions unchanged, and that file is deleted.
- `ui/src/cells.ts` gains `cellOf`, `changesOf`, `reviewable` and `hintOf`, each written with its test first, bound to the scenario whose text covers it.
- `ui/src/cells.ts` gains the stage track's tables `SEGMENTS`, `DONE` and `RUNNING`, and `wordOf`, `segmentClass` and `stem`, which no scenario covers and which move untested ([D3](design.md#d3)).
- `ui/src/views/Hub.vue` switches to them and keeps its template, classes, `data-*` hooks and keys as they are.
- No requirement is touched: the change carries `skip_specs: true` and an empty `specs/`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Code: `ui/src/views/Hub.vue`, `ui/src/bars.ts`, `ui/src/cells.ts`.
- Tests: `ui/src/bars.test.ts`, `ui/src/cells.test.ts`, `ui/src/views/Hub.test.ts` deleted, the `Hub.vue` row's number in `tests/test_ratchets.py`.
- Documents: none is made false; no document names where these rules live.

## Not in this change

- The hub's focus, selection, `place`, `select`, `moveBy` and the restored spot: state, not rules. They move to a composable when `Hub.vue` must fall under its ceiling, and its ratchet row goes with them.
- `Review.vue`, its rules and its actions, and the sheet's history.
- The panes, the lens' DOM code and the chips; a child component; a key's declaration; any class or `data-*` hook; the CSS.
