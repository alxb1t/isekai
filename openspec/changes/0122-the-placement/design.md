# The placement — design

The placement screen gains its stages: pairs that carry a tattoo's ink onto the photograph and the render, a live preview, a limb and exclusions, a review, and a bake that queues an edit request. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The core (0121) keeps tattoos in the library, outlines them and shows their ink; the tattoo edit (0119) bakes a composite into a render. This change joins them: clicks give the composite, and the composite goes to the edit stage as a request.

```
① tattoo ─ ② outline + ink ─┬─ ③ tattoo ↔ photograph ─ ④ photograph ↔ render ─┐
   (upload)                 ├─ ③ tattoo ↔ render (not on this photo) ─────────┼─ ⑤ review ─ Bake
   (cut)                    └─ ④ photograph ↔ render (a cut: no stage 1) ─────┘     │
                                                                                     ▼
  POST …/preview ─▶ JPEG, ink on white, on a crop        edit_request: <seed>.edit-<k>.composite.png
  (every pair change, 1 s)                                              <seed>.edit-<k>.json
                                                                        <seed>.edit-<k>.placement.json
```

The build runs stacked on the core's, which runs on the tattoo edit's. It uses `isekai/shared/chain.py`, `isekai/pipeline/tattoos.py`, the panel and the picker of the core, and `request` of `isekai/pipeline/edit.py`. The bakes version, which shares files with this one and nothing else, builds the bake's own large view, the chain listing and the Render dialog's bakes.

## Goals / Non-Goals

