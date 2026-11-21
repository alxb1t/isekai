# The upload session — tasks

Move `Reader` and `Imports` from `isekai/pipeline/importing.py` to `isekai/interface/ui/uploads.py`, which reads the stage only as `importing.<name>`, and take the stage's row out of the long files. No moved line changes but the reads of [D1](design.md#d1).

## Progress

- [x] 1 — The session in its new module · moderate
- [x] 2 — The readers · moderate
- [x] 3 — The old session leaves the stage · moderate
- [x] 4 — The documents · moderate

## 1 — The session in its new module

- [x] 1.1 In `isekai/pipeline/importing.py` rename `_refuse_name` and `_CLAIM` to the new public names `refuse_name` and `CLAIM`, at each definition and each read in the file ([D2](design.md#d2)). Body, docstring and the comment over the lock stay.
  Verify: `git grep -n -w -e "_refuse_name" -e "_CLAIM" -- isekai/pipeline/importing.py` prints nothing.
- [x] 1.2 Create `isekai/interface/ui/uploads.py` with the docstring and imports of [D1](design.md#d1), the stage imported as `from isekai.pipeline import importing`: the docstring says it holds the upload session, `Reader` for one open import's uploads and `Imports` for each open import of a library, that both call the stage only as `importing.<name>` so a test that replaces `importing.read` or `importing.commit` reaches them, and that it imports no web framework. Run `git add isekai/interface/ui/uploads.py`: `tools.mutate` copies tracked files only.
  Verify: `uv run python -c "import isekai.interface.ui.uploads"` exits 0.
- [x] 1.3 Copy from `isekai/pipeline/importing.py` into `uploads.py`, in the order of their lines, unchanged with their docstrings and comments: `_record`, `Reader`, `_UNREAD` and `_STAGED` with their comments, `_closed`, `_failed`, `Imports` ([D1](design.md#d1)). Leave them in `importing.py` until phase 3 ([D4](design.md#d4)).
  Verify: `grep -n -e "^class Reader" -e "^class Imports" isekai/interface/ui/uploads.py` prints two lines.
- [x] 1.4 In the new `uploads.py` make each edit of the table in [D1](design.md#d1), and none else: the old private names become `importing.refuse_name(` and `importing.CLAIM`, `Upload` becomes `importing.Upload`, and the calls of `read`, `stage`, `commit` and `cancel`, and the return type `Committed`, take `importing.`.
  Verify: `grep -n -e "staged = read(" -e "folder = stage(" -e "done = commit(" -e "^        cancel(" -e "state: Upload" -e "_refuse_name" -e "_CLAIM" isekai/interface/ui/uploads.py` prints nothing.
- [x] 1.5 **HALT CHECK** Run `uv run ruff format isekai/interface/ui/uploads.py`, then `uv run ruff check isekai/interface/ui/uploads.py`. It holds no undefined and no unused name: a failure names a name of `importing.py` that [D1](design.md#d1) does not list, or an import it does not need, and the plan is wrong.
  Verify: `uv run ruff check isekai/interface/ui/uploads.py` exits 0.
- [x] 1.6 `uploads.py` binds no name of the stage by `from … import`.
  Verify: `grep -n -e "from isekai.pipeline.importing import" -e "^import isekai" isekai/interface/ui/uploads.py` prints nothing.
- [x] 1.7 Run `uv run python -m tools.derive_imported_by`: `uploads.py` imports `importing.py` and the refusal, so the derived tables of the layer READMEs change.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 1.8 Confirm the stage still holds, its own classes still in it.
  Verify: `uv run pytest tests/test_importing.py tests/test_ui_api.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py` exits 0.

## 2 — The readers

- [x] 2.1 In `isekai/interface/ui/app.py` change `from isekai.interface.ui import events` to import `uploads` after `events`, and build `imports = uploads.Imports(` where `importing.Imports(` is. Its arguments and `importing.upload_limit()` stay, so the `importing` import stays.
  Verify: `git grep -n -F "uploads.Imports(" -- isekai/interface/ui/app.py` prints one line.
- [x] 2.2 In `isekai/interface/ui/surface.py` import `uploads` after `library` in `from isekai.interface.ui import events, library`, annotate `imports: uploads.Imports`, and delete `from isekai.pipeline import importing`.
  Verify: `git grep -n -w "importing" -- isekai/interface/ui/surface.py` prints nothing.
- [x] 2.3 In `tests/test_importing.py` add `from isekai.interface.ui import uploads` after the `isekai.interface.cli` import. Every line that reads `importing.Reader`, `importing.Imports` or `importing.tempfile` reads `uploads` in its place ([D3](design.md#d3)). Every other line stays, `importing.commit`, `importing._clean` and `importing.os` included.
  Verify: `git grep -n -e "importing.Reader" -e "importing.Imports" -e "importing.tempfile" -- tests/test_importing.py` prints nothing.
- [x] 2.4 In `tests/test_ui_api.py` add `import isekai.interface.ui.uploads as uploads_module  # noqa: E402` after the `app_module` import. The line that patches `Reader.put` and the line that notes `Imports.close` read `uploads_module` where they read `importing_module` ([D3](design.md#d3)).
  Verify: `git grep -n -e "importing_module.Reader" -e "importing_module.Imports" -- tests/test_ui_api.py` prints nothing.
- [x] 2.5 Run `uv run ruff format` and `uv run ruff check --fix` on `isekai/interface/ui/app.py`, `isekai/interface/ui/surface.py`, `tests/test_importing.py` and `tests/test_ui_api.py`, which sort the new imports.
  Verify: `uv run ruff check isekai/interface/ui/app.py isekai/interface/ui/surface.py tests/test_importing.py tests/test_ui_api.py` exits 0.
- [x] 2.6 In `tests/mutants.json` set `path` in `PA-14` and in `PA-15` so each holds `"path": "isekai/interface/ui/uploads.py"` ([D6](design.md#d6)). Their `find`, `replace`, `tests` and `why` stay.
  Verify: `git grep -n -F '"path": "isekai/interface/ui/uploads.py"' -- tests/mutants.json` prints two lines.
- [x] 2.7 Run `uv run python -m tools.derive_imported_by`: the app and the surface import `uploads.py`, and the surface no longer imports `importing.py`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 2.8 **HALT CHECK** The injected failures still reach the session: the test that replaces `importing.read` and the test that replaces `importing.commit` hold with the app and the tests on the new classes. A failure means a read in `uploads.py` binds a name the plan reads through the module.
  Verify: `uv run pytest tests/test_importing.py tests/test_ui_api.py tests/test_ui.py tests/test_layers.py tests/test_ratchets.py tests/test_docs.py tests/test_derive_wire.py` exits 0.
- [x] 2.9 Replay the mutants the repository keeps, `PA-14` and `PA-15` on `uploads.py`.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

## 3 — The old session leaves the stage

- [x] 3.1 Delete from `isekai/pipeline/importing.py`, with their comments: `_record`, `Reader`, `_UNREAD`, `_STAGED`, `_closed`, `_failed` and `Imports`. Leave every other line.
  Verify: `git grep -n -e "^class Reader" -e "^class Imports" -e "^def _record" -- isekai/pipeline/importing.py` prints nothing.
- [x] 3.2 Run `uv run ruff check isekai/pipeline/importing.py`: it names each import no code of the file reads. Delete each by hand: `queue`, `tempfile`, `Callable`, `Mapping` and `Any`. Then run `uv run ruff format isekai/pipeline/importing.py`.
  Verify: `uv run ruff check isekai/pipeline/importing.py` exits 0.
- [x] 3.3 In the module docstring of `isekai/pipeline/importing.py` delete the sentence that begins "An upload waits in the folder" and ends "one file at a time."
  Verify: `git grep -n -e "An upload waits in the folder" -- isekai/pipeline/importing.py` prints nothing.
- [x] 3.4 In the same docstring, on its own line after the sentence that ends "deletes what was staged.", add the sentence "The upload session over it, the reader and the open imports, is the app's:" with `isekai/interface/ui/uploads.py.` as the start of the next line.
  Verify: `git grep -n -F "is the app's" -- isekai/pipeline/importing.py` prints one line.
- [x] 3.5 In `tests/test_ratchets.py` delete the `LONG_FILES` row `isekai/pipeline/importing.py` and set `FILE_ROWS` to the rows left ([D5](design.md#d5)). `PATCHED_MODULES` stays.
  Verify: `git grep -n -F "isekai/pipeline/importing.py" -- tests/test_ratchets.py` prints nothing.
- [x] 3.6 **HALT CHECK** The stage is under the long-file ceiling and no table holds a stale row. A failure means the delete differs from what the plan names.
  Verify: `uv run pytest tests/test_ratchets.py tests/test_layers.py` exits 0.
- [x] 3.7 Run `uv run python -m tools.derive_imported_by` once more: the delete changes no import of `isekai` in `importing.py`, so the tables stay as the second phase wrote them.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 3.8 Replay the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [x] 3.9 Confirm the suite on the stage alone.
  Verify: `uv run pytest tests/test_importing.py tests/test_ui_api.py tests/test_ui.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py tests/test_derive_wire.py` exits 0.

## 4 — The documents

- [x] 4.1 In `isekai/pipeline/README.md` replace the *Files* row of `importing.py` with ``| `importing.py` | reads a file into staging, cleans it to its pixels and orientation, verifies it, previews it, and commits the collection's `sources/`; the upload session over it is `interface/ui/uploads.py`'s | free |``.
  Verify: `git grep -n -F "the upload session over it" -- isekai/pipeline/README.md` prints one line.
- [x] 4.2 In `isekai/interface/README.md` add this row to the *Files* table after the `ui/surface.py` row: ``| `ui/uploads.py` | the upload session behind the import sheet: `Reader` reads one open import's uploads in turn, and `Imports` holds each open import's staging folder and reader and seals the reader before a commit; both call `pipeline/importing.py` as `importing.<name>`, so a test replaces `read` or `commit` by name. **Imports no web framework** |``.
  Verify: `git grep -n -e "^| .ui/uploads.py. |" -- isekai/interface/README.md` prints one line.
- [x] 4.3 In `isekai/interface/ui/README.md` change "The import's reader in" and the path after it, `pipeline/importing.py`, to the path `uploads.py`, and in the next line put "through pipeline/importing.py," after "one at a time".
  Verify: `git grep -n -e "reader in .uploads.py." -- isekai/interface/ui/README.md` prints one line.
- [x] 4.4 In `docs/modules.md` change the words "both compose it, and" to "both compose it, the upload session over it is interface/ui/uploads.py's, and", and change "import's reader," to "the reader of interface/ui/uploads.py,".
  Verify: `git grep -n -F "import's reader" -- docs/modules.md` prints nothing.
- [x] 4.5 Confirm the suite, the layer rules, the docs, the bindings and the wire hold at the end.
  Verify: `uv run pytest tests/test_importing.py tests/test_ui_api.py tests/test_ui.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py tests/test_spec_bindings.py tests/test_derive_wire.py` exits 0.
