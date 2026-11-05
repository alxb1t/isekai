# Design — 0104 the ninth walkthrough

Each decision, settled at the grilling and read at `2c379d2a`. **Verdict: feasible.**

## Context

**The Render dialog** is `ui/src/components/RenderDialog.vue`, mounted by the hub (`ui/src/views/Hub.vue:456`) and
Renders (`ui/src/views/Renders.vue:364`). Its quote comes from `quoteRender()` (`ui/src/api.ts:115`). Each line is
text: the collection's tick (`RenderDialog.vue:143-152`), a `render-dialog__flow` line per flow naming each source
`· name vN ×N` (`:153-159`), and one `Not included:` line (`:160-165`).

**The payload already carries a thumbnail's address.** Each source is `{name, digest, version, images}` and each
left-out `{name, digest, version, flow, reason}` (`ui/src/types.ts:312-326`). `_quoted_row`
(`isekai/interface/ui/app.py:1439-1481`) names a run not among the hub's sources by its run id (`:1450-1452`), so its
`sourceThumbAt` (`api.ts:273-276`) answers 404. The session drawer falls back to `photoUrl({collection, digest, flow})`
(`ui/src/components/SessionDrawer.vue:116-123`, `api.ts:226-228`); the quote's `digest` is the run's 12-character
prefix, the same one `photoUrl` takes.

**The `.render-dialog*` rules are shared.** `DraftDialog.vue` and `ThemeDialog.vue` reuse them (`app.css:192-318`).
`.render-dialog` is 720 px wide with no max height. The hub's tile is `--tile-width` × `--tile-height`, 96×128
(`app.css:10-13`), drawn by `.hub__thumb` (`:1810-1828`). Review's head shows 15 a row, then `+n`
(`ui/src/views/ReviewHead.vue:34`, `:113-126`).

**The tag list** is `ui/src/components/TagAutocomplete.vue`'s `.drop`, `position: absolute; top: 30px` inside
`.row__tags` (`app.css:1465-1478`, `:1189-1195`). The sheet scrolls in `.rows` (`ui/src/components/SheetForm.vue:46`,
`app.css:1162-1166`), so on the last rows the list hangs past `.rows`' foot. `TagInput.vue` alone mounts it
(`:146-158`), and only Review's sheet mounts `TagInput` (`Review.vue:626`). Its keys are `onKey` (`TagInput.vue:71-129`).

**vitest runs in node** (`ui/vitest.config.ts`) with no DOM library, so a component is tested through the pure
module it draws from, as `SessionDrawer.test.ts` tests `useSessionViewer`.

## Goals / Non-Goals

**Goals:** the dialog's photographs as thumbnails by flow, the left-out by reason; the tag list above its input near
the sheet's foot.

