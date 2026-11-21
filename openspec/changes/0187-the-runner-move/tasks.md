# The runner move — tasks

Pin the moving lines by mutation, move the runner from [`isekai/interface/cli.py`](../../../isekai/interface/cli.py) to `isekai/interface/verbs/runner.py`, bind `prepare`'s run in its own module, then replay the mutation and amend the documents.

## Progress

- [ ] 1 — Pin the moving lines by mutation · moderate
- [ ] 2 — Move the runner to `verbs/runner.py` · moderate
- [ ] 3 — Bind `prepare`'s run in its own module · moderate
- [ ] 4 — Replay the mutation and amend the documents · moderate

## 1 — Pin the moving lines by mutation

- [ ] 1.1 **HALT CHECK** The premise of [D1](design.md#d1) stands: the runner cut's code is in `isekai/interface/cli.py`, where the mutation runs of 1.3 and 1.4 read it.
  Verify: `git grep -n -e '^class _Item' -e '^def _item_of' -e '^_BUILDERS' -e '^def _run_item' -- isekai/interface/cli.py` prints a line for each.

- [ ] 1.2 Find the lines of the moving code: `_existing_run` ends one line before `_flows_for`, and `_seam` through `_assign_one` end one line before `main`.
  Verify: `git grep -n -e '^def _existing_run' -e '^def _flows_for' -e '^def _seam(' -e '^def main(' -- isekai/interface/cli.py` prints a line for each, in that order.

- [ ] 1.3 Run the mutation over `_existing_run`, per [D6](design.md#d6): `uv run python -m tools.mutate isekai/interface/cli.py:<first>-<last> --tests tests/test_pipeline_cli.py tests/test_progress.py tests/test_resume.py tests/test_tagging.py tests/test_assign.py tests/test_review.py`, `<first>` the line of `def _existing_run` and `<last>` one less than the line of `def _flows_for`, both from 1.2. Kill each survivor with a case in `tests/test_pipeline_cli.py`; a survivor no case can kill is named equivalent, with its reason, in the commit body.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

- [ ] 1.4 Run the same command over `_seam` through `_assign_one`: `<first>` the line of `def _seam(` and `<last>` one less than the line of `def main(`, both from 1.2, the survivors handled as in 1.3.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

## 2 — Move the runner to `verbs/runner.py`

- [ ] 2.1 **HALT CHECK** The premise of [D2](design.md#d2) and [D3](design.md#d3) stands: no test, tool or evaluation file reads a name that moves but `_per_item`, which the runner cut's cases import from `isekai.interface.cli`.
  Verify: `git grep -n -w -e _seam -e _existing_run -e _assign_one -e _prepare -e _item_of -e _run_item -- tests tools evaluation` prints nothing.

- [ ] 2.2 Add `isekai/interface/verbs/runner.py` with a module docstring, the imports the moved code reads, taken from the modules `cli.py` takes them from and the verbs' own through `isekai.interface.verbs.common`, and `T = TypeVar("T")`, per [D1](design.md#d1) and [D5](design.md#d5).
  Verify: `grep -n -F 'T = TypeVar("T")' isekai/interface/verbs/runner.py` prints one line.

- [ ] 2.3 Copy into `isekai/interface/verbs/runner.py`, in the order of [D1](design.md#d1) and text for text, `_existing_run`, `_seam`, the runner cut's block from `_Item` to `_run_item`, `_per_item`, `_assign` and `_assign_one`.
  Verify: `grep -n -e '^def _per_item' -e '^def _existing_run' -e '^def _seam' -e '^def _assign' isekai/interface/verbs/runner.py` prints a line for `_per_item`, `_existing_run`, `_seam`, `_assign` and `_assign_one`.

- [ ] 2.4 Delete from `isekai/interface/cli.py` everything copied in 2.3, `_Item` with its decorator included.
  Verify: `git grep -n -e '^def _per_item' -e '^def _seam' -e '^def _assign' -e '^def _existing_run' -e '^class _Item' -e '^def _run_item' -- isekai/interface/cli.py` prints nothing.

- [ ] 2.5 In `isekai/interface/verbs/__init__.py` import `_per_item` from `isekai.interface.verbs.runner` and list it in `__all__`, per [D2](design.md#d2); in `isekai/interface/cli.py` read it from `isekai.interface.verbs` and drop the imports and `T` that nothing left in the file reads, per [D5](design.md#d5).
  Verify: `uv run ruff check isekai/interface` exits 0.

- [ ] 2.6 Derive the *Imported by* tables again per [D7](design.md#d7): `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.

- [ ] 2.7 In `tests/mutants.json` change the `path` of `PB-2b` to `isekai/interface/verbs/runner.py`, per [D6](design.md#d6); its `find`, `replace`, `tests` and `why` stand.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

## 3 — Bind `prepare`'s run in its own module

- [ ] 3.1 In `isekai/interface/verbs/prepare.py` delete `PerItem` and the `per_item` parameter of `run_prepare`, and call `_per_item`, imported from `isekai.interface.verbs.runner`, where `run_prepare` called `per_item`, per [D3](design.md#d3); drop the imports nothing left in the file reads, and name `_per_item` in the docstring where it names `per_item`.
  Verify: `git grep -n -F 'PerItem' -- isekai/interface/verbs/prepare.py` prints nothing.

- [ ] 3.2 In `isekai/interface/verbs/prepare.py` pass `run_prepare` as the `run` of the `Verb` in `PREPARE_ROW`, on a line of its own, and change the module docstring's "with no run bound" to say the row carries its run.
  Verify: `grep -n -e '^    run_prepare,' isekai/interface/verbs/prepare.py` prints one line.

- [ ] 3.3 In `isekai/interface/verbs/__init__.py` stop importing and listing `run_prepare`.
  Verify: `git grep -n -F 'run_prepare' -- isekai/interface/verbs/__init__.py` prints nothing.

- [ ] 3.4 In `isekai/interface/cli.py` delete `_prepare`, put `PREPARE_ROW` in `ROWS` as it is, with no `dataclasses.replace`, and drop the import of `run_prepare` and each import nothing left in the file reads.
  Verify: `git grep -n -e '^def _prepare' -e 'run_prepare' -- isekai/interface/cli.py` prints nothing.

- [ ] 3.5 Derive the *Imported by* tables again, as in 2.6, now that `prepare.py` and `isekai/interface/cli.py` have changed their imports: `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.

- [ ] 3.6 Check the package's lint, formatting and imports.
  Verify: `uv run ruff check isekai/interface` exits 0.

## 4 — Replay the mutation and amend the documents

- [ ] 4.1 Find the lines of the moved code in its new home: `_existing_run` is its first definition and `_assign_one` its last.
  Verify: `grep -n -e '^def _existing_run' -e '^def _assign_one' isekai/interface/verbs/runner.py` prints a line for each.

- [ ] 4.2 Run the mutation over the new home, per [D6](design.md#d6): `uv run python -m tools.mutate isekai/interface/verbs/runner.py:<first>-<last> --tests tests/test_pipeline_cli.py tests/test_progress.py tests/test_resume.py tests/test_tagging.py tests/test_assign.py tests/test_review.py`, `<first>` the line of `def _existing_run` and `<last>` the last line of `_assign_one`, both from 4.1. Kill each survivor with a case in `tests/test_pipeline_cli.py`; a survivor no case can kill is named equivalent, with its reason, in the commit body.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

- [ ] 4.3 In `docs/decisions.md` amend D58 per [D4](design.md#d4): its *Accepts* no longer names `_per_item` or `prepare`, names the runs of `render` and `migrate` alone, bound in `cli.py` because they need `_dispatch_argv` and the `RUNS_ROOT` and `wiring` the tests patch there, and reopens when a version moves `_dispatch_argv`; its *Made by* gains `0187`. No decision is added.
  Verify: `git grep -n -F '_per_item' -- docs/decisions.md` prints nothing.

- [ ] 4.4 In `isekai/interface/README.md` add the *Files* row of `verbs/runner.py` and rewrite the rows of `cli.py` and `verbs/__init__.py`: `cli.py` no longer keeps the per-item work or `prepare`'s run, and the front door lists the rows, `_per_item` and the shared names.
  Verify: `git grep -n -e '^| .verbs/runner.py. |' -- isekai/interface/README.md` prints one line.

- [ ] 4.5 In `isekai/README.md` add `runner.py` to the list of `verbs/` in the `interface/` row.
  Verify: `git grep -n -F 'runner.py' -- isekai/README.md` prints one line.

- [ ] 4.6 In the docstring of `isekai/interface/cli.py` replace the sentence that says it keeps the flow stages' per-item work and the runs of `render` and `prepare` with one that says the runner is `verbs/runner.py` and this file keeps `migrate` and the run of `render`.
  Verify: `git grep -n -F 'per-item work' -- isekai/interface/cli.py` prints nothing.
