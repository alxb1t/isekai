# The server's seams — tasks

The phases: the jobs, the file response, the draft's four, the documents. Nothing moves; each phase but the last turns the patches of the names it takes into arguments, and [design](design.md) says where each seam is read.

## Progress

- [x] 1 — The jobs · moderate
- [x] 2 — The file response · moderate
- [ ] 3 — The draft's four · moderate
- [ ] 4 — The documents · moderate

## 1 — The jobs

- [x] 1.1 **HALT CHECK** `create_app` builds the jobs itself, with `jobs = Jobs(`, the one place [D1](design.md#d1) changes.
  Verify: `git grep -n -F 'jobs = Jobs(' -- isekai/interface/ui/app.py` prints a line.
- [x] 1.2 In `isekai/interface/ui/app.py` give `create_app` the keyword-only parameter `make_jobs: Callable[..., Jobs] = Jobs` after `port`, build `jobs = make_jobs(` with the arguments it passes today, and add a line to the docstring ([D1](design.md#d1), [D2](design.md#d2)).
  Verify: `git grep -n -F 'jobs = make_jobs(' -- isekai/interface/ui/app.py` prints a line.
- [x] 1.3 In `tests/test_ui.py`, in `test_sigint_ends_streams_without_cancellation_output`, and in `tests/test_ui_jobs.py`, in `test_reconnect_keeps_prepare_progress`, pass the test's own `make_jobs` to `create_app` and delete the line that patched `Jobs`; drop `tests/test_ui_jobs.py`'s import of `app_module`, which that patch alone read ([D5](design.md#d5)).
  Verify: `git grep -n -F '"Jobs", make_jobs)' -- tests` prints nothing.
- [x] 1.4 Run the server's tests, the ratchets and the record: no assertion changes.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui.py tests/test_ui_billing.py tests/test_ui_propose.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ratchets.py tests/test_record.py` passes.

## 2 — The file response

- [x] 2.1 **HALT CHECK** `_photograph` is read by `read_staged`, `read_photo`, `read_source_copy` and `read_source` alone: its definition and those callers are the lines that name it ([D3](design.md#d3)).
  Verify: `git grep -c -F '_photograph(' -- isekai/interface/ui/app.py` prints `isekai/interface/ui/app.py:5`.
- [x] 2.2 In `isekai/interface/ui/surface.py` give `Surface.__init__` the keyword-only parameter `file_response: Callable[..., Any]`, store it as `self.file_response = file_response`, and name it in the module's docstring ([D2](design.md#d2)).
  Verify: `git grep -n -F 'self.file_response = file_response' -- isekai/interface/ui/surface.py` prints a line.
- [x] 2.3 In `app.py` give `create_app` the keyword-only parameter `file_response: Callable[..., Response] = FileResponse` after `make_jobs`, pass `file_response=file_response` to `Surface(`, and add a line to the docstring ([D1](design.md#d1)).
  Verify: `git grep -n -F 'file_response=file_response' -- isekai/interface/ui/app.py` prints a line.
- [x] 2.4 In `app.py` give `_photograph` the first parameter `file_response: Callable[..., Response]`, so its last line reads `return file_response(path, media_type=kind, headers=headers)`, and have `read_staged`, `read_photo`, `read_source_copy` and `read_source` pass `surface.file_response` first ([D3](design.md#d3)).
  Verify: `git grep -n -F 'return file_response(path, media_type=kind, headers=headers)' -- isekai/interface/ui/app.py` prints a line.
- [x] 2.5 In `app.py` make `read_render_image`, `read_render_thumb`, `read_bake_image`, `read_bake_thumb` and `read_source_thumb` answer `surface.file_response(` with the arguments they pass to `FileResponse(` today, and change each return annotation `-> FileResponse` to `-> Response`. `page` keeps `FileResponse` ([D3](design.md#d3)).
  Verify: `git grep -n -F 'FileResponse(' -- isekai/interface/ui/app.py` prints one line, `page`'s.
- [x] 2.6 In `tests/test_ui_api.py` give `_client` the keyword-only parameter `seams: Mapping[str, Any] | None = None` and call `create_app(..., **(seams or {}))`. Have `test_a_cross_site_request_without_origin_is_refused` and `test_a_request_from_this_page_reads_the_photograph` take `wired`, `made` and `tmp_path` for `client`, build `_client(wired, made, tmp_path, seams=...)` with the recorder each patched in, and delete both patches ([D5](design.md#d5)).
  Verify: `git grep -n -F '"FileResponse"' -- tests` prints nothing.
- [x] 2.7 Run the server's tests, the ratchets, the record, the layer guards and the entry point's import guard.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui.py tests/test_ui_billing.py tests/test_ui_propose.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ratchets.py tests/test_record.py tests/test_layers.py tests/test_pipeline_cli.py tests/test_ui_wire.py` passes.

## 3 — The draft's four

- [ ] 3.1 **HALT CHECK** The module's lock is the one `threading.Lock()` of `app.py`, the lock the routes of [D1](design.md#d1) take.
  Verify: `git grep -c -F 'threading.Lock()' -- isekai/interface/ui/app.py` prints `isekai/interface/ui/app.py:1`.
- [ ] 3.2 In `surface.py` give `Surface.__init__` the keyword-only parameters `save_draft`, `approve`, `precondition` and `draft_lock`, typed as [D2](design.md#d2) says with `AbstractContextManager` from `contextlib`, and store each under its own name.
  Verify: `git grep -n -E '^        self\.(save_draft|approve|precondition|draft_lock) = ' -- isekai/interface/ui/surface.py` prints a line for each of `save_draft`, `approve`, `precondition` and `draft_lock`.
- [ ] 3.3 In `app.py` move `def _precondition(`, its signature, docstring and body unchanged, from below `create_app` to sit between `authorities` and `create_app` ([D4](design.md#d4)).
  Verify: `git grep -n -E '^def (authorities|_precondition|create_app)\(' -- isekai/interface/ui/app.py` prints `authorities`, `_precondition` and `create_app`, in that order.
- [ ] 3.4 In `app.py` import `AbstractContextManager` from `contextlib`, give `create_app` the keyword-only parameters `save_draft`, `approve`, `precondition` and `draft_lock` after `file_response`, as [D1](design.md#d1) shows, pass each to `Surface(`, the lock as `draft_lock=draft_lock if draft_lock is not None else threading.Lock()`, and add a docstring line for each ([D4](design.md#d4)).
  Verify: `git grep -n -F 'draft_lock=' -- isekai/interface/ui/app.py` prints a line.
- [ ] 3.5 In `app.py` make `put_draft`, `post_approve`, `post_cancel`, `post_discard`, `post_draft` and `delete_render` write `with surface.draft_lock:`; `put_draft`, `post_approve` and `post_discard` call `surface.precondition(`; `put_draft` calls `surface.save_draft(`; `post_approve` calls `surface.approve(` ([D4](design.md#d4)).
  Verify: `git grep -c -F 'with surface.draft_lock:' -- isekai/interface/ui/app.py` prints `isekai/interface/ui/app.py:6`.
- [ ] 3.6 In `app.py` delete `_DRAFT_UPDATE = threading.Lock()` and the comment above it.
  Verify: `git grep -n -F '_DRAFT_UPDATE' -- isekai` prints nothing.
- [ ] 3.7 In `tests/test_ui_api.py` re-arrange `_overlap`, `_update_during_approval` and the tests that call them as [D5](design.md#d5) says: each builds its wrappers, then its client with them as seams, then reads `body`, and none patches `_DRAFT_UPDATE`. The patch of `review_module.write` stays.
  Verify: `git grep -n -F '_DRAFT_UPDATE' -- tests` prints nothing.
- [ ] 3.8 Add `test_an_app_given_no_lock_holds_one_of_its_own` to `tests/test_ui_api.py` after the draft's twins, as [D6](design.md#d6) says, marked `@pytest.mark.spec("ui:draft-update:overlapping-updates-cannot-both-commit")`, with a case each for no lock argument and `contextlib.nullcontext()`.
  Verify: `uv run pytest tests/test_ui_api.py -k test_an_app_given_no_lock_holds_one_of_its_own` passes.
- [ ] 3.9 In `tests/test_ratchets.py` change the row `"isekai.interface.ui.app": 12,` of `PATCHED_MODULES` to `"isekai.interface.ui.app": 1,`; the row stays for the patch of `run`, and `PATCHED_ROWS` is unchanged ([D1](design.md#d1)).
  Verify: `git grep -n -F '"isekai.interface.ui.app": 1,' -- tests/test_ratchets.py` prints the row.
- [ ] 3.10 Check that the measure is the row's number.
  Verify: `uv run python -c "from tests.test_ratchets import patched_modules, REPO_ROOT; print(patched_modules(REPO_ROOT)['isekai.interface.ui.app'])"` prints `1`.
- [ ] 3.11 Check that the one patch of `app.py` left is the patch of `run` ([D5](design.md#d5)).
  Verify: `git grep -n -F 'setattr(app_module' -- tests` prints one line, `tests/test_ui.py`'s patch of `run`.
- [ ] 3.12 Run the server's tests, the ratchets, the record, the layer guards and the entry point's import guard.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui.py tests/test_ui_billing.py tests/test_ui_propose.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ratchets.py tests/test_record.py tests/test_layers.py tests/test_pipeline_cli.py tests/test_ui_wire.py` passes.

## 4 — The documents

- [ ] 4.1 **HALT CHECK** `0149`'s decision is on the page, so D61 is the next free number ([D7](design.md#d7)).
  Verify: `git grep -n -F '### D60 · ' -- docs/decisions.md` prints a line.
- [ ] 4.2 In `docs/decisions.md` add the decision of [D7](design.md#d7), `### D61 · What a test replaces in the server is a parameter of create_app`, after D60's block and before `## Infrastructure`.
  Verify: `git grep -n -F '### D61 · What a test replaces in the server is a parameter of create_app' -- docs/decisions.md` prints its line.
- [ ] 4.3 In `docs/decisions.md`, D59's *Accepts* line reads in full "the routes that read a seam of `create_app` stay closures of `create_app`, with `make_jobs` and `run` kept there, and so do the library, staging, review and images routes, until their versions. Reopen when the last of them moves.", where it read "the routes that read a name a test patches stay closures of `create_app`, with `Jobs(` and `run` kept there, and so do …". Its *Made by* line reads `0147`, `0148`, `0150`.
  Verify: `git grep -n -F 'the routes that read a name a test patches stay closures' -- docs/decisions.md` prints nothing.
- [ ] 4.4 In the docstring of `isekai/interface/ui/app.py` the sentence "`create_app` declares the routes that read a name a test patches, and the rest." reads "`create_app` takes what a test replaces and declares the routes that read it, and the rest."
  Verify: `git grep -n -F 'takes what a test replaces' -- isekai/interface/ui/app.py` prints a line.
- [ ] 4.5 In the docstring of `isekai/interface/ui/surface.py` say that the surface also holds the seams a test replaces: the file response, `save_draft`, `approve`, the precondition check and the draft lock.
  Verify: `git grep -n -F 'a test replaces' -- isekai/interface/ui/surface.py` prints a line.
- [ ] 4.6 In `isekai/interface/README.md` the `ui/surface.py` row reads "… the shared vocabulary, the upload limit and the seams a test replaces (the file response, `save_draft`, `approve`, the precondition check and the draft lock), and the lookups every route makes over them. …"; the `ui/app.py` row reads "… it takes the seams a test replaces and the jobs' factory, builds the `Surface`, mounts each resource of `ui/routes/` and imports uvicorn".
  Verify: `git grep -n -F 'the precondition check and the draft lock' -- isekai/interface/README.md` prints a line.
- [ ] 4.7 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` passes.
- [ ] 4.8 Replay the recorded mutants: no entry of `tests/mutants.json` is anchored in a line this change rewrites ([D8](design.md#d8)).
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
- [ ] 4.9 Hold the series' conditions: nothing under `tests/record/` and no entry of `tests/mutants.json` differs from the cut's base.
  Verify: `git diff --exit-code bc16b803 -- tests/record tests/mutants.json` exits 0.
- [ ] 4.10 Run the documents' and the guards' tests.
  Verify: `uv run pytest tests/test_docs.py tests/test_ratchets.py tests/test_layers.py tests/test_record.py` passes.
