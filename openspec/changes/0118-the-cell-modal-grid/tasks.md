# Tasks — 0118 the cell modal as a grid

The grid first, then Renders deleted, then the prose, per [design](design.md). Paths are from the repository root.

## Progress

- [ ] 1 — The grid
- [ ] 2 — Renders deleted
- [ ] 3 — The prose

## 1 — The grid

- [ ] 1.1 **HALT CHECK** — `cellGrid` still takes `(flow, images, at)`, as [D1](design.md#d1) keeps it.
  Verify: `grep -n -F 'export function cellGrid(' ui/src/cells.ts` prints one line.
- [ ] 1.2 In `ui/src/cells.ts`, add `gridColumns(count)` and make `CellGrid` and `cellGrid` one balanced grid, their doc
  comments and examples with them, per [D1](design.md#d1).
  Verify: `grep -n -E 'export (const|function) gridColumns' ui/src/cells.ts` prints one line.
- [ ] 1.3 In `ui/src/cells.ts`, add `moveCell(grid, at, move)` with its doc comment and example, per [D2](design.md#d2).
  Verify: `grep -n -F 'export function moveCell(' ui/src/cells.ts` prints one line.
- [ ] 1.4 In `ui/src/cells.test.ts`, rewrite `ui:hub:the-cell-modal-moves-by-version-and-seed` over `cellGrid` and
  `moveCell`, set `ui:hub:a-seed-under-two-versions-is-marked`'s `start` to `{ row: 0, column: 2 }`, and add
  `spec('ui:hub:the-cell-modal-balances-its-rows', …)`, per [Tests](design.md#tests).
  Verify: `grep -c '^spec(' ui/src/cells.test.ts` prints `10`.
- [ ] 1.5 In `ui/src/components/CellModal.vue`, draw the rows, tiles and badge as [D3](design.md#d3) says and set
  `--rows` on `.pick--cell` per [D4](design.md#d4); walk by `moveCell`; the head comment says one balanced grid, badged. Verify: `grep -n -F 'moveCell(props.grid' ui/src/components/CellModal.vue` prints one line.
- [ ] 1.6 In `ui/src/app.css`, give `.pick--cell .renders__image` `width: auto`, `aspect-ratio: 3 / 4` and D4's
  `height`, its comment saying the tiles fit the window, per [D4](design.md#d4).
  Verify: `grep -n -F 'calc((100vh - 96px) / var(--rows) - 44px)' ui/src/app.css` prints one line.
- [ ] 1.7 In `tests/e2e/test_render.py`'s `test_a_rendered_cell_opens_its_newest_image`, add the
  `ui:renders:the-large-view-shows-its-sheet` marker, `hair_colour` on the sheet, and the `COMPARED` steps
  [Tests](design.md#tests) names, the short window at 1280 × 320. Verify: `grep -n -F '"height": 320' tests/e2e/test_render.py` prints one line.
- [ ] 1.8 In `openspec/changes/0118-the-cell-modal-grid/specs/ui/spec.md`, rewrap the paragraphs holding *A cell
  holding images SHALL show every one of them* and *`⇧H` SHALL close the drawer* to 120 characters, whitespace
  only, every word, code span and emphasis kept: the gate reads the effective spec, which reads this delta.
  Verify: `uv run pytest tests/test_spec_prose.py -k test_no_spec_line_passes_120_characters` exits 0.

## 2 — Renders deleted

- [ ] 2.1 **HALT CHECK** — the Renders route stands, as [D5](design.md#d5) finds it.
  Verify: `grep -n -F "name: 'renders'" ui/src/router.ts` prints one line.
- [ ] 2.2 `git rm ui/src/views/Renders.vue`; in `ui/src/router.ts`, remove its import and the `renders` route, per
  [D5](design.md#d5). Verify: `git grep -n -F 'Renders.vue' -- ui/src` prints nothing.
- [ ] 2.3 In `ui/src/App.vue`, remove the everywhere key `renders` and the Renders tab, and light the Hub tab per
  [D10](design.md#d10). Verify: `grep -n -F "'renders'" ui/src/App.vue` prints nothing.
- [ ] 2.4 In `ui/src/components/SessionDrawer.vue`, make `renders()` `hub()`, its key `view-hub` on `⇧H` and the link
  *View in Hub*, per [D7](design.md#d7). Verify: `grep -n -F 'data-view-hub' ui/src/components/SessionDrawer.vue` prints one line.
- [ ] 2.5 In `ui/src/views/RenderLarge.vue`, drop `from`, `store`, `back`, `step`'s focus write and the `state` that
  `compare` and `step` pass; `Esc` and the *Back to Hub* link push `hubCell`; the unread imports and the comments naming
  Renders go, per [D6](design.md#d6). Verify: `grep -n -F 'history.state' ui/src/views/RenderLarge.vue` prints nothing.
- [ ] 2.6 In `ui/src/views/Compare.vue`, the `back` key pushes the large view with no `state`, its comment "Back to the
  large view."; in `ui/src/views/Hub.vue`, `openLarge` pushes with no `state`, per [D6](design.md#d6).
  Verify: `git grep -n -F 'state: {' -- ui/src/views/Compare.vue ui/src/views/Hub.vue` prints nothing.
- [ ] 2.7 In `ui/src/stores/collection.ts`, remove `renders`, `reloadRenders`, their imports, their lines in `open`,
  `ended` and the return, and `focus.renders`, with the comment words naming them, per [D5](design.md#d5).
  Verify: `grep -n -F 'reloadRenders' ui/src/stores/collection.ts` prints nothing.
- [ ] 2.8 In `ui/src/stores/collection.test.ts`, turn `spec('ui:renders:a-grid-keeps-its-focus', …)` into
  `spec('ui:hub:the-hub-keeps-its-focus', …)` over `store.focus.hub`, its last expectation `{ hub: null }`, per
  [Tests](design.md#tests). Verify: `grep -n -F "spec('ui:hub:the-hub-keeps-its-focus'" ui/src/stores/collection.test.ts` prints one line.
- [ ] 2.9 Remove `renders()` and its `RendersInfo` import from `ui/src/api.ts`, and `RendersInfo` and `RenderVersion`
  from `ui/src/types.ts`; `RenderDetail`'s comments on `came_from` and `source` stop naming them and Renders.
  Verify: `git grep -n -w -e RendersInfo -e RenderVersion -- ui/src` prints nothing.
- [ ] 2.10 In `ui/src/grid.test.ts`, delete `spec('ui:keys:renders-moves-by-cell-and-by-image', …)`, and rewrite
  `ui:keys:a-row-move-keeps-the-column` over `moveCell` on a cell modal, per [Tests](design.md#tests). Verify: `grep -n -F 'renders-moves-by-cell-and-by-image' ui/src/grid.test.ts` prints nothing.
- [ ] 2.11 In `isekai/interface/ui/app.py`, delete `read_renders` and `_version_out`; the module docstring's line
  for `GET  /api/c/{collection}/renders` names the large view's address alone; `_version`'s refusal
  says "go back to the collection's hub to choose one", per [D5](design.md#d5). Verify: `grep -n -F 'def read_renders' isekai/interface/ui/app.py` prints nothing.
- [ ] 2.12 In `isekai/interface/ui/library.py`, delete `lacking` and the `shortfall` import, and drop `Version.at` and
  `Version.rendered` with their docstring words, `versions()`'s reads of them, its `suffix` parameter and the locals left unread, and
  `read_render`'s `suffix` argument to it, per [D5](design.md#d5).
  Verify: `grep -n -F 'def lacking' isekai/interface/ui/library.py` prints nothing.
- [ ] 2.13 In `tests/test_ui_api.py`, delete `test_a_cells_approvals_are_listed_newest_first_with_their_images` and
  `test_a_cell_counts_the_images_its_newest_approval_lacks`, and rewrite the damaged approval's test as
  [Tests](design.md#tests) says, keeping its marker. Verify: `uv run pytest tests/test_ui_api.py -k damaged_approval_heads_its_large_view` exits 0.
- [ ] 2.14 In `tests/e2e/test_render.py`, delete `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from`
  and `test_a_damaged_versions_images_are_drawn_and_hold_the_focus`, and the `DAMAGED` import, per
  [Tests](design.md#tests). Verify: `grep -n -F 'def test_a_damaged_versions_images' tests/e2e/test_render.py` prints nothing.
- [ ] 2.15 In `tests/e2e/test_render.py`'s `test_the_drawer_holds_the_render`, the link in view on the last row is
  `[data-view-hub]`, per [D7](design.md#d7). Verify: `grep -n -F '[data-view-hub]' tests/e2e/test_render.py` prints one line.
- [ ] 2.16 In `tests/e2e/conftest.py`, remove `DAMAGED`, its comment, its block in the fixture and the `json` and
  `approval_of` imports it leaves unread, per [Tests](design.md#tests). Verify: `grep -n -w DAMAGED tests/e2e/conftest.py` prints nothing.
- [ ] 2.17 In `ui/src/app.css`, rename the shared `.renders__` rules and delete Renders' own, per [D8](design.md#d8);
  `.hub__cell--focused` keeps its rule alone. Verify: `grep -n -E '\.renders(__| \{)' ui/src/app.css` prints nothing.
- [ ] 2.18 Rename the classes per [D8](design.md#d8) in `ui/src/views/Hub.vue`, `ui/src/components/CellModal.vue`,
  `ui/src/components/ComparePick.vue`, `ui/src/components/DeleteDialog.vue` and `ui/src/views/RenderLarge.vue`.
  Verify: `git grep -n -F 'renders__' -- ui/src tests` prints nothing.

## 3 — The prose

Each edit keeps its `after` phrase on one line, rewrapping around it, per [the words](design.md#the-words).

- [ ] 3.1 In `ui/design/spec.md`, apply [S1](design.md#s1) to [S6](design.md#s6): the AppBar line, the routes table
  and J2. Verify: `grep -n -F 'One grid of every image of the cell' ui/design/spec.md` prints one line.
- [ ] 3.2 In `ui/design/spec.md`, apply [S7](design.md#s7) to [S14](design.md#s14): J4 and J5.
  Verify: `grep -n -F 'whatever opened it.' ui/design/spec.md` prints one line.
- [ ] 3.3 In `ui/design/spec.md`, apply [S15](design.md#s15) to [S20](design.md#s20): J6, the states table and §7.
  Verify: `grep -n -E '⇧I|^\| Renders \|' ui/design/spec.md` prints nothing.
- [ ] 3.4 Apply [W1](design.md#w1) to [W4](design.md#w4), [W14](design.md#w14) and [W15](design.md#w15) in `README.md`,
  `isekai/interface/ui/README.md`, `docs/data-flow.md`, `isekai/interface/README.md` and `docs/principles.md`. Verify: `grep -n -F 'cell modal sets a cell' README.md` prints one line.
- [ ] 3.5 Apply [W5](design.md#w5) to [W13](design.md#w13) in `isekai/interface/ui/app.py`, `ui/src/bars.ts`,
  `ui/src/app.css`, `ui/src/grid.ts`, `tests/test_ui_api.py` and `tests/e2e/conftest.py`.
  Verify: `git grep -n -E 'Renders (shows|and|names|seed|tile|view|draws|a row|---)|[Oo]n Renders|\*\*Renders\*\*|─▶ Renders|or Renders' -- ui/src isekai tests README.md docs` prints nothing.
