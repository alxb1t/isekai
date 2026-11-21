# The stage attempt — design

One function, `attempt` in `isekai/foundation/run.py`, owns the sequence `caption`, `wd14`, `tags` and `sheet` share, and each refusal stays byte-equal. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Each of `caption`, `wd14`, `tags` and `sheet` ends in the same sequence, spelled at its own site: `caption` in `isekai/pipeline/caption.py`, `wd14` and `tags` in `isekai/pipeline/tagging.py`, `sheet` in `_from_tag_list` of `isekai/pipeline/sheet.py`.

```
guard + numbering   (each site's own)
check_budget(key, directory, version, run)
[open step]         caption: read the briefing · wd14: open_tagger()
try: work           caption/tags: StageFailure · wd14: Refusal, OSError · sheet: Refusal
except: record_failure(...) ; raise refusal_for(...) from failed
```

[D73](../../../docs/decisions.md#d73--a-stage-is-declared-once-in-isekaifoundationproducerspy) declares each stage once, in `PRODUCERS`, and accepts the sequence inside a stage as it is. The sites differ only in the caught exceptions, the kind (`failed.kind` for a `StageFailure`, `permanent` otherwise), the refusal's noun, and the open step that `caption` and `wd14` take between the check and the work.

`refusal_for` reads `stage_command`, which reads the `RUNS_ROOT` one test patches on `isekai.foundation.run`; a sibling of `run.py` imports no `run.py` ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)). So the function that calls it sits beside it, in `run.py`.

No test holds a refusal whole. The suite holds fragments: `tests/test_run_directory.py` the remedy and the record's place, `tests/test_sheet_stage.py` the ending, `tests/test_resume.py` the command's prefix.

## Goals / Non-Goals

