# Tattoo fixes — tasks

The phases: the picker, the steps, the review and the soft edge. Each ends on a green gate, built in this order.

## Progress

- [x] 1 — The picker · moderate
- [x] 2 — The steps · hard
- [x] 3 — The review · moderate
- [ ] 4 — The soft edge · hard

## 1 — The picker

- [x] 1.1 **HALT CHECK** The render's `Delete` is the one user of `DeleteDialog.vue`, so one edit of `ui/src/views/RenderLarge.vue` swaps it for the shared dialog.
  Verify: `git grep -l -w DeleteDialog -- ui/src` prints `ui/src/views/RenderLarge.vue`.
- [x] 1.2 Add `ui/src/confirm.ts` exporting `deletion` and `removal(name)`, each a `{ title, name }` object per [D1](design.md#d1), and `ui/src/confirm.test.ts` with one `spec('ui:picker:remove-asks-in-a-dialog', …)` on both.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [x] 1.3 Write `ui/src/components/ConfirmDialog.vue` from the body of `DeleteDialog.vue` per [D1](design.md#d1): props `title`, `name`, `marker`, `run`; emits `close` and `done`; the `data-<marker>-…` attributes.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.4 In `ui/src/views/RenderLarge.vue` use `ConfirmDialog` with `marker="delete"`, `deletion` and `run` calling `deleteRender(place)`; delete `ui/src/components/DeleteDialog.vue`.
  Verify: `git grep -n "ConfirmDialog" -- ui/src/views/RenderLarge.vue` prints the import and the tag.
- [x] 1.5 In `ui/src/components/TattooPicker.vue` delete the arm, its blur handler and the card's refusal line; *Remove* sets the tattoo to ask about and a `ConfirmDialog` with `marker="remove"` and `removal` runs `removeTattoo`, then emits `removed`.
  Verify: `git grep -n -E "disarm|data-remove-refusal" -- ui/src/components/TattooPicker.vue` prints nothing.
- [x] 1.6 Delete `armRemoval` from `ui/src/tattoos.ts`, its test `ui:picker:remove-takes-a-second-click` from `ui/src/tattoos.test.ts` and the rule `.picker__remove[data-armed='true']` from `ui/src/app.css`.
  Verify: `git grep -n -E "armRemoval|armed='true'" -- ui/src` prints nothing.
- [x] 1.7 In `ui/src/nokeys.test.ts` import `ConfirmDialog.vue?raw` and assert it holds one `useKeys('overlay'` and no `keydown`, beside the screen's own read.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [x] 1.8 In `ui/src/views/Place.vue` delete the head's `<img class="place__render">` and the `thumbAt` import, and `.place__render` from `ui/src/app.css` per [D4](design.md#d4).
  Verify: `git grep -n "place__render" -- ui/src` prints nothing.
- [x] 1.9 In `ui/src/views/Place.vue` pass `:version` and `:seed` to `TattooPicker`; in the picker add the props and, above `.picker__make`, a `data-picker-images` row of two `<figure class="picker__shown">`: the render (`imageAt`, left) and the photograph (`photoUrl`, right), each with a `<figcaption>`, per [D2](design.md#d2).
  Verify: `git grep -n "data-picker-images" -- ui/src/components/TattooPicker.vue` prints one line.
- [x] 1.10 In `ui/src/app.css` add `.picker__images`, a grid of equal columns with a gap of 16px, and `.picker__shown img` at `width: 100%` and `height: auto`, after the `.picker` rule.
  Verify: `git grep -n "^\.picker__images" -- ui/src/app.css` prints one line.
- [x] 1.11 Add `FRAME` and `thumbCrop(points, size, frame)` to `ui/src/tattoos.ts` per [D3](design.md#d3), and a test `ui:picker:a-cuts-card-shows-its-own-crop` in `ui/src/tattoos.test.ts` on the example of [D3](design.md#d3), on no point and on a lone point, the last two giving `null`.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [x] 1.12 Add `ui/src/components/CutImage.vue` per [D3](design.md#d3): props `place` and `tattoo`; it reads the outline with `tattooNamed`, draws `thumbCrop` over `photoUrl`, and once closed shows `inkView`'s image, revoking its URL on unmount.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.13 In `ui/src/components/TattooPicker.vue` show `CutImage` for a cut's card in place of its `<img>`, and make `src` the upload's design alone.
  Verify: `git grep -n "CutImage" -- ui/src/components/TattooPicker.vue` prints the import and the tag.
- [x] 1.14 In `ui/design/spec.md` edit frame J9·1 to say the render and its photograph stand above the forms, the card bullet to say a cut shows its own crop, and the *Remove* bullet to the dialog of [D1](design.md#d1).
  Verify: `git grep -n "above the forms" -- ui/design/spec.md` prints one line.
- [x] 1.15 In `docs/edit-tattoo.md` change `*Remove* asks a second click` to `*Remove* asks in a dialog`.
  Verify: `git grep -n "asks a second click" -- docs/edit-tattoo.md` prints nothing.

## 2 — The steps

- [x] 2.1 **HALT CHECK** Leaving step ② reloads the tattoo without waiting, a read that [D7](design.md#d7) replaces by the save's own answer.
  Verify: `git grep -n "void placing.reload()" -- ui/src/views/Place.vue` prints one line.
- [x] 2.2 Add `withOutline(tattoo, outline)` to `ui/src/tattoos.ts` per [D5](design.md#d5), and a test `ui:outline-step:the-head-reads-the-saves-answer` in `ui/src/tattoos.test.ts` on a closed save and then an open one.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [x] 2.3 In `ui/src/composables/usePlacing.ts` add `track(work)`, which counts the work in flight and counts it down in a `finally`; add `adopt(name, outline)`, which sets the held tattoo's `outline` and `outlined` only when it is `name`; return `reading`, true while tracked work runs; run `load` through `track` and delete `reload`. Extend `ui/src/composables/usePlacing.test.ts` with a test bound to `ui:proposal:an-ask-waits-for-the-saved-outline` on a pending tracked save, an adopted outline and an adopt of another name.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [x] 2.4 In `ui/src/components/OutlineStep.vue` add an `inject(PLACING)`; in `flush` call `placing.track` at once on the promise it queues, and in that step, on `saveOutline`'s answer, set the head's tattoo with `withOutline` and call `placing.adopt(props.name, saved)` per [D7](design.md#d7).
  Verify: `git grep -n "withOutline" -- ui/src/components/OutlineStep.vue` prints the import and the call.
- [x] 2.5 In `ui/src/views/Place.vue` delete the `placing.reload()` line and the `before` argument of the watcher that held it, `before?.[0]`, and fix that watcher's comment to say the tattoo is read once.
  Verify: `git grep -n -F "before?" -- ui/src/views/Place.vue` prints nothing.
- [x] 2.6 In `ui/src/app.css` add `.pair > .panel { flex: 1; }` after the `.pair` rule, per [D6](design.md#d6).
  Verify: `git grep -n "^\.pair > \.panel" -- ui/src/app.css` prints one line.
- [x] 2.7 In `ui/src/propose.ts` make `due(mode, pairs, asks, key, points, reading)` false while `reading` or with no `points`, a count of the points to send; make the `refused` variant of `Ask` carry no words, `refused(asks, key)` take none and `view` return `Could not propose pairs — place them by clicking`. Update every `due` and `refused` call of `ui/src/propose.test.ts` and `ui/src/composables/usePlacing.test.ts`, re-key the refusal test to `ui:proposal:a-refusal-says-so-in-a-plain-line-and-the-clicks-still-work`, and add to `ui/src/propose.test.ts` a test bound to `ui:proposal:an-ask-waits-for-the-saved-outline` on `reading` and no points.
  Verify: `uv run python -m tools.test_ui` exits 0, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 2.8 In `ui/src/components/StageRender.vue` pass `due` the count of `pointsOf`'s points, 0 while `tattoo` is null, and `placing.reading.value`, and call `refused` without the error's message.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 2.9 In `ui/design/spec.md` edit frame J9·14 and the proposed-pairs bullet: the ask waits for the saved outline, and a refusal reads `Could not propose pairs — place them by clicking`.
  Verify: `git grep -n "Could not propose pairs" -- ui/design/spec.md` prints one line.
- [x] 2.10 In `docs/edit-tattoo.md` end the proposed-pairs bullet's last sentence `which the refusal names when they are absent` with `which the server's refusal names when they are absent; the page shows a plain line`.
  Verify: `git grep -n "the page shows a plain line" -- docs/edit-tattoo.md` prints one line.

## 3 — The review

- [x] 3.1 Add `fitted(box, size)` to `ui/src/review.ts` per [D8](design.md#d8), and a test `ui:review:the-crops-are-fitted-to-their-columns` in `ui/src/review.test.ts` on the box 100 by 50 at 250, 275 over 1100 by 600, and on a box as wide as the render, which places at `0%`.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [x] 3.2 In `ui/src/components/ReviewBake.vue` delete `ZOOM` and `over`, build the crop's style from `fitted` and the render's `backgroundImage`, and fix the head comment to say the crops are fitted.
  Verify: `git grep -n -w ZOOM -- ui/src/components/ReviewBake.vue` prints nothing.
- [x] 3.3 In the template of `ui/src/components/ReviewBake.vue` delete the whole render and its ink, give the step's root `class="stage"` alone, and replace the `stage__forward` block by `<div class="review__actions">`: the bake's state line, then one `outline__row` of the back buttons and *Bake*.
  Verify: `git grep -n -E "review__image|review__render|stage review" -- ui/src/components/ReviewBake.vue` prints nothing.
- [x] 3.4 In `ui/src/app.css` delete `.review__image` and `.review__render`, make `.review__crops` a grid of equal columns and `.review__pixels` `width: 100%`, and add `.review__actions`: a flex column with a gap of 8px and `margin-top: auto`.
  Verify: `git grep -n -E "^\.review__(image|render)" -- ui/src/app.css` prints nothing.
- [x] 3.5 In `ui/design/spec.md` edit frame J9·12: the crops `before` and `after` side by side, the summary beside them, `Back to …` and *Bake* in one row.
  Verify: `git grep -n "in one row" -- ui/design/spec.md` prints one line.

## 4 — The soft edge

- [ ] 4.1 In `isekai/shared/chain.py` add `SUPERSAMPLE = 4` and make `polygon_mask` fill at that factor, each point at `4x + 1.5`, and reduce with a box filter, per [D9](design.md#d9); fix its docstring.
  Verify: `git grep -n -w SUPERSAMPLE -- isekai/shared/chain.py` prints the constant and its uses.
- [ ] 4.2 In `isekai/shared/chain.py` make `clip` multiply the opacity by `1.0 - mask / 255.0` for each exclusion, keep the limb's blur, and fix its docstring.
  Verify: `git grep -n -F "1.0 - mask" -- isekai/shared/chain.py` prints one line.
- [ ] 4.3 In `tests/test_chain.py` add `test_chain_composite_a_polygon_mask_is_antialiased_at_its_edge` and `test_chain_composite_an_exclusions_edge_is_partly_removed`, each bound to its key of the `tattoo` delta.
  Verify: `uv run pytest tests/test_chain.py -k "antialiased or partly_removed"` exits 0.
- [ ] 4.4 In `tests/test_tattoo_placement.py` add `test_placement_preview_ink_layer_has_a_soft_edge`: the alpha channel of `ink_layer` over `_around(34, 24)` holds values between none and full, bound to `tattoo:chain:a-polygon-mask-is-antialiased`.
  Verify: `uv run pytest tests/test_tattoo_placement.py -k soft_edge` exits 0.
- [ ] 4.5 The far edge of a polygon moves half a pixel in ([D9](design.md#d9)): in `tests/test_chain.py` move the probe `layer[18, 18, 3]` of `test_chain_place_clips_to_the_limb_and_removes_each_exclusion` to `layer[16, 16, 3]`, and in `tests/test_tattoo_placement.py` the probe `_at(shown, kept, 240, 170)` of `test_placement_preview_the_limb_keeps_the_ink_and_an_exclusion_removes_it` to `243, 170`.
  Verify: `git grep -n -F "layer[16, 16, 3]" -- tests/test_chain.py` prints one line.
- [ ] 4.6 **HALT CHECK** The soft edge turns no other existing test red: the interior pixels the tests read are unchanged.
  Verify: `uv run pytest tests/test_chain.py tests/test_ink.py tests/test_tattoo_placement.py tests/test_tattoo_library.py` exits 0.
- [ ] 4.7 In `isekai/shared/README.md` change the `chain.py` row's `the polygon mask` to `the antialiased polygon mask`.
  Verify: `git grep -n "the antialiased polygon mask" -- isekai/shared/README.md` prints one line.
