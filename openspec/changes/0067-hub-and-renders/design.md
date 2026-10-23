# Design — 0067 hub and Renders

How sources are seen, how a cell acts, how Render is offered, and how Renders reads in time.
**Verdict: feasible** — every number the screens need is already counted by a stage or a listing; this change
serves it and draws it.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `47e0ec0` (`v0.40.1`):

- **Thumbnails** exist for renders only: `library.thumbnail` caches under `.cache/<run digest>/…`
  (`isekai/interface/ui/library.py:373-387`), served at `…/renders/{digest}/{flow}/{version}/{seed}/thumb`
  (`isekai/interface/ui/app.py:867-875`). `_shrunk` applies no orientation (`library.py:390-403`); the import preview
  does, with `ImageOps.exif_transpose` (`isekai/pipeline/importing.py:343-358`).
- **The hub's size** is `_size(run)`, null without a run (`app.py:1210-1218`). Source digests are cached by stat in
  `_DIGESTS` (`library.py:85`). `Row` carries no source names (`library.py:129-138`).
- **A cell** opens Review on `@dblclick` only (`ui/src/views/Hub.vue:433-434`), gated by `reviewable` (`:140-142`);
  its hint is always `↵ review` (`:464-468`). `stage()` reads only the newest approval's images
  (`library.py:455-462`).
- **Render** is a header button with `data-render-reason` beside it (`Hub.vue:378-387`). The offer returns only
  `disabled` (`app.py:449-458`). `Short.wanted` and `Short.images` (`isekai/interface/render.py:410-431`) and
  `shortfall` (`isekai/pipeline/generate.py:322-331`) count what is short.
- **Renders** draws `library.versions`, newest first (`library.py:302-341`, the `reversed` at `:320`), a heading per
  version (`ui/src/views/Renders.vue:198-209`). The large view shows `flow · vN · seed` (`ui/src/views/RenderLarge.vue:75-77`)
  and `Esc` always pushes Renders (`:51-53`).
- **Motion:** the spinner and the import bar's fill (`ui/src/app.css:716-737`, `:1676-1691`); the running segment is
  static (`:1758-1760`).
