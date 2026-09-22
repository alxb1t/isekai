# `pipeline/` — the staged verbs, and one module that is not one

One file per stage, in the order a photograph passes through them. No stage reads
another's output directly: each is handed a path inside a run and hands back a
numbered artifact, and **no stage imports another** — the last such edge closed
when `validate` moved to `shared/fields.py`. Every stage is per flow: the flow
supplies the briefing it reads, the schema it fills against and the directory it
writes into.

**The verbs are `caption` · `sheet` · `review` · `approve` · `generate` — five
verbs over four files, because `review.py` holds two of them — and `tagging.py`
is not one of them.** Its two functions write the two tag artifacts `caption` also
produces, in the same invocation and under the same flow — so it is a file here
without being a verb. It sits beside `caption.py` rather than inside it because `caption()`
had to be provably unchanged by this version, and a function with no edit is
provably unchanged by `git diff`.

## Files

| file | does | costs |
|---|---|---|
| `caption.py` | ① turns a photograph into descriptive prose | a model call |
| `tagging.py` | ① twice more: a scored tag list from a local ONNX session, and a raw one from a hosted model. **Neither is narrowed** — filtering is ②'s job | free, then a model call |
| `sheet.py` | ② routes the local tag list into the flow's schema's fields, through the authored table | free |
| `review.py` | ③ copies a sheet somewhere a human may correct it, then approves it | a human — the largest measured gain in the pipeline |
| `generate.py` | ④ assembles every prompt locally, then renders each against an endpoint | free, then **money** |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `caption.py` | `interface/cli.py`, `interface/wiring.py` | `tests/stages.py`, `tests/test_caption.py`, `tests/test_generate.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_ui_api.py` |
| `tagging.py` | `interface/cli.py`, `interface/wiring.py` | `tests/test_generate.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_run_view.py`, `tests/test_tagging.py`, `tests/test_ui_api.py` |
| `sheet.py` | `interface/cli.py` | `tests/stages.py` |
| `review.py` | `interface/cli.py`, `interface/ui/app.py`, `interface/ui/batch.py` | `tests/test_generate.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_ui.py`, `tests/test_ui_api.py` |
| `generate.py` | `interface/cli.py`, `interface/run_view.py` | `tests/test_generate.py`, `tests/test_resume.py`, `tests/test_run_directory.py`, `tests/test_run_view.py` |

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
