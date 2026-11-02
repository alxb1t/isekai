# Tasks — 0089 the paydown

The flake first, then evaluation, the render, import, cancel, the guard, the UI and docs, and the tests, per
[design](design.md). Each new test carries the `spec` marker its task names, or `spec_exempt` with its reason.

## Progress

- [x] 1 — The flake
- [x] 2 — Evaluation
- [x] 3 — The render
- [x] 4 — Import
- [x] 5 — Cancel and draft-from
- [x] 6 — The guard
- [x] 7 — The UI and the docs
- [x] 8 — The tests

## 1 — The flake

- [x] 1.1 In `tests/test_ui_jobs.py`, `close_once_open` publishes `events.CLOSE` with `{}` in place of
  `broadcast.close()`, per [D1](design.md#d1).
  Verify: `grep -c 'broadcast.close()' tests/test_ui_jobs.py` prints `0`, and `for i in $(seq 30); do uv run pytest -q tests/test_ui_jobs.py -k both_slots || exit 1; done` exits 0.

## 2 — Evaluation

- [x] 2.1 [The evaluation delta](specs/evaluation/spec.md) changes no code. Rebind
  `test_every_render_of_a_run_whose_frame_does_not_read_is_an_unreadable_row` in `tests/test_recall_cli.py` to
  `evaluation:recall:a-run-whose-frame-does-not-read-is-a-row`.
  Verify: `grep -c 'a-run-whose-frame-does-not-read-is-a-row' tests/test_recall_cli.py` prints `1` before 2.2, `2` after it.
- [x] 2.2 In `read` in `isekai/foundation/artifacts.py`, catch `OSError` from `path.read_text()` and raise `Refusal`
  naming the path and its remedy, per [D2](design.md#d2). Add `test_an_unreadable_file_is_refused_by_name` to
  `tests/test_recall_cli.py`, bound to the key of 2.1: a run whose `run.json` is a directory is a row, the next run read.
  Verify: `uv run pytest tests/test_recall_cli.py -k unreadable_file` exits 0.

## 3 — The render

- [x] 3.1 `read_env` in `isekai/boundary/gpu.py` follows [D3](design.md#d3); add an `export` line, a trailing comment
  and an empty value as cases of `test_the_env_file_is_read_as_key_value_lines` in `tests/test_render.py`.
  Verify: `uv run pytest tests/test_render.py -k env_file` exits 0, and `grep -c 'export ' tests/test_render.py` prints a count above 0.
- [x] 3.2 `except TeardownFailed` in `isekai/interface/render.py` prints `refused: <cause>` first when `__cause__` is a
  `Refusal`, per [D4](design.md#d4). Add `test_a_failed_body_is_named_beside_a_failed_teardown` to `tests/test_render.py`, `spec_exempt` as its neighbours.
  Verify: `uv run pytest tests/test_render.py -k failed_body` exits 0.
- [x] 3.3 Reword the unreachable refusal in `isekai/boundary/comfy/client.py` per [D4](design.md#d4): after "could not
  be reached (…)" it says "; if a session is open, its tunnel has dropped", then offers `python -m isekai render`, keeping
  "--server". `tests/test_generate.py` and `tests/test_resume.py` assert those words.
  Verify: `grep -c 'tunnel has dropped' isekai/boundary/comfy/client.py` prints `1`, and `uv run pytest tests/test_generate.py tests/test_resume.py -k unreachable` exits 0.

## 4 — Import

- [x] 4.1 The `MAX_PIXELS` comment in `isekai/pipeline/importing.py`, before → after: "a photograph's sensor is far
  below it" → "it refuses some full-resolution photographs from the largest sensors".
  Verify: `grep -c 'far below it' isekai/pipeline/importing.py` prints `0`.
- [x] 4.2 `put` catches `Exception` around the hold, recording `refused`, and `_refuse_name` refuses a name holding
  `"\x00"`, per [D5](design.md#d5). Add `test_a_name_holding_a_nul_byte_is_refused_alone` to `tests/test_importing.py`,
  bound to `ui:sheet:a-failed-read-refuses-its-file-alone`: the file is refused and `seal` commits the rest.
  Verify: `uv run pytest tests/test_importing.py -k nul_byte` exits 0.

## 5 — Cancel and draft-from

- [x] 5.1 `cancel` in `isekai/pipeline/review.py` follows [the review delta](specs/review/spec.md) and returns
  `Cancelled(left, changed)` per [D6](design.md#d6); `approve_flow` in `isekai/interface/cli.py`, `post_cancel` in
  `isekai/interface/ui/app.py` and every `cancel` assertion in `tests/` follow it. Add
  `test_a_flow_with_no_approval_has_nothing_to_cancel` to `tests/test_review.py`, bound to the delta's new key.
  Verify: `uv run pytest tests/test_review.py -k nothing_to_cancel` exits 0, and `grep -c 'has no approval to cancel; run' isekai/pipeline/review.py` prints `0`.
- [x] 5.2 Update the cancel text `ui/src/composables/useSheet.test.ts` carries, if its needle changed in 5.1.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [x] 5.3 `drafting_approval`'s refusal for an approval the source does not hold follows [D6](design.md#d6): the held
  approvals named, then the `draft` command on an image of one, else the `render` command. Add `test_a_missing_version_names_the_held_approvals` to `tests/test_review.py`, bound to
  `review:draft-from:a-missing-source-approval-is-refused`.
  Verify: `uv run pytest tests/test_review.py -k held_approvals` exits 0, and `grep -c -- '--version' isekai/pipeline/review.py` prints `0`.
- [x] 5.4 `_derived` adds that flow's `--discard` after a drafted approval's cancel, and `_cancelling`'s refusal says
  the discard drops that flow's fields, per [D6](design.md#d6). In `test_an_approval_drafted_from_a_source_refuses_the_sources_cancel`,
  run the printed chain and assert the source's cancel then succeeds.
  Verify: `uv run pytest tests/test_review.py -k refuses_the_sources_cancel` exits 0.
- [x] 5.5 Add a copy's cancel as a step to `test_approve_cancel_answers_each_run_on_its_own` in `tests/test_pipeline_cli.py`
  and to `test_an_approved_sheet_carries_why_it_cannot_be_cancelled` in `tests/test_ui_api.py`, and a step copying over
  a re-opened flow to `test_a_copy_is_deleted_and_an_approval_with_a_later_draft_refuses_its_discard`: the draft
  comes back and the flow reads `re-opened`.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_ui_api.py tests/test_review.py -k "cancel or copy"` exits 0.

## 6 — The guard

- [x] 6.1 In `tests/test_resume.py`, `_every_refusal` provokes a waiting draft's refusal, an unrendered seed's, the
  target-without-sheet, missing-approval and edited-waiting-draft refusals of `draft_from`, and one cancel refusal of
  each kind; `_unrunnable` accepts a `draft` command by its images; `AVAILABLE` gains the prefixes they print, per
  [D7](design.md#d7).
  Verify: `uv run pytest tests/test_resume.py -k refusal` exits 0, and `grep -c 'cancel' tests/test_resume.py` prints a count above 0.

## 7 — The UI and the docs

- [x] 7.1 `set` in `ui/src/slots.ts` compares and keeps seeds as `String(BigInt(seed))`; add a step to the
  `ui:review:each-image-has-a-slot` test in `ui/src/slots.test.ts`: `0144` beside `144` is refused.
  Verify: `grep -c 'BigInt' ui/src/slots.ts` prints a count above 0, and `uv run python -m tools.test_ui` exits 0.
- [x] 7.2 `change()` in `ui/src/components/RendersBlock.vue` clears `refused` whenever the count changes, per
  [D8](design.md#d8).
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 7.3 The comments at `ui/src/components/SheetForm.vue`, `FieldRow.vue` and `ApproveBar.vue`, before → after: "a
  revision" → "a revision, or a draft drafted from another flow's approval".
  Verify: `grep -l 'drafted from another flow' ui/src/components/SheetForm.vue ui/src/components/FieldRow.vue ui/src/components/ApproveBar.vue` names all of them.
- [x] 7.4 `README.md`'s *Review* line, before → after: "or the first unapproved sheet when one flow waits" → "or, when
  one flow waits, its first unapproved sheet, else its first approved sheet short of its images".
  Verify: `grep -c 'short of its images' README.md` prints a count above 0.
- [x] 7.5 `openspec/specs/sheet/spec.md`'s `## Purpose`, before → after: "and whether a tag list is expected" → "whether
  a tag list is expected, and the source flow the operator names".
  Verify: `sed -n '/^## Purpose/,/^## Requirements/p' openspec/specs/sheet/spec.md | grep -c 'the source flow the operator names'` prints `1`.
- [x] 7.6 Add `### D45 · A repeated seed is refused on every read` to `docs/decisions.md`, after D13: an approval written
  before `v0.44` with a repeated seed reads as damaged, and the way on is a new draft.
  Verify: `grep -c '^### D45 ' docs/decisions.md` prints `1`.

## 8 — The tests

- [x] 8.1 The bundle-timeout test, `test_a_build_that_does_not_finish_is_stopped_and_named` in `tests/test_ui.py`, waits
  for its stand-in's pid file before the ceiling starts, keeping its seconds assertion, per [D9](design.md#d9).
  Verify: `for i in $(seq 10); do uv run pytest -q tests/test_ui.py -k does_not_finish || exit 1; done` exits 0.
- [x] 8.2 The `SHOWN` comment in `tests/e2e/conftest.py` adds: "a routes test needs it to hold no sheet waiting for review".
  Verify: `grep -c 'no sheet waiting' tests/e2e/conftest.py` prints `1`.
- [x] 8.3 Merge `tests/e2e/test_review.py`'s tests as [Tests](design.md#tests) lists: move each step, delete the three
  removed tests.
  Verify: `grep -c '^def test_' tests/e2e/test_review.py` prints `2`, and `uv run pytest tests/e2e/test_review.py` exits 0.
