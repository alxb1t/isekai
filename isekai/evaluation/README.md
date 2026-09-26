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
| `eval_models.py` | reads the scorer's manifest, and proves it has not drifted from the graph's; `boundary/provision.py` verifies the bytes |
| `labels.py` | collects the operator's blind judgement and correlates a metric against it |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `evaluate.py` | `eval_backends.py` | `../../evaluate.py`, `tests/eval_fakes.py`, `tests/test_evaluate.py` |
| `eval_backends.py` | — | `../../evaluate.py` |
| `ciede2000.py` | `eval_backends.py`, `evaluate.py` | `tests/eval_fakes.py`, `tests/test_ciede2000.py` |
| `eval_models.py` | `eval_backends.py` | `tools/derive_eval_manifest.py`, `tests/test_eval_manifest.py`, `tests/test_package_paths.py`, `tests/test_vocabulary_manifest.py` |
| `labels.py` | — | `tests/test_labels.py` |

> `eval_backends.py` has **no test importer** and `pyproject.toml`'s
> `unresolved-import` override blinds `ty` to its first-party imports, so no gate
> command reads them. **That debt is open and unpaid**, and naming a version that
> would pay it has not worked: it was written against v0.19 and has outlasted
> three releases since. It is in the backlog, not in a sentence here.

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