- Goal: every refusal, every record file and every exit of `caption`, `wd14`, `tags` and `sheet` byte-equal to the base.
- Goal: `refusal_for` within the ratchet's ceiling of positional parameters, and its row gone from the wide-function ratchet.
- Non-goal: `assemble` and `render` in `isekai/pipeline/generate.py`, a stage's guard or numbering, a field of the row for the refusal's noun, a changed assertion, a file under `ui/`, `tools/` or `evaluation/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `attempt` in `run.py` owns the budget's check, an optional open step, the work, the failure's record and the refusal, for `caption`, `wd14`, `tags` and `sheet` | the sequences are the same up to the key, the noun, the caught exceptions, the flow and the open step, and `attempt` calls `stage_command`, which a sibling of `run.py` may not reach | `attempt` in `failures.py`, which cannot import `run.py` |
| [D2](#d2) | The open step runs after the budget's check and outside the `try`; the budget is checked first | the open step keeps which refusal an exhausted run sees, and `wd14`'s opens a graph of 467 MB; inside the `try` a build condition would be recorded as a photograph's failure | opening before the check; opening inside the `try` |
| [D3](#d3) | `producer_for(key)` in `producers.py` returns a stage's row; `refusal_for` reads the folder, the verb and the budget key from it | the key is the budget's key and the `stage` of a record, and `attempt` and `refusal_for` then take one argument for three | a dict beside `PRODUCERS`; passing the row |
| [D4](#d4) | `refusal_for(key, run, kind, detail, record, flow, *, noun)`; the noun stays the site's argument, as a keyword | one function reads the noun, so a field of the row is not earned; `key`, `run`, `kind`, `detail`, `record` and `flow` meet the ceiling | the noun as a field of the row |
| [D5](#d5) | `assemble` and `render` keep their own sequences | the paid stage's per-seed check decides spending, its refusals have their own templates, and its failure's kind is a boundary class the foundation cannot import | one function for the six |
| [D6](#d6) | Cases that hold each stage's refusal whole are written and green before a line moves, and a mutation run pins each sequence and `refusal_for` | byte-equal is the promise, and only fragments are held today | moving first and comparing by eye |
| [D7](#d7) | Each site keeps its guard and its numbering; `caption`'s briefing and `wd14`'s tagger are the open step | the guards and numbering differ, and `sheet`'s unrecorded refusals sit before its budget | a guard inside `attempt` |
| [D8](#d8) | [D73](../../../docs/decisions.md#d73--a-stage-is-declared-once-in-isekaifoundationproducerspy)'s *Accepts* is amended; no decision is added | the sequence is no longer inside a stage, and the series' rule amends a document the change makes false | a new decision |

### D1

```
caption.caption ─┐
tagging.tag_wd14 ┤
tagging.tag_hosted ┼─▶ run.attempt ─▶ failures.check_budget / record_failure
sheet._from_tag_list ┘                 run.refusal_for ─▶ run.stage_command (RUNS_ROOT)
```

`attempt(key, run, directory, version, work, *, noun, catching, flow=None, opening=None)` returns what `work` returns:

1. `check_budget(key, directory, version, run)`.
2. When `opening` is given, call it once and keep its result.
3. In a `try`, return `work(opened)`, or `work()` when there is no `opening`; `opening is None` decides, never the opened value, so an empty briefing is still handed to `work`.
4. On an exception of `catching`: the kind is `failed.kind` when `failed` is a `StageFailure`, else `permanent`; the detail is `str(failed)`; `record_failure(directory, version, kind, {"stage": key, "detail": detail})`; `raise refusal_for(...) from failed`.

An exception outside `catching`, and one raised by `opening`, leaves `attempt` unrecorded. `str(StageFailure)` is its `detail`, so the detail of `caption` and `tags` is as before; `wd14` and `sheet` catch no `StageFailure`, so their kind is `permanent`, as before. `key`, `run`, `directory`, `version` and `work` are its positional parameters. The typing of `work` and `opening` is the build's, and `ty` stays green without a suppression.

### D2

The order is a promise to the operator, held by `tests/test_tagging.py` for a complete run and by the cases of phase 1 for an exhausted one: an exhausted `wd14` refuses without hashing the graph, an exhausted `caption` without reading the briefing. `wd14` returns the scores with the tagger's pins, so the site reads `pins` after the call without holding the tagger.

### D3

`producer_for(key)` finds the row in `PRODUCERS` and raises `KeyError` for a key it lacks, as `BUDGETS[stage]` does. The module imports nothing of `isekai`. `run.py` re-exports it under `__all__` ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)).

| key | folder | verb | what a site passed before |
|---|---|---|---|
| `caption` | `captions` | `caption` | `CAPTIONS`, `STAGE` |
| `wd14` | `wd14` | `tag` | `WD14`, `VERB` |
| `tags` | `tags` | `tag` | `TAGS`, `VERB` |
| `sheet` | `sheets` | `sheet` | `SHEETS`, `STAGE` |

### D4

In the phase that adds `attempt`, it calls `refusal_for` in its present form, with the folder, the verb and the key read from the row. The phase that narrows the function changes `refusal_for(key, run, kind, detail, record, flow, *, noun)`, the call in `attempt` and the test call in `tests/test_run_directory.py`. The text of the refusal is not edited.

The row `isekai/foundation/run.py::refusal_for` leaves `WIDE_FUNCTIONS`, and `WIDE_ROWS` is 12. The ratchet reads a row whose offender no longer offends as red, so the row goes in the phase that narrows the function.

### D5

`isekai/pipeline/generate.py` does not change.

### D6

The cases hold the whole text of each stage's refusal. The templates, from `refusal_for`, with `R` the run's `--runs` option when its root is not the default and `N` the `--new-version` option when the record's version is above 1:

| stage | when | text |
|---|---|---|
| `caption`, `tags` | transient, below the budget | `<id>: the <noun> failed (transient) -- <detail>; see photo/<folder>/<record>, and run `<command>` again once what it names is fixed` |
| `caption`, `tags` | permanent, or at the budget | `<id>: the <noun> failed (<kind>) -- <detail>; see photo/<folder>/<record>, fix what it names and delete it, then run `<command>`` |
| `wd14` | always permanent | the same, `the tagger failed (permanent)`, folder `wd14` |
| `sheet` | always permanent | the same, `the sheet failed (permanent)`, `see <flow>/sheets/<record>`, command `python -m isekai sheet --flow <flow><R><N> <id>` |

`<noun>` is `reader` for `caption` and `tagger` for `wd14` and `tags`. A mutation run over a sequence is one run per line range, with `uv run python -m tools.mutate <path>:<first>-<last> --tests …`; a survivor is killed by a case, and one no case can kill is named equivalent, with its reason, in the commit body. The ranges are found by the tasks, since earlier changes move the files.

### D7

```
caption   guard: latest(...) and not new_version → None     numbering: next_version
wd14      same                                              open step: open_tagger
tags      same                                              no open step
sheet     guard in sheet(); two unrecorded refusals before the budget; numbering (kept or 0) + 1
```

`sheet` keeps `_from_tag_list`'s absent-list refusal and its draft branch, which return or refuse before the budget; `attempt` is called where `check_budget` was.

### D8

[D73](../../../docs/decisions.md#d73--a-stage-is-declared-once-in-isekaifoundationproducerspy)'s *Accepts* no longer says the sequence inside a stage stays: it says `attempt` is the sequence of `caption`, `wd14`, `tags` and `sheet`, the paid stages keep their own, and the other tables stay. Its statement gains a sentence naming `attempt` and `producer_for`; its *Made by* gains `0188`. The *Files* rows of `run.py` and `producers.py` in `isekai/foundation/README.md` name `attempt` and `producer_for`.

## Tests

Adds tests at the unit layer, none end-to-end and none in a browser. Removes no test, so there is no table of removed tests; no existing assertion changes.

| layer | file | added | binds |
|---|---|---|---|
| unit | `tests/test_caption.py` | the whole refusal of `caption`, below its budget and exhausted | `cli:refusals:refusal-names-the-remedy` |
| unit | `tests/test_tagging.py` | the whole refusal of `tags`, below its budget and exhausted; of `wd14` | `cli:refusals:refusal-names-the-remedy` |
| unit | `tests/test_sheet_stage.py` | the whole refusal of `sheet` | `cli:refusals:refusal-names-the-remedy` |
| unit | `tests/test_run_directory.py` | `attempt`: the budget before the open step, the open step outside the `try`, the kind and the record, the chained refusal, an exception outside `catching`; `producer_for` | `run-directory:budget:at-budget-the-stage-refuses`, `run-directory:failure:kind-and-attempt-are-in-the-filename` |
| unit | `tests/test_ratchets.py` | none: the `WIDE_FUNCTIONS` row of `refusal_for` goes, and `WIDE_ROWS` is 12 | — |

- The cases bind scenarios that exist, since a `spec_exempt` that is no twin raises a ceiling that only shrinks.
- The whole-refusal cases are written against the code as it stands, stay green through every phase and are the proof of equality.
- The cases are counted by `uv run pytest --collect-only -q tests/test_caption.py tests/test_tagging.py tests/test_sheet_stage.py tests/test_run_directory.py`, before and after.
- A case builds a run in `tmp_path` and calls a fake; none boots a browser, so none carries `slow`.

End-to-end runs added: none; `git grep -n -e 'tests/e2e' -- openspec/changes/0188-the-stage-attempt/tasks.md` prints nothing.

## Dependencies

None.

## Risks / Trade-offs

- A mutation run may leave a survivor a case cannot kill; the commit body names it equivalent, with its reason.
- `ty` may not type `work` over an optional open step in one signature. The fix is an overload or a second entry point, never a `# type: ignore`.
- `attempt` is read through `run.py` by name, so a patch of `isekai.foundation.run.RUNS_ROOT` still lands: the function stays beside `stage_command`.
- `VERB` in `isekai/pipeline/tagging.py` is read by nothing once the sites call `attempt`; it goes with its comment.
- `ruff` names each import a site no longer reads: `check_budget`, `record_failure` and `refusal_for` in `caption.py`, `tagging.py` and `sheet.py`.
- The ranges of the mutation runs are known only when the task runs, so the `Verify:` of each mutation task is a proxy that already holds: the replay of the standing mutants for 1.7 and 5.2, the stages' test files for 1.8. The run is the proof.

## Verdict

Ready to build in the phases of [tasks](tasks.md): hold the refusals whole, add `attempt` and its lookup, call it from the sites, narrow `refusal_for` and take its row out, then replay the mutation and amend the documents.
