# The verbs move — tasks

The phases take the verbs out of `isekai/interface/cli.py` into `isekai/interface/verbs/`, one row a verb, and the last assembles the rows and amends what the move makes false.

## Progress

- [ ] 1 — The package and the shared module · moderate
- [ ] 2 — The leaf families · moderate
- [ ] 3 — Prepare and generate · moderate
- [ ] 4 — The front door · moderate

## 1 — The package and the shared module

- [ ] 1.1 **HALT CHECK** The premises of [D3](design.md#d3) and [D7](design.md#d7) stand: `_per_item`, `_migrate` and `main` are in `isekai/interface/cli.py`, and its ratchet keys are listed in `tests/test_ratchets.py`.
  Verify: `grep -c "isekai/interface/cli.py" tests/test_ratchets.py` prints `4`.
- [ ] 1.2 Pre-flight the lines phase 1 moves in `isekai/interface/cli.py` as it stands, per [D5](design.md#d5): the argument types, `_cells`, the run helpers, `_once` and the reporter. Kill each survivor.
  Verify: `uv run python -m tools.mutate isekai/interface/cli.py:167-252 isekai/interface/cli.py:737-757 isekai/interface/cli.py:989-992 isekai/interface/cli.py:1001-1028 isekai/interface/cli.py:1172-1198 isekai/interface/cli.py:1533-1583 --tests tests/test_pipeline_cli.py tests/test_progress.py tests/test_assign.py tests/test_render.py tests/test_ink.py` exits 0.
- [ ] 1.3 Add `isekai/interface/verbs/__init__.py`, the front door of [D1](design.md#d1), and `isekai/interface/verbs/common.py` holding `_seed`, `_positive`, `_count`, `_seconds`, `_session_id`, `_depth` and `_Targets`, moved verbatim with their spelling kept ([D4](design.md#d4)).
  Verify: `grep -c -E '^(def _seed|def _positive|def _session_id|def _depth|class _Targets)' isekai/interface/verbs/common.py` prints `5`.
- [ ] 1.4 Move `_Reporter`, `_say`, `_once`, `_run_for`, `_named`, `_require_tracked` and `_cells` into `isekai/interface/verbs/common.py` as `Reporter`, `say`, `once`, `run_for`, `run_or_photo`, `require_tracked` and `parse_cells` ([D4](design.md#d4)); `_existing_run` stays in `isekai/interface/cli.py` and calls `run_or_photo`.
  Verify: `grep -c -E '^(class Reporter|def say|def once|def run_for|def run_or_photo|def require_tracked|def parse_cells)' isekai/interface/verbs/common.py` prints `7`.
- [ ] 1.5 Export every name `isekai/interface/cli.py` still reads from the front door in `__all__`: the argument types its own `build_parser` blocks name, `Reporter`, `say`, `once`, `run_for`, `run_or_photo`, `require_tracked` and `parse_cells`. Import them there, delete each moved definition, and drop the imports it no longer reads ([D1](design.md#d1)).
  Verify: `grep -c -E '^from isekai.interface.verbs import' isekai/interface/cli.py` prints `1`.
- [ ] 1.6 Add a `verbs/` row to the `## Imported by` table of `isekai/interface/README.md`, then re-derive every layer README's table with `uv run python -m tools.derive_imported_by`, which also rewrites `isekai/foundation/README.md`, `isekai/shared/README.md`, `isekai/boundary/README.md` and `isekai/pipeline/README.md`.
  Verify: `uv run pytest tests/test_docs.py -q` exits 0.
- [ ] 1.7 Stage the new files with `git add isekai/interface/verbs/__init__.py isekai/interface/verbs/common.py`, then run the lines of 1.2 on their new home, per [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/common.py:1-600 --tests tests/test_pipeline_cli.py tests/test_progress.py tests/test_assign.py tests/test_render.py tests/test_ink.py` exits 0.
- [ ] 1.8 Bring the record, the ratchets, the layer guards, the docs tests and the entry point's `-S` guard green for the phase's end state, changing no assertion and leaving `tests/record/verbs.json` byte-identical.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py -q` exits 0.

## 2 — The leaf families

- [ ] 2.1 Add `Verb` ([D2](design.md#d2)) with `name`, `arguments` and `run` to `isekai/interface/verbs/common.py`, export it from the front door, and give `isekai/interface/cli.py` an empty tuple `_MOVED` that `build_parser` and `dispatch` read, as [D2](design.md#d2) says.
  Verify: `grep -c '^class Verb' isekai/interface/verbs/common.py` prints `1`.
- [ ] 2.2 Pre-flight the library family in `isekai/interface/cli.py` per [D5](design.md#d5): `_ui`, `_import`, `_staged_line`, the `compare` branch of `dispatch` and the arguments of `import`, `compare` and `ui` in `build_parser`. Run `tools.mutate` over those ranges and kill each survivor.
  Verify: `uv run pytest tests/test_importing.py tests/test_compare.py tests/test_pipeline_cli.py tests/test_record.py -q` exits 0.
- [ ] 2.3 Add `isekai/interface/verbs/library.py` holding `run_import`, `staged_line`, `run_compare`, `run_ui`, `DEFAULT_PORT`, `import_arguments`, `compare_arguments`, `ui_arguments` and the rows `IMPORT_ROW`, `COMPARE_ROW` and `UI_ROW`, moved verbatim ([D4](design.md#d4)); delete them from `isekai/interface/cli.py`, export the rows, put them in `_MOVED` and drop the imports `cli.py` no longer reads.
  Verify: `grep -c -E '^(def run_import|def staged_line|def run_compare|def run_ui|def import_arguments|def compare_arguments|def ui_arguments|IMPORT_ROW = |COMPARE_ROW = |UI_ROW = )' isekai/interface/verbs/library.py` prints `10`.
- [ ] 2.4 Stage `isekai/interface/verbs/library.py` with `git add`, then run the lines of 2.2 on their new home, per [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/library.py:1-600 --tests tests/test_importing.py tests/test_compare.py tests/test_pipeline_cli.py tests/test_record.py` exits 0.
- [ ] 2.5 Pre-flight the drafts family in `isekai/interface/cli.py` per [D5](design.md#d5): `_draft`, `_discard` and the arguments of `draft` and `discard` in `build_parser`. Run `tools.mutate` over those ranges and kill each survivor.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_review.py tests/test_edit_session.py tests/test_record.py -q` exits 0.
- [ ] 2.6 Add `isekai/interface/verbs/drafts.py` holding `run_draft`, `run_discard`, `draft_arguments`, `discard_arguments` and the rows `DRAFT_ROW` and `DISCARD_ROW`, moved as [D4](design.md#d4) says; the lazy `isekai.interface.ui` import stays inside `run_discard`. Delete them from `isekai/interface/cli.py`, export the rows, put them in `_MOVED` and drop the imports `cli.py` no longer reads.
  Verify: `grep -c -E '^(def run_draft|def run_discard|def draft_arguments|def discard_arguments|DRAFT_ROW = |DISCARD_ROW = )' isekai/interface/verbs/drafts.py` prints `6`.
- [ ] 2.7 Stage `isekai/interface/verbs/drafts.py` with `git add`, then run the lines of 2.5 on their new home, per [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/drafts.py:1-600 --tests tests/test_pipeline_cli.py tests/test_review.py tests/test_edit_session.py tests/test_record.py` exits 0.
- [ ] 2.8 Pre-flight the edits family in `isekai/interface/cli.py` per [D5](design.md#d5): `_ink`, `_edit`, `_pending` and the arguments of `ink` and `edit` in `build_parser`. Run `tools.mutate` over those ranges and kill each survivor.
  Verify: `uv run pytest tests/test_ink.py tests/test_edit.py tests/test_edit_session.py tests/test_record.py -q` exits 0.
- [ ] 2.9 Add `isekai/interface/verbs/edits.py` holding `run_ink`, `run_edit`, `run_pending`, `ink_arguments`, `edit_arguments` and the rows `INK_ROW` and `EDIT_ROW`, moved verbatim ([D4](design.md#d4)); delete them from `isekai/interface/cli.py`, export the rows, put them in `_MOVED` and drop the imports `cli.py` no longer reads.
  Verify: `grep -c -E '^(def run_ink|def run_edit|def run_pending|def ink_arguments|def edit_arguments|INK_ROW = |EDIT_ROW = )' isekai/interface/verbs/edits.py` prints `7`.
- [ ] 2.10 Stage `isekai/interface/verbs/edits.py` with `git add`, then run the lines of 2.8 on their new home, per [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/edits.py:1-600 --tests tests/test_ink.py tests/test_edit.py tests/test_edit_session.py tests/test_record.py` exits 0.
- [ ] 2.11 Pre-flight render's arguments in `isekai/interface/cli.py` per [D5](design.md#d5): the blocks of `build_parser` that name `render`. Run `tools.mutate` over those ranges and kill each survivor.
  Verify: `uv run pytest tests/test_render.py tests/test_pipeline_cli.py tests/test_record.py -q` exits 0.
- [ ] 2.12 Add `isekai/interface/verbs/session.py` holding `render_arguments` and the row `RENDER_ROW` with no run ([D3](design.md#d3)); in `isekai/interface/cli.py` put `RENDER_ROW` in `_MOVED` with its run bound to `run_session(args, wired, _dispatch_argv)`, delete the `render` branch of `dispatch` and the arguments moved, and drop the imports `cli.py` no longer reads.
  Verify: `grep -c -E '^(def render_arguments|RENDER_ROW = )' isekai/interface/verbs/session.py` prints `2`.
- [ ] 2.13 Stage `isekai/interface/verbs/session.py` with `git add`, then run the lines of 2.11 on their new home, per [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/session.py:1-600 --tests tests/test_render.py tests/test_pipeline_cli.py tests/test_record.py` exits 0.
- [ ] 2.14 Re-derive every layer README's `## Imported by` table with `uv run python -m tools.derive_imported_by`, which rewrites `isekai/interface/README.md`, `isekai/foundation/README.md`, `isekai/shared/README.md`, `isekai/boundary/README.md` and `isekai/pipeline/README.md`.
  Verify: `uv run pytest tests/test_docs.py -q` exits 0.
- [ ] 2.15 Remove from `tests/test_ratchets.py` each row of `isekai/interface/cli.py` the ratchets now report as `no longer offends`, and lower its `*_ROWS` count, per [D7](design.md#d7); remove no other row.
  Verify: `uv run pytest tests/test_ratchets.py -q` exits 0.
- [ ] 2.16 Bring the record, the ratchets, the layer guards, the docs tests and the entry point's `-S` guard green for the phase's end state, changing no assertion.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py -q` exits 0.

## 3 — Prepare and generate

- [ ] 3.1 Pre-flight `prepare` in `isekai/interface/cli.py` per [D5](design.md#d5): `_prepare` and the arguments of `prepare` in `build_parser`. Run `tools.mutate` over those ranges and kill each survivor.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_resume.py tests/test_record.py -q` exits 0.
- [ ] 3.2 Add `isekai/interface/verbs/prepare.py` holding `run_prepare(args, wired, per_item)`, `prepare_arguments` and the row `PREPARE_ROW` with no run, and `progress_flag` in `isekai/interface/verbs/common.py` ([D4](design.md#d4)); in `isekai/interface/cli.py` put `PREPARE_ROW` in `_MOVED` with its run bound to `run_prepare` and `_per_item` ([D3](design.md#d3)), delete `_prepare` and its arguments, take `prepare` out of every loop of `build_parser` that names it ([D2](design.md#d2)), and drop the imports `cli.py` no longer reads.
  Verify: `grep -c -E '^(def run_prepare|def prepare_arguments|PREPARE_ROW = )' isekai/interface/verbs/prepare.py` prints `3`.
- [ ] 3.3 Stage `isekai/interface/verbs/prepare.py` with `git add`, then run the lines of 3.1 on their new home, per [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/prepare.py:1-600 --tests tests/test_pipeline_cli.py tests/test_resume.py tests/test_record.py` exits 0.
- [ ] 3.4 Pre-flight `generate` in `isekai/interface/cli.py` per [D5](design.md#d5): `_generate` and the arguments of `generate` in `build_parser`. Run `tools.mutate` over those ranges and kill each survivor.
  Verify: `uv run pytest tests/test_generate.py tests/test_resume.py tests/test_record.py -q` exits 0.
- [ ] 3.5 Add `isekai/interface/verbs/generate.py` holding `generate_batch`, `generate_arguments` and the row `GENERATE_ROW` with no run, and `photographs` and `required_flow` in `isekai/interface/verbs/common.py` ([D4](design.md#d4)); in `isekai/interface/cli.py` put `GENERATE_ROW` in `_MOVED`, call `generate_batch` from the tail of `dispatch`, delete `_generate` and its arguments, take `generate` out of every loop of `build_parser` that names it ([D2](design.md#d2)), drop the imports `cli.py` no longer reads, and drop the argument types and their imports from the front door.
  Verify: `grep -c -E '^(def generate_batch|def generate_arguments|GENERATE_ROW = )' isekai/interface/verbs/generate.py` prints `3`.
- [ ] 3.6 Stage `isekai/interface/verbs/generate.py` with `git add`, then run the lines of 3.4 on their new home, per [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/generate.py:1-600 --tests tests/test_generate.py tests/test_resume.py tests/test_record.py` exits 0.
- [ ] 3.7 Re-derive every layer README's `## Imported by` table with `uv run python -m tools.derive_imported_by`, which rewrites `isekai/interface/README.md`, `isekai/foundation/README.md`, `isekai/shared/README.md`, `isekai/boundary/README.md` and `isekai/pipeline/README.md`.
  Verify: `uv run pytest tests/test_docs.py -q` exits 0.
- [ ] 3.8 Remove from `tests/test_ratchets.py` each row of `isekai/interface/cli.py` the ratchets now report as `no longer offends`, and lower its `*_ROWS` count, per [D7](design.md#d7); remove no other row.
  Verify: `uv run pytest tests/test_ratchets.py -q` exits 0.
- [ ] 3.9 Bring the record, the ratchets, the layer guards, the docs tests and the entry point's `-S` guard green for the phase's end state, changing no assertion.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py -q` exits 0.

## 4 — The front door

- [ ] 4.1 Give `Verb` a `summary` field after `name` in `isekai/interface/verbs/common.py` ([D2](design.md#d2)), and fill it in each existing row with the text `VERBS` holds for that verb in `isekai/interface/cli.py`.
  Verify: `grep -c -E '^    summary: str' isekai/interface/verbs/common.py` prints `1`.
- [ ] 4.2 Add `isekai/interface/verbs/stages.py` holding `assign_arguments`, `caption_arguments`, `tag_arguments`, `sheet_arguments`, `review_arguments`, `approve_arguments`, `show_arguments` and the rows `ASSIGN_ROW`, `CAPTION_ROW`, `TAG_ROW`, `SHEET_ROW`, `REVIEW_ROW`, `APPROVE_ROW` and `SHOW_ROW`, each with its summary and no run; take their arguments from the loops of `build_parser` in the order [D2](design.md#d2) fixes, with `hidden_flow` and `new_version_flag` added to `isekai/interface/verbs/common.py`.
  Verify: `grep -c -E '^(ASSIGN_ROW|CAPTION_ROW|TAG_ROW|SHEET_ROW|REVIEW_ROW|APPROVE_ROW|SHOW_ROW) = ' isekai/interface/verbs/stages.py` prints `7`.
- [ ] 4.3 Replace `_MOVED` in `isekai/interface/cli.py` with `ROWS`, every verb's row in the order `VERBS` holds, with `render` and `prepare` bound as in [D3](design.md#d3) and `migrate` declared there with its own arguments function; derive `VERBS` from `ROWS` as a tuple of `(row.name, row.summary)`, and make `build_parser` add each row's arguments to its subparser, deleting its loops. Keep the line `dest="verb", metavar="verb", required=True, parser_class=_Verb` as it stands.
  Verify: `grep -c -E '^ROWS' isekai/interface/cli.py` prints `1`.
- [ ] 4.4 Make `dispatch` in `isekai/interface/cli.py` look the verb's row up in the new `ROWS` and `return row.run(args, wired)` when the row has a run, inside its `try` ([D2](design.md#d2)); drop its remaining branches for such verbs, `migrate` included, and leave the tail for the flow-stage verbs and `generate` as it is.
  Verify: `grep -c 'return row.run(args, wired)' isekai/interface/cli.py` prints `1`.
- [ ] 4.5 Remove from `tests/test_ratchets.py` the rows of `isekai/interface/cli.py` and of its `build_parser` that still stand, and lower `FILE_ROWS` and `FUNCTION_ROWS` for each, per [D7](design.md#d7); the rows of `_per_item` and its `work` stay.
  Verify: `uv run pytest tests/test_ratchets.py -q` exits 0.
- [ ] 4.6 Give the entries `CL-10`, `PA-4`, `PB-6` and `PB-16` of `tests/mutants.json` their new `path` as [D6](design.md#d6) lists, with `find`, `replace` and every other key unchanged.
  Verify: `grep -c -E '"path": "isekai/interface/verbs/(common|generate|edits).py"' tests/mutants.json` prints `4`.
- [ ] 4.7 Add `D58 · A verb is declared once, in its family's module` to `docs/decisions.md` after D56, in the form of the decisions around it, with `Made by: 0145` ([D8](design.md#d8)).
  Verify: `grep -c '^### D58' docs/decisions.md` prints `1`.
- [ ] 4.8 Amend the module docstring of `isekai/interface/cli.py`: it names `isekai/interface/verbs/`, says a verb is a row there, "declared once", and says what stays in the file; amend each docstring and comment of the file and of `isekai/interface/verbs/` that names a moved definition by its old name ([D8](design.md#d8)).
  Verify: `grep -q 'declared once' isekai/interface/cli.py` exits 0.
- [ ] 4.9 Amend `isekai/interface/README.md` ([D8](design.md#d8)): a files-table row for `verbs/` and each of its modules, the `cli.py` row, the lines that name the handlers of `ui`, `migrate` and `discard`, and the sibling note.
  Verify: `grep -q 'verbs/common.py' isekai/interface/README.md` exits 0.
- [ ] 4.10 Amend the `interface` bullet of `ARCHITECTURE.md` to say the CLI's verbs live in `interface/verbs/`, one row each ([D8](design.md#d8)).
  Verify: `grep -q 'interface/verbs' ARCHITECTURE.md` exits 0.
- [ ] 4.11 Amend `isekai/README.md` ([D8](design.md#d8)): the interface row names `verbs/` and its modules, and the line on sub-packages' front doors names `interface/verbs/__init__.py`.
  Verify: `grep -q 'verbs/' isekai/README.md` exits 0.
- [ ] 4.12 Amend `docs/modules.md` ([D8](design.md#d8)): the lazy edge names `run_ui` and `run_discard` of the package and `_migrate` of `cli.py`, and the notes that name `cli.py`'s `_ui`, reporter, `ink` verb and `edit` verb name the package's modules; the graph shows `interface/verbs/`.
  Verify: `grep -q 'interface/verbs/' docs/modules.md` exits 0.
- [ ] 4.13 Amend the known breaks of `docs/principles.md` that name `interface/cli.py`'s `_once` and `_discard` to name `once` of `interface/verbs/common.py` and `run_discard` of `interface/verbs/drafts.py` ([D8](design.md#d8)).
  Verify: `grep -q 'interface/verbs/common.py' docs/principles.md` exits 0.
- [ ] 4.14 Re-derive every layer README's `## Imported by` table with `uv run python -m tools.derive_imported_by`, which rewrites `isekai/interface/README.md`, `isekai/foundation/README.md`, `isekai/shared/README.md`, `isekai/boundary/README.md` and `isekai/pipeline/README.md`.
  Verify: `uv run pytest tests/test_docs.py -q` exits 0.
- [ ] 4.15 Bring the record, the ratchets, the layer guards, the docs tests, the migrate tests and the entry point's `-S` guard green for the version's end state, changing no assertion.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_migrate.py tests/test_pipeline_cli.py -q` exits 0.
- [ ] 4.16 Replay the audit's mutants over the moved entries and the rest, per [D6](design.md#d6), staging each new module first with `git add`.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
