# Tasks — 0117 the Hub cell modal

The cell modal on the Hub, then the render page's walk and way back, then the design spec, per [design](design.md).
Paths are from the repository root.

## Progress

- [x] 1 — The cell modal
- [x] 2 — The walk
- [x] 3 — The prose

## 1 — The cell modal

- [x] 1.1 **HALT CHECK** — the Hub payload carries the pending count `HubCell.short`, as [D5](design.md#d5) says.
  Verify: `grep -n -F 'short: number | null' ui/src/types.ts` prints one line.
- [x] 1.2 In `ui/src/cells.ts`, add `cellOrder(images)` per [D2](design.md#d2), the `CellGrid` interface and
  `cellGrid(flow, images, at)` per [D1](design.md#d1), and `ready(cell)` per [D5](design.md#d5); widen `movePick`'s
  parameter per [D7](design.md#d7). Verify: `grep -n -F 'export function cellGrid(' ui/src/cells.ts` prints one line.
- [x] 1.3 In `ui/src/cells.test.ts`, add `spec('ui:hub:the-cell-modal-moves-by-version-and-seed', …)`,
  `spec('ui:hub:a-seed-under-two-versions-is-marked', …)` and `spec('ui:hub:a-cell-shows-what-is-ready', …)`, per
  [Tests](design.md#tests). Verify: `grep -c -F "spec('ui:hub:" ui/src/cells.test.ts` prints `5`.
- [x] 1.4 Create `ui/src/components/CellModal.vue` from `ComparePick.vue`, per [D1](design.md#d1): props `title`,
  `grid: CellGrid` and `src`, emits `open` with a `PickTile` and `close`, the dialog `data-cell-modal`, grid classes
  `pick pick--cell`, the data attributes where D1 puts them. Verify: `grep -n -F 'data-cell-modal' ui/src/components/CellModal.vue` prints one line.
- [x] 1.5 In `ui/src/app.css`, after the `.pick__tile` rules, size `.pick--cell .renders__image` at
  `calc(var(--tile-width) * 2)` by `calc(var(--tile-height) * 2)`, and cut its caption by an ellipsis, per
  [D1](design.md#d1). Verify: `grep -n -F 'calc(var(--tile-width) * 2)' ui/src/app.css` prints one line.
- [x] 1.6 In `ui/src/views/Hub.vue`, make `view(source, flow, at?)` open `<CellModal>` on `at`, else `cell.newest`,
  its grid taken once at opening, `src` from `thumbAt`, `open` pushing route `render` with `state: { from: 'hub' }`;
  `viewing`, its comment and `<ImageViewer>` drop `open`, and the unread `imageAt` import goes, per [D1](design.md#d1). Verify: `grep -n -F '<CellModal' ui/src/views/Hub.vue` prints one line.
- [x] 1.7 In `ui/src/views/Hub.vue`, draw a cell's thumbnails by `cellOrder`, a click opening the modal on that image,
  and the pending tile last, `.hub__images` shown for either, per [D5](design.md#d5).
  Verify: `grep -n -F 'data-ready' ui/src/views/Hub.vue` prints one line.
- [x] 1.8 In `ui/src/composables/useViewer.ts`, remove `viewerKeys`' `open` option, its `open` command, their doc
  words and the `shifted` import it leaves unused, per [D6](design.md#d6). Verify: `grep -n -F 'dialog.open' ui/src/composables/useViewer.ts` prints nothing.
- [x] 1.9 In `ui/src/components/ImageViewer.vue`, remove the `open` prop, its line in the `viewerKeys` call and its
  words in the head comment, per [D6](design.md#d6). Verify: `grep -n -F 'props.open' ui/src/components/ImageViewer.vue` prints nothing.
- [x] 1.10 In `ui/src/components/ImageViewer.test.ts`, drop `opened`'s `open` parameter, and turn
  `ui:viewer:enter-toggles-full-size`'s `⇧↵` step into `⇧↵` matching no command, per [Tests](design.md#tests).
  Verify: `grep -n -w open ui/src/components/ImageViewer.test.ts` prints nothing.
- [x] 1.11 In `tests/e2e/test_render.py`, rewrite `test_a_rendered_cell_opens_its_newest_image` for the cell modal and
  add its `COMPARED` step and marker, per [Tests](design.md#tests).
  Verify: `grep -n -F 'ui:hub:a-thumbnail-opens-the-cell-modal-on-it' tests/e2e/test_render.py` prints one line.

## 2 — The walk

- [x] 2.1 In `ui/src/cells.ts`, replace `screenOrder(detail, from)` with `rowOrder(detail)` and its doc, per
  [D2](design.md#d2). Verify: `grep -n -F 'export function rowOrder(detail: RenderDetail)' ui/src/cells.ts` prints one line.
- [x] 2.2 In `ui/src/views/RenderLarge.vue`, read `order` from `rowOrder(detail.value)`, per [D2](design.md#d2).
  Verify: `grep -n -F 'rowOrder(detail.value)' ui/src/views/RenderLarge.vue` prints one line.
- [x] 2.3 In `ui/src/views/RenderLarge.vue`, add `const hubCell`, the Hub on the shown image's cell, and make `back`'s
  Hub branch and `deleted` push it, per [D4](design.md#d4); the head comment says `h` `l` walk the photograph's row.
  Verify: `grep -n -F 'const hubCell' ui/src/views/RenderLarge.vue` prints one line.
- [x] 2.4 In `ui/src/cells.test.ts`, turn `spec('ui:renders:the-large-view-steps-its-screens-order', …)` into
  `spec('ui:renders:the-large-view-walks-the-photographs-row', …)` over `rowOrder`, per [Tests](design.md#tests).
  Verify: `grep -n -F "spec('ui:renders:the-large-view-walks-the-photographs-row'" ui/src/cells.test.ts` prints one line.
- [x] 2.5 In `ui/src/views/Hub.vue`, `onMounted`'s comment: "A large view's Delete sends the cell it deleted from" →
  "A large view's Esc, Back to Hub and Delete send the cell of the image it closed"; in `ui/src/stores/collection.ts`,
  `focus`'s comment: "Esc from a large view" → "Renders' Esc from a large view", per [D4](design.md#d4).
  Verify: `grep -n -F "A large view's Esc, Back to Hub and Delete send" ui/src/views/Hub.vue` prints one line.
- [x] 2.6 In `isekai/interface/ui/app.py`'s `read_render`, remove the `"cell"` entry and its comment; in
  `ui/src/types.ts`, remove `RenderDetail.cell` and its comment, per [D3](design.md#d3).
  Verify: `grep -n -F 'cell: { version: number; seed: string }[]' ui/src/types.ts` prints nothing.
- [x] 2.7 In `tests/test_ui_api.py`'s `test_compare_takes_any_two_images_of_a_source`, replace the `view["cell"]`
  assertion with `assert "cell" not in view`, and drop "; the hub carries its write order" from its comment, per
  [D3](design.md#d3). Verify: `uv run pytest tests/test_ui_api.py -k any_two_images_of_a_source` exits 0.

## 3 — The prose

Each edit in `ui/design/spec.md` keeps its grepped phrase on one line, rewrapping around it.

- [x] 3.1 J2, *Focus*: "`Esc` from a large view, the Back button and a tab switch come back to the cell left" → "the
  Back button and a tab switch come back to the cell left, and `Esc` from a large view to the cell of the image it closed".
  Verify: `grep -n -F 'to the cell of the image it closed' ui/design/spec.md` prints one line.
- [x] 3.2 J2, *A click or ↵ follows the stage*: "opens the viewer on its newest (`↵ view`), `← →` `h l` step its images
  and `⇧↵` opens the shown one's large view" → "opens the cell modal on its newest (`↵ view`)".
  Verify: `grep -n -F 'opens the cell modal on its newest' ui/design/spec.md` prints one line.
- [x] 3.3 J2, after *A click or ↵ follows the stage*, add a bullet **The cell modal** stating [D1](design.md#d1): its
  head, a row per version, numeric seeds, tiles twice 96×128, `⇄`, the keys, `↵` or a click the large view, `Esc` closing.
  Verify: `grep -n -F '**The cell modal**' ui/design/spec.md` prints one line.
- [x] 3.4 J2, *A cell's images*: "oldest to newest" → "versions oldest first, seeds in numeric order"; after "wrapping"
  add "and last the ready tile, `ready · n images`, as on Renders"; "opens the viewer on it" → "opens the cell modal on it".
  Verify: `grep -n -F 'a click on one opens the cell modal on it' ui/design/spec.md` prints one line.
- [x] 3.5 J2, *The viewer* (the second bullet so named): delete "A hub image's name is `ada.jpg · summon-anime-wai ·
  v2`, without its seed." Verify: `grep -n -F "A hub image's name is" ui/design/spec.md` prints nothing.
- [x] 3.6 J5, *↵ always opens the large view*: "go back to where it was opened, the hub or else Renders, focused on the
  cell or the image left" → "go back to where it was opened: the hub, on the cell of the image it closed, or else
  Renders, on that image". Verify: `grep -n -F 'the hub, on the cell of the image it closed' ui/design/spec.md` prints one line.
- [x] 3.7 J5, the same bullet: "step through the images of that screen, in its order — Renders' row across its flows,
  the hub's cell —" → "walk the photograph's row wherever it was opened — its flows in the hub's column order, versions
  oldest first, seeds in numeric order —". Verify: `grep -n -F "walk the photograph's row wherever it was opened" ui/design/spec.md` prints one line.
- [x] 3.8 §7, the Hub row: ", ⇧↵ the large view" → " · in the cell modal, h j k l or ←↓↑→ move, ↵ the large view,
  esc closes". Verify: `grep -n -F 'in the cell modal, h j k l' ui/design/spec.md` prints one line.
