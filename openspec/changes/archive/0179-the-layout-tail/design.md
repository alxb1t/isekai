# The layout tail — design

The layout names each kind of an edit's file once, and the draft's and the source copy's names move into the foundation. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`isekai/foundation/layout.py` lists an edit's files by hand in `is_edit_file`, `edit_numbers` and `delete_edits`, each in its own order:

| function | order it takes the suffixes in |
|---|---|
| `is_edit_file` | composite, placement, record, image |
| `edit_numbers` | image, composite, placement, record |
| `delete_edits` | image, record, placement, composite |

Each loop tests a full match of the stem, so the order changes no answer. `delete_edits`' order is the one that matters: the image goes first, so a delete cut short leaves a request that reads as pending. The edit stage spells the composite's suffix again in `_ready` (`isekai/pipeline/edit.py`).

`DRAFT`, `current_draft` and `source_copy` sit in `isekai/pipeline/review.py`. Their bodies read foundation names alone: `latest_artifact`, `approved_versions`, `version_of`, `SOURCES` and the flow module's `OUTPUT_SUFFIX`. `render.py`, `ui/surface.py`, `ui/library.py` and `routes/reviewing.py` import them from the stage. A delete owner in the foundation could not name them without importing a stage.

## Goals / Non-Goals

- Goals: each of an edit's suffixes is spelled once; the draft's label and the source copy's path are foundation names; the render verb and the app's surface stop importing the review stage; no file a run writes changes.
- Non-Goals: see [proposal](proposal.md#not-in-this-change). In short, the thumbnail and the delete owner are later versions, and `edit_files` and `placement_file` stay as they are.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `EDIT_SUFFIXES` is one tuple in `layout.py`, in delete order; `is_edit_file`, `edit_numbers` and `delete_edits` read it | a list spelt in each function's own order is a chance to miss a kind at each; the delete's order is the one that carries a reason | a named constant for `.png`: the image suffix has no other reader in the layout; a tuple in each function's own order |
| [D2](#d2) | `_ready` names the composite by `EDIT_COMPOSITE` | the suffix is spelled once, in the layout | leaving the string: a changed suffix would break the edit stage alone |
| [D3](#d3) | `DRAFT` is in `names.py`; `current_draft` and `source_copy` are in `layout.py`; `run.py` re-exports them; review imports them from `run.py` and keeps them bound | the bodies read foundation names alone, and the owner of a delete cannot sit in the foundation without them | a new module for the draft: a file for `current_draft` and `source_copy` alone; moving the tests' imports: the tests import them from review and hold |
| [D4](#d4) | `render.py`, `ui/surface.py`, `ui/library.py` and `routes/reviewing.py` read them from `isekai.foundation.run` | a module above the pipeline reads the layout from the foundation ([D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation)) | leaving review's names bound for them: the stage import stays |
| [D5](#d5) | the loops of `is_edit_file`, `edit_numbers` and `delete_edits`, `current_draft` and `source_copy` are measured by `tools.mutate` before a line moves; the cases for the moved names are written first and green on the old home | a move is pre-flighted, and a case at the new home proves the move kept the name's answers | a pre-flight over the whole of `layout.py`: its other lines move in no phase |
| [D6](#d6) | D69 is amended and no decision is added | the change widens D69's list of names and adds no rule | a new decision: the rule that a module above the pipeline reads the layout from the foundation is D69's |

### D1

`EDIT_SUFFIXES` follows `EDIT_PLACEMENT` after one blank line, and two blank lines follow it:

```python
# The four suffixes an edit's files take after the stem, in the order a delete takes
# them: the image, then its record, its placement and its composite, so a delete cut
# short leaves a request that reads as pending rather than an image no record explains.
EDIT_SUFFIXES = (".png", EDIT_RECORD, EDIT_PLACEMENT, EDIT_COMPOSITE)
```

`is_edit_file` and `edit_numbers` loop `for suffix in EDIT_SUFFIXES:`, each loop's body unchanged. `delete_edits` is:

```python
    deleted: list[Path] = []
    for number in numbers:
        for suffix in EDIT_SUFFIXES:
            path = group / f"{edit_stem(seed, number)}{suffix}"
            if path.is_file():
                path.unlink()
                deleted.append(path)
    return deleted
```

`edit_files` keeps its paths and `placement_file` its one; callers that want one path read them. `run.py` re-exports `EDIT_SUFFIXES` beside `EDIT_STEM`. A path built as `group / "42.edit-1.png"` is the path `edit_files` returned, so every list `delete_edits` returns is as it was.

### D2

`_ready` builds the composite's name as `f"{record.name.removesuffix(EDIT_RECORD)}{EDIT_COMPOSITE}"`. The edit stage adds `EDIT_COMPOSITE` to its import from `isekai.foundation.run`, where it already imports `EDIT_RECORD`.

### D3

`DRAFT = "draft"` goes into `names.py` after `APPROVED`, and the comment above them says both are there because `review` writes them and other parts of the run read them. `current_draft` and `source_copy` go to the end of `layout.py`, their text unchanged, in this order, each after the blank lines the file keeps between definitions. `layout.py`'s imports gain the flow module's `OUTPUT_SUFFIX` and `names.py`'s `DRAFT` and `SOURCES`.

The module's docstring names them as this text does, which fixes the line numbers the closing runs name:

```python
"""A run's numbering and completion, its seeds, its render groups and its edit files.

The version numbers a directory holds and the one it takes next, the paths of a flow's
sheets and approvals, the seeds a render's file is named for, the names of a render's
image and record, the rule that a seed is rendered, the listing of a flow's render
groups and their seeds, the refs an image's path names, the version an artifact's name
spells, the files an edit writes beside its source, the draft being worked on and the
copy of the image a draft was drafted from. `run.py` re-exports each name; a module
outside the foundation imports them from there (D69, D70).

Stdlib only, and on `python -m isekai`'s import graph.
"""
```

`run.py` imports `DRAFT` from `names.py` and `current_draft` and `source_copy` from `layout.py`, and lists them in `__all__`. `review.py` deletes `DRAFT = "draft"` and the definitions of `current_draft` and `source_copy`, and imports them from `isekai.foundation.run`. Every name stays bound in review, so `tests/test_review.py`, `tests/test_ui_api.py` and the browser tests, which import them from the stage, hold with no edit.

### D4

Each module of D4's row drops its name from its `isekai.pipeline.review` import and adds it to its import from `isekai.foundation.run`. `render.py` and `ui/surface.py` import nothing else from the stage, so their import of it goes; `ui/library.py` keeps `Status`, `came_from` and `state`, and `routes/reviewing.py` the rest of its list.

### D5

The pre-flight is `tools.mutate` over each range, one run a range, on the tests that reach it. The cut ran each at `a6d6d745`:

| range at the base | command | result |
|---|---|---|
| `is_edit_file`, `layout.py:241-251` | `uv run python -m tools.mutate isekai/foundation/layout.py:241-251 --tests tests/test_run_directory.py tests/test_edit.py tests/test_edit_placement.py tests/test_edit_session.py` | 4 killed, 0 survived |
| `edit_numbers`, `layout.py:283-298` | the same, over `283-298` | 5 killed, 0 survived |
| `delete_edits`, `layout.py:307-322` | the same, over `307-322` | 3 killed, 0 survived |
| `current_draft`, `review.py:122-134` | `uv run python -m tools.mutate isekai/pipeline/review.py:122-134 --tests tests/test_review.py tests/test_run_directory.py` | 6 killed, 0 survived |
| `source_copy`, `review.py:375-380` | the same, over `375-380` | 1 killed, 0 survived |

No mutant survives at the base, so no case is written to kill one and none is named equivalent. A build whose base differs runs the same commands over each function's lines from its `def` to its last line, and kills a survivor by a case in `tests/test_run_directory.py` before the lines move.

The closing runs name the ranges of `layout.py` as D1 and D3 leave it:

| function | range after the change |
|---|---|
| `is_edit_file` | `layout.py:249-259` |
| `edit_numbers` | `layout.py:291-306` |
| `delete_edits` | `layout.py:315-330` |
| `current_draft` and `source_copy` | `layout.py:415-435` |

They sit in phase 2's last tasks, because that phase is the last to edit `layout.py`; a range in phase 1 would be shifted by phase 2's imports and its docstring. A rescue re-fits them if the file's text differs from D1 and D3. The runs leave `tests/test_ui_api.py` out: its draft-lock race times a mutant out, and none of these ranges is reached through the server.

The cases for the moved names are unit tests in `tests/test_run_directory.py`, written against review's names and green before a line moves, and switched to the foundation's names in the move:

| case | holds |
|---|---|
| `test_a_draft_above_the_approval_is_the_current_draft` | a directory holding `001.approved.json` and `002.draft.json` answers the draft |
| `test_a_draft_at_or_below_the_approval_is_no_current_draft` | `002.draft.json` beside `002.approved.json` answers `None`, and so does an empty directory |
| `test_a_draft_copy_is_named_for_its_version_in_the_flows_sources` | `source_copy` names `<run>/<flow>/sources/002.png` for version 2 and `012.png` for version 12 |

### D6

D69's bold paragraph gains `DRAFT`, `current_draft` and `source_copy` and the foundation's home for them, its heading stays so no link to it moves, and its *Made by* gains `0179`. The foundation README's `layout.py` row names the draft and its source copy, `layout.py`'s docstring is D3's, and the pipeline README's derived row for `review.py` is the one `tools.derive_imported_by` writes once `render.py` and `ui/surface.py` stop importing the stage.

## Tests

The change adds unit tests in `tests/test_run_directory.py` and no end-to-end run, and removes no test, so no table maps a deleted test. The pre-flight runs read `tests/test_review.py`, `tests/test_edit.py`, `tests/test_edit_placement.py` and `tests/test_edit_session.py` and change none of them.

| count | command | prints |
|---|---|---|
| unit tests added | `git grep -c -E "^def test_(a_draft_above\|a_draft_at_or_below\|a_draft_copy)" -- tests/test_run_directory.py` | `3` |

Each new case binds an existing scenario, `review:approval:draft-is-not-done` for the `current_draft` cases and `review:draft-from:a-draft-from-an-image-copies-it` for `source_copy`: this version adds no scenario, and a new test binds one that exists. They sit at the lowest layer, over a directory and a `Run` in `tmp_path`, with no run opened and no page booted.

## Dependencies

None.

## Risks / Trade-offs

- **A closing range shifts if the text differs from D1 and D3.** The runs name ranges of a file this change edits. A different wrapping of the docstring moves them, and a range with no mutant is refused with exit 2. A rescue re-fits them.
- **`delete_edits` no longer calls `edit_files` or `placement_file`.** Both keep their other callers, and this change removes neither.
- **Review keeps the moved names bound only for the tests.** The tests import them from the stage; moving those imports edits existing tests, which this version does not do.
- **The derived tables move with the importers, not with the documents.** `tests/test_docs.py` re-derives the *Imported by* tables, so the phase that drops the importers of the stage writes the pipeline README's row.

## Verdict

Ready to build, in the phases of [tasks](tasks.md).
