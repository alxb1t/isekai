# Tasks — 0091 the sixth walkthrough

The bars, the import, the viewer, Review, then the dialogs, per [design](design.md). Each new test carries the `spec`
marker its task names. No `Verify:` runs `tests/e2e/`: the build collects them, and CI runs them.

## Progress

- [x] 1 — The bars
- [x] 2 — The import
- [x] 3 — The viewer
- [x] 4 — Review
- [ ] 5 — The dialogs

## 1 — The bars

- [x] 1.1 `_Job` in `isekai/interface/ui/jobs.py` counts each stage's completed cells against its total from `job.steps`,
  and the snapshot carries them, per [D1](design.md#d1); `test_ui_jobs.py`'s `ui:prepare:totals-count-cells-not-stages`
  test asserts a count per stage, a refused cell in none.
  Verify: `uv run pytest tests/test_ui_jobs.py -k totals` exits 0.
- [x] 1.2 Add `progress({done, of})` to `ui/src/bars.ts` and size the Prepare bar, the Render bar (`RenderBar.vue`) and the
  drawer's bar (`SessionDrawer.vue`) by it; `prepareTotals` in `ui/src/stores/live.ts` reads each stage. Add vitest in
  `ui/src/bars.test.ts` bound to `ui:sessions:one-progress-for-the-bar-and-the-drawer`.
  Verify: `grep -c 'function progress' ui/src/bars.ts` prints `1`, and `uv run python -m tools.test_ui` exits 0.
- [x] 1.3 The Prepare bar in `ui/src/views/Hub.vue` reads `<n> photographs to prepare in <collection>`, per
  [D2](design.md#d2); vitest bound to `ui:prepare:the-bar-names-its-photographs`. Update the strip's text that
  `tests/e2e/test_prepare.py` asserts to the per-stage form.
  Verify: `grep -c 'photographs to prepare in' ui/src/views/Hub.vue` prints a count above 0, and `uv run pytest --collect-only -q tests/e2e/test_prepare.py` exits 0.
- [x] 1.4 `ui/design/spec.md`'s Prepare bar and Render bar lines say what [D1](design.md#d1) and [D2](design.md#d2) make them.
  Verify: `grep -c 'photographs to prepare in' ui/design/spec.md` prints a count above 0.

## 2 — The import

- [x] 2.1 Add `remove(name)` to `Reader` in `isekai/pipeline/importing.py`, refused once sealed, and
  `DELETE /api/staging/{staged}/files/{name}` in `isekai/interface/ui/app.py` calling it, per [D3](design.md#d3); pytest
  bound to `import:stage:a-staged-file-is-removed-alone` in `tests/test_importing.py`.
  Verify: `uv run pytest tests/test_importing.py -k removed_alone` exits 0.
- [x] 2.2 Add `GET /api/staging/{staged}/files/{name}`, the cleaned file full size, to `isekai/interface/ui/app.py` and its
  module docstring's route list; a test in `tests/test_ui_api.py` beside the thumb's.
  Verify: `uv run pytest tests/test_ui_api.py -k staging` exits 0.
- [x] 2.3 In `ui/src/components/ImportSheet.vue`: the `×` on a read or skipped tile and `⌫` remove it, the focus moving
  to the next tile; `.import__tiles` in `ui/src/app.css` a CSS grid stepped by `moved`; `↵` opens the viewer full size.
  Add vitest in `ui/src/staging.test.ts` bound to `ui:sheet:the-tiles-take-the-keys` and `ui:sheet:a-chosen-file-is-removed-alone`.
  Verify: `sed -n '/^\.import__tiles {/,/}/p' ui/src/app.css | grep -c 'display: grid'` prints `1`, and `uv run python -m tools.test_ui` exits 0.

## 3 — The viewer

- [x] 3.1 `ImageViewer.vue` follows [D4](design.md#d4); add vitest in `ui/src/components/ImageViewer.test.ts` bound to
  `ui:viewer:enter-toggles-full-size` and `ui:viewer:full-size-scrolls-by-the-keys`.
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c 'full-size-scrolls-by-the-keys' ui/src/components/ImageViewer.test.ts` prints `1`.
- [x] 3.2 The hub's large view moves to `⇧↵` in `ui/src/views/Hub.vue` and in `test_a_rendered_cell_opens_its_newest_image`
  in `tests/e2e/test_render.py`.
  Verify: `grep -c 'Shift+Enter' tests/e2e/test_render.py` prints a count above 0, and `uv run pytest --collect-only -q tests/e2e/test_render.py` exits 0.

## 4 — Review

- [x] 4.1 `paneKeys` in `ui/src/panes.ts` follows [D5](design.md#d5). Rewrite the `ui:keys:review-moves-between-its-panes`
  test in `ui/src/panes.test.ts` to press `⌃L` through the key store with `isMac` stubbed; `ui/src/stores/keys.test.ts`'s
  Linux list stays `['left','right']`.
  Verify: `grep -c 'KeyL' ui/src/panes.test.ts` prints a count above 0, and `uv run python -m tools.test_ui` exits 0.
- [x] 4.2 Delete `⌃E` and `⌃Y` from `ui/src/views/Review.vue` and from `ui/design/spec.md`'s Review row.
  Verify: `grep -c "code: 'KeyE', ctrl: true" ui/src/views/Review.vue` prints `0`.
- [x] 4.3 ④ follows [D6](design.md#d6): `moveRenders` in `Review.vue` steps a grid by `moved`, `−`'s disabling passes the
  focus to `+`. Add vitest bound to `ui:review:four-is-one-grid-for-the-keys` and `ui:review:a-stepped-sheet-stays-in-view`.
  Verify: `grep -rl 'four-is-one-grid-for-the-keys' ui/src` names a test file, and `uv run python -m tools.test_ui` exits 0.
- [x] 4.4 Add `slot-down` and `slot-up` to D25's in-field list in `docs/decisions.md`.
  Verify: `sed -n '/^### D25 /,/^### D/p' docs/decisions.md | grep -c 'slot'` prints a count above 0.

## 5 — The dialogs

- [ ] 5.1 `KeyList.vue` is a modal `<dialog>` per [D7](design.md#d7), the key store exposing each entry's scope; vitest in
  `ui/src/stores/keys.test.ts` bound to `ui:dialogs:the-key-list-is-a-dialog`.
  Verify: `grep -c '<dialog' ui/src/components/KeyList.vue` prints `1`, and `uv run python -m tools.test_ui` exits 0.
- [ ] 5.2 The pick's width and head in `ComparePick.vue` and `ui/src/app.css` per [D7](design.md#d7); a step in
  `test_compare_shows_both_versions_of_a_seed_each_under_its_head`, under that test's own key, that moves the focus from
  an image to the photograph and asserts the pick's width does not change.
  Verify: `sed -n '/^\.pick {/,/}/p' ui/src/app.css | grep -c '720px'` prints `0`, and `uv run pytest --collect-only -q tests/e2e/test_render.py` exits 0.
- [ ] 5.3 The drawer's width in `ui/src/app.css` per [D7](design.md#d7); a step in `test_the_drawer_holds_the_render`,
  under that test's own key, asserting the drawer's width is at least `max(50vw, 480px)` and at most `100vw − 100px`.
  `ui/design/spec.md`'s pick, drawer and key-list lines say what they are.
  Verify: `grep -c 'calc(100vw - 100px)' ui/src/app.css` prints a count above 0, and `uv run pytest --collect-only -q tests/e2e` exits 0.
