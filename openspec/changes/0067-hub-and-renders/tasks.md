# Tasks — 0067 hub and Renders

Source images, Home, cell actions, the Render bar, the Renders grid, then motion, per [design](design.md). Every
new pytest test carries `@pytest.mark.spec`, and every new vitest test `spec("…")`, with the key its task names.

## Progress

- [ ] 1 — Source images and the viewer
- [ ] 2 — Home
- [ ] 3 — Cell actions
- [ ] 4 — The Render bar
- [ ] 5 — The Renders grid
- [ ] 6 — Motion

## 1 — Source images and the viewer

- [ ] 1.1 **HALT CHECK** — no route serves a source by name.
  Verify: `grep -c '/api/b/{batch}/sources' isekai/interface/ui/app.py` prints `0`.
- [ ] 1.2 Add `source_thumbnail` and `Source.size` to `isekai/interface/ui/library.py`, the source routes to
  `isekai/interface/ui/app.py` and drop `_size`, per [D1](design.md#d1). Bind `ui:hub:a-source-is-sized-from-its-file`
  in `tests/test_ui_library.py` and `ui:renders:a-source-thumbnail-is-upright` in `tests/test_ui_api.py`.
  Verify: `uv run pytest -q tests/test_ui_library.py tests/test_ui_api.py` exits 0, and `cat tests/test_ui_library.py tests/test_ui_api.py | grep -c -E 'ui:hub:a-source-is-sized-from-its-file|ui:renders:a-source-thumbnail-is-upright'` prints `2`.
- [ ] 1.3 Add `ui/src/components/ImageViewer.vue` per [D2](design.md#d2), the source addresses to `ui/src/api.ts`,
  and the source cell of [D3](design.md#d3) to `ui/src/views/Hub.vue`.
  Verify: `uv run python -m tools.typecheck_ui` exits 0, and `grep -c 'ImageViewer' ui/src/views/Hub.vue` prints a number of at least `1`.
- [ ] 1.4 In `test_a_reload_lands_on_the_same_hub_and_the_same_review` in `tests/e2e/test_routes.py`, read
  `ada.jpg` from `.hub__file` instead of `.hub__name`.
  Verify: `grep -c 'hub__name' tests/e2e/test_routes.py` prints `0`, and `uv run pytest -q tests/e2e/test_routes.py` exits 0.
- [ ] 1.5 In `ui/design/spec.md` J2's grid bullet, say the source's thumbnail opens the viewer and its name is the
  file's stem.
  Verify: `grep -c 'opens the viewer' ui/design/spec.md` prints a number of at least `1`.

## 2 — Home

- [ ] 2.1 Add `thumbs` to `Row` in `isekai/interface/ui/library.py` per [D3](design.md#d3); bind
  `ui:batch-folder:a-row-names-its-first-sources` in `tests/test_ui_library.py`.
  Verify: `uv run pytest -q tests/test_ui_library.py` exits 0, and `grep -c 'ui:batch-folder:a-row-names-its-first-sources' tests/test_ui_library.py` prints `1`.
- [ ] 2.2 Draw each row's thumbnails and `+n`, and move *New batch* into the library's header row, in
  `ui/src/views/Home.vue`, with `thumbs` in `ui/src/types.ts`, per [D3](design.md#d3).
  Verify: `uv run python -m tools.typecheck_ui` exits 0, and `grep -c 'thumbs' ui/src/views/Home.vue` prints a number of at least `1`.
- [ ] 2.3 Move the first-start step out of `test_each_chosen_file_shows_its_upload_then_its_result` into a new
  `test_first_start_shows_new_batch_under_the_privacy_line` in `tests/e2e/test_import.py`, bound to
  `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`, per [D10](design.md#d10).
  Verify: `uv run pytest -q tests/e2e/test_import.py` exits 0, and `grep -c 'first-start-shows-new-batch-under-the-privacy-line' tests/e2e/test_import.py` prints `1`.
- [ ] 2.4 In `ui/design/spec.md` J7·1, put `[ New batch ⌥N ]` at the right of the `LIBRARY · 4 batches` line.
  Verify: `grep -c 'newest activity first.*New batch' ui/design/spec.md` prints `1`.

## 3 — Cell actions

- [ ] 3.1 **HALT CHECK** — a cell opens Review on a double-click.
  Verify: `grep -c '@dblclick' ui/src/views/Hub.vue` prints `1`.
- [ ] 3.2 Add `newest` to `Cell` in `isekai/interface/ui/library.py` and `HubCell` in `ui/src/types.ts` per [D4](design.md#d4),
  and to the rendered cells of `test_a_cells_stage_is_the_furthest_its_run_directory_holds` and `source` in
  `ui/src/composables/useQueue.test.ts`. Bind `ui:hub:a-cell-names-its-newest-image` in `tests/test_ui_library.py`.
  Verify: `uv run pytest -q tests/test_ui_library.py` exits 0, `uv run python -m tools.typecheck_ui` exits 0, and `grep -c 'ui:hub:a-cell-names-its-newest-image' tests/test_ui_library.py` prints `1`.
- [ ] 3.3 Add `action` to a new `ui/src/cells.ts`, bound to `ui:hub:a-click-follows-the-cells-stage` in a new
  `ui/src/cells.test.ts`; run it on a click and `↵` in `ui/src/views/Hub.vue`, per [D4](design.md#d4).
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c '@dblclick' ui/src/views/Hub.vue` prints `0`.
- [ ] 3.4 Push the large view with `state: { from: 'hub' }` from `ui/src/views/Hub.vue`, and send `Esc` and the back
  button to it in `ui/src/views/RenderLarge.vue`, per [D5](design.md#d5).
  Verify: `uv run python -m tools.typecheck_ui` exits 0, and `grep -c 'Back to Hub' ui/src/views/RenderLarge.vue` prints a number of at least `1`.
- [ ] 3.5 Add `test_a_rendered_cell_opens_its_newest_image` to `tests/e2e/test_render.py`, on the `SHOWN` batch's
  hub, bound to `ui:hub:a-rendered-cell-opens-its-newest-image`.
  Verify: `uv run pytest -q tests/e2e/test_render.py` exits 0, and `grep -c 'ui:hub:a-rendered-cell-opens-its-newest-image' tests/e2e/test_render.py` prints `1`.
- [ ] 3.6 In `test_a_reload_lands_on_the_same_hub_and_the_same_review` in `tests/e2e/test_routes.py`, replace the
  draft cell's click, `↵ review` and `Enter` with one click that opens its Review.
  Verify: `grep -c 'press("Enter")' tests/e2e/test_routes.py` prints `1`, and `uv run pytest -q tests/e2e/test_routes.py` exits 0.
- [ ] 3.7 Rewrite the `approved` comment in `ui/src/components/BatchRail.vue` to name `useQueue`'s count, read
  from the hub's statuses, per [D10](design.md#d10).
  Verify: `grep -c "server's own count" ui/src/components/BatchRail.vue` prints `0`.
- [ ] 3.8 In `ui/design/spec.md`, say in J2 that a click follows the stage, per [D4](design.md#d4)'s table, and in
  J5 that `Esc` goes back to where the large view was opened.
  Verify: `grep -c 'follows the stage' ui/design/spec.md` prints a number of at least `1`, and `grep -c 'where it was opened' ui/design/spec.md` prints a number of at least `1`.

## 4 — The Render bar

- [ ] 4.1 **HALT CHECK** — Render's reason sits in the hub's header.
  Verify: `grep -c 'data-render-reason' ui/src/views/Hub.vue` prints `1`.
- [ ] 4.2 Return `images` from `read_render_offer` in `isekai/interface/ui/app.py` per [D6](design.md#d6); in
  `test_with_every_count_rendered_render_is_disabled_naming_why` in `tests/test_ui_jobs.py`, assert `images` is `0`.
  Verify: `uv run pytest -q tests/test_ui_jobs.py` exits 0, and `grep -c 'offer\["images"\] == 0' tests/test_ui_jobs.py` prints `1`.
- [ ] 4.3 Add `bar` and `failed` to a new `ui/src/bars.ts`, bound to `ui:render:prepare-takes-the-bar-first` and
  `ui:events:a-hub-opened-after-a-failure-shows-it` in a new `ui/src/bars.test.ts`, per [D6](design.md#d6) and
  [D10](design.md#d10).
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c -E 'prepare-takes-the-bar-first|a-hub-opened-after-a-failure-shows-it' ui/src/bars.test.ts` prints `2`.
- [ ] 4.4 Add `ui/src/components/RenderBar.vue`, its button keeping `data-render`; draw it in `ui/src/views/Hub.vue`
  and `ui/src/views/Renders.vue`; drop the header's Render button; read `failed` with `immediate` in `Hub.vue`.
  Verify: `grep -c 'data-render-reason' ui/src/views/Hub.vue` prints `0`, and `uv run pytest -q tests/e2e/test_render.py tests/e2e/test_prepare.py` exits 0.
- [ ] 4.5 In `ui/design/spec.md`: rule 4 shows a reason only where the screen does not already show why; J2's
  header loses `[ Render 2 ⌥R ]` for the bar of [D6](design.md#d6); §6 drops *Every approved…*.
  Verify: `grep -c 'Every approved source × flow already has its Count' ui/design/spec.md` prints `0`, and `grep -c 'ready to render' ui/design/spec.md` prints a number of at least `1`.

## 5 — The Renders grid

- [ ] 5.1 **HALT CHECK** — the Renders payload names no ready count.
  Verify: `grep -c '"ready"' isekai/interface/ui/app.py` prints `0`.
- [ ] 5.2 Add `ready` to `read_renders` per [D7](design.md#d7), and the heading fields to `read_render` per
  [D8](design.md#d8). In `tests/test_ui_api.py`, bind `ui:renders:a-cell-counts-what-is-ready`, and read
  `ui:compare:a-version-is-named-by-what-changed` from rendered images' large views.
  Verify: `uv run pytest -q tests/test_ui_api.py` exits 0, and `grep -c 'ui:renders:a-cell-counts-what-is-ready' tests/test_ui_api.py` prints `1`.
- [ ] 5.3 Draw the grid of [D8](design.md#d8) in `ui/src/views/Renders.vue` — rows, badges, the damaged and ready
  tiles, the source column opening `ImageViewer` — and the heading in `ui/src/views/RenderLarge.vue`.
  Verify: `uv run python -m tools.typecheck_ui` exits 0, and `grep -c 'ImageViewer' ui/src/views/Renders.vue` prints a number of at least `1`.
- [ ] 5.4 In `tests/e2e/test_render.py`, select the grid's image as `[data-version='1'][data-seed='7']`, and add
  `test_a_source_opens_in_the_viewer` bound to `ui:renders:a-source-opens-in-the-viewer`.
  Verify: `uv run pytest -q tests/e2e/test_render.py` exits 0, and `grep -c 'ui:renders:a-source-opens-in-the-viewer' tests/e2e/test_render.py` prints `1`.
- [ ] 5.5 Say Renders reads oldest to newest with a ready count, and Render comes from its bar, in
  `isekai/interface/ui/README.md`; redraw J5·1's grid bullet and §6's *Renders · empty* in `ui/design/spec.md`.
  Verify: `grep -c 'newest first' isekai/interface/ui/README.md` prints `0`, `grep -c 'oldest to newest' ui/design/spec.md` prints a number of at least `1`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 6 — Motion

- [ ] 6.1 Add the running line, the segment pulse and their reduced-motion stop, with the import fill's, to
  `ui/src/app.css` per [D9](design.md#d9); mark the running Prepare bar in `ui/src/views/Hub.vue` and the running
  Render bar in `ui/src/components/RenderBar.vue`.
  Verify: `grep -c 'prefers-reduced-motion' ui/src/app.css` prints a number of at least `2`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 6.2 In `ui/design/spec.md` J2's PrepareBar bullet, state the running line, the pulse and their stop under
  `prefers-reduced-motion`.
  Verify: `grep -c 'prefers-reduced-motion' ui/design/spec.md` prints a number of at least `1`.