- **Goals:** the stage-1 pairs kept per photograph; the preview; the composite and the placement record through the edit stage; a bake placed on a render or a baked edit; the pairs editor, the stages ③ and ④, the direct stage, the limb and exclusions, the review and the Leave dialog; the decisions and the docs.
- **Non-Goals:** keys, a minimap, the tint view, automatic placement, the bake's large view and the chain listing, *Place a tattoo* on a baked image, keeping stage-2 pairs across a leave, deleting, browser tests, a pod. See the proposal's *Not in this change*.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | stage-1 pairs are kept in a file per photograph under the tattoo, saved as the page sends them | stage 1 depends on the tattoo and the photograph, not the render | pairs in the edit only; a file a render |
| [D2](#d2) | the mode is read from the tattoo, and the floors and limits live in `config/tattoo.json` | the page and the server read one source | floors in both |
| [D3](#d3) | the ink's layer is made on the outline's crop, and the pairs' source side is shifted by its origin | the crop keeps a preview about a second | a full-size layer |
| [D4](#d4) | the preview is one sync `POST` returning the ink on white as a JPEG over a crop of the target | the page multiplies it, as the bake does | an alpha PNG; a preview file |
| [D5](#d5) | a bake is the composite over the whole render, written by the edit stage with a placement record | the edit stage owns a request's files | `app.py` writing the files |
| [D6](#d6) | a bake is placed on a render or on a baked edit, and each is a new edit | an edit's record is its own history | re-baking in place |
| [D7](#d7) | stage-1 pairs are saved as they change; stage-2 pairs, limb and exclusions are held by the page until the bake | the brief names no other file | a draft file the brief does not settle |
| [D8](#d8) | the pairs, preview, steps, outlines, review and leave logic are plain TypeScript under vitest; the components draw | the component cannot run in node | logic inside components |
| [D9](#d9) | the steps are `tattoo`, `outline`, `photo`, `render` and `review`, and a mode redirects a step it skips | the numbers name one screen in every mode | a step a mode |
| [D10](#d10) | each new colour is a token in each theme | D48 | a colour in a component |
| [D11](#d11) | tests sit at the lowest layer; no end-to-end test | the standards' lowest-layer rule | a browser test for a click |
| [D12](#d12) | D53 is new and the repository's [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) is amended where they live | the decisions page says what holds | prose only in `design.md` |

### D1

- `isekai/pipeline/tattoos.py` gains `read_stage1(library, name, digest)`, `save_stage1(library, name, digest, pairs, not_on_photo)` and `stage1_states(library, digest)`. The file is `.tattoos/<name>/stage1/<digest>.json`, holding `pairs` and `not_on_photo`.
- A pair is `[[ax, ay], [bx, by]]`, the tattoo's point first. `digest` is the twelve-character run digest the URLs carry, and a digest that is no plain name is refused as a tattoo's name is.
- `save_stage1` refuses a coordinate that is not a finite non-negative number, a tattoo-side point outside `size` of the tattoo's record, and a cut, whose ink is already in the photograph's pixels. It replaces the file atomically.
- `read_stage1` of a photograph with no file returns no pairs and the flag off, and writes nothing. `stage1_states` returns, per tattoo with a file, `{pairs, not_on_photo}`.
- `GET` and `PUT /api/tattoos/<name>/stage1/<digest>` read and save it. `GET /api/tattoos?digest=<digest>` adds `stage1`, the states, to the list.
- The flag keeps the pairs: `PUT` sends both, and the page keeps the pairs it read when it sends only the flag.

### D2

- `mode_of(kind, not_on_photo)` returns `cut`, `direct` or `two-stage`: a cut is a cut, an upload with the flag is direct, else two-stage.
- `config/tattoo.json` gains `floor_stage1` 6, `floor_stage2` 8, `floor_direct` 6, `preview_floor` 3, `preview_margin` 96, `preview_wait_ms` 1000, `pair_radius` 8 and `region_min` 3. `GET /api/tattoos` carries them with the core's limits.
- The pairs of a stage are `a` and `b`: stage 1 is tattoo and photograph, stage 2 is photograph and render, the direct stage is tattoo and render.

### D3

- `tattoos.ink_layer(library, name, photograph, digest, points, white, neutral, depth)` is the extraction the core's `ink_view` makes from the outline values it is given, returning the RGBA layer and its **origin**, the crop's corner in the tattoo's or the photograph's pixels. `ink_view` passes the values the page sent and flattens what it returns; `preview` and `composite` pass the saved outline, read by `read_outline`.
- `isekai/shared/chain.py` gains `place(ink, origin, stages, box, limb=None, exclusions=())`. Each stage is `(target_side, source_side)` points, the stage nearest the target first. It fits a `Spline` per stage from the target side to the source side, shifts the last source side by `origin`, runs `lookup` over `box`, and applies `polygon_mask` and `clip` for the limb and each exclusion. It returns a float RGBA array over `box`, transparent white where nothing lands.
- `chain.flatten(layer)` returns the layer on white as 8-bit RGB. `box` is `(x, y, width, height)` in the target's pixels.

### D4

- `POST /api/c/<collection>/tattoos/<name>/preview` takes `{target, digest, flow, version, seed, edit, pairs, limb, exclusions}`. `target` is `photo` for stage 1 and `render` for every other stage. A pair with a missing side is lone and refused, naming its number.
- `tattoos.preview(library, name, photograph, digest, target_path, target, pairs, limb, exclusions)` returns `Preview(jpeg, box, white)`. It reads the mode, refuses what the spec's requirement says, and calls `ink_layer`, `place` and `flatten`.
- The crop is `crop_box` of the target-side points and the limb, grown by `preview_margin`, clipped to the target's size. A render stage reads the stage-1 file for a two-stage tattoo, and refuses fewer pairs than `floor_stage1`.
- The answer is `Response(bytes, image/jpeg, no-store)` with `X-Preview-Box: x,y,w,h` and `X-Ink-White`, after the ink view's precedent. `photograph` is the run's photograph and `target_path` the render's image, from `rendered(...)` as the `/image` route has it, or the image of edit `edit`, `edit_files(group, seed, edit)[0]` of that image's group.
- A cut asked on a digest it is not cut from is refused. Nothing is written.

### D5

- `tattoos.composite(library, name, photograph, digest, render, pairs, limb, exclusions)` returns `Composite(png, values)`: the render with the layer multiplied on, over the whole render's grid, as PNG bytes; and `values`, every field of the placement but `places_on` and the schema, which `request_placed` adds.
- `isekai/pipeline/edit.py` gains `request_placed(edit, source, composite, placement, *, overrides, seed, rng)`. It shares its body with `request`, which keeps its signature, takes the composite as bytes, and writes the composite, then the placement record, then the edit's record last.
- `isekai/foundation/artifacts.py` gains `PLACEMENT_FILE` and `PlacementRecord`; `isekai/foundation/run.py` gains `placement_file(group, seed, number)`, `<seed>.edit-<k>.placement.json`.
- The record holds `tattoo`, `kind`, `cut_from`, `mode`, `places_on`, `outline` (`points`, `white`, `neutral`, `depth`), `stage1`, `pairs`, `limb` and `exclusions`. `stage1` is a copy of the pairs the bake used, or none; the copy keeps the record whole when the tattoo's pairs change later.
- `POST /api/c/<collection>/tattoos/<name>/bake` takes `{digest, flow, version, seed, edit, pairs, limb, exclusions}` and answers `{edit: <k>}`. `app.py` calls `composite` and `request_placed` and writes nothing.
- The photograph is read to extract a cut's ink and is never written into the run.

### D6

- `edit` in the preview and bake bodies is the number of a baked edit to place on, or none for the render. The image is `<seed>.edit-<k>.png` beside the render's.
- `request_placed` refuses an edit image that is not on disk, saying that edit waits for its render session. The edit's own chaining gives the next free number, so a second bake on one image is a new edit.
- `places_on` is the number of the edit placed on, none for the render. No earlier record is read for writing.
- The screen offers placing on a render's own image only, as the core does. Placing on a baked image's large view waits for that view: the bakes version builds it and this one shares files with it.

### D7

- `usePlacing(place)` in `ui/src/composables/usePlacing.ts` holds the screen's tattoo, the stage-1 pairs it read, the stage-2 or direct pairs, the limb and the exclusions. `Place.vue` creates it and provides it to the steps, so a step change keeps it.
- A change to the stage-1 pairs sends `PUT` with the complete pairs at once; a lone point is not sent. The stage-2 and direct pairs, the limb and the exclusions are held until the bake writes them into the placement.
- Leaving the screen, or reloading it, loses the held work; stage 1 and the outline stay. The risks name it.

### D8

- `ui/src/pairs.ts` holds the pair editor over an immutable state with its history: `clicked`, `moved`, `deleted`, `undone`, `cleared`, `selected`, `lone` and `forward`. The selection radius is `pair_radius` screen pixels divided by the scale.
- `ui/src/preview.ts` holds the ask's schedule and the answers: `due`, `asked`, `answered`, `dimmed`, `refused`, and `previewable`. The newest ask's answer alone is kept.
- `ui/src/stages.ts` holds `modeOf`, `stepsOf`, `forwardOf`, `startStep` and `skipped`. `ui/src/outlines.ts` holds the limb and the exclusions over `polygon.ts`: `begun`, `closed`, `rows` and `held`.
- `ui/src/review.ts` holds `summary` and `bakeState`; `ui/src/leave.ts` holds `lone`, `asks` and `left`.
- The components `PairPanel`, `PairList`, `StagePhoto`, `StageRender`, `ReviewBake` and `LeaveDialog` draw from these and declare no command.
- `PairPanel` draws the point markers over `ImagePanel` and the preview over the target with `mix-blend-mode: multiply`, at the operator's opacity, with a hide control. The selected pair and the waiting image take `--accent`.

### D9

- `ui/src/routes.ts` holds the step set `tattoo|outline|photo|render|review`. `stages.ts`'s `skipped(mode, step)` names the step a mode takes in its place: `photo` for a cut or a direct tattoo goes to `render`; `review` before the stages' floors goes to the earliest step short of its floor. `Place.vue` replaces the route with that step once the tattoo is read, since the mode is read data and a route cannot know it.
- `startStep` is the step a card opens: `outline` until outlined, then `photo` for a two-stage tattoo with fewer than `floor_stage1` pairs, else `render`.
- The stepper lists `stepsOf(mode)`: a number names one screen in every mode, so a step a mode skips is absent, not renumbered.

### D10

- `--limb-fill` and `--exclusion-fill` are tokens, in the Nocturne block of `ui/src/styles.css` and in each Catppuccin block of `ui/src/themes.css`. The limb's stroke is `--accent-ink`, the exclusion's is dashed in the same colour.
- The point rings and the waiting edge are the core's `--point-ring` and `--accent`.

### D11

See [Tests](#tests). Every new test carries its `spec` marker.

### D12

- `docs/decisions.md` gets D53, a placement is recorded beside its edit: the placement record, the held stage state, and that stage-1 pairs are the tattoo's. The repository's [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) gains the edit request among the writes that go through the function that owns them.
- `ui/design/spec.md` gets the steps in §4, the version in §10 and the journey J9 extended; `docs/edit-tattoo.md` gets the placement record in its app section.

## Tests

Tests sit at the lowest layer that can fail: arrays for the chain, the store over a temporary library, the edit stage over a temporary run, the routes over the test client, and the editor, the preview's schedule, the steps and the summary as plain TypeScript. No test boots a browser, and the end-to-end suite gains none: `git diff --name-only main -- tests/e2e` prints nothing at the release.

| file | layer | holds |
|---|---|---|
| `tests/test_tattoo_placement.py` | unit | the stage-1 file and states, the preview, the composite |
| `tests/test_chain.py` | unit | `place` and `flatten` |
| `tests/test_edit_placement.py` | unit | the placement record, `request_placed`, the chain, the listings, the discards |
| `tests/test_ui_placement.py` | unit | the stage-1, preview and bake routes, the guard, the invariant |
| `tests/test_tattoo_library.py` | unit | the new config keys |
| `tests/test_ui_tattoo.py` | unit | the list route's limits |
| `tests/test_run_view.py` | unit | a placement record is no unread file |
| `ui/src/pairs.test.ts`, `ui/src/preview.test.ts` | unit | the editor and the preview's schedule |
| `ui/src/stages.test.ts`, `ui/src/outlines.test.ts` | unit | the modes' steps and forward, the limb and exclusions |
| `ui/src/review.test.ts`, `ui/src/leave.test.ts` | unit | the summary and the bake's state, the Leave dialog |
| `ui/src/composables/usePlacing.test.ts` | unit | the pairs stay across steps |
| `ui/src/tattoos.test.ts`, `ui/src/viewkey.test.ts` | unit | the picker's states, the route's steps |
| `ui/src/nokeys.test.ts`, `ui/src/themes.test.ts` | unit | no command in the new components, each token in each theme |

No test is deleted or merged, so no table of removals is owed. Counts are read from the release's `tests-unit` metric, `scripts/metrics/tests_collected.py`.

## Dependencies

None.

## Risks / Trade-offs

- **The held stage-2 work is lost on a leave or a reload.** Stage 1 and the outline are saved; the clicks of stage 2, the limb and the exclusions wait for the bake. A draft record is for a later version, when losing them is missed.
- **A bake over the whole render costs seconds.** Each stage's spline over a render's grid is slow; the preview stays on a crop.
- **The core's `lookup`, `Spline` and `ink_view` are not built at the cut.** The first task checks them and halts the plan when they are missing.
- **The edit stage's request is not built at the cut.** The bake's phase checks `request` and `edit_files` and halts the plan when they are missing.
- **The bake's large view and the chain's listing are not here.** Until the bakes version is in the default branch with this one, a baked image is placed on only by a request; the screen offers the render.
- **The preview's crop is the points' box and a margin.** A tattoo whose ink reaches far beyond its pairs shows cut off in the preview, and whole in the bake.

## Verdict

Ready to build. Each phase ends green, and nothing here spends money or needs a pod.
