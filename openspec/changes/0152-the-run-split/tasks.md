# The run split — tasks

The phases: names and rundir, layout, failures, the documents. Each moves text and edits none; [design](design.md) says where each name goes.

## Progress

- [x] 1 — Names and rundir · moderate
- [x] 2 — Layout · moderate
- [ ] 3 — Failures · moderate
- [ ] 4 — The documents · moderate

## 1 — Names and rundir

- [x] 1.1 **HALT CHECK** No test patches a name the moved code reads: `RUNS_ROOT` is the one patch of `isekai/foundation/run.py`, and it stays there ([D3](design.md#d3)).
  Verify: `git grep -n -E 'setattr\(run_module, ' -- tests` prints one line, the patch of `RUNS_ROOT`.
- [x] 1.2 Open with the pre-flight over the functions this phase moves, in `run.py`: the identity functions, `Run` and `assign` ([D10](design.md#d10)). A survivor, the ones the design lists in [Survivors at the cut](design.md#survivors-at-the-cut) among them, is killed by a test or named in [Equivalent mutants](design.md#equivalent-mutants). The ranges are the lines of the cut's base, run once with `uv run python -m tools.mutate isekai/foundation/run.py:198-235 isekai/foundation/run.py:241-335 isekai/foundation/run.py:419-444 --tests tests/test_run_directory.py tests/test_assign.py tests/test_package_paths.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_migrate.py` before the move; once the move has shifted `run.py` they hold other lines, and 1.10 runs the same mutants on their new homes.
  Verify: `grep -n -F 'Equivalent mutants' openspec/changes/0152-the-run-split/design.md` prints a line.
- [x] 1.3 Write `isekai/foundation/names.py` with its docstring and the `names.py` row of [D2](design.md#d2), each block moved from `run.py` with its comments and docstring unchanged ([D4](design.md#d4)), in the order the cut's base has them, importing `hashlib`, `re` and `Refusal`.
  Verify: `grep -n -E '^(def (slug|digest_of|run_id|media_type)\(|FRAME_NAME = |ARTIFACT = |ERROR = )' isekai/foundation/names.py` prints a line for each of the names.
- [x] 1.4 Write `isekai/foundation/rundir.py` with its docstring: `_PHOTO_FIELDS`, `Run` and `assign` moved whole, importing `FRAME_NAME`, `ID_DIGEST_CHARS` and `PHOTO` from `names.py`, `RUN_FILE`, `Frame`, `PhotoRecord`, `read` and `require` from `artifacts.py`, and `Refusal`.
  Verify: `grep -n -E '^(class Run|def assign\(|_PHOTO_FIELDS)' isekai/foundation/rundir.py` prints a line for each of the names.
- [x] 1.5 In `run.py` delete the moved blocks. Import each name of `names.py` and `rundir.py` from them, and list every public name of the cut's base but `T` in `__all__`, sorted as `interface/verbs/__init__.py` sorts its own ([D1](design.md#d1), [D6](design.md#d6)). Keep the imports of `os` and `write_atomically`; drop each other import the move leaves unused, as `ruff check` names them.
  Verify: `git grep -n -E '^(def (slug|digest_of|run_id|media_type|assign)\(|class Run[:(])' -- isekai/foundation/run.py` prints nothing.
- [x] 1.6 Check `__all__` against the cut's base: no public name of the base is missing from it, and each name it lists resolves.
  Verify: `uv run python -c "import ast,subprocess,isekai.foundation.run as r; t=ast.parse(subprocess.run(['git','show','ce753c64:isekai/foundation/run.py'],capture_output=True,check=True).stdout); n={x.name for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and not x.name.startswith('_')}|{y.id for x in t.body if isinstance(x,(ast.Assign,ast.AnnAssign)) for z in (getattr(x,'targets',None) or [x.target]) for y in ast.walk(z) if isinstance(y,ast.Name) and not y.id.startswith('_') and len(y.id)>1}; print(sorted(n-set(r.__all__)), [m for m in r.__all__ if not hasattr(r,m)])"` prints `[] []`.
- [x] 1.7 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` passes.
- [x] 1.8 Run the record, the ratchets, the layer guards, the documents, the run directory, the package paths and the CLI's tests: no assertion changes.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_run_directory.py tests/test_package_paths.py tests/test_pipeline_cli.py` passes.
- [x] 1.9 In `tests/mutants.json` the entries FN-4a and FN-4b take the path `isekai/foundation/names.py`, their `find` and `replace` unchanged ([D10](design.md#d10)).
  Verify: `grep -c -F 'isekai/foundation/names.py' tests/mutants.json` prints `2`.
- [x] 1.10 Close with the same run on the new homes. `tools.mutate` copies tracked files only, so run `git add -N isekai/foundation/names.py isekai/foundation/rundir.py` first. A survivor is killed by a test or named in [Equivalent mutants](design.md#equivalent-mutants).
  Verify: `uv run python -m tools.mutate isekai/foundation/names.py:1-400 --tests tests/test_run_directory.py tests/test_assign.py tests/test_package_paths.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_migrate.py` and `uv run python -m tools.mutate isekai/foundation/rundir.py:1-400 --tests tests/test_run_directory.py tests/test_assign.py tests/test_package_paths.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_migrate.py` each exit 0, each survivor they print named in the design.

## 2 — Layout

- [x] 2.1 Open with the tests' baseline: phase 1 has shifted `run.py`, so no range of it holds, and the closing run covers the same mutants ([D10](design.md#d10)).
  Verify: `uv run pytest tests/test_run_directory.py tests/test_edit.py tests/test_edit_placement.py tests/test_edit_session.py tests/test_review.py tests/test_ui_api.py` passes.
- [x] 2.2 Write `isekai/foundation/layout.py` with its docstring and the `layout.py` row of [D2](design.md#d2), each block moved from `run.py` unchanged in the order the cut's base has them ([D4](design.md#d4)), importing `ARTIFACT`, `APPROVED`, `FRAME_NAME`, `OUTPUTS`, `REVIEW` and `SHEETS` from `names.py`, `Run` from `rundir.py`, `SEED_RANGE` from `artifacts.py`, and `Refusal`.
  Verify: `grep -n -E '^def (versions|latest|next_version|artifact_name|is_version|approval_of|sheet_of|group_of|is_seed|_laid_out|is_edit_file|edit_stem|edit_files|placement_file|edit_numbers|next_edit|delete_edits|edit_at|latest_artifact|is_approved|approved_versions)\(' isekai/foundation/layout.py` prints a line for each of the names.
- [x] 2.3 In `run.py` delete the moved blocks. Import each name of `layout.py` from it, `_laid_out` by its own name for `rendered_at` ([D5](design.md#d5)); drop each import the move leaves unused, as `ruff check` names them. `rendered_at` stays.
  Verify: `git grep -n -E '^def (versions|latest|next_version|artifact_name|is_seed|edit_at|edit_files)\(' -- isekai/foundation/run.py` prints nothing.
- [x] 2.4 Check `__all__` against the cut's base, as 1.6 does.
  Verify: `uv run python -c "import ast,subprocess,isekai.foundation.run as r; t=ast.parse(subprocess.run(['git','show','ce753c64:isekai/foundation/run.py'],capture_output=True,check=True).stdout); n={x.name for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and not x.name.startswith('_')}|{y.id for x in t.body if isinstance(x,(ast.Assign,ast.AnnAssign)) for z in (getattr(x,'targets',None) or [x.target]) for y in ast.walk(z) if isinstance(y,ast.Name) and not y.id.startswith('_') and len(y.id)>1}; print(sorted(n-set(r.__all__)), [m for m in r.__all__ if not hasattr(r,m)])"` prints `[] []`.
- [x] 2.5 In `tests/test_ui.py` add `"isekai.foundation.layout": frozenset({"artifact_name"})` to `_ARTIFACT_WRITERS`, and a twin `test_the_check_catches_artifact_name_imported_from_the_layout` after the existing one, as [D7](design.md#d7) says: `laid.py` importing `artifact_name` from `isekai.foundation.layout`, expecting `(["laid.py: artifact_name"], 1)`, marked `spec_exempt` with `structural: twin of test_the_invariant_holds_no_module_of_the_surface_names_an_artifact`. The existing assertion stays.
  Verify: `grep -c -F 'isekai.foundation.layout' tests/test_ui.py` prints `2`.
- [x] 2.6 Run the tripwire and its twins.
  Verify: `uv run pytest tests/test_ui.py -k test_the_check_catches_artifact_name_imported_from_the_layout` passes, and `uv run pytest tests/test_ui.py -k artifact` passes.
- [x] 2.7 Remove the row `"isekai/foundation/run.py": 1045` from `LONG_FILES` in `tests/test_ratchets.py` and set `FILE_ROWS` to 6 ([D8](design.md#d8)); `refusal_for`'s row and the patch row stay.
  Verify: `git grep -n -F '"isekai/foundation/run.py": 1045' -- tests/test_ratchets.py` prints nothing, and `uv run pytest tests/test_ratchets.py` passes.
- [x] 2.8 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` passes.
- [x] 2.9 Run the record, the ratchets, the layer guards, the documents, the run directory, the package paths, the CLI's and the UI's tests: no existing assertion changes.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_run_directory.py tests/test_package_paths.py tests/test_pipeline_cli.py tests/test_ui.py` passes.
- [x] 2.10 Close with `tools.mutate` on the new module, after `git add -N isekai/foundation/layout.py`. The run is split by range, so none outlasts the plan check's 600 seconds. A survivor, one the design lists in [Survivors at the cut](design.md#survivors-at-the-cut) too, is killed by a test or named in [Equivalent mutants](design.md#equivalent-mutants).
  Verify: `uv run python -m tools.mutate isekai/foundation/layout.py:1-150 --tests tests/test_run_directory.py tests/test_edit.py tests/test_edit_placement.py tests/test_edit_session.py tests/test_review.py tests/test_ui_api.py` and `uv run python -m tools.mutate isekai/foundation/layout.py:151-400 --tests tests/test_run_directory.py tests/test_edit.py tests/test_edit_placement.py tests/test_edit_session.py tests/test_review.py tests/test_ui_api.py` each exit 0, each survivor they print named in the design.

## 3 — Failures

- [ ] 3.1 Open with the tests' baseline: phase 2 has shifted `run.py` again ([D10](design.md#d10)).
  Verify: `uv run pytest tests/test_run_directory.py tests/test_caption.py tests/test_tagging.py tests/test_sheet_stage.py tests/test_resume.py tests/test_edit_session.py` passes.
- [ ] 3.2 Write `isekai/foundation/failures.py` with its docstring and the `failures.py` row of [D2](design.md#d2), each block moved from `run.py` unchanged in the order the cut's base has them ([D4](design.md#d4)), importing `ERROR` from `names.py`, `Run` from `rundir.py`, `ERROR_FILE`, `ErrorRecord`, `Failure` and `write` from `artifacts.py`, and `Refusal`.
  Verify: `grep -n -E '^(Kind = |T = |BUDGETS|class (Attempt|StageFailure)|def (attempts|failure_named|failures_alone|record_failure|_spent|exhausted|check_budget|across)\()' isekai/foundation/failures.py` prints a line for each of the names.
- [ ] 3.3 In `run.py` delete the moved blocks. Import each name of `failures.py` from it, `Kind` and `exhausted` for `refusal_for`; drop each import the move leaves unused, as `ruff check` names them.
  Verify: `git grep -n -E '^(BUDGETS|class (Attempt|StageFailure)|def (attempts|record_failure|check_budget|across)\()' -- isekai/foundation/run.py` prints nothing.
- [ ] 3.4 Check `__all__` against the cut's base, as 1.6 does.
  Verify: `uv run python -c "import ast,subprocess,isekai.foundation.run as r; t=ast.parse(subprocess.run(['git','show','ce753c64:isekai/foundation/run.py'],capture_output=True,check=True).stdout); n={x.name for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and not x.name.startswith('_')}|{y.id for x in t.body if isinstance(x,(ast.Assign,ast.AnnAssign)) for z in (getattr(x,'targets',None) or [x.target]) for y in ast.walk(z) if isinstance(y,ast.Name) and not y.id.startswith('_') and len(y.id)>1}; print(sorted(n-set(r.__all__)), [m for m in r.__all__ if not hasattr(r,m)])"` prints `[] []`.
- [ ] 3.5 In `tests/mutants.json` the entries FN-1, FN-2 and FN-6 take the path `isekai/foundation/failures.py`, their `find` and `replace` unchanged ([D10](design.md#d10)).
  Verify: `grep -c -F 'isekai/foundation/failures.py' tests/mutants.json` prints `3`.
- [ ] 3.6 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` passes.
- [ ] 3.7 Run the record, the ratchets, the layer guards, the documents, the run directory, the package paths and the CLI's tests: no assertion changes.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_run_directory.py tests/test_package_paths.py tests/test_pipeline_cli.py` passes.
- [ ] 3.8 Close with `tools.mutate` on the new module, after `git add -N isekai/foundation/failures.py`. A survivor, those the design lists among [Survivors at the cut](design.md#survivors-at-the-cut) included, is killed by a test or named in [Equivalent mutants](design.md#equivalent-mutants).
  Verify: `uv run python -m tools.mutate isekai/foundation/failures.py:1-400 --tests tests/test_run_directory.py tests/test_caption.py tests/test_tagging.py tests/test_sheet_stage.py tests/test_resume.py tests/test_edit_session.py` exits 0, each survivor it prints named in the design.

## 4 — The documents

- [ ] 4.1 In `docs/decisions.md`, add D62 after D60, as [D9](design.md#d9) writes it, with *Made by* `0152`.
  Verify: `git grep -n -F '### D62 · The run directory is run.py, its siblings imported through it' -- docs/decisions.md` prints a line.
- [ ] 4.2 In D21, the sentence "The numbers are `run.py`'s `BUDGETS`." reads "The numbers are `BUDGETS` of `failures.py`, read through `run.py`." and stays on one line.
  Verify: `grep -n -E 'BUDGETS. of .failures.py.' docs/decisions.md` prints a line.
- [ ] 4.3 In `docs/modules.md`, "`assign` is `foundation/run.py`'s, because a tick is the run's layout" reads "`assign` is `foundation/rundir.py`'s, read through `run.py`, because a tick is the run's layout"; the path stays on one line.
  Verify: `grep -n -F 'foundation/rundir.py' docs/modules.md` prints a line.
- [ ] 4.4 In `docs/modules.md`, the bullet on `StageFailure` reads "`StageFailure` lives in `foundation/failures.py`, read through `run.py`, not `refusal.py`." and ends "… the class needs `Kind`, and `failures.py` already imports `refusal.py`, so the move would be a cycle."; the path stays on one line.
  Verify: `grep -n -F 'foundation/failures.py' docs/modules.md` prints a line.
- [ ] 4.5 In `docs/data-flow.md`, "The names above are `run.py`'s, not each stage's: the run owns the layout." reads "The names above are read from `run.py`, which re-exports `names.py`'s, not each stage's: the run owns the layout."; the word `re-exports` stays on one line.
  Verify: `grep -n -F 're-exports' docs/data-flow.md` prints a line.
- [ ] 4.6 In `isekai/foundation/README.md`, the `run.py` row of *Files* describes the front: it re-exports its siblings' names and holds the roots, `open_run` and `find_run`, `rendered_at`, the command text with `photo_of`, the migration state, `refusal_for`, `instructions_record` and `constant_record`. A row follows it for each sibling: `names.py` (a run's id and the names of its layout), `rundir.py` (`Run`, one photograph's directory and its frame, and `assign`), `layout.py` (numbering and completion, the seeds and the edit files) and `failures.py` (the failure shape the stages share: `Kind`, the budgets, the attempts a directory records, `across` and `StageFailure`, here and not in `refusal.py` because `refusal.py` imports nothing by design and the class needs `Kind`).
  Verify: `grep -n -E '^\| .(names|rundir|layout|failures)\.py. \|' isekai/foundation/README.md` prints a line for each of the siblings.
- [ ] 4.7 In the *Imported by* table of `isekai/foundation/README.md`, add a row for each of `names.py`, `rundir.py`, `layout.py` and `failures.py` after the `run.py` row, each as `` | `<file>` | — | — | ``, then re-derive with `uv run python -m tools.derive_imported_by`.
  Verify: `grep -c -E '^\| .(names|rundir|layout|failures)\.py. \|' isekai/foundation/README.md` prints `8`.
- [ ] 4.8 In the docstring of `isekai/foundation/run.py`, "nothing outside this module decides what a file is called" reads "nothing outside this module and its siblings decides what a file is called", and a paragraph before "Stdlib only" reads: "The siblings `names.py`, `rundir.py`, `layout.py` and `failures.py` hold the identity and the names, the run and its frame, the numbering and the edit files, and the failure budgets. This module imports them and re-exports every name, so a module outside the foundation imports a run's names from here (D62)."
  Verify: `git grep -n -F '(D62)' -- isekai/foundation/run.py` prints a line.
- [ ] 4.9 **HALT CHECK** MT-7's and FN-5's anchors stay in `run.py`: no phase moves the roots or `instructions_record`.
  Verify: `grep -c -E 'DATA_ROOT = Path|if inside else resolved.name,' isekai/foundation/run.py` prints `2`.
- [ ] 4.10 Replay the recorded mutants.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
- [ ] 4.11 Hold the series' conditions: nothing under `tests/record/` differs from the cut's base, and no image-frozen file does.
  Verify: `git diff --exit-code ce753c64 -- tests/record Dockerfile image config/models.json isekai/boundary/provision.py isekai/boundary/pod_start.py` exits 0.
- [ ] 4.12 Hold that no test file is deleted or renamed; a test a survivor needs is added in `tests/test_run_directory.py` or its caller's file ([Survivors at the cut](design.md#survivors-at-the-cut)).
  Verify: `git diff --name-only --diff-filter=DR ce753c64 -- tests` prints nothing.
- [ ] 4.13 Run the documents' and the guards' tests.
  Verify: `uv run pytest tests/test_docs.py tests/test_ratchets.py tests/test_layers.py tests/test_record.py tests/test_run_directory.py tests/test_package_paths.py tests/test_pipeline_cli.py tests/test_ui.py` passes.
