---
bump: patch
version: 0.87.40
after: [0183-the-stage-record]
---

# The evaluator seams

The evaluator's entry points and its encoder take their collaborators as arguments, so the evaluator's modules leave the patched-modules table of the ratchet.

Reading map: [design](design.md) holds the signatures and the test cost, [tasks](tasks.md) holds a phase for each seam.

## Why

`tests/test_ratchets.py` lists each module whose own names a test patches, and [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets) says a row goes with its offender. The rows of `evaluation.__main__`, `evaluation.recall` and `evaluation.eval_models` stand over a few product lines, all under `evaluation/`. A collaborator passed as an argument needs no patch, so each row is paid by one default parameter and a test that passes its fake.

## What Changes

- `main(argv, *, embedder=)` in `evaluation/__main__.py`, defaulting to `_embedder`. The tests that patched `_embedder` pass a fake embedder.
- `main(argv, *, reader=)` in `evaluation/recall.py`, defaulting to `_reader`. The tests that patched `_reader` pass a fake reader.
- `_embedder(models, *, manifest=)` in `evaluation/__main__.py`, defaulting to the tracked eval manifest. The tests that patched `load_eval_manifest` pass the manifest they built.
- The rows of `evaluation.__main__`, `evaluation.recall` and `evaluation.eval_models` leave `PATCHED_MODULES`, and `PATCHED_ROWS` is set to 21.

Every printed line, record and exit code is unchanged, and no test's assertion changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement changes, so the change carries `skip_specs: true`.

## Impact

- `evaluation/__main__.py` and `evaluation/recall.py`: a parameter each, and the line of each body that calls it.
- `tests/test_evaluation_cli.py`, `tests/test_recall_cli.py` and `tests/test_eval_manifest.py`: a fake passed where a patch stood.
- `tests/test_ratchets.py`: the rows of the evaluator's modules and the row ceiling.

## Not in this change

- The other patched rows, which later versions of the series pay or name in the stage principle's *Known breaks*.
- The ratchet's sight: how it finds a patch stays as it is.
- Any change to what `evaluation/` prints, writes or refuses.
- A file under the product's package, the page or the tools, and a decision.
