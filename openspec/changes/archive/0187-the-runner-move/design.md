# The runner move — design

The runner the cut left in `isekai/interface/cli.py` moves, text for text, to `isekai/interface/verbs/runner.py`, and `prepare` binds its own run. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

After `0186-the-runner-cut`, `cli.py` holds, between `_seam` and `main`, `_Item`, `_item_of`, the builders `_caption_step`, `_tag_step`, `_sheet_step`, `_review_step` and `_approve_step`, `_BUILDERS`, `_reported`, `_run_item`, `_per_item`, `_assign` and `_assign_one`; `_existing_run` sits above `_flows_for`. `dispatch` calls `_per_item`, and `_prepare` hands it to `run_prepare` of `verbs/prepare.py`.

[D58](../../../docs/decisions.md#d58--a-verb-is-declared-once-in-its-familys-module) accepts that `prepare`'s run is bound in `cli.py` because it needs `_per_item`, and reopens when `_per_item` leaves.

```
before                                   after
cli.py   dispatch ─▶ _per_item           cli.py   dispatch ─▶ verbs/__init__ ─▶ runner._per_item
         _prepare ─▶ run_prepare                  render, migrate stay
verbs/prepare.py  run_prepare(per_item)  verbs/prepare.py  run_prepare ─▶ runner._per_item
```

A name that moves is read by the runner cut's cases `test_per_item_refuses_a_verb_that_is_no_stage` and `test_per_item_opens_the_run_before_it_refuses_a_verb` of `tests/test_pipeline_cli.py`: they import `_per_item` from `isekai.interface.cli`, and keep working because `cli.py` reads it ([D2](#d2)). The other tests take `build_parser`, `dispatch`, `main`, `VERBS`, `_flows_for` and `_dispatch_argv` from `cli.py`, and patch `cli.RUNS_ROOT` and `cli.wiring`, which stay. `tests/test_assign.py`'s `_assign` is that file's own helper.

## Goals / Non-Goals

- Goal: every printed line, progress line and exit code byte-equal, and the set of modules `python -m isekai` imports unchanged.
- Goal: `_per_item` read from `verbs/runner.py` by `cli.py` and by `prepare.py`, and `_prepare` gone.
- Non-goal: any edit of the moved text, any new decision, a changed assertion, a file of `tests/record/`, a file under `ui/`, `tools/` or `evaluation/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `runner.py` holds `_existing_run`, `_seam`, the runner cut's block from `_Item` to `_run_item`, `_per_item`, `_assign` and `_assign_one`, in that order, text for text | a move that edits nothing is held by the suite and by a mutation run over the same lines | a module for the builders and another for the runner |
| [D2](#d2) | `verbs/__init__.py` lists `_per_item`, and `cli.py` reads it from there under that name | `dispatch` stays byte-equal, the runner cut's cases still import it from `cli.py`, and `cli.py` enters the package by its front door alone | a public alias; `cli.py` importing `runner` by its module |
| [D3](#d3) | `run_prepare(args, wired)` drops its `per_item` parameter and `PerItem`, reads `_per_item` from its sibling `runner`, and is the run of `PREPARE_ROW`; `cli.py`'s `_prepare` goes and `run_prepare` leaves the front door | the parameter existed only because the runner lived in `cli.py`; no test calls `run_prepare` | keeping the parameter and binding it with a lambda in `prepare.py` |
| [D4](#d4) | The runs of `render` and `migrate` stay bound in `cli.py` | they need `_dispatch_argv`, and the tests patch `cli.RUNS_ROOT` and `cli.wiring` | moving them with the runner |
| [D5](#d5) | `cli.py` drops each import and the `T` its remaining code does not read, and `runner.py` imports the same names from the same modules | the import graph `python -m isekai` loads is unchanged, which the `-S` guard holds | a lazy import in `runner.py` |
| [D6](#d6) | A mutation run over the moving lines opens the change and one over their new home closes it; `PB-2b` is re-pointed in the move's phase | [CONTRIBUTING](../../../CONTRIBUTING.md) pre-flights a move; a mutant is addressed by its path, so the replay is red from the move until it is re-pointed | re-pointing it in the last phase |
| [D7](#d7) | The derived *Imported by* tables are re-derived in the move's phase, and D58 and the prose follow in the last | `tests/test_docs.py` re-derives each table, so a phase that moves an import ends red without it | deriving once, in the last phase |

### D1

The order is the order of `cli.py`, so the moved lines read as they did: `_existing_run` first, then `_seam`, then `0186`'s block from `_Item` to `_run_item`, then `_per_item`, `_assign` and `_assign_one`. The module opens with a docstring, then the imports the moved code reads, then `T = TypeVar("T")` for `_seam`. A function's body, signature and docstring are not edited.

### D2

```
verbs/runner.py ─▶ verbs/__init__.py  (import and __all__: _per_item)
cli.py:            from isekai.interface.verbs import ..., _per_item, ...
dispatch:          work = _per_item(verb, args, wired, flows, collected)   # unchanged line
```

`common.py` already lets a sibling import a private name (`_session_id`, `_Targets` in `session.py`). `_seam`, `_assign`, `_assign_one` and `_existing_run` are read inside `runner.py` alone once moved, so none is listed.

### D3

`run_prepare` keeps its body: its calls `per_item("tag", …)`, `per_item("caption", …)` and `per_item("sheet", …)` become calls of `_per_item` imported by `from isekai.interface.verbs.runner import _per_item`. `PREPARE_ROW` gains `run_prepare` as the `run` field of its `Verb`. `dispatch` calls a row's run before it reads the flows, as it called `_prepare`'s.

### D4

`_render`, `_migrate`, `_dispatch_argv`, `RUNS_ROOT` and the `wiring` import stay where they are. [D58](../../../docs/decisions.md#d58--a-verb-is-declared-once-in-its-familys-module)'s *Accepts* then names `render` and `migrate` alone.

### D5

`cli.py` keeps `PHOTOGRAPH_VERBS`, `across` and `require_tracked`, which `dispatch` reads. Each other import the moved code alone read goes, and `ruff check` names it: `LocalTagger`, `load_caption_config`, `assign`, `find_run`, `report`, `approve_across`, `Reporter`, `once`, `run_for`, `run_or_photo`, `say`, `caption`, `approve`, `discard`, `review`, `cancel_approval`, `sheet`, `tag_hosted`, `tag_wd14`, `FieldMap`, `Vocabulary`, `cache` and `TypeVar`, as far as nothing else reads them. `runner.py` takes them from the modules `cli.py` took them from, the verbs' own through `isekai.interface.verbs.common`.

### D6

Before any line moves, `uv run python -m tools.mutate` runs over `_existing_run` and over `_seam` to the line before `main`, in `cli.py`, on the tests that cover them. A survivor is killed by a new case in `tests/test_pipeline_cli.py`; one no case can kill is named equivalent, with its reason, in the commit body. After the move the same tool runs over `runner.py` from `_existing_run` to its last line.

`PB-2b`, the standing mutant in the approve builder, has its `path` changed to `isekai/interface/verbs/runner.py`; its `find`, `replace`, `tests` and `why` stand, since the moved text is the text.

### D7

The move changes which module imports `caption.py`, `tagging.py`, `sheet.py`, `review.py`, `field_map.py`, `vocabulary.py`, `wd14.py`, `caption_config.py`, `drafting.py` and `run_view.py`, so `uv run python -m tools.derive_imported_by` runs in phase 2. The hand-written rows follow in phase 4: the *Files* row of `runner.py`, the rows of `cli.py` and `verbs/__init__.py`, D58 and the docstring of `cli.py`. The table is derived where the import moves.

## Tests

Adds no test unless the mutation run of phase 1 finds a survivor a case can kill; such a case sits in `tests/test_pipeline_cli.py`, the lowest layer that reaches the runner, and carries `spec_exempt("structural: …")` as the file's other cases do. Removes no test, so there is no table of removed tests. Adds no end-to-end run and no browser test.

`tests/mutants.json` has `PB-2b` re-pointed; no assertion changes. The suite is the proof: the cases of `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_tagging.py`, `tests/test_assign.py`, `tests/test_progress.py` and `tests/test_review.py` read every line the runner prints, the record's and the layers' tests hold each verb's arguments, the cycle rule and the front-door rule, and `tests/test_docs.py` the derived tables. The replay `uv run python -m tools.mutate --edits tests/mutants.json` holds `PB-2b`.

## Dependencies

None.

## Risks / Trade-offs

- A survivor the run finds at the start may need a case that is hard to write; the commit body may name it equivalent, with its reason.
- The ranges of the mutation runs are known only after `0186-the-runner-cut` is built, so each task finds them first and its `Verify:` is the replay, a proxy; the run is the proof.
- `ty` may refuse the import of a private name through the front door. The fix is in the import, never in a `# type: ignore`.
- A derived row names a module by path, so a mistake in phase 2's derive shows only in `tests/test_docs.py`; phase 3 may move no row, and its derive is then a no-op.
- `tools.mutate` edits one line of a function body, so `_BUILDERS` and `_Item`, at module level, get no mutant, as in the cut.

## Verdict

Ready to build in the phases of [tasks](tasks.md): pin the moving lines by mutation, move the runner, bind `prepare`'s run, then replay the mutation and amend the documents.
