# The wire states — tasks

Each task names its file and its check. The decisions are in [design](design.md); each phase ends on a green gate.

## Progress

- [x] 1 — The cell's stage and the job's state · moderate
- [x] 2 — The file's state · moderate
- [x] 3 — The documents · moderate

## 1 — The cell's stage and the job's state

- [x] 1.1 **HALT CHECK** The base is typed clean, so a red `ty` after an edit is this change's.
  Verify: `uv run ty check` exits 0.
- [x] 1.2 In `isekai/interface/ui/library.py` add `Stage` above `Cell` as [D2](design.md#d2) gives it, under the comment `# The stages a cell holds, from `assigned` to `rendered`; `unreadable` marks a cell` and `# whose deciding file cannot be read.`. Change `stage: str | None` in `Cell` to `stage: Stage | None`, and leave every `Cell(` as it is.
  Verify: `git grep -n -F "stage: str | None" -- isekai/interface/ui/library.py` prints nothing.
- [x] 1.3 In `isekai/interface/ui/jobs.py` add `State` below `KINDS` as [D2](design.md#d2) gives it, under the comment `# The states of a job: `running` until it ends, then `failed`, `stopped` or `done`.`. Change `state: str = "running"` in `_Job` to `state: State = "running"`.
  Verify: `git grep -n -F "state: str = " -- isekai/interface/ui/jobs.py` prints nothing.
- [x] 1.4 In `isekai/interface/ui/shapes.py` change `from isekai.interface.ui import jobs` to `from isekai.interface.ui import jobs, library`, `HubCell.stage` to `library.Stage | None`, `Job.state` to `jobs.State` and `Snapshot.jobs` from `dict[str, Job | None]` to `dict[jobs.Kind, Job | None]` ([D1](design.md#d1), [D5](design.md#d5)). Leave `CellEvent`, `JobStage`, `Job.stage` and `BillingVolume` as they are ([D4](design.md#d4)).
  Verify: `git grep -n -F "dict[str, Job | None]" -- isekai/interface/ui/shapes.py` prints nothing.
- [x] 1.5 **HALT CHECK** Hold the phase on `ty`: it refuses a word outside a set, so a test that builds a `Cell` or a `_Job` with a `str` shows red here. That is a plan problem: halt, and change no assertion.
  Verify: `uv run ty check` exits 0.
- [x] 1.6 Run the tests that read these modules and the layer and document guards.
  Verify: `uv run pytest tests/test_ui_shapes.py tests/test_ui_library.py tests/test_ui_jobs.py tests/test_layers.py tests/test_docs.py` exits 0.

## 2 — The file's state

- [x] 2.1 **HALT CHECK** Before an edit, run `uv run python -m tools.mutate isekai/pipeline/importing.py:218 isekai/pipeline/importing.py:302 isekai/pipeline/importing.py:319 isekai/pipeline/importing.py:325 --tests tests/test_importing.py tests/test_ui_api.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` on the module as it stands ([D6](design.md#d6)). It starts from green tests and kills each mutant, as the design's *Equivalent mutants* records; a survivor is a plan problem: halt.
  Verify: `uv run pytest tests/test_importing.py` exits 0.
- [x] 2.2 In `isekai/pipeline/importing.py` add `Mapping` to the `collections.abc` import, `Upload` under `State` with the comment `# Every state a file is published in: one `Staged` holds, or one the reader holds` and `# before it has staged the file.`, and `_record` above `class Reader`, all as [D3](design.md#d3) gives them.
  Verify: `git grep -n -F "Upload = Literal[State," -- isekai/pipeline/importing.py` prints the alias line.
- [x] 2.3 In the same file rewrite `put`'s `record = {"file": name, "state": "waiting"}`, the `refused` call of `put`, `_run` from its `converting` call to its last call of `_set`, and `_set`, to the text [D3](design.md#d3) gives. Leave `shutil.rmtree(held.parent, ignore_errors=True)` and every comment as they are.
  Verify: `git grep -n -F "self._set(upload, name, state, fields)" -- isekai/pipeline/importing.py` prints one line.
- [x] 2.4 In `isekai/interface/ui/shapes.py` change `from isekai.pipeline import tattoos` to `from isekai.pipeline import importing, tattoos` and `FileState.state` to `importing.Upload` ([D1](design.md#d1)).
  Verify: `git grep -n -E "^    (stage|state): str" -- isekai/interface/ui/shapes.py` prints five lines.
- [x] 2.5 Run `uv run python -m tools.derive_imported_by`, which adds `interface/ui/shapes.py` to the `importing.py` row of `isekai/pipeline/README.md`.
  Verify: `git grep -n -F "interface/ui/shapes.py" -- isekai/pipeline/README.md` prints three lines.
- [x] 2.6 **HALT CHECK** Hold the phase on `ty`. A test callback `ty` refuses is a plan problem: halt, and change no assertion.
  Verify: `uv run ty check` exits 0.
- [x] 2.7 Run the tests that read the importer, the declarations and the guards.
  Verify: `uv run pytest tests/test_importing.py tests/test_ui_shapes.py tests/test_layers.py tests/test_docs.py` exits 0.
- [x] 2.8 Close with `tools.mutate` on the rewritten lines, against the layout 2.3 gives: the return of `_record`, the `refused` call of `put`, `_run`'s last call and `_set`'s publish ([D6](design.md#d6)). A survivor halts the build, and a range that lies off by one is re-fitted to the layout 2.3 gave.
  Verify: `uv run python -m tools.mutate isekai/pipeline/importing.py:171 isekai/pipeline/importing.py:227 isekai/pipeline/importing.py:328 isekai/pipeline/importing.py:337 --tests tests/test_importing.py` exits 0.
- [x] 2.9 Close with `tools.mutate` on `_run`'s `converting` call, which `tests/test_importing.py` leaves alive and the stream's case in `tests/test_ui_api.py` kills.
  Verify: `uv run python -m tools.mutate isekai/pipeline/importing.py:311 --tests tests/test_importing.py tests/test_ui_api.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.

## 3 — The documents

- [x] 3.1 In `docs/decisions.md` edit [D66](design.md#d7) in place: append to its bold statement `A cell's stage, a job's state and kind and a file's state are the `Literal` of the module that writes them, and `shapes.py` reads it.`. In its *Accepts* line change `a file's state, a job's state and the billing volume's state are `str`` to `the billing volume's state, a session's outcome and a cell event's stage and state are `str``. Change its *Made by* line from `` `0166`. `` to `` `0166`, `0167`. ``.
  Verify: `git grep -n -F "the billing volume's state, a session's outcome" -- docs/decisions.md` prints the *Accepts* line.
- [x] 3.2 In `isekai/interface/README.md` change the `ui/shapes.py` row from `a test holds each and no route reads it.` to `a test holds each and no route reads it. A cell's stage, a job's state and kind and a file's state are the `Literal` of the module that writes them, and `ty` holds each write.`.
  Verify: `git grep -n -F "a job's state and kind and a file's state" -- isekai/interface/README.md` prints the row.
- [x] 3.3 Hold that the derived tables and the documents agree with the code.
  Verify: `uv run pytest tests/test_docs.py tests/test_spec_prose.py` exits 0.
- [x] 3.4 Hold that the change touched no record and no page file.
  Verify: `git diff --stat main...HEAD -- tests ui/src` prints nothing.
