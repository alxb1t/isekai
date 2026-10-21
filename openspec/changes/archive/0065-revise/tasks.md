# Tasks — 0065 revise

The pipeline, the verbs, the API, the UI, then the cards and the docs, per [design](design.md). Every new pytest test
carries `@pytest.mark.spec` with the key its task names.

## Progress

- [x] 1 — Revise and discard
- [x] 2 — The verbs
- [x] 3 — The API
- [x] 4 — The UI
- [x] 5 — The cards and the docs

## 1 — Revise and discard

- [x] 1.1 **HALT CHECK** — `review` copies the newest approval only, and nothing in the pipeline is called `revise`.
  Verify: `grep -c 'def revise' isekai/pipeline/review.py` prints `0`, and `grep -c 'copied = review_directory / artifact_name(approved\[-1\], APPROVED)' isekai/pipeline/review.py` prints `1`.
- [x] 1.2 Add `revise` and `discard` to `isekai/pipeline/review.py` per [D1](design.md#d1) and [D3](design.md#d3), and the unchanged refusal to `approve` per [D4](design.md#d4); bind every `review:revise:*` and `review:discard:*` key in `tests/test_review.py`.
  Verify: `uv run pytest -q tests/test_review.py` exits 0, and `grep -c -E 'review:(revise|discard):' tests/test_review.py` prints `6`.

## 2 — The verbs

- [x] 2.1 Add the `revise` verb and `review --discard` to `isekai/interface/cli.py` per [D2](design.md#d2) and [D3](design.md#d3); bind every `cli:revise:*` key in `tests/test_review.py`.
  Verify: `uv run python -m isekai revise --help` exits 0, and `grep -c 'cli:revise:' tests/test_review.py` prints `2`.

## 3 — The API

- [x] 3.1 Add the revise, discard and compare routes of [D7](design.md#d7) to `isekai/interface/ui/app.py`, and the version header of [D5](design.md#d5) to `read_renders`; bind `ui:compare:a-version-is-named-by-what-changed` and `ui:compare:a-seed-pairs-with-its-newest-older-version` in `tests/test_ui_api.py`.
  Verify: `grep -c '/compare' isekai/interface/ui/app.py` prints a number of at least `1`, and `grep -c 'ui:compare:' tests/test_ui_api.py` prints `2`.

## 4 — The UI

- [x] 4.1 Add Revise to `ui/src/views/RenderLarge.vue` and `ui/src/views/Renders.vue`, the revision's render and `was` lines to `ui/src/views/Review.vue`, `ui/src/views/Compare.vue` with its route in `ui/src/router.ts`, per [D7](design.md#d7) and the design spec's J5, J6.
  Verify: `grep -c "compare" ui/src/router.ts` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 4.2 Extend `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from` in `tests/e2e/test_render.py` along J5, with steps binding `ui:revise:revise-opens-review-on-the-revision` and `ui:compare:compare-shows-the-pair-and-the-change`.
  Verify: `uv run pytest -q tests/e2e/test_render.py` exits 0, and `grep -c -E 'ui:revise:|ui:compare:compare-shows' tests/e2e/test_render.py` prints `2`.

## 5 — The cards and the docs

- [x] 5.1 Drop the disabled-Render step from `test_confirming_the_dialog_opens_the_session` in `tests/e2e/test_render.py`, per [D8](design.md#d8) and the [Tests](design.md#tests) table.
  Verify: `grep -c 'already has its Count' tests/e2e/test_render.py` prints `0`.
- [x] 5.2 In the stream test in `tests/test_ui_api.py`, close the helper's broadcast in a `finally`, re-raise its exception, and read the snapshot before uploading, per [D8](design.md#d8).
  Verify: `grep -A2 'def upload_once_open' tests/test_ui_api.py | grep -c 'try:'` prints `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [x] 5.3 Describe `isekai revise`, `review --discard` and Compare in `README.md` and `docs/data-flow.md`.
  Verify: `grep -c 'isekai revise' README.md docs/data-flow.md` prints a number of at least `1` for each file, and `uv run pytest -q tests/test_docs.py tests/test_spec_prose.py` exits 0.