- **The cards:** `0062·R12` — `watch(job, …)` has no `immediate` (`Hub.vue:320-327`); `0064·R6` — the first-start
  step rides `test_each_chosen_file_shows_its_upload_then_its_result` (`tests/e2e/test_import.py:88-94`);
  `0061·R18` — the comment at `ui/src/components/BatchRail.vue:9-12`.

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_api.py` | 60 | `grep -c "def test_" tests/test_ui_api.py` |
| tests in `tests/test_ui_library.py` | 15 | `grep -c "def test_" tests/test_ui_library.py` |
| tests in `tests/test_ui_jobs.py` | 20 | `grep -c "def test_" tests/test_ui_jobs.py` |
| e2e tests | 17 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |
| vitest tests | 4 | `cat ui/src/*.test.ts ui/src/composables/*.test.ts \| grep -c "^spec("` |

## Goals / Non-Goals

**Goals:** every source seen; one click per cell; Render offered where the work is; Renders in time order; one
derivation per number. **Non-Goals:** Pinia; the key registry; Review's screens; Sessions; a second job slot.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `GET /api/b/{batch}/sources/{name}/thumb` and `GET /api/b/{batch}/sources/{name}`, the name resolved by `library.source_files`; `library.source_thumbnail` caches under `.cache/<digest>/sources/<digest>.jpg`, made upright; `library.Source` gains `size`, read from the file's header and cached by stat | an unassigned source has no run; a source keeps its orientation | serving through a run; sizing from `run.photo` |
| [D2](#d2) | `ui/src/components/ImageViewer.vue`: a native `<dialog>`, the image fitted; a click toggles 1:1, scrolling inside; `Esc` or a click outside closes; a title of name, dimensions and `fit n%` or `1:1` | one viewer, built once, adopted by Review later | a route; extending `PhotoOverlay` |
| [D3](#d3) | the hub's source cell: a 96×128 thumbnail, a render tile's size, opening the viewer, the stem in mono 13, `file · dims` in mono 11; `Row` gains `thumbs`, its first seven source names; Home draws them at 84×114, then `+n`; *New batch* moves into the library's header row | J2, J7·1; rule 2 | thumbnails in the library payload as data |
| [D4](#d4) | `library.Cell` gains `newest: {version, seed} \| null`; `ui/src/cells.ts` `action(cell)` returns `tick`, `review`, `sheet`, `view` or `none` with its hint; a click and `↵` run it; the checkbox's click does not reach the cell; no `@dblclick` | one table of stage → action, tested alone | a per-template condition |
| [D5](#d5) | a large view opened from a hub cell is pushed with `state: { from: 'hub' }`; `Esc` and the back button go to `history.state.from`, else Renders | the URL stays the image's | a query parameter |
| [D6](#d6) | the offer returns `{disabled, images}`, `images` summed from `render.short`; `ui/src/components/RenderBar.vue` on the hub and Renders; `ui/src/bars.ts` `bar(…)` decides `prepare`, `render` or none; the header's Render button and `data-render-reason` go; running, the bar shows the strip's totals and a link to `/session` | the render stage counts once; one forward action | a count in the browser |
| [D7](#d7) | `read_renders` gives each source `ready: {flow: n}` from `shortfall` on the newest approval; a refused `shortfall` is `0`, its version already marked damaged | the page and the render agree | `count - len(rendered)` in the browser |
| [D8](#d8) | `library.versions` stays newest first and `ui/src/views/Renders.vue` draws each cell reversed; a cell is one wrapped row of thumbnails, each with a `vN` badge and `⇄` when its seed is shared, a damaged version a striped tile before its images with its refusal under the cell, the ready tile last; `read_render` gains `came_from`, `kind`, `count` and `seeds`, drawn in the large view's label | the payload's order is a living scenario; the heading lives with the sheet | reordering the payload |
| [D9](#d9) | `.running` on a bar draws a 2 px accent line sliding along its top edge; the running segment pulses `accent-dim` ↔ `accent`; `prefers-reduced-motion` stops both and the import fill | the settled motion; the clock still ticks | animated dots |
| [D10](#d10) | `0062·R12`: `bars.ts` `failed(slot, batch)` read with `immediate`; `0064·R6`: the first-start step moves into its own test; `0061·R18`: the comment names `useQueue`'s count | the cards' fixes | |

### D1

```
GET /api/b/{batch}/sources/{name}/thumb ──▶ source_files(folder)(name) ──▶ .cache/<digest>/sources/<digest>.jpg
                                                                         (exif_transpose, then thumbnail_jpeg)
GET /api/b/{batch}/sources/{name}       ──▶ the file, whole
```

### D4

```
stage               click / ↵        hint
none · assigned     tick / untick    —
tagged · unreadable none             —
sheet · draft       Review           ↵ review
approved, no image  Review, read-only ↵ review
newest ≠ null       large view       ↵ view
```

### D6

```
changes waiting ─▶ Prepare bar
else images > 0 ─▶ Render bar   [ n ready to render  Render ⌥R ]   disabled: its reason
else render running ─▶ Render bar   [ image 1 of 2 · 06:41 of ≤10:30   Session ⌥4 ]
else none
```

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `ui:batch-folder:a-row-names-its-first-sources`, `ui:hub:a-source-is-sized-from-its-file`, `ui:hub:a-cell-names-its-newest-image`, `ui:renders:a-source-thumbnail-is-upright`, `ui:renders:a-cell-counts-what-is-ready`, `ui:renders:a-photograph-is-served-as-its-bytes`, `ui:render:a-refused-count-is-shown` | `ui:render:nothing-short-disables-render`, `ui:compare:a-version-is-named-by-what-changed`, `ui:renders:a-damaged-approval-marks-its-version` | `tests/test_ui_library.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py` |
| unit · vitest | `ui:hub:a-click-follows-the-cells-stage`, `ui:render:prepare-takes-the-bar-first`, `ui:events:a-hub-opened-after-a-failure-shows-it`, `ui:render:a-refused-count-is-shown` | none | `ui/src/cells.test.ts`, `ui/src/bars.test.ts` |
| e2e | `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`, `ui:hub:a-rendered-cell-opens-its-newest-image`, `ui:renders:a-source-opens-in-the-viewer`, `ui:renders:a-damaged-versions-images-are-drawn` | the grid selector in `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from`; the hub steps in `test_a_reload_lands_on_the_same_hub_and_the_same_review`; the damaged batch's Render bar step in `test_a_damaged_versions_images_are_drawn_and_hold_the_focus`; the selection step in `test_a_tick_assigns_the_flow_and_survives_a_reload` | `tests/e2e/test_import.py`, `tests/e2e/test_prepare.py`, `tests/e2e/test_render.py`, `tests/e2e/test_routes.py` |

**End-to-end runs added:** four tests, on Chromium only (T4), each shown only by a browser (T1). First start owns an
empty library, which no other test reaches. The rendered cell and the viewer each start on the `SHOWN` batch's hub
or grid; a test carries one scenario's marker, so neither is a step in the large-view test (T2). The damaged version
owns the `DAMAGED` batch, because a damaged approval in `SHOWN` would mark its hub cell unreadable and refuse its
large view; whether the grid draws what the focus moves across is a template's, which only a browser renders. Which
bar shows and what a click does are vitest units, not browser tests (T1).

**Removed or merged:** none. The first-start step leaves `test_each_chosen_file_shows_its_upload_then_its_result`
for its own test, which carries `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** reading every source's header on each hub read is slow on a large batch → the size is cached by stat,
  as the digest is.
- **[Risk]** a checkbox click also clicks its cell and toggles twice → the checkbox stops its click; the tick e2e
  test clicks the checkbox.
- **[Trade-off]** `history.state` is lost when a large view's address is pasted into a new tab → `Esc` falls back
  to Renders, which holds every image.
- **[Trade-off]** the viewer is built before Review uses it → `PhotoOverlay` stays until Review adopts the viewer.

## Verdict

**Feasible.** The counts exist in `render.short` and `shortfall`, the images in `sources/` and the runs; the change
serves them and draws them.
