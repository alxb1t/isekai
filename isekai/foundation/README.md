# `foundation/` — what a run, a flow and a refusal are

The types every other group is built on. Nothing here knows about a stage, an
endpoint or a score; everything here is imported by something that does.

## Files

| file | does |
|---|---|
| `refusal.py` | one error that names its own fix, raised anywhere and caught once |
| `run.py` | the run directory: ids, the frame, the input-above-flow-below layout and its names, numbering, approval, budgets, and the JSON form every artifact is written in |
| `flow.py` | reads and validates a frozen flow directory of five flat files, lists what is tracked, and owns the `Schema` type and prompt assembly |

## Imported by

| file | inside `isekai/` | outside |
|---|---|---|
| `refusal.py` | `boundary/claude_cli.py`, `evaluation/evaluate.py`, `flow.py`, `run.py`, `interface/cli.py`, `interface/wiring.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `shared/fields.py`, `shared/vocabulary.py` | ten test modules |
| `run.py` | `boundary/claude_cli.py`, `interface/cli.py`, `interface/run_view.py`, `interface/wiring.py`, and all four of `pipeline/` | ten test modules |
| `flow.py` | `interface/cli.py`, `interface/run_view.py`, `interface/wiring.py`, `pipeline/generate.py`, `pipeline/review.py`, `pipeline/sheet.py`, `shared/fields.py` | twelve test modules |

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
