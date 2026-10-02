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

uv run python -m evaluation.recall <batch>/runs [<run>…]
        │
        ├─ recall.py   count · totals · record · table · the reader · the command
        ├─ record.py   destination: where a record goes, refused where git can reach
        └─ writes <batch>/recall.json, prints the table
```

Recall needs no cohort: it asks whether the hair, the eyes and the clothes the operator approved
survive into the picture, per scored field, naming each tag the tagger does not read back
([D39](../docs/decisions.md#d39--attribute-recall-uses-the-sheets-tagger)).

## The control arm

**The floor under the count: `summon` with the face chain at zero, on the same sheet and the same noise.**
Run it over a batch's runs after `summon` has rendered them:

```
uv run python -m isekai approve --runs <runs> --flow control-anime-wai --from summon-anime-wai <run>…
bash infra/render.sh <runs> control-anime-wai=summon-anime-wai
uv run python -m evaluation <runs> --cohort <cohort>
uv run python -m isekai compare <batch>
```

On a batch `summon` has not rendered, one session renders both, the source first:

```
bash infra/render.sh <runs> summon-anime-wai=1 control-anime-wai=summon-anime-wai
```

The control row is the floor; the difference from the `summon` row is the face mechanism's share.

## Files

| file | does |
|---|---|
| `__main__.py` | the command line: matches each run to its cohort photograph, embeds, ranks, writes the record |
| `cohort.py` | the cohort, the two counts, chance, the record and its table. Stdlib only |
| `face.py` | finds the face, aligns it to the template, embeds it; `python -m evaluation.face <image>…` probes the detector |
| `recall.py` | the recall count, its record and table, the reader over the pipeline's tagger, and the command: `python -m evaluation.recall` |
| `record.py` | `destination`: `<batch>/<name>`, refused where git can reach it; both commands call it |
| `eval_models.py` | reads the evaluator's manifest, and names any entry whose destination or digest the graph's manifest also carries (D37) |
| `eval_models.json` | the evaluator's pinned manifest, derived by `tools/derive_eval_manifest.py` |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `evaluation/` | outside |
|---|---|---|
| `__main__.py` | — | `tests/test_evaluation_cli.py`, `tests/test_eval_manifest.py` |
| `recall.py` | — | `tests/test_recall.py`, `tests/test_recall_cli.py` |
| `record.py` | `__main__.py`, `recall.py` | — |
| `cohort.py` | `__main__.py` | `tests/test_cohort.py`, `tests/test_evaluation_cli.py` |
| `face.py` | `__main__.py` | `tests/test_evaluation_cli.py`, `tests/test_face.py`, `tests/test_wd14.py` |
| `eval_models.py` | `__main__.py`, `face.py` | `tools/derive_eval_manifest.py`, `tests/test_eval_manifest.py`, `tests/test_evaluation_cli.py`, `tests/test_package_paths.py`, `tests/test_vocabulary_manifest.py` |

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../docs/decisions.md)'s; neither restates the other.
