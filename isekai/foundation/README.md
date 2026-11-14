# `foundation/` — what a run, a flow and a refusal are

The types every other group is built on. Nothing here knows about a stage, an
endpoint or a score; everything here is imported by something that does.

## Files

| file | does |
|---|---|
| `refusal.py` | one error that names its own fix, raised anywhere and caught once |
| `artifacts.py` | the run directory's contract: every run file kind's shape and version, one typed `read` and `write`, `require` for a key a hand-edited file may lack, and the JSON form every artifact is written in |
| `run.py` | the run directory: ids, the frame, the layout and its names — the photograph's description in `photo/`, reached through `photo_of`, which refuses a run not yet migrated, and each flow's work below — a flow's assignment, numbering, approval, budgets, and **the failure shape the stages share** — `StageFailure`, `refusal_for`, `instructions_record`, `constant_record`, rehomed here from `boundary/claude_cli.py` in v0.22 because `refusal.py` imports nothing by design and the class needs `Kind` |
| `migrate.py` | `migrate(run)`: copies a run's per-flow caption and tag lists into `photo/`, each kind whole or not at all, never deleting a source |
| `flow.py` | reads and validates a frozen flow directory — flat, its files named rather than counted — lists what is tracked, and owns the `Workflow` graph type, the `Schema` type, its reader and prompt assembly |
| `caption_config.py` | reads `config/caption.json` — the model the reader and the hosted tagger run, and the briefing beside it — the library's, not a flow's |
| `atomic_write.py` | writes bytes to a path, or writes nothing — temp-then-replace on one filesystem |

## Imported by

**Derived.** `uv run python -m tools.derive_imported_by` writes this table from the import graph of `tools/import_graph.py`, the one the layer guards read, and a test re-derives it. It names importers in `isekai/`, `evaluation/` and `tools/`, never a test.

| file | inside `isekai/` | outside |
|---|---|---|
| `refusal.py` | `boundary/comfy/contract.py`, `boundary/comfy/prompt.py`, `boundary/ollama.py`, `boundary/pose.py`, `boundary/sam2.py`, `boundary/wd14.py`, `artifacts.py`, `caption_config.py`, `edit.py`, `flow.py`, `migrate.py`, `run.py`, `interface/cli.py`, `interface/compare_view.py`, `interface/drafting.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/app.py`, `interface/ui/bundle.py`, `interface/ui/jobs.py`, `interface/ui/library.py`, `interface/verbs/common.py`, `interface/wiring.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/importing.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `pipeline/tattoos.py`, `shared/chain.py`, `shared/field_map.py`, `shared/fields.py`, `shared/image.py`, `shared/ink.py`, `shared/tattoo.py`, `shared/vocabulary.py` | `evaluation/__main__.py`, `evaluation/cohort.py`, `evaluation/face.py`, `evaluation/recall.py`, `evaluation/record.py` |
| `artifacts.py` | `boundary/comfy/prompt.py`, `boundary/ollama.py`, `boundary/wd14.py`, `migrate.py`, `run.py`, `interface/compare_view.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/app.py`, `interface/ui/jobs.py`, `interface/ui/library.py`, `interface/verbs/common.py`, `pipeline/caption.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `pipeline/tattoos.py`, `shared/field_map.py`, `shared/vocabulary.py` | `evaluation/__main__.py`, `evaluation/recall.py`, `tools/derive_field_map.py` |
| `run.py` | `boundary/comfy/contract.py`, `boundary/gpu.py`, `boundary/ollama.py`, `migrate.py`, `interface/cli.py`, `interface/compare_view.py`, `interface/drafting.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/__init__.py`, `interface/ui/app.py`, `interface/ui/bundle.py`, `interface/ui/jobs.py`, `interface/ui/library.py`, `interface/verbs/common.py`, `interface/wiring.py`, `pipeline/caption.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/importing.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `pipeline/tattoos.py`, `shared/field_map.py`, `shared/vocabulary.py` | `evaluation/__main__.py`, `evaluation/recall.py`, `evaluation/record.py` |
| `flow.py` | `boundary/comfy/client.py`, `boundary/comfy/contract.py`, `boundary/comfy/prompt.py`, `edit.py`, `interface/cli.py`, `interface/compare_view.py`, `interface/drafting.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/app.py`, `interface/ui/library.py`, `interface/verbs/common.py`, `interface/wiring.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `shared/field_map.py`, `shared/fields.py` | `evaluation/__main__.py`, `evaluation/recall.py` |
| `migrate.py` | `interface/cli.py` | — |
| `caption_config.py` | `interface/cli.py`, `interface/wiring.py` | — |
| `atomic_write.py` | `artifacts.py`, `run.py`, `interface/compare_view.py`, `interface/ui/library.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/importing.py`, `pipeline/review.py`, `pipeline/tattoos.py`, `shared/ink.py` | — |

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
