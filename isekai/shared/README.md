# `shared/` — primitives with no domain of their own

Used on both sides of the pipeline, and belonging to neither. Each one takes its
inputs and returns an answer, and none of them reads a score.

**Each reads `foundation`.** `chain.py` imports `refusal`; `field_map.py` imports `artifacts`, `flow`,
`refusal` and `run`; `fields.py` imports `flow` and `refusal`; `image.py`
imports `refusal`; `ink.py` imports `atomic_write` and `refusal`; `tattoo.py` imports `refusal`;
`vocabulary.py` imports `artifacts`, `refusal` and `run`. A schema is a flow's, so
validating a sheet against one means knowing what a flow is. What none of them
does is reach a boundary or decide a stage's order.

## Files

| file | does |
|---|---|
| `chain.py` | the maths of a placement, each a function over arrays: a thin-plate `Spline` exact at its pairs, the `lookup` of ink through a chain of them, the polygon mask, the `clip` to an outline, the `multiply` over a render, the `place` of an ink layer through the stages' splines, its `flatten` on white and the `crop_box` every caller crops to; Pillow and numpy are imported inside its functions |
| `field_map.py` | answers *which identity criterion does this tag belong to* — one authored table, read `tag → field` to route and `field → tags` to browse |
| `fields.py` | answers *is this filled sheet exactly the schema's fields of canonical tags* |
| `image.py` | reads a JPEG or PNG header and derives the render target the image's own dimensions imply, refusing what render cannot take; strips a photograph's metadata for upload, names what a file carries beyond its pixels, and makes a thumbnail |
| `ink.py` | the maths of `isekai ink`: cuts a tattoo's photograph or image into a layer to multiply over a render, under `config/ink.json`, at a `white` scale on the automatic white point, whose grey `white_grey` reads, or `extract_ink_grey` with the layer from one read; Pillow and numpy are imported inside its functions |
| `tattoo.py` | the maths of an edit, each a function over arrays: the ink, darkness, mask and control of a composite over its render, the crop box and sampling size, the refusals, and the stitch of a sampled crop back; Pillow and numpy are imported inside its functions |
| `vocabulary.py` | answers *is this a real tag* and *how strong is it* |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `chain.py` | `pipeline/tattoos.py` | `tests/test_chain.py`, `tests/test_tattoo_placement.py` |
| `field_map.py` | `interface/cli.py`, `interface/drafting.py`, `interface/ui/app.py`, `interface/wiring.py`, `pipeline/sheet.py` | `tools/derive_field_map.py`, `tests/stages.py`, `tests/test_field_map.py`, `tests/test_package_paths.py`, `tests/test_ui_api.py` |
| `fields.py` | `pipeline/review.py`, `pipeline/sheet.py` | `tests/test_sheet_schema.py` |
| `image.py` | `interface/ui/app.py`, `interface/ui/library.py`, `pipeline/generate.py`, `pipeline/importing.py` | `tests/test_generate.py`, `tests/test_image.py`, `tests/test_importing.py`, `tests/test_resume.py` |
| `ink.py` | `interface/cli.py`, `interface/ui/app.py`, `pipeline/tattoos.py` | `tests/test_ink.py`, `tests/test_tattoo_library.py` |
| `tattoo.py` | `pipeline/edit.py`, `pipeline/tattoos.py`, `ink.py` | `tests/test_edit.py` |
| `vocabulary.py` | `boundary/wd14.py`, `interface/cli.py`, `interface/drafting.py`, `interface/ui/app.py`, `interface/wiring.py`, `pipeline/review.py`, `pipeline/sheet.py`, `field_map.py`, `fields.py` | `evaluation/__main__.py`, `evaluation/face.py`, `evaluation/recall.py`, `tests/conftest.py`, `tests/stages.py`, `tests/test_artifact_bytes.py`, `tests/test_compare.py`, `tests/test_field_map.py`, `tests/test_generate.py`, `tests/test_package_paths.py`, `tests/test_pipeline_cli.py`, `tests/test_progress.py`, `tests/test_render.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_sheet_schema.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `tests/test_ui_library.py`, `tests/test_vocabulary.py`, `tools/derive_field_map.py` |

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
