---
bump: minor
version: v0.80
after: [0119-the-tattoo-edit]
debt: [0108·R3, 0118·R3]
---

# The bakes in the app

A bake, the tattoo edit's request, is seen, quoted and run in the isekai app: on a render's large view, in the Render dialog and in the Render bar.

Reading map: [design](design.md) holds the server, the screens and the tests, [tasks](tasks.md) holds the phases: server, large view, dialog, docs.

## Why

The tattoo edit writes a **bake** — an edit request with no image yet — and `isekai render` runs it in the next session. The app counts only images, so a queued bake is invisible to it, its Render bar says nothing is short, and a session of bakes alone cannot start. A baked image has no address, and a render's large view does not show that it has bakes.

The placement screen places the tattoo and writes the request. It needs these surfaces first: where a queued bake is seen, where it is priced, and where its image is read.

## What Changes

- The quote counts bakes with images, keeps a collection that holds only bakes, and lists each bake with its photograph, version, seed and edit number.
- `POST /api/render` carries the number of bakes the dialog showed, and is refused when the quote taken again has another; a session of bakes alone starts.
- The offer counts bakes, its collection's and every other's.
- A bake has an address, `…/<seed>/edit/<k>`, and the server serves its record, its image and its thumbnail.
- A render's large view shows the photograph's thumbnail and, when the render has bakes, the chain of them, each baked row opening its bake.
- The Render bar shows with bakes alone and counts them.
- The Render dialog lists bakes under each collection, is titled for what it does, and counts bakes in its estimate.
- Each theme sets the chain's new colours.
- [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) says the confirmation carries image and bake totals.
- `ui/design/spec.md` draws the bake's route, the dialog's tiles and bakes, the large view's chain and the one-image drafting; the READMEs say it.

Requirement lines of [the `ui` delta](specs/ui/spec.md):

- MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most*: bakes in the bar, the dialog, the quote and the confirmation.
- ADDED *A render's large view shows its photograph and its bakes, and each bake has its own address*: the chain, the bake's view, its routes and their refusals.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: the Render requirement counts bakes; a new requirement holds the bake's view.

## Impact

- The server: `isekai/interface/render.py`, `isekai/interface/ui/app.py`, `isekai/interface/ui/library.py`, and `isekai/foundation/run.py` read for the edit's names. The surface's modules in `isekai/interface/ui` stay free of an edit's file stem.
- The server's tests: `tests/test_render.py`, `tests/test_ui_library.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `tests/test_ui.py`.
- The screens: `ui/src/types.ts`, `ui/src/api.ts`, `ui/src/router.ts`, `ui/src/App.vue`, `ui/src/views/RenderLarge.vue`, `ui/src/views/Hub.vue`, `ui/src/components/RenderDialog.vue`, `ui/src/components/RenderBar.vue`, `ui/src/thumbs.ts`, `ui/src/bars.ts`, `ui/src/stores/collection.ts`, and the new `ui/src/bakes.ts` and `ui/src/components/BakeChain.vue`.
- The colours and styles: `ui/src/styles.css`, `ui/src/themes.css`, `ui/src/app.css`.
- The screens' tests: `ui/src/bakes.test.ts`, `ui/src/bars.test.ts`, `ui/src/stores/collection.test.ts`, `ui/src/components/RenderDialog.test.ts`.
- The docs: `docs/decisions.md`, `ui/design/spec.md`, `isekai/interface/ui/README.md`, `README.md`.
- No run file kind moves, no verb or flag changes, and the pod receives nothing new.
- The release deletes the debt cards `0108·R3` and `0118·R3`.

## Not in this change

- The placement screen, its keys and *Place a tattoo*: when the placement screen is built.
- Placing a tattoo on a bake, and the large view's compare of a bake with the image it was placed on: when the placement screen is built.
- Deleting a bake or a kept tattoo: when it is missed.
- A tick for one bake apart from its photograph's flow: when the render verb can take a bake out alone.
- A bake's landing in the session drawer: the session's progress lines stay a render's.
- A browser test: the e2e tattoo tests, on the scenarios the person names after using the screen.
- A pod phase, and a change to `per_edit_s`: the quote shows the edit's configured figure.
