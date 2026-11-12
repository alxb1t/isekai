# The outline gestures — tasks

The press rule, the placing rule and the redo first; the keys, the words and the ask second. Each task names its files; the rules are in [design](design.md).

## Progress

- [x] 1 — The gestures · hard
- [ ] 2 — The keys and words · moderate

## 1 — The gestures

- [x] 1.1 **HALT CHECK** `ui/src/components/ImagePanel.vue` still holds the press rule [D1](design.md#d1) rewrites: `SLOP`, `grab` and `Press.shift`. A panel that no longer has them means the plan reads stale code.
  Verify: `git grep -q "SLOP" -- ui/src/components/ImagePanel.vue` exits 0.
- [x] 1.2 Add `ui/src/press.ts` with `gestureOf` and `cursorOf` per [D1](design.md#d1) and [D2](design.md#d2), and `ui/src/press.test.ts` bound to `ui:panel:shift-places-and-a-plain-press-pans` and `ui:panel:the-cursor-follows-shift-and-the-pan`.
  Verify: `grep -rq "cursorOf" ui/src` exits 0.
- [x] 1.3 In `ui/src/polygon.ts` add `future` to `Draft` and `redone`, per [D5](design.md#d5): `changed` clears it, `undone` fills it, `blank` and `drafted` start it empty, a drag's later moves keep it. Test it in `ui/src/polygon.test.ts` as `ui:outline-edit:redo-restores-what-undo-took`.
  Verify: `git grep -q "redone" -- ui/src/polygon.ts` exits 0.
- [x] 1.4 In `ui/src/polygon.ts` add `canClose` and `placed` per the table of [D3](design.md#d3). Test them in `ui/src/polygon.test.ts` as `ui:outline-edit:a-shift-click-places-by-where-it-lands`, `ui:outline-edit:a-near-miss-never-adds-a-vertex` and `ui:outline-edit:closing-needs-the-floor`; the near miss is an outline below the floor and another at it, a few image pixels off the first vertex.
  Verify: `git grep -q "canClose" -- ui/src/polygon.ts` exits 0.
- [x] 1.5 In `ui/src/pairs.ts` add `future` to `Pairs`, `redone` and `touched` per [D4](design.md#d4) and [D5](design.md#d5); `arrived` joins the arrival to every snapshot of `future` too. Test them in `ui/src/pairs.test.ts` as `ui:pairs:a-plain-click-selects-and-places-nothing` and `ui:pairs:redo-restores-what-undo-took`.
  Verify: `git grep -q "touched" -- ui/src/pairs.ts` exits 0.
- [x] 1.6 Rewrite the test in `ui/src/nokeys.test.ts` as `ui:place-keys:the-screen-declares-only-undo-redo-and-close` ([D6](design.md#d6)), before the panel listens: `useKeys` only in the outline step and the stages that hold pairs, only the ids `undo`, `redo` and `close`, `keydown` and `keyup` only in `ImagePanel.vue`, and `useKeyStore` and `.declare(` in none.
  Verify: `git grep -q "the-screen-declares-only-undo-redo-and-close" -- ui/src/nokeys.test.ts` exits 0.
- [x] 1.7 In `ui/src/components/ImagePanel.vue` read each press with `gestureOf`: `grab` is asked only with Shift up, a `place` press that travels past `SLOP` is dropped, `Press.shift` is the Shift held at the press, and `dblclick` carries it. Draw `cursorOf`'s cursor from a class on `.panel__viewport`, kept by `keydown` and `keyup` of Shift on `window`, `shiftKey` on each pointer move and `blur`, and map the classes in `ui/src/app.css` to `cursor: crosshair`, `grab` and `grabbing`, replacing the fixed `cursor: grab` of `.panel__viewport`.
  Verify: `git grep -q "cursor: crosshair" -- ui/src/app.css` exits 0.
- [x] 1.8 In `ui/src/components/OutlineStep.vue` make `clicked` call `placed` for a press with `shift` and return for one without, and make `doubled` act only without `shift`. In `ui/src/components/StageRender.vue` make `sketched` do the same, importing `placed as placedDraft` because the file's pair `placed` function holds the name, and drop its own `closes` and `vertexAt` branches and every import they leave unused, in both files.
  Verify: `git grep -q "placed(" -- ui/src/components/OutlineStep.vue` exits 0.
- [x] 1.9 In `ui/src/components/StagePhoto.vue` and `ui/src/components/StageRender.vue` make the pair editor's `placed` call `clicked` for a press with `shift` and `touched` for one without.
  Verify: `git grep -q "touched(" -- ui/src/components/StagePhoto.vue` exits 0.

## 2 — The keys and words

- [ ] 2.1 Add `ui/src/placeKeys.ts` with `placeCommands({ undo, redo, close })` per [D6](design.md#d6), and `ui/src/placeKeys.test.ts` bound to `ui:place-keys:undo-redo-and-close-run-from-the-keys` and `ui:place-keys:the-keys-are-listed-with-the-apps`, built on `useKeyStore` as `ui/src/stores/keys.test.ts` builds it.
  Verify: `grep -rq "placeCommands" ui/src` exits 0.
- [ ] 2.2 Call `useKeys('screen', placeCommands(…))` in `ui/src/components/OutlineStep.vue` (its draft, `close` through `canClose`), `ui/src/components/StagePhoto.vue` (its pairs, no `close`) and `ui/src/components/StageRender.vue` (the sketch while one is drawn, else its pairs; `close` closes the sketch), per [D6](design.md#d6).
  Verify: `git grep -q "placeCommands" -- ui/src/components/StageRender.vue` exits 0.
- [ ] 2.3 Delete the hint lines: the gesture `<p class="outline__hint mono">` of `ui/src/components/OutlineStep.vue`, whose text begins `click adds` (keep the crop line's), the `data-outline-hint` note of `ui/src/components/StageRender.vue`, and the empty-list note of `ui/src/components/PairList.vue` with its `.pairlist__note` rule in `ui/src/app.css`.
  Verify: `git grep -L "click adds" -- ui/src/components/OutlineStep.vue` prints `ui/src/components/OutlineStep.vue`.
- [ ] 2.4 Add `closeLine` to `ui/src/tattoos.ts` per [D7](design.md#d7) and test it in `ui/src/tattoos.test.ts` as `ui:outline-step:one-line-says-how-to-close`. In `ui/src/components/OutlineStep.vue` draw it above the ink view's heading and stop drawing `wait` in the ink view, the white point (keep *reading the ink*) and the tone; leave `controlsWait` as the predicate.
  Verify: `git grep -q "closeLine" -- ui/src/tattoos.ts` exits 0.
- [ ] 2.5 Per [D8](design.md#d8) make `ui/src/components/ImagePanel.vue` emit `hover`, and `ui/src/components/OutlineStep.vue` draw the first vertex larger with the text *close* while `closes` holds at the pointer.
  Verify: `git grep -q "hover" -- ui/src/components/OutlineStep.vue` exits 0.
- [ ] 2.6 Per [D9](design.md#d9) set `proposalAsked` to `noAsks` in the replacing branch of `load` in `ui/src/composables/usePlacing.ts`, and reverse the kept-ask assertions of `ui:proposal:a-stage-with-no-pairs-asks-once` in `ui/src/composables/usePlacing.test.ts`. Add `ui:proposal:returning-to-a-tattoo-asks-again` there: answered, another tattoo, back, due, and an answer still on its way is not applied.
  Verify: `git grep -q "returning-to-a-tattoo-asks-again" -- ui/src/composables/usePlacing.test.ts` exits 0.
- [ ] 2.7 In `docs/edit-tattoo.md` say in *The outline* and *The stages* bullets that Shift places and the plain mouse pans, and name `⌘Z`, `⇧⌘Z` (Ctrl off a Mac) and `↵`.
  Verify: `git grep -q "⇧⌘Z" -- docs/edit-tattoo.md` exits 0.
- [ ] 2.8 In `ui/design/spec.md` change the J9·3 frame to "the ink view, the white point and the tone disabled, the line `close the outline on its first point · 0 points` above them", the J9·4 trigger to "shift-click the first point again", the J9·10 frame without its `click on the render adds a point` hint, and *The panel* bullet to: Shift places, a plain drag pans or moves, a double click removes, `⌘Z` `⇧⌘Z` `↵` are read. Make the Placement row of §7 Keys read `⌘Z ⇧⌘Z undo and redo · ↵ closes the outline · the everywhere keys stay`.
  Verify: `git grep -q "shift-click the first point again" -- ui/design/spec.md` exits 0.
