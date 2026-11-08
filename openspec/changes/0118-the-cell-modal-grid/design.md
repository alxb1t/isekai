# Design — 0118 the cell modal as a grid

How the cell modal becomes one balanced grid, fitted to the window and moved in 2D, and how Renders is deleted with every
large view going back to the hub. Verdict: `feasible` — page and style edits, one view and one endpoint deleted.

## Context

See [proposal](proposal.md) for why. At `fc1c49df` (`v0.77.0`):

| where | today |
|---|---|
| `cellGrid(flow, images, at)` in `ui/src/cells.ts` | a row per version, `CellGrid.rows` each `{ version, tiles }`; `start` is `at`'s place |
| `ui/src/components/CellModal.vue` | a `.pick__row` per version labelled `vN` (`.pick__flow`); tiles `class="renders__image"`, caption `seed N` and `<span data-shared> ⇄</span>`; moves by `movePick` |
| `.pick--cell .renders__image` in `ui/src/app.css` | fixed at twice `--tile-width` by twice `--tile-height` |
| `ui/src/views/Renders.vue` | the Renders page, route `renders` at `/c/:collection/renders` in `ui/src/router.ts` |
| `ui/src/App.vue` | the Renders tab, lit on `renders` and `render`, and the everywhere key `renders` on `⇧I` |
| `ui/src/components/SessionDrawer.vue` | `renders()`, the overlay key `renders` on `⇧I`, and the *View in Renders* link `data-renders` |
| `ui/src/views/RenderLarge.vue` | `from` read from `history.state`, `'hub'` or else `'renders'`; `back` the hub cell or Renders; `step` writes `store.focus.renders` when from Renders; `compare` passes `state: { from }` |
| `ui/src/views/Compare.vue` | its `Esc` passes `state: { from }` back to the large view |
| `openLarge` in `ui/src/views/Hub.vue` | pushes route `render` with `state: { from: 'hub' }` |
| `ui/src/stores/collection.ts` | `renders`, `reloadRenders`, `focus: { hub, renders }`, a reload of `renders` when a job ends |
| `renders()` in `ui/src/api.ts`; `RendersInfo`, `RenderVersion` in `ui/src/types.ts` | Renders' read, and its types |
| `read_renders` in `isekai/interface/ui/app.py` | `GET /api/c/{collection}/renders`, reading `library.lacking` and `library.versions` through `_version_out` |
| `library.Version` in `isekai/interface/ui/library.py` | carries `at` and `rendered`, read by `_version_out` alone; `read_render` reads the rest |
| the `.renders__` rules in `app.css` | shared by the hub, the picks and the dialogs (`renders__image`, `--selected`, `--ready`, `renders__badge`, `renders__refusal`), the rest Renders' own |

`git grep -nw` at `fc1c49df` names each reader below; the tasks name each one.

```
Hub cell ──↵ or click──▶ the cell modal: one grid ──↵ or click──▶ large view ──h l──▶ the photograph's row
   ▲                          │ Esc                                    │ Esc · Back to Hub
   │                          ▼                                        ▼
   └── the Hub, focus kept ◀──┘          the Hub, on the cell of the image it closed
drawer ──⇧H or View in Hub──▶ the Hub of the focused image's collection
```

## Goals / Non-Goals

**Goals**

- A cell's renders read as one set, as large as the window lets them be, by keyboard alone.
- The hub is the one screen of images: nothing links to, reads for or styles a Renders page.

**Non-Goals**

- The routes' names: the large view and Compare keep `/c/:collection/renders/…` (brief Q7 of `0117`).
- The draft endpoint's list of images, and `DraftDialog.vue`'s several-image head: the endpoint stays as it is; only the
  page's selection goes (brief Q5 of `0117`).
