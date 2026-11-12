# The bakes in the app — tasks

The phases: the server, the large view, the dialog and the bar, the docs. The server comes first because the screens read what it serves.

## Progress

- [x] 1 — Server · hard
- [ ] 2 — Large view · moderate
- [ ] 3 — Dialog and bar · moderate
- [ ] 4 — Docs · moderate

## 1 — Server

- [x] 1.1 **HALT CHECK** The tattoo edit's names are on the base: `edits_of` in `isekai/interface/render.py`, `edit_numbers` in `isekai/foundation/run.py`, `records` in `isekai/pipeline/edit.py`.
  Verify: `git grep -n "def edits_of" -- isekai/interface/render.py` prints the definition.
- [x] 1.2 Extend `isekai/interface/render.py` per [D1](design.md#d1): `Edits.records`, `Quote.edits`, `Quote.bakes`, a collection holding a bake kept in `shorts`, `blocked` naming nothing short only without images and bakes; tests in `tests/test_render.py` carry `bake_quote`.
  Verify: `uv run pytest tests/test_render.py -k bake_quote` passes.
- [x] 1.3 Add `Bake` and `bakes(group, seed)` to `isekai/interface/ui/library.py` per [D6](design.md#d6): numbers from `edit_numbers`, a number with no record skipped, a record that cannot be read listed `damaged` with its `reason`; its docstring spells no `.edit-`; tests in `tests/test_ui_library.py` carry `bake_library`.
  Verify: `uv run pytest tests/test_ui_library.py -k bake_library` passes.
- [x] 1.4 Add to `isekai/interface/ui/app.py` the routes `…/{seed}/edit/{k}`, `…/edit/{k}/image` and `…/edit/{k}/thumb` per [D6](design.md#d6): `k` taken as text and refused unless a number the seed has an edit for, a damaged record refused on each route, naming its file, the image of a queued bake refused naming the render session; tests in `tests/test_ui_api.py` carry `bake_routes`.
  Verify: `uv run pytest tests/test_ui_api.py -k bake_routes` passes.
- [x] 1.5 Add `bakes` to `read_render`'s answer in `isekai/interface/ui/app.py`, and make `delete_render` drop each of the seed's edit images' thumbnails before `discard_render` ([D6](design.md#d6)); tests in `tests/test_ui_api.py` carry `bake_detail`.
  Verify: `uv run pytest tests/test_ui_api.py -k bake_detail` passes.
- [x] 1.6 In `isekai/interface/ui/app.py` add `bakes` and `other_bakes` to the offer of `read_render_offer`, with `idle` reading them, and pass `made.edits[<runs root>]` to `_quoted_row`, which adds each bake with its version from `edit_at` and leaves `source()` as it is ([D3](design.md#d3), [D4](design.md#d4)); tests in `tests/test_ui_api.py` carry `bake_offer`.
  Verify: `uv run pytest tests/test_ui_api.py -k bake_offer` passes.
- [x] 1.7 Make `post_render` in `isekai/interface/ui/app.py` require `bakes` and refuse another number per [D2](design.md#d2); add `bakes` to each `/api/render` body in `tests/test_ui_api.py` and `tests/test_ui_jobs.py`, and tests carrying `bake_confirm` for the refusals and a bakes-alone job.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_ui_jobs.py -k bake_confirm` passes.
- [x] 1.8 Add a test in `tests/test_ui.py` carrying `bake_names` that no module of `isekai/interface/ui` holds the spelling `.edit-`, so every edit file's name comes from `isekai/foundation/run.py`.
  Verify: `uv run pytest tests/test_ui.py -k bake_names` passes.
- [x] 1.9 In `docs/decisions.md` amend [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) per [D13](design.md#d13): the bold sentence and *Why* name image total, bake total and limit; add `0120` to *Made by*.
  Verify: `git grep -n "bake total" docs/decisions.md` prints the amended line.
- [x] 1.10 Hold the phase's tests under the acceptance's selector.
  Verify: `uv run pytest tests/test_ui.py -k "bake or edit"` passes.

## 2 — Large view

- [ ] 2.1 In `ui/src/types.ts` add `Bake`, with its `reason`, and `RenderDetail.bakes`; in `ui/src/api.ts` add `bakeAt`, `bakeThumbAt` and `bakeDetail` over the routes of [D6](design.md#d6).
  Verify: `git grep -n "bakeAt" -- ui/src/api.ts` prints the function.
- [ ] 2.2 Add `ui/src/bakes.ts` with `chainRows` and `offered` per [D7](design.md#d7), and `ui/src/bakes.test.ts` binding `ui:bakes:the-chain-lists-the-bakes-in-order` and `ui:bakes:a-bakes-view-offers-no-writes`.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [ ] 2.3 Add the route `name: 'bake'` to `ui/src/router.ts` and name it in `HUB_SCREENS` of `ui/src/App.vue` per [D5](design.md#d5).
  Verify: `git grep -n "name: 'bake'" -- ui/src/router.ts` prints the route.
- [ ] 2.4 Add `--chain-ground` and `--chain-ring` to `:root` in `ui/src/styles.css` and to each Catppuccin block of `ui/src/themes.css` per [D10](design.md#d10).
  Verify: `git grep -c "chain-ring" -- ui/src/themes.css` prints a count.
- [ ] 2.5 Add `ui/src/components/BakeChain.vue`, the chain's list drawn from `chainRows` with the shown row framed by the tokens, each baked row a `RouterLink` to the `bake` route, a queued or damaged row none, and its styles in `ui/src/app.css` framing the shown row with `--chain-ring`.
  Verify: `git grep -n "chain-ring" -- ui/src/app.css` prints the frame's rule.
- [ ] 2.6 In `ui/src/views/RenderLarge.vue` take the optional prop `k`; with it show `bakeAt`'s image, the bake's record rows and the refusal `bakeDetail` raises, and gate *Draft from this*, *Compare with…*, *Delete* and their keys on `offered` ([D8](design.md#d8)); `k` is left out of the params it passes to the `compare`, `compare-photo` and `render` routes.
  Verify: `git grep -n "offered" -- ui/src/views/RenderLarge.vue` prints the gate.
- [ ] 2.7 In `ui/src/views/RenderLarge.vue` show the photograph's thumbnail from `photoUrl` above the actions ([D9](design.md#d9)), and `BakeChain` when the render has bakes.
  Verify: `git grep -n "BakeChain" -- ui/src/views/RenderLarge.vue` prints the import.
- [ ] 2.8 Hold the unit tests, the themes' among them, with the new route and tokens.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 3 — Dialog and bar

- [ ] 3.1 In `ui/src/types.ts` give `QuotedCollection` its `bakes` and `RenderOffer` its `bakes` and `other_bakes`; in `ui/src/api.ts` give `startRender` a `bakes` parameter after `images`, sent in the body.
  Verify: `git grep -n "other_bakes" -- ui/src/types.ts` prints the key.
- [ ] 3.2 In `ui/src/stores/collection.ts` give `NO_OFFER` the keys `bakes` and `other_bakes` and let `openDialog` open on bakes alone ([D12](design.md#d12)); update the offer fixtures of `ui/src/stores/collection.test.ts`.
  Verify: `git grep -n "other_bakes" -- ui/src/stores/collection.ts` prints the key.
- [ ] 3.3 In `ui/src/thumbs.ts` add `drawnBakes` and make `allOut` and `confirmReason` count bake keys ([D11](design.md#d11)); tests in `ui/src/components/RenderDialog.test.ts` bind `ui:render:a-photograph-taken-out-takes-its-bakes` and `ui:render:nothing-left-disables-render`, and its existing rows gain `bakes`.
  Verify: `git grep -n "drawnBakes" -- ui/src/thumbs.ts` prints the function.
- [ ] 3.4 In `ui/src/bakes.ts` add `dialogTitle` ([D7](design.md#d7)); its test in `ui/src/bakes.test.ts` binds `ui:render:the-dialog-is-titled-for-what-it-does`.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [ ] 3.5 In `ui/src/bars.ts` give `BarState` its `bakes` and let `bar()` return `render` above zero; pass the offer's bakes from `ui/src/views/Hub.vue`; show them in `ui/src/components/RenderBar.vue` ([D12](design.md#d12)); tests in `ui/src/bars.test.ts` bind `ui:render:a-bar-counts-a-bake-alone` and `ui:render:prepare-takes-the-bar-first`, and its existing states gain `bakes`.
  Verify: `git grep -n "bakes" -- ui/src/bars.ts` prints the lines.
- [ ] 3.6 In `ui/src/components/RenderDialog.vue` draw the title from `dialogTitle`, a row per bake from `drawnBakes` with its `×`, the estimate's bakes and the confirm label, and send `bakes` in `startRender`; style the rows in `ui/src/app.css` with existing tokens ([D11](design.md#d11)).
  Verify: `git grep -n "dialogTitle" -- ui/src/components/RenderDialog.vue` prints the use.
- [ ] 3.7 Hold the types with the dialog and the bar.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 3.8 Hold the unit tests with the dialog and the bar.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 4 — Docs

- [ ] 4.1 In `ui/design/spec.md` §4 add the row of the bake's route, `…/<seed>/edit/:k`, the large view of a bake.
  Verify: `git grep -n 'edit/:k' -- ui/design/spec.md` prints the bake route.
- [ ] 4.2 Pay `0108·R3`: redraw J4·1 in `ui/design/spec.md` without the *Not included* lines and the sentence *What is left out is named*, with the tiles' `×`, *all removed*, the bakes' rows and the titles of [D7](design.md#d7).
  Verify: `git grep -n 'Not included' -- ui/design/spec.md` prints nothing and exits 1.
- [ ] 4.3 Pay `0118·R3`: in J5 of `ui/design/spec.md` describe the one-image drafting, dropping `Deselect those 2 and draft 1 ⇧↵` and *In a selection it is left out*; the endpoint's list stays described as the API's.
  Verify: `git grep -n -E 'Deselect those|In a selection' -- ui/design/spec.md` prints nothing and exits 1.
- [ ] 4.4 In J5 of `ui/design/spec.md` describe the large view's photograph thumbnail, the chain and a bake's view; in §10 add the row `bakes`: the bake's route, the chain, the bakes in the bar and the dialog.
  Verify: `git grep -n '| \*\*bakes\*\*' -- ui/design/spec.md` prints the row.
- [ ] 4.5 In §2 of `ui/design/spec.md` add `--chain-ground` and `--chain-ring` to the token table, each with its role.
  Verify: `git grep -n -E "^\| .*chain-ground" -- ui/design/spec.md` prints the row.
- [ ] 4.6 In `isekai/interface/ui/README.md` say the Render bullet quotes and confirms bakes beside images, and the large view bullet the chain and a bake's routes; in `README.md` say the same in the paragraph on Render and the large view.
  Verify: `git grep -n "bakes" -- isekai/interface/ui/README.md README.md` prints the lines.
