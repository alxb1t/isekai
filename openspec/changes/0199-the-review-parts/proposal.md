---
bump: patch
after: [0198-the-review-base]
---

# The review parts

The drafts, the approval and the cancel leave the review stage's front door for `drafts.py`, `approval.py` and `cancelling.py` in `isekai/pipeline/review/`. `approve` is cut to 100 lines or fewer and `draft_across` takes `seed` by keyword, so the stage leaves the ratchet tables.

Reading map: [design](design.md) holds the decisions and the names that move, [tasks](tasks.md) its phases: the approval, the drafts, the cancel, then the decision and the documents.

## Why

[The review base](../0198-the-review-base/proposal.md) put the draft's records and the token budget beside the front door, so no part has to import another. The drafts, the approval and the cancel still share a file the ratchet lists as long, and `approve` and `draft_across` are listed offenders. This version cuts each part into its module and takes the rows out, and changes no behaviour.

## What Changes

- `isekai/pipeline/review/approval.py` is new. It holds `approve`, `_copy_approval`, `_refuse_unchanged`, `_resheet` and `_NOT_COPIED`, and imports `records.py` and `budget.py` and no other part.
- `isekai/pipeline/review/drafts.py` is new. It holds `review`, `revise`, `draft_from`, `drafting_sheet`, `drafting_approval`, `refuse_drafts`, `refuse_revision`, `waiting_edit`, `Revision` and their private helpers, and imports `records.py` and no other part.
- `isekai/pipeline/review/cancelling.py` is new. It holds `Cancelled`, `discard`, `cancellable`, `cancel` and their private helpers, and imports `records.py` and no other part.
- `isekai/pipeline/review/records.py` gains `DISCARD`, which each part reads.
- `isekai/pipeline/review/__init__.py` keeps the module docstring, `Status` and `state`, and re-exports every name an importer or a test reads.
- `approve` takes its over-window warning from a helper, `_window_warnings`, and is 100 lines or fewer. Its row among the long functions goes.
- `draft_across` in `isekai/interface/drafting.py` takes `seed` by keyword, and its one caller says so. Its row among the wide functions goes.
- The front door's row among the long files goes. `tests/test_ratchets.py` holds no row that names `isekai/pipeline/review`.
- The key of `BYTE_WRITERS` for a source image's copy names `drafts.py`. Each standing mutant of the front door is found in the module that now holds its text.
- D77 is amended in `docs/decisions.md`: its *Accepts* no longer lists the parts. The pipeline README and the derived tables name the modules.

No requirement is touched. The code moves as it is; every message, record and byte stays. The extracted warning keeps its lines and its order.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

`isekai/pipeline/review/__init__.py` shrinks to the front door; the parts arrive beside it. `isekai/interface/drafting.py` changes a signature and its call. `tests/test_ratchets.py`, `tests/test_artifact_bytes.py` and `tests/mutants.json` change keys, rows and paths; `tests/test_review.py` gains a case only for a survivor of the pre-flight; no test changes an assertion. `docs/decisions.md`, `isekai/pipeline/README.md` and the derived tables of the layer READMEs name the modules; `tests/test_docs.py` re-derives each table. `ui/src/wire.ts` does not change.

## Not in this change

- The upload session: `Reader` and `Imports` stay in `importing.py`; they are the next version.
- `Status`, `state`: they stay in the front door, so the page's `ReviewStatus` keeps its module and `ui/src/wire.ts` does not change.
- The cleaner to `shared/`, and `Flow` passed whole: not taken.
- A scenario, a spec delta, and any file under `ui/`, `tools/` or `evaluation/`.
- A message, a record or a parameter of the moved code, but `draft_across`'s `seed` being keyword-only.
