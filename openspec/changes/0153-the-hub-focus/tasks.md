# The hub's focus — tasks

The focus's module with its tests, then the view's switch with the ratchet row. Each rule is written in its module with its test first ([D4](design.md#d4)).

## Progress

- [x] 1 — The focus's module and its tests · moderate
- [x] 2 — The view switches to it · moderate

## 1 — The focus's module and its tests

- [x] 1.1 Write `ui/src/composables/useHubFocus.test.ts`, first, with a test `spec('ui:hub:the-hub-keeps-its-focus', …)` of `restoredSpot`: with a held name it returns that spot, with a held name no longer there the first, with no source nothing. Import `restoredSpot` from `./useHubFocus`; pass sources as `{ name, digest }` and flows as names ([D2](design.md#d2)).
  Verify: `grep -n -F "ui:hub:the-hub-keeps-its-focus" ui/src/composables/useHubFocus.test.ts` prints its line.
- [x] 1.2 Add a test `spec('ui:hub:a-rendered-cell-opens-its-newest-image', …)`: a `sent` cell `{ digest, flow }` gives the spot of that source's row and that flow's column, over a held name; a `sent` cell no source holds gives the held name's spot.
  Verify: `grep -n -F "ui:hub:a-rendered-cell-opens-its-newest-image" ui/src/composables/useHubFocus.test.ts` prints its line.
- [x] 1.3 Add a test `spec('ui:hub:an-edge-row-shows-the-head', …)` of `useHubFocus`, with refs for the sources and the flows, a `grid` ref holding `{ querySelector: vi.fn(() => cell) }`, `reveal` and `remember` as `vi.fn()`, and `await nextTick()` after each move. Cast each stub with `as unknown as`, as `useEdges.test.ts` does. `place(5, 9, 'key')` clamps to the last row and column, calls `remember` with `spotName` of that spot, focuses the cell with `{ preventScroll: true }` and calls `reveal(cell, row, rows)`; `place(0, 0)` scrolls the cell `{ block: 'nearest' }`; `moveBy(1, 0)()` moves one row down; `place` over no sources changes nothing and does not call `remember`.
  Verify: `grep -n -F "ui:hub:an-edge-row-shows-the-head" ui/src/composables/useHubFocus.test.ts` prints its line.
- [x] 1.4 Create `ui/src/composables/useHubFocus.ts` as [D1](design.md#d1) and [D2](design.md#d2) say: `spotName`, `restoredSpot` and `useHubFocus`, each body the view's today (`Hub.vue` lines 273-316 and 392-406), `useHubFocus` returning `focus`, `selected`, `place`, `select` and `moveBy`. Import `clamp`, `kept` and `Focus` from `../grid`, and `at` from `../stores/collection`. It declares no keys ([D3](design.md#d3)).
  Verify: `uv run python -m tools.test_ui ui/src/composables/useHubFocus.test.ts` exits 0.
- [x] 1.5 Keep `useHubFocus.ts` free of any `useKeys` call ([D3](design.md#d3)).
  Verify: `grep -L "useKeys" ui/src/composables/useHubFocus.ts` prints `ui/src/composables/useHubFocus.ts`.
- [x] 1.6 Check the types and the spec bindings with the module in place and no reader yet.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
  Verify: `uv run pytest tests/test_spec_bindings.py` exits 0.

## 2 — The view switches to it

- [x] 2.1 In `ui/src/views/Hub.vue`, delete the refs `focus` and `selected`, and the functions `named`, `place`, `focusedCell`, `select` and `moveBy`. Call `useHubFocus({ sources, flows, grid, reveal, remember: (name) => (store.focus.hub = name) })` once, right after the `sources` computed, and take `focus`, `selected`, `place`, `select` and `moveBy` from it. The view keeps `grid`, `page`, `reveal` and its one `useKeys` call, its commands in today's order.
  Verify: `git grep -n "useHubFocus(" -- ui/src/views/Hub.vue` prints its line.
- [x] 2.2 In `Hub.vue`'s `onMounted`, replace the `spots`, `deletedFrom` and `kept` lines with `restoredSpot(sources.value, flows.value, sent, store.focus.hub)`. Keep the read of `window.history.state?.cell` and its `replaceState` as they are. Drop the imports `nextTick`, `clamp` and `kept` that nothing reads, and import `useHubFocus` and `restoredSpot`.
  Verify: `git grep -n -E "kept\(|clamp\(|nextTick" -- ui/src/views/Hub.vue` prints nothing.
- [x] 2.3 **HALT CHECK** In `tests/test_ratchets.py`, remove the row `"ui/src/views/Hub.vue": 622,` from `BIG_UI_FILES` and set `UI_ROWS = 1`. A failure means `Hub.vue` is still past the ceiling and [D5](design.md#d5) is wrong: halt, do not keep the row.
  Verify: `uv run pytest tests/test_ratchets.py` exits 0.
- [x] 2.4 Run the page's tests and types with the view switched. No existing test's assertion changed.
  Verify: `uv run python -m tools.test_ui` exits 0.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 2.5 Check the scenario bindings with the view switched.
  Verify: `uv run pytest tests/test_spec_bindings.py` exits 0.
