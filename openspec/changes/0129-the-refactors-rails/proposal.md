---
bump: patch
after: [0128-the-guards-hold]
---

# The refactor's rails

The gate learns the rules the refactor will lean on: a stage may be a package, size and patches are held by ratchets, the importer tables are derived, and the frozen files and the documents say what is true.

Reading map: [design](design.md) holds the decisions, the tables the phases read and the cost of the tests, [tasks](tasks.md) the stage rule, the ratchets, the importer tables, then the frozen files and the documents.

## Why

The refactor that follows moves stages into packages, splits the largest files and removes patched globals. The gate holds none of that today: a guard reads a stage as any file under `pipeline/`, nothing holds a file's size or a test's patch of a module's own names, and the READMEs' importer tables are hand-kept and short. The documents also say things the code no longer does.

```
today                                      after

stage = any file under pipeline/           stage = first segment under isekai.pipeline
size and patches: no rule                  a table of offenders and a ceiling each
Imported by: hand-kept, and short          derived from the layer guards' graph, re-derived by a test
```

## What Changes

Edits to tests, tools and documents. No `.py` under `isekai/` or `evaluation/` moves.

- `tests/test_layers.py` reads a stage as the first segment under `isekai.pipeline`, with twins; the principle says so and D55 records it.
- `tests/test_ratchets.py` holds a file's lines, a function's lines, a function's positional parameters, a `ui/src` file's lines and the patches of a module's own names, each as a table of listed offenders and a ceiling, each with its twin; D56 records the rule.
- The graph functions of `tests/test_layers.py` move to `tools/import_graph.py`, and `tools/derive_imported_by.py` writes each README's *Imported by* table from them. `tests/test_docs.py` re-derives each table, and the tests column and the route list go.
- `AGENTS.md` names the files the pod image freezes, a test holds that list equal to the image record's, and the record's failure says the recipe.
- `docs/principles.md`'s *Known breaks* name what the audit found and the page left out.
- The stale claims in `ARCHITECTURE.md`, `docs/principles.md`, `docs/modules.md`, `isekai/interface/README.md`, `docs/pins.md` and `tools/manifest.py` are corrected.

No requirement is touched, so the delta is empty and `.openspec.yaml` carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Guards edited, with their twins: `tests/test_layers.py`, `tests/test_docs.py` and `tests/test_infra.py`.
- Added: `tests/test_ratchets.py`, `tools/import_graph.py` and `tools/derive_imported_by.py`; the `derive` recipe of `Makefile` runs the second.
- Rewritten by the deriver: the *Imported by* tables of `isekai/foundation/README.md`, `isekai/shared/README.md`, `isekai/boundary/README.md`, `isekai/pipeline/README.md`, `isekai/interface/README.md` and `evaluation/README.md`.
- Documents edited: `docs/principles.md`, `docs/decisions.md` (D55, D56), `docs/modules.md`, `docs/pins.md` (it gains `tools/derive_eval_manifest.py` and `evaluation/eval_models.json`), `ARCHITECTURE.md`, `AGENTS.md` and `isekai/interface/README.md`; `tools/manifest.py`'s docstring is corrected.
- Read and not edited: `config/image.json`, the image-frozen files it names, and `ui/src`, which a ratchet scans.
- No format version moves, no verb or flag is deprecated, and the product is the same for the same inputs, so the change meets each condition of a patch in [CONTRIBUTING.md](../../../CONTRIBUTING.md).
- No dependency is added.

## Not in this change

- A product file moved to meet a ratchet: each listed offender stays until the refactor version that removes it.
- The record of whole outputs and the mutation runner: the next versions of this series.
- The mis-bound scenarios — the *spec audit* — and the tattoo screens' browser tests — *e2e tattoo*.
- Stale claims in product comments and the image-frozen `Dockerfile`: the refactor version that edits each file.
- A row for each module a README's *Files* table leaves out: the deriver writes the rows it is given.
