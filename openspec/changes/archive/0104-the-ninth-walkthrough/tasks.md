# Tasks — 0104 the ninth walkthrough

The thumbnails, then the flip, then the record, per [design](design.md). Each new test or step carries the `spec` key
its task names.

## Progress

- [x] 1 — The thumbnails
- [x] 2 — The flip
- [x] 3 — The record

## 1 — The thumbnails

- [x] 1.1 Add `ui/src/thumbs.ts` per [D1](design.md#d1): `ROW_THUMBS`, the `Thumb` shape, `thumbs` and `leftOut`, from
  `./api` and `./types` alone.
  Verify: `grep -n -e '^export const ROW_THUMBS = 15$' -e '^export function thumbs(' -e '^export function leftOut(' ui/src/thumbs.ts` prints a line for each.
- [x] 1.2 In `ui/src/views/ReviewHead.vue`, delete `const ROW_THUMBS = 15` and the comment above it, and import
  `ROW_THUMBS` from `../thumbs`, per [D1](design.md#d1); its template is unchanged.
  Verify: `grep -n "import { ROW_THUMBS } from '../thumbs'" ui/src/views/ReviewHead.vue` prints a line.
- [x] 1.3 Add `ui/src/components/RenderDialog.test.ts` under `ui:render:the-dialog-shows-thumbnails-by-flow`, the cases
  [design](design.md#tests)'s unit row names, over `thumbs` and `leftOut`.
  Verify: `npm --prefix ui run test -- src/components/RenderDialog.test.ts` exits 0.
- [x] 1.4 In `ui/src/components/RenderDialog.vue`, draw the flows and the left-out per [D2](design.md#d2), and its head
  comment's `per flow what renders and what is left out` → `per flow the thumbnails of what renders and, dimmed, of what is left out`.
  Verify: `grep -n -F -e 'class="render-dialog__collections"' -e 'render-dialog__thumb--left' -e 'class="render-dialog__times mono"' -e 'fell.has(thumb.key)' ui/src/components/RenderDialog.vue` prints a line for each.
- [x] 1.5 In `ui/src/app.css`, add [D3](design.md#d3)'s rules after `.render-dialog__reason`, under the comment
  `/* The Render dialog's thumbnails (J4·1): new rules, as DraftDialog and ThemeDialog share the ones above. */`.
  Verify: `grep -n -e '^\.render-dialog__collections {' -e '^\.render-dialog__thumbs {' -e '^\.render-dialog__thumb {' -e '^\.render-dialog__thumb--left {' -e '^\.render-dialog__times {' -e '^\.render-dialog__more {' ui/src/app.css` prints a line for each.
- [x] 1.6 In `tests/e2e/test_render.py`'s `test_the_render_dialog_opens_on_its_checkbox`, add the key
  `ui:render:the-dialog-shows-thumbnails-by-flow` and, after `expect(keep).to_be_focused()`, a step: `render`'s `FLOW` row
  holds one `.render-dialog__thumb`, titled `gia.jpg v1`, its `img` `src` ending `/sources/gia.jpg/thumb`, no `.render-dialog__times`.
  Verify: `grep -n -e 'ui:render:the-dialog-shows-thumbnails-by-flow' -e 'render-dialog__thumb' tests/e2e/test_render.py` prints a line for each.

## 2 — The flip

- [x] 2.1 **HALT CHECK** `.rows` is the sheet's scroller, around every `FieldRow`, as [D5](design.md#d5) measures it.
  Verify: `grep -n -F '<div class="rows">' ui/src/components/SheetForm.vue` prints a line.
- [x] 2.2 Add `ui/src/placement.ts` per [D4](design.md#d4), and `ui/src/placement.test.ts` under
  `ui:vocabulary:the-list-opens-above-near-the-foot`, at a height of 300: below 300, above 500 is `'below'`; below 100, above 400
  is `'above'`; neither holding it, below 120, above 200 is `'above'` and below 200, above 120 is `'below'`.
  Verify: `npm --prefix ui run test -- src/placement.test.ts` exits 0.
- [x] 2.3 In `ui/src/components/TagAutocomplete.vue`, add the `above: boolean` prop and the `drop--above` binding per
  [D5](design.md#d5); its comment's `under its row:` → `under its row, or above it, mirrored, when only the room above holds it, or neither does and above is larger:`.
  Verify: `grep -n -F -e 'above: boolean' -e "'drop--above': above" ui/src/components/TagAutocomplete.vue` prints a line for each.
- [x] 2.4 In `ui/src/components/TagInput.vue`, measure and pass `above` per [D5](design.md#d5), the room from the list's
  `offsetParent` (`.row__tags`), not the input; `onKey` is unchanged.
  Verify: `grep -n -F -e "closest('.rows')" -e 'offsetParent' -e 'placement(' -e ':above="above"' ui/src/components/TagInput.vue` prints a line for each.
- [x] 2.5 In `ui/src/app.css`, add [D5](design.md#d5)'s `.drop--above` rules after `.drop__foot`, under the comment
  `/* Near the sheet's foot the list opens above its input, mirrored: row 1 nearest it, the footer on top. */`.
  Verify: `grep -n -F -e '.drop--above {' -e '.drop--above .drop__foot {' ui/src/app.css` prints a line for each.
- [x] 2.6 In `tests/e2e/test_review.py`'s `test_the_photograph_opens_in_the_viewer`, add the key
  `ui:vocabulary:the-list-opens-above-near-the-foot` and a last step: `_open` the draft, a 1280×560 viewport, `eyes` typed
  in the last `input.fragment`; `.drop` has `drop--above`, its box's bottom at most the field's top + 1 px, row 0 below row 1, `↓` selects row 1.
  Verify: `grep -n -e 'ui:vocabulary:the-list-opens-above-near-the-foot' -e 'drop--above' tests/e2e/test_review.py` prints a line for each.

## 3 — The record

- [x] 3.1 In `ui/design/spec.md`'s J4·1 block, replace the collections' lines with [the frame](design.md#frame), per
  [D6](design.md#d6).
  Verify: `grep -n -F -e 'Not included · a draft · summon-anime-wai' -e '[▒▒]×2' -e 'the rows scroll in a max height' ui/design/spec.md` prints a line for each.
