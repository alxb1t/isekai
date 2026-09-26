# Tasks — 0031 the backlog

Behaviour first, then the guards, then the prose that describes the result ([D5](design.md#d5)).

## Progress

- [x] 1 — Behaviour: v0.22.8's families finished
- [x] 2 — Structure: the retry rule once, the annotation guard, the saved-draft golden, test nits
- [ ] 3 — Prose: the documentation that drifted

Line numbers are `3278647`'s; find each site by the text it names.

## 1 — Behaviour: v0.22.8's families finished

- [x] 1.1 **HALT CHECK** — `post_approve` calls `approve` outside the draft lock, and the client does not catch `TypeError`.
  Verify: `grep -c 'with _DRAFT_UPDATE' isekai/interface/ui/app.py` prints `1`, and `grep -c 'except (ValueError, KeyError)' isekai/boundary/comfy/client.py` prints `1`.
- [x] 1.2 Refuse a wrong-shaped answer in `isekai/boundary/comfy/client.py` and `_submit` (`isekai/pipeline/generate.py:500-506`), per [D1](design.md#d1), with tests in `tests/test_generate.py`.
  Verify: `grep -c 'TypeError' isekai/boundary/comfy/client.py` prints a number above `0`.
- [x] 1.3 Refuse every missing key [D1](design.md#d1) lists by name in `isekai/pipeline/review.py` and `isekai/pipeline/sheet.py`, with tests in `tests/test_review.py` and `tests/test_sheet_stage.py`.
  Verify: `cat isekai/pipeline/review.py isekai/pipeline/sheet.py | grep -c -e 'int(body\["sheet"\])' -e '\*\*body\["producer"\]' -e 'listed\["producer"\]\["models"\]'` prints `0`.
- [x] 1.4 Give `Run.frame`'s refusal its own remedy in `isekai/foundation/run.py`, per [D1](design.md#d1), with a test in `tests/test_run_directory.py`.
  Verify: `grep -c 'offer the photograph again by its path' isekai/foundation/run.py` prints `1`.
- [x] 1.5 Hold `_DRAFT_UPDATE` around `approve` in `post_approve`, per [D1](design.md#d1), with `test_an_update_overlapping_an_approval_is_refused` in `tests/test_ui_api.py`.
  Verify: `grep -c 'with _DRAFT_UPDATE' isekai/interface/ui/app.py` prints `2`, and `grep -c '^def test_an_update_overlapping_an_approval_is_refused' tests/test_ui_api.py` prints `1`.

## 2 — Structure: the retry rule once, the annotation guard, the saved-draft golden, test nits

- [x] 2.1 Give `exhausted` and `check_budget` one predicate in `isekai/foundation/run.py`, per [D2](design.md#d2).
  Verify: `grep -c 'recorded\[-1\].kind == "permanent"' isekai/foundation/run.py` prints `1`.
- [x] 2.2 Add `test_every_write_gets_an_annotated_artifact` and its twin to `tests/test_artifact_bytes.py`, per [D2](design.md#d2).
  Verify: `grep -c -e '^def test_every_write_gets_an_annotated_artifact' -e '^def test_the_check_catches_a_bare_literal' tests/test_artifact_bytes.py` prints `2`.
- [x] 2.3 Add the `draft-saved` kind and capture `tests/golden/draft-saved.json` from today's code; reword the comment at `tests/test_artifact_bytes.py:92`, per [D2](design.md#d2).
  Verify: `test -f tests/golden/draft-saved.json && grep -c '"draft-saved"' tests/test_artifact_bytes.py` prints `1`.
- [x] 2.4 Type `collect`'s argument in `tests/test_resume.py:279-281`, and drop the unused `flow` parameter at `tests/test_flow.py:692`, per [D2](design.md#d2).
  Verify: `grep -c 'ty: ignore\[call-non-callable\]' tests/test_resume.py` prints `0`, and `grep -c '^def test_every_tracked_flows_graph_carries_no_negative_of_its_own() -> None' tests/test_flow.py` prints `1`.

## 3 — Prose: the documentation that drifted

- [ ] 3.1 Apply [D3](design.md#d3)'s rows to `README.md`, `isekai/README.md`, `isekai/shared/README.md`, `isekai/foundation/README.md`, `docs/modules.md` and `docs/principles.md`.
  Verify: `grep -c 'ISEKAI_VOCABULARY' README.md` prints a number above `0`, `grep -c 'by its full path' docs/principles.md` prints `0`, and `grep -c 'Two of them do read' isekai/shared/README.md` prints `0`.
- [ ] 3.2 Pass `prog="python -m <module>"` to the parsers [D3](design.md#d3) names.
  Verify: `grep -l 'prog="python -m ' evaluation/__main__.py tools/derive_field_map.py evaluation/baseline/build_contact_sheets.py evaluation/baseline/build_subjects.py | wc -l | tr -d ' '` prints `4`.
- [ ] 3.3 Reword *"a format you do not know"* in `isekai/foundation/artifacts.py:321`, and the sheet budget's comment at `isekai/foundation/run.py:154-157`, per [D3](design.md#d3).
  Verify: `grep -c 'format you do not know' isekai/foundation/artifacts.py` prints `0`, and `grep -c 'records no failure' isekai/foundation/run.py` prints `1`.
