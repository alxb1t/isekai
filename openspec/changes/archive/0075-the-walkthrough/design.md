# Design — 0075 the walkthrough

How each finding of the manual pass after `v0.47.0` is closed.
**Verdict: feasible** — the viewer, its pair mode, the batch store and the output listings exist; the change reuses
them.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `40e9eb7` (`v0.47.0`):

- **Home's row** is a four-column grid, name · sources · chips · last activity (`ui/src/app.css:715-717`);
  `library__sources` holds the count and the thumbnails (`ui/src/views/Home.vue:134-149`).
- **The large view** offers *Compare with vN* on `c` (`ui/src/views/RenderLarge.vue:65-69`, `:129`); the design spec's
  J5 promises "the photograph a key away (⇧C)" (`ui/design/spec.md:324`); `ImageViewer` has a pair mode (`pair?`,
  `ui/src/components/ImageViewer.vue:19`), which Review's *Side by side* opens (`ui/src/views/Review.vue:94`, `:127`,
  `:474-477`); the run's photograph is `GET …/review/{digest}/{flow}/photo` (`isekai/interface/ui/app.py:703`).
- **The hub:** `place` clamps the column to the flows (`ui/src/views/Hub.vue:258-264`); the source thumbnail opens the
  viewer on a click only (`:33`, `:361-370`, `:401`); a rendered cell's action opens the newest image's large view
  (`act`, `:180-187`); `place(0, 0)` on every mount (`:352`); the large view is pushed with `state: { from: 'hub' }`
  (`:174`).
- **Renders** starts at `{row: 0, column: 0}` and focuses the first filled cell on mount (`ui/src/views/Renders.vue:30`,
  `:192-201`).
- **The cell:** `library.Cell` carries `renders` and `newest` (`isekai/interface/ui/library.py:170`); `stage` lists the
  newest group for `renders` and `_newest_image` lists the groups again (`:571-595`, `:630`) — `0070·R13`.
- **Review's tab** counts every flow's unapproved sheets (`ui/src/App.vue:57-60`); the rail lists the open flow's
  (`ui/src/components/BatchRail.vue`, `rail` in `ui/src/composables/useQueue.ts`).
- **`0070·R14`:** Review's *Side by side* test and the Discard test each open the revision (`tests/e2e/test_render.py`).
- **`0074·R7`:** the design spec gives each job-strip item its own dot; the strip draws one.

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_library.py` | 20 | `grep -c "def test_" tests/test_ui_library.py` |
| e2e tests | 27 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |
| vitest tests | 31 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -c "^spec("` |

## Goals / Non-Goals

**Goals:** close the six findings with what exists. **Non-Goals:** Renders' grid layout; a dialog besides the viewer;
what the Review tab counts.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Home's row: a header line — `library__name`, `library__meta` (`n sources`), `library__chips` inline and wrapping, `library__when` with `open ↵` at the right — over `library__thumbs`, which take the full width; the inert row unchanged | the operator's layout | the four-column grid |
| [D2](#d2) | the large view gains `Side by side ⇧C` beside `Compare with vN c`: `ImageViewer` with `pair`, the run's photograph and this image | Review's name; the key the spec promises | a new dialog |
| [D3](#d3) | the hub's grid gains the source column as column `0`, flows from `1`; `↵` on it opens the viewer on its photograph, stepping the batch's sources; `Space` does nothing there; `⇧J` `⇧K` select from it; its hint reads *view photo* | as Review's viewer steps its rail | a separate key |
| [D4](#d4) | the batch store keeps `focus.hub` and `focus.renders` for the open batch, written on every move; each view restores its own on mount when that spot exists, else the first | one memory for `Esc`, Back and tabs | a router state per push |
| [D5](#d5) | `Cell.images: [{version, seed}]`, oldest to newest, from the one listing `stage` makes per group, `renders` and `newest` read from it (`0070·R13`); the cell draws them under the stage track at `--tile-width` × `--tile-height`, each marked `vN`, wrapping; a click on the cell or `↵` opens `ImageViewer` on the newest, a click on a thumbnail on that one; `ImageViewer` gains `open(index)`, which the hub sets to push the large view | the existing viewer; one listing | a hub dialog |
| [D6](#d6) | `useQueue.waiting(hub, flow)` gives each other flow's unapproved count; `BatchRail`'s head adds `<flow> · n waiting ⇧F` per flow holding some | the screen says where the rest are | counting the open flow alone |
| [D7](#d7) | `0070·R13` per D5; `0070·R14`: the two tests stay apart, recorded below; `0074·R7`: the design spec's job strip reads "one dot, then one item per running job, each a label and its totals" | the cards' fixes; Q11 | folding the tests |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `ui:hub:a-cell-lists-its-images` | none | `tests/test_ui_library.py` |
| unit · vitest | `ui:renders:a-grid-keeps-its-focus`, `ui:review:the-rail-names-the-other-flows-waiting` | none | `ui/src/stores/batch.test.ts`, `ui/src/composables/useQueue.test.ts` |
| e2e | `ui:hub:the-source-cell-opens-its-photograph`, `ui:compare:side-by-side-sets-the-image-beside-its-photograph` | `test_a_rendered_cell_opens_its_newest_image` — the viewer, `↵` to the large view, `Esc` focused on the cell; `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from` — a second image, `Esc` focused on it | `tests/e2e/test_render.py` |

**End-to-end runs added:** two, on Chromium only (T4). The source cell's focus and the pair dialog are a browser's
(T1); each carries its own scenario, and a test binds one (T2). **`0070·R14`:** Review's *Side by side* test and the
Discard test stay apart — a test binds one scenario, and OpenSpec keeps every living scenario of a MODIFIED
requirement, so folding them would cost a re-titled requirement for one browser run.

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a remembered focus outlives its cell, as a source is added or a version rendered → restore falls back to
  the first spot.
- **[Trade-off]** a cell of many images grows tall → the strip wraps at the tile size, as Renders' rows do.

## Verdict

**Feasible.** Every piece exists; the change places them.
