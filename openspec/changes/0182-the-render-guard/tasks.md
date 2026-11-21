# The render guard — tasks

The foundation gets the rule for a held collection, the app's guard asks it, and the documents say so.

## Progress

- [x] 1 — The rule · moderate
- [ ] 2 — The guard · moderate
- [ ] 3 — The documents · moderate

## 1 — The rule

- [x] 1.1 **HALT CHECK** `running` and `render_running` stand in `isekai/foundation/library.py` where [D1](design.md#d1) places the new function: after the first, before the second.
  Verify: `git grep -n -e "^def render_running" -e "^def running" -- isekai/foundation/library.py` prints `100:def running(folder: Path) -> list[dict[str, Any]]:` and `116:def render_running(run: Run) -> bool:`.
- [x] 1.2 In `tests/test_ui_library.py`, add `import fcntl`, extend the `isekai.foundation.library` import with `collection_held`, and add `test_a_collection_is_held_by_a_live_session_lock` at the file's end, marked `@pytest.mark.spec_exempt("structural: a collection is held by a session's live lock")`, per [D4](design.md#d4). It holds that a folder with no `sessions/` and one whose record's lock is free are not held; that a record's lock held through a second open file with `fcntl.flock(held, fcntl.LOCK_EX)` holds the folder, an unreadable record (`{`) included; and that another folder stays unheld meanwhile.
  Verify: `uv run pytest tests/test_ui_library.py` exits 2, an `ImportError` of `collection_held`.
- [x] 1.3 In `isekai/foundation/library.py`, add `collection_held` between `running` and `render_running`, exactly as [D1](design.md#d1) gives it, and end `render_running` on `return collection_held(runs.parent)` in place of its `return any(...)` line.
  Verify: `uv run pytest tests/test_ui_library.py tests/test_pipeline_cli.py` exits 0.
- [x] 1.4 Run `tools.mutate` over `collection_held`, from its `def` line to its last line; a survivor is killed by a further assertion in the case of 1.2.
  Verify: `uv run python -m tools.mutate isekai/foundation/library.py:116-123 --tests tests/test_ui_library.py` exits 0.

## 2 — The guard

- [ ] 2.1 **HALT CHECK** `Surface.rendering` stands where [D2](design.md#d2) replaces it.
  Verify: `git grep -n -F "def rendering(" -- isekai/interface/ui/surface.py` prints `196:    def rendering(self, collection: str) -> str | None:`.
- [ ] 2.2 In `tests/test_ui_api.py`, add `import fcntl` before `import io` and a context manager `_session_held(folder: Path)` that writes `<folder>/sessions/20261024T091200Z.json` and holds the lock of its `.lock` file through a second open file ([D4](design.md#d4)). Add the delete case of [D3](design.md#d3)'s table, marked with its scenario key, leaving `Jobs.slot` unpatched: it holds the lock on `v1/11`, asserts the refusal's sentence and an unchanged `snapshot(made.path)`, then holds a lock of a second collection `other` (its `sources/` made) and deletes `v2/22` with status `200`.
  Verify: `uv run pytest tests/test_ui_api.py -k deleting_a_render_is_refused_while_another_process` exits 1, on the missing refusal.
- [ ] 2.3 In `tests/test_ui_api.py`, add the sheet case and the cancel case of [D3](design.md#d3)'s table, each marked with its scenario key, leaving `Jobs.slot` unpatched. Each approves with `_approved` and holds the lock with `_session_held`; the sheet case asserts the payload's `["cancel"]`, the cancel case the `409` and the approval still on disk.
  Verify: `uv run pytest tests/test_ui_api.py -k "sheet_names_a_session_another_process or cancel_is_refused_while_another_process"` exits 1, on the missing refusal.
- [ ] 2.4 In `isekai/interface/ui/surface.py`, import `collection_held` from `isekai.foundation.library` between the imports of `flow` and `refusal`, and replace `rendering` exactly as [D2](design.md#d2) gives it.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_ui_library.py tests/test_layers.py` exits 0.
- [ ] 2.5 Check the guard reads the rule once, as [D2](design.md#d2) writes it.
  Verify: `git grep -n -F "collection_held(" -- isekai/interface/ui/surface.py` prints one line, the `if ours or` line of `rendering`.
- [ ] 2.6 Run `tools.mutate` over `Surface.rendering`, from its `def` line to its last line, on the cases that reach it; a survivor is killed by a further assertion in the cases of 2.2 and 2.3.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/surface.py:197-208 --tests tests/test_ui_api.py "-k cancel or delet"` exits 0.
- [ ] 2.7 Replay the standing mutants over the edited files.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 3 — The documents

- [ ] 3.1 In `docs/decisions.md`, amend D72 as [D5](design.md#d5) says: its *Accepts* line takes the app's guard's new words from there, in place of "the app's job slot", and its *Made by* gains `0182`. The heading stays.
  Verify: `git grep -n -F "refuses while its render slot runs or a session holds the collection" -- docs/decisions.md` prints the *Accepts* line of D72.
- [ ] 3.2 In `isekai/foundation/README.md`, in the `library.py` row of *Files*, change `` `record_running`, `running`, `render_running` and `session` `` to `` `record_running`, `running`, `collection_held`, `render_running` and `session` ``.
  Verify: `git grep -n -F "collection_held" -- isekai/foundation/README.md` prints the `library.py` row of *Files*.
- [ ] 3.3 Derive the *Imported by* tables again with `uv run python -m tools.derive_imported_by`; `interface/ui/surface.py` joins the `library.py` row.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py` exits 0.
- [ ] 3.4 In `isekai/interface/ui/README.md`, in the **Delete** bullet, change `refused` / `while a render runs for the collection` to `refused` / `while this server's render slot runs or a session of any process holds the collection`.
  Verify: `git grep -n -F "a session of any process holds the collection" -- isekai/interface/ui/README.md` prints the bullet's second line.
- [ ] 3.5 In `CHANGELOG.md`, in the `0.87.37` notes, drop the clause ", and its *Known breaks* leave" and the path that follows it from the first bullet that names D72, as [D5](design.md#d5) writes it. Cards `0181·R1` and `0181·S3`.
  Verify: `git grep -n -F "Known breaks* leave" -- CHANGELOG.md` prints nothing.
