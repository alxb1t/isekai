---
bump: patch
---

# The library's names

Move the collection's names and the session's read side into `isekai/foundation/library.py`, each re-bound at its old home; behaviour unchanged.

Reading map: [design](design.md) holds the home, the re-binds and the proof, [tasks](tasks.md) its phases.

## Why

`ui/library.py` reads `SOURCES` from the importer and `record_running` from the render verb, so nothing below the interface can meet a collection. The foundation imports nothing above it, so the names move down to it ([docs D68](../../../docs/decisions.md), added here). The change only moves: no importer and no test changes.

## What Changes

```
1 · the collection   the five constants, SOURCES, root, is_collection, listed and collection
                     -> foundation/library.py; re-bound in ui/library.py, importing.py and,
                     as COLLECTION_RUNS and COLLECTION_PHOTOS, compare_view.py
2 · the session      UNSUPPORTED, record_running, running, render_running, session and _session
                     -> foundation/library.py; re-bound in render.py and ui/library.py
3 · the documents    D68, the interface README's row, the foundation's role line
```

- `isekai/foundation/library.py` is new; `ui/library.py` ends near 804 lines and keeps its ratchet row.
- `ui/library.py` no longer imports the render verb; `render.py` no longer imports `errno`.
- The foundation README gains a *Files* row and an *Imported by* row; the derived tables are re-derived.

## Capabilities

### New Capabilities

None. A move of code under test touches no requirement, so the change carries `skip_specs`.

### Modified Capabilities

None.

## Impact

- Code: `isekai/foundation/library.py` (new), `isekai/interface/ui/library.py`, `isekai/interface/render.py`, `isekai/interface/compare_view.py`, `isekai/pipeline/importing.py`.
- Documents: `docs/decisions.md`, `isekai/foundation/README.md`, `isekai/interface/README.md`, `ARCHITECTURE.md`, `docs/principles.md`, and the derived tables of the layer READMEs.
- No test, browser or tool file changes.

## Not in this change

- `Record`, `open_library` and `collection_runs`.
- The CLI's imports of the UI package, for `collection_runs`, `serve` and `drop_thumbnails`.
- `STAGING` and the `"log.txt"` literal.
- The hand copies of `is_collection`'s test, in the importer and the library verb.
- A rename of `SOURCES` or `RUNS`.
- A further move to bring `ui/library.py` under 800 lines.
- `isekai/README.md`'s file list.
- Any test, browser or tool file.
