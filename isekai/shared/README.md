# `shared/` — primitives with no domain of their own

Used on both sides of the pipeline, and belonging to neither. Each one takes its
inputs and returns an answer, and none of them reads a score.

**Each reads `foundation`.** `field_map.py` imports `artifacts`, `flow`,
`refusal` and `run`; `fields.py` imports `flow` and `refusal`; `image.py`
imports `refusal`; `vocabulary.py` imports `artifacts`. A schema is a flow's, so
validating a sheet against one means knowing what a flow is. What none of them
does is reach a boundary or decide a stage's order.

## Files

| file | does |
|---|---|
| `field_map.py` | answers *which identity criterion does this tag belong to* — one authored table, read `tag → field` to route and `field → tags` to browse |
| `fields.py` | answers *is this filled sheet exactly the schema's fields of canonical tags* |
| `image.py` | reads a JPEG or PNG header and derives the render target the image's own dimensions imply |
| `vocabulary.py` | answers *is this a real tag* and *how strong is it* |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `field_map.py` | `interface/cli.py`, `interface/ui/batch.py`, `interface/wiring.py`, `pipeline/sheet.py` | `tools/derive_field_map.py`, `tests/stages.py`, `tests/test_field_map.py`, `tests/test_ui_api.py` |
| `fields.py` | `pipeline/review.py`, `pipeline/sheet.py` | `tests/test_sheet_schema.py` |
| `image.py` | `interface/ui/batch.py`, `pipeline/generate.py` | `evaluation/evaluate.py`, `tests/test_evaluate.py`, `tests/test_generate.py`, `tests/test_image.py` |
| `vocabulary.py` | `boundary/wd14.py`, `interface/cli.py`, `interface/ui/batch.py`, `interface/wiring.py`, `pipeline/review.py`, `pipeline/sheet.py`, `field_map.py`, `fields.py` | `tools/derive_field_map.py`, `tests/conftest.py`, `tests/stages.py`, `tests/test_field_map.py`, `tests/test_generate.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_sheet_schema.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_ui_api.py`, `tests/test_vocabulary.py` |

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
