# The review routes — tasks

The phases are the reads, the writes and the documents. Each moves lines and no behaviour, and the suite as it stands is the proof.

## Progress

- [ ] 1 — The reads · moderate
- [ ] 2 — The writes · moderate
- [ ] 3 — The documents · moderate

## 1 — The reads

- [ ] 1.1 **HALT CHECK** No test patches a name of `isekai/interface/ui/app.py` that the review's routes or helpers read: the one patch the module keeps is `run`'s, which `serve` reads.
  Verify: `git grep -n "setattr(app_module" -- tests` prints one line.
- [ ] 1.2 Before any line moves, run each pre-flight run [D7](design.md#d7) lists over the lines of `isekai/interface/ui/app.py` that the reads and the writes move, one command at a time. Kill each survivor with a case added to an existing test; name it in [Equivalent mutants](design.md#equivalent-mutants) only when no case can tell it from the code, then set that section's first line to `Pre-flight at the base: run.`
  Verify: `grep -n "Pre-flight at the base: run" openspec/changes/0154-the-review-routes/design.md` prints a line.
- [ ] 1.3 Write `isekai/interface/ui/routes/reviewing.py`: `class ReviewRoutes` with `read_input`, `read_photo` and `read_source_copy` as [D1](design.md#d1) and [D4](design.md#d4) say, `_revision`, `_drafted`, `_prose`, `_wd14`, `_tags`, `_command`, `_remedy`, `_flow_of` and `_budget` as module functions, a `ROUTES` table in `app.py`'s order and `mount(app, surface)`.
  Verify: `grep -nE "^(class ReviewRoutes|ROUTES|def mount)" isekai/interface/ui/routes/reviewing.py` prints a line for each of those names.
- [ ] 1.4 Move `_approved`, `_fields`, `_untagged`, `_decimal`, `_renders_out`, `_saved` and `_photograph` from `isekai/interface/ui/app.py` into `isekai/interface/ui/routes/common.py`, each with its docstring and text unchanged ([D3](design.md#d3)).
  Verify: `git grep -nE "^def _(approved|fields|untagged|decimal|renders_out|saved|photograph)\(" -- isekai/interface/ui/routes/common.py` prints a line for each of those names.
- [ ] 1.5 Delete the closures `read_input`, `read_photo` and `read_source_copy` from `create_app` in `isekai/interface/ui/app.py`, call `review_mount(app, surface)` after `stream_mount(app, surface)`, and import back `_approved`, `_decimal`, `_photograph`, `_renders_out`, `_saved` and `_untagged` from `routes/common.py` and `_budget` and `_command` from `routes/reviewing.py`. Prune the imports `app.py` no longer reads, and keep each name a test reads from `app.py` ([D3](design.md#d3), [D6](design.md#d6)).
  Verify: `git grep -nE "def (read_input|read_photo|read_source_copy)\(" -- isekai/interface/ui/app.py` prints nothing.
- [ ] 1.6 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`: the new module and the pruned imports change them.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 1.7 Prove the move against the record, the ratchets, the layers, the entry point's imports, the wire and the server's own tests.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py tests/test_ui_api.py tests/test_ui.py` exits 0.
- [ ] 1.8 Run `git add -N isekai/interface/ui/routes/reviewing.py`, since `tools.mutate` copies tracked files only, then close with `tools.mutate` on the module's first range ([D7](design.md#d7)). Kill each survivor with a case added to an existing test; name it in [Equivalent mutants](design.md#equivalent-mutants) only when no case can tell it from the code.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/reviewing.py:1-100 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 1.9 Close with the next range of `isekai/interface/ui/routes/reviewing.py`, each survivor handled as 1.8 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/reviewing.py:101-200 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 1.10 Close with the rest of `isekai/interface/ui/routes/reviewing.py`, each survivor handled as 1.8 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/reviewing.py:201-2000 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 1.11 Close with `tools.mutate` on the helpers `isekai/interface/ui/routes/common.py` holds now, each survivor handled as 1.8 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/common.py:1-2000 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.

## 2 — The writes

- [ ] 2.1 Add to `ReviewRoutes` in `isekai/interface/ui/routes/reviewing.py` the handlers `put_draft`, `post_approve`, `post_cancel`, `post_discard` and `post_draft`, their text unchanged but as [D4](design.md#d4) says and `post_draft` annotated ``-> object`` as [D5](design.md#d5) says, with their rows in `ROUTES` in `app.py`'s order. Add `_update`, `_renders_in`, `_images`, `_image_out` and `_numbered` as module functions ([D3](design.md#d3)).
  Verify: `grep -nE "def (put_draft|post_approve|post_cancel|post_discard|post_draft)\(" isekai/interface/ui/routes/reviewing.py` prints a line for each of those names.
- [ ] 2.2 Move `REFUSED`, with its comment, from `isekai/interface/ui/app.py` into `isekai/interface/ui/routes/common.py`, and import it back into `app.py`, where `_refused` reads it ([D3](design.md#d3)).
  Verify: `git grep -n "^REFUSED = 409" -- isekai/interface/ui/routes/common.py` prints a line.
- [ ] 2.3 Delete the closures `put_draft`, `post_approve`, `post_cancel`, `post_discard` and `post_draft` from `create_app` in `isekai/interface/ui/app.py`, with the helpers only they read, drop its imports of `_untagged`, `_budget` and `_command`, and prune the imports it no longer reads. Keep each name a test reads from `app.py`.
  Verify: `git grep -nE "def (put_draft|post_approve|post_cancel|post_discard|post_draft)\(" -- isekai/interface/ui/app.py` prints nothing.
- [ ] 2.4 In `tests/test_ratchets.py`, remove the row ``"isekai/interface/ui/app.py": 2351`` from `LONG_FILES`, since `app.py` now holds fewer lines than the ceiling ([D9](design.md#d9)).
  Verify: `git grep -nF '"isekai/interface/ui/app.py": 2351' -- tests/test_ratchets.py` prints nothing.
- [ ] 2.5 In `tests/test_ratchets.py`, lower `FILE_ROWS` to ``FILE_ROWS = 5``, the count of the rows `LONG_FILES` now holds.
  Verify: `git grep -n "^FILE_ROWS = 5" -- tests/test_ratchets.py` prints a line.
- [ ] 2.6 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`: the module's new imports change them.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 2.7 Prove the move against the record, the ratchets, the layers, the entry point's imports, the wire and the server's own tests.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py tests/test_ui_api.py tests/test_ui.py` exits 0.
- [ ] 2.8 Close with `tools.mutate` on the first range of `isekai/interface/ui/routes/reviewing.py` as it now stands ([D7](design.md#d7)). Kill each survivor with a case added to an existing test; name it in [Equivalent mutants](design.md#equivalent-mutants) only when no case can tell it from the code.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/reviewing.py:1-110 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 2.9 Close with the next range of `isekai/interface/ui/routes/reviewing.py`, each survivor handled as 2.8 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/reviewing.py:111-220 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 2.10 Close with the next range of `isekai/interface/ui/routes/reviewing.py`, each survivor handled as 2.8 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/reviewing.py:221-330 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 2.11 Close with the next range of `isekai/interface/ui/routes/reviewing.py`, each survivor handled as 2.8 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/reviewing.py:331-420 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 2.12 Close with the rest of `isekai/interface/ui/routes/reviewing.py`, each survivor handled as 2.8 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/reviewing.py:421-2000 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.

## 3 — The documents

- [ ] 3.1 In `docs/decisions.md`, change ``the library, staging, review and images routes, until their versions`` in D59's *Accepts* line to ``the library, staging and images routes, until their versions``, and add `0154` to its *Made by* line ([D59](../../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface)).
  Verify: `git grep -n "staging and images routes, until their versions" -- docs/decisions.md` prints a line.
- [ ] 3.2 In the docstring of `isekai/interface/ui/app.py`, add `ReviewRoutes` to the resource classes `routes/` holds.
  Verify: `git grep -n "ReviewRoutes" -- isekai/interface/ui/app.py` prints a line.
- [ ] 3.3 In the same docstring, delete `the join of caption, sheet, draft, approved and budget into one payload,` from what `app.py` owns, and say that join is the review routes' own in `routes/reviewing.py`.
  Verify: `git grep -n "the join of caption, sheet" -- isekai/interface/ui/app.py` prints nothing.
- [ ] 3.4 In `isekai/interface/README.md`, change the `ui/routes/` row's `render and jobs, and events routes` to `render and jobs, review, and events routes`.
  Verify: `git grep -n "render and jobs, review, and events routes" -- isekai/interface/README.md` prints a line.
- [ ] 3.5 In the same README, change the `ui/app.py` row to say `create_app` still declares ``the library, staging, images and sources endpoints``.
  Verify: `git grep -n "the library, staging, images and sources endpoints" -- isekai/interface/README.md` prints a line.
- [ ] 3.6 In `docs/modules.md`, after the words ``stage ③'s review functions,`` add the words ``which `ReviewRoutes` of `interface/ui/routes/reviewing.py` calls,``.
  Verify: `git grep -n "ReviewRoutes" -- docs/modules.md` prints a line.
- [ ] 3.7 In `docs/principles.md`, name `interface/ui/routes/reviewing.py` and `interface/ui/routes/common.py` where its *Known breaks* name `interface/ui/app.py` as deciding what makes a draft, an approval, a caption or a tag list damaged, and name `interface/ui/routes/reviewing.py` where they name `interface/ui/app.py`'s `_revision`.
  Verify: `git grep -nE "ui/app\.py. decides what makes a draft" -- docs/principles.md` prints nothing.
- [ ] 3.8 In `tests/mutants.json`, change `PB-2c`'s `path` to `isekai/interface/ui/routes/reviewing.py`, its `find` and `replace` unchanged ([D8](design.md#d8)).
  Verify: `git grep -n "routes/reviewing.py" -- tests/mutants.json` prints a line.
- [ ] 3.9 In `tests/mutants.json`, re-anchor `UA-7` on the artifacts import of `isekai/interface/ui/app.py` as it now ends: its `find` is ``from isekai.foundation.artifacts import renders_of`` and its `replace` the same import with `write_json` added ([D8](design.md#d8)).
  Verify: `git grep -n "artifacts import renders_of" -- tests/mutants.json` prints a line.
- [ ] 3.10 Replay the recorded mutants: every entry's `find` must occur once in its file and each must die.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
- [ ] 3.11 Prove the documents against the record, the ratchets, the layers, the entry point's imports, the wire and the server's own tests.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py tests/test_ui_api.py tests/test_ui.py` exits 0.
