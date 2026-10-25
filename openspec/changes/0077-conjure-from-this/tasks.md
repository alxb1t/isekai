# Tasks — 0077 conjure from this

The review stage, the verb, then the surface, per [design](design.md). Every new pytest test carries
`@pytest.mark.spec` with the key its task names.

## Progress

- [ ] 1 — The review stage
- [ ] 2 — The verb
- [ ] 3 — The surface

## 1 — The review stage

- [ ] 1.1 **HALT CHECK** — the review stage drafts from no other flow.
  Verify: `grep -c 'def draft_from' isekai/pipeline/review.py` prints `0`.
- [ ] 1.2 Add `drafted_from: NotRequired[CopiedFrom]` to `ChainProducer` in `isekai/foundation/artifacts.py` per
  [D2](design.md#d2), declaring `CopiedFrom` above it.
  Verify: `grep -c '"drafted_from": NotRequired\[CopiedFrom\]' isekai/foundation/artifacts.py` prints `1`, and `uv run ty check` exits 0.
- [ ] 1.3 Add `draft_from` to `isekai/pipeline/review.py` per [D1](design.md#d1), [D2](design.md#d2) and
  [D3](design.md#d3); bind every `review:draft-from:` key of the [review](specs/review/spec.md) delta in `tests/test_review.py`.
  Verify: `uv run pytest -q tests/test_review.py` exits 0, and `grep -c 'review:draft-from:' tests/test_review.py` prints `7`.

## 2 — The verb

- [ ] 2.1 **HALT CHECK** — `review` takes no `--from`.
  Verify: `uv run python -m isekai review --help | grep -c -- '--from'` prints `0`.
- [ ] 2.2 Add `--from` and `--version` to `review` in `isekai/interface/cli.py`, and call `draft_from` from
  `review_flow`, per [D4](design.md#d4); bind both `cli:review-from:` keys in `tests/test_pipeline_cli.py`.
  Verify: `uv run python -m isekai review --help | grep -c -- '--version'` prints a number of at least `1`, and `grep -c 'cli:review-from:' tests/test_pipeline_cli.py` prints `2`, and `uv run pytest -q tests/test_pipeline_cli.py` exits 0.
- [ ] 2.3 In `README.md`'s options list, `--from FLOW` — on `approve`: … → `--from FLOW` — on `approve`: … ; on
  `review`: draft each `--flow` from that flow's approval, its own fields from its sheet, and add `--version N`.
  Verify: `grep -c 'on .review.: draft each' README.md` prints `1`, and `grep -c -- '--version N' README.md` prints a number of at least `1`.
- [ ] 2.4 In `docs/data-flow.md`'s stage diagram, under `revise`, add the line
  `review --from ── reads another flow's approval and its own sheet ──▶ review/NNN.draft.json`.
  Verify: `grep -c 'review --from' docs/data-flow.md` prints `1`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 3 — The surface

- [ ] 3.1 **HALT CHECK** — the server drafts from no other flow.
  Verify: `grep -c 'draft-from' isekai/interface/ui/app.py` prints `0`.
- [ ] 3.2 Add `targets` to `read_render`, the `draft-from` route and its docstring line, and `drafted` to
  `read_input`, in `isekai/interface/ui/app.py`, per [D5](design.md#d5) and [D7](design.md#d7); bind the unit
  `ui:conjure-from:` keys in `tests/test_ui_api.py`.
  Verify: `grep -c 'ui:conjure-from:' tests/test_ui_api.py` prints `3`, and `uv run pytest -q tests/test_ui_api.py tests/test_ui.py` exits 0.
- [ ] 3.3 Add `draftFrom` to `ui/src/api.ts`, `targets` and `drafted` to `ui/src/types.ts`, the buttons and `f` to
  `ui/src/views/RenderLarge.vue` per [D6](design.md#d6), and the marks, kicker and Discard to `ui/src/views/Review.vue`
  per [D7](design.md#d7).
  Verify: `grep -c "id: 'draft-from'" ui/src/views/RenderLarge.vue` prints `1`, and `uv run python -m tools.typecheck_ui` exits 0, and `uv run python -m tools.test_ui` exits 0.
- [ ] 3.4 Add a `CONJURED` batch to `tests/e2e/conftest.py` — a run with summon rendered at seed 7 and a conjure
  sheet — and `test_conjure_from_this_opens_review` to `tests/e2e/test_render.py`, bound to
  `ui:conjure-from:conjure-from-this-opens-review`.
  Verify: `grep -c 'conjure-from-this-opens-review' tests/e2e/test_render.py` prints `1`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.
- [ ] 3.5 In `ui/design/spec.md` §7's Renders row, `in the large view, e Revise, c compare,` →
  `in the large view, e Revise, f Conjure from this, c compare,`; in J5's *↵ always opens the large view* bullet,
  say each flow drafted from a sheet alone is offered as *Conjure from this*, and Review marks its draft against
  that flow's sheet.
  Verify: `grep -c 'f Conjure from this' ui/design/spec.md` prints a number of at least `1`, and `grep -c 'against that flow.s sheet' ui/design/spec.md` prints `1`.
