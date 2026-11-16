# The review rules — design

Pure modules take Review's viewer and status rules out of its `<script setup>`; the view switches to them and its behaviour does not move. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`ui/src/views/Review.vue` is 692 lines at the cut (`wc -l`). Its setup holds a viewer rule (`viewed`, `ui/src/views/Review.vue:132-141`), the `⌃P` transition (`photograph`, `ui/src/views/Review.vue:388-393`), the time formats (`clock` and `minute`, `ui/src/views/Review.vue:143-156`) and the status line (`kicker`, `ui/src/views/Review.vue:172-182`). Vitest cannot import a view's setup locals, so none of them has a test of its own.

```
before                           after
Review.vue                       Review.vue ──▶ lens.ts    viewedOf · photographStep
  viewed · photograph                       └──▶ kicker.ts  kickerOf · clock · minute
  clock · minute · kicker
```

Review's own refs and computeds (`lens`, `photos`, `opened`, `revised`, `revision`, `drafted`, `approvedAt`) stay in the view. The modules take plain values and return plain values; neither imports Vue.

## Goals / Non-Goals

- **Goal:** each rule lives in a module with its test written first, and the view reads it.
- **Goal:** the view shows the same viewer, the same `⌃P` steps and the same status words as before.
- **Non-goal:** the actions (reread, discard, approve, cancel), the sheet's history, the panes, the chips, `openLens` and `closeLens`, a key's declaration, the CSS.
- **Non-goal:** a scenario, a requirement or a decision: a patch adds none.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `ui/src/lens.ts` holds `Lens`, `viewedOf` and `photographStep` | the viewer's choice and `⌃P`'s steps are rules over a lens, a revision and the rail's photographs | a `useLens` composable: the lens' DOM code is the view's, and no ref moves |
| [D2](#d2) | `ui/src/kicker.ts` holds `kickerOf`, `clock` and `minute` | the status line and the time formats are rules over values the view already has | a composable: nothing here is reactive state |
| [D3](#d3) | each test binds the scenario whose text covers its rule; a rule no scenario covers moves untested and is named below | a vitest test has no exempt form, and a patch adds no requirement | a bare `test(`, or a new scenario |
| [D4](#d4) | each phase writes its test file, then its module, then switches the view | the test is first; the phase still ends green | a test written after the switch |
| [D5](#d5) | the view keeps its one `useKeys` call, its commands in today's order, and every class and `data-*` hook | a second call makes a newer layer that answers first, and the key scans read the view alone | none |
| [D6](#d6) | the `Review.vue` row of `BIG_UI_FILES` is lowered to the view's new length and stays | the view is still over its ceiling, and its row goes with its actions | removing the row now: the view still offends |

### D1

`ui/src/lens.ts` exports:

```ts
export type Lens = 'photo' | 'render' | 'pair' | 'cheatsheet'
export function viewedOf(
  lens: Lens | null,
  photos: Shown[],
  opened: number,
  revised: { src: string; seed: string | null } | null,
): { images: Shown[]; start: number } | null
export function photographStep(lens: Lens | null, revised: boolean): 'photo' | 'pair' | 'close'
```

`Shown` is the type `ui/src/components/ImageViewer.vue` exports. `viewedOf` is the body of `viewed` with its inputs as arguments: `photo` gives the photographs from the open one, `render` the image alone, `pair` the photograph and the image, and any lens with no image to show gives `null`. The image's name is `render · seed N`, or `the image it was drafted from` when the seed is `null`.

`photographStep` is the branch order of `photograph`: `pair` steps to `photo`; `photo` steps to `pair` when there is an image, else to `close`; any other lens opens `pair` when there is an image, else `photo`. The view then closes, assigns or opens:

```ts
function photograph(): void {
  const to = photographStep(lens.value, revised.value !== null)
  if (to === 'close') closeLens()
  else if (lens.value === 'pair' || lens.value === 'photo') lens.value = to
  else void openLens(to)
}
```

### D2

`ui/src/kicker.ts` exports:

```ts
export function clock(at: number | null): string | null
export function minute(at: number | null): string | null
export interface Standing {
  drafted: boolean
  approved: boolean
  readonly: boolean
  approvedAt: string | null
  revision: { seed: string | null; version: number } | null
}
export function kickerOf(held: Standing): string
```

`clock` and `minute` are today's arrow functions, unchanged. `kickerOf` is the branch order of `kicker`, with `drafted.value !== null` as `drafted`, `Boolean(sheet.detail.value?.approved)` as `approved`, `sheet.readonly.value` as `readonly` and `approvedAt.value` as `approvedAt`. The comments that explain why the order holds move with the code. The view's `kicker` becomes one `computed` calling `kickerOf`, and its `approvedAt` stays a `computed` over `clock`.

### D3

| module | case | scenario it binds | covers |
|---|---|---|---|
| `lens.ts` | the photograph's lens gives the rail's photographs from the open one | `ui:review:the-photograph-opens-in-the-viewer` | `viewedOf` with `photo`; `photographStep` from no lens with no image |
| `lens.ts` | the pair gives the photograph and the image, then the photograph's lens follows it | `ui:revise:side-by-side-shows-the-pair` | `viewedOf` with `pair` and with `photo`; `photographStep` from no lens with an image and from `pair` |
| `lens.ts` | the image is headed by its seed, or `the image it was drafted from` | `ui:conjure-from:conjure-from-this-opens-review` | the image's name in `viewedOf` |
| `kicker.ts` | a draft from another flow's approval is a plain draft, naming no approval | `ui:conjure-from:conjure-from-this-opens-review` | `kickerOf` with `drafted` and not `approved` |

The rules no scenario covers move untested, each a copy of today's text: the `render` lens alone in `viewedOf`, `photographStep` from `photo`, with or without an image, `kickerOf` for a sheet not yet read, an approved sheet with and without its time, a re-opened sheet, and a revision of a render or of a version, and `clock` and `minute`. The view's browser tests still run them in CI.

### D4

Phase 1 writes `ui/src/lens.test.ts`, then `ui/src/lens.ts` in the same task, then switches `Review.vue`. Phase 2 does the same for `ui/src/kicker.test.ts` and `ui/src/kicker.ts`, then lowers the ratchet row. A test names the module's exports and each case's assertions are the text of its scenario's WHEN and THEN, so it fails when a branch of the rule is removed.

### D5

The view's `useKeys('screen', …)` stays one call. `photographKey` keeps its `run: photograph`. No module declares a key.

### D6

`BIG_UI_FILES` holds the row of `ui/src/views/Review.vue` alone. The ratchet checks the row's name and the table's count, not its number, and a row's number may only fall. Phase 2 sets it to `wc -l` of the view after the switch.

## Tests

The change adds vitest tests at the lowest layer, the unit layer, and no end-to-end run: the scenarios of [D3](#d3) are `e2e` scenarios whose browser tests already run in CI (`T1`). No test is deleted or merged (`T5`), so there is no table of removals.

| layer | file | change | command that lists it |
|---|---|---|---|
| unit (vitest) | `ui/src/lens.test.ts` | each case of [D3](#d3)'s `lens.ts` rows is added | `git grep -n "^spec(" -- ui/src/lens.test.ts` |
| unit (vitest) | `ui/src/kicker.test.ts` | the case of [D3](#d3)'s `kicker.ts` row is added | `git grep -n "^spec(" -- ui/src/kicker.test.ts` |
| structural (pytest) | `tests/test_ratchets.py` | no test is added; the `Review.vue` row's number is lowered | `git grep -n "Review.vue" -- tests/test_ratchets.py` |

The tests run in `make gate` by `uv run python -m tools.test_ui`. No test takes more than a second, and none needs a marker for `slow`.

## Dependencies

None.

## Risks / Trade-offs

- **A branch moves with a changed order.** `kickerOf` and `photographStep` are branch chains where the order is the rule. The tests of [D3](#d3) fail on a swap of the covered branches; the rest is held by copying the text and by the browser tests in CI.
- **A scenario bound from a unit test is an `e2e` scenario.** The binding names the rule's text; the `e2e` binders stay where they are, so no key loses its layer.
- **The row's number is not checked.** A wrong number passes the ratchet; the task takes it from `wc -l`, and its Verify shows the old number gone.

## Verdict

Feasible. The rules are pure, every reader of them is inside `ui/src/views/Review.vue`, and no test or document reads them elsewhere.
