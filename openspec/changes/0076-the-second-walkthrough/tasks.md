# Tasks — 0076 the second walkthrough

The layout, the keys, the dialogs, then the session grid, per [design](design.md). Every new pytest test carries
`@pytest.mark.spec`, and every new vitest test `spec("…")`, with the key its task names.

## Progress

- [x] 1 — The layout
- [x] 2 — The keys
- [ ] 3 — The dialogs
- [ ] 4 — The session grid

## 1 — The layout

- [x] 1.1 **HALT CHECK** — the key bar is on every screen.
  Verify: `grep -rl '<KeyBar' ui/src/views | wc -l` prints `9`.
- [x] 1.2 Make the hub's source cell a column and wrap source names per [D3](design.md#d3), in `ui/src/views/Hub.vue`,
  `ui/src/views/Renders.vue`, `ui/src/components/BatchRail.vue`, `ui/src/views/Home.vue` and `ui/src/app.css`.
  Verify: `grep -c 'overflow-wrap: anywhere' ui/src/app.css` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.3 Delete `ui/src/components/KeyBar.vue` and its uses; add the app bar's `?` button in `ui/src/App.vue`, per
  [D5](design.md#d5); recast `ui:keys:hints-come-from-the-declarations` in `ui/src/stores/keys.test.ts` to no key bar.
  Verify: `test -e ui/src/components/KeyBar.vue` exits 1, and `uv run python -m tools.test_ui` exits 0.

## 2 — The keys

- [x] 2.1 **HALT CHECK** — Renders' letters move by cell.
  Verify: `grep -c "'cell-'" ui/src/grid.ts` prints a number of at least `1`.
- [x] 2.2 Detect the platform in `ui/src/stores/keys.ts` and declare `⌃H` `⌃L` on macOS in `ui/src/views/Review.vue`, per
  [D1](design.md#d1); bind `ui:keys:review-panes-move-from-a-field-on-macos` and `ui:keys:an-esc-ending-a-composition-closes-nothing` in `ui/src/stores/keys.test.ts`.
  Verify: `grep -c -E 'review-panes-move-from-a-field-on-macos|an-esc-ending-a-composition-closes-nothing' ui/src/stores/keys.test.ts` prints `2`, and `uv run python -m tools.test_ui` exits 0.
- [x] 2.3 Rewrite `ui/src/grid.ts` and Renders' keys in `ui/src/views/Renders.vue` per [D6](design.md#d6); recast
  `ui:keys:renders-moves-by-cell-and-by-image` and bind `ui:keys:a-row-move-keeps-the-column` in `ui/src/grid.test.ts`.
  Verify: `grep -c "'cell-'" ui/src/grid.ts` prints `0`, and `grep -c 'a-row-move-keeps-the-column' ui/src/grid.test.ts` prints `1`.
- [x] 2.4 Add D25's macOS pair to `docs/decisions.md` per [D1](design.md#d1).
  Verify: `grep -c '⌃H' docs/decisions.md` prints a number of at least `1`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 3 — The dialogs

- [ ] 3.1 **HALT CHECK** — Compare names one image.
  Verify: `grep -c "path: '/b/:batch/renders/:digest/:flow/:version/:seed/compare'," ui/src/router.ts` prints `1`.
- [ ] 3.2 Close the Render dialog per [D4](design.md#d4) in `ui/src/components/RenderDialog.vue`, `ui/src/views/Hub.vue` and
  `ui/src/views/Renders.vue`.
  Verify: `grep -c 'closeDialog\|dialog.value = false' ui/src/components/RenderDialog.vue` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 3.3 Compare any pair per [D2](design.md#d2) in `isekai/interface/ui/app.py`, `ui/src/router.ts`,
  `ui/src/views/RenderLarge.vue`, `ui/src/views/Compare.vue` and `ui/src/components/ImageViewer.vue`; bind `ui:compare:any-two-images-of-a-cell` in `tests/test_ui_api.py`.
  Verify: `grep -c 'ui:compare:any-two-images-of-a-cell' tests/test_ui_api.py` prints `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [ ] 3.4 Add the steps of the design's [Tests](design.md#tests) to the grid, compare and render tests in
  `tests/e2e/test_render.py`.
  Verify: `grep -c 'different seeds' tests/e2e/test_render.py` prints a number of at least `1`, and `uv run pytest -q tests/e2e` exits 0.

## 4 — The session grid

- [ ] 4.1 **HALT CHECK** — the record plans nothing.
  Verify: `grep -c 'planned' isekai/interface/render.py` prints `0`.
- [ ] 4.2 Add `planned` to `SessionRecord` in `isekai/foundation/artifacts.py` and write it in `isekai/interface/render.py`
  per [D7](design.md#d7); bind `cli:render-session:the-record-plans-each-photograph` in `tests/test_render.py`.
  Verify: `grep -c 'planned' isekai/interface/render.py` prints a number of at least `1`, and `uv run pytest -q tests/test_render.py` exits 0.
- [ ] 4.3 Build the grid and its moves in `ui/src/sessions.ts` and draw them in `ui/src/views/SessionPage.vue` per
  [D7](design.md#d7); bind both `ui:sessions:` grid keys in a new `ui/src/sessions.test.ts`.
  Verify: `grep -c -E 'the-grid-holds-each-flow|the-grid-moves-by-photograph' ui/src/sessions.test.ts` prints `2`, and `uv run python -m tools.test_ui` exits 0.
- [ ] 4.4 Redraw `ui/design/spec.md`'s J2 source cell, rule 1, J5's Compare and J4's session page per [D3](design.md#d3),
  [D5](design.md#d5), [D2](design.md#d2) and [D7](design.md#d7).
  Verify: `grep -c 'bottom key bar' ui/design/spec.md` prints `0`, and `uv run pytest -q tests/test_docs.py` exits 0.