- The server's order: `HubCell.images` and `newest` keep their write order.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **One balanced grid.** `cellGrid(flow, images, at)` keeps its signature; it takes `cellOrder(images)` as tiles carrying `flow`, and cuts them into rows of `columns` tiles, the last row the rest: rows = ⌈n/3⌉, columns = ⌈n/rows⌉, by an exported `gridColumns(count)` (0 for none). `CellGrid.rows` becomes `{ tiles: NonNullable<PickTile>[] }[]`; `shared` is unchanged; `start` is `at`'s place in the one order, `{ row: ⌊i/columns⌋, column: i mod columns }`, else `{ row: 0, column: 0 }` | brief Q1, Q2; one order, so a click on a thumbnail lands where the cell shows it | rows per version (the operator's complaint); a fixed three columns, which leaves 4 as 3+1 |
| <a id="d2"></a>**D2** | **2D moves.** `moveCell(grid, at, move)` in `cells.ts`: `column+` at a row's last tile goes to the next row's first, `column-` at a row's first to the previous row's last, when that row exists; every other move is `moved(last, at, move)`, which holds at the grid's ends and lands a row move on a shorter row's last tile. `CellModal.vue` walks by `moveCell`; `movePick` stays `ComparePick.vue`'s | brief Q4; `h` mirrors `l`, so a walk back retraces a walk on | `movePick` with no wrap, where `l` dead-ends mid-grid |
| <a id="d3"></a>**D3** | **The tile.** In `CellModal.vue` the grid is a `.pick__tiles` line per row, keyed by its index, with no `.pick__row` wrapper and no row label; a tile is keyed `` `${tile.version}/${tile.seed}` ``, as `Hub.vue`'s thumbnails are, since one row can hold one seed under two versions; each tile's button holds its image and `<span class="renders__badge mono" data-badge>v{{ tile.version }}</span>`, as `Hub.vue` draws its thumbnails, `data-badge` for the tests; the caption stays `seed N` and the `<span data-shared> ⇄</span>`. The button keeps `data-row`, `data-column`, `data-version`, `data-seed` | brief Q1, Q1a | a `vN` caption, which the operator turned down |
| <a id="d4"></a>**D4** | **Fit the window.** `CellModal.vue` sets `--rows` on `.pick--cell` to `Math.min(grid.rows.length, 3)`. In `app.css`, `.pick--cell .renders__image` takes `width: auto`, `aspect-ratio: 3 / 4` and `height: min(calc(var(--tile-height) * 2), calc((100vh - 96px) / var(--rows) - 44px))`: 96 px the dialog's chrome, as `.pick`'s `max-height` already leaves, 44 px a row's caption and gap. `.pick` already scrolls past `max-height` | brief Q3: three rows whole, then the fourth scrolls; the tile keeps the thumbnail's 3:4 | a measured layout in script; a fixed 2× that scrolls at two rows in a short window |
| <a id="d5"></a>**D5** | **Renders is deleted**: `ui/src/views/Renders.vue`; the `renders` route; `App.vue`'s tab and its `renders` key on `⇧I`; the store's `renders`, `reloadRenders` and `focus.renders`; `api.renders`; `RendersInfo` and `RenderVersion`; `read_renders`, `_version_out` and `library.lacking`; `Version.at` and `Version.rendered`, which only `_version_out` read, and `versions()`'s `suffix`, which only `rendered` read. The refusal of an address naming no version sends the operator to the collection's hub | brief Q6; nothing else reads them | keeping the list endpoint for a script: none calls it |
| <a id="d6"></a>**D6** | **Every large view goes back to the hub.** `RenderLarge.vue` drops `from`, the store, `back` and `step`'s focus write: `Esc` and the *Back to Hub* link push `hubCell`, the hub on the shown image's cell, as `deleted` does. Nothing passes `state.from`: `Hub.vue`'s `openLarge`, `RenderLarge.vue`'s `compare` and `step`, and `Compare.vue`'s `Esc` push without it | brief Q6: `0117`'s D4 kept `from` only while Renders stood; a pasted address has the hub as its one way back | keeping `from` with one value |
| <a id="d7"></a>**D7** | **The drawer's link is *View in Hub*.** `SessionDrawer.vue`'s `renders()` becomes `hub()`, pushing route `hub` for the focused grid's collection; its key is `{ id: 'view-hub', keys: [shifted('KeyH')], label: 'view in hub' }`, the link `data-view-hub` with `<KeyHint command="view-hub" />`, to the hub of `current?.collection ?? collections[0]`. The overlay's `⇧H` shadows the everywhere `hub` while the drawer is open | brief Q6; a distinct id keeps each hint its own declaration's | reusing id `hub`, whose hint two declarations would answer |
| <a id="d8"></a>**D8** | **The `.renders__` rules go.** The shared ones are renamed: `.renders__image` → `.tile` (and its `img`), `--selected` → `.tile--selected`, `--ready` → `.tile--ready`, `.renders__badge` → `.tile__badge`, `.renders__refusal` → `.large__refusal`. Renders' own go: `.renders`, `__grid`, `__source`, `__source--focused`, `__cell`, `__shared`, `__bar`, `__reason`, `__images`, `__image--focused`, `__image--damaged`. `.tile--ready` keeps the flex centring the damaged tile shared | brief Q6; the hub, the picks and the dialogs still draw the shared ones | keeping a `renders__` prefix no page is named for |
| <a id="d9"></a>**D9** | **The spec.** The Renders requirement is removed and added as *An image's large view shows its sheet and walks the photograph's row, and its thumbnail is made once*, its surviving scenarios keeping their `ui:renders:` keys, as the `/renders/…` addresses keep theirs; *a grid keeps its focus* moves to the hub as `ui:hub:the-hub-keeps-its-focus`, the one grid left that keeps one. The keys requirement is removed and added as *Each command has one key, declared once, and none fires while typing*, dropping *Renders moves by cell and by image*. The hub, Render, drawer and Draft requirements are modified | `openspec validate --strict` refuses a MODIFIED block that drops a scenario, as `0102`'s D7 and `0117`'s D8 found | stale scenario titles kept to satisfy the validator |
| <a id="d10"></a>**D10** | **The Hub tab is lit on the large view and Compare**: `screen` is `hub`, `render`, `compare` or `compare-photo` | they open from the hub now; the Renders tab lit `render` before | no tab lit there |

### D1 and D2 in shape

```
n:  1   2    3     4     5      6      7       8       9       10
    ▢   ▢▢   ▢▢▢   ▢▢    ▢▢▢    ▢▢▢    ▢▢▢     ▢▢▢     ▢▢▢     ▢▢▢
                   ▢▢    ▢▢     ▢▢▢    ▢▢▢     ▢▢▢     ▢▢▢     ▢▢▢
                                       ▢       ▢▢      ▢▢▢     ▢▢▢
                                                               ▢       ← past three rows, scrolls

5 tiles, v1 [9, 2] v2 [4, 6, 8]:   v1·2  v1·9  v2·4        l at v2·4 → v2·6     h at v2·6 → v2·4
                                   v2·6  v2·8              j at v2·4 → v2·8     l at v2·8 holds
```

### D4 in numbers

| window height | rows | tile height |
|---|---|---|
| 720 px | 1 | min(256, 720 − 96 − 44) = 256 px, 2× |
| 720 px | 3 | min(256, 624 / 3 − 44) = 164 px |
| 320 px | 1 | min(256, 224 − 44) = 180 px |

## Tests

New behaviour is pure functions in `cells.ts`, tested as units (`T1`): the shape, the start and the moves. A browser alone
shows the badge, the one row and the fit; the hub's e2e test `test_a_rendered_cell_opens_its_newest_image` already
opens the cell modal on `COMPARED` and takes the steps (`T2`), and takes over the sheet assertion of the deleted Renders
test. Every e2e test runs on Chromium alone (`T4`).

| layer | adds | changes |
|---|---|---|
| unit · vitest | in `ui/src/cells.test.ts`: `spec('ui:hub:the-cell-modal-balances-its-rows', …)` — `cellGrid` row lengths for 1 to 10 images, and `gridColumns(0)` is 0 | `ui:hub:the-cell-modal-moves-by-version-and-seed`: v1 [9, 2], v2 [4, 6, 8] → rows [v1·2, v1·9, v2·4], [v2·6, v2·8], `start` from v1·9 `{0, 1}`; `moveCell`: `l` at `{0, 2}` → `{1, 0}`, `h` back, `j` at `{0, 2}` → `{1, 1}`, `l` at `{1, 1}` and `h` at `{0, 0}` hold. `ui:hub:a-seed-under-two-versions-is-marked`: `start` `{0, 2}`. In `ui/src/stores/collection.test.ts`, `ui:renders:a-grid-keeps-its-focus` becomes `spec('ui:hub:the-hub-keeps-its-focus', …)` over `store.focus.hub`. In `ui/src/grid.test.ts`, `ui:keys:a-row-move-keeps-the-column` runs `moveCell` on a `cellGrid` of 3 and 2 tiles: `j` at `{0, 2}` → `{1, 1}`, `k` back to `{0, 1}`, its comment the cell modal's |
| unit · pytest | none | `test_a_damaged_approval_marks_its_own_version_and_the_rest_are_shown` in `tests/test_ui_api.py` becomes `test_a_damaged_approval_heads_its_large_view_damaged`, keeping its `ui:renders:a-damaged-approval-marks-its-version` marker: the v1 large view damaged, naming the file, `count` null; the v2 large view's `damaged` null |
| end-to-end | none | `test_a_rendered_cell_opens_its_newest_image` gains the `ui:renders:the-large-view-shows-its-sheet` marker and `hair_colour` on the sheet; on `COMPARED`, the two tiles share one top, each holds a `[data-badge]` reading its `vN`; at a 320 px window the tile is shorter than twice the thumbnail and `.pick--cell` does not scroll |

Deleted, each mapped:

| test | file | carried by, or retired by |
|---|---|---|
| `test_a_cells_approvals_are_listed_newest_first_with_their_images` | `tests/test_ui_api.py` | retired by [D5](#d5): the list endpoint goes; `ui:renders:versions-newest-first` with it |
| `test_a_cell_counts_the_images_its_newest_approval_lacks` | `tests/test_ui_api.py` | `test_a_cell_counts_what_its_newest_approval_lacks` in `tests/test_ui_library.py` (`ui:review:a-cell-counts-what-it-lacks`), the hub's count; `ui:renders:a-cell-counts-what-is-ready` goes |
| `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from` | `tests/e2e/test_render.py` | its sheet steps by `test_a_rendered_cell_opens_its_newest_image` (`ui:renders:the-large-view-shows-its-sheet`), its photograph steps by the same test's `ui:hub:the-source-cell-opens-its-photograph`; Renders' focus retired by [D6](#d6); `ui:renders:a-source-opens-in-the-viewer` goes |
| `test_a_damaged_versions_images_are_drawn_and_hold_the_focus` | `tests/e2e/test_render.py` | retired by [D5](#d5); its Render bar's refusal by `test_an_offer_whose_only_short_approval_is_damaged_carries_its_refusal` and `ui/src/bars.test.ts` (`ui:render:a-refused-count-is-shown`); `ui:renders:a-damaged-versions-images-are-drawn` goes |
| `spec('ui:keys:renders-moves-by-cell-and-by-image', …)` | `ui/src/grid.test.ts` | retired by [D5](#d5); `moved`'s holds at a row's ends by `ui:hub:the-cell-modal-moves-by-version-and-seed`, its row moves by `ui:keys:a-row-move-keeps-the-column` |

With its one test gone, the `DAMAGED` collection leaves `tests/e2e/conftest.py`, and the `json` and `approval_of` imports only it read.

Counted at `fc1c49df`, and as planned:

| count | command | at `fc1c49df` | planned |
|---|---|---|---|
| the suite | `uv run pytest --ignore=tests/e2e --collect-only -q \| tail -1` | 1521 | 1519 |
| `tests/test_ui_api.py` | `uv run pytest tests/test_ui_api.py --collect-only -q \| tail -1` | 97 | 95 |
| `tests/e2e` | `uv run pytest tests/e2e --collect-only -q \| tail -1` | 19 | 17 |
| `spec(` blocks in `ui/src/cells.test.ts` | `grep -c '^spec(' ui/src/cells.test.ts` | 9 | 10 |
| `spec(` blocks in `ui/src/grid.test.ts` | `grep -c '^spec(' ui/src/grid.test.ts` | 2 | 1 |

End-to-end runs added: none; two removed; the one extended test runs once, on Chromium.

## The words

Phase 3's prose edits, each before → after. ` / ` marks a line break in the file; a rewrapped paragraph keeps each
`after` phrase on one line. The S rows are `ui/design/spec.md`'s; a table row there is named by its first cells. Its §10, the versions each built, is history and stays as written.

| id | where | before | after |
|---|---|---|---|
| <a id="s1"></a>S1 | §3, the AppBar line | `Review 3 ⇧R  Renders ⇧I    flow` | `Review 3 ⇧R                flow` — twelve spaces for the twelve characters cut, so the box keeps its width |
| <a id="s2"></a>S2 | §4, the routes table | the row whose cells are `` `/c/<collection>/renders` ``, `Renders grid`, `*Draft from this*` | deleted |
| <a id="s3"></a>S3 | J2, **The cell modal** | its text after `naming the focused image.` | `One grid of every image of the cell, versions oldest first, seeds in numeric order, at most three to a row, rows balanced — 4 is 2 and 2, 5 is 3 and 2, 7 is 3, 3 and 1; each tile twice 96×128, scaled down so up to three rows show whole, a fourth scrolling, its vN badge on the image, seed N under it, then ⇄ where the seed was rendered under another version too. h j k l and ←↓↑→ move, a row move keeping the column, held at a shorter row's last tile, l at a row's end going on to the next row's first and h at a row's start back to the previous row's last; ↵ or a click opens the focused image's large view; Esc closes it, the hub's focus kept.` — `vN`, `seed N`, `⇄`, the keys, `↵` and `Esc` in backticks, as the bullet sets them now |
| <a id="s4"></a>S4 | J2, **A cell's images** | `` `ready · n images`, as on Renders; `` | `` `ready · n images`; `` |
| <a id="s5"></a>S5 | J2, **The RenderBar** | `takes the PrepareBar's place, on the hub and on Renders, once` | `takes the PrepareBar's place on the hub once` |
| <a id="s6"></a>S6 | J2, **The grid** | `it does on Renders, Review's rail and Home` | `it does on Review's rail and Home` |
| <a id="s7"></a>S7 | J4's table, the J4·4 row | `J4·4 Renders with the four new images`; `⇧I View in Renders`; `` `…/c/2026-10-19/renders` `` | `J4·4 the hub with the four new images`; `⇧H View in Hub`; `` `…/c/2026-10-19/hub` `` |
| <a id="s8"></a>S8 | J4, **The session** | `` `⇧I` opens the focused image's collection's Renders. `` | `` `⇧H` opens the focused image's collection's hub. `` |
| <a id="s9"></a>S9 | J5's table, the J5·1 row | `J5·1 Renders, before the revision`; `—`; `` `…/c/2026-09-17/renders` `` | `J5·1 the hub's cell modal, before the revision`; `↵ on the cell`; `` `…/c/2026-09-17/hub` — the modal has none `` |
| <a id="s10"></a>S10 | J5's table, the J5·7 row | `` J5·7 Renders: v2 after v1, both marked `⇄` ``; `⇧I View in Renders`; `` `…/c/2026-09-17/renders` `` | `` J5·7 the hub's cell modal: v2 after v1, both marked `⇄` ``; `⇧H View in Hub · ↵ on the cell`; `` `…/c/2026-09-17/hub` `` |
| <a id="s11"></a>S11 | J5, **Renders** | the bullet `- **Renders** is a grid of sources × flows, …`, to its last line `approval time, the Count and the seeds — is in the large view.` | deleted |
| <a id="s12"></a>S12 | J5, **↵ always opens the large view** | `back to where it was opened: the hub, on the cell of the image it closed, or else Renders, on that image.` | `back to the hub, on the cell of the image it closed, whatever opened it.` |
| <a id="s13"></a>S13 | J5, the same bullet | `tiles at Renders' size oldest first` | `tiles at a thumbnail's size oldest first` |
| <a id="s14"></a>S14 | J5, **Draft from this** | `on the large view and over a Renders selection: a dialog`; ``, or `· 3 images` over a selection, with a row`` | `on the large view: a dialog`; `, with a row` |
| <a id="s15"></a>S15 | J6's table, the J6·2 row | `J6·2 Renders: three new images after v1, no pair`; `⇧I`; `` `…/c/2026-09-17/renders` `` | `J6·2 the hub's cell modal: three new images after v1, no pair`; `⇧H View in Hub · ↵ on the cell`; `` `…/c/2026-09-17/hub` `` |
| <a id="s16"></a>S16 | the states table | the rows `Renders` · `empty` and `Renders` · `*Draft from this* disabled`; the first cell `Renders` of the rows `a missing image, its record kept` and `a deleted render` | the first two deleted; the other two's first cell `large view` |
| <a id="s17"></a>S17 | §7, the everywhere row | ` · ⇧I Renders` | nothing |
| <a id="s18"></a>S18 | §7, the Renders row | first cell `Renders`; its keys | first cell `Large view`; `h l or ←→ the photograph's row · ⇧D Draft from this · ⇧C Compare with… · esc back to the hub · in its pick, h j k l or the arrows, ↵ compare, esc close · in compare, \ swap, esc back`, the `\` in backticks as now |
| <a id="s19"></a>S19 | §7, the Drawer row | `⇧I its collection's Renders` | `⇧H its collection's hub` |
| <a id="s20"></a>S20 | §7, the Hub row | `in the cell modal, h j k l or ←↓↑→ move, ↵ the large view` | `in the cell modal, h j k l or ←↓↑→ move, l and h going on across rows, ↵ the large view` |
| <a id="w1"></a>W1 | `README.md` | `Renders shows` / `each source's images by flow, versions oldest to newest, each marked with its version, and an image's large view` | `The hub's` / `cell modal sets a cell's images side by side, each marked with its version, and an image's large view` |
| <a id="w2"></a>W2 | `README.md` | `from the large view or over a selection, lists every flow` | `from the large view, lists every flow` |
| <a id="w3"></a>W3 | `isekai/interface/ui/README.md` | `- **Renders** reads each cell's images, versions oldest to newest, with how many its newest approval still lacks,` / `the render stage's own count; Render comes from its bar, as on the hub. The large view shows an image` | `- **The large view** shows an image, headed by its version, and walks the photograph's row; the hub's cells` / `carry each image and what each newest approval lacks. The large view sets an image` |
| <a id="w4"></a>W4 | `docs/data-flow.md` | `─▶ the render drawer ─▶ Renders` | `─▶ the render drawer ─▶ the hub` |
| <a id="w5"></a>W5 | `isekai/interface/ui/app.py` | `# version first, then by seed: Renders and the pick.` | `# version first, then by seed: the large view's walk and the pick.` |
| <a id="w6"></a>W6 | `isekai/interface/ui/app.py` | `"""Describe rendered images by version and decimal seed, as Renders names them.` | `"""Describe rendered images by version and decimal seed, as the page names them.` |
| <a id="w7"></a>W7 | `ui/src/bars.ts` | `Which bar a hub or Renders shows` | `Which bar the hub shows` |
| <a id="w8"></a>W8 | `ui/src/app.css` | `One image's tile on the hub and on Renders:` | `One image's tile on the hub:` |
| <a id="w9"></a>W9 | `ui/src/app.css` | `/* — Renders and the large view (J5·1, J5·2) — */` | `/* — the tile and the large view (J5·2) — */` |
| <a id="w10"></a>W10 | `ui/src/app.css` | `Compare with…'s tiles, at a Renders tile's size` and `A cell's images at its foot, at a Renders tile's size` | `Compare with…'s tiles, at a thumbnail's size` and `A cell's images at its foot, at a thumbnail's size` |
| <a id="w11"></a>W11 | `ui/src/grid.ts` | `On Renders a row is a source, and a focus column counts its source, column 0,` / `then its images across its cells; the render drawer's grid is rectangular.` | `On the hub a row is a source, its source cell column 0; the cell modal's last` / `row may end short; the render drawer's grid is rectangular.` |
| <a id="w12"></a>W12 | `tests/test_ui_api.py` | `# --- Renders ---…`, `# The hub follows write time within an approval, Renders seed order.`, `# Renders and Compare retain seed order.` | `# --- The large view ---…` (dashes to the same width), `# The hub follows write time within an approval, the large view seed order.`, `# The large view and Compare retain seed order.` |
| <a id="w13"></a>W13 | `tests/e2e/conftest.py` | `# The collection the Renders view is read from: one source already rendered once;` | `# The collection the hub's cell modal is read from: one source already rendered once;` |
| <a id="w14"></a>W14 | `isekai/interface/README.md`, the `ui/app.py` row | `` `GET /api/c/{collection}/renders` with `…/renders/{digest}/{flow}/{version}/{seed}`, its `DELETE`, `` | `` `GET /api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}`, its `DELETE`, `` |
| <a id="w15"></a>W15 | `docs/principles.md` | ``interface/ui/library.py`'s `lacking` and `stage` decide that an unapproved or damaged flow lacks no image, and`` | ``interface/ui/library.py`'s `stage` decides that an unapproved or damaged flow lacks no image, and`` |

## Dependencies

None.

## Risks / Trade-offs

- **The fit is a formula, not a measure.** `44px` a row's caption and gap and `96px` the dialog's chrome are set by
  today's styles; a larger caption font would clip the third row's caption. The e2e step at 320 px catches a scroll.
- **`⇧H` means two things.** Everywhere it opens the open collection's hub; in the drawer, the focused image's
  collection's. The drawer is the one place a key names another collection.
- **A pasted `/c/<collection>/renders` address** now falls to the router's catch-all, the library.
- **`library.versions` stays newest first** for `read_render` alone; ordering no longer matters to any reader, and it
  is left as it reads.

## Verdict

`feasible`. `cellGrid`, `gridColumns` and `moveCell` in `cells.ts` with their unit tests; `CellModal.vue` restyled and
fitted; Renders' page, route, tab, key, store slice, types, endpoint and CSS deleted; the way back made the hub's; the
tests and the prose moved to the hub.
