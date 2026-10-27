# Design — 0086 compare any image

How the large view's `c` picks any image of the source, and how Compare shows the pair. **Verdict: feasible** — the
large view already reads its source's runs, the view already sets two images side by side; the pick widens to every
flow and the photograph, and the route names what is picked.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `10c6078` (`v0.58.0`):

- **The large view:** `read_render` serves the cell's `images` and `compare`, the newest older version of the seed
  (`isekai/interface/ui/app.py:983`, `:1015`, `:1019`; `library.paired`, `isekai/interface/ui/library.py:433`); `c`
  opens `ComparePick.vue` over the cell's other images, `pick` comparing at once with one other
  (`ui/src/views/RenderLarge.vue:98`, `:194`; `ui/src/cells.ts:82`); *Side by side* `⇧C` (`RenderLarge.vue:105–106`,
  `data-side-by-side` `:175`).
- **The route:** `/c/:collection/renders/:digest/:flow/:version/:seed/compare/:with?/:withSeed?` (`ui/src/router.ts:29`);
  `read_compare` at `…/compare` and `…/compare/{other}/{other_seed}`, one flow, the older before
  (`app.py:1026–1070`).
- **The view:** `Compare.vue` sets `before` and `after` with the changed fields and the seeds
  (`ui/src/views/Compare.vue:10–34`, `:105–107`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_api.py` | 80 | `grep -c "def test_" tests/test_ui_api.py` |
| vitest tests | 44 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -cE "^(spec\|test\|it)\("` |
| e2e tests | 32 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** any image of a source beside any other, the photograph among them. **Non-Goals:** across sources; Review's
side by side.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **the source's images:** `read_render` adds `source`, the source's images by flow — each offered flow holding images, its versions oldest first — beside the cell's `images` | the pick reads one payload | a request per flow |
| [D2](#d2) | **the pick** `ComparePick.vue`, its own grid: the photograph's row on top, a row per flow headed by its name, tiles at Renders' size named `vN · seed`, the image compare started from marked; `cells.ts` gains `sourceGrid(detail)` and `movePick(grid, at, move)` — `h j k l` and the arrows, the column kept, held at a shorter row's end; the focus on the newest older version of the seed, else the image before it, else the photograph; `↵` compares, `Esc` closes; `pick`'s compare-at-once deleted | the app's grid keys, a layout for the choice | the drawer's grid |
| [D3](#d3) | **the route** `…/compare/:withFlow/:withVersion/:withSeed` and `…/compare/photo`, replacing `…/compare/:with?/:withSeed?`; the API `…/compare/{other_flow}/{other_version}/{other_seed}` and `…/compare/photo`, replacing `…/compare` and `…/compare/{other}/{other_seed}` | a pair across flows names the flow | |
| [D4](#d4) | **the view:** `left` the image picked, `right` the image compare started from, each headed by its flow, version and seed; between renders the fields both flows declare, marked where they differ, *different seeds* and *same sheet* as today; with the photograph the pair alone, at equal height; `before` and `after` become `left` and `right` | the eye returns to where it came from, on the right | the older before |
| [D5](#d5) | **`⇧C` and *Side by side* leave the large view**; Review's `⌃P` stays | the photograph is a pick | |
| [D6](#d6) | **the docs:** `ui/design/spec.md`'s J5 large-view and Compare bullets, its `J5·9` drawing (picked left, origin right) and §7's Renders row (`⇧C *Side by side*` deleted) | the docs name what the screen does | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | none | `ui:compare:any-two-images-of-a-cell` — summon against flat summon, the picked left; `ui:compare:a-seed-pairs-with-its-newest-older-version` — the pick's start | `tests/test_ui_api.py` |
| unit · vitest | `ui:compare:the-pick-moves-by-row-and-column` | none | `ui/src/cells.test.ts` |
| e2e | none | `test_compare_shows_both_versions_of_a_seed_and_the_field_that_changed` — the grid, the picked left; `test_side_by_side_sets_the_image_beside_its_photograph` — the photograph's row | `tests/e2e/test_render.py` |

**End-to-end runs added:** none.

**Removed or merged:**

| test | where | goes to |
|---|---|---|
| `ui:compare:one-other-image-is-compared-at-once` | `ui/src/cells.test.ts` | retired by [D2](#d2): the photograph is always a choice, so a pick never holds one image alone |

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** two flows with different schemas → the view marks the fields both declare; a field one alone declares is
  not compared.
- **[Trade-off]** the older-before order goes → picked left, origin right, whichever is older.

## Verdict

**Feasible.** The payload widens, the route names the pick, the view orders the pair.
