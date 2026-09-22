# `foundation/` — what a run, a flow and a refusal are

The types every other group is built on. Nothing here knows about a stage, an
endpoint or a score; everything here is imported by something that does.

## Files

| file | does |
|---|---|
| `refusal.py` | one error that names its own fix, raised anywhere and caught once |
| `run.py` | the run directory: ids, the frame, the input-above-flow-below layout and its names, numbering, approval, budgets, the JSON form every artifact is written in, and **the failure shape the stages share** — `StageFailure`, `refusal_for`, `instructions_record`, `constant_record`, rehomed here from `boundary/claude_cli.py` in v0.22 because `refusal.py` imports nothing by design and the class needs `Kind` |
| `flow.py` | reads and validates a frozen flow directory — flat, its files named rather than counted — lists what is tracked, and owns the `Schema` type, its reader and prompt assembly |

## Imported by

| file | inside `isekai/` | outside |
|---|---|---|
| `refusal.py` | `boundary/ollama.py`, `boundary/wd14.py`, `evaluation/evaluate.py`, `flow.py`, `run.py`, `interface/cli.py`, `interface/wiring.py`, `interface/ui/app.py`, `interface/ui/batch.py`, `interface/ui/bundle.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `pipeline/tagging.py`, `shared/field_map.py`, `shared/fields.py`, `shared/vocabulary.py` | fifteen test modules |
| `run.py` | `boundary/ollama.py`, `interface/cli.py`, `interface/run_view.py`, `interface/wiring.py`, `interface/ui/app.py`, `interface/ui/batch.py`, `shared/field_map.py`, and all five of `pipeline/` | eleven test modules |
| `flow.py` | `interface/cli.py`, `interface/run_view.py`, `interface/wiring.py`, `interface/ui/batch.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `shared/field_map.py`, `shared/fields.py` | seventeen test modules |

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
