# Tasks — 0081 the fourth walkthrough

The record, then Review, per [design](design.md). Every new pytest test carries `@pytest.mark.spec` with the key its
task names.

## Progress

- [x] 1 — The image a draft came from, recorded
- [x] 2 — Review shows it

## 1 — The image a draft came from, recorded

- [x] 1.1 **HALT CHECK** — no producer records an image.
  Verify: `grep -c '"image": NotRequired' isekai/foundation/artifacts.py` prints `0`.
- [x] 1.2 Add `DraftImage` and `image` to `ChainProducer` in `isekai/foundation/artifacts.py` per [D1](design.md#d1);
  write it from `revise` and `draft_from` in `isekai/pipeline/review.py` per [D2](design.md#d2); in
  `tests/test_review.py` bind `review:revise:a-revision-records-its-image` and
  `review:draft-from:a-draft-from-an-image-records-it`, and add `image` to
  `test_a_revision_copies_the_images_approval_and_keeps_its_seed`'s producer.
  Verify: `grep -c 'a-revision-records-its-image\|a-draft-from-an-image-records-it' tests/test_review.py` prints `2`, and `uv run pytest -q tests/test_review.py` exits 0, and `uv run ty check` exits 0.
- [x] 1.3 Pass the seed through `draft_across` (`isekai/interface/drafting.py`), `post_draft_from`
  (`isekai/interface/ui/app.py`) and `draftFrom` (`ui/src/api.ts`, `ui/src/views/RenderLarge.vue`) per
  [D2](design.md#d2).
  Verify: `grep -c 'seed' isekai/interface/drafting.py` prints a number of at least `1`, and `uv run pytest -q tests/test_ui_api.py tests/test_pipeline_cli.py` exits 0, and `uv run python -m tools.typecheck_ui` exits 0.

## 2 — Review shows it

- [x] 2.1 **HALT CHECK** — Review guesses a revision's image from its seeds.
  Verify: `grep -c 'The image is the first listed seed rendered under that approval' isekai/interface/ui/app.py` prints `1`.
- [x] 2.2 Read `image` in `_revision` and `_drafted` (`isekai/interface/ui/app.py`) per [D3](design.md#d3); bind
  `ui:revise:a-revision-keeps-its-image-after-its-seed-changes` in `tests/test_ui_api.py`.
  Verify: `grep -c 'a-revision-keeps-its-image-after-its-seed-changes' tests/test_ui_api.py` prints `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [x] 2.3 Draw a drafted draft's image in `ui/src/views/Review.vue` and `ui/src/components/SourcePanel.vue`, with
  `ui/src/types.ts`, per [D4](design.md#d4); in `test_conjure_from_this_opens_review` (`tests/e2e/test_render.py`)
  check `[data-revised] img` beside the photograph.
  Verify: `grep -c 'drafted from' ui/src/components/SourcePanel.vue` prints a number of at least `1`, and `uv run pytest -q tests/e2e/test_render.py -k conjure` exits 0.
- [x] 2.4 Edit `ui/design/spec.md` per [D5](design.md#d5).
  Verify: `grep -c 'shows the summon image beside the photograph' ui/design/spec.md` prints `1`, and `grep -c 'whatever its seeds become' ui/design/spec.md` prints `1`, and `uv run pytest -q tests/e2e` exits 0.
