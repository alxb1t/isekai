# The placement core — design

The app keeps tattoos in the library and shows the placement screen's first steps: the picker and the outline with its ink. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The tattoo edit (0119) bakes a tattoo into a render from a composite made by hand. This change starts the app's way to that composite: clicks, not Krita. The whole screen is too large for one review, so it is built in parts, and this part holds what the rest stand on.

```
render's large view ─ ⇧P ─▶ ① picker ─▶ ② outline + ink          (this change)
                              │              │
   ~/isekai/.tattoos/<name>/ ◀┘              └─ POST …/ink ─▶ JPEG on the outline's crop
        design.png · tattoo.json · outline.json

                              ③ ④ ⑤ stages, preview, bake        (not here)
```

The prototypes proved the chain and the extraction: a thin-plate spline in numpy, a Pillow polygon, a Multiply; the extraction's white point read per channel. The build runs stacked on 0119's, which adds `extract_ink` in `isekai/shared/ink.py` and `config/ink.json`.

## Goals / Non-Goals

- **Goals:** the tattoo library and its cut; an outline kept with its tone; `white` on `extract_ink`; the chain module; the ink view's `POST`; the panel's geometry under vitest and its component; the picker and the outline step; the route and *Place a tattoo*; tokens; the decisions and the docs.
- **Non-Goals:** the stages and the live warp preview, the limb and exclusions, review and the bake, the Leave dialog, *not on this photo*, keys, a minimap, deleting, browser tests, any CLI verb, automatic placement, a pod. See the proposal's *Not in this change*.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | a tattoo is a folder of `.tattoos/` in the library, written by `isekai/pipeline/tattoos.py`; no delete, no rename | one tattoo is an input for many renders in many collections | a folder in each collection; `.data/` |
| [D2](#d2) | an upload goes through the import's staging and is kept upright as `design.png`, at most the declared long side | staging already cleans, verifies and bounds a file | a second reader for tattoos |
| [D3](#d3) | a cut is a tattoo with no image: its record names the photograph's digest | the ink is already in the photograph's pixels | copying the photograph |
| [D4](#d4) | the outline and its tone are one file, saved as the page sends it, bounded by `config/tattoo.json` | saving happens as you go | a save button; bounds in the page and the server apart |
| [D5](#d5) | `white` is a scale on the automatic per-channel point; the page shows the point as one grey | the prototype's point is a vector, the design's control one number | a single number replacing the vector |
| [D6](#d6) | the chain is `isekai/shared/chain.py` over arrays, with numpy and Pillow inside the functions | one tested implementation, no wheel on the entry point's import graph | scipy; the warp in the browser |
| [D7](#d7) | the ink view is one sync `POST` returning a JPEG on the outline's crop, `no-store`, headers for the box and the white | a staged file's preview is already made this way; a full grid is slow | a stored preview file; a websocket |
| [D8](#d8) | the panel's geometry is plain TypeScript in `zoom.ts` and `polygon.ts` under vitest; the component only draws | the component cannot run in node; no browser test here | geometry inside the component |
| [D9](#d9) | the screen is the route `…/place/<step>/<name?>`, its view key stops at `/place`, and it declares no key | steps must not remount it; keys wait for use | a nested router view; keys now |
| [D10](#d10) | each new colour is a token in each theme | D48 | a colour in a component |
| [D11](#d11) | tests sit at the lowest layer; no end-to-end test | the standards' lowest-layer rule | a browser test for a click |
| [D12](#d12) | D52 is new; D43 and D40 are amended where they live | the decisions page says what holds | prose only in `design.md` |

### D1

- `isekai/pipeline/tattoos.py` holds `TATTOOS` (`.tattoos`), `TATTOO_CONFIG`, `INK_CONFIG`, `check_name`, `listed`, `named`, `design_bytes`, `save_outline`, `read_outline`, `keep`, `cut` and `ink_view`. Pillow is imported inside the functions that decode.
- `check_name(name)` refuses a name that is not a folder name; `named(library, name)` returns the tattoo's record or refuses an unknown name; `design_bytes(library, name)` returns `design.png`'s bytes and refuses a cut. A pipeline module imports no other, so `tattoos.py` takes bytes and paths from `app.py`.
- The layout, per tattoo:

```
~/isekai/.tattoos/<name>/
  design.png      the image, upright, no metadata; absent for a cut
  tattoo.json     name, kind (image | cut), size, downscaled_from, cut_from, kept (time)
  outline.json    points, closed, white, neutral, depth
```

- `size` is the image's, or the photograph's for a cut. `keep` and `cut` each write `outline.json` with the defaults of [D4](#d4) and no points, so a tattoo always has one.

- A name is refused when empty, dot-leading, holding `/`, `\` or NUL, or taken; the refusal names the fix, `<name> is kept; choose another name`.
- The library's `listed` already skips dot-folders, so no collection is listed from `.tattoos/` ([D40](../../../docs/decisions.md#d40--a-collection-is-a-library-folder-holding-sources)). A test holds it.
- `app.py` calls the module and writes no file itself; the invariant of `tests/test_ui.py` over the surface, which refuses `write(` there, holds it.

### D2

- The page stages a file through `POST /api/staging` and `PUT /api/staging/<id>/files/<name>`, as the import does. `POST /api/tattoos` then names the staging id, the staged name and the tattoo's name.
- The server takes the staged file, refuses one `importing.verify` says still carries metadata, and calls `keep(library, name, body)` with its bytes. The staging is cancelled after.
- `keep` turns the pixels upright, scales a long side past `long_side` down with a high-quality filter, holds the aspect, and writes `design.png` atomically. `tattoo.json` holds `size`, and `downscaled_from` when it scaled.
- A non-image is refused at staging, by the import's own read.

### D3

- `POST /api/c/<collection>/tattoos` takes `{name, digest, flow}`, finds that run's photograph as `…/review/<digest>/<flow>/photo` does, reads its size, and calls `cut(library, name, digest, size)`.
- `cut` writes `tattoo.json` with kind `cut`, `cut_from` the twelve-character run digest the URLs carry and `size` the photograph's, and an `outline.json` with no points.
- The tone, neutral, depth and the white scale, starts from the newest cut of the same digest, the later `kept` time and on a tie the later name; with none, neutral on, `photo_depth` of `config/ink.json` and white 1.0. An uploaded tattoo starts neutral off and `image_depth`.
- A cut has no `design.png`: `GET /api/tattoos/<name>/design` refuses it, saying it is cut from a photograph.
- The page lists every cut; a cut of another photograph cannot be chosen on this render.

### D4

- `outline.json` holds `points` (pairs of numbers in the image's pixels, the photograph's for a cut), `closed`, `white` (a scale, 1.0 automatic), `neutral` and `depth`.
- `config/tattoo.json` holds `long_side` 4096, `outline_min` 20, `outline_max` 120 and `view_quality` 90. `GET /api/tattoos` carries the limits, so the page and the server read one source.
- `tattoos.py` reads `photo_depth`, `image_depth`, `depth_min`, `depth_max` and `reach` from `config/ink.json` through `INK_CONFIG`, as `importing.upload_limit` reads `config/ui.json`.
- `outline.json`'s defaults come from one function of the kind, so `keep`, `cut` and a read of a tattoo with no file agree.
- `PUT /api/tattoos/<name>/outline` replaces the file, atomically. It refuses a point outside the image, more than `outline_max` points, a closed outline under `outline_min`, a depth outside `depth_min`–`depth_max` of `config/ink.json`, and a white scale of zero or less or past 255. An open outline may hold any number of points up to the ceiling.
- A tattoo is **outlined** when its outline is closed.

### D5

- `extract_ink` gains a keyword `white: float = 1.0`, a scale. The automatic point, read per channel at the percentile `white` of 0119's `config/ink.json`, is multiplied by it before the division. That config key stays the percentile; the keyword is the scale. 1.0 is the extraction as 0119 built it.
- `isekai/shared/ink.py` also holds `white_grey(image, outline)`: the automatic point's luminance, weighted 0.299, 0.587 and 0.114 as the extraction's neutral is, times 255, rounded to a whole number from 0 to 255. The outline is a mask, as 0119's `isekai ink` takes it.
- The page keeps the scale. It shows the automatic grey, or the grey of a hand setting; a grey `g` against an automatic `a` is stored as `g / a`, and a scale `s` is shown as `round(a * s)`.
- No CLI flag is added: `isekai ink` is as 0119 built it.

### D6

- `isekai/shared/chain.py` holds `Spline`, `lookup`, `polygon_mask`, `clip`, `multiply` and `crop_box`, each over arrays.
- `Spline(source, target, smooth=0.0)` solves the thin-plate system with `np.linalg.solve`, kernel r²·log r², and refuses fewer pairs than `MIN_PAIRS`, the least the system solves, naming it. It refuses pairs that lie on one line, whose system does not solve, as it refuses too few. A call is chunked so a large grid does not hold the whole kernel.
- `lookup` is the prototype's, from `prototype/placement/chain.py` at `a6005952` on its branch: the target crop's grid goes backwards through each stage's spline, then a bilinear sample of the ink; outside the ink it is transparent white.
- `polygon_mask(points, size)` fills a Pillow polygon into an `L` mask. `clip` blurs it by one pixel and multiplies the ink's alpha; an exclusion polygon sets the alpha to 0 inside it.
- `multiply(render, layer)` is `render * (1 - alpha + alpha * layer)`.
- `crop_box(points, margin, size)` is the points' box grown by `margin` and clipped to `size`. It serves the ink view now and the stages' previews later.
- A preview holds about a second only on a crop; a full grid over a large photograph takes seconds. So every caller crops.

### D7

- `POST /api/c/<collection>/tattoos/<name>/ink` takes `{points, white, neutral, depth}`, and for a cut also `digest` and `flow`, the run whose photograph it is asked on. The route is `Response(bytes, image/jpeg, no-store)` after `read_staged_thumb`'s precedent.
- `ink_view(library, name, photograph, digest, points, white, neutral, depth)` returns `InkView(jpeg, box, white)`. `app.py` passes `photograph`, the run's photograph path, and `digest` for a cut, and `None` for both for an upload; `ink_view` refuses a cut whose `cut_from` is not `digest`.
- `ink_view` does the work and `app.py` only calls it: the crop is `crop_box` of the outline with the extraction's `reach` as margin; the image is read once and cut, the outline is made a mask by `polygon_mask` in the crop's pixels, `extract_ink` runs, and the layer is flattened on white and written as a JPEG at `view_quality`. It returns the bytes, the box and the automatic grey.
- Headers: `X-Ink-Box: x,y,w,h` in the image's pixels, and `X-Ink-White: <0-255>`. The page reads them with `fetch`.
- It refuses an open outline, an unknown tattoo and a cut whose `cut_from` is not the `digest` asked, each a `Refusal`. The Host and Origin middleware answers it as every route.
- For a cut the image is the run's photograph; for an upload, `design.png`. Nothing is written.
- The warp's preview over pairs is the stages' and is not made here: it has no reader before ③.

### D8

- `ui/src/zoom.ts` holds the view: `fitted`, `actual`, `zoomedAt`, `panned`, `toImage`, `toScreen`. The scale is held between 0.25 and 16; a pan keeps part of the image in the viewport.
- `ui/src/polygon.ts` holds the outline: `added`, `closes`, `moved`, `inserted`, `removed`, `undone`, `box` and `ready`, over an immutable state with its history. The closing radius is in screen pixels and is divided by the scale.
- `ui/src/tattoos.ts` holds what the picker and the step read: the card's state and source line, the upload's default name, where a refusal is shown (`refusalField`: beside the name when it asks for another name, else on the file), why the controls wait (`controlsWait`: *outline open* until the outline is closed), the white grey ↔ scale, the reset test.
- `ImagePanel.vue` draws the image, a slot for the overlay, the zoom as a percentage, *Fit* and *1:1*. A press that moves under a few pixels is a click; one that moves more is a pan; a press on a vertex is a drag of it.
- The mouse set: click adds; the first vertex closes; a drag moves; shift-click inserts on an edge; a double click removes; *Undo* and *Clear* are buttons. No key is read.

### D9

- The route is `place`, path `/c/:collection/renders/:digest/:flow/:version/:seed/place/:step/:name?`, steps `tattoo` and `outline`, the step param held to those by `:step(tattoo|outline)`; a second route `…/place/:other(.*)*` redirects any other step to `tattoo` of the same render. The routes are in `ui/src/routes.ts`, which `router.ts` builds its router from, so a test makes a router on a memory history; `router.ts` alone reads `window`.
- `App.vue`'s view key is `route.path`; `ui/src/viewkey.ts` holds `viewKey`, which for the route `place` gives the path up to `/place`, so a step or name change does not mount the screen again, and `HUB_SCREENS`, which gains `place` so the Hub stays lit.
- `viewkey.ts` also holds `offerTo(place)`, the route location of the first step, which the button and the command both go to. `RenderLarge.vue` gains the `place` command on `⇧P` and a *Place a tattoo* button in its own `.large__group`.
- `Place.vue` and its components call no `useKeys`. The app-wide keys stay; a native dialog closes on `esc`.
- The stepper lists ① tattoo and ② outline; a later step is added where it is built. ② has no forward action in this change: its outline and ink are saved as they are made.
- A tattoo is placed on a render's own image only. A bake's large view is not offered the command here.

### D10

- The new colours are tokens: `--outline-fill`, the translucent fill of an outline, and `--point-ring`, the ring and tag of a vertex. The outline's stroke is `--accent-ink`, the waiting edge `--accent`.
- Each is declared in the Nocturne block of `ui/src/styles.css`, `:root, [data-theme="nocturne"]`, and in each Catppuccin block of `ui/src/themes.css`, in `#rrggbb` or `#rrggbbaa`. The existing `themes.test.ts` holds that each flavour sets every token Nocturne does and no theme value is `rgba(`.

### D11

See [Tests](#tests). Every new test carries its `spec` marker.

### D12

- `docs/decisions.md` gets D52, the tattoo library is library-wide, its layout and rules. D43 says a tattoo is cleaned as a source is and bounded; D40 names `.tattoos/` among the library's dot-folders.
- `ui/design/spec.md` gets the route in §4, `⇧P` in §7's large-view row, the version in §10 and the journey J9 as built here. `docs/edit-tattoo.md` gets its app section.

## Tests

Tests sit at the lowest layer that can fail: arrays for the chain and the extraction, the store over a temporary library, the routes over the test client, the panel's geometry as plain TypeScript. No test boots a browser, and the end-to-end suite gains none: `git diff --name-only main -- tests/e2e` prints nothing at the release.

| file | layer | holds |
|---|---|---|
| `tests/test_tattoo_library.py` | unit | the store: names, keep, downscale, cut and its tone, the outline's bounds and defaults |
| `tests/test_chain.py` | unit | the spline, the lookup, the clip, the Multiply, the crop box |
| `tests/test_ink.py` | unit | `white` and `white_grey` on `extract_ink` |
| `tests/test_ui_tattoo.py` | unit | the routes: list, upload from staging, cut, outline, the ink view, the guard, no delete |
| `tests/test_ui_library.py` | unit | `.tattoos/` lists no collection |
| `tests/test_package_paths.py` | unit | `TATTOO_CONFIG` resolves inside the repository |
| `ui/src/zoom.test.ts`, `ui/src/polygon.test.ts` | unit | the panel's and the outline's geometry |
| `ui/src/tattoos.test.ts` | unit | the card's state, the default name, the white conversion, reset |
| `ui/src/viewkey.test.ts` | unit | the route, the view key, the Hub stays lit |
| `ui/src/offer.test.ts` | unit | `⇧P` declared once on the large view |
| `ui/src/nokeys.test.ts` | unit | no command on the screen or its components |
| `ui/src/themes.test.ts` | unit | already holds each new token in each theme |

No test is deleted or merged, so no table of removals is owed. Counts are read from the release's `tests-unit` metric, `scripts/metrics/tests_collected.py`.

## Dependencies

None.

## Risks / Trade-offs

- **The chain has no caller but its tests until the stages are built.** It is held by arrays, so a fault shows at the stages' first run; the module is small and the prototype's.
- **0119's `extract_ink` is not built at the cut.** The build runs stacked on it; the first phase of the chain checks the symbol and halts the plan when it is missing.
- **The crop changes the automatic white point.** It is read inside the outline, so a crop of the outline's box and the reach does not move it; a photograph whose bright skin lies far outside the box could.
- **A cut's white point is one number for a bent limb.** The edge shading is the extraction's fault, recorded in 0119, not this screen's.
- **The mouse set is the cut's.** Delete and insert are a double click and a shift-click until the screen shows which keys are useful.
- **A phase of components has no browser test.** The geometry carries the logic under vitest; `vue-tsc` holds the types; the person's use of the screen is the rest.

## Verdict

Ready to build. Each phase ends green, and nothing here spends money or needs a pod.
