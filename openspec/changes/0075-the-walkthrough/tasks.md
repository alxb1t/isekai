# Tasks — 0075 the walkthrough

Home, the hub, the kept focus, the large view, then Review, per [design](design.md). Every new pytest test carries
`@pytest.mark.spec`, and every new vitest test `spec("…")`, with the key its task names.

## Progress

- [x] 1 — Home's row
- [x] 2 — The hub
- [x] 3 — The kept focus
- [x] 4 — The large view
- [ ] 5 — Review's rail

## 1 — Home's row

- [x] 1.1 **HALT CHECK** — the count and the thumbnails share one container.
  Verify: `grep -c 'class="library__sources"' ui/src/views/Home.vue` prints `1`.
- [x] 1.2 Lay Home's row out per [D1](design.md#d1) in `ui/src/views/Home.vue` and `ui/src/app.css`.
  Verify: `grep -c 'class="library__sources"' ui/src/views/Home.vue` prints `0`, and `uv run pytest -q tests/e2e/test_import.py tests/e2e/test_routes.py` exits 0.

## 2 — The hub

- [x] 2.1 **HALT CHECK** — the hub's columns are the flows alone.
  Verify: `grep -c 'columns - 1' ui/src/views/Hub.vue` prints `1`.
- [x] 2.2 Add `images` to `Cell` in `isekai/interface/ui/library.py` from one listing per group per [D5](design.md#d5),
  with `ui/src/types.ts`; bind `ui:hub:a-cell-lists-its-images` in `tests/test_ui_library.py`.
  Verify: `uv run pytest -q tests/test_ui_library.py` exits 0, and `grep -c 'ui:hub:a-cell-lists-its-images' tests/test_ui_library.py` prints `1`.
- [x] 2.3 Add the source column, the cell's strip and the viewer from a cell to `ui/src/views/Hub.vue`, and `open` to
  `ui/src/components/ImageViewer.vue`, per [D3](design.md#d3) and [D5](design.md#d5).
  Verify: `grep -c 'columns - 1' ui/src/views/Hub.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 2.4 Extend `test_a_rendered_cell_opens_its_newest_image` in `tests/e2e/test_render.py` through the viewer to the
  large view; add `test_the_source_cell_opens_its_photograph`, bound to its key.
  Verify: `grep -c 'the-source-cell-opens-its-photograph' tests/e2e/test_render.py` prints `1`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.

## 3 — The kept focus

- [x] 3.1 **HALT CHECK** — the hub starts at its first cell on every mount.
  Verify: `grep -c 'place(0, 0)' ui/src/views/Hub.vue` prints `1`.
- [x] 3.2 Keep `focus.hub` and `focus.renders` in `ui/src/stores/batch.ts`, restored by `ui/src/views/Hub.vue` and
  `ui/src/views/Renders.vue`, per [D4](design.md#d4); bind `ui:renders:a-grid-keeps-its-focus` in `ui/src/stores/batch.test.ts`.
  Verify: `grep -c 'place(0, 0)' ui/src/views/Hub.vue` prints `0`, and `uv run python -m tools.test_ui` exits 0.
- [x] 3.3 Add the `Esc` steps of the design's [Tests](design.md#tests) to the rendered-cell test and
  `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from` in `tests/e2e/test_render.py`.
  Verify: `grep -c 'hub__cell--focused' tests/e2e/test_render.py` prints a number of at least `1`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.

## 4 — The large view

- [x] 4.1 **HALT CHECK** — the large view offers no *Side by side*.
  Verify: `grep -c 'Side by side' ui/src/views/RenderLarge.vue` prints `0`.
- [x] 4.2 Add `Side by side ⇧C` to `ui/src/views/RenderLarge.vue` per [D2](design.md#d2); add
  `test_side_by_side_sets_the_image_beside_its_photograph` to `tests/e2e/test_render.py`, bound to its key.
  Verify: `grep -c 'Side by side' ui/src/views/RenderLarge.vue` prints a number of at least `1`, and `grep -c 'side-by-side-sets-the-image-beside-its-photograph' tests/e2e/test_render.py` prints `1`.

## 5 — Review's rail

- [ ] 5.1 **HALT CHECK** — the rail names no other flow.
  Verify: `grep -c 'waiting' ui/src/composables/useQueue.ts` prints `0`.
- [ ] 5.2 Add `waiting` to `ui/src/composables/useQueue.ts` and the other flows' line to `ui/src/components/BatchRail.vue`
  per [D6](design.md#d6); bind `ui:review:the-rail-names-the-other-flows-waiting` in `ui/src/composables/useQueue.test.ts`.
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c 'the-rail-names-the-other-flows-waiting' ui/src/composables/useQueue.test.ts` prints `1`.
- [ ] 5.3 In `ui/design/spec.md`: J7·1's row per [D1](design.md#d1), J2's source column and strip, J5's *Side by side*,
  J3's rail head, and the job strip's line per [D7](design.md#d7).
  Verify: `grep -c 'one dot, then one item per running job' ui/design/spec.md` prints `1`, and `uv run pytest -q tests/test_docs.py` exits 0.
