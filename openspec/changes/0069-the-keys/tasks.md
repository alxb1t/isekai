# Tasks — 0069 the keys

The registry, the screens, Review, then the dialogs, per [design](design.md). Every new vitest test carries
`spec("…")`, and every new pytest test `@pytest.mark.spec`, with the key its task names.

## Progress

- [x] 1 — The registry
- [x] 2 — The screens
- [ ] 3 — Review
- [ ] 4 — The dialogs

## 1 — The registry

- [x] 1.1 **HALT CHECK** — no key store exists, and the shell matches Option.
  Verify: `test -e ui/src/stores/keys.ts` exits 1, and `grep -c 'altKey' ui/src/App.vue` prints `1`.
- [x] 1.2 Add `ui/src/stores/keys.ts` and `ui/src/composables/useKeys.ts` per [D1](design.md#d1), with the field
  rule of [D2](design.md#d2) and the `Esc` order of [D3](design.md#d3); install the one listener in `ui/src/App.vue`.
  Verify: `grep -c 'useKeyStore' ui/src/App.vue` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.3 Declare the everywhere keys of [D4](design.md#d4) in `ui/src/App.vue`, its Option branch gone; add
  `ui/src/components/KeyList.vue` on `?` and `ui/src/components/KeyHint.vue` per [D6](design.md#d6).
  Verify: `grep -c 'altKey' ui/src/App.vue` prints `0`, and `test -e ui/src/components/KeyList.vue` exits 0.
- [x] 1.4 Bind the `ui:keys:` scenarios of `ui/src/stores/keys.test.ts` named in the design's [Tests](design.md#tests).
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c "spec('ui:keys:" ui/src/stores/keys.test.ts` prints `6`.
- [x] 1.5 In `test_a_tag_is_committed_from_the_ranked_autocomplete` in `tests/e2e/test_review.py`, press `Escape`, then
  `Shift+KeyH`, where it pressed `Alt+Digit1`.
  Verify: `grep -c 'Alt+Digit1' tests/e2e/test_review.py` prints `0`, and `uv run pytest -q tests/e2e/test_review.py` exits 0.
- [x] 1.6 Rewrite D25 in `docs/decisions.md` per [D8](design.md#d8), and the *everywhere* row of `ui/design/spec.md` §7.
  Verify: `grep -c 'Option shortcuts match the physical key' docs/decisions.md` prints `0`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 2 — The screens

- [x] 2.1 **HALT CHECK** — the hub listens for keys itself.
  Verify: `grep -c "addEventListener('keydown'" ui/src/views/Hub.vue` prints `1`.
- [x] 2.2 Add `ui/src/grid.ts`, the Renders movement of [D4](design.md#d4), bound to
  `ui:keys:renders-moves-by-cell-and-by-image` in a new `ui/src/grid.test.ts`.
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c 'renders-moves-by-cell-and-by-image' ui/src/grid.test.ts` prints `1`.
- [x] 2.3 Move `ui/src/views/Home.vue`, `ui/src/views/Hub.vue`, `ui/src/views/Renders.vue`, `ui/src/views/RenderLarge.vue`,
  `ui/src/views/Compare.vue` and `ui/src/views/Session.vue` onto `useKeys` with the map of [D4](design.md#d4), each
  with `ui/src/components/KeyBar.vue`; their hints through `KeyHint`, `ui/src/components/RenderBar.vue`'s too.
  Verify: `grep -c "addEventListener('keydown'" ui/src/views/Home.vue ui/src/views/Hub.vue ui/src/views/Renders.vue ui/src/views/RenderLarge.vue ui/src/views/Compare.vue` prints `0` for each file, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 2.4 In `tests/e2e/test_render.py`, press `e` where it pressed `Alt+KeyE`; in `README.md`, Revise's key reads `e`.
  Verify: `grep -c 'Alt+KeyE' tests/e2e/test_render.py` prints `0`, `grep -c '⌥E' README.md` prints `0`, and `uv run pytest -q tests/e2e` exits 0.
- [x] 2.5 Rewrite the *Home*, *Hub* and *Renders* rows of `ui/design/spec.md` §7 per [D4](design.md#d4).
  Verify: `grep -c '⌥A Add sources' ui/design/spec.md` prints `0`.

## 3 — Review

- [ ] 3.1 **HALT CHECK** — Review has three panes.
  Verify: `grep -c "PANES: Pane\[\] = \['rail', 'source', 'sheet'\]" ui/src/views/Review.vue` prints `1`.
- [ ] 3.2 Add `ui/src/panes.ts` per [D5](design.md#d5), bound to `ui:keys:review-moves-between-its-panes` in a new
  `ui/src/panes.test.ts`.
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c 'review-moves-between-its-panes' ui/src/panes.test.ts` prints `1`.
- [ ] 3.3 Move `ui/src/views/Review.vue` onto `useKeys` per [D4](design.md#d4) and [D5](design.md#d5), with a
  `KeyBar`; the tag cheatsheet on `Mod+K`; the hints in `ui/src/components/SourcePanel.vue`,
  `ui/src/components/PhotoOverlay.vue` and `ui/src/components/CheatsheetOverlay.vue` through `KeyHint`.
  Verify: `grep -c 'altKey' ui/src/views/Review.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 3.4 In `tests/e2e/test_review.py`, open the tag cheatsheet with `ControlOrMeta+KeyK`, the test renamed
  `test_mod_k_opens_the_cheatsheet`; add `test_a_command_waits_until_the_field_is_left`, bound to its `ui:keys:` key.
  Verify: `grep -c 'Alt+Space' tests/e2e/test_review.py` prints `0`, and `uv run pytest -q tests/e2e/test_review.py` exits 0.
- [ ] 3.5 Rewrite the *Review* row of `ui/design/spec.md` §7 per [D4](design.md#d4) and [D5](design.md#d5).
  Verify: `grep -c '⌥Space' ui/design/spec.md` prints `0`.

## 4 — The dialogs

- [ ] 4.1 **HALT CHECK** — Cancel stays live while Import commits.
  Verify: `grep -c 'committing' ui/src/components/ImportSheet.vue` prints `5`.
- [ ] 4.2 Move `ui/src/components/ImportSheet.vue`, `ui/src/components/RenderDialog.vue`,
  `ui/src/components/ReviseConfirm.vue` and `ui/src/components/ImageViewer.vue` onto `useKeys` as overlays per [D4](design.md#d4); hold
  the import sheet's Cancel and `Esc` while `committing` per [D7](design.md#d7); `RefusalPage.vue`'s hint by `KeyHint`.
  Verify: `grep -rc "addEventListener('keydown'" ui/src/components` prints `0` for each file, and `grep -c 'altKey' ui/src/components/ReviseConfirm.vue` prints `0`.
- [ ] 4.3 Move the in-flight step out of `test_importing_a_new_batch_opens_its_hub_with_every_source_unassigned`
  into a new `test_a_commit_in_flight_holds_the_sheet` in `tests/e2e/test_import.py`, also pressing `Escape`.
  Verify: `grep -c 'a-commit-in-flight-holds-the-sheet' tests/e2e/test_import.py` prints `1`, and `uv run pytest -q tests/e2e/test_import.py` exits 0.
- [ ] 4.4 Rewrite every other `⌥` key in `ui/design/spec.md` per [D4](design.md#d4), and its *dialogs* row.
  Verify: `grep -c '⌥' ui/design/spec.md` prints `0`.
