# `evaluation/` — scoring a render against its photograph

A real install boundary as well as a filing one: `eval_backends.py` is the only
module in the tree that imports the `[eval]` extra, and it is imported lazily.
Everything the scorer *decides* is stdlib-only and is tested in CI with the stack
absent.

## Files

| file | does |
|---|---|
| `evaluate.py` | what a score is and when one may not be claimed — the axes, the guards, the cohort question, the report. Stdlib only |
| `eval_backends.py` | the real models behind the seams: detect, parse, encode, sample, read pose. The only importer of the optional extra |
| `ciede2000.py` | one absolute colour distance — the only axis that means the same thing in a photograph and a drawing |
| `eval_models.py` | proves the scorer's models are the bytes that were pinned, and that they have not drifted from the graph's manifest |
| `labels.py` | collects the operator's blind judgement and correlates a metric against it |

## Imported by

| file | inside `isekai/` | outside |
|---|---|---|
| `evaluate.py` | `eval_backends.py` | `../../evaluate.py`, `tests/eval_fakes.py`, `tests/test_evaluate.py` |
| `eval_backends.py` | — | `../../evaluate.py` only |
| `ciede2000.py` | `eval_backends.py`, `evaluate.py` | `tests/eval_fakes.py`, `tests/test_ciede2000.py` |
| `eval_models.py` | `eval_backends.py`, `shared/vocabulary.py` | `scripts/derive_eval_manifest.py`, two test modules |
| `labels.py` | — | `tests/test_labels.py` |

> `eval_backends.py` has **no test importer** and `pyproject.toml`'s
> `unresolved-import` override blinds `ty` to its first-party imports, so no gate
> command reads them. v0.19 owes either coverage or a narrower override.

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
