# Tasks — 0112 deleting a render whole

The source copy, then the page, the discard and the records, the copy's sheet, the delete and the record, per
[design](design.md). Paths are from the repository root.

## Progress

- [x] 1 — The source copy
- [ ] 2 — The page
- [ ] 3 — The discard and the records
- [ ] 4 — The copy's own sheet
- [ ] 5 — The delete
- [ ] 6 — The record

## 1 — The source copy

- [x] 1.1 **HALT CHECK** — [D2](design.md#d2) replaces the one place a draft records another flow's image.
  Verify: `grep -n 'else {"flow": source, "version": approval, "seed": seed},' isekai/pipeline/review.py` prints one line.
- [x] 1.2 In `isekai/foundation/run.py`, add `SOURCES = "sources"` after `OUTPUTS`, per [D2](design.md#d2).
  Verify: `grep -n '^SOURCES = "sources"$' isekai/foundation/run.py` prints one line.
- [x] 1.3 In `isekai/pipeline/review.py`, add `source_copy` beside `group_of`'s readers, and make `drafting_approval`
  refuse a seed whose image file is gone as it refuses one never rendered, per [D2](design.md#d2).
  Verify: `grep -n 'def source_copy(run: Run, flow: str, version: int) -> Path:' isekai/pipeline/review.py` prints one line.
- [x] 1.4 In `isekai/pipeline/review.py`, make `draft_from` copy a named seed's image to the source copy of its draft's
  number after `_refuse_edited`, immediately before `_write_draft`, and record no `image`, per [D2](design.md#d2).
  Verify: `grep -n '"seed": seed},' isekai/pipeline/review.py` prints one line.
- [x] 1.5 In `isekai/interface/run_view.py`, make `unread` read a flow's `sources/` and each file in it named a
  three-digit number and the flow's output suffix, per [D2](design.md#d2).
  Verify: `grep -n 'SOURCES' isekai/interface/run_view.py` prints at least one line.
- [x] 1.6 In `isekai/interface/ui/app.py`, rewrite `_drafted` and add the source copy's route, listed in the module
  docstring's routes, per [D3](design.md#d3).
  Verify: `grep -n '"/api/c/{collection}/review/{digest}/{flow}/source/{version}"' isekai/interface/ui/app.py` prints one line.
- [x] 1.7 In `tests/test_review.py`, make the copy and refusal rows of [the pipeline's tests](design.md#the-pipelines-tests)
  for `draft_from`.
  Verify: `uv run pytest tests/test_review.py -k "copies_it_into_the_targets_sources or never_rendered_is_refused or records_the_image_it_names"` exits 0.
- [x] 1.8 In `tests/test_pipeline_cli.py`, make the draft edits of
  [the server's and the verb's tests](design.md#the-servers-and-the-verbs-tests), bar `tags_from`.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k "images_approval_and_seed or fills_it_from_the_source"` exits 0.
- [x] 1.9 In `tests/test_ui_api.py`, make the `drafted` edits of
  [the server's and the verb's tests](design.md#the-servers-and-the-verbs-tests).
  Verify: `uv run pytest tests/test_ui_api.py -k "drafted_draft_against_its_sheet or approved_drafted_drafts_marks or waiting_draft_is_its_sheet or selection_from_two_runs"` exits 0.
- [x] 1.10 In `tests/test_run_view.py`, make the `sources/` edits of
  [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_run_view.py -k "name_show_does_not_read and sources"` exits 0.

## 2 — The page

- [ ] 2.1 In `ui/src/types.ts`, make `Drafted` `{ fields; version: number }`, `version`'s comment
  `/* The number its source copy is held under: the image it was drafted from. */`, and the `drafted` field's comment
  say its own sheet's fields and its source copy, per [D3](design.md#d3).
  Verify: `grep -n 'The number its source copy is held under' ui/src/types.ts` prints one line.
- [ ] 2.2 In `ui/src/api.ts`, add `sourceCopyUrl(place: Place, version: number): string` after `photoUrl`, returning
  `` `${at(place)}/source/${version}` ``, per [D3](design.md#d3).
  Verify: `grep -n 'export function sourceCopyUrl(place: Place, version: number): string' ui/src/api.ts` prints one line.
- [ ] 2.3 In `ui/src/views/Review.vue`, make `revised` a revision's image with its seed, else a drafted draft's
  `sourceCopyUrl` with `seed: null`, and name the lens's image `the image it was drafted from` where `seed` is null,
  per [D3](design.md#d3).
  Verify: `grep -n 'sourceCopyUrl(' ui/src/views/Review.vue` prints one line.
- [ ] 2.4 In `ui/src/components/SourcePanel.vue`, make `revised` `{ src: string; seed: string | null }`, its kicker
  and its image's `alt` `render being revised · seed N` with a seed, else `the image it was drafted from`, per
  [D3](design.md#d3).
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 2.5 In `tests/e2e/test_render.py`, make the kicker step and the `[data-revised]` step of
  [the end-to-end steps](design.md#the-end-to-end-steps).
  Verify: `grep -n 'to_contain_text("the image it was drafted from")' tests/e2e/test_render.py` prints one line.

## 3 — The discard and the records

- [ ] 3.1 **HALT CHECK** — [D5](design.md#d5) removes the one write of `tags_from`.
  Verify: `grep -n 'made_by\["tags_from"\] = tags_from' isekai/pipeline/sheet.py` prints one line.
- [ ] 3.2 In `isekai/pipeline/sheet.py`, rename `sheet`'s and `prepare_sheet`'s `tags_from` to `drafted_from`, record
  it nowhere, and delete `tagged_from` and `_superseded`'s branch on it, each docstring saying so, per [D5](design.md#d5).
  Verify: `grep -n 'tags_from\|tagged_from' isekai/pipeline/sheet.py` prints nothing.
- [ ] 3.3 In `isekai/foundation/artifacts.py`, delete `SheetProducer`'s `tags_from` and end the comment above it at
  `` names a list in `photo/wd14/`. ``, per [D5](design.md#d5).
  Verify: `grep -n 'tags_from' isekai/foundation/artifacts.py` prints nothing.
- [ ] 3.4 In `isekai/interface/drafting.py`, pass `drafted_from=source` for `tags_from=source`, and make
  `draft_across`'s docstring say the image is copied and the sheet records no source, per [D5](design.md#d5).
  Verify: `grep -n 'tags_from' isekai/interface/drafting.py` prints nothing.
- [ ] 3.5 In `isekai/pipeline/review.py`, make `discard` delete the draft and its source copy alone and delete
  `_drafting_wrote` and any import only it used, the docstring saying so, per [D4](design.md#d4).
  Verify: `grep -n '_drafting_wrote' isekai/pipeline/review.py` prints nothing.
- [ ] 3.6 In `tests/test_review.py`, rewrite the discard row of [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_review.py -k drafted_draft_goes_alone` exits 0.
- [ ] 3.7 In `tests/test_sheet_stage.py`, make the edits and the deletion of
  [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_sheet_stage.py` exits 0.
- [ ] 3.8 In `tests/test_run_view.py` and `tests/test_resume.py`, pass `drafted_from=FLOW` for `tags_from=FLOW`.
  Verify: `uv run pytest tests/test_run_view.py tests/test_resume.py` exits 0.
- [ ] 3.9 In `tests/test_pipeline_cli.py`, assert `"tags_from" not in filled["producer"]`, per
  [the server's and the verb's tests](design.md#the-servers-and-the-verbs-tests).
  Verify: `uv run pytest tests/test_pipeline_cli.py -k fills_it_from_the_source` exits 0.

## 4 — The copy's own sheet

- [ ] 4.1 **HALT CHECK** — [D6](design.md#d6) replaces the one line saying a copy keeps its source's sheet.
  Verify: `grep -n 'it is provenance' isekai/pipeline/review.py` prints one line.
- [ ] 4.2 In `isekai/pipeline/review.py`, make `_copy_approval` name the target's newest sheet and compute `edited`
  against it, refusing a target with none, its local `latest` renamed `newest`, per [the copy](design.md#the-copy).
  Verify: `grep -n 'which a revision of the copy' isekai/pipeline/review.py` prints one line.
- [ ] 4.3 In `isekai/interface/drafting.py`, add `approve_across` after `draft_across`, per [the copy](design.md#the-copy).
  Verify: `grep -n 'def approve_across(' isekai/interface/drafting.py` prints one line.
- [ ] 4.4 In `isekai/interface/cli.py`, make `approve_flow` call `approve_across` for `--from`, per
  [the copy](design.md#the-copy).
  Verify: `grep -n 'approve_across(' isekai/interface/cli.py` prints one line.
- [ ] 4.5 In `tests/test_review.py`, make `_approved_source` fill CONTROL's sheet and add
  `test_a_copy_names_the_targets_own_sheet`, per [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_review.py` exits 0.
- [ ] 4.6 In `tests/test_generate.py`, `tests/test_ui_api.py` and `tests/test_pipeline_cli.py`, fill a CONTROL sheet
  before each copy, per [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_generate.py tests/test_ui_api.py tests/test_pipeline_cli.py` exits 0.
- [ ] 4.7 In `tests/test_pipeline_cli.py`, add `test_approve_from_fills_a_target_with_no_sheet_first`, per
  [the server's and the verb's tests](design.md#the-servers-and-the-verbs-tests).
  Verify: `uv run pytest tests/test_pipeline_cli.py -k approve_from_fills_a_target_with_no_sheet_first` exits 0.

## 5 — The delete

- [ ] 5.1 **HALT CHECK** — [D1](design.md#d1) drops the one call that takes an approval back to its draft on a delete.
  Verify: `grep -nx '    cancel(run, flow)' isekai/pipeline/review.py` prints one line.
- [ ] 5.2 In `isekai/pipeline/review.py`, rewrite `withdraw` per [the delete](design.md#the-delete).
  Verify: `grep -n 'once its group is gone; return what went, absolute' isekai/pipeline/review.py` prints one line.
- [ ] 5.3 In `isekai/interface/cli.py`, make `_discard` print what `discard_render` and `withdraw` return with no
  refusal branch, its docstring saying the last render takes its approval, per [D1](design.md#d1).
  Verify: `grep -n 'refused = refusal' isekai/interface/cli.py` prints nothing.
- [ ] 5.4 In `isekai/interface/ui/app.py`, make the module docstring and `delete_render`'s say what `withdraw` deletes,
  per [D1](design.md#d1).
  Verify: `grep -n 'back to its draft once its last render' isekai/interface/ui/app.py` prints nothing.
- [ ] 5.5 In `tests/test_review.py`, rewrite the `withdraw` rows of [the pipeline's tests](design.md#the-pipelines-tests).
  Verify: `uv run pytest tests/test_review.py -k "takes_its_approval_and_the_waiting_draft or older_approvals_with_no_render or keeps_only_its_assignment"` exits 0.
- [ ] 5.6 In `tests/test_pipeline_cli.py`, edit `test_discarding_the_last_render_takes_its_approval_with_it`, per
  [the server's and the verb's tests](design.md#the-servers-and-the-verbs-tests).
  Verify: `uv run pytest tests/test_pipeline_cli.py -k last_render_takes_its_approval` exits 0.
- [ ] 5.7 In `tests/test_ui_api.py`, edit `test_deleting_a_render_deletes_its_files_and_thumbnail`, per
  [the server's and the verb's tests](design.md#the-servers-and-the-verbs-tests).
  Verify: `grep -n "# The last approval's only render goes, and the flow keeps only its assignment." tests/test_ui_api.py` prints one line.
- [ ] 5.8 In `tests/e2e/test_render.py`, make the comment and the cell step of
  [the end-to-end steps](design.md#the-end-to-end-steps).
  Verify: `grep -n 'to_have_attribute("data-stage", "tagged")' tests/e2e/test_render.py` prints one line.

## 6 — The record

- [ ] 6.1 In `docs/decisions.md`, edit D4 and D49 and add D50 after D49, per [the record](design.md#the-record).
  Verify: `grep -n '^### D50 · The last render takes its approval, and a flow holds only its own files' docs/decisions.md` prints one line.
- [ ] 6.2 In `docs/data-flow.md`, edit the discard paragraph, the `--from` line, the draft paragraph and the run tree,
  per [the record](design.md#the-record).
  Verify: `grep -n 'a flow left with no approval keeps only its assignment' docs/data-flow.md` prints one line.
- [ ] 6.3 In `docs/principles.md`, edit *Known breaks* per [the record](design.md#the-record).
  Verify: `grep -n 'once the flow holds no approval, the sheets the sheet stage' docs/principles.md` prints one line.
- [ ] 6.4 In `README.md`, edit the `--from` and `--discard` bullets, per [the record](design.md#the-record).
  Verify: `grep -n 'drafting wrote, takes that sheet' README.md` prints nothing.
- [ ] 6.5 In `isekai/interface/README.md`, edit `drafting.py`'s row, per [the record](design.md#the-record).
  Verify: `grep -n 'copies an approval across for' isekai/interface/README.md` prints one line.
