# Design — 0117 the Hub cell modal

How the Hub shows a cell's renders in a modal grid, one order serves the Hub and the render page, and `Esc` lands on
the Hub cell. Verdict: `feasible` — page edits, one new component, and one field dropped from a payload.

## Context

See [proposal](proposal.md) for why. At `c13a1bc5`:

| where | today |
|---|---|
| `action` in `ui/src/cells.ts` | a cell holding images returns `view`, hint `↵ view` |
| `view` in `ui/src/views/Hub.vue` | opens `ImageViewer` over the cell's images, `⇧↵` there pushing route `render` with `state: { from: 'hub' }`; a thumbnail's click opens it at that index |
| the cell's thumbnails in `Hub.vue` | `cell.images` as the server sends them: oldest version first, each version's seeds by write time |
| `ui/src/components/ComparePick.vue` | a modal grid, a row per flow, `h j k l` by `movePick`, `↵` picks, `Esc` closes |
| `screenOrder(detail, from)` in `cells.ts` | from the Hub `detail.cell`, one flow by write time; else `detail.source`, the row across flows, seeds numeric |
| `back` in `ui/src/views/RenderLarge.vue` | the Hub with no state, so the Hub restores `store.focus.hub`, the cell it opened from |
| `deleted` in `RenderLarge.vue` | the Hub with `state: { cell: { digest, flow } }`, which `Hub.vue`'s `onMounted` reads once |
| `HubCell.short` in `ui/src/types.ts` | what the newest approval lacks, the render stage's count; nothing on the Hub draws it |
| Renders' pending tile, `Renders.vue:326-331` | `<span class="renders__image renders__image--ready mono" data-ready>ready · n images</span>`, last in the row |

`detail.source` and the Hub's columns follow `config/ui.json`'s order: `app.py` builds `source` over the offered
flows, and `library.hub` reads the same list. So "flows as the Hub's columns" is `detail.source`'s order already.

```
Hub cell ──↵ or click──▶ the cell modal ──↵ or click──▶ render page ──h l──▶ the photograph's row
   ▲                          │ Esc                          │
   │                          ▼                              │ Esc · Back to Hub
   └──────── the Hub, focus kept ◀──── the Hub, focused on the image's cell
```

## Goals / Non-Goals

**Goals**

- A rendered Hub cell opens its renders together, at a size to compare them, by keyboard alone.
- One order, held by one pure function each in `cells.ts`, for the Hub cell, the modal and the render page.

**Non-Goals**

