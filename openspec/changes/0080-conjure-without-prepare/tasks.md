# Tasks — 0080 conjure without Prepare

The sheet from another flow's tags, the drafting sequence, then the page, per [design](design.md). Every new pytest
test carries `@pytest.mark.spec` with the key its task names.

## Progress

- [x] 1 — A sheet from another flow's tags
- [x] 2 — The drafting sequence
- [ ] 3 — The page

## 1 — A sheet from another flow's tags

- [x] 1.1 **HALT CHECK** — the sheet stage reads only the flow's own tag list.
  Verify: `grep -c 'tags_from' isekai/pipeline/sheet.py isekai/foundation/artifacts.py` prints `0` for each file.
- [x] 1.2 Add `tags_from` to `sheet` in `isekai/pipeline/sheet.py` and to `SheetProducer` in
  `isekai/foundation/artifacts.py` per [D1](design.md#d1); bind both `sheet:tags-from:` keys in
  `tests/test_sheet_stage.py`.
  Verify: `grep -c 'sheet:tags-from:' tests/test_sheet_stage.py` prints `2`, and `uv run pytest -q tests/test_sheet_stage.py` exits 0, and `uv run ty check` exits 0.

## 2 — The drafting sequence

- [x] 2.1 **HALT CHECK** — no interface module runs assign, sheet and draft together.
  Verify: `test -e isekai/interface/drafting.py; echo $?` prints `1`.
- [x] 2.2 Add `draft_across` in `isekai/interface/drafting.py` per [D2](design.md#d2), and call it from `review_flow`
  in `isekai/interface/cli.py`; bind `cli:review-from:a-target-with-no-sheet-is-filled-first` in
  `tests/test_pipeline_cli.py`.
  Verify: `grep -c 'draft_across' isekai/interface/cli.py` prints a number of at least `1`, and `grep -c 'a-target-with-no-sheet-is-filled-first' tests/test_pipeline_cli.py` prints `1`, and `uv run pytest -q tests/test_pipeline_cli.py tests/test_layers.py` exits 0.
- [x] 2.3 Edit `README.md` and `docs/data-flow.md` per [D7](design.md#d7).
  Verify: `grep -c "filling a target with no sheet from the source's tags" README.md` prints `1`, and `grep -c "the source's tag list where no sheet" docs/data-flow.md` prints `1`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 3 — The page

- [ ] 3.1 **HALT CHECK** — the page's targets are read from the batch's assigned runs.
  Verify: `grep -c 'run.directory(name).is_dir()' isekai/interface/ui/app.py` prints `1`.
- [ ] 3.2 In `isekai/interface/ui/app.py`, read the targets per [D4](design.md#d4) and call `draft_across` from
  `post_draft_from`; add `waiting_edit` to `isekai/pipeline/review.py` and answer it per [D3](design.md#d3); in
  `tests/test_ui_api.py` bind `ui:conjure-from:a-waiting-edit-is-opened` and edit the targets and refused-draft
  tests to their scenarios.
  Verify: `grep -c 'run.directory(name).is_dir()' isekai/interface/ui/app.py` prints `0`, and `grep -c 'ui:conjure-from:a-waiting-edit-is-opened' tests/test_ui_api.py` prints `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [ ] 3.3 Serve `drafted` for an approval per [D5](design.md#d5) and the borrowed caption per [D6](design.md#d6) in
  `isekai/interface/ui/app.py`; bind `ui:conjure-from:an-approved-draft-keeps-its-marks` and
  `ui:source:a-borrowed-sheet-shows-its-sources-caption` in `tests/test_ui_api.py`.
  Verify: `grep -c 'an-approved-draft-keeps-its-marks\|a-borrowed-sheet-shows-its-sources-caption' tests/test_ui_api.py` prints `2`, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [ ] 3.4 Keep `drafted` read-only in `ui/src/views/Review.vue`, head the caption `caption · <flow>` in
  `ui/src/components/SourcePanel.vue`, and open a `waiting` answer in `ui/src/views/RenderLarge.vue`, with
  `ui/src/types.ts`.
  Verify: `grep -c 'caption_from\|captionFrom' ui/src/types.ts` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 3.5 Delete the conjure sheet the `conjured` batch fills in `tests/e2e/conftest.py`, and check the caption named as
  summon's in `test_conjure_from_this_opens_review` (`tests/e2e/test_render.py`).
  Verify: `grep -c 'sheet(conjured' tests/e2e/conftest.py` prints `0`, and `uv run pytest -q tests/e2e/test_render.py -k conjure` exits 0.
- [ ] 3.6 Edit `ui/design/spec.md`'s large-view bullet per [D7](design.md#d7).
  Verify: `grep -c 'Each offered flow drafted from a sheet alone, assigned or not' ui/design/spec.md` prints `1`, and `uv run pytest -q tests/e2e` exits 0.
