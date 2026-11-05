# Design — 0105 the tenth walkthrough

Each fix, settled at the grilling and read at `2c379d2a`. **Verdict: feasible.**

## Context

**The rule** is `useEdges(page)` (`ui/src/composables/useEdges.ts:3-12`): a key's move to row 0 scrolls `page` to its
top, to the last row to its foot, then the cell scrolls `nearest`. The caller focuses the cell with `preventScroll`.
The hub's `place()` (`ui/src/views/Hub.vue:317-338`) and the library's `walk()` (`ui/src/views/Home.vue:54-60`) use it.

**The drawer** is `ui/src/components/SessionDrawer.vue`.

- Its grids are stacked by `stacked()` (`:128`); `located()` (`ui/src/sessions.ts:118-125`) names the grid a stacked
  row falls in.
- Its keys (`:176-202`) move by `go` (`:169`), which calls `place(at)` (`:154-159`); `place` only focuses, as it does
  for the first focus (`:210`, `:224`).
- The scroller is the `<dialog class="drawer">` (`:229`, `dialog` `:35`): `.drawer` is `100vh` and sets no overflow
  (`ui/src/app.css:524-536`), so the open modal scrolls itself.
- Each grid's `<section data-session-collection>` opens with its `.session__collection` label (`:252-260`).

**The sheet** is `ui/src/components/ImportSheet.vue`.

- Its tile keys (`:370-382`) call `move()` (`:243-245`), which calls `focusTile(index)` (`:232-235`); `remove()`
  (`:272`), `closeViewer()` (`:299`) and the first focus (`:305`) call it too.
- The scroller is `<div class="import__body">` (`:449`; `app.css:1961-1966`); `sources · N · size` (`:451`) sits above
  the tiles.
- `stepped()` (`ui/src/staging.ts:126-134`) lays a row as `columns` wide, or the whole count at 0.

**The open version** `0104-the-ninth-walkthrough` shares no code file. It modifies other `ui` requirements; both add a
`CHANGELOG.md` entry.

## Goals / Non-Goals

**Goals:** the drawer's head and foot, a later grid's name, and the sheet's label shown on a key's move.

**Non-Goals:** Renders; Compare's pick; a click, a restored focus or a first focus; `useEdges.ts`; any CSS.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `SessionDrawer.vue` imports `useEdges` from `../composables/useEdges` and holds `const reveal = useEdges(() => dialog.value)`. `place(at: Focus, key = false)` looks up the cell in its `nextTick`; with `key` it calls `cell.focus({ preventScroll: true })`, then `reveal(cell, at.row, stack.value.last.length)`; without, `cell.focus()` as now. `go` calls `place(…, true)`; both `place(start())` calls stay | the hub's rule, on the scroller the drawer already has; only a key's move reaches it, as on the hub | a new ref on `.session` — it does not scroll |
| <a id="d2"></a>**D2** | In `place`'s `key` branch, after `reveal`, when `located(stack.value, at.row).row === 0`, `cell.closest('[data-session-collection]')?.querySelector('.session__collection')?.scrollIntoView({ block: 'nearest' })` | the label sits just above its grid's first row, so `nearest` after the cell's keeps both in view; on stacked row 0 the drawer is at its top already, and it moves nothing | the label for every row of a grid |
| <a id="d3"></a>**D3** | `ImportSheet.vue` imports `useEdges`, puts `ref="scroller"` on `<div class="import__body">` and holds `const scroller = ref<HTMLElement \| null>(null)` and `const reveal = useEdges(() => scroller.value)`. `focusTile(index: number \| null, key = false)` looks up the tile in its `nextTick`; with `key` it calls `tile.focus({ preventScroll: true })`, then, with `const wide = columns() \|\| shown.value.length`, `reveal(tile, Math.floor(index / wide), Math.ceil(shown.value.length / wide))`; without, `tile.focus()` as now. `move()` calls `focusTile(…, true)`; every other call stays | `wide` is `stepped()`'s, so the row the reveal reads is the row the move made | a helper in `staging.ts`: two lines, read once |
| <a id="d4"></a>**D4** | An e2e step each, in a short window: `tests/e2e/test_render.py`'s `test_the_drawer_holds_the_render` ends on the `WIDE` drawer at 800 × 520, and `tests/e2e/test_import.py`'s `test_each_chosen_file_shows_its_upload_then_its_result` walks its tiles at 560 × 520, one tile a row, before *Cancel* | a scroll is what a browser alone shows; each test already reaches the state (`T1`, `T2`); 560 px leaves the files' column one 142 px tile wide; 520 px holds the head and the first row, not the foot | a unit test: vitest has no DOM, and `useEdges.test.ts` holds the rule |

## The e2e steps

Each step, per [D4](#d4), checks the state before it moves.

- **The drawer**, last in `test_the_drawer_holds_the_render`: `[data-outcome]` reads `done`;
  `page.set_viewport_size({"width": 800, "height": 520})`; `drawer.locator('[data-cell="0-0"]').focus()`; `j` →
  `[data-session-timer]` `not_to_be_in_viewport()` and `[data-renders]` `to_be_in_viewport()`; `k` →
  `[data-session-timer]` `to_be_in_viewport()`.
- **The sheet**, before *Cancel* in `test_each_chosen_file_shows_its_upload_then_its_result`:
  `page.set_viewport_size({"width": 560, "height": 520})`; `_tile(page, "held.jpg").focus()`; `j` →
  `expect(_tile(page, "plain.heic")).to_be_focused()` and `page.locator(".import__files > .section-label").first`
  `not_to_be_in_viewport()`; `k` → it `to_be_in_viewport()`.

## Tests

The tests a change adds are counted at `2c379d2a`: `git grep -c '^spec(' -- 'ui/src/*.test.ts'` sums to 63 vitest tests,
`git grep -c '^def test_' -- tests/e2e/` to 19 browser tests, each on Chromium alone.

| layer | adds | removes |
|---|---|---|
| unit | none: the rule is `useEdges`', held by `ui/src/composables/useEdges.test.ts` under `ui:batch-folder:an-edge-row-shows-the-head`, unchanged | none |
| end-to-end | steps only, no new test: `test_the_drawer_holds_the_render` under `ui:sessions:an-edge-row-shows-the-head`; `test_each_chosen_file_shows_its_upload_then_its_result` under `ui:sheet:an-edge-row-shows-the-head` | none |

**The end-to-end runs added:** 0 tests × 1 engine. Each step extends a test that already reaches the drawer or the
sheet (`T2`). The steps run by `make e2e`, in CI, outside the gate.

This change deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **[D2](#d2) is held by no test** → the settled steps walk one grid; no e2e session holds two collections, so a
  later grid's label is read by eye.
- **Each window is sized by estimate** → 520 px holds the drawer's head and its first row, and the sheet's label and
  its first tile, under the open modal's `overflow: auto`; a taller head breaks the step in CI, not the rule.
- **The old code's failure leans on Chromium's focus scroll** → a partly shown target scrolls to its nearest edge, a
  hidden one to the centre; in both steps the target is partly shown, the sheet's by about 8 px.
- **The `WIDE` session could still be running at `j`** → the step waits for `[data-outcome]` to read `done` first, so
  the foot no longer grows.

## Verdict

**feasible.** Every file and symbol named exists at `2c379d2a`; no file is added.
