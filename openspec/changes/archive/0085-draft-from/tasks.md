# Tasks — 0085 draft from

The stage, the verb, then the page, per [design](design.md). Every new test carries its spec key.

## Progress

- [x] 1 — The stage
- [x] 2 — The verb
- [x] 3 — The page

## 1 — The stage

- [x] 1.1 **HALT CHECK** — a draft from an image lists no seed.
  Verify: `grep -c 'a-draft-from-an-image-prefills-its-seed' tests/test_review.py` prints `0`.
- [x] 1.2 Replace an unedited waiting draft in `revise` per [D1](design.md#d1), and list the image's seed in
  `draft_from` per [D2](design.md#d2), in `isekai/pipeline/review.py`; in `tests/test_review.py` bind
  `review:revise:an-unedited-waiting-draft-is-replaced` and `review:draft-from:a-draft-from-an-image-prefills-its-seed`,
  and give `review:revise:a-waiting-draft-refuses` an edited draft.
  Verify: `grep -c 'review:revise:an-unedited-waiting-draft-is-replaced\|a-draft-from-an-image-prefills-its-seed' tests/test_review.py` prints `2`, and `uv run pytest -q tests/test_review.py` exits 0.

## 2 — The verb

- [x] 2.1 **HALT CHECK** — the CLI revises with its own verb.
  Verify: `grep -c 'made\["revise"\]' isekai/interface/cli.py` prints a number of at least `1`.
- [x] 2.2 Add `draft` and delete `revise` and `review --from`/`--version` in `isekai/interface/cli.py` and
  `isekai/interface/drafting.py`, print `isekai draft --flow …` from `_revise_command`, renamed `_draft_command` (`isekai/pipeline/review.py`),
  and drop `review --from` from the sheet stage's remedy in `isekai/pipeline/sheet.py`,
  per [D3](design.md#d3) and [D6](design.md#d6); run the `cli:revise:` tests in `tests/test_review.py` through
  `draft --flow`; in `tests/test_pipeline_cli.py` bind `cli:draft:another-flow-is-drafted-from-the-image`, run
  `cli:review-from:a-target-with-no-sheet-is-filled-first` through `draft --flow`, and delete the tests the design's
  table retires.
  Verify: `grep -c 'made\["revise"\]' isekai/interface/cli.py` prints `0`, and `grep -c 'another-flow-is-drafted-from-the-image' tests/test_pipeline_cli.py` prints `1`, and `uv run pytest -q tests/test_pipeline_cli.py tests/test_review.py` exits 0.
- [x] 2.3 Edit `README.md` and `docs/data-flow.md` per [D7](design.md#d7).
  Verify: `grep -c 'isekai revise\|review --from' README.md docs/data-flow.md` prints `0` for each file, and `grep -c 'isekai draft --flow' README.md` prints a number of at least `1`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 3 — The page

- [x] 3.1 **HALT CHECK** — the page drafts through two routes.
  Verify: `grep -c '/draft-from"\|/revise"' isekai/interface/ui/app.py` prints `2`.
- [x] 3.2 Add `/api/c/{collection}/draft` and every offered flow as a target, and delete `/draft-from` and `/revise`, in
  `isekai/interface/ui/app.py` per [D4](design.md#d4) and [D6](design.md#d6); in `tests/test_ui_api.py` bind
  `ui:draft-from:an-unedited-waiting-draft-is-replaced` and `ui:draft-from:a-selection-drafts-into-the-flow-chosen`, and
  move the revise and draft-from tests to `/draft`.
  Verify: `grep -c '/draft-from"\|/revise"' isekai/interface/ui/app.py` prints `0`, and `grep -c 'ui:draft-from:' tests/test_ui_api.py` prints `2`, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [x] 3.3 Add `ui/src/components/DraftDialog.vue` and delete `ui/src/components/ReviseConfirm.vue`, open it on `⇧D` in
  `ui/src/views/RenderLarge.vue` and `ui/src/views/Renders.vue`, and delete `⇧E` and `⇧F`, with `ui/src/api.ts` and
  `ui/src/types.ts`, per [D5](design.md#d5); in `tests/e2e/test_render.py` press `Shift+D`, then `Enter` on the row.
  Verify: `test -e ui/src/components/ReviseConfirm.vue; echo $?` prints `1`, and `grep -c "shifted('KeyE')\|shifted('KeyF')" ui/src/views/RenderLarge.vue ui/src/views/Renders.vue` prints `0` for each file, and `uv run python -m tools.typecheck_ui` exits 0, and `uv run pytest -q tests/e2e/test_render.py` exits 0.
- [x] 3.4 Edit `ui/design/spec.md` per [D7](design.md#d7).
  Verify: `grep -c 'Draft from this' ui/design/spec.md` prints a number of at least `2`, and `grep -c '⇧E Revise\|⇧F Conjure' ui/design/spec.md` prints `0`, and `uv run pytest -q tests/e2e` exits 0.
