---
bump: minor
version: 0.81
after: [0119-the-tattoo-edit]
beside: [0120-the-bakes-in-the-app]
---

# The placement core

The app keeps tattoos library-wide and opens the placement screen's first steps: pick, upload or cut a tattoo, outline it, and see its ink.

Reading map: [design](design.md) holds the library, the chain module, the ink view and the panel, [tasks](tasks.md) its phases.

## Why

A tattoo is placed on a render by clicks, and a prototype proved the clicks faster and better than Krita. The whole screen is too large for one review, so it is built in parts.

This part is what the stages stand on: a place to keep a tattoo, the maths that warps its ink, a panel that zooms and takes clicks, and the picker and the outline step. Nothing here spends money or touches a pod.

## What Changes

- New requirement, *A tattoo is kept in the library, whole and never deleted*: `~/isekai/.tattoos/<name>/`, upright, at most the declared long side, a name once.
- New requirement, *A tattoo is cut from a photograph*: no image, the photograph's digest, the newest cut's tone.
- New requirement, *An outline and its ink tone are kept with the tattoo*: points, closed, white, neutral, depth, saved as it changes.
- New requirement, *The white point is a scale on the automatic point*: `white` on `extract_ink`, the automatic point read as an 8-bit grey.
- New requirement, *Ink is placed by thin-plate splines*: the chain module over arrays, fitted backwards, clipped, multiplied.
- New requirement, *The ink view is made on the server*: one `POST`, a JPEG on a crop, never stored.
- New requirement, *The large view offers Place a tattoo*: a button and `⇧P` on a render.
- New requirement, *The placement screen has a route of its own per step*: the steps do not remount it.
- New requirement, *The screen holds no key of its own*: the app-wide keys stay.
- New requirement, *The panel zooms at the pointer, pans by a drag, and fits or shows 1:1*.
- New requirement, *An outline is clicked, closed on its first point and edited by dragging*.
- New requirement, *The picker lists the kept tattoos and takes an upload or a cut*.
- New requirement, *The outline step shows the ink and keeps its white point and tone*.
- Each new colour is a token in each theme; the decisions D52 (new), D43 and D40 (amended) and the design spec's routes, keys and journey are edited where they live.

## Capabilities

### New Capabilities

- `tattoo`: the library, the cut, the outline and its tone, the white point, the chain and the ink view.

### Modified Capabilities

- `ui`: the large view's *Place a tattoo*, the screen's routes and keys, the panel, the outline, the picker and the outline step. Added requirements only; none of the existing ones changes.

## Impact

- New: `config/tattoo.json`, `isekai/pipeline/tattoos.py`, `isekai/shared/chain.py`, `ui/src/zoom.ts`, `ui/src/polygon.ts`, `ui/src/tattoos.ts`, `ui/src/routes.ts`, `ui/src/viewkey.ts`, `ui/src/components/ImagePanel.vue`, `ui/src/components/TattooPicker.vue`, `ui/src/components/OutlineStep.vue`, `ui/src/views/Place.vue`, and a test beside each.
- Changed: `isekai/shared/ink.py`, `isekai/interface/ui/app.py`, `ui/src/api.ts`, `ui/src/types.ts`, `ui/src/router.ts`, `ui/src/App.vue`, `ui/src/views/RenderLarge.vue`, `ui/src/styles.css`, `ui/src/themes.css`.
- Tests: `tests/test_tattoo_library.py`, `tests/test_chain.py`, `tests/test_ui_tattoo.py`, `tests/test_ink.py`, `tests/test_ui_library.py`, `tests/test_package_paths.py`.
- Docs: `docs/decisions.md`, `docs/edit-tattoo.md`, `docs/modules.md`, `ui/design/spec.md`, `isekai/shared/README.md`, `isekai/pipeline/README.md`.
- No dependency, no flow, no pinned digest and no end-to-end test changes.

## Not in this change

- The stages that click pairs, the live warp preview over them, the limb and exclusion outlines, the review, the bake's request and the Leave dialog: when the stages' own screens are built.
- The *not on this photo* mode and a tattoo's *ready for this photo* state: when a stage's pairs are kept.
- The render's scale in the cut's source line: when the stage on the render needs the render's size.
- A bake's large view offering *Place a tattoo*, and a chain of tattoos: when a bake can be placed on.
- Keys on the placement screen, a minimap, *follow* and exposure: when the screen has been used and shows which are useful.
- Deleting or renaming a kept tattoo: when one is missed.
- Browser tests: when the scenarios the person names after using the screen exist.
- A CLI verb over the chain: when one is asked for; the module is shared so it can come.
- Automatic outlines, white points and pairs: when automatic placement is built.
