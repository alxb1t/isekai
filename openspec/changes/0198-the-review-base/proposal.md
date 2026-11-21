---
bump: patch
after: [0197-the-session-plan]
---

# The review base

`isekai/pipeline/review.py` becomes the package `isekai/pipeline/review/`. Its front door re-exports every name the module held; the draft's records and the token budget move into modules beside it.

Reading map: [design](design.md) holds the decisions and the names that move, [tasks](tasks.md) its phases: the package, the token budget, the records, then the decision and the documents.

## Why

`review.py` is a file the ratchet lists as long, and it holds the drafts, the approval and the cancel together. Each reads the same records and a set of shared helpers, so none can leave the file before those do. This version cuts the base the next version builds on, moves code and changes no behaviour.

## What Changes

- `isekai/pipeline/review.py` is `isekai/pipeline/review/__init__.py`. It re-exports every name the module held and defines `Status` as before, so no importer in `isekai/` and no import in `tests/` changes but the two that patch.
- `isekai/pipeline/review/records.py` is new. It holds `save_draft`, `_write_draft` and `_publish`, with the readers and helpers the stage's parts share.
- `isekai/pipeline/review/budget.py` is new. It holds `ENCODER_WINDOW`, `estimate_tokens`, `TokenBudget` and `token_budget`.
- `_write_draft` takes `renders`, `version` and `image` by keyword, and each caller says so. Its row among the wide functions goes.
- The tests that patch `create` and `write` import `isekai.pipeline.review.records`; the patched row of `tests/test_ratchets.py` is renamed, not added.
- The long-file and long-function rows are keyed to the front door. Each standing mutant of `review.py` is found in the module that now holds its text.
- `docs/decisions.md` gains D77. The pipeline README, `isekai/README.md` and the derived tables name the package.

No requirement is touched. The code moves as it is; every message, record and byte stays.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

`isekai/pipeline/review.py` leaves and `isekai/pipeline/review/` arrives. `tests/test_review.py` and `tests/test_ui_api.py` change an import and its uses, no assertion. `tests/test_ratchets.py`, `tests/test_artifact_bytes.py` and `tests/mutants.json` re-point rows that name the old path. `docs/decisions.md`, `isekai/pipeline/README.md`, `isekai/README.md` and the derived tables of the layer READMEs name the package; `tests/test_docs.py` re-derives each table and changes nothing, and `ui/src/wire.ts` does not change.

## Not in this change

- The parts: `drafts.py`, `approval.py` and `cancelling.py`. The drafts, the approval and the cancel stay in the front door, with `approve` at its length and `draft_across`'s positional parameters; they are the next version.
- `Status`: it stays defined in the front door, so the page's `ReviewStatus` keeps its name and `ui/src/wire.ts` does not change.
- The cleaner to `shared/`, and `Flow` passed whole: not taken.
- A scenario, a spec delta, and any file under `ui/`, `tools/` or `evaluation/`.
- A message, a record or a parameter of the moved code, but `_write_draft`'s three.
