# `foundation/` — what a run, a flow and a refusal are

The types every other group is built on. Nothing here knows about a stage, an
endpoint or a score; everything here is imported by something that does.

## Files

| file | does |
|---|---|
| `refusal.py` | one error that names its own fix, raised anywhere and caught once |
| `artifacts.py` | the run directory's contract: every run file kind's shape and version, one typed `read` and `write`, `require` for a key a hand-edited file may lack, and the JSON form every artifact is written in |
| `run.py` | the run directory: ids, the frame, the input-above-flow-below layout and its names, numbering, approval, budgets, and **the failure shape the stages share** — `StageFailure`, `refusal_for`, `instructions_record`, `constant_record`, rehomed here from `boundary/claude_cli.py` in v0.22 because `refusal.py` imports nothing by design and the class needs `Kind` |
| `flow.py` | reads and validates a frozen flow directory — flat, its files named rather than counted — lists what is tracked, and owns the `Workflow` graph type, the `Schema` type, its reader and prompt assembly |
| `atomic_write.py` | writes bytes to a path, or writes nothing — temp-then-replace on one filesystem |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `refusal.py` | `boundary/comfy/contract.py`, `boundary/ollama.py`, `boundary/wd14.py`, `artifacts.py`, `flow.py`, `run.py`, `interface/cli.py`, `interface/ui/app.py`, `interface/ui/batch.py`, `interface/ui/bundle.py`, `interface/wiring.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `shared/field_map.py`, `shared/fields.py`, `shared/image.py` | `evaluation/evaluate.py`, `tests/test_caption.py`, `tests/test_field_map.py`, `tests/test_flow.py`, `tests/test_generate.py`, `tests/test_ollama.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_sheet_schema.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_vocabulary_manifest.py`, `tests/test_wd14.py` |
| `artifacts.py` | `boundary/wd14.py`, `run.py`, `interface/run_view.py`, `interface/ui/app.py`, `pipeline/caption.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `shared/field_map.py`, `shared/vocabulary.py` | `tools/derive_field_map.py`, `tests/stages.py`, `tests/test_artifact_bytes.py`, `tests/test_caption.py`, `tests/test_generate.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui_api.py`, `tests/test_wd14.py` |
| `run.py` | `boundary/comfy/contract.py`, `boundary/ollama.py`, `interface/cli.py`, `interface/run_view.py`, `interface/ui/batch.py`, `interface/ui/bundle.py`, `interface/wiring.py`, `pipeline/caption.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `shared/field_map.py` | `tests/stages.py`, `tests/test_artifact_bytes.py`, `tests/test_caption.py`, `tests/test_generate.py`, `tests/test_package_paths.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_ui_api.py` |
| `flow.py` | `boundary/comfy/client.py`, `boundary/comfy/contract.py`, `interface/cli.py`, `interface/run_view.py`, `interface/ui/batch.py`, `interface/wiring.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `shared/field_map.py`, `shared/fields.py` | `tests/conftest.py`, `tests/fakes.py`, `tests/stages.py`, `tests/test_artifact_bytes.py`, `tests/test_field_map.py`, `tests/test_flow.py`, `tests/test_generate.py`, `tests/test_image.py`, `tests/test_infra.py`, `tests/test_manifest_binding.py`, `tests/test_package_paths.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_sheet_schema.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_ui_api.py` |
| `atomic_write.py` | `artifacts.py`, `run.py`, `pipeline/generate.py` | `tests/test_run_directory.py` |

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