**Non-Goals:** the payload and the backend; the estimate, the price, the keep-volume box and the keys; the
`.render-dialog` base rules; the list's place on a scroll while it is open.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | A new `ui/src/thumbs.ts` exports `ROW_THUMBS = 15`, `thumbs(collection, flow, sources)` and `leftOut(collection, left)`. A `Thumb` is `{ key, src, fallback, title, times }`: `key` `` `${collection}\|${digest}\|${flow}` ``, `src` `sourceThumbAt(collection, name)`, `fallback` `photoUrl({ collection, digest, flow })`, `title` `` `${name} v${version}` `` or `name` when `version` is `null`, `times` the source's `images` when above 1, else `null`. `thumbs` returns `{ thumbs, more }`: the first `ROW_THUMBS`, and how many past them. `leftOut` groups by reason and flow, in the order each pair first appears, each group `{ reason, flow, thumbs, more }`, its `times` `null`. `ReviewHead.vue` imports `ROW_THUMBS` from `../thumbs` in place of its own | the grouping, the cap and the badge are logic a unit test reaches in node; one cap for Review's head and the dialog (Q1, Q2, Q3) | the logic in the template; a third `ROW_THUMBS` |
| <a id="d2"></a>**D2** | `RenderDialog.vue` wraps its `render-dialog__collection` sections in `<div class="render-dialog__collections">`. Each flow is a `<div :data-flow="one.flow">` holding its `render-dialog__flow` line, the flow's name and count with no source names, then a `render-dialog__thumbs` row. Each left-out group is a `<div data-left-out>` holding a `render-dialog__left` line, `Not included · <reason> · <flow>`, the flow in `render-dialog__name`, then a `render-dialog__thumbs` row of `render-dialog__thumb render-dialog__thumb--left`, capped as a flow's is. A thumbnail is `<span class="render-dialog__thumb" :title="thumb.title">` holding `<img alt="" loading="lazy">` and, when `times`, `<span class="render-dialog__times mono">×N</span>`; past the cap, in a flow's row and a left-out group's alike, `<span class="render-dialog__more mono">+n</span>`. The script holds `fell = ref<Set<string>>(new Set())`; the template binds `:src="fell.has(thumb.key) ? thumb.fallback : thumb.src"` and `@error` adds `thumb.key` to a new `fell` set. The tick label and the `row.refused` line are kept | Q4's fallback with no payload change: the client cannot tell a run id from a file name, and a source removed since falls back too; a `<span>` and an `<img>` take no focus, so *Keep the volume open* stays first (Q5) | a run-id test in the client; a `<button>` per thumbnail |
| <a id="d3"></a>**D3** | New rules only in `ui/src/app.css`, after `.render-dialog__reason`: `.render-dialog__collections` `max-height: max(160px, calc(100vh - 380px)); overflow-y: auto`; `.render-dialog__thumbs` `display: flex; flex-wrap: wrap`, `gap: 6px`, `padding-left: 22px`, `margin: 0 0 10px`; `.render-dialog__collection--off .render-dialog__thumbs` `opacity: 0.5`; `.render-dialog__thumb` `position: relative`, `var(--tile-width)` × `var(--tile-height)`, `border-radius: 3px`, `overflow: hidden`, `background: var(--placeholder)`, its `img` covering it; `.render-dialog__thumb--left` `opacity: 0.4`; `.render-dialog__times` `position: absolute; right: 4px; bottom: 4px; padding: 0 4px; border-radius: 3px`, 11 px, `var(--ink)` on `var(--raised)`; `.render-dialog__more` `align-self: center`, 12 px, `var(--ink-2)`. No `.render-dialog*` rule above `.render-dialog__reason` changes | the hub's size and the design spec's 3 px radius (Q1); the estimate, the price and the buttons stay in view whatever the collections hold, as about 310 px of the dialog is not the list (Q3); `DraftDialog` and `ThemeDialog` keep their look | a flex `.render-dialog` with a growing list: a base rule |
| <a id="d4"></a>**D4** | A new `ui/src/placement.ts` exports `placement(below: number, above: number, height: number): 'above' \| 'below'`: `'below'` when `below >= height`; else `'above'` when `above >= height`; else `'above'` when `above > below`, and `'below'` otherwise | the rule is pure and unit-tested; a short sheet keeps its list below, and a list that fits neither side takes the larger, so it is never clipped where the other side had the room (Q7, Q10) | an always-above last row; Q7's room-below test alone, which can flip a middle row's list into less room |
| <a id="d5"></a>**D5** | `TagInput.vue` holds `above = ref(false)` and a ref on `TagAutocomplete`. A `watch([open, matches], …, { flush: 'post' })` sets `above` to `false` while closed, else to `placement(<.rows' bottom> − (<.row__tags' top> + 30), <.row__tags' top> − <.rows' top>, <the list's offsetHeight>) === 'above'`, each edge from `getBoundingClientRect()`, `.row__tags` the list's `offsetParent` and `.rows` from `box.value.closest('.rows')`; no `.rows` or no offset parent, below. `TagAutocomplete.vue` takes `above: boolean` and binds `{ 'drop--above': above }` on `.drop`; its comment says it opens above when the room below is short. `app.css` adds `.drop--above` `top: auto; bottom: 100%; display: flex; flex-direction: column-reverse` and `.drop--above .drop__foot` `border-top: 0; border-bottom: 1px solid var(--color-neutral-800)`. `onKey` is unchanged | measured after the list is drawn and before it is painted, from the box the list is placed in — `.drop`'s `top: 30px` below `.row__tags`' top, `.drop--above`'s `bottom: 100%` at it — so chips wrapped above the input neither overstate the room above nor understate the room below; `column-reverse` mirrors it, row 1 nearest the input and the footer on top, and `↓` still moves down the list (Q8, Q10) | floating-ui: a dependency; mirrored keys |
| <a id="d6"></a>**D6** | The record: the `ui` delta's MODIFIED *Render is confirmed…* and *Tag suggestions…* requirements and their new scenarios, `ui:render:the-dialog-shows-thumbnails-by-flow` and `ui:vocabulary:the-list-opens-above-near-the-foot`; `ui/design/spec.md`'s J4·1 frame drawn with thumbnails, as [the frame](#frame) gives it | Q6 | — |

## <a id="frame"></a>The J4·1 frame

In `ui/design/spec.md`'s J4·1 block, the lines from `      ☑ 2026-10-19 3 images` to
`          summon-anime-wai 1 image  · 16_01 v1 count 1` become these, the rest of the block as it is:

```
      ☑ 2026-10-19 3 images                                          a row per collection
          summon-anime-wai 2 images                                  96×128 thumbnails, 15 then +n
          [▒▒]×2                                                     ×n above one · name vN on hover
          conjure-anime-wai 1 image
          [▒▒]
          Not included · a draft · summon-anime-wai                  dimmed, by reason and flow
          [░░]
      ☑ 2026-10-20 1 image                                           the rows scroll in a max height
          summon-anime-wai 1 image
          [▒▒]
```

## Tests

Counted at `2c379d2a`: `git grep -c '^spec(' -- 'ui/src/*.test.ts'` sums to 63 vitest tests, and
`git grep -c '^def test_' -- tests/e2e/` to 19 browser tests, each on Chromium alone.

| layer | adds | removes |
|---|---|---|
| unit | `ui/src/components/RenderDialog.test.ts`, under `ui:render:the-dialog-shows-thumbnails-by-flow`: `thumbs` caps at 15 with `more`, counts only above one, titles with and without a version, the `src` and `fallback` addresses; `leftOut` groups by reason and flow in first-seen order. `ui/src/placement.test.ts`, under `ui:vocabulary:the-list-opens-above-near-the-foot`: the room below holds the list; only the room above does; neither does, each side the larger | none |
| end-to-end | steps only, no new test: `tests/e2e/test_render.py`'s `test_the_render_dialog_opens_on_its_checkbox` reads `render`'s thumbnail, under `ui:render:the-dialog-shows-thumbnails-by-flow`; `tests/e2e/test_review.py`'s `test_the_photograph_opens_in_the_viewer` opens the last field's list, under `ui:vocabulary:the-list-opens-above-near-the-foot` | none |

**The end-to-end runs added:** 0 tests × 1 engine. The steps extend tests that already open the dialog and the
sheet (`T2`); a thumbnail's address and the list's place are what a browser alone shows (`T1`). The dialog's step
leaves its Tab loop as it is, which holds Q5.

This change deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **A 404 before each fallback** → only a run not among the hub's sources costs one, once per open.
- **The list's room is measured once per open and per new matches** → a scroll while it is open keeps its place.
- **A scroller can take focus in Chromium** → `.render-dialog__collections` holds the ticks' inputs, so it takes no
  Tab stop and the dialog's loop is unchanged.
- **The review step leans on a short window** → it sets the viewport; the last field's focus scrolls it to `.rows`' foot.

## Verdict

**feasible.** Every file and symbol named exists at `2c379d2a`; `thumbs.ts`, `placement.ts`, `placement.test.ts` and
`RenderDialog.test.ts` are new.
