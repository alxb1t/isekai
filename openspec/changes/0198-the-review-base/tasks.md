# The review base — tasks

Make `review` a package: move `isekai/pipeline/review.py` to `isekai/pipeline/review/__init__.py`, move the token budget and the draft's records into modules beside it, and keep every name importable from `isekai.pipeline.review`. No moved line changes but `_write_draft`'s parameters.

## Progress

- [x] 1 — The package · moderate
- [ ] 2 — The token budget · moderate
- [ ] 3 — The records · moderate
- [ ] 4 — The decision and the documents · moderate

## 1 — The package

- [x] 1.1 Run `mkdir isekai/pipeline/review`, then `git mv isekai/pipeline/review.py isekai/pipeline/review/__init__.py`. The text does not change ([D1](design.md#d1)).
  Verify: `git ls-files isekai/pipeline/review/__init__.py` prints that path.
- [x] 1.2 In `tests/test_ratchets.py` change each key that names `isekai/pipeline/review.py` to `isekai/pipeline/review/__init__.py`, each number as it stands: the row of `LONG_FILES`, the `::approve` row of `LONG_FUNCTIONS` and the `::_write_draft` row of `WIDE_FUNCTIONS`.
  Verify: `git grep -n -e "^    .isekai/pipeline/review.py" -- tests/test_ratchets.py` prints nothing.
- [x] 1.3 In `tests/test_artifact_bytes.py` change the key of `BYTE_WRITERS`, `"isekai/pipeline/review.py"`, to `"isekai/pipeline/review/__init__.py"`, its text as it stands. The front door still calls `write_atomically` for a draft's source copy.
  Verify: `git grep -n -F '"isekai/pipeline/review.py"' -- tests/test_artifact_bytes.py` prints nothing.
- [x] 1.4 In `tests/mutants.json` set `path` to `isekai/pipeline/review/__init__.py` in each entry holding `"path": "isekai/pipeline/review.py"`: `PB-14`, `PB-5`, `PB-1a`, `PB-1b`, `PB-2`, `PB-3a` and `PB-3b` ([D8](design.md#d8)). No `find` changes.
  Verify: `git grep -n -F '"path": "isekai/pipeline/review.py"' -- tests/mutants.json` prints nothing.
- [x] 1.5 In `isekai/pipeline/README.md` change `review.py` to `review/` in the first cell of the Files row and of the Imported by row, and in the sentence "`review.py` holds `review`, `approve` …".
  Verify: `git grep -n -F "review.py" -- isekai/pipeline/README.md` prints nothing.
- [x] 1.6 In `isekai/README.md` change `review.py` to `review/` in the `pipeline/` row.
  Verify: `git grep -n -F "review.py" -- isekai/README.md` prints nothing.
- [x] 1.7 Run `uv run python -m tools.derive_imported_by`: each importer of the stage is now `isekai/pipeline/review/__init__.py`, so the derived tables of the layer READMEs change, and `tests/test_docs.py` holds each to the import graph.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 1.8 Run the mutants the repository keeps: each re-pointed entry finds its text once in the front door.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [x] 1.9 Confirm the suite reads every name through the front door, `Status` still derives the page's `ReviewStatus`, and `Status` is still defined there.
  Verify: `uv run pytest tests/test_review.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py tests/test_spec_bindings.py tests/test_derive_wire.py` exits 0.

## 2 — The token budget

- [ ] 2.1 Create `isekai/pipeline/review/budget.py`: a docstring saying it holds the token budget of a sheet and imports nothing of the front door; the imports `Mapping` and `Sequence` from `collections.abc`, `dataclass` from `dataclasses`, and `Flow`, `Schema` and `assemble` from `isekai.foundation.flow`; then, copied from `isekai/pipeline/review/__init__.py` in this order, unchanged with their comments and docstrings: `ENCODER_WINDOW`, `estimate_tokens`, `TokenBudget`, `token_budget`. Run `git add isekai/pipeline/review/budget.py`: `tools.mutate` copies tracked files only.
  Verify: `uv run python -c "from isekai.pipeline.review.budget import ENCODER_WINDOW, estimate_tokens, TokenBudget, token_budget"` exits 0.
- [ ] 2.2 In `isekai/pipeline/review/__init__.py` delete the definitions that 2.1 copied into `isekai/pipeline/review/budget.py`, with the comment of the constant. Import the constant, `estimate_tokens` and `token_budget` from `isekai.pipeline.review.budget` plainly, and `TokenBudget` as `TokenBudget as TokenBudget`, as [D7](design.md#d7) says.
  Verify: `git grep -n -e "^def estimate_tokens" -e "^def token_budget" -e "^class TokenBudget" -e "^ENCODER_WINDOW =" -- isekai/pipeline/review/__init__.py` prints nothing.
- [ ] 2.3 In `isekai/pipeline/review/__init__.py` delete by hand the imports nothing there reads now: `dataclass` and `assemble`. Then run `uv run ruff check --fix isekai/pipeline/review` and `uv run ruff format isekai/pipeline/review`, which sort the imports of both files; ruff removes no unused import from an `__init__.py`. `budget.py` imports nothing of the front door.
  Verify: `uv run ruff check isekai/pipeline/review` exits 0.
- [ ] 2.4 In `tests/mutants.json` set `path` to `isekai/pipeline/review/budget.py` in `PB-1a` and `PB-1b`, so each holds `"path": "isekai/pipeline/review/budget.py"`. `PB-2` stays in the front door, where `approve` is.
  Verify: `git grep -n -F '"path": "isekai/pipeline/review/budget.py"' -- tests/mutants.json` prints two lines.
- [ ] 2.5 Run `uv run python -m tools.derive_imported_by`: `budget.py` now imports the flow, so the derived tables change.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 2.6 Confirm each name is still importable from the front door, and is the one `budget.py` defines.
  Verify: `uv run python -c "from isekai.pipeline.review import ENCODER_WINDOW, estimate_tokens, TokenBudget, token_budget; assert token_budget.__module__ == TokenBudget.__module__ == 'isekai.pipeline.review.budget'"` exits 0.
- [ ] 2.7 Run the mutants the repository keeps, and the suite.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [ ] 2.8 Confirm the suite still reads each name through the front door.
  Verify: `uv run pytest tests/test_review.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py` exits 0.

## 3 — The records

- [ ] 3.1 Create `isekai/pipeline/review/records.py`: a docstring saying it holds the draft's and the approval's reads and writes and the helpers the stage's parts share, and imports no part and not the front door. Its imports are `shlex`; `Mapping` and `Sequence` from `collections.abc`; `Path` from `pathlib`; `cast` from `typing`; from `isekai.foundation.artifacts` `APPROVED_FILE`, `DRAFT_FILE`, `SHEET_FILE`, `DraftImage`, `Renders`, `ReviewApproved`, `ReviewDraft`, `Sheet`, `create`, `read`, `renders_of`, `require` and `write`; `OUTPUT_SUFFIX` from `isekai.foundation.flow`; `Refusal` from `isekai.foundation.refusal`; and from `isekai.foundation.run` `DRAFT`, `NEW_VERSION`, `REVIEW`, `Run`, `approval_of`, `artifact_name`, `current_draft`, `group_of`, `next_version`, `render_image`, `rendered_seeds` and `stage_command`. Run `git add isekai/pipeline/review/records.py`: `tools.mutate` copies tracked files only.
  Verify: `uv run python -c "import isekai.pipeline.review.records"` exits 0.
- [ ] 3.2 Move into `records.py`, after `STAGE = "review"`, in the order of their lines in `isekai/pipeline/review/__init__.py`, unchanged with their docstrings and comments: `_first_image`, `_draft_command`, `_approval`, `_write_draft`, `save_draft`, `_publish`, `_again`, `_recopy`, `_differs`, `same_fields`, `draft_image`, `came_from`, `is_copy`, `copied_renders` ([D2](design.md#d2)). Delete them and `STAGE` from the front door.
  Verify: `uv run python -c "from isekai.pipeline.review.records import STAGE, _first_image, _draft_command, _approval, _write_draft, save_draft, _publish, _again, _recopy, _differs, same_fields, draft_image, came_from, is_copy, copied_renders"` exits 0.
- [ ] 3.3 In the front door import from `isekai.pipeline.review.records`, plainly, `STAGE`, `_approval`, `_write_draft`, `_publish`, `_again`, `_recopy`, `_differs`, `same_fields`, `draft_image`, `came_from`, `is_copy`, `copied_renders`, `_first_image` and `_draft_command`, and `save_draft` as `save_draft as save_draft` ([D7](design.md#d7)). Then delete by hand the imports nothing in the front door reads now: `create`, `write`, `DraftImage`, `ReviewDraft` and `rendered_seeds`. Then run `uv run ruff check --fix isekai/pipeline/review` and `uv run ruff format isekai/pipeline/review`, which sort the imports; ruff removes no unused import from an `__init__.py`.
  Verify: `git grep -n -e "^def _write_draft" -e "^def save_draft" -e "^def _publish" -e "^def _approval" -e "^def _again" -- isekai/pipeline/review/__init__.py` prints nothing.
- [ ] 3.4 In `records.py` put `*,` on its own line in `_write_draft`'s parameters, after `sheet_version: int,`, so `renders`, `version` and `image` are keyword-only, defaults as they are. In the front door pass them by keyword at each call: `review`'s approved branch (`renders=carried.get("renders")`), `revise` (`renders=renders`, its keywords as they are), `draft_from` (`renders=` the conditional expression, `version=number` as it is) and `cancel` (`renders=body.get("renders")`, `version=version`, `image=draft_image(body)`) ([D4](design.md#d4)).
  Verify: `uv run python -c "import inspect; from isekai.pipeline.review.records import _write_draft; p = inspect.signature(_write_draft).parameters; assert p['renders'].kind == p['version'].kind == p['image'].kind == inspect.Parameter.KEYWORD_ONLY"` exits 0.
- [ ] 3.5 In `tests/test_review.py` and `tests/test_ui_api.py` change `import isekai.pipeline.review as review_module` to `import isekai.pipeline.review.records as review_records`, keeping the `# noqa: E402` on the second, and read and patch through `review_records` where each read `review_module` ([D5](design.md#d5)). No assertion changes.
  Verify: `git grep -n -F "review_module" -- tests` prints nothing.
- [ ] 3.6 In `tests/test_ratchets.py` delete the `WIDE_FUNCTIONS` row `isekai/pipeline/review/__init__.py::_write_draft` and set `WIDE_ROWS` to the rows left. Rename the `PATCHED_MODULES` key `isekai.pipeline.review` to `isekai.pipeline.review.records`, its number as it stands; `PATCHED_ROWS` does not change ([D5](design.md#d5)).
  Verify: `git grep -n -e "^    .isekai\.pipeline\.review\.records.: [0-9]" -- tests/test_ratchets.py` prints one line.
- [ ] 3.7 In `tests/mutants.json` set `path` to `isekai/pipeline/review/records.py` in `PB-3a` and `PB-3b`, so each holds `"path": "isekai/pipeline/review/records.py"`. Their `find` is in `_publish`, and `write`, their `replace`, is a name of `records.py`.
  Verify: `git grep -n -F '"path": "isekai/pipeline/review/records.py"' -- tests/mutants.json` prints two lines.
- [ ] 3.8 Run `uv run python -m tools.derive_imported_by`: `records.py` now imports the artifacts, the run and the refusal, so the derived tables change.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 3.9 **HALT CHECK** The front door is still over the long-file ceiling, `approve` still over the long-function one, and `_write_draft` is wide no more. A failure means the move differs from what the plan names.
  Verify: `uv run pytest tests/test_ratchets.py tests/test_layers.py` exits 0.
- [ ] 3.10 Run the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [ ] 3.11 Confirm the suite reads each name through the front door, and each patch reaches the module that reads the name.
  Verify: `uv run pytest tests/test_review.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py tests/test_spec_bindings.py tests/test_derive_wire.py` exits 0.

## 4 — The decision and the documents

- [ ] 4.1 In `docs/decisions.md` add D77 directly after D74 and before `## Infrastructure`, with the title, rule, *Why*, *Accepts* and *Made by* that [D9](design.md#d9) gives.
  Verify: `git grep -n -F "### D77" -- docs/decisions.md` prints one line.
- [ ] 4.2 In `isekai/pipeline/README.md` change "One file per stage, in the order a photograph passes through them." to "One file per stage, or one package, in the order a photograph passes through them.", and put in the Files row of `review/` what its modules hold: the front door `__init__.py` — `review`, `approve`, the revisions, the drafts and the cancel; `records.py` — the draft's reads and writes and the helpers the stage shares; `budget.py` — the token budget.
  Verify: `git grep -n -F "records.py" -- isekai/pipeline/README.md` prints one line.
- [ ] 4.3 Run `uv run python -m tools.derive_imported_by`, which writes the derived tables again.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 4.4 Confirm `records.py` holds `_write_draft`, `save_draft` and `_publish`.
  Verify: `git grep -n -e "^def _write_draft" -e "^def save_draft" -e "^def _publish" -- isekai/pipeline/review/records.py` prints three lines.
- [ ] 4.5 Confirm the front door defines `Status`, so the page's `ReviewStatus` keeps its module; `ui/src/wire.ts` is held by the deriver's test.
  Verify: `git grep -n -e "^Status = " -- isekai/pipeline/review/__init__.py` prints one line.
- [ ] 4.6 Run the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [ ] 4.7 Confirm the suite, the layer rules and the docs hold at the end.
  Verify: `uv run pytest tests/test_review.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_artifact_bytes.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py tests/test_spec_bindings.py tests/test_derive_wire.py` exits 0.
