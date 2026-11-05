# Tasks — 0101 the review tags fixes

The table, then the guards, per [design](design.md).

## Progress

- [x] 1 — The table
- [x] 2 — The guards

## 1 — The table

- [x] 1.1 **HALT CHECK** No `FILED` key, nor anything else in the deriver, names a tattoo tag at the base, as
  [Context](design.md#context) states.
  Verify: `git grep -c tattoo 7fdbad24 -- tools/derive_field_map.py` prints nothing and exits 1.
- [x] 1.2 In `tools/derive_field_map.py`, add `EXCLUDED_CONTAINING` and `exclusions()` below `EXCLUDED`, and replace
  the comment at `:148-154` with [the comment](design.md#the-comment), per [D1](design.md#d1).
  Verify: `grep -c -F -e 'EXCLUDED_CONTAINING: tuple[str, ...] = ("tattoo",)' -e 'def exclusions(vocabulary: Vocabulary) -> set[str]:' tools/derive_field_map.py` prints `2`.
- [x] 1.3 In `tools/derive_field_map.py`, give `build()` its `excluded` parameter and subtraction, make `main()` pass
  and write `exclusions(vocabulary)`, and set `REVISION = 4`, per [D2](design.md#d2).
  Verify: `grep -c -F -e 'REVISION = 4' -e 'browsable[field] -= excluded' -e '"excluded": vocabulary.rank(excluded),' tools/derive_field_map.py` prints `3`.
- [x] 1.4 Re-derive the table: `uv run python -m tools.derive_field_map`. Never hand-edit `config/field_map.json`.
  Verify: `grep -c tattoo config/field_map.json` prints `23`.
- [x] 1.5 Add `test_the_committed_table_excludes_every_tattoo_tag_and_photorealistic` to `tests/test_field_map.py`,
  marked `field-map:excluded:tattoos-and-photorealistic-are-excluded`, per [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_field_map.py::test_the_committed_table_excludes_every_tattoo_tag_and_photorealistic` exits 0.

## 2 — The guards

- [x] 2.1 Give `Vocabulary.search` in `isekai/shared/vocabulary.py` its `skip` parameter per [D3](design.md#d3), and
  add `test_search_skips_the_tags_it_is_told_to` to `tests/test_vocabulary.py`, per [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_vocabulary.py::test_search_skips_the_tags_it_is_told_to` exits 0.
- [x] 2.2 In `isekai/interface/ui/app.py`'s `read_tags` (`:661`), pass `skip=shared.field_map().excluded`, per
  [D3](design.md#d3); add `test_the_tag_search_offers_no_excluded_tag` to `tests/test_ui_api.py`, per
  [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_ui_api.py::test_the_tag_search_offers_no_excluded_tag` exits 0.
- [x] 2.3 In `tests/test_ui_api.py`'s `test_the_excluded_list_reaches_no_group_and_is_not_in_the_response`, the
  comment "The committed table's excluded list is empty" → "The fixture table's excluded list is empty".
  Verify: `grep -c -F "The fixture table's excluded list is empty" tests/test_ui_api.py` prints `1`.
- [x] 2.4 Give `validate()` in `isekai/shared/fields.py` its `excluded` check and docstring per [D4](design.md#d4);
  add `test_a_sheet_carrying_an_excluded_tag_is_refused` to `tests/test_sheet_schema.py`, per [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_sheet_schema.py::test_a_sheet_carrying_an_excluded_tag_is_refused` exits 0.
- [x] 2.5 Give `approve` and `_copy_approval` in `isekai/pipeline/review.py` their `excluded` per [D5](design.md#d5);
  add `test_an_excluded_tag_refuses_approval_naming_the_remedy` and `test_an_excluded_tag_refuses_a_copied_approval`
  to `tests/test_review.py`, per [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_review.py -k excluded_tag` exits 0.
- [x] 2.6 In `isekai/interface/cli.py`'s approve call (`:928-934`), pass `excluded=field_map().excluded`, per
  [D5](design.md#d5); add `test_approve_refuses_a_tag_the_wired_field_map_excludes` to `tests/test_pipeline_cli.py`,
  per [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_pipeline_cli.py::test_approve_refuses_a_tag_the_wired_field_map_excludes` exits 0.
- [x] 2.7 In `isekai/interface/ui/app.py`'s approve handler (`:827-829`), pass `excluded=shared.field_map().excluded`,
  and give `tests/test_ui_api.py`'s fake `approve_` (`:1013-1024`) the same keyword, per [D5](design.md#d5); add
  `test_approve_refuses_an_excluded_tag_the_draft_saved` to `tests/test_ui_api.py`, per [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_ui_api.py::test_approve_refuses_an_excluded_tag_the_draft_saved` exits 0.
- [x] 2.8 In `isekai/pipeline/sheet.py`, pass `excluded=field_map.excluded` to `validate` at `:189`, `:270` and
  `:305`, per [D6](design.md#d6); add `test_sheet_preparation_refuses_an_excluded_tag` to
  `tests/test_sheet_stage.py`, per [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_sheet_stage.py::test_sheet_preparation_refuses_an_excluded_tag` exits 0.
- [x] 2.9 Amend D2 in `docs/decisions.md:60-67` in place to [the decision](design.md#the-decision), per
  [D7](design.md#d7).
  Verify: `grep -c -e 'Why those excluded' -e 'Made by:\*\* .0021., .0101.\.$' docs/decisions.md` prints `2`.
