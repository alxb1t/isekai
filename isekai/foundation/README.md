# `foundation/` — what a run, a flow and a refusal are

The types every other group is built on. Nothing here knows about a stage, an
endpoint or a score; everything here is imported by something that does.

## Files

| file | does |
|---|---|
| `refusal.py` | one error that names its own fix, raised anywhere and caught once |
| `artifacts.py` | the run directory's contract: every run file kind's shape and version, one typed `read` and `write`, `require` for a key a hand-edited file may lack, and the JSON form every artifact is written in |
| `run.py` | the front of the run directory: it re-exports its siblings' names and holds the roots, `open_run` and `find_run`, `rendered_at`, the command text with `photo_of`, the migration state, `refusal_for`, `instructions_record` and `constant_record` |
| `names.py` | a run's id, the names of its layout and the draft's label |
| `rundir.py` | `Run`, one photograph's directory and its frame, `assign`, and `runs_in` and `run_at`, which folders are runs |
| `layout.py` | numbering and completion, the seeds, the names of a render's image and record, the rule that a seed is rendered, a render group's listing, the refs an image's path names, the edit files, the draft being worked on and its source copy |
| `failures.py` | the failure shape the stages share: `Kind`, the budgets, the attempts a directory records, `across` and `StageFailure`, here and not in `refusal.py` because `refusal.py` imports nothing by design and the class needs `Kind` |
| `migrate.py` | `migrate(run)`: copies a run's per-flow caption and tag lists into `photo/`, each kind whole or not at all, never deleting a source |
| `flow.py` | reads and validates a frozen flow directory — flat, its files named rather than counted — lists what is tracked, and owns the `Workflow` graph type, the `Schema` type, its reader and prompt assembly |
| `caption_config.py` | reads `config/caption.json` — the model the reader and the hosted tagger run, and the briefing beside it — the library's, not a flow's |
| `config.py` | reads a JSON config by the keys a build reads, refusing a key it does not read and a key it lacks |
| `atomic_write.py` | writes bytes to a path, or writes nothing — temp-then-replace on one filesystem |
| `library.py` | the library's folder names and a collection's, `root`, `is_collection`, `listed` and `collection`, and the read side of a collection's session records: `UNSUPPORTED`, `record_running`, `running`, `render_running` and `session`, and where a thumbnail sits in the cache and what names it: `stat_key`, `file_digest`, `thumbnail_of` and `drop_thumbnails` |

## Imported by

**Derived.** `uv run python -m tools.derive_imported_by` writes this table from the import graph of `tools/import_graph.py`, the one the layer guards read, and a test re-derives it. It names importers in `isekai/`, `evaluation/` and `tools/`, never a test.

