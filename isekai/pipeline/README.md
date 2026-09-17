# `pipeline/` — the four staged verbs

One file per stage, in the order a photograph passes through them. No stage reads
another's output directly: each is handed a path inside a run and hands back a
numbered artifact. Exactly one stage imports another — `review.py` calls
`sheet.py`'s `validate`, which is behaviour rather than layout.

## Files

| file | does | costs |
|---|---|---|
| `caption.py` | ① turns a photograph into descriptive prose | a model call |
| `sheet.py` | ② sorts prose into a schema's fields | a model call |
| `review.py` | ③ copies a sheet somewhere a human may correct it, then approves it | a human — the largest measured gain in the pipeline |
| `generate.py` | ④ assembles every prompt locally, then renders each against an endpoint | free, then **money** |

## Imported by

| file | inside `isekai/` | outside |
|---|---|---|
| `caption.py` | `interface/cli.py`, `interface/wiring.py` | six test modules |
| `sheet.py` | `interface/cli.py`, `interface/wiring.py`, `review.py` | nine test modules |
| `review.py` | `interface/cli.py` | four test modules |
| `generate.py` | `interface/cli.py`, `interface/run_view.py` | three test modules |

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
