# Design — 0078 the third walkthrough

Each finding of the third pass, its fix, its keys and its layout. **Verdict: feasible** — every fix is a layout,
a key declaration, a payload field or a dialog element over code that already holds what it shows.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `7300efc` (`v0.50.0`):

- **The hub's row:** the source cell is a column — stem, `file · dims`, thumbnail (`ui/src/views/Hub.vue:458–485`;
  `.hub__source`, `ui/src/app.css:1666`); a flow cell is its tick line, then `.hub__images` (`Hub.vue:499–546`;
  `.hub__cell` `align-content: flex-start`, `app.css:1649`); `↵ view photo` joins the column on focus (`Hub.vue:473`).
  `read_hub` serves each source's `width` and `height` (`isekai/interface/ui/app.py:317`); the viewer's title reads
  `name · W×H` (`ui/src/components/ImageViewer.vue:58–65`).
- **Renders' source cell:** `.renders__name` beside the thumbnail (`ui/src/views/Renders.vue:271`), in a `250px` column
  (`:251`).
- **The Library's row:** `ROW_THUMBS = 7` (`isekai/interface/ui/library.py:95`, used at `:768`); `Home.vue:150–160`
  draws the thumbnails, then `+n`.
- **Review's keys:** `↵` opens the photograph only on its pane (`id: 'photo'`, `ui/src/views/Review.vue:483–487`);
  `⇧C` *Side by side* `when` a revision (`:489–494`); `⇧F` the next flow (`:445–449`, `nextFlow` `:73`); `⌃E` `⌃Y` are
  real `Ctrl` (`:472`, `:478`). `paneKeys` declares macOS's `⌃H` `⌃L` `inField` (`ui/src/panes.ts`). A tag field's
  `↓` `↑` step the suggestions while open, else `emit('row')` (`ui/src/components/TagInput.vue:61–72`).
- **The key list:** `?` is `shifted('Slash')`, not `inField` (`ui/src/App.vue:98`); the app bar's button
  (`App.vue:163`); `KeyList.vue` closes on `Escape` and `?` (`ui/src/components/KeyList.vue:14`).
- **A revision's payload:** `read_input` computes `revision` in the draft branch only (`app.py:663`, `:671–677`);
  `Review.vue:53–54` drops it when read-only. `came_from` reads an approval as a draft (`isekai/pipeline/review.py:880`).
- **Revise:** `post_revise` (`app.py:846`) answers every image's refusal from `refuse_revisions`
  (`review.py:289`), which refuses a waiting draft through `refuse_revision` (`:326`) and `current_draft` (`:103`);
  `ReviseConfirm.vue` shows them.
- **The Review tab:** `ReviewHead.vue` replaces itself with `head` (`ui/src/composables/useQueue.ts:50`); `waiting`
  (`:35`) feeds the rail's head (`ui/src/components/BatchRail.vue:47`).
- **The large view:** `e` `f` `c` `⇧C` `esc` (`ui/src/views/RenderLarge.vue:117–140`); *Compare…* opens the viewer over
  `choices` (`picking`, `:33–34`; `others`, `:52`; `choices`, `:57`); `.large__actions` (`:189`; `app.css:633–637`) in
  a 360 px aside (`.large__sheet`, `app.css:610–618`), below the fields. Renders revises with `e` (`Renders.vue:185`).
- **The dialogs:** `RenderDialog.vue`, `ReviseConfirm.vue` and `ImportSheet.vue` are `div.scrim`s
  (`ui/src/components/ImportSheet.vue:278`); the viewer is a modal `<dialog>` (`showModal`, `ImageViewer.vue:111`).
  The key store's overlay masks the screen's commands (`ui/src/stores/keys.ts:148–156`), not the browser's focus.