| file | inside `isekai/` | outside |
|---|---|---|
| `refusal.py` | `boundary/comfy/contract.py`, `boundary/comfy/prompt.py`, `boundary/ollama.py`, `boundary/pose.py`, `boundary/sam2.py`, `boundary/wd14.py`, `artifacts.py`, `caption_config.py`, `config.py`, `edit.py`, `failures.py`, `flow.py`, `layout.py`, `library.py`, `migrate.py`, `names.py`, `run.py`, `rundir.py`, `interface/cli.py`, `interface/compare_view.py`, `interface/drafting.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/app.py`, `interface/ui/bundle.py`, `interface/ui/jobs.py`, `interface/ui/library.py`, `interface/ui/routes/common.py`, `interface/ui/routes/hub.py`, `interface/ui/routes/images.py`, `interface/ui/routes/place.py`, `interface/ui/routes/rendering.py`, `interface/ui/routes/reviewing.py`, `interface/ui/routes/staging.py`, `interface/ui/routes/stream.py`, `interface/ui/routes/tattoos.py`, `interface/ui/surface.py`, `interface/verbs/common.py`, `interface/verbs/drafts.py`, `interface/verbs/edits.py`, `interface/verbs/library.py`, `interface/verbs/prepare.py`, `interface/wiring.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/importing.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `pipeline/tattoos.py`, `shared/chain.py`, `shared/field_map.py`, `shared/fields.py`, `shared/image.py`, `shared/ink.py`, `shared/tattoo.py`, `shared/vocabulary.py` | `evaluation/__main__.py`, `evaluation/cohort.py`, `evaluation/face.py`, `evaluation/recall.py`, `evaluation/record.py` |
| `artifacts.py` | `boundary/comfy/prompt.py`, `boundary/ollama.py`, `boundary/wd14.py`, `discard.py`, `failures.py`, `layout.py`, `library.py`, `migrate.py`, `run.py`, `rundir.py`, `interface/compare_view.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/jobs.py`, `interface/ui/library.py`, `interface/ui/routes/common.py`, `interface/ui/routes/images.py`, `interface/ui/routes/reviewing.py`, `interface/ui/shapes.py`, `interface/verbs/common.py`, `pipeline/caption.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `pipeline/tattoos.py`, `shared/field_map.py`, `shared/vocabulary.py` | `evaluation/__main__.py`, `evaluation/recall.py`, `tools/derive_field_map.py` |
| `run.py` | `boundary/comfy/contract.py`, `boundary/gpu.py`, `boundary/ollama.py`, `discard.py`, `library.py`, `migrate.py`, `interface/cli.py`, `interface/compare_view.py`, `interface/drafting.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/__init__.py`, `interface/ui/bundle.py`, `interface/ui/jobs.py`, `interface/ui/library.py`, `interface/ui/routes/common.py`, `interface/ui/routes/hub.py`, `interface/ui/routes/images.py`, `interface/ui/routes/place.py`, `interface/ui/routes/rendering.py`, `interface/ui/routes/reviewing.py`, `interface/ui/surface.py`, `interface/verbs/common.py`, `interface/verbs/drafts.py`, `interface/verbs/edits.py`, `interface/verbs/generate.py`, `interface/verbs/library.py`, `interface/verbs/prepare.py`, `interface/wiring.py`, `pipeline/caption.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/importing.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `pipeline/tattoos.py`, `shared/field_map.py`, `shared/vocabulary.py` | `evaluation/__main__.py`, `evaluation/recall.py`, `evaluation/record.py` |
| `names.py` | `failures.py`, `layout.py`, `run.py`, `rundir.py` | — |
| `rundir.py` | `failures.py`, `layout.py`, `run.py` | — |
| `layout.py` | `run.py` | — |
| `failures.py` | `run.py` | — |
| `flow.py` | `boundary/comfy/client.py`, `boundary/comfy/contract.py`, `boundary/comfy/prompt.py`, `edit.py`, `layout.py`, `interface/cli.py`, `interface/compare_view.py`, `interface/drafting.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/library.py`, `interface/ui/routes/images.py`, `interface/ui/routes/rendering.py`, `interface/ui/surface.py`, `interface/verbs/common.py`, `interface/verbs/drafts.py`, `interface/verbs/generate.py`, `interface/verbs/prepare.py`, `interface/wiring.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `shared/field_map.py`, `shared/fields.py` | `evaluation/__main__.py`, `evaluation/recall.py` |
| `migrate.py` | `interface/cli.py` | — |
| `caption_config.py` | `interface/cli.py`, `interface/wiring.py` | — |
| `config.py` | `caption_config.py`, `pipeline/tattoos.py`, `shared/ink.py` | — |
| `atomic_write.py` | `artifacts.py`, `run.py`, `interface/compare_view.py`, `interface/ui/library.py`, `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/importing.py`, `pipeline/review.py`, `pipeline/tattoos.py`, `shared/ink.py` | — |
| `library.py` | `interface/compare_view.py`, `interface/render.py`, `interface/ui/library.py`, `interface/verbs/drafts.py`, `pipeline/importing.py` | — |
| `discard.py` | `pipeline/edit.py`, `pipeline/generate.py`, `pipeline/review.py` | — |

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