- Deleting Renders, freeing `⇧I` or *View in Hub* (brief Q6, Q8 part B).
- A render page opened from Renders, or from a pasted address: its `Esc` still goes to Renders.
- The server's `HubCell.images` and `newest`: the page sorts; `newest` stays the last-written image.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **The cell modal** is `ui/src/components/CellModal.vue`, built from `ComparePick.vue`: a `dialog.viewer` with `data-cell-modal`, held by `useHeldFocus`, keys in the `overlay` scope. Its grid is `cellGrid(flow, images, at)` in `cells.ts`: a row per version holding images, oldest first, labelled `vN`; each row's tiles its images in numeric seed order, each a `PickTile` carrying `flow`, captioned `seed N`, then ` ⇄` when `grid.shared` holds the seed; `start` is `at`'s place. A tile's button carries `data-row`, `data-column`, `data-version` and `data-seed`; the `⇄` in its caption is a `<span data-shared>`. The Hub takes the grid once at opening, so a render landing meanwhile moves nothing under the focus, and `src` is `thumbAt`, the thumbnail being 512 px on its long side. `h j k l` and the arrows move by `movePick`; `↵` or a click emits `open` with the focused tile; `Esc` closes. The head is one line, `` `${title} · ${imageName(tile)}` ``, `title` the source's name. Tiles are twice `--tile-width` by twice `--tile-height`, `.pick--cell .renders__image` in `ui/src/app.css` | ComparePick already holds the dialog, focus and moves; a row per version gives `j k` a meaning; `⇄` is the seeds seen under more than one version of the cell, computed in the browser (brief Q4) | one wrapped row of every image, where `j k` mean nothing; a server field for `⇄` (brief Q4) |
| <a id="d2"></a>**D2** | **One order.** `cellOrder(images)` in `cells.ts` returns a cell's images by version, then by seed as a number: a shorter decimal string first, then by text. `cellGrid` and the Hub cell's thumbnails read it. `rowOrder(detail)` replaces `screenOrder(detail, from)`: `detail.source` flattened, a tile per image with its flow. `RenderLarge.vue`'s `h` `l` always read `rowOrder` | brief Q2; the server already sends `source` in that order, and seeds are decimal strings past `Number`'s safe range, so length first compares them as numbers | sorting `HubCell.images` on the server, which `newest` reads by write time |
| <a id="d3"></a>**D3** | **The render detail drops `cell`.** `read_render` in `isekai/interface/ui/app.py` stops sending it, and `RenderDetail.cell` leaves `ui/src/types.ts`. `tests/test_ui_api.py` asserts `"cell" not in view` | its one reader, `screenOrder`'s Hub branch, is gone with D2 | keeping a write-order copy nothing reads |
| <a id="d4"></a>**D4** | **`Esc` and *Back to Hub* land on the image's cell.** `RenderLarge.vue`'s `back`, when `from === 'hub'`, is `{ name: 'hub', params: { collection }, state: { cell: { digest, flow } } }`, `flow` the shown image's, which `deleted` pushes too. `Hub.vue`'s `onMounted` already focuses that cell, scrolled to the centre. The modal is not reopened. `from` stays: a render page opened from Renders, or pasted, still goes back to Renders | brief Q3; `h` `l` cross flows, so the cell opened from may not be the image's; the `cell` state is the Delete's mechanism already | reopening the modal; sending every opener to the Hub while Renders still stands |
| <a id="d5"></a>**D5** | **The pending tile.** `ready(cell)` in `cells.ts` returns `ready · n images`, `noun`'s plural, when `cell.short` is above 0, else `null`. `Hub.vue` draws `.hub__images` when the cell holds images or `ready(cell)` is not `null`, and last in it `<span class="renders__image renders__image--ready mono" data-ready>`, inert, as Renders draws it | brief wish 3; `HubCell.short` is the render stage's count, the one Renders shows; no server change | a second count on the server |
| <a id="d6"></a>**D6** | **The viewer loses `⇧↵`.** `ImageViewer.vue`'s `open` prop and `viewerKeys`' `open` option and command go; the Hub's `viewing` is for photographs alone. `ImageViewer` stays for the source column, Renders, Review, the import sheet and the drawer | brief Q1; the Hub's cells were the one caller passing `open` | keeping a hook no caller passes |
| <a id="d7"></a>**D7** | **`movePick` takes any grid of rows of tiles**: its parameter becomes `{ rows: { tiles: readonly unknown[] }[] }`, so `CellModal.vue` and `ComparePick.vue` share it | one move rule for both picks, already held by `ui:compare:the-pick-moves-by-row-and-column` | a second move function |
| <a id="d8"></a>**D8** | **The Renders requirement is removed and added** under *The Renders view shows each source's images by flow, and a large view walks the photograph's row*, its scenarios carried, `ui:renders:the-large-view-steps-its-screens-order` becoming `ui:renders:the-large-view-walks-the-photographs-row` | `openspec validate --strict` refuses a MODIFIED block that drops a scenario title, as `0102`'s D7 found | a stale scenario title kept to satisfy the validator |

### D1 in shape

```
hal.jpg · summon-anime-wai · v2 · seed 7                     ← the focused tile
v1   [ 192×256 ]  [ 192×256 ]
     seed 2       seed 7 ⇄
v2   [ 192×256 ]
     seed 7 ⇄
```

`cellGrid(flow, images, at)` from a click on the v1 seed 7 thumbnail → `start {row 0, column 1}`; from `↵` on the cell, `at` is
`cell.newest` → `{row 1, column 0}`.

### D4 in code

```
step(±1)   router.replace render, state { from }               (unchanged)
Esc        from === 'hub' ? push hub, state { cell: { digest, flow: props.flow } } : push renders
deleted()  push hub, state { cell: { digest, flow: props.flow } }  (unchanged)
```

