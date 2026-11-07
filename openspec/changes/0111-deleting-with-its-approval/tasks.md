# Tasks — 0111 deleting with its approval

The cancel, then the checks, the copy, the delete, the page and the record, per [design](design.md). Paths are from
the repository root.

## Progress

- [x] 1 — The cancel
- [x] 2 — The checks
- [x] 3 — The copy and the draft
- [ ] 4 — The delete
- [ ] 5 — The page
- [ ] 6 — The record

## 1 — The cancel

- [x] 1.1 **HALT CHECK** — [D2](design.md#d2) drops the one branch that reads `firsts`.
  Verify: `grep -n 'elif len(firsts) == len(derived):' isekai/pipeline/review.py` prints one line.
- [x] 1.2 In `isekai/pipeline/review.py`, cut `_derived` to the approval's own files and drop `firsts` from
  `_cancelling`, per [D2](design.md#d2), each docstring saying so.
  Verify: `grep -n 'def _derived(run: Run, flow: str, version: int) -> list\[str\]:' isekai/pipeline/review.py` prints one line.
- [x] 1.3 In `tests/test_review.py`, rewrite `test_an_approval_drafted_from_a_source_refuses_the_sources_cancel` as
  `test_what_is_drafted_from_an_approval_holds_no_source_cancel`, per
  [the pipeline's tests](design.md#the-pipelines-tests); drop `_run_printed` if nothing else calls it.
  Verify: `uv run pytest tests/test_review.py -k what_is_drafted_from_an_approval_holds_no_source_cancel` exits 0.
- [x] 1.4 In `tests/test_review.py`, rewrite `test_a_copy_in_another_flow_refuses_the_sources_cancel` as
  `test_what_another_flow_took_holds_no_cancel`, per [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_review.py -k what_another_flow_took_holds_no_cancel` exits 0.
- [x] 1.5 In `tests/test_resume.py`'s `_draft_and_cancel_refusals`, delete the `collect(lambda: cancel(drafted, FLOW))`
  after `approve(drafted, conjure.id, …)`: per [D2](design.md#d2) that cancel no longer refuses.
  Verify: `uv run pytest tests/test_resume.py` exits 0.

## 2 — The checks

- [x] 2.1 **HALT CHECK** — [D5](design.md#d5) deletes the one function that checks a copy against its source.
  Verify: `grep -n 'def refuse_out_of_step' isekai/pipeline/generate.py` prints one line.
- [x] 2.2 In `isekai/pipeline/generate.py`, delete `refuse_out_of_step` and any import only it used, per [D5](design.md#d5).
  Verify: `grep -n 'refuse_out_of_step' isekai/pipeline/generate.py` prints nothing.
- [x] 2.3 In `isekai/interface/cli.py`, delete `--in-step-with`, its import, guards, loop and `return` clause, per
  [D5](design.md#d5).
  Verify: `grep -n 'in_step_with' isekai/interface/cli.py` prints nothing.
- [x] 2.4 In `isekai/interface/render.py`, make `_asked` skip a late request and say `--seeds-from` alone, and say in
  `in_session_sources`'s docstring that such a dependent has no check before the pod, per [D5](design.md#d5).
  Verify: `grep -n 'in-step-with' isekai/interface/render.py` prints nothing.
- [x] 2.5 In `tests/test_generate.py`, delete the four tests [the Tests table](design.md#tests) retires, and any import
  only they used.
  Verify: `grep -n 'in-step-with' tests/test_generate.py` prints nothing.
- [x] 2.6 In `tests/test_render.py`, delete `test_a_dependent_behind_its_source_in_one_session_refuses_before_the_pod`.
  Verify: `grep -n 'in-step-with' tests/test_render.py` prints nothing.

## 3 — The copy and the draft

- [x] 3.1 **HALT CHECK** — [D3](design.md#d3) replaces the one place a copy's origin is written.
  Verify: `grep -n '"copied_from": {"flow": source, "approval": approval}' isekai/pipeline/review.py` prints one line.
- [x] 3.2 In `isekai/foundation/artifacts.py`, delete `CopiedFrom` and `ChainProducer`'s `drafted_from`, and give
  `ApprovedProducer` `copied: NotRequired[bool]` for `copied_from`, per [D3](design.md#d3) and [D4](design.md#d4).
  Verify: `grep -n 'CopiedFrom' isekai/foundation/artifacts.py` prints nothing.
- [x] 3.3 In `isekai/pipeline/review.py`, add `is_copy` and `copied_renders` beside `came_from`, as
  [the copy](design.md#the-copy) writes them.
  Verify: `grep -n 'def copied_renders(run: Run, flow: str, version: int, body: ReviewApproved) -> Renders:' isekai/pipeline/review.py` prints one line.
- [x] 3.4 In `isekai/pipeline/review.py`, rewrite `_copy_approval` and the docstrings of `approve` and `state` per
  [the copy](design.md#the-copy).
  Verify: `grep -n '"copied": True' isekai/pipeline/review.py` prints one line.
- [x] 3.5 In `isekai/pipeline/review.py`, make `cancel` test `is_copy(body["producer"])` and `came_from` test
  `is_copy(producer)` where each tests `copied_from`, per [D3](design.md#d3).
  Verify: `grep -n 'if is_copy(body\["producer"\]):' isekai/pipeline/review.py` prints one line.
- [x] 3.6 In `isekai/pipeline/review.py`, edit `draft_from`, `_write_draft`, `cancel`'s draft call and
  `_drafting_wrote`, and delete `drafted_from()`, per [D4](design.md#d4). The one `drafted_from` left is the key
  [the copy](design.md#the-copy)'s `_NOT_COPIED` strips, per [D3](design.md#d3).
  Verify: `grep -n 'drafted_from' isekai/pipeline/review.py` prints one line, `_NOT_COPIED = frozenset({"copied_from", "drafted_from", "image"})`.
- [x] 3.7 In `isekai/interface/ui/app.py`, rewrite `_drafted` per [D6](design.md#d6) and drop the `drafted_from` import.
  Verify: `grep -n 'drafted_from' isekai/interface/ui/app.py` prints nothing.
- [x] 3.8 In `tests/test_review.py`, make the copy rows of [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_review.py -k "copy_carries_the_sources_seeds or copy_leaves_the_sources_files or copied_again"` exits 0.
- [x] 3.9 In `tests/test_review.py`, make the draft rows and the readers changed in place of
  [the pipeline's tests](design.md#the-pipelines-tests), bar the cancel rows.
  Verify: `uv run pytest tests/test_review.py -k "records_its_sheet_and_no_source or draft_from_no_image_carries or unedited_waiting_draft"` exits 0.
- [x] 3.10 In `tests/test_pipeline_cli.py:821`, assert `"drafted_from" not in draft["producer"]` for its
  `drafted_from` value, per [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_pipeline_cli.py -k draft_writes_another_flow` exits 0.
- [x] 3.11 In `tests/test_ui_api.py`, make the `drafted` edits of [the server's tests](design.md#the-servers-tests).
  Verify: `uv run pytest tests/test_ui_api.py -k "drafted_draft_against_its_sheet_and_its_image or approved_drafted_drafts_marks or selection_from_two_runs or waiting_draft_is_its_sheet"` exits 0.
- [x] 3.12 In `tests/test_generate.py`, mark `test_a_flow_renders_the_seeds_of_its_sources_latest_group`
  `run-directory:layout:a-named-source-is-recorded`, above its present mark.
  Verify: `grep -n 'run-directory:layout:a-named-source-is-recorded' tests/test_generate.py` prints one line.

## 4 — The delete

- [ ] 4.1 **HALT CHECK** — [D7](design.md#d7) replaces the one glob `0106·R1` names.
  Verify: `grep -n 'dropped = sorted(cached.glob(f"{image.stem}.\*.jpg"))' isekai/interface/ui/library.py` prints one line.
- [ ] 4.2 In `isekai/interface/ui/library.py`, make `drop_thumbnails` delete the image's own thumbnail alone, its
  docstring saying the image must still exist, the digest read after the collection check, per [D7](design.md#d7).
  Verify: `grep -n 'f"{image.stem}.{_digest(image)}.jpg"' isekai/interface/ui/library.py` prints one line.
- [ ] 4.3 In `isekai/pipeline/review.py`, add `withdraw` after `cancel`, per [D1](design.md#d1).
  Verify: `grep -n 'def withdraw(run: Run, flow: str, version: int) -> list\[Path\]:' isekai/pipeline/review.py` prints one line.
- [ ] 4.4 In `isekai/interface/cli.py`, make `_discard` take `(run, flow, version, _)` from `rendered_at`, drop the
  thumbnails, discard, then `withdraw`, printing the run's files before the thumbnails, a `withdraw` refusal printed
  as `refused: {image}: {refusal}` with exit 1, per [D1](design.md#d1) and [D7](design.md#d7); its docstring says so.
  Verify: `grep -n 'withdraw(run, flow, version)' isekai/interface/cli.py` prints one line.
- [ ] 4.5 In `isekai/interface/ui/app.py`, make `delete_render` drop the thumbnails, discard, then `withdraw` under
  `_DRAFT_UPDATE`, per [D1](design.md#d1) and [D7](design.md#d7); its docstring says so.
  Verify: `grep -n 'withdraw(run, flow, _version(version))' isekai/interface/ui/app.py` prints one line.
- [ ] 4.6 In `tests/test_ui_library.py`, rewrite `test_dropping_a_renders_thumbnails_leaves_the_others` per
  [the server's tests](design.md#the-servers-tests).
  Verify: `uv run pytest tests/test_ui_library.py -k dropping_a_renders_thumbnails` exits 0.
- [ ] 4.7 In `tests/test_pipeline_cli.py`, edit `test_discard_deletes_the_render_and_its_thumbnail` and add
  `test_discarding_the_last_render_takes_its_approval_with_it`, per [the server's tests](design.md#the-servers-tests).
  Verify: `uv run pytest tests/test_pipeline_cli.py -k "discard_deletes_the_render or last_render_takes_its_approval"` exits 0.
- [ ] 4.8 In `tests/test_review.py`, add the three `withdraw` rows of
  [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_review.py -k "takes_it_back_to_its_draft or older_approvals_last_render or waiting_draft_keeps_the_approval"` exits 0.
- [ ] 4.9 In `tests/test_ui_api.py`, add the `v2/22` step to `test_deleting_a_render_deletes_its_files_and_thumbnail`,
  per [the server's tests](design.md#the-servers-tests).
  Verify: `grep -n "# The newest approval's only render goes, and its approval with it." tests/test_ui_api.py` prints one line.

## 5 — The page

- [ ] 5.1 In `ui/src/types.ts`, cut `Drafted` to `fields` and `image?`, the latter's comment
  `/* The image the draft was written from, while its file exists. */`, per [D6](design.md#d6).
  Verify: `grep -n 'The image the draft was written from, while its file exists.' ui/src/types.ts` prints one line.
- [ ] 5.2 In `ui/src/views/Review.vue`, replace the kicker's `from FLOW vN` line per [D6](design.md#d6).
  Verify: `grep -n "if (drafted.value && !sheet.detail.value?.approved) return 'draft'" ui/src/views/Review.vue` prints one line.
- [ ] 5.3 In `tests/e2e/test_render.py`, make the edits of [the end-to-end steps](design.md#the-end-to-end-steps).
  Verify: `grep -n 'to_have_attribute("data-stage", "draft")' tests/e2e/test_render.py` prints one line.

## 6 — The record

- [ ] 6.1 In `docs/decisions.md`, edit D4 per [the record](design.md#the-record).
  Verify: `grep -n "the newest approval its last render leaves through review" docs/decisions.md` prints one line.
- [ ] 6.2 In `docs/decisions.md`, mark D38 superseded and add D49 after it, per [the record](design.md#the-record).
  Verify: `grep -n '^### D49 · A control flow is its subject with the face chain at zero, copied once' docs/decisions.md` prints one line.
- [ ] 6.3 In `docs/decisions.md`, point D17's link at D49, per [the record](design.md#the-record).
  Verify: `grep -n 'd38--a-control-flow' docs/decisions.md` prints nothing.
- [ ] 6.4 In `docs/data-flow.md`, edit the discard paragraph and point the D38 link at D49, per
  [the record](design.md#the-record).
  Verify: `grep -n 'takes that approval back to its draft' docs/data-flow.md` prints one line.
- [ ] 6.5 In `docs/principles.md`, add the `withdraw` sentence to *Known breaks*, per [the record](design.md#the-record).
  Verify: `grep -n "withdraw. deletes the prompt and failure records" docs/principles.md` prints one line.
- [ ] 6.6 In `docs/modules.md`, name `withdraw` beside `discard_render`, per [the record](design.md#the-record).
  Verify: `grep -n "and review's .withdraw." docs/modules.md` prints one line.
- [ ] 6.7 In `README.md`, edit `--seeds-from` and `--from` and delete `--in-step-with`, per
  [the record](design.md#the-record).
  Verify: `grep -n 'in-step-with' README.md` prints nothing.
