# Design — 0076 the second walkthrough

How each finding of the second manual pass after `v0.48.0` is closed, but *conjure from this*, its own change.
**Verdict: feasible** — the viewer, the key store, the grids and the session record exist; the change bends them.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `2be8bd2` (`v0.48.0`):

- **Review's panes:** plain `h` `l` `←` `→` (`ui/src/views/Review.vue:448-449`, `nextPane` `:318`); a field passes only
  `inField` commands (`ui/src/stores/keys.ts:170`).
- **Compare:** `c` is declared only `when` a same-seed older version exists (`ui/src/views/RenderLarge.vue:73-77`);
  `library.paired` names the newest (`isekai/interface/ui/library.py:446`); `read_compare`
  (`isekai/interface/ui/app.py:945`); the route `…/:seed/compare` (`ui/src/router.ts:31`).
- **The hub's source cell:** a fixed `250px` column (`ui/src/views/Hub.vue:429`); `.hub__source` a flex row without
  `min-width: 0`, no line breaking (`ui/src/app.css:1625-1664`).
- **The Render dialog:** `confirm` navigates without closing (`ui/src/components/RenderDialog.vue:28-49`); `dialog` in
  the batch store (`ui/src/stores/batch.ts:52`), reset on a batch change alone (`:82`).
- **Key bars:** `KeyBar` on Home, Hub, Review, Renders, the large view, Compare, Sessions, the session page, Billing;
  `?` opens `KeyList` (`ui/src/App.vue:98`, `:176`); rule 1 (`ui/design/spec.md:14`).
- **Renders' moves:** `h` `l` by cell, arrows by image (`ui/src/grid.ts:1`, `Move` `:12`; `ui/src/views/Renders.vue:155-159`);
  scenario `ui:keys:renders-moves-by-cell-and-by-image` (`openspec/specs/ui/spec.md:1417-1420`).
- **The session page:** renders in landing order, every batch photograph below, on clicks alone
  (`ui/src/views/SessionPage.vue:37`, `:84`, `:88`, `:148-168`); the record's `asked` per flow
  (`isekai/foundation/artifacts.py:359`), written by `render.py` (`"asked": dict(asked)`, `isekai/interface/render.py:246`).
- **D25** in `docs/decisions.md` — shortcuts by the physical key, Mod for `⌘` / `Ctrl`.
- **`0069·R12`:** the row move and the IME rule unstated in the keys requirement; trigger: the next change opening
  `ui/src/grid.ts`.

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_render.py` | 38 | `grep -c "def test_" tests/test_render.py` |
| e2e tests | 29 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |
| vitest tests | 33 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -c "^spec("` |

## Goals / Non-Goals

**Goals:** close the nine findings with what exists. **Non-Goals:** a conjure draft from summon; Linux's pane keys; a
dialog besides the viewer.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `keys.ts` reads the platform once (`navigator.userAgentData?.platform`, else `navigator.platform`), injectable for tests; on macOS Review declares `⌃H` / `⌃L` beside `h` / `l`, `inField`, drawn `⌃H ⌃L`; D25 gains the pair | the operator: macOS only | Linux's `Alt` |
| [D2](#d2) | `c` on every large view opens `ImageViewer` in a pick mode over the cell's other images, all versions and seeds, starting on the newest older same-seed image, else the previous; `↵` pushes Compare at `…/:version/:seed/compare/:with/:withSeed`, the same-seed address still answering; `read_compare` takes the pair and reports `different seeds` and `same sheet` | any image with any other | a new picker |
| [D3](#d3) | the hub's source cell a column — the name, `file · dims`, the thumbnail — its first line level with the tick line; `min-width: 0` and `overflow-wrap: anywhere` there, on Renders' source column, Review's rail cards and Home's row name | items 3 and 9 together | ellipsis |
| [D4](#d4) | `confirm` closes the dialog before it pushes; the hub and Renders close it as they unmount | the dialog belongs to its page | |
| [D5](#d5) | `KeyBar.vue` deleted with its uses; a `?` button at the right end of the app bar opens `KeyList`; rule 1 drops *the bottom key bar* | `?` the one place for keys | Review alone |
| [D6](#d6) | `grid.ts`'s moves become `image-` / `image+` crossing cells, into the source column at a row's start, and `row-` / `row+`; `h` `l` and `←` `→` both step images; the source column opens its photograph on `↵`; `0069·R12`: the row move and the IME rule each gain a SHALL clause and a scenario in the keys requirement | one behaviour for letters and arrows | keeping the split |
| [D7](#d7) | the record gains `planned: [{digest, flow, images}]` beside `asked`, version 1 kept (an older record reads as no plan, D32); `sessions.ts` builds the grid — a column per planned photograph, a row per flow, the photographs' row last, a cell's images stacked with a waiting tile per one to come — and its moves; the page draws it, the first render focused on opening and on `Tab`, `↵` opening the viewer over the row | the operator's grid | a format bump |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `cli:render-session:the-record-plans-each-photograph`, `ui:compare:any-two-images-of-a-cell` | none | `tests/test_render.py`, `tests/test_ui_api.py` |
| unit · vitest | `ui:keys:review-panes-move-from-a-field-on-macos`, `ui:sessions:the-grid-holds-each-flow-over-the-originals`, `ui:sessions:the-grid-moves-by-photograph-and-row` | `ui:keys:renders-moves-by-cell-and-by-image` to image steps; `ui:keys:hints-come-from-the-declarations` with no key bar; `0069·R12`'s row move and IME rule rebound to `ui:keys:a-row-move-keeps-the-column` and `ui:keys:an-esc-ending-a-composition-closes-nothing` | `ui/src/stores/keys.test.ts`, `ui/src/grid.test.ts`, `ui/src/sessions.test.ts` |
| e2e | none | the grid test reaches the source cell and opens it; the compare test picks another seed; the render test finds the dialog closed back on the hub | `tests/e2e/test_render.py` |

**End-to-end runs added:** none — three steps in tests that already reach each state (T2). The macOS keys are a vitest
unit with the platform injected, as the e2e runs on Linux.

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** `navigator.platform` is deprecated → `userAgentData` first; a wrong guess only hides `⌃H` `⌃L`.
- **[Trade-off]** a cell of several images stacks in the session grid → the column stays one tile wide.

## Verdict

**Feasible.** Every piece exists; the change bends it to what the pass found.
