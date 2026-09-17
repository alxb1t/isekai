# `shared/` — primitives with no domain of their own

Used on both sides of the pipeline, and belonging to neither. Each one takes its
inputs and returns an answer; none of them reads a run, a flow or a score.

## Files

| file | does |
|---|---|
| `atomic_write.py` | writes bytes to a path, or writes nothing — temp-then-replace on one filesystem |
| `image.py` | reads a JPEG or PNG header and derives the render target the image's own dimensions imply |
| `vocabulary.py` | answers *is this a real tag*, *how strong is it*, *what does this phrase mean* |

## Imported by

| file | inside `isekai/` | outside |
|---|---|---|
| `atomic_write.py` | `foundation/run.py`, `pipeline/generate.py` | `tests/test_run_directory.py` |
| `image.py` | `evaluation/evaluate.py`, `pipeline/generate.py` | three test modules |
| `vocabulary.py` | `interface/wiring.py`, `pipeline/review.py`, `pipeline/sheet.py` | nine test modules |

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