## Tests

Every new case is a unit test of a pure function in `cells.ts` (`T1`): the modal's grid, its marks, the order and the
ready tile. A browser alone shows the modal opening on a click, its tile size, and `Esc` landing on the cell; the
existing Hub test, `test_a_rendered_cell_opens_its_newest_image` in `tests/e2e/test_render.py`, reaches that state and
is rewritten for the modal (`T2`). No test is deleted or merged.

| layer | adds | changes |
|---|---|---|
| unit · vitest | in `ui/src/cells.test.ts`: `spec('ui:hub:the-cell-modal-moves-by-version-and-seed', …)` — `cellOrder` and `cellGrid` over seeds 9 then 2 under v1 and 4 under v2, `start` from v1 seed 9, `movePick` holding a row move at the shorter row's end; `spec('ui:hub:a-seed-under-two-versions-is-marked', …)` — `cellGrid(...).shared` holds 7, not 5; `spec('ui:hub:a-cell-shows-what-is-ready', …)` — `ready` for `short` 2, 1, 0 and `null` | `ui:renders:the-large-view-steps-its-screens-order` becomes `ui:renders:the-large-view-walks-the-photographs-row`, over `rowOrder`: the row's next image, then the next flow's first, `l` held at the last; the old `detail.cell` steps go |
| unit · vitest | none | `ui:viewer:enter-toggles-full-size` in `ui/src/components/ImageViewer.test.ts`: `opened` takes no `open`; its step "the opener's large view is ⇧↵" becomes `⇧↵` matching no command |
| unit · pytest | none | `test_compare_takes_any_two_images_of_a_source` in `tests/test_ui_api.py`: the `view["cell"]` assertion becomes `assert "cell" not in view` |
| end-to-end | none | `test_a_rendered_cell_opens_its_newest_image`: every modal selector scoped to `[data-cell-modal]`: a click opens it focused on v1 seed 7, `↵` the large view, `Esc` the Hub on that cell; then on `COMPARED`'s hub a click on the v1 thumbnail opens the modal focused on v1 seed 7, the tile twice the thumbnail's width, `[data-shared]` on both tiles. It carries `ui:hub:a-thumbnail-opens-the-cell-modal-on-it` beside its two keys |

The `COMPARED` step stands on its own fixture's v1 and v2, not on the first step's state (`T3`). The e2e test runs on
Chromium alone, as every test under `tests/e2e/` does (`T4`).

Counted at `c13a1bc5`, and as planned:

| count | command | at `c13a1bc5` | planned |
|---|---|---|---|
| the suite | `uv run pytest --ignore=tests/e2e --collect-only -q \| tail -1` | 1521 | 1521 |
| `tests/e2e` | `uv run pytest tests/e2e --collect-only -q \| tail -1` | 19 | 19 |
| `spec(` blocks in `ui/src/cells.test.ts` | `grep -c '^spec(' ui/src/cells.test.ts` | 6 | 9 |
| `spec(` blocks in `ui/src/components/ImageViewer.test.ts` | `grep -c '^spec(' ui/src/components/ImageViewer.test.ts` | 3 | 3 |

End-to-end runs added: none; the one rewritten test runs once, on Chromium.

## Dependencies

None.

## Risks / Trade-offs

- **The Hub and Renders as ways back while Renders stands.** Opened from the Hub, `Esc` lands on the Hub cell; from
  Renders, on Renders. Part B removes the second.
- **The browser's Back differs from `Esc`.** It returns to the Hub entry the modal opened from, focused on the cell left
  (`store.focus.hub`), not on the cell `h` `l` walked to.
- **A long seed widens a tile's caption.** At twice the tile's width a ten-digit seed in mono 11 fits; a longer one is
  cut by the caption's ellipsis.
- **The Hub's thumbnails change order** within a version: numeric, no longer by write time. `newest`, what `↵` opens
  on, is still the last-written image.

## Verdict

`feasible`. `CellModal.vue` built from ComparePick; `cellOrder`, `cellGrid`, `ready` and `rowOrder` in `cells.ts` with
their unit tests; the render page's way back; the detail's `cell` dropped; and the Hub's e2e test rewritten.
