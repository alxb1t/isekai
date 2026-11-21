# The runner cut — design

`_per_item` is cut in `isekai/interface/cli.py` into one shared item, a builder per stage verb, a table and a runner, so that its ratchet rows go and nothing it prints changes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`dispatch` hands a verb that has no row `run` to `_per_item(verb, args, wired, flows, collected)`, which returns `work(identifier)`. `prepare` calls it too, through `run_prepare`, for `tag`, for `caption` and for `sheet` a flow ([D58](../../../docs/decisions.md#d58--a-verb-is-declared-once-in-its-familys-module)). `work` holds `assign`, then opens the run, then `show`, then a chain of branches, `caption`, `tag`, `sheet`, `review` and `approve`, each defining a step; a last `else` refuses a verb that is no stage. A nested `reported` and the `across` loops then run the step.

The rows are `isekai/interface/cli.py::_per_item` and `isekai/interface/cli.py::_per_item.work` of `LONG_FUNCTIONS` in [`tests/test_ratchets.py`](../../../tests/test_ratchets.py). A row goes in the version whose function drops to 100 lines or fewer ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).

## Goals / Non-Goals

- Goal: `_per_item` and every new function at 100 lines or fewer, six positional parameters at most.
- Goal: every printed line, progress line and exit code byte-equal, and the order of every read unchanged.
- Non-goal: any move out of `cli.py`, any new import, any decision, any change to a test's assertion, a file of `tests/record/`, or the docs.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One frozen `_Item` holds what a `_per_item` call shares; `_item_of` builds it | the branches read the same things, and a builder with them in hand needs no closure | a closure per builder; a parameter per read |
| [D2](#d2) | A builder is `(run, item) -> step` and does nothing but return the step; every read happens inside the step | `_seam`'s refusal and the tagger's open are reported by `reported` as the step's own | reading the seams in the builder, before `start` is printed |
| [D3](#d3) | `_BUILDERS` maps the verb's name to its builder; a miss raises the chain's last refusal, after the run is opened | the refusal text and its place in the order stay byte-equal | a table with a default row; the miss before `run_for` |
| [D4](#d4) | `_run_item(verb, run, item)` looks up the builder, builds the step and runs it once, or once a flow | it is the code `work` ends with, apart | keeping it nested in `work` |
| [D5](#d5) | `assign` and `show` stay in `work`, before the table | they are no stages, and a row's run is called before the flows are read | table rows for them |
| [D6](#d6) | The tagger's open is memoised inside `_item_of`, so each `_per_item` call opens it once | `prepare` builds a work for each step, and its `tag` work opens the tagger once | one open for the process |
| [D7](#d7) | The ratchet rows of `_per_item` go in the phase that cuts it, and `FUNCTION_ROWS` follows | a row whose offender no longer offends is red | removing the rows in a later phase |
| [D8](#d8) | A mutation run over `_per_item` opens the change, and one over the new code closes it; `PB-2b` is re-pointed | [CONTRIBUTING](../../../CONTRIBUTING.md) pre-flights a move; `PB-2b`'s find text leaves `_per_item` | trusting the suite alone |

### D1

```
@dataclasses.dataclass(frozen=True)
class _Item:
    args, wired, flows, collected, reporter, new_version,
    vocabulary, field_map, tagger
```

`reporter` is `Reporter(wired.out, wired.err, getattr(args, "progress", None) == "json")`. `new_version` is `bool(getattr(args, "new_version", False))`. `vocabulary` and `field_map` are the memoised thunks `_per_item` holds today, `field_map` handed the memoised vocabulary. `tagger` is today's `tagger` function: it returns the thunk that opens the local tagger once. `collected` is the caller's list, shared by reference. `_item_of(args, wired, flows, collected)` builds it and carries the docstrings of those thunks.

### D2

A builder never reads `wired.reader`, `wired.tagger`, `wired.hosted_tagger`, the vocabulary or the field map; its step does, as the branch's nested function did. The builders are `_caption_step`, `_tag_step`, `_sheet_step`, `_review_step` and `_approve_step`. A step takes the flow's name as a `str`; the photograph's verbs, `caption` and `tag`, ignore it.

The approve step reads `flow = item.flows[name]` after its `--cancel` branch has returned, as the branch read `flows[name]` there and not before, and passes `definition=flow,` to `approve`, on a line of its own with a trailing comma, so that `PB-2b` has one text to find.

### D3

```
_BUILDERS: Mapping[str, _Builder] = {"caption": _caption_step, "tag": _tag_step,
    "sheet": _sheet_step, "review": _review_step, "approve": _approve_step}
miss -> Refusal(f"{verb!r} is not a stage this build runs")
```

No CLI verb reaches the miss: `dispatch` gives `_per_item` only verbs that are stages, `assign` and `show`. A test reaches it by calling `_per_item` directly, and holds its place in the order: the run is opened before it, and no progress line is printed for it.

### D4

```
work(identifier)
  ├─ assign ────────────────────▶ _assign(...)                 (D5)
  ├─ run_for, a refusal reported for each name
  ├─ show ──────────────────────▶ report(run, ...)             (D5)
  └─ _run_item(verb, run, item)
        ├─ build = _BUILDERS.get(verb)      miss: the refusal   (D3)
        ├─ step  = build(run, item)
        └─ names = [None] for a photograph's verb, else the flows
             across(names, each name: _reported(item, run, verb, name, step))
```

`_reported(item, run, verb, name, step)` is today's `reported`: a `start` line, the step, its `refused` line when it raises or when `collected` grew, else `done`. A photograph's verb passes `""` to its step and `None` to the reporter, so its progress line names no flow. The `tag` step still collects each tagger's refusal into `item.collected` itself.

### D5

The order inside `work` stays: `assign`; `run_for` with its refusal reported once for each name; `show`; then `_run_item`. A refusal of the table's miss is raised, not collected, as the chain's was.

### D6

`prepare` calls `_per_item("tag", …)` once, so one `_Item` is built once, and its tagger thunk opens the tagger on the first photograph that needs it. A second `_per_item` call builds a second `_Item` and a second memo, as today.

### D7

`LONG_FUNCTIONS` loses its `_per_item` and `_per_item.work` rows and `FUNCTION_ROWS` is 6. No row is added: each new function stays under the ceilings of its tables. `PATCHED_MODULES` is untouched: no test patches a new name.

### D8

Before any line moves, `uv run python -m tools.mutate` runs over `isekai/interface/cli.py:372-582`, the lines of `_per_item`, on the tests that cover it. A survivor is killed by a new case in `tests/test_pipeline_cli.py`; one no case can kill is named equivalent, with its reason, in the commit body. After the cut the same tool runs over the new code, from `_Item` to the line before `_assign`. `PB-2b`, the one standing mutant in `_per_item`, has its find text `definition=flows[name],` replaced by `definition=flow,`, its replace text `definition=None,`, in the phase that moves the approve branch.

## Tests

Adds unit cases for the table's miss, its text and its place in the order, and one case for each survivor of the mutation run over `_per_item`; each sits in `tests/test_pipeline_cli.py`, the lowest layer that reaches `_per_item`, and carries `spec_exempt("structural: …")` as the file's other cases do. Removes no test, so there is no table of removed tests. Adds no end-to-end run and no browser test.

`tests/test_ratchets.py` loses the rows of `_per_item`, and `tests/mutants.json` has `PB-2b` re-pointed; neither changes an assertion. The suite is the proof: the cases of `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_tagging.py`, `tests/test_assign.py`, `tests/test_progress.py` and `tests/test_review.py` read every line `_per_item` prints. The replay `uv run python -m tools.mutate --edits tests/mutants.json` holds `PB-2b`.

## Dependencies

None.

## Risks / Trade-offs

- A survivor the run finds at the start may need a case that is hard to write; the commit body may name it equivalent, with its reason.
- `ty` may refuse a step that ignores its `str` argument, or a table value typed as a function. The fix is in the annotation, never in a `# type: ignore`.
- `ruff format` may fold `definition=flow,` onto one line; the trailing comma keeps it apart, and the replay in phase 2 proves it.
- A mutant of the old chain is not replayed on the new code: the first run is the old code's proof and the last run the new code's.
- `tools.mutate` edits one line of a function body, so `_BUILDERS` and `_Item`, at module level, get no mutant; the verb cases of `tests/test_pipeline_cli.py` hold each table entry, since each verb runs through `dispatch`.
- The mutation run of 1.3 may find no survivor, and then its `Verify:` holds before the task. The range of 3.2 is known only after phase 2, so its `Verify:` is the replay, a proxy, and the task's own run is the proof.

## Verdict

Ready to build in the phases of [tasks](tasks.md): pin `_per_item` by mutation, cut it, then replay the mutation over the new code.
