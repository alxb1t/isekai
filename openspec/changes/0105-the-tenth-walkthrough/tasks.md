# Tasks — 0105 the tenth walkthrough

The drawer, then the sheet, per [design](design.md). Each new step carries the `spec` key its task names.

## Progress

- [x] 1 — The drawer
- [ ] 2 — The sheet

## 1 — The drawer

- [x] 1.1 In `ui/src/components/SessionDrawer.vue`, reveal a key's move by `useEdges` over `dialog`, and a grid's first
  row's `.session__collection` label `nearest` after it, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `grep -n -F -e 'useEdges(() => dialog.value)' -e 'cell.focus({ preventScroll: true })' -e 'reveal(cell, at.row, stack.value.last.length)' -e 'located(stack.value, at.row).row === 0' -e 'focus.value, move), true)' ui/src/components/SessionDrawer.vue` prints a line for each.
- [x] 1.2 In `tests/e2e/test_render.py`'s `test_the_drawer_holds_the_render`, add
  `@pytest.mark.spec("ui:sessions:an-edge-row-shows-the-head")` and the drawer's step of
  [the e2e steps](design.md#the-e2e-steps).
  Verify: `grep -n -F -e 'ui:sessions:an-edge-row-shows-the-head' -e '{"width": 800, "height": 520}' -e '[data-cell="0-0"]' tests/e2e/test_render.py` prints a line for each.

## 2 — The sheet

- [ ] 2.1 In `ui/src/components/ImportSheet.vue`, reveal a key's move among the tiles by `useEdges` over
  `.import__body`, per [D3](design.md#d3).
  Verify: `grep -n -F -e 'ref="scroller"' -e 'useEdges(() => scroller.value)' -e 'tile.focus({ preventScroll: true })' -e 'Math.ceil(shown.value.length / wide)' -e 'columns(), to), true)' ui/src/components/ImportSheet.vue` prints a line for each.
- [ ] 2.2 In `tests/e2e/test_import.py`'s `test_each_chosen_file_shows_its_upload_then_its_result`, add
  `@pytest.mark.spec("ui:sheet:an-edge-row-shows-the-head")` and the sheet's step of
  [the e2e steps](design.md#the-e2e-steps).
  Verify: `grep -n -F -e 'ui:sheet:an-edge-row-shows-the-head' -e '{"width": 560, "height": 520}' -e '.import__files > .section-label' tests/e2e/test_import.py` prints a line for each.
