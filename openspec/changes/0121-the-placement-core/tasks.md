# The placement core — tasks

The phases: the store, the chain, the routes and the ink view, the panel, the screens, the docs. No phase is a person's, and none spends money.

## Progress

- [x] 1 — Store · moderate
- [x] 2 — Chain · hard
- [x] 3 — Preview · moderate
- [x] 4 — Panel · hard
- [x] 5 — Screens · moderate
- [x] 6 — Docs · moderate

## 1 — Store

- [x] 1.1 **HALT CHECK** 0119's extraction is built: its tests carry `ink_extract`.
  Verify: `uv run pytest tests/test_ink.py -k ink_extract` passes.
- [x] 1.2 **HALT CHECK** Pillow and numpy are declared, so the library and the chain add no dependency.
  Verify: `git grep -n "Pillow==" pyproject.toml` prints the pin.
- [x] 1.3 Add `config/tattoo.json` (`long_side`, `outline_min`, `outline_max`, `view_quality`) and `isekai/pipeline/tattoos.py` with `TATTOOS`, `TATTOO_CONFIG`, `INK_CONFIG`, `check_name`, `listed`, `named` per [D1](design.md#d1); tests in `tests/test_tattoo_library.py` carry `tattoo_names`, and `tattoo_config` reads the keys of both configs.
  Verify: `uv run pytest tests/test_tattoo_library.py -k "tattoo_names or tattoo_config"` passes.
- [x] 1.4 Extend `tattoos.py` with `save_outline`, `read_outline` and the defaults of a kind per [D4](design.md#d4): the bounds, the atomic write; tests carry `tattoo_outline`.
  Verify: `uv run pytest tests/test_tattoo_library.py -k tattoo_outline` passes.
- [x] 1.5 Extend `tattoos.py` with `keep(library, name, body)` and `design_bytes` per [D2](design.md#d2): upright, scaled to `long_side`, `design.png`, `tattoo.json` and the default outline written atomically, Pillow imported inside; tests carry `tattoo_keep`.
  Verify: `uv run pytest tests/test_tattoo_library.py -k tattoo_keep` passes.
- [x] 1.6 Extend `tattoos.py` with `cut(library, name, digest, size)` per [D3](design.md#d3), the neutral, depth and white scale from the newest cut of that digest, a tie to the later name; tests carry `tattoo_cut`.
  Verify: `uv run pytest tests/test_tattoo_library.py -k tattoo_cut` passes.
- [x] 1.7 Add `tattoos.TATTOO_CONFIG` to `ANCHORS` of `tests/test_package_paths.py` as `pytest.param(tattoos.TATTOO_CONFIG, ("config", "tattoo.json"), id="tattoos.TATTOO_CONFIG")`, importing `tattoos` from `isekai.pipeline`.
  Verify: `uv run pytest tests/test_package_paths.py -k TATTOO_CONFIG` passes.
- [x] 1.8 Add to `tests/test_ui_library.py` a test carrying `tattoo_listing`: a library holding `.tattoos/<name>/` lists no collection from it.
  Verify: `uv run pytest tests/test_ui_library.py -k tattoo_listing` passes.
- [x] 1.9 Hold that the entry point's import graph reaches no wheel and the layers hold.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.

## 2 — Chain

- [x] 2.1 **HALT CHECK** 0119's extraction takes the outline, neutral and depth this phase extends: its tests carry `ink_flags`.
  Verify: `uv run pytest tests/test_ink.py -k ink_flags` passes.
- [x] 2.2 Add to `extract_ink` in `isekai/shared/ink.py` the keyword `white: float = 1.0` per [D5](design.md#d5), a scale on the automatic per-channel point; tests in `tests/test_ink.py` carry `ink_white`.
  Verify: `uv run pytest tests/test_ink.py -k ink_white` passes.
- [x] 2.3 Add `white_grey(image, outline)` to `isekai/shared/ink.py` per [D5](design.md#d5): the automatic point's luminance as a whole number from 0 to 255; tests carry `ink_grey`.
  Verify: `uv run pytest tests/test_ink.py -k ink_grey` passes.
- [x] 2.4 Add `isekai/shared/chain.py` with `Spline` per [D6](design.md#d6): thin-plate, exact at its pairs, chunked, refusing too few pairs and pairs on a line; numpy imported inside; tests in `tests/test_chain.py` carry `chain_spline`.
  Verify: `uv run pytest tests/test_chain.py -k chain_spline` passes.
- [x] 2.5 Extend `chain.py` with `lookup`, the prototype's: the target grid backwards through each stage's spline, a bilinear sample, transparent white outside; tests carry `chain_lookup`.
  Verify: `uv run pytest tests/test_chain.py -k chain_lookup` passes.
- [x] 2.6 Extend `chain.py` with `polygon_mask`, `clip` (softened by one pixel, an exclusion removing the ink) and `multiply`; Pillow imported inside; tests carry `chain_composite`.
  Verify: `uv run pytest tests/test_chain.py -k chain_composite` passes.
- [x] 2.7 Extend `chain.py` with `crop_box(points, margin, size)`; tests carry `chain_crop`.
  Verify: `uv run pytest tests/test_chain.py -k chain_crop` passes.
- [x] 2.8 Hold that the entry point's import graph reaches no wheel and the layers hold.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.

## 3 — Preview

- [x] 3.1 Add `ink_view(library, name, photograph, digest, points, white, neutral, depth)` to `isekai/pipeline/tattoos.py` per [D7](design.md#d7): the crop, the mask, `extract_ink`, the flattened JPEG, an `InkView` returned; it refuses an open outline and a cut asked on another digest; tests carry `ink_view`.
  Verify: `uv run pytest tests/test_tattoo_library.py -k ink_view` passes.
- [x] 3.2 Add to `isekai/interface/ui/app.py` `GET /api/tattoos` (the list and the limits), `GET /api/tattoos/{name}` (`named`) and `GET /api/tattoos/{name}/design` (`design_bytes`), and to the module's route table; tests in `tests/test_ui_tattoo.py` carry `tattoo_route_read`.
  Verify: `uv run pytest tests/test_ui_tattoo.py -k tattoo_route_read` passes.
- [x] 3.3 Add `POST /api/tattoos` (a staged file per [D2](design.md#d2), refused when `importing.verify` reports metadata) and `POST /api/c/{collection}/tattoos` (a cut per [D3](design.md#d3)); tests carry `tattoo_route_keep`.
  Verify: `uv run pytest tests/test_ui_tattoo.py -k tattoo_route_keep` passes.
- [x] 3.4 Add `PUT /api/tattoos/{name}/outline` per [D4](design.md#d4); a refusal answers as every refusal does; tests carry `tattoo_route_outline`.
  Verify: `uv run pytest tests/test_ui_tattoo.py -k tattoo_route_outline` passes.
- [x] 3.5 Add `POST /api/c/{collection}/tattoos/{name}/ink` per [D7](design.md#d7), calling `ink_view`: a JPEG, `no-store`, `X-Ink-Box` and `X-Ink-White`; tests carry `ink_preview_route`.
  Verify: `uv run pytest tests/test_ui_tattoo.py -k ink_preview_route` passes.
- [x] 3.6 Hold that no route under `/api/tattoos` takes a tattoo away or changes its name, and that the guard answers each new route; tests carry `tattoo_route_guard`.
  Verify: `uv run pytest tests/test_ui_tattoo.py -k tattoo_route_guard` passes.
- [x] 3.7 Hold that `app.py` writes no file of its own.
  Verify: `uv run pytest tests/test_ui.py -k invariant` passes.
- [x] 3.8 Hold the phase's tests under the acceptance's selector.
  Verify: `uv run pytest tests/test_tattoo_library.py tests/test_chain.py tests/test_ui_tattoo.py -k "tattoo or chain or preview"` passes.

## 4 — Panel

- [x] 4.1 Add `ui/src/zoom.ts` per [D8](design.md#d8): `fitted`, `actual`, `zoomedAt`, `panned`, `toImage`, `toScreen`; its tests in `ui/src/zoom.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/zoom.test.ts` passes.
- [x] 4.2 Add `ui/src/polygon.ts` per [D8](design.md#d8): `added`, `closes`, `moved`, `inserted`, `removed`, `undone`, `box` and `ready` over an immutable state; its tests in `ui/src/polygon.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/polygon.test.ts` passes.
- [x] 4.3 Add `ui/src/tattoos.ts`: the card's state and source line, the upload's default name, `refusalField`, `controlsWait`, the white grey and scale of [D5](design.md#d5), the reset test; its tests in `ui/src/tattoos.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/tattoos.test.ts` passes.
- [x] 4.4 Add to `ui/src/types.ts` `Tattoo`, `Outline` and `InkView`, and to `ui/src/api.ts` `tattoos`, `stageFile`, `keepTattoo`, `cutTattoo`, `saveOutline`, `export function inkView` and `designAt`; `inkView` reads the headers of [D7](design.md#d7).
  Verify: `git grep -n "export function inkView" ui/src/api.ts` prints it.
- [x] 4.5 Add `ui/src/components/ImagePanel.vue` per [D8](design.md#d8): the image in a viewport, the wheel zoom, the drag pan, *Fit*, *1:1*, the zoom as a percentage, a slot for the overlay.
  Verify: `ls ui/src/components/ImagePanel.vue` prints the path.
- [x] 4.6 Declare `--outline-fill` and `--point-ring` per [D10](design.md#d10) in the Nocturne block of `ui/src/styles.css`, `:root, [data-theme="nocturne"]`, and in each Catppuccin block of `ui/src/themes.css`.
  Verify: `git grep -c -e "--outline-fill" -e "--point-ring" -- ui/src/styles.css ui/src/themes.css` prints `ui/src/styles.css:2` and `ui/src/themes.css:8`.
- [x] 4.7 Hold that each theme sets every token Nocturne does.
  Verify: `npm --prefix ui run test -- src/themes.test.ts` passes.
- [x] 4.8 Hold the browser's types.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.

## 5 — Screens

- [x] 5.1 Add `ui/src/components/TattooPicker.vue`, the first step, per its requirement: the cards, the upload through staging with its name field, *Cut from this photo*, the refusal beside the name, a click opening the outline step.
  Verify: `ls ui/src/components/TattooPicker.vue` prints the path.
- [x] 5.2 Add `ui/src/components/OutlineStep.vue`, the second step, per [D8](design.md#d8): the panel, the outline saved as it changes, the ink view, the white point, the tone, *Reset*, and on a cut the source line and *Upload a tattoo instead*.
  Verify: `ls ui/src/components/OutlineStep.vue` prints the path.
- [x] 5.3 Add `ui/src/views/Place.vue`: the render's context, the stepper of the steps built, *Back to the render*, the refusal page for an unknown render, and the step's component by the route's `step`.
  Verify: `ls ui/src/views/Place.vue` prints the path.
- [x] 5.4 Per [D9](design.md#d9) move the routes of `ui/src/router.ts` into `ui/src/routes.ts` and add the route `place` and its redirect of an unknown step; move the `key` and `HUB_SCREENS` of `ui/src/App.vue` into `ui/src/viewkey.ts`, `viewKey` stopping at `/place`, and add `offerTo`; tests in `ui/src/viewkey.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/viewkey.test.ts` passes.
- [x] 5.5 In `ui/src/views/RenderLarge.vue` declare the command `place` on `shifted('KeyP')` and add a *Place a tattoo* button in its own `.large__group`, both going to `offerTo`'s location; tests in `ui/src/offer.test.ts` read that `KeyP` is declared once and that the button's location is the first step.
  Verify: `npm --prefix ui run test -- src/offer.test.ts` passes.
- [x] 5.6 Hold that the screen and its components declare no command: a test in `ui/src/nokeys.test.ts` reads their sources for `useKeys`.
  Verify: `npm --prefix ui run test -- src/nokeys.test.ts` passes.
- [x] 5.7 Hold the browser's types.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 5.8 Hold the browser's unit tests.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 6 — Docs

- [x] 6.1 Add `### D52` to `docs/decisions.md` after D51 per [D12](design.md#d12): the tattoo library is library-wide, `.tattoos/<name>/`, its files, the cut, no deleting, the photograph never leaving the machine.
  Verify: `git grep -n "### D52" docs/decisions.md` prints its heading.
- [x] 6.2 Amend D43 in `docs/decisions.md` by one sentence: a tattoo is cleaned as a source is, and bounded.
  Verify: `git grep -n "cleaned as a source is" docs/decisions.md` prints the sentence.
- [x] 6.3 Amend D40 in `docs/decisions.md` by one sentence: `.tattoos/` is a dot-folder of the library, never a collection.
  Verify: `git grep -n "never a collection" docs/decisions.md` prints the sentence.
- [x] 6.4 In `ui/design/spec.md` add to §4's table the row for `…/<seed>/place/<step>`, the placement screen, opening over it nothing.
  Verify: `git grep -n "/place/<step>" ui/design/spec.md` prints the row.
- [x] 6.5 In `ui/design/spec.md` add `⇧P` *Place a tattoo* to §7's large-view row, and a row `**the placement core**` to §10's table.
  Verify: `git grep -n "the placement core" ui/design/spec.md` prints the row.
- [x] 6.6 In `ui/design/spec.md` add the journey `### J9 · Place a tattoo` after J8: the picker and the outline step as built, in the spec's own style, state and refusals only.
  Verify: `git grep -n "### J9" ui/design/spec.md` prints its heading.
- [x] 6.7 Add to `docs/edit-tattoo.md` the section `## The app`: `⇧P` on a render, the library, the cut, the outline and the ink view, and that the stages come later; no path of the operator's notebook.
  Verify: `git grep -n "## The app" -- docs` prints the section's heading.
- [x] 6.8 Name `tattoos.py` and `chain.py` and their edges in `docs/modules.md`, `isekai/pipeline/README.md` and `isekai/shared/README.md`.
  Verify: `git grep -n "chain.py" isekai/shared/README.md` prints the line.
