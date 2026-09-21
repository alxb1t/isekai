# `pipeline/` — the four staged verbs, and one module that is not one

One file per stage, in the order a photograph passes through them. No stage reads
another's output directly: each is handed a path inside a run and hands back a
numbered artifact, and **no stage imports another** — the last such edge closed
when `validate` moved to `shared/fields.py`. Every stage is per flow: the flow
supplies the briefing it reads, the schema it fills against and the directory it
writes into.

**`tagging.py` is the fifth file and not a fifth verb.** Its two functions write
the two tag artifacts `caption` also produces, in the same invocation and under
the same flow — so the count of *verbs* stays four while the count of files here
is five. It sits beside `caption.py` rather than inside it because `caption()`
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

| file | inside `isekai/` | outside |
|---|---|---|
| `caption.py` | `interface/cli.py`, `interface/wiring.py` | nine test modules |
| `tagging.py` | `interface/cli.py`, `interface/wiring.py` | six test modules |
| `sheet.py` | `interface/cli.py` | `tests/stages.py`, which every other module reaches it through |
| `review.py` | `interface/cli.py` | five test modules |
| `generate.py` | `interface/cli.py`, `interface/run_view.py` | four test modules |

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
