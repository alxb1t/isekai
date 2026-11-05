# Design — 0099 the eighth walkthrough

Each fix, settled at the grilling and read at `22291a5f`. **Verdict: feasible.**

## Context

The sheet is one component, `ui/src/components/ImportSheet.vue`, for New collection (Home, `⇧N`) and Add sources (the
hub, `⇧A`). Its keys are an `overlay` layer (`:362-402`), which masks the screen's (`ui/src/stores/keys.ts:163-171`),
and `keys.press` runs a command in the `keydown` itself (`keys.ts:190-191`), so a command's `picker.click()` is a user
gesture. Its hidden picker (`:448-455`) is clicked on mount (`:412-415`) and by *Add files…* (`:440-447`).

`remove()` (`ImportSheet.vue:263-293`) sets no guard before its `await`, and its hand-off (`:271-275`) and `settle()`'s
reset (`:161-172`) are held by no test: the backlog cards `0091·R5`, `0091·R7` and `0091·R8`.

The hub's `place()` (`ui/src/views/Hub.vue:316-329`) scrolls `nearest` for a key's move (`moveBy`, `:346-347`;
`select`, `:339-344`), a click (`:274`, `:483`, `:529`, `:566`) and, with `{ block: 'center' }`, a restored focus
(`:427`). The library's `walk()` (`ui/src/views/Home.vue:50-53`) is a bare `.focus()`. Each screen scrolls in its
`<section>`: `.hub` and `.home` are `overflow-y: auto` (`ui/src/app.css:1718-1722`, `:791-795`).

The open versions: `0097-the-gpunit-upgrade` shares no file. `0098-the-catppuccin-themes` adds a requirement to
`openspec/specs/ui/spec.md` and `⇧T` to `ui/design/spec.md` §7's *everywhere* row; this version modifies other
requirements and §7's *dialogs* row, and touches no CSS file.

## Goals / Non-Goals

**Goals:** the cards paid, each with a unit step; `⇧A` in the sheet; the head or the foot shown at an edge row.

**Non-Goals:** Renders, its routes and `⇧I`; Review's rail; the sheet's tiles' scroll; a restored focus; any CSS.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `0091·R5`: `removal(phase, state, leaving = false)` in `ui/src/staging.ts` returns `null` when `leaving`. `ImportSheet.vue` keeps `const leaving = new Set<number>()` of tile keys; `remove()` reads `removal(one.phase, one.result?.state, leaving.has(one.key))`, adds `one.key` before `removing.value += 1`, and deletes it in its `finally`. The template's `removal(one.phase, one.result?.state)` stays as it is | a second press sends no second `DELETE`, so no false refusal and no `Removing 2 files` for one file; the guard is a pure step a unit test reaches | hiding `×` while the removal is in flight |
| <a id="d2"></a>**D2** | `0091·R7`: `Phase` and `Tile` move from `ImportSheet.vue` into `staging.ts`, exported, comments with them. `handOff(tiles: Tile[], one: Tile): string \| null` hands `one`'s `upload`, `result` and `asIs` to the first copy `heir` finds and returns `null`, else returns `one.result.name`, or `null` with no result. `remove()` calls it for a `'staging'` removal and sends `removeStaged` for the name it returns | the hand-off is held by a test of its effect, not only of the index `heir` picks | returning the heir's index for the caller to copy onto |
| <a id="d3"></a>**D3** | `0091·R8`: `requeue(tiles: Tile[]): Tile[]` in `staging.ts` clears `upload` and `result`, sets `phase` to `'queued'` and `progress` to `0` on each tile `orphans` names, and returns them. `settle()` keeps its `apply` loop, then calls `pump()` when `requeue(tiles.value)` returns any | the reset is held by a test of the cleared fields; `orphans` stays, with its steps | folding it into `handOff` |
| <a id="d4"></a>**D4** | `ImportSheet.vue`'s overlay keys gain `{ id: 'add-files', keys: [shifted('KeyA')], label: 'add files', run: () => picker.value?.click(), when: () => !committing.value }`, no `inField`; *Add files…* reads `Add files…<KeyHint command="add-files" />`. `⇧N` stays Home's alone | the hub's `⇧A` means *add sources*, so in the sheet it adds more; a text field keeps its `A` | `⇧N` in the sheet |
| <a id="d5"></a>**D5** | A new `ui/src/composables/useEdges.ts`: `useEdges(page: () => HTMLElement \| null \| undefined)` returns `(cell: HTMLElement, row: number, rows: number) => void`, which at `row === 0` calls `page()?.scrollTo({ top: 0 })`, else at `row === rows - 1` `page()?.scrollTo({ top: <page's scrollHeight> })`, then scrolls `cell` into view `{ block: 'nearest' }` | one rule for the hub and Home, in the script; `nearest` last keeps the focused row and a wide grid's column in view, past a foot taller than the window | CSS `scroll-padding` or a sticky head: 0098 rewrites the CSS |
| <a id="d6"></a>**D6** | The hub's `<section class="hub">` and Home's `<section class="home">` each take `ref="page"`, and each script holds `const page = ref<HTMLElement \| null>(null)` and `const reveal = useEdges(() => page.value)`. `place()`'s third parameter becomes `how: ScrollIntoViewOptions \| 'key' = { block: 'nearest' }`; `moveBy` and `select` pass `'key'`, which reveals the focused cell by `reveal(cell, focus.value.row, rows)`; a click and a restored focus scroll as now. `walk()` focuses its row with `{ preventScroll: true }`, then `reveal(row, index, held.length)` | only a key's move reaches an edge rule; Review's rail already centres | the rule on a click too |

## Tests

The tests a change adds are counted at `22291a5f`: `git grep -c '^spec(' -- 'ui/src/*.test.ts'` sums to 58 vitest tests,
`git grep -c '^def test_' -- tests/e2e/` to 19 browser tests, each on Chromium alone.

| layer | adds | removes |
|---|---|---|
| unit | steps in `ui/src/staging.test.ts`: the `leaving` guard under `ui:sheet:a-chosen-file-is-removed-alone`; `handOff` and `requeue` under `ui:sheet:a-removed-files-copy-keeps-it`. One new test, `ui/src/composables/useEdges.test.ts`, under `ui:batch-folder:an-edge-row-shows-the-head`: the hub's scenario is a browser's | none |
| end-to-end | steps only, no new test: `tests/e2e/test_import.py`'s `_choose` opens the chooser by `⇧A`, and its first caller checks the hint, under `ui:sheet:shift-a-opens-the-file-dialog`; `tests/e2e/test_prepare.py`'s `test_a_tick_assigns_the_flow_and_survives_a_reload` walks a short window's rows, under `ui:hub:an-edge-row-shows-the-head` | none |

**The end-to-end runs added:** 0 tests × 1 engine. The steps extend tests that already reach the sheet and the hub (`T2`);
the scroll and the file dialog are what a browser alone shows (`T1`). The vitest suite runs in node, so
`useEdges.test.ts` stubs `scrollIntoView`, `scrollTo` and `scrollHeight`, as `useCentred.test.ts` does.

This change deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **The mount's own picker click opens a chooser before `⇧A`'s** → `_choose` answers the mount's with no files first,
  so it ends before `⇧A`'s opens.
- **The hub's step leans on a short window** → it sets the viewport itself, so the grid overflows whatever the default.
- **An edge row scrolls to the edge, then by `nearest`** → each is instant; `nearest` moves nothing while the row is in view.

## Verdict

**feasible.** Every file and symbol named exists at `22291a5f`; `useEdges.ts` and `useEdges.test.ts` are new.
