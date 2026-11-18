# The review's panes — tasks

`panes.ts` gains the rules with their test, then `Review.vue` reads them. The text of each piece is in [design](design.md).

## Progress

- [x] 1 — The rules · moderate
- [x] 2 — The switch · moderate

## 1 — The rules

- [x] 1.1 In `ui/src/panes.ts`, add `PaneSelectors` and `SELECTORS` below `PANES`, as written in [D1](design.md#d1).
  Verify: `git grep -n -F "export const SELECTORS" -- ui/src/panes.ts` prints one line.
- [x] 1.2 In `ui/src/panes.ts`, add `NESTED` and `paneOf` below `nextPane`, as written in [D2](design.md#d2).
  Verify: `git grep -n -F "export function paneOf" -- ui/src/panes.ts` prints one line.
- [x] 1.3 In `ui/src/panes.test.ts`, import `paneOf` and `SELECTORS`, add `inside` above the test, and end the one test with the steps of [D4](design.md#d4): one `expect(paneOf(…)).toBe(…)` per row of its table, and the one `expect(SELECTORS).toEqual(…)` step under the table. Keep the test's key and its existing assertions as they are.
  Verify: `git grep -n -F "paneOf(" -- ui/src/panes.test.ts` prints the steps' lines.
- [x] 1.4 The steps pass against the rules of 1.1 and 1.2.
  Verify: `uv run python -m tools.test_ui ui/src/panes.test.ts` exits 0.

## 2 — The switch

- [x] 2.1 In `ui/src/views/Review.vue`, import `paneOf` and `SELECTORS` from `../panes` beside `nextPane`, delete `function paneOf` with its comment, and rewrite `entry` as written in [D3](design.md#d3).
  Verify: `git grep -n "function paneOf" -- ui/src/views/Review.vue` prints nothing.
- [x] 2.2 Leave `paneNow`, `remember`, `enter`, `movePane` and the view's one `useKeys` call as they are; `paneNow` and `remember` now call the imported `paneOf(`.
  Verify: `git grep -n -F "paneOf(" -- ui/src/views/Review.vue` prints one line in paneNow and one in remember.
- [x] 2.3 Leave no pane selector that the table holds in `entry`: `rail__card--current` is the table's alone.
  Verify: `git grep -n -F "rail__card--current" -- ui/src/views/Review.vue` prints nothing.
- [x] 2.4 The view types against the table's exports.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 2.5 Run `tests/test_spec_bindings.py` and `tests/test_ratchets.py` unchanged: the scenario's binding stands, and the page's table stays empty with `Review.vue` shorter.
  Verify: `uv run pytest tests/test_spec_bindings.py tests/test_ratchets.py` exits 0.
