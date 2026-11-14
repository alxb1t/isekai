# Tattoo fixes — design

The decisions behind the fixes the person's acceptance test of *Place a tattoo* found. Verdict: ready to build, in the
phases of [tasks](tasks.md).

## Context

*Place a tattoo* shipped as the placement screen of `ui/src/views/Place.vue`, its steps built on `PairPanel`,
`ImagePanel` and the shared `usePlacing` state. The person placed a tattoo end to end and found the fixes below.

The render's deletion already asks in a modal, `DeleteDialog.vue`, and the app's dialogs share the `render-dialog`
frame. The ink's mask is `polygon_mask` in `isekai/shared/chain.py`, a hard polygon that the preview and the bake both
sample bilinear, about 1.6 times larger on a render.

## Goals / Non-Goals

Goals:

- Each finding fixed where it lives, with the unit test the node-only vitest run can hold.
- One confirmation dialog for the render's deletion and a tattoo's removal.
- A soft ink edge in the preview and the bake alike.

Non-goals:

- A brush eraser, and the stray pair a later press placed.
- A server route or a format version: every fix reads what the routes already answer.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One shared confirmation dialog serves *Delete this render?* and *Remove this tattoo?*; *Remove* opens it and the arm goes | the lit button read as a stuck state; a second dialog would drift | a second dialog beside the first; keeping the arm |
| [D2](#d2) | The picker shows the render left and its photograph right at its top, each fitted to half the width | the operator places a tattoo between them and saw neither | thumbnails in the head; a photograph in each card |
| [D3](#d3) | A cut's card shows its own crop: the outline's box, as the ink view once outlined | cuts of one photograph read alike | the whole photograph; a server route for the crop |
| [D4](#d4) | The head loses the render's thumbnail, on every step | the person asked; no requirement or test names it | keeping it on some steps |
| [D5](#d5) | Step ②'s head takes the outline save's answer | the head read the tattoo once, on mount | reading the tattoo again after each save |
| [D6](#d6) | The panels of a pair editor grow to the page's height | most of step ④'s page sat empty | a taller `min-height` |
| [D7](#d7) | An ask for pairs waits for the saved outline and asks nothing with no point; a refusal is one plain line | a fresh cut's ask sent the old, empty outline and showed the request's words | awaiting the read in `Place.vue`; retrying a refused ask |
| [D8](#d8) | The review shows *before* and *after* side by side, fitted, with no render above; the summary and one row of buttons stand to the right | stacked crops at full size are never seen together | keeping the render; a zoom of 2 |
| [D9](#d9) | A polygon mask is filled at `SUPERSAMPLE` times its size and box-reduced; the exclusions multiply by it, the limb keeps its blur | the hard edge, enlarged onto the render, reads as a saw-tooth | a wider blur; a hard exclusion edge |
| [D10](#d10) | A minor, cut on its own, beside no version | the baked image changes for the same inputs, and the picker shows the photograph | a patch |

### D1

**One dialog.** `ui/src/components/ConfirmDialog.vue` is `DeleteDialog.vue`'s body made general: it takes `title`, `name`,
`marker` and `run`, and emits `close` and `done`. The words come from `ui/src/confirm.ts`, each a `{ title, name }`
object: `deletion` is *Delete this render?* with `name` null, `removal(name)` is *Remove this tattoo?* with the
tattoo's name, shown under the title.

*No* comes first and holds the focus, `h` `l` `←` `→` move, `↵` presses the focused choice, `Esc` is *No*, and a refusal
shows inside and returns the focus to *No*. The `marker` prop names the `data-<marker>-dialog`, `-choice`, `-no`, `-yes`
and `-refusal` attributes, so the render's deletion keeps the selectors `tests/e2e/test_render.py` reads. `DeleteDialog.vue`
is deleted; `armRemoval`, `data-armed` and the card's refusal line go with the arm.

The dialog declares its keys through `useKeys('overlay', …)` as every dialog does, so the screen's own key rule gains one
sentence in the `ui` delta.

### D2

**The picker's top.** `TattooPicker.vue` takes the render's `version` and `seed` beside its `place` and shows, above the
forms, the render (`imageAt`) left and the photograph (`photoUrl`) right, each `width: 100%` of its half. The forms and
the cards keep their order below.

### D3

**A cut's own crop.** `CutImage.vue` reads the cut's outline with `tattooNamed`, takes its box, and draws the photograph
cropped to it with `thumbCrop(points, size, frame)` in `ui/src/tattoos.ts`. Once the outline is closed it asks `inkView`
for the same cut and shows the ink view instead.

`thumbCrop` fits the box into `FRAME`, 160 by 120 pixels: the scale is the least of frame width over box width and frame
height over box height, and it returns the frame's `width` and `height` and the photograph's `backgroundSize` and
`backgroundPosition` in pixels. No point, or a box of no area, which a cut with one point or points on a line has, gives
`null`, and the card then shows the whole photograph as it does today.

The photograph's size is the tattoo's `size`, which for a cut is the photograph's. Example: the box 100 by 50 at 250, 275
on a 1100 by 600 photograph gives a frame of 160 by 80, a `backgroundSize` of `1760px 960px` and a `backgroundPosition`
of `-400px -440px`.

### D4

**The head.** The thumbnail, its `thumbAt` import and `.place__render` go. The head reads *place a tattoo · flow · v ·
seed* and the steps, as before.

### D5

**The head's state.** `OutlineStep.vue` keeps what `saveOutline` answers and sets its tattoo's `outlined` from the
answer's `closed` through `withOutline(tattoo, outline)` in `ui/src/tattoos.ts`. The server derives `outlined` from
`closed`, so the head and the picker agree at once. The same answer goes to the screen's state, as D7 says.

### D6

**Full height.** `.pair > .panel { flex: 1; }` lets the panel grow inside the flex column of `.pair`, so the viewport,
`flex: 1` over a `min-height` of 360px, fills the grid row. The rule sits on the shared `.pair`, so step ③ and the
direct stage grow too: they use the same panel.

### D7

**The ask waits.** `usePlacing` counts the reads and the outline saves in flight through `track`, which counts down in a
`finally`, and exposes `reading`, true while any runs. `adopt(name, outline)` sets the held tattoo's `outline` and
`outlined` from a save's answer, and does nothing for another tattoo than the one held.

`OutlineStep.vue` tracks each save the moment `flush` queues it and adopts its answer. That replaces the read `Place.vue`
started on leaving step ②, which a save still on its way could pass: a step left by a head link now reaches the stage
with the saved outline, and no read can overwrite it with an older one.

`due(mode, pairs, asks, key, points, reading)` is false while `reading` is true or `points`, the count of points the ask
would send, is none. `StageRender.vue` passes both, so its watch fires again when the saved outline arrives and the ask
goes out with it.

A refusal now shows `Could not propose pairs — place them by clicking`, whatever the server's words. The ask can no
longer refuse for its shape; the one refusal left is absent models, which `make setup` fetches. The line costs the screen
that fix and keeps every refusal one short line.

The requirements of the `ui` capability that lose a scenario change their titles for it: a modified requirement may not drop a scenario, and
the scenarios *remove takes a second click* and *a refusal shows its words…* go. Each is removed and its successor added.

### D8

**The review.** `ReviewBake.vue` drops the render and the ink over it. The *before* and *after* crops sit in two equal
columns, each `width: 100%` with the box's aspect ratio, through `fitted(box, size)` in `ui/src/review.ts`: the render is
sized at the natural width over the box's width and placed by the box's offset over what is left of the render. An axis
the box fills, with nothing left, places at 0%.

The step's root loses the class `review`, which the Review view's column rule matched, so the side column now stands right
of the crops as on step ④. *Back* and *Bake* sit in one row under the bake's state line.

### D9

**The soft edge.** `polygon_mask` draws the polygon at `SUPERSAMPLE`, 4, times its size with each point at `4x + 1.5`, the
centre of its pixel's block, and reduces it to the mask's size with a box filter. The mask stays `uint8`, 255 well inside.

The far edge of a polygon moves half a pixel in: the hard fill covered the pixel a vertex names, and the soft one covers
half of it. A test that reads a pixel on a polygon's edge moves its probe inside the polygon and keeps its value.

`clip` multiplies the ink's opacity by one minus the exclusion's mask over 255 where it zeroed any covered pixel, and keeps
the blur of 1 on the limb's mask. The ink's outline takes the same mask in `ink_layer`, and `isekai/shared/ink.py` is
unchanged: its white point reads the pixels whose opacity is over 127, so the soft edge keeps the selection.

### D10

**A minor.** `CONTRIBUTING.md` allows a patch no change to the image for the same inputs, and the baked ink's edge moves.
The picker also gains the photograph. The cut starts its own run, beside no version.

## Tests

Growth is small and every new test sits at the lowest layer: a pure function over a node-only vitest run, or a function of
`isekai/shared/chain.py`. No end-to-end test is added, and `make e2e` adds no run: the render's deletion keeps its markers.

| layer | added | where | count command |
|---|---|---|---|
| vitest | the dialog's words | `ui/src/confirm.test.ts` | `git grep -c "^spec(" -- ui/src/confirm.test.ts` prints 1 |
| vitest | the cut's crop, the head's state | `ui/src/tattoos.test.ts` | `git grep -c "^spec(" -- ui/src/tattoos.test.ts` prints 18, from 17 less the arm's plus two |
| vitest | the ask waits, the read in flight | `ui/src/propose.test.ts`, `ui/src/composables/usePlacing.test.ts` | one in each, bound to the same key |
| vitest | the fit of the crops | `ui/src/review.test.ts` | `git grep -c "^spec(" -- ui/src/review.test.ts` prints 5 |
| pytest | the mask's edge, an exclusion's edge | `tests/test_chain.py` | `git grep -c "^def test_" -- tests/test_chain.py` prints 27 |
| pytest | the ink layer's edge | `tests/test_tattoo_placement.py` | `git grep -c "^def test_" -- tests/test_tattoo_placement.py` prints 30 |

Reads change in place: `ui/src/nokeys.test.ts` also reads `ConfirmDialog.vue`, the refusal test of
`ui/src/propose.test.ts` is re-keyed to the plain line, and the `due` and `refused` calls of that file and of
`ui/src/composables/usePlacing.test.ts` take the new arguments.

The test the change deletes, mapped per `I16`:

| deleted | carried by |
|---|---|
| `ui/src/tattoos.test.ts` `ui:picker:remove-takes-a-second-click` | its scenario is re-keyed `ui:picker:remove-asks-in-a-dialog`, carried by `ui/src/confirm.test.ts`; the arm's assertions go with `armRemoval` |

These existing tests read a pixel on a polygon's far edge, which the soft fill moves half a pixel in:
`test_chain_place_clips_to_the_limb_and_removes_each_exclusion` in `tests/test_chain.py` and
`test_placement_preview_the_limb_keeps_the_ink_and_an_exclusion_removes_it` in `tests/test_tattoo_placement.py`. Each moves its
probe inside the polygon and keeps its value. Every other test of those files, of `tests/test_ink.py` and of
`tests/test_tattoo_library.py` reads interior pixels or builds its own outline; a further red one is a plan problem.

The change rewrites lines of `isekai/shared/chain.py`, so the pre-flight of `CONTRIBUTING.md` applies to the build: it runs
`uv run python -m tools.mutate` over the rewritten lines of `polygon_mask` and `clip` on `tests/test_chain.py` before and
after phase 4, and its commit body says how a test killed each survivor or why it is equivalent.

## Dependencies

None.

## Risks / Trade-offs

- **Requests per picker visit.** Each cut card reads its outline, and each closed one asks its ink view. A library of many
  cuts costs that many requests, each local. A server list carrying the boxes would cost one, and is a later change.
- **Mask memory.** The 4× fill holds 16 times the crop's pixels at one byte each. A crop of 4000 by 3000 holds about
  190 MB for the moment of the fill. The operator's machine takes it; a banded fill is the fix if one does not.
- **The plain line hides the cause.** A refusal for absent models no longer names its command on the stage. `make setup`
  fetches the models, and the CLI's own refusals still name theirs.
- **Step ③ grows too.** It shares `PairPanel`, so the same rule lays it out; the person asked for step ④ and this is the
  same fault.

## Verdict

Feasible. Each fix reads what the routes and the state already hold, and the one change of product, the ink's edge, is
a function of `chain.py` that the preview and the bake share. Ready to build in the phases of [tasks](tasks.md).
