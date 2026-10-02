# `evaluation/` — counting whether a render is its person

The cohort evaluator, beside the package it measures: `isekai` never imports it.
It ranks a cohort's photographs for each render and counts two hits beside chance.
It adds no package: `onnxruntime`, `numpy` and `Pillow` are already the pipeline's.

```
uv run python -m evaluation <batch>/runs --cohort <cohort>
        │
        ├─ cohort.py   load_cohort · rank · hits · chance · record · table
        ├─ face.py     Detector (YuNet) · align · Encoder (SFace) · embed
        └─ writes <batch>/evaluation.json, prints the table
```

## Files

| file | does |
|---|---|
| `__main__.py` | the command line: matches each run to its cohort photograph, embeds, ranks, writes the record |
| `cohort.py` | the cohort, the two counts, chance, the record and its table. Stdlib only |
| `face.py` | finds the face, aligns it to the template, embeds it; `python -m evaluation.face <image>…` probes the detector |
| `eval_models.py` | reads the evaluator's manifest, and names any entry whose destination or digest the graph's manifest also carries (D37) |
| `eval_models.json` | the evaluator's pinned manifest, derived by `tools/derive_eval_manifest.py` |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `evaluation/` | outside |
|---|---|---|
| `__main__.py` | — | `tests/test_evaluation_cli.py`, `tests/test_eval_manifest.py` |
| `cohort.py` | `__main__.py` | `tests/test_cohort.py`, `tests/test_evaluation_cli.py` |
| `face.py` | `__main__.py` | `tests/test_evaluation_cli.py`, `tests/test_face.py`, `tests/test_wd14.py` |
| `eval_models.py` | `__main__.py`, `face.py` | `tools/derive_eval_manifest.py`, `tests/test_eval_manifest.py`, `tests/test_evaluation_cli.py`, `tests/test_package_paths.py`, `tests/test_vocabulary_manifest.py` |

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../docs/decisions.md)'s; neither restates the other.
