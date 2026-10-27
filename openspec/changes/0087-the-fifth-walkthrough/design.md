# Design — 0087 the fifth walkthrough

Six fixes of the fifth pass. **Verdict: feasible** — each is a template branch, a scroll, a key, a caption, a
layout, or a step over a sequence the page already holds.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `7301425` (`v0.59.0`):

- **The bar:** its count branch shows whenever any collection is short, its running branch only when none is
  (`ui/src/components/RenderBar.vue:34`, `:58`); `bar()` and `reasons()` build its state (`ui/src/bars.ts:23`, `:33`).
- **The restore:** Renders restores its focus with `hold` and scrolls nothing (`ui/src/views/Renders.vue:219–220`); a
  key's move scrolls `nearest` (`go`, `:132–147`); the hub restores likewise (`ui/src/views/Hub.vue:388–400`).
- **The keys:** `compare` is `plain('KeyC')` (`ui/src/views/RenderLarge.vue:86–87`); the large view declares `⇧D`, `c`,
  `Esc` (`:77–95`) and knows where it came from, `history.state.from` (`:69–74`); Renders' `h l` (`Renders.vue:156–157`);
  D25's clause *always for one that writes* (`docs/decisions.md:390`).
- **The pick:** captions `v<N> · seed <S>` (`ui/src/components/ComparePick.vue:96–97`).
- **Compare:** `.compare__sides` sized to the window, not centred (`ui/src/views/Compare.vue:109`;
  `ui/src/app.css:702–706`); each image's `count · seeds · tokens` line (`Compare.vue:121`); the change block
  (`data-changed`, `:124–135`); `read_compare` returns `changed`, `different_seeds` and `same_sheet`
  (`isekai/interface/ui/app.py:1034`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_api.py` | 80 | `grep -c "def test_" tests/test_ui_api.py` |
| vitest tests | 45 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -cE "^(spec\|test\|it)\("` |
| e2e tests | 32 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** the six fixes. **Non-Goals:** the isekai command; any change to the render job or the drawer.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **the bar while a session runs:** `bar()` takes the running session's plan; while one runs the bar shows its totals (`image 2 of 4 · 06:41 of ≤10:30`) and *Session* `⌃;`; the images short and not in its plan read `n images wait for the next session`; Render and *A render session is running.* are hidden | they are rendering, not ready | Render shown disabled |
| [D2](#d2) | **the restore:** Renders and the hub scroll a restored focus to the window's centre once the grid is drawn — `nextTick`, then `scrollIntoView({ block: 'center' })`; a key's move keeps `nearest` | the eye finds it | `nearest` on restore |
| [D3](#d3) | **the key rule:** `compare` takes `shifted('KeyC')`; D25's rule reads *a plain letter moves; a command is `⇧` + a letter* | the last plain-letter command; one rule | |
| [D4](#d4) | **the pick:** each tile's caption `v<N>`; the pick's head names the focused tile, `Compare <flow> v<N> · seed <S> with <flow> v<M> · seed <T>…` | a 64-bit seed breaks the grid; two seeds of one version told apart | |
| [D5](#d5) | **Compare:** each image under its one-line head alone; the `count · seeds · tokens` lines and the change block deleted; `.compare__sides` centred, the pair as tall as the window less the app bar and the heads; the page's padding the app's 12 px; `read_compare` drops `changed`, `different_seeds` and `same_sheet` | the images as big as possible | keeping the fields unread |
| [D6](#d6) | **`h` `l` on the large view:** `cells.ts` gains `screenOrder(detail, from)` — from Renders, the source's renders across its flows, as Renders' row; from the hub, the cell's; `h` `l` and `←` `→` replace the address with the step before or after, held at either end; the head adds `2 of 5`; `Esc` returns focused on the image shown | the screen's own order | `j` `k` |
| [D7](#d7) | **the docs:** D25 in `docs/decisions.md` per [D3](#d3); `ui/design/spec.md` — the Render bar's running state, J5's `Compare with…  c` → `⇧C`, the pick, the Compare drawing, §7's large-view keys gaining `h l` | the docs name what the screen does | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | none | `ui:compare:any-two-images-of-a-cell` — no changed fields | `tests/test_ui_api.py` |
| unit · vitest | `ui:render:a-running-session-shows-its-totals`; `ui:renders:the-large-view-steps-its-screens-order`; `ui:compare:the-pick-names-the-focused-tile` | none | `ui/src/bars.test.ts`, `ui/src/cells.test.ts` |
| e2e | none | `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from` and the hub's `test_a_rendered_cell_opens_its_newest_image` — the image in view after `Esc`; the compare tests press `Shift+C` and find no change block | `tests/e2e/test_render.py` |

**End-to-end runs added:** none.

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a centred scroll on every restore jumps the page → it runs once, on opening, where the page was at its top.
- **[Trade-off]** Compare no longer lists the changed fields → the large view and Review carry the sheet.

## Verdict

**Feasible.** Six small fixes over what the pages already hold.
