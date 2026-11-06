# Tasks — 0108 removing a photo

The planner, then the server, then the dialog, then the record, per [design](design.md). Paths are from the
repository root.

## Progress

- [x] 1 — The planner
- [x] 2 — The server
- [x] 3 — The dialog
- [ ] 4 — The record

## 1 — The planner

- [x] 1.1 **HALT CHECK** — [D1](design.md#d1) checks a removal after the one `shortfall()` call in `short()`.
  Verify: `grep -n 'lacking = shortfall(run, loaded\[flow\])' isekai/interface/render.py` prints one line.
- [x] 1.2 In `isekai/interface/render.py`, give `short` and `quote` their `without` per [D1](design.md#d1), the check
  written `runs / run_id / flow not in without`, `Collection` imported from `collections.abc`.
  Verify: `grep -n 'runs / run_id / flow not in without' isekai/interface/render.py` prints one line.
- [x] 1.3 In `isekai/interface/render.py`, after `again`, add `without_flags`, and give `again` its `without`, per
  [D2](design.md#d2) and [the flag](design.md#the-flag).
  Verify: `grep -n 'def without_flags(without: Sequence\[Path\]) -> list\[str\]:' isekai/interface/render.py` prints one line.
- [x] 1.4 In `isekai/interface/render.py`, add `_taken` after `without_flags`, and make `run_session` and `_session`
  take `without`, per [D2](design.md#d2), raising [the flag](design.md#the-flag)'s refusals.
  Verify: `grep -n 'def _taken(roots: Sequence\[Path\], without: Sequence\[Path\]) -> list\[Path\]:' isekai/interface/render.py` prints one line.
- [x] 1.5 In `isekai/interface/cli.py`, add `render`'s `--without` after `--session`, as [the flag](design.md#the-flag)
  writes it.
  Verify: `uv run python -m isekai render --help` exits 0 and prints `--without <runs>/<run-id>/<flow>`.
- [x] 1.6 In `tests/test_render.py`, import `Sequence` from `collections.abc`, and give `session()` a
  `without: Sequence[Path] = ()` parameter, before `**seams`, set on its `Namespace` as `without=list(without)`.
  Verify: `grep -n 'without=list(without)' tests/test_render.py` prints one line.
- [x] 1.7 In `tests/test_render.py`, after `test_many_collections_render_in_one_session_in_the_order_named`, add
  `test_a_flow_named_without_is_not_rendered` (`cli:render-short:a-flow-named-without-is-not-rendered`) per
  [the planner's tests](design.md#the-planners-tests).
  Verify: `uv run pytest tests/test_render.py -k flow_named_without` exits 0.
- [x] 1.8 In `tests/test_render.py`, add `test_a_without_naming_nothing_is_refused`
  (`cli:render-short:a-without-naming-nothing-is-refused`) per [the planner's tests](design.md#the-planners-tests).
  Verify: `uv run pytest tests/test_render.py -k without_naming_nothing` exits 0.
- [x] 1.9 In `tests/test_render.py`, add `test_a_without_beside_a_request_is_refused`
  (`cli:render-short:a-without-beside-a-request-is-refused`) per [the planner's tests](design.md#the-planners-tests).
  Verify: `uv run pytest tests/test_render.py -k without_beside_a_request` exits 0.
- [x] 1.10 In `tests/test_render.py`, add `test_a_damaged_approval_taken_out_is_still_refused`
  (`cli:render-short:a-damaged-approval-taken-out-is-refused`) per [the planner's tests](design.md#the-planners-tests).
  Verify: `uv run pytest tests/test_render.py -k damaged_approval_taken_out` exits 0.
- [x] 1.11 In `tests/test_render.py`, add `test_the_limits_retry_keeps_each_without`
  (`cli:render-short:the-retry-keeps-without`) per [the planner's tests](design.md#the-planners-tests).
  Verify: `uv run pytest tests/test_render.py -k retry_keeps_each_without` exits 0.

## 2 — The server

- [x] 2.1 **HALT CHECK** — [D4](design.md#d4) appends to the one line `_render_child` builds.
  Verify: `grep -n 'argv = self._render(limit, roots, job.session\["id"\])' isekai/interface/ui/jobs.py` prints one line.
- [x] 2.2 In `isekai/interface/ui/jobs.py`, give `Jobs.render`, `_run_render` and `_render_child` their `without` per
  [D4](design.md#d4).
  Verify: `grep -n 'without_flags(without)' isekai/interface/ui/jobs.py` prints one line.
- [x] 2.3 In `isekai/interface/ui/app.py`, after `_quoted_row`, add `_taken_out` per [D3](design.md#d3), raising
  [the flag](design.md#the-flag)'s server refusals.
  Verify: `grep -n 'def _taken_out(value: object, found: Mapping\[str, Path\]) -> list\[Path\]:' isekai/interface/ui/app.py` prints one line.
- [x] 2.4 In `isekai/interface/ui/app.py`, make `quoted`, `post_quote`, `post_render` and `source()` carry
  `without` and the run per [D3](design.md#d3).
  Verify: `grep -n '"run": run_id' isekai/interface/ui/app.py` prints one line.
- [x] 2.5 In `tests/test_ui_jobs.py`, give the `left_out` entry that
  `test_the_quote_lists_each_flows_images_what_is_left_out_and_the_price` expects `"run": drafted.id`, after `"digest"`.
  Verify: `uv run pytest tests/test_ui_jobs.py -k quote_lists_each_flows_images_what_is_left_out` exits 0.
- [x] 2.6 In `tests/test_ui_jobs.py`, make `_order`'s script write each argument after the session too, and add
  `test_the_render_job_carries_each_photograph_taken_out` per [the server's tests](design.md#the-servers-tests).
  Verify: `uv run pytest tests/test_ui_jobs.py -k carries_each_photograph_taken_out` exits 0.
- [x] 2.7 In `tests/test_ui_jobs.py`, add `test_a_photograph_taken_out_leaves_the_quote_and_the_session` per
  [the server's tests](design.md#the-servers-tests).
  Verify: `uv run pytest tests/test_ui_jobs.py -k photograph_taken_out_leaves_the_quote` exits 0.
- [x] 2.8 In `tests/test_ui_jobs.py`, add `test_a_photograph_no_quoted_run_holds_is_refused` per
  [the server's tests](design.md#the-servers-tests).
  Verify: `uv run pytest tests/test_ui_jobs.py -k no_quoted_run_holds` exits 0.

## 3 — The dialog

- [x] 3.1 In `ui/src/types.ts`, give `QuoteSource` its `run`, add `TakenOut`, and drop `QuotedCollection`'s
  `left_out` and its comment's words for it, per [D5](design.md#d5) and [D9](design.md#d9).
  Verify: `grep -n 'export interface TakenOut' ui/src/types.ts` prints one line.
- [x] 3.2 In `ui/src/thumbs.ts`, make the edits of [D5](design.md#d5), and drop `leftOut`, `Left` and the header
  comment's left-out words per [D9](design.md#d9).
  Verify: `grep -n 'export function tileMoved(' ui/src/thumbs.ts` prints one line.
- [x] 3.3 In `ui/src/api.ts`, give `quoteRender` and `startRender` their `without` per [D5](design.md#d5).
  Verify: `grep -c 'without: TakenOut\[\]' ui/src/api.ts` prints `2`.
- [x] 3.4 In `ui/src/composables/useEdges.ts`, add the `centred` parameter per [D8](design.md#d8), its doc comment
  saying it.
  Verify: `grep -n 'centred = false' ui/src/composables/useEdges.ts` prints one line.
- [x] 3.5 In `ui/src/components/RenderDialog.vue`, make the edits of [D6](design.md#d6), [D7](design.md#d7),
  [D8](design.md#d8), [D9](design.md#d9) and [the dialog](design.md#the-dialog).
  Verify: `grep -n "id: 'take-out'" ui/src/components/RenderDialog.vue` prints one line.
- [x] 3.6 In `ui/src/app.css`, make the edits of [the dialog](design.md#the-dialog).
  Verify: `grep -n '^\.render-dialog__remove {' ui/src/app.css` prints one line.
- [x] 3.7 In `isekai/interface/ui/app.py`, drop `_quoted_row`'s `left_out` per [D9](design.md#d9).
  Verify: `grep -L '"left_out": \[' isekai/interface/ui/app.py` prints `isekai/interface/ui/app.py`.
- [x] 3.8 In `tests/test_ui_jobs.py`, rename the quote test and replace its `left_out` assertion per
  [the dialog's tests](design.md#the-dialogs-tests).
  Verify: `uv run pytest tests/test_ui_jobs.py -k quote_lists_each_flows_images_and_the_price` exits 0.
- [x] 3.9 In `ui/src/components/RenderDialog.test.ts`, drop the `leftOut` block and import, and give `source()` a
  `run`, per [the dialog's tests](design.md#the-dialogs-tests).
  Verify: `grep -L 'leftOut' ui/src/components/RenderDialog.test.ts` prints `ui/src/components/RenderDialog.test.ts`.
- [x] 3.10 In `ui/src/components/RenderDialog.test.ts`, add the `ui:render:taking-out-shows-the-next` block per
  [the dialog's tests](design.md#the-dialogs-tests).
  Verify: `grep -c 'ui:render:taking-out-shows-the-next' ui/src/components/RenderDialog.test.ts` prints `1`.
- [x] 3.11 In `ui/src/components/RenderDialog.test.ts`, add the `ui:render:nothing-left-disables-render` block per
  [the dialog's tests](design.md#the-dialogs-tests).
  Verify: `grep -c 'ui:render:nothing-left-disables-render' ui/src/components/RenderDialog.test.ts` prints `1`.
- [x] 3.12 In `ui/src/components/RenderDialog.test.ts`, add the `ui:render:the-tiles-move-by-flow` block per
  [the dialog's tests](design.md#the-dialogs-tests).
  Verify: `grep -c 'ui:render:the-tiles-move-by-flow' ui/src/components/RenderDialog.test.ts` prints `1`.
- [x] 3.13 In `ui/src/composables/useEdges.test.ts`, add the `ui:render:a-key-move-centres-the-tile` block per
  [the dialog's tests](design.md#the-dialogs-tests).
  Verify: `grep -c 'ui:render:a-key-move-centres-the-tile' ui/src/composables/useEdges.test.ts` prints `1`.
- [x] 3.14 In `tests/e2e/test_render.py`, rename the dialog test, swap its dialogs key and add the tile key, per
  [the tests](design.md#tests); change its opening lines per [the end-to-end steps](design.md#the-end-to-end-steps).
  Verify: `grep -n 'def test_the_render_dialog_opens_on_its_first_photograph' tests/e2e/test_render.py` prints one line.
- [x] 3.15 In `tests/e2e/test_render.py`, add the `WIDE` step of [the end-to-end steps](design.md#the-end-to-end-steps),
  importing nothing new.
  Verify: `grep -c 'all removed' tests/e2e/test_render.py` prints `1`.

## 4 — The record

- [ ] 4.1 In `docs/decisions.md`, replace docs D3's, D4's and D36's lines with those of
  [the record](design.md#the-record).
  Verify: `grep -c '0108' docs/decisions.md` prints `3`.
- [ ] 4.2 In `README.md`, replace line `:184` with the lines of [the record](design.md#the-record).
  Verify: `grep -n 'repeatable and beside no request, takes that run' README.md` prints one line.
- [ ] 4.3 In `isekai/interface/README.md`, edit the `render.py` row per [the record](design.md#the-record).
  Verify: `grep -n 'finds what each approval lacks, less each' isekai/interface/README.md` prints one line.
- [ ] 4.4 In `isekai/interface/ui/README.md`, replace lines `:31` and `:33` per [the record](design.md#the-record).
  Verify: `grep -n 'each source with its run, less what' isekai/interface/ui/README.md` prints one line.
