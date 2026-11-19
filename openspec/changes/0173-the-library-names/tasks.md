# The library's names — tasks

Each phase moves names into `isekai/foundation/library.py` and ends green; the code is verbatim, per [design](design.md).

## Progress

- [x] 1 — The collection · moderate
- [ ] 2 — The session · moderate
- [ ] 3 — The documents · moderate

## 1 — The collection

- [x] 1.1 Create `isekai/foundation/library.py` per [D1](design.md#d1) and [D3](design.md#d3): the constants `VARIABLE`, `DEFAULT`, `RUNS`, `LOG`, `CACHE` of `isekai/interface/ui/library.py:80-85` with the cache comment, `SOURCES` of `isekai/pipeline/importing.py:44`, and `root`, `is_collection`, `listed`, `collection` verbatim. Import `os`, `Mapping`, `Path` and `Refusal` for them. The docstring says `RUNS` is a collection's runs root, `SOURCES` its photographs' folder, and `names.py`'s `SOURCES` a flow's.
  Verify: `uv run python -c "from isekai.foundation.library import CACHE, DEFAULT, LOG, RUNS, SOURCES, VARIABLE, collection, is_collection, listed, root"` exits 0.
- [x] 1.2 In `isekai/interface/ui/library.py`, delete those constants and `root`, `is_collection`, `listed` and `collection`, and import them from `isekai.foundation.library` per [D2](design.md#d2): `CACHE`, `RUNS`, `SOURCES`, `VARIABLE`, `is_collection`, `listed` plain; `DEFAULT`, `LOG`, `root`, `collection` as `X as X`. Narrow `from isekai.pipeline.importing import SOURCES, UI_CONFIG` to `UI_CONFIG`. Order the imports with `uv run ruff check --fix isekai/interface/ui/library.py`; `import os` stays, read by `os.walk`.
  Verify: `git grep -n -e "^def root" -e "^def is_collection" -e "^def listed" -e "^def collection" -- isekai/interface/ui/library.py` prints nothing, and `uv run pytest tests/test_ui_library.py tests/test_ui.py` exits 0.
- [x] 1.3 In `isekai/pipeline/importing.py`, delete `SOURCES = "sources"` (line 44) and import `SOURCES` plain from `isekai.foundation.library`, in the foundation block between `atomic_write` and `refusal`; `uv run ruff check --fix isekai/pipeline/importing.py` orders it.
  Verify: `git grep -n -F 'SOURCES = "sources"' -- isekai/pipeline/importing.py` prints nothing, and `uv run pytest tests/test_importing.py` exits 0.
- [x] 1.4 In `isekai/interface/compare_view.py`, delete `COLLECTION_RUNS = "runs"`, the comment citing D40 and `COLLECTION_PHOTOS = "sources"` (lines 38-41); import `RUNS as COLLECTION_RUNS` and `SOURCES as COLLECTION_PHOTOS` from `isekai.foundation.library` ([D3](design.md#d3)); `uv run ruff check --fix isekai/interface/compare_view.py` orders them.
  Verify: `git grep -n -F 'COLLECTION_PHOTOS = "sources"' -- isekai/interface/compare_view.py` prints nothing, and `uv run pytest tests/test_compare.py tests/test_render.py` exits 0.
- [x] 1.5 In `isekai/foundation/README.md`, add after the `atomic_write.py` row of *Files* the row ``| `library.py` | the library's folder names and a collection's, `root`, `is_collection`, `listed` and `collection` |``, and after the last row of *Imported by* the row ``| `library.py` | — | — |``. Then run `uv run python -m tools.derive_imported_by`, which fills it and every other layer README's derived rows.
  Verify: `git grep -n -E "^. .library\.py. " -- isekai/foundation/README.md` prints `2`, and `uv run pytest tests/test_docs.py tests/test_layers.py tests/test_ratchets.py tests/test_pipeline_cli.py` exits 0.

## 2 — The session

- [ ] 2.1 In `isekai/foundation/library.py`, after `collection`, add `UNSUPPORTED` with its comment (`isekai/interface/render.py:248-251`), `record_running` (`:254-274`), then `running`, `render_running`, `session` and `_session` (`isekai/interface/ui/library.py:306-351`), verbatim, in that order ([D1](design.md#d1)). Import `contextlib`, `errno`, `fcntl`, `Any`, `Run` from `isekai.foundation.run`, and `SESSION_FILE`, `SESSION_ID`, `SESSIONS`, `SessionRecord`, `read` from `isekai.foundation.artifacts`. Keep `fcntl.flock(held, fcntl.LOCK_SH | fcntl.LOCK_NB)` ([D4](design.md#d4)).
  Verify: `git grep -n -e "^def record_running" -e "^def running" -e "^def render_running" -e "^def session" -e "^def _session" -- isekai/foundation/library.py` prints `5`, `git grep -n -F "from fcntl import" -- isekai/foundation/library.py` prints nothing, and `git grep -n -F "fcntl.flock(" -- isekai/foundation/library.py` prints `1`.
- [ ] 2.2 In `isekai/interface/render.py`, delete the `UNSUPPORTED` block and `record_running`, and `import errno` (line 24); keep `import fcntl`. Import `UNSUPPORTED` plain and `record_running as record_running` from `isekai.foundation.library` ([D2](design.md#d2), [D4](design.md#d4)); `uv run ruff check --fix isekai/interface/render.py` orders them.
  Verify: `git grep -n -F "import errno" -- isekai/interface/render.py` prints nothing, `git grep -n -e "^def record_running" -e "^UNSUPPORTED" -- isekai/interface/render.py` prints nothing, and `uv run pytest tests/test_render.py` exits 0.
- [ ] 2.3 In `isekai/interface/ui/library.py`, delete `running`, `render_running`, `session`, `_session` and the import `from isekai.interface.render import record_running`; import `running`, `render_running` and `session` from `isekai.foundation.library` as `X as X`, and drop the artifacts imports `SESSION_FILE`, `SESSION_ID`, `SESSIONS` and `SessionRecord` that nothing reads. Run `uv run ruff check --fix isekai/interface/ui/library.py` for the order and any other unread import.
  Verify: `git grep -n -e "^def running" -e "^def render_running" -e "^def session" -e "^def _session" -e "isekai.interface.render" -- isekai/interface/ui/library.py` prints nothing, and `uv run pytest tests/test_ui_library.py tests/test_ui.py tests/test_ui_api.py` exits 0.
- [ ] 2.4 **HALT CHECK** — `isekai/interface/ui/library.py` still measures more than 800 lines, so its row in the long files' ratchet, which this change leaves as it stands, holds ([D5](design.md#d5)). Move nothing more to pass under: a red ratchet here means the plan is wrong.
  Verify: `uv run pytest tests/test_ratchets.py -k test_no_long_file_is_unlisted` exits 0.
- [ ] 2.5 In `isekai/foundation/README.md`, extend the `library.py` row of *Files* with ``, and the read side of a collection's session records: `UNSUPPORTED`, `record_running`, `running`, `render_running` and `session` ``; run `uv run python -m tools.derive_imported_by`. The `render.py` row of `isekai/interface/README.md` loses `ui/library.py`.
  Verify: `git grep -n -E "^. .render\.py. .*ui/library\.py" -- isekai/interface/README.md` prints nothing, and `uv run pytest tests/test_docs.py tests/test_layers.py tests/test_pipeline_cli.py tests/test_spec_bindings.py` exits 0.

## 3 — The documents

- [ ] 3.1 In `docs/decisions.md`, add D68 after D67's `Made by` line and before `## Infrastructure`, as [D8](design.md#d8) gives it.
  Verify: `git grep -n -F "### D68" -- docs/decisions.md` prints `1`.
- [ ] 3.2 In `isekai/interface/README.md`, in the `ui/library.py` row, replace ``each approval's rendered seeds, each collection's session records, and the thumbnails in the library's `.cache/`.`` with ``each approval's rendered seeds and the thumbnails in the library's `.cache/`; the collection's names and its session records' read side are `foundation/library.py`'s, re-bound here (D68).``
  Verify: `git grep -n -F "foundation/library.py" -- isekai/interface/README.md` prints `1`.
- [ ] 3.3 In `ARCHITECTURE.md` and `docs/principles.md`, change the foundation line's `the migration and the command text a refusal prints.` to `the migration, the command text a refusal prints, and the library's collection names and its session records' read side.`
  Verify: `git grep -n -F "the library's collection names" -- ARCHITECTURE.md docs/principles.md` prints `2`.
- [ ] 3.4 Replay the standing mutants once over the moved code ([D7](design.md#d7)).
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
