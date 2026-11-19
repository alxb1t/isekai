# The wire, rendering — tasks

The phases: the tattoos and place, the rendering, then the rows that hold every route and the documents.

## Progress

- [ ] 1 — The tattoos and place · moderate
- [ ] 2 — The rendering · hard
- [ ] 3 — The rows and the documents · moderate

## 1 — The tattoos and place

- [ ] 1.1 In `isekai/interface/ui/shapes.py` add the constants `TATTOO` and `STAGE1` and the classes `Tattoo`, `OutlinedTattoo`, `TattooLimits`, `Stage1`, `Tattoos`, `Outline` and `BakeQueued`, written as in [the declarations](design.md#the-declarations), with `from isekai.pipeline import tattoos` for `tattoos.Kind`.
  Verify: `grep -c -E '^class (Tattoo|OutlinedTattoo|TattooLimits|Stage1|Tattoos|Outline|BakeQueued)\(' isekai/interface/ui/shapes.py` prints `7`.
- [ ] 1.2 In the same file add the rows of `ANSWERS` for the tattoos' routes and the bake, as [the declarations](design.md#the-declarations) lists them, after the reviewing rows. The `DELETE` row answers `Empty`, already declared, and is held by task 3.1.
  Verify: `grep -c -E ': (Tattoos|OutlinedTattoo|Tattoo|Outline|Stage1|BakeQueued),$' isekai/interface/ui/shapes.py` prints `8`, and `uv run pytest tests/test_ui_shapes.py` passes.
- [ ] 1.3 In the same file add the class `Proposed`, `from isekai.shared import proposal` for `proposal.Side`, and `UNRECORDED: dict[str, Any]` holding the propose row of [D1](design.md#d1); say in the module docstring that `UNRECORDED` keys the answers the record lacks.
  Verify: `grep -c '^UNRECORDED: dict' isekai/interface/ui/shapes.py` prints `1`.
- [ ] 1.4 In `tests/test_ui_propose.py` add `test_the_propose_answer_fits_its_declaration` with `spec_exempt("structural: the propose answer fits the declaration UNRECORDED holds")`: it asks the route as the file's first test does and asserts `faults(UNRECORDED["POST /api/c/{collection}/place/propose"], shape(answered.json()), "") == []`; the file's own `COLLECTION` and `PROPOSE` stay as they are ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_ui_propose.py::test_the_propose_answer_fits_its_declaration` passes.
- [ ] 1.5 Run `uv run python -m tools.derive_imported_by`: the rows of `tattoos.py` in `isekai/pipeline/README.md` and of `proposal.py` in `isekai/shared/README.md` gain `interface/ui/shapes.py` ([D8](design.md#d8)).
  Verify: `uv run pytest tests/test_docs.py` passes.

## 2 — The rendering

- [ ] 2.1 **HALT CHECK** The modules `shapes.py` is about to import, `jobs.py`, `billing.py`, `events.py`, `library.py` and `render.py`, import no web framework, no Pillow, no numpy and no onnx at module level; if one does, the plan is wrong.
  Verify: `git grep -n -E "^(from|import) (fastapi|starlette|uvicorn|PIL|numpy|onnxruntime)" -- isekai/interface/ui/jobs.py isekai/interface/ui/billing.py isekai/interface/ui/events.py isekai/interface/ui/library.py isekai/interface/render.py` prints nothing.
- [ ] 2.2 In `isekai/interface/ui/shapes.py` add the classes of the offer, the quote and the check from [the declarations](design.md#the-declarations) — `RenderOffer`, `QuotedSource`, `QuotedFlow`, `QuotedBake`, `QuotedRow`, `QuoteEstimate`, `QuotePrice`, `Quote`, `BillingVolume`, `Billing`, `BillingChecked` — and the rows of `ANSWERS` for the offer, the quote and the check.
  Verify: `grep -c -E ': (RenderOffer|Quote|BillingChecked),$' isekai/interface/ui/shapes.py` prints `3`, and `uv run pytest tests/test_ui_shapes.py` passes.
- [ ] 2.3 In the same file add the classes `JobStage`, `JobProgress`, `JobSession`, `Job`, `JobStarted`, `ServedSession`, `RunningSession` and `RunningSessions`, `NotRequired` in the `typing` import, the imports `from isekai.foundation import artifacts` and `from isekai.interface.ui import jobs`, and the rows of `UNRECORDED` for prepare, stop, render, the running sessions and a session that [the declarations](design.md#the-declarations) lists, `Job.state` and `BillingVolume.state` as `str` ([D5](design.md#d5)).
  Verify: `grep -c -E ': (Proposed|JobStarted|RunningSessions|ServedSession),$' isekai/interface/ui/shapes.py` prints `6`, and `uv run pytest tests/test_ui_shapes.py` passes.
- [ ] 2.4 In `tests/test_ui_shapes.py` add `test_the_served_session_is_the_record_with_a_nullable_outcome` with `spec_exempt("structural: the served session is the session record with a nullable outcome")`: `get_type_hints`, `__required_keys__` and `__optional_keys__` of `ServedSession` equal `SessionRecord`'s, `outcome` apart, which is `str | None` ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_ui_shapes.py::test_the_served_session_is_the_record_with_a_nullable_outcome` passes.
- [ ] 2.5 In `tests/test_ui_jobs.py` add `_Idle(Jobs)` overriding `_occupy`, a `make_jobs` keyword defaulting to `Jobs` on `_held_client` and `_quoting`, and `test_the_prepare_answer_fits_its_declaration`, `test_the_stop_answer_fits_its_declaration` and `test_the_render_answer_fits_its_declaration`, each exempt as `structural: the <verb> answer fits the declaration UNRECORDED holds` ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_ui_jobs.py::test_the_prepare_answer_fits_its_declaration tests/test_ui_jobs.py::test_the_stop_answer_fits_its_declaration tests/test_ui_jobs.py::test_the_render_answer_fits_its_declaration` passes.
- [ ] 2.6 In `tests/test_ui_api.py` add `test_the_running_sessions_answer_fits_its_declaration` and `test_a_served_session_fits_its_declaration_running_and_stale`, each exempt as `structural: the <answer> fits the declaration UNRECORDED holds`; they hold a `Record` open for `outcome` `running`, then closed for `null`, as `test_a_terminal_session_is_live_without_a_job_slot` does.
  Verify: `uv run pytest tests/test_ui_api.py::test_the_running_sessions_answer_fits_its_declaration tests/test_ui_api.py::test_a_served_session_fits_its_declaration_running_and_stale` passes.
- [ ] 2.7 Run `uv run python -m tools.derive_imported_by`: the row of `artifacts.py` in `isekai/foundation/README.md` gains `interface/ui/shapes.py` ([D8](design.md#d8)).
  Verify: `uv run pytest tests/test_docs.py` passes.

## 3 — The rows and the documents

- [ ] 3.1 In `tests/test_ui_shapes.py` add `test_every_json_route_of_the_three_tables_has_a_row_in_one_table` with `spec_exempt("structural: each JSON route of the tattoo, place and render tables has a row in one table")`, as [D9](design.md#d9) states; the shipped case's `TABLES` stay as they are.
  Verify: `uv run pytest tests/test_ui_shapes.py::test_every_json_route_of_the_three_tables_has_a_row_in_one_table` passes.
- [ ] 3.2 In `isekai/interface/README.md` replace the `ui/shapes.py` row's text with: "each JSON answer of the hub, staging, images, vocabulary, review, tattoo, place and render routes as a `TypedDict`, `ANSWERS` keyed as the record is for the answers it records, and `UNRECORDED` for those it lacks; a test holds each and no route reads it. **Imports no web framework**".
  Verify: `git grep -c "UNRECORDED" -- isekai/interface/README.md` prints `isekai/interface/README.md:1`.
- [ ] 3.3 In `docs/decisions.md` add `### D64 · The answers the record lacks are a second table, held by cases that ask the server` after D63, in D63's form, and change D63's *Accepts* line and *Made by* line as [D10](design.md#d10) says.
  Verify: `git grep -n "^### D64" -- docs/decisions.md` prints one line, and `uv run pytest tests/test_docs.py tests/test_spec_prose.py tests/test_ratchets.py` passes.
