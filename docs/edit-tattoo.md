# Adding a tattoo to a render

Place a tattoo by hand on a finished render in Krita, then bake it in with `isekai edit`. The bake is
the one paid step, and `isekai render` runs it.

```
photo ─ isekai ink ─▶ ink.png ─ Krita ─▶ composite.png
render.png + composite.png ─ isekai edit ─▶ <seed>.edit-<k>.{composite.png,json}   pending
isekai render <runs> ─ the session ─▶ <seed>.edit-<k>.png                         beside the render
```

The decisions are [D51](decisions.md#d51--an-edit-is-one-flat-directory-pinned-by-its-digest) and
[D36](decisions.md#d36--a-render-session-is-isekai-render). The tattoo's photograph never enters a run.

## 1. Cut the ink

`isekai ink <image> <out>` turns a tattoo's photograph, or an image of one, into a PNG layer to multiply over a
render. It is free and local.

```sh
python -m isekai ink .inputs/tattoo.jpg .inputs/ink.png --outline .inputs/outline.png
python -m isekai ink .inputs/flash.png .inputs/ink.png
```

| input | `--outline` | the layer |
|---|---|---|
| a photograph of skin | a mask, white where the ink is | the skin under the ink removed, bare skin white, the mask as alpha, grey |
| a tattoo image | none | the whole image, in colour |

`--neutral` and `--no-neutral` set grey or colour against what the input implies. `--depth` is the power the layer's
Multiply factor is raised to, from the range `config/ink.json` names; a higher depth darkens a fill.

## 2. Place the ink in Krita

1. Open the render, `.data/runs/<run>/<flow>/outputs/<NNN>/<seed>.png`.
2. Add `ink.png` as a layer and set its blend mode to **Multiply**. Move, scale and warp it to the skin.
3. Add no layer that lightens the render: the edit refuses a pixel lighter than the render.
4. Flatten and export a PNG **at the render's size, with no transparency**, as `composite.png`.

## 3. Request the edit

```sh
python -m isekai edit tattoo-wai .data/runs/<run>/<flow>/outputs/<NNN>/<seed>.png --composite composite.png
```

The request is free and local. It checks the composite against the render, derives the mask and the crop box, and
writes two files beside the render: `<seed>.edit-<k>.composite.png` and `<seed>.edit-<k>.json`. An edit with no
`<seed>.edit-<k>.png` is **pending**. A request refuses, naming its fix, a composite of another size, one with
transparency, one with no ink, one lighter than the render, and a near-black render that reads no ink.

To edit an edit, name its image as the render: `<seed>.edit-<k>.png` makes the next free `k`.

## 4. Override a dial for one request

`--denoise`, `--strength` and `--lines` take a number for this request alone; `edits/tattoo-wai/edit.json` is
unchanged, and the record marks each one overridden. `--seed` repeats a sampling seed.

| dial | what it does |
|---|---|
| `--denoise` | how far the pass repaints under the mask |
| `--strength` | how firmly the control holds the ink's lines |
| `--lines` | how much of the ink is multiplied back after the pass |

## 5. Render

```sh
python -m isekai render .data/runs
```

With no request, `isekai render` runs each named collection's pending edits after its renders. It checks every
pending edit first, free, so a source that changed since the request refuses before a pod is rented. A session may
hold edits alone, and `--without <runs>/<run-id>/<flow>` leaves a run's flow and its edits out. The pod receives the
crop, its mask and its control; the stitch and the lines are made here. The quote counts each edit
at `per_edit_s` of `config/render.json`, or the median of the newest recorded edits when that is higher. Money,
the pod and its teardown are as [D36](decisions.md#d36--a-render-session-is-isekai-render) says.

A failed sampling records nothing: the request stays pending, and the next session tries it again. Discard an edit the
endpoint keeps rejecting.

## 6. Discard

```sh
python -m isekai discard .data/runs/<run>/<flow>/outputs/<NNN>/<seed>.edit-<k>.png
```

An edit's path deletes that edit and every edit chained from it; the render stays. Discarding the render takes all
its edits. Both refuse while a render session holds the collection.

## The app

`isekai ui` starts the placement screen's first steps. They keep and outline a tattoo; the composite is still made in
Krita (§2) until the stages that click point pairs are built.

```
render's large view ─ ⇧P ─▶ ① tattoo ─▶ ② outline + ink view
                              │             └─ the ink as the server draws it, on the outline's crop
                .tattoos/<name>/ in the library
```

- **Open it** with `⇧P` or *Place a tattoo* on a render's large view.
- **The library** is `.tattoos/<name>/` beside the collections, in the folder `ISEKAI_LIBRARY` names, so one tattoo
  serves every render in every collection ([D52](decisions.md#d52--the-tattoo-library-is-library-wide-kept-whole-and-never-deleted)).
  It holds `design.png`, `tattoo.json` and `outline.json`. The app deletes and renames nothing.
- **An upload** goes through the import's staging, is cleaned as a source is, and is kept upright, scaled down to the
  `long_side` of `config/tattoo.json`, under a name kept once.
- **A cut** is a tattoo with no image: *Cut from this photo* keeps the render's photograph as the source of the ink, so
  the photograph stays in its run and serves only its own renders. A second cut from the same photograph starts from
  the newest cut's tone.
- **The outline** is clicked on the tattoo, or on the photograph for a cut, and closed on its first point. It is saved
  as it changes, with the white point and the tone.
- **The ink view** is the same extraction as §1, drawn by the server on the outline's crop. The white point is the
  automatic one as a grey from 0 to 255, set by hand or back to *Auto*. *Neutral* and *depth* are `--neutral` and
  `--depth`, and *Reset* returns them to the kind's defaults.

The stages come later: the point pairs, the warp's preview and the bake.