- **The unit tests run in `node`** (`ui/vitest.config.ts:9`): a browser's layout and focus are e2e's alone.

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_api.py` | 71 | `grep -c "def test_" tests/test_ui_api.py` |
| tests in `tests/test_ui_library.py` | 21 | `grep -c "def test_" tests/test_ui_library.py` |
| vitest tests | 38 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -cE "^(spec\|test\|it)\("` |
| e2e tests | 30 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** every settled finding of the pass but the session drawer and conjure without Prepare. **Non-Goals:** a
change to the review stage or the CLI; the session pages; a sweep of every refusal's wording.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **the hub's row:** `.hub__source` and `.hub__cell` are columns whose picture — `.hub__thumb`, `.hub__images` — takes `margin-top: auto`; `.hub__refusal` stands above `.hub__images`; `.hub__source` is `position: relative` and `↵ view photo` sits absolutely at its top right; `.hub__file` is deleted, the stem alone stays; `read_hub` keeps `width` and `height` | the row's pictures share a foot whatever the text above; the viewer names the size | the size on the row |
| [D2](#d2) | **Renders' source cell:** the thumbnail alone, its `aria-label` the name; `.renders__name` and its rule deleted; the column `calc(var(--tile-width) + 20px)` | the viewer names the photograph | |
| [D3](#d3) | **the Library's row:** `ROW_THUMBS = 15` | the row has the room | fitted to the width |
| [D4](#d4) | **`⌃P` on Review:** `{ code: 'KeyP', ctrl: true }`, `inField`, on every platform, `preventDefault`; on a draft the photograph's viewer, `← →` the rail's; on a revision *Side by side*, where `⌃P` toggles the pair and the photograph alone; `Esc` back to the focus left, a field included; Review's `photo` (`↵`) and `side-by-side` (`⇧C`) commands deleted; the click on the photograph and the *Side by side* button stay; the large view's `⇧C` stays | one key from any pane and a field | `⌃O` for the pair |
| [D5](#d5) | **`⌃J` `⌃K`:** `paneKeys` gains `field-down` and `field-up` on macOS alone, `inField`, which do in a tag field what `↓` `↑` do — step the open suggestions, else `emit('row')`; drawn in the key list beside `⌃H` `⌃L` | vim's rows from a field | a Linux pair: `Ctrl+K` is `Mod+K`, `Ctrl+J` the browser's |
| [D6](#d6) | **`⌃/`:** the key list's command is `{ code: 'Slash', ctrl: true }`, `inField`, everywhere; `?` (`shifted('Slash')`) deleted from `App.vue` and from `KeyList.vue`'s close keys, which gain `⌃/`; the app bar's button stays, its hint `⌃/` | reachable from a field | keeping `?` |
| [D7](#d7) | **an approved revision:** `read_input` computes `revision` for the approval it shows as for a draft; `Review.vue` keeps it when read-only: the image beside the photograph, the `was` marks, `⌃P`; the approve bar's *Discard draft* on a draft only | the comparison matters after approve | only until its own render exists |
| [D8](#d8) | **Revise on a waiting draft:** `post_revise` answers an image whose flow holds a waiting draft (`current_draft`) with `waiting: <draft>` and writes nothing for it; from the large view `ReviseConfirm` opens Review on that flow's draft without asking; over a selection the confirm leaves such images out, naming them `already waiting`, and revises the rest; no message on Review; the review stage's refusal and the CLI's are unchanged | the draft is the work in hand; a page has no terminal | a refusal; a line on Review |
| [D9](#d9) | **the flow chooser:** `useQueue` gains `flowsWaiting(info) -> {flow, approve, short, sources}[]`; `ReviewHead.vue` replaces itself with the one flow's `head` when one flow waits, and draws the chooser when two or more do — a row per flow, its name, its counts, up to fifteen waiting photographs at the hub's tile size, then `+n`; `j` `k` `↓` `↑` move rows, `↵` or a row click opens its head, a photograph's click that sheet; the focused row is kept across a return; Review's `Esc`, with no overlay and outside a field, opens the chooser; `next-flow` (`⇧F`) and `nextFlow` deleted; the rail's head names the other flows with `⇧R` | the operator chooses the flow | `⇧F` kept |
| [D10](#d10) | **writes shifted:** the large view's `revise` takes `shifted('KeyE')` and `draft-from` `shifted('KeyF')`; Renders' `revise` `shifted('KeyE')`; `c` and `⇧C` stay | a shifted letter is not pressed in passing | `e` alone |
| [D11](#d11) | ***Compare with…*** `c`: `cells.ts` gains `pick(images, version, seed, compare) -> {at: number} \| {compare: image}` — one other image compares at once, else the pick starts where the viewer starts today; the pick is a modal dialog headed *Compare vN · seed S with…*, the cell's other images as tiles at Renders' size, `vN · seed` under each, oldest first; `h j k l` and the arrows move, `↵` or a click compares, `Esc` back; the viewer loses its `action` mode | a choice reads as one | a *Compare with this* button in the viewer |
| [D12](#d12) | **the button column:** `.large__actions` is a column of full-width buttons, label left, key right, in groups 12 px apart — *Revise this image*, *Conjure from this*; *Compare with…*, *Side by side*; *Back to …* — placed under the heading, above the fields; the large view alone | five buttons need ~640 px; the fields pushed them past the fold | one row |
| [D13](#d13) | **modal dialogs:** `RenderDialog`, `ReviseConfirm` and `ImportSheet` render a `<dialog>` opened by `showModal`, as `ImageViewer` is; each restores the focus it found on close; first focus — Render: *Keep the volume open*, where `Space` toggles and `↵` does nothing; Revise: its confirm button; import: its first control; `Esc` cancels through the key store, as today | the keys reach what is shown | the Render dialog alone |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `ui:revise:an-approved-revision-keeps-its-image`; `ui:revise:a-waiting-draft-is-opened` | `test_a_row_names_its_first_seven_sources_in_the_hubs_order` — seventeen sources, fifteen named | `tests/test_ui_api.py`, `tests/test_ui_library.py` |
| unit · vitest | `ui:keys:the-key-list-opens-from-a-field`; `ui:keys:review-fields-move-from-a-field-on-macos`; `ui:review:two-flows-waiting-open-the-chooser`; `ui:compare:one-other-image-is-compared-at-once` | `ui:review:a-batch-opens-its-head` — one flow | `ui/src/stores/keys.test.ts`, `ui/src/composables/useQueue.test.ts`, `ui/src/cells.test.ts` |
| e2e | `ui:review:the-chooser-opens-a-flow`; `ui:dialogs:the-render-dialog-opens-on-its-checkbox` | `test_the_source_cell_opens_its_photograph` — the feet level; `test_the_photograph_opens_in_the_viewer` — `⌃P` from a field; `test_side_by_side_shows_the_pair` — `⌃P` twice; `test_revise_opens_review_on_the_revision` — `⇧E`, the render kept after approve; `test_conjure_from_this_opens_review` — `⇧F`; `test_compare_shows_both_versions_of_a_seed_and_the_field_that_changed` — the tile pick; the routes test — `.hub__name` for `.hub__file` | `tests/e2e/conftest.py`, `tests/e2e/test_review.py`, `tests/e2e/test_render.py`, `tests/e2e/test_routes.py` |

**End-to-end runs added:** two, on Chromium only (T4) — a chooser's keys and a dialog's focus are a browser's (T1).
No test reaches two flows waiting in one batch, so the chooser takes a batch of its own in `tests/e2e/conftest.py`
(T2, T3); the Render test confirms and leaves for the session page, so the dialog's focus takes its own test on the
same batch, cancelled (T3).

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** `⌃P` is Print in Linux browsers and `⌃/` nothing there → the page takes `⌃P` by `preventDefault`, as it
  does `⌃H` `⌃L`; checked by hand on Linux, the e2e running on Chromium.
- **[Risk]** a modal `<dialog>` closes on `Esc` itself → each closes through its `close` event, as `ImageViewer`
  does (`ImageViewer.vue:92`, `:126`), so the store's `Esc` and the browser's end in one place.
- **[Trade-off]** `⇧F` gone → another flow is two keys away, `⇧R` then a row.

## Verdict

**Feasible.** Each fix lands on code that already holds what it shows.
