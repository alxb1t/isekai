# Tasks — 0078 the third walkthrough

The layout, the keys, Review, the chooser, the large view, then the dialogs, per [design](design.md). Every new
pytest test carries `@pytest.mark.spec`, every new vitest test `spec(…)`, with the key its task names.

## Progress

- [x] 1 — The layout
- [x] 2 — Review's keys from a field
- [x] 3 — The approved revision and the waiting draft
- [x] 4 — The flow chooser
- [ ] 5 — The large view
- [ ] 6 — The dialogs

## 1 — The layout

- [x] 1.1 **HALT CHECK** — the Library names seven sources a row.
  Verify: `grep -c 'ROW_THUMBS = 7$' isekai/interface/ui/library.py` prints `1`.
- [x] 1.2 Set `ROW_THUMBS = 15` in `isekai/interface/ui/library.py` per [D3](design.md#d3); in `tests/test_ui_library.py`,
  `test_a_row_names_its_first_seven_sources_in_the_hubs_order` becomes `…_first_fifteen_…`, seventeen sources.
  Verify: `grep -c 'ROW_THUMBS = 15$' isekai/interface/ui/library.py` prints `1`, and `uv run pytest -q tests/test_ui_library.py` exits 0.
- [x] 1.3 Redraw the hub's row in `ui/src/views/Hub.vue` and `ui/src/app.css` per [D1](design.md#d1); in
  `tests/e2e/test_routes.py` find the source by `.hub__name`.
  Verify: `grep -c 'hub__file' ui/src/views/Hub.vue ui/src/app.css tests/e2e/test_routes.py` prints `0` for each file, and `uv run pytest -q tests/e2e/test_routes.py` exits 0.
- [x] 1.4 Add the step to `test_the_source_cell_opens_its_photograph` in `tests/e2e/test_render.py`: with the source
  cell focused, `.hub__thumb`'s bottom equals the row's `.hub__images` bottom.
  Verify: `grep -c 'hub__images' tests/e2e/test_render.py` prints a number of at least `1`, and `uv run pytest -q tests/e2e/test_render.py -k source_cell` exits 0.
- [x] 1.5 Draw Renders' source cell as the thumbnail alone in `ui/src/views/Renders.vue` and `ui/src/app.css` per
  [D2](design.md#d2).
  Verify: `grep -c 'renders__name' ui/src/views/Renders.vue ui/src/app.css` prints `0` for each file, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.6 In `ui/design/spec.md`: J2's grid drawing loses its `file · dims` lines; its grid bullet's ``then mono 11
  `file · dims`, the size read from the file,`` → `the size in the viewer's title,`; the Renders bullet loses `, and
  its name`; Home's `up to seven` → `up to fifteen`.
  Verify: `grep -c 'file · dims' ui/design/spec.md` prints `0`, and `grep -c 'up to fifteen' ui/design/spec.md` prints `1`.

## 2 — Review's keys from a field

- [x] 2.1 **HALT CHECK** — the key list opens on `?` alone.
  Verify: `grep -c "keys: \[shifted('Slash')\]" ui/src/App.vue` prints `1`.
- [x] 2.2 Open the key list on `⌃/` per [D6](design.md#d6) in `ui/src/App.vue` and `ui/src/components/KeyList.vue`;
  bind `ui:keys:the-key-list-opens-from-a-field` in `ui/src/stores/keys.test.ts`.
  Verify: `grep -c "shifted('Slash')" ui/src/App.vue ui/src/components/KeyList.vue` prints `0` for each file, and `grep -c 'ui:keys:the-key-list-opens-from-a-field' ui/src/stores/keys.test.ts` prints `1`.
- [x] 2.3 Add `field-down` and `field-up` to `paneKeys` in `ui/src/panes.ts` and route them in `ui/src/views/Review.vue`
  and `ui/src/components/TagInput.vue` per [D5](design.md#d5); bind `ui:keys:review-fields-move-from-a-field-on-macos`
  in `ui/src/stores/keys.test.ts`.
  Verify: `grep -c "'field-down'" ui/src/panes.ts` prints `1`, and `grep -c 'review-fields-move-from-a-field-on-macos' ui/src/stores/keys.test.ts` prints `1`.
- [x] 2.4 Declare `⌃P` and delete Review's `photo` and `side-by-side` commands in `ui/src/views/Review.vue` per
  [D4](design.md#d4); in `tests/e2e/test_review.py` open the viewer by `Control+P` from a tag field in
  `test_the_photograph_opens_in_the_viewer`; in `tests/e2e/test_render.py` press `Control+P` twice in
  `test_side_by_side_shows_the_pair`.
  Verify: `grep -c "code: 'KeyP', ctrl: true" ui/src/views/Review.vue` prints `1`, and `uv run python -m tools.test_ui` exits 0, and `uv run pytest -q tests/e2e/test_review.py tests/e2e/test_render.py` exits 0.
- [x] 2.5 In `ui/design/spec.md` §7: the intro's `` `?` lists them`` → `` `⌃/` lists them``; the *everywhere* row's
  `? the key list` → `⌃/ the key list, from a field too`; the Review row's `↵ on the photograph opens the viewer, ← → its
  photographs` → `⌃P the photograph, on a revision Side by side, from a field too, ← → its photographs`, its
  `⇧C *Side by side*, the photograph and the render, on a revision` deleted, and `⌃J ⌃K the fields from a field on
  macOS` added after `⌃H ⌃L`.
  Verify: `grep -c '⌃/ the key list' ui/design/spec.md` prints `1`, and `grep -c '⌃J ⌃K the fields' ui/design/spec.md` prints `1`.
- [x] 2.6 In `docs/decisions.md` D25's rule, `` and `Mod+K` run, and on macOS Review's `⌃H` and `⌃L`, which move between
  its panes.`` → ``, `Mod+K` and `⌃/` run, Review's `⌃P`, and on macOS Review's `⌃H` `⌃L`, which move between its panes,
  and `⌃J` `⌃K`, which move between its fields.``; its *Made by* gains `` `0078` ``.
  Verify: `grep -c "Review's .⌃P." docs/decisions.md` prints `1`, and `grep -c '0076., .0078' docs/decisions.md` prints `1`.

## 3 — The approved revision and the waiting draft

- [x] 3.1 **HALT CHECK** — Review drops a revision once read-only.
  Verify: `grep -c 'sheet.readonly.value ? null : (sheet.detail.value?.revision' ui/src/views/Review.vue` prints `1`.
- [x] 3.2 Compute `revision` for the approval in `read_input` (`isekai/interface/ui/app.py`) and keep it in
  `ui/src/views/Review.vue` per [D7](design.md#d7); bind `ui:revise:an-approved-revision-keeps-its-image` in
  `tests/test_ui_api.py`.
  Verify: `grep -c 'ui:revise:an-approved-revision-keeps-its-image' tests/test_ui_api.py` prints `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [x] 3.3 Answer a waiting draft in `post_revise` (`isekai/interface/ui/app.py`) and open it from
  `ui/src/components/ReviseConfirm.vue`, with `ui/src/api.ts` and `ui/src/types.ts`, per [D8](design.md#d8); bind
  `ui:revise:a-waiting-draft-is-opened` in `tests/test_ui_api.py`.
  Verify: `grep -c 'ui:revise:a-waiting-draft-is-opened' tests/test_ui_api.py` prints `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 3.4 In `test_revise_opens_review_on_the_revision` (`tests/e2e/test_render.py`), after *Approve sheet*, the
  `[data-revised] img` is still shown.
  Verify: `uv run pytest -q tests/e2e/test_render.py -k revise_opens_review` exits 0.
- [x] 3.5 In `ui/design/spec.md` J5: *The revision's sheet* bullet adds `, and keeps them once approved`; the Revise
  bullet adds `An image whose flow holds a waiting draft opens Review on that draft, writing nothing.`
  Verify: `grep -c 'keeps them once approved' ui/design/spec.md` prints `1`, and `grep -c 'holds a waiting draft opens Review' ui/design/spec.md` prints `1`.

## 4 — The flow chooser

- [x] 4.1 **HALT CHECK** — Review jumps to the next flow on `⇧F`.
  Verify: `grep -c "id: 'next-flow'" ui/src/views/Review.vue` prints `1`.
- [x] 4.2 Add `flowsWaiting` to `ui/src/composables/useQueue.ts` per [D9](design.md#d9); in
  `ui/src/composables/useQueue.test.ts` bind `ui:review:two-flows-waiting-open-the-chooser` and give
  `ui:review:a-batch-opens-its-head` its one flow.
  Verify: `grep -c 'two-flows-waiting-open-the-chooser' ui/src/composables/useQueue.test.ts` prints `1`, and `uv run python -m tools.test_ui` exits 0.
- [x] 4.3 Draw the chooser in `ui/src/views/ReviewHead.vue`, return to it on `Esc` and delete `next-flow` and
  `nextFlow` in `ui/src/views/Review.vue`, and name `⇧R` in `ui/src/components/BatchRail.vue`, per [D9](design.md#d9).
  Verify: `grep -c "id: 'next-flow'" ui/src/views/Review.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 4.4 Add a batch whose source holds an unapproved sheet in summon and in conjure to `tests/e2e/conftest.py`, and
  `test_the_chooser_opens_a_flow` to `tests/e2e/test_queue.py`, bound to `ui:review:the-chooser-opens-a-flow`.
  Verify: `grep -c 'the-chooser-opens-a-flow' tests/e2e/test_queue.py` prints `1`, and `uv run pytest -q tests/e2e/test_queue.py` exits 0.
- [x] 4.5 In `ui/design/spec.md`: the Review row's `⇧F the next flow holding unapproved sheets · ` deleted; J3 opens on
  a sentence: `With two or more flows waiting, the Review tab is a chooser, a row per flow; ↵ opens its head, esc on
  Review returns.`
  Verify: `grep -c '⇧F the next flow' ui/design/spec.md` prints `0`, and `grep -c 'the Review tab is a chooser' ui/design/spec.md` prints `1`.

## 5 — The large view

- [ ] 5.1 **HALT CHECK** — the large view revises on a plain `e`.
  Verify: `grep -c "keys: plain('KeyE')" ui/src/views/RenderLarge.vue` prints `1`.
- [ ] 5.2 Shift `revise` and `draft-from` in `ui/src/views/RenderLarge.vue` and `revise` in `ui/src/views/Renders.vue`
  per [D10](design.md#d10); press `Shift+E` in `test_revise_opens_review_on_the_revision` and `Shift+F` in
  `test_conjure_from_this_opens_review` (`tests/e2e/test_render.py`).
  Verify: `grep -c "plain('KeyE')" ui/src/views/RenderLarge.vue ui/src/views/Renders.vue` prints `0` for each file, and `grep -c "plain('KeyF')" ui/src/views/RenderLarge.vue` prints `0`.
- [ ] 5.3 Add `pick` to `ui/src/cells.ts` and bind `ui:compare:one-other-image-is-compared-at-once` in
  `ui/src/cells.test.ts`; draw the pick in a new `ui/src/components/ComparePick.vue` opened from
  `ui/src/views/RenderLarge.vue`, and drop `action` from `ui/src/components/ImageViewer.vue`, per [D11](design.md#d11);
  pick by tile in `test_compare_shows_both_versions_of_a_seed_and_the_field_that_changed`.
  Verify: `grep -c 'one-other-image-is-compared-at-once' ui/src/cells.test.ts` prints `1`, and `grep -c 'action' ui/src/components/ImageViewer.vue` prints `0`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.
- [ ] 5.4 Lay `.large__actions` out as the grouped column above the fields in `ui/src/views/RenderLarge.vue` and
  `ui/src/app.css` per [D12](design.md#d12).
  Verify: `grep -c 'large__group' ui/src/views/RenderLarge.vue` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 5.5 In `ui/design/spec.md`: the Renders row's `e Revise` → `⇧E Revise` in both places, `f Conjure from this` →
  `⇧F Conjure from this`, `c compare` → `c Compare with…`; J5's `e Revise this image` → `⇧E Revise this image`;
  `` `Compare…  c` `` → `` `Compare with…  c` `` in J5's table and its large-view bullet, which says the pick is a
  dialog of tiles and one other image compares at once.
  Verify: `grep -c '⇧E Revise' ui/design/spec.md` prints a number of at least `2`, and `grep -c 'Compare…  c' ui/design/spec.md` prints `0`.
- [ ] 5.6 In `docs/decisions.md` D25's rule, `` `⇧`+letter for a command,`` → `` `⇧`+letter for a command, always for
  one that writes,``.
  Verify: `grep -c 'always for' docs/decisions.md` prints a number of at least `1`, and `grep -c 'one that writes' docs/decisions.md` prints `1`.

## 6 — The dialogs

- [ ] 6.1 **HALT CHECK** — the Render dialog is no `<dialog>`.
  Verify: `grep -c '<dialog' ui/src/components/RenderDialog.vue` prints `0`.
- [ ] 6.2 Render `ui/src/components/RenderDialog.vue`, `ui/src/components/ReviseConfirm.vue` and
  `ui/src/components/ImportSheet.vue` as modal `<dialog>`s with their first focus per [D13](design.md#d13).
  Verify: `grep -c 'showModal' ui/src/components/RenderDialog.vue ui/src/components/ReviseConfirm.vue ui/src/components/ImportSheet.vue` prints `1` for each file, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 6.3 Add `test_the_render_dialog_opens_on_its_checkbox` to `tests/e2e/test_render.py`, bound to
  `ui:dialogs:the-render-dialog-opens-on-its-checkbox`, on the `RENDER` batch, cancelled.
  Verify: `grep -c 'the-render-dialog-opens-on-its-checkbox' tests/e2e/test_render.py` prints `1`, and `uv run pytest -q tests/e2e` exits 0.
- [ ] 6.4 Add rule 11 to `ui/design/spec.md` §1: `**A dialog holds the focus** while open — on its first control, the
  page behind inert — and gives it back on close.`
  Verify: `grep -c 'A dialog holds the focus' ui/design/spec.md` prints `1`.
