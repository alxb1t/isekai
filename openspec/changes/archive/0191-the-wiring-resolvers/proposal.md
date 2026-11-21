---
bump: patch
version: 0.88.1
after: [0190-the-terminal-guards]
---

# The wiring's resolvers

What a test replaces in the wiring becomes a keyword, each defaulting to today's name, and the wiring's row leaves the patch ratchet.

Reading map: [design](design.md) holds the resolvers and the tests' arrangements, [tasks](tasks.md) its phases.

## Why

`PATCHED_MODULES` of `tests/test_ratchets.py` lists `isekai.interface.wiring`, and patches of its names stand in the tests of the proposer, the evaluators, the tagging and the pipeline's CLI. A patch of a module's name is global state: it breaks the principle that a component is a contract, and it strands silently when the reading code moves. Each patch here replaces a collaborator the wiring resolves, so each is a parameter.

The row empties only when every kind of patch goes: the proposer's cache and its openers, the roots `trackable` reads, the local tagger's opener and the caption config's loader. None is a behaviour change: each keyword defaults to the name the product reads today.

## What Changes

- `isekai/interface/wiring.py` holds the proposer's cache as `Proposers`, an object with `open_pose`, `open_segmenter` and the lock, and one default instance, `PROPOSERS`; `proposer_for` reads it and the module global `_proposer` goes.
- `trackable` takes `repository=` and `data_root=`; `destination` of `evaluation/record.py` and the `main` of `evaluation/__main__.py` and of `evaluation/recall.py` pass them on.
- `tagger_for` takes `open_session=`; `reader_for` and `hosted_tagger_for` take `config=`, a loader.
- Each test that patched one of these passes it instead; no assertion changes, and the autouse reset fixture of `tests/test_propose.py` goes.
- The wiring's row leaves `PATCHED_MODULES`, and `PATCHED_ROWS` is 18.
- A case holds that the default cache opens the boundary's openers.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change carries `skip_specs: true`: no requirement's text changes and none is added.

## Impact

- Code: `isekai/interface/wiring.py`, `evaluation/record.py`, `evaluation/__main__.py`, `evaluation/recall.py`.
- Tests: `tests/test_propose.py`, `tests/test_evaluation_cli.py`, `tests/test_recall_cli.py`, `tests/test_tagging.py`, `tests/test_pipeline_cli.py`, `tests/test_ratchets.py`.
- Docs: none but the changelog entry the build writes. No decision is added or amended.
- No format version moves, no printed text changes, no flow is re-pinned.

## Not in this change

- `isekai/interface/ui/routes/place.py`: the placement routes read the proposer through `Wiring` and stay as they are.
- `Wiring` grouped into parts: it removes no row.
- The model openers' `manifest=` keyword and `unpack`'s row: they wait for *the model manifests*.
- Any file under `ui/` or `tools/`.
