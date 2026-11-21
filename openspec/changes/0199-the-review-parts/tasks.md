# The review parts — tasks

Move the review stage's approval, drafts and cancel out of `isekai/pipeline/review/__init__.py` into `approval.py`, `drafts.py` and `cancelling.py`, shorten `approve`, give `draft_across` a keyword `seed`, and take the stage's rows out of the ratchets. No moved line changes but `approve`'s warning block, which becomes `_window_warnings`.

## Progress

- [x] 1 — The approval · moderate
- [x] 2 — The drafts · moderate
- [x] 3 — The cancel · moderate
- [ ] 4 — The decision and the documents · moderate

## 1 — The approval

- [x] 1.1 Run `git grep -n -e "^def approve" -e "^    return path, warnings" -- isekai/pipeline/review/__init__.py`: the number of its first line is `<first>` and of its last `<last>`, below.
  Verify: the same command prints two lines.
- [x] 1.2 Before any line moves, run the pre-flight over `approve` ([D5](design.md#d5)): `uv run python -m tools.mutate isekai/pipeline/review/__init__.py:<first>-<last> --tests tests/test_review.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py`. Kill each survivor with a case in `tests/test_review.py`, carrying the `spec` marker its neighbours carry.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [x] 1.3 Move `DISCARD` with its comment from `isekai/pipeline/review/__init__.py` to `isekai/pipeline/review/records.py`, after `STAGE` ([D3](design.md#d3)). Import it plainly in the front door from `isekai.pipeline.review.records`.
  Verify: `grep -n -e "^DISCARD = " isekai/pipeline/review/records.py` prints one line.
- [x] 1.4 Create `isekai/pipeline/review/approval.py`: a docstring saying it holds `approve` and its helpers and imports `records.py` and `budget.py` and neither the front door nor another part. Its imports: `Mapping` and `Sequence` from `collections.abc`; `Path`; `cast` from `typing`; from `isekai.foundation.artifacts` `APPROVED_FILE`, `DRAFT_FILE`, `SHEET_FILE`, `ApprovedProducer`, `Renders`, `ReviewApproved`, `read`, `renders_of` and `require`; `OUTPUT_SUFFIX`, `Flow` and `Schema` from `isekai.foundation.flow`; `Refusal`; from `isekai.foundation.run` `APPROVED`, `NEW_VERSION`, `REVIEW`, `SHEETS`, `Run`, `approval_of`, `approved_versions`, `artifact_name`, `current_draft`, `group_of`, `is_rendered`, `latest`, `latest_artifact`, `next_version`, `sheet_of`, `stage_command` and `version_of`; `validate` from `isekai.shared.fields`; `Vocabulary` from `isekai.shared.vocabulary`; from `isekai.pipeline.review.records` `DISCARD`, `STAGE`, `_again`, `_differs`, `_publish`, `_recopy`, `came_from`, `copied_renders`, `is_copy` and `same_fields`; from `isekai.pipeline.review.budget` `ENCODER_WINDOW`, `estimate_tokens` and `token_budget`. Run `git add isekai/pipeline/review/approval.py`: `tools.mutate` copies tracked files only.
  Verify: `uv run python -c "import isekai.pipeline.review.approval"` exits 0.
- [x] 1.5 Move from `isekai/pipeline/review/__init__.py` into `isekai/pipeline/review/approval.py`, in the order of their lines, unchanged with their docstrings and comments: `approve`, `_NOT_COPIED` with its comment, `_copy_approval`, `_refuse_unchanged`, `_resheet` ([D2](design.md#d2)). Delete them from the front door.
  Verify: `uv run python -c "from isekai.pipeline.review.approval import approve, _NOT_COPIED, _copy_approval, _refuse_unchanged, _resheet"` exits 0.
- [x] 1.6 Add `_window_warnings` to `approval.py` directly above `approve`, as [D5](design.md#d5) gives it, with a one-line docstring and the block's lines unchanged. In `approve` replace the block with `warnings = _window_warnings(run, flow, fields, schema, definition)`.
  Verify: `grep -n -e "^def _window_warnings" -e "^def approve" isekai/pipeline/review/approval.py` prints two lines.
- [x] 1.7 In the front door import `approve` from `isekai.pipeline.review.approval` as `approve as approve` ([D7](design.md#d7)). Run `uv run ruff check isekai/pipeline/review`: it names each import no code reads. In `__init__.py` rewrite as `X as X`, one statement each, a name [D7](design.md#d7) lists, and delete every other by hand. Then run `uv run ruff check --fix isekai/pipeline/review` and `uv run ruff format isekai/pipeline/review`.
  Verify: `uv run ruff check isekai/pipeline/review` exits 0.
- [x] 1.8 `approval.py` imports no part and not the front door.
  Verify: `grep -n -e "review.drafts" -e "review.cancelling" -e "pipeline.review import" isekai/pipeline/review/approval.py` prints nothing.
- [x] 1.9 In `tests/mutants.json` set `path` in `PB-2` so it holds `"path": "isekai/pipeline/review/approval.py"` ([D9](design.md#d9)). Its `find` and `replace` stay.
  Verify: `git grep -n -F '"path": "isekai/pipeline/review/approval.py"' -- tests/mutants.json` prints one line.
- [x] 1.10 In `tests/test_ratchets.py` delete the `LONG_FILES` row `isekai/pipeline/review/__init__.py` and the `LONG_FUNCTIONS` row `isekai/pipeline/review/__init__.py::approve`, and set `FILE_ROWS` and `FUNCTION_ROWS` to the rows left.
  Verify: `git grep -n -e "^    .isekai/pipeline/review" -- tests/test_ratchets.py` prints nothing.
- [x] 1.11 **HALT CHECK** The front door is under the long-file ceiling and `approve` under the long-function one, so no row stands for either. A failure means the move differs from what the plan names.
  Verify: `uv run pytest tests/test_ratchets.py tests/test_layers.py` exits 0.
- [x] 1.12 Run `uv run python -m tools.derive_imported_by`: `approval.py` imports the artifacts, the flow, the run and the shared fields, so the derived tables of the layer READMEs change.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 1.13 Run `grep -n -e "^def _window_warnings" -e "^    return path, warnings" isekai/pipeline/review/approval.py`, then the pre-flight over those lines ([D5](design.md#d5)): `uv run python -m tools.mutate isekai/pipeline/review/approval.py:<first>-<last> --tests tests/test_review.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py`, `<first>` and `<last>` the numbers it printed. Kill each survivor with a case in `tests/test_review.py`.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [x] 1.14 Confirm the suite reads each name through the front door.
  Verify: `uv run pytest tests/test_review.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py` exits 0.

## 2 — The drafts

- [x] 2.1 Create `isekai/pipeline/review/drafts.py`: a docstring saying it holds the drafts and what refuses them and imports `records.py` and neither the front door nor another part. Its imports: `shlex`; `Sequence` from `collections.abc`; `Path`; from `isekai.foundation.artifacts` `DRAFT_FILE`, `ONE_RENDER`, `SHEET_FILE`, `Renders`, `ReviewApproved`, `Sheet`, `read`, `renders_of` and `require`; `write_atomically` from `isekai.foundation.atomic_write`; `OUTPUT_SUFFIX` and `Schema` from `isekai.foundation.flow`; `Refusal`; from `isekai.foundation.run` `APPROVED`, `NEW_VERSION`, `REVIEW`, `SHEETS`, `RenderRef`, `Run`, `approval_of`, `approved_versions`, `artifact_name`, `current_draft`, `group_of`, `is_rendered`, `latest`, `next_version`, `render_image`, `sheet_of`, `source_copy`, `stage_command`, `version_of` and `versions`; from `isekai.pipeline.review.records` `DISCARD`, `STAGE`, `_again`, `_approval`, `_differs`, `_draft_command`, `_first_image`, `_write_draft` and `copied_renders`. Run `git add isekai/pipeline/review/drafts.py`.
  Verify: `uv run python -c "import isekai.pipeline.review.drafts"` exits 0.
- [x] 2.2 Move from `isekai/pipeline/review/__init__.py` into `isekai/pipeline/review/drafts.py`, in the order of their lines, unchanged with their docstrings and comments: `review`, `revise`, `_DRAFT_AGAIN` with its comment, `draft_from`, `drafting_sheet`, `drafting_approval`, `_held_way`, `waiting_edit`, `_refuse_edited`, `_waiting_number`, `_discarding`, `_edited`, `Revision` with its comment, `refuse_drafts`, `refuse_revision` ([D2](design.md#d2)). Delete them from the front door.
  Verify: `uv run python -c "from isekai.pipeline.review.drafts import review, revise, _DRAFT_AGAIN, draft_from, drafting_sheet, drafting_approval, _held_way, waiting_edit, _refuse_edited, _waiting_number, _discarding, _edited, Revision, refuse_drafts, refuse_revision"` exits 0.
- [x] 2.3 In the front door import from `isekai.pipeline.review.drafts`, as `X as X` one statement each, `Revision`, `draft_from`, `drafting_approval`, `drafting_sheet`, `refuse_drafts`, `refuse_revision`, `review`, `revise` and `waiting_edit`. Then run the steps of 1.7: `ruff check` names each import no code reads, `__init__.py` re-binds a name [D7](design.md#d7) lists and drops every other, `ruff --fix` and `ruff format` sort the rest.
  Verify: `uv run ruff check isekai/pipeline/review` exits 0.
- [x] 2.4 `drafts.py` imports no part and not the front door.
  Verify: `grep -n -e "review.approval" -e "review.cancelling" -e "pipeline.review import" isekai/pipeline/review/drafts.py` prints nothing.
- [x] 2.5 In `isekai/interface/drafting.py` put `*,` on its own line in `draft_across`'s parameters, before `seed: int,`, and pass `seed=seed` in the call of `draft_from_image` ([D6](design.md#d6)).
  Verify: `git grep -n -F "seed=seed" -- isekai/interface/drafting.py` prints one line.
- [x] 2.6 In `tests/test_ratchets.py` delete the `WIDE_FUNCTIONS` row `isekai/interface/drafting.py::draft_across` and set `WIDE_ROWS` to the rows left.
  Verify: `git grep -n -F "drafting.py::draft_across" -- tests/test_ratchets.py` prints nothing.
- [x] 2.7 In `tests/test_artifact_bytes.py` change the key of `BYTE_WRITERS`, `"isekai/pipeline/review/__init__.py"`, to `"isekai/pipeline/review/drafts.py"`, its text as it stands. `draft_from` calls `write_atomically` for a draft's source copy.
  Verify: `git grep -n -F '"isekai/pipeline/review/drafts.py"' -- tests/test_artifact_bytes.py` prints one line.
- [x] 2.8 In `tests/mutants.json` set `path` in `PB-5` so it holds `"path": "isekai/pipeline/review/drafts.py"` ([D9](design.md#d9)). Its `find` and `replace` stay.
  Verify: `git grep -n -F '"path": "isekai/pipeline/review/drafts.py"' -- tests/mutants.json` prints one line.
- [x] 2.9 Run `uv run python -m tools.derive_imported_by`: `drafts.py` imports `write_atomically`, the artifacts, the flow and the run, so the derived tables change.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 2.10 Run the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [x] 2.11 Confirm the suite reads each name through the front door, and the byte writers' scan finds `drafts.py`.
  Verify: `uv run pytest tests/test_review.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py` exits 0.

## 3 — The cancel

- [x] 3.1 Create `isekai/pipeline/review/cancelling.py`: a docstring saying it holds the discard and the cancel and imports `records.py` and neither the front door nor another part. Its imports: `Path`; `NamedTuple` from `typing`; `ReviewApproved` and `require` from `isekai.foundation.artifacts`; `Refusal`; from `isekai.foundation.run` `APPROVED`, `DRAFT`, `PROMPTS`, `REVIEW`, `Run`, `approval_of`, `approved_versions`, `artifact_name`, `attempts`, `current_draft`, `group_of`, `latest_artifact`, `source_copy`, `stage_command` and `version_of`; from `isekai.pipeline.review.records` `DISCARD`, `STAGE`, `_again`, `_approval`, `_draft_command`, `_first_image`, `_write_draft`, `draft_image` and `is_copy`. Run `git add isekai/pipeline/review/cancelling.py`.
  Verify: `uv run python -c "import isekai.pipeline.review.cancelling"` exits 0.
- [x] 3.2 Move from `isekai/pipeline/review/__init__.py` into `isekai/pipeline/review/cancelling.py`, in the order of their lines, unchanged with their docstrings and comments: `CANCEL` with its comment, `Cancelled`, `discard`, `cancellable`, `cancel`, `_at_draft`, `_cancelling`, `_derived` ([D2](design.md#d2), [D3](design.md#d3)). Delete them from the front door.
  Verify: `uv run python -c "from isekai.pipeline.review.cancelling import CANCEL, Cancelled, discard, cancellable, cancel, _at_draft, _cancelling, _derived"` exits 0.
- [x] 3.3 In `isekai/pipeline/review/__init__.py` import from `isekai.pipeline.review.cancelling`, as `X as X` one statement each, `Cancelled`, `cancel`, `cancellable` and `discard`. Then run the steps of 1.7. The names that go unread in this phase and that [D7](design.md#d7) keeps for tests and importers are `DRAFT`, `current_draft` and `source_copy` of `isekai.foundation.run` and `draft_image` of `records.py`: re-bind each `X as X`. Drop each private name of `records.py`.
  Verify: `uv run ruff check isekai/pipeline/review` exits 0.
- [x] 3.4 `cancelling.py` imports no part and not the front door.
  Verify: `grep -n -e "review.approval" -e "review.drafts" -e "pipeline.review import" isekai/pipeline/review/cancelling.py` prints nothing.
- [x] 3.5 In `tests/mutants.json` set `path` in `PB-14` so it holds `"path": "isekai/pipeline/review/cancelling.py"` ([D9](design.md#d9)). Its `find` and `replace` stay.
  Verify: `git grep -n -F '"path": "isekai/pipeline/review/cancelling.py"' -- tests/mutants.json` prints one line.
- [x] 3.6 The front door defines `state` and no other function or class, and `Status`.
  Verify: `git grep -c -e "^def " -e "^class " -- isekai/pipeline/review/__init__.py` prints `isekai/pipeline/review/__init__.py:1`.
- [x] 3.7 **HALT CHECK** No part closes a cycle and no file or function of the stage is past a ceiling with no row. A failure means a move differs from what the plan names.
  Verify: `uv run pytest tests/test_layers.py tests/test_ratchets.py` exits 0.
- [x] 3.8 Run `uv run python -m tools.derive_imported_by`: `cancelling.py` imports the artifacts, the refusal and the run, so the derived tables change.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 3.9 Run the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [x] 3.10 Confirm the suite reads each name through the front door.
  Verify: `uv run pytest tests/test_review.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py tests/test_derive_wire.py` exits 0.

## 4 — The decision and the documents

- [ ] 4.1 In `docs/decisions.md` amend D77: replace its bold rule with the one [D10](design.md#d10) gives, its *Accepts* with the one there, and its *Made by* with `0198`, `0199`. Its *Why* stays. Find it with `git grep -n -F "### D77" -- docs/decisions.md`.
  Verify: `git grep -c -F "cancelling.py" -- docs/decisions.md` prints `docs/decisions.md:1`.
- [ ] 4.2 In `isekai/pipeline/README.md` change the Files row of `review/` so it names each module: the front door `__init__.py` holds `Status`, `state` and the re-exports; `drafts.py` the drafts and what refuses them; `approval.py` `approve`; `cancelling.py` the discard and the cancel; `records.py` and `budget.py` as they stand.
  Verify: `git grep -c -F "cancelling.py" -- isekai/pipeline/README.md` prints `isekai/pipeline/README.md:1`.
- [ ] 4.3 Run `uv run python -m tools.derive_imported_by`, which writes the derived tables again.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 4.4 Confirm `approval.py` holds `approve`.
  Verify: `git grep -n -e "^def approve" -- isekai/pipeline/review/approval.py` prints one line.
- [ ] 4.5 Confirm no row of the ratchets names the stage.
  Verify: `git grep -n -e "^    .isekai/pipeline/review" -- tests/test_ratchets.py` prints nothing.
- [ ] 4.6 Confirm each name [D7](design.md#d7) lists is importable from the front door, and `Status` is defined there, so the page's `ReviewStatus` keeps its module; `ui/src/wire.ts` is held by the deriver's test.
  Verify: `uv run python -c "from isekai.pipeline.review import Status, state, Cancelled, Revision, approve, cancel, cancellable, discard, draft_from, drafting_approval, drafting_sheet, refuse_drafts, refuse_revision, review, revise, waiting_edit, save_draft, came_from, draft_image, ENCODER_WINDOW, estimate_tokens, TokenBudget, token_budget, DRAFT, current_draft, source_copy, withdraw"` exits 0.
- [ ] 4.7 Run the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [ ] 4.8 Confirm the suite, the layer rules, the docs and the wire hold at the end.
  Verify: `uv run pytest tests/test_review.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py tests/test_spec_bindings.py tests/test_derive_wire.py` exits 0.
