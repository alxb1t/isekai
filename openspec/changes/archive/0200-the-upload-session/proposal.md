---
bump: patch
version: 0.88.10
after: [0199-the-review-parts]
---

# The upload session

The app's upload session, `Reader` and `Imports`, leaves `isekai/pipeline/importing.py` for `isekai/interface/ui/uploads.py`, which reads `importing` only through the module. The import stage keeps the read, the clean, the verify and the commit, and falls off the ratchet's long files.

Reading map: [design](design.md) holds the decisions and the names that move, [tasks](tasks.md) its phases: the copy, the readers, the delete, then the documents.

## Why

Only the app calls `Reader` and `Imports`, yet they sit in the stage's file, which the ratchet lists as long and which falls under its ceiling without them. Tests replace `importing.read` and `importing.commit` by name to inject a failure, so the session must keep reaching those names through the module. This version moves the session to the app and changes no behaviour.

## What Changes

- `isekai/interface/ui/uploads.py` is new. It holds `Reader`, `Imports` and the names only they read, unchanged, and reads `importing` only as `importing.<name>`. It imports no web framework.
- `isekai/pipeline/importing.py` loses those names and the imports they alone read. The stage's name rule and its lock become public, `refuse_name` and `CLAIM`, because the session reads both from another layer.
- `isekai/interface/ui/app.py` builds `uploads.Imports`, and `isekai/interface/ui/surface.py` names it in its annotation.
- The lines of `tests/test_importing.py` and `tests/test_ui_api.py` that read `Reader`, `Imports` or `tempfile` through `importing` read them through `uploads`. No assertion changes.
- The long-file row of `importing.py` goes from `tests/test_ratchets.py`. The standing mutants `PA-14` and `PA-15` take the path of `uploads.py`, their text unchanged.
- The pipeline and interface READMEs, the app's README, `docs/modules.md` and the derived tables name the new home.

No requirement is touched. Every message, record, event and byte stays, and `ui/src/wire.ts` does not change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

`isekai/pipeline/importing.py` shrinks to the stage; `isekai/interface/ui/uploads.py` arrives beside `isekai/interface/ui/surface.py`, and `isekai/interface/ui/app.py` and `isekai/interface/ui/surface.py` change an import and the name they read. `tests/test_importing.py` and `tests/test_ui_api.py` change import lines and the lines named above; `tests/test_ratchets.py` loses a row; `tests/mutants.json` re-points `PA-14` and `PA-15`. `isekai/pipeline/README.md`, `isekai/interface/README.md`, `isekai/interface/ui/README.md` and `docs/modules.md` name the new home, and `tests/test_docs.py` re-derives each *Imported by* table. No decision is added or amended.

## Not in this change

- `importing.staged_file`, `verify`, `preview`, `STAGING` and the rest of the stage: they stay where the tattoo and staging routes read them.
- A message, a state, a record or a parameter of the moved code, and `Upload` and `State`, which stay in `importing.py` so the page's file type keeps its module.
- A decision, a scenario, a spec delta, and any file under `ui/`, `tools/` or `evaluation/`.
- A new test, and a mutation run over the moved lines: the code moves as it is, and the standing mutants of the session replay on its new home.
