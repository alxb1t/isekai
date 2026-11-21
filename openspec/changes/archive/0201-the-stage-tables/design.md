# The stage tables — design

Hold the tables above the foundation to the stage record by one guard, read `_KINDS`' keys from the record, and write Prepare's order and its tag rule once, beside it. Verdict: ready to build, in the phases of [tasks](tasks.md); the guard passes before a line moves, and the cases of Prepare pass before its move.

## Context

[D73](../../../docs/decisions.md#d73--a-stage-is-declared-once-in-isekaifoundationproducerspy) puts each stage in `isekai/foundation/producers.py` and leaves the tables above the foundation written by hand. These name stages:

| table | home | keys |
|---|---|---|
| `_KINDS` | `isekai/interface/ui/library.py` | each stage's folder, to the word Home's row shows |
| `STAGES` | `isekai/interface/run_view.py` | the flow's folders but `outputs`, in run order |
| `_WRITES` | `isekai/interface/cli.py` | the photograph's verbs |
| `PREPARE` | `isekai/interface/progress.py` after 0196 | tag, caption, sheet |
| `REACHED` | `isekai/interface/ui/jobs.py` | tag and sheet |
| `_BUILDERS` | `isekai/interface/verbs/runner.py` | the verbs the runner builds a step for |

`PREPARE` is in `jobs.py` where the brief read it. The design of `0196-the-child-lines-declared` moves it to `isekai/interface/progress.py`, which imports the standard library alone, and `jobs.py` imports it from there; this version follows it in the chain. Prepare's tag rule is written by `plan` of `jobs.py` and again by `run_prepare` of `verbs/prepare.py`:

```
plan(todo, tagged)             tag runs = those a tagged flow names, in that flow's order
run_prepare(args, wired)       tag a run when any of its cells' flows has a tagger
```

Neither reads the order; each spells tag, caption, sheet by hand.

## Goals / Non-Goals

- Goal: one test names each table to edit when a stage joins the record, and fails on a key the record lacks.
- Goal: `_KINDS`' keys are the record's folders, read from it, and its words stay written.
- Goal: Prepare's order and its tag rule are written once, in the foundation, and read by `plan` and by `run_prepare`.
- Goal: every line a verb prints, every wire byte and every file a run writes is as it was, held by cases written first.
- Non-goal: a field on `Producer`, or `STAGES`, `_WRITES`, `REACHED` or `_BUILDERS` derived from it.
- Non-goal: a decision added, a scenario, a spec delta, and any file under the top-level `ui/`, `tools/` or `evaluation/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One guard test and its twin in `tests/test_run_directory.py` hold the keys of these tables to the record; the runner's builders are the record's verbs less `generate`, plus `approve`; `PREPARE` and `REACHED` are held to the record's verbs, not equal to them (Q320, C28) | a new stage then fails one test that names every table to edit; `generate` is the paid stages' verb, which `generate_batch` runs, and Prepare runs tag, caption and sheet alone | a test per table, which a new table escapes; equality for `PREPARE` and `REACHED`, which name some of the record's verbs only |
| [D2](#d2) | `_KINDS` reads its keys from the record through `_WORDS`, which is keyed by the stage's key and holds the written words (Q321) | the key is the budget's key and never changes; a stage the record adds then fails at import until it has a word | a field on `Producer` for the word, which one reader does not earn (Q298); words by folder, which a folder's rename would break silently |
| [D3](#d3) | `PREPARE` and `tagged_runs(todo, taggers)` join `producers.py`, and `run.py` re-exports both (Q322, C27) | the app and the verbs may not import each other, and the layer guard counts a lazy import; the foundation is the one place both read | a copy in each reader held equal by a test, which writes the order twice; a per-photograph `any`, which reorders `plan`'s tag step |
| [D4](#d4) | `plan` and `run_prepare` walk `PREPARE` and read `tagged_runs` | the order and the rule are then in one place, and the cases of [D6](#d6) hold both readers to it | leaving the order spelt by hand in each reader |
| [D5](#d5) | `PREPARE` leaves `progress.py`; `jobs.py` imports it from `isekai.foundation.run`, so `jobs.PREPARE` stays; the test that reads it through `progress` takes it from `run` (C26, C29) | `progress.py` imports nothing of `isekai` and cannot read the foundation; a second copy would leave the order written twice | a copy kept in `progress.py` and held equal by a test |
| [D6](#d6) | The cases of `_KINDS`' words, of `plan` and of the verb are written first and pass on today's code; `tools.mutate` runs over `plan` and the verb's steps before and after | a refactor is held by what passes before it moves | cases written after the move, which prove the new lines against themselves |
| [D7](#d7) | Phases: the guard, the kinds, Prepare, the documents | the brief's own; each ends green, since the guard reads `jobs.PREPARE`, which holds before and after the move | one phase of the whole, which cannot be checked apart |
| [D8](#d8) | D73 is amended and no decision is added | no new rule: the record already declares the stage, and this holds the tables to it | a new decision for a guard |

### D1

The guard is a function, a test and its twin, after `test_the_stage_tables_are_read_from_the_record` in `tests/test_run_directory.py`. The file already imports the CLI, so it adds `Collection`, `Mapping` and `Sequence` from `collections.abc`, `Producer` from `isekai.foundation.run`, `STAGES` from `isekai.interface.run_view`, `_WRITES` from `isekai.interface.cli`, `_KINDS` from `isekai.interface.ui.library`, `_BUILDERS` from `isekai.interface.verbs.runner`, and `jobs` from `isekai.interface.ui`.

```python
def _off_the_record(
    record: Sequence[Producer], tables: Mapping[str, Collection[str]]
) -> list[str]:
    """Return the names of the tables whose keys the record does not hold."""
    verbs = {p.verb for p in record}
    holds = {
        "_KINDS": set(tables["_KINDS"]) == {p.folder for p in record},
        "STAGES": tuple(tables["STAGES"])
        == tuple(p.folder for p in record if p.scope == "flow" and p.folder != OUTPUTS),
        "_WRITES": set(tables["_WRITES"])
        == {p.verb for p in record if p.scope == PHOTO},
        "PREPARE": set(tables["PREPARE"]) <= verbs,
        "REACHED": set(tables["REACHED"]) <= verbs,
        "_BUILDERS": set(tables["_BUILDERS"]) == (verbs - {"generate"}) | {"approve"},
    }
    return [name for name, held in holds.items() if not held]


def _tables() -> dict[str, Collection[str]]:
    """Return the six tables as the code holds them."""
    return {
        "_KINDS": _KINDS,
        "STAGES": STAGES,
        "_WRITES": _WRITES,
        "PREPARE": jobs.PREPARE,
        "REACHED": jobs.REACHED,
        "_BUILDERS": _BUILDERS,
    }


@pytest.mark.spec_exempt("structural: each stage table's keys are the record's")
def test_each_stage_tables_keys_are_the_records() -> None:
    assert _off_the_record(PRODUCERS, _tables()) == []


@pytest.mark.spec_exempt(
    "structural: the guard names a table with a key the record lacks"
)
def test_a_table_with_a_key_the_record_lacks_is_named() -> None:
    for name, keys in _tables().items():
        grown = {**_tables(), name: [*keys, "mask"]}
        assert _off_the_record(PRODUCERS, grown) == [name]
    flow = Producer("mask", "masks", "flow", "mask", 1)
    photo = Producer("pose", "poses", "photo", "pose", 1)
    assert _off_the_record((*PRODUCERS, flow), _tables()) == [
        "_KINDS",
        "STAGES",
        "_BUILDERS",
    ]
    assert _off_the_record((*PRODUCERS, photo), _tables()) == [
        "_KINDS",
        "_WRITES",
        "_BUILDERS",
    ]
```

`PREPARE` and `REACHED` are read as `jobs.PREPARE` and `jobs.REACHED`, which hold before and after [D5](#d5), so no line of the guard changes in phase 3. A mutation of the guard's own lines is not run: it is a test, and its twin is its proof.

### D2

In `isekai/interface/ui/library.py` the literal `_KINDS` becomes:

```python
# What a stage's folder says was written last, for Home's row, by the stage's key.
# The folders come from the record, so a stage the record adds has no word until
# one is written here, and `_KINDS` fails at import for it.
_WORDS = {
    "caption": "caption",
    "wd14": "tag",
    "tags": "tag",
    "sheet": "sheet",
    "review": "review",
    "assemble": "prompt",
    "render": "render",
}
_KINDS: Mapping[str, str] = {
    producer.folder: _WORDS[producer.key] for producer in PRODUCERS
}
```

`PRODUCERS` joins the import from `isekai.foundation.run`. `CAPTIONS`, `OUTPUTS`, `PROMPTS` and `TAGS` leave it, since nothing else in the file reads them; `REVIEW`, `SHEETS` and `WD14` stay. `_KINDS.get(parts[3], "run")` in `_kind` is as it was.

### D3

After `producer_for` in `isekai/foundation/producers.py`, with `from collections.abc import Mapping, Sequence` among its imports, which stay the standard library's:

```python
# Prepare's order, by verb. Every flow reads one description (D17), so a photograph
# is tagged and captioned once and then sheeted for each of its cells. It is not the
# order a run passes the stages in above, which captions first.
PREPARE: tuple[str, ...] = ("tag", "caption", "sheet")


def tagged_runs(
    todo: Mapping[str, Sequence[str]], taggers: Mapping[str, bool]
) -> tuple[str, ...]:
    """Return the runs `tag` takes: those a flow that declares a tagger names.

    `todo` holds each flow's runs and `taggers` whether each flow declares one. A run
    comes once, in the order the first such flow lists it.
    e.g. {"a": ["r1", "r2"], "b": ["r2"]} with only b tagged -> ("r2",)
    """
    return tuple(
        dict.fromkeys(run for flow, ids in todo.items() if taggers[flow] for run in ids)
    )
```

The expression is the one `plan` holds today, moved whole: it keeps the plan's order and reads `taggers[flow]` for each flow of `todo`, as `plan` does. The module docstring gains a sentence naming both. `run.py` imports both names, adds them to `__all__` and nothing else. The module still imports nothing of `isekai`.

### D4

`plan` of `isekai/interface/ui/jobs.py` becomes:

```python
def plan(todo: Mapping[str, Sequence[str]], tagged: Mapping[str, bool]) -> list[Step]:
    """Return the steps that prepare `todo`'s runs, in `PREPARE`'s order.

    The photographs' steps name no flow and the sheets go by flow. `tag` takes the
    runs `tagged_runs` names, and is left out when that leaves none.
    e.g. {"summon": ["r1"]} -> tag, caption over r1, then sheet over r1 in summon
    """
    photographs = tuple(dict.fromkeys(run for ids in todo.values() for run in ids))
    described = {"tag": tagged_runs(todo, tagged), "caption": photographs}
    steps: list[Step] = []
    for verb in PREPARE:
        if verb not in PHOTOGRAPH_VERBS:
            steps += [Step(flow, verb, tuple(ids)) for flow, ids in todo.items() if ids]
        elif described[verb]:
            steps.append(Step(None, verb, described[verb]))
    return steps
```

`PHOTOGRAPH_VERBS`, `PREPARE` and `tagged_runs` join the import from `isekai.foundation.run`.

In `run_prepare` of `isekai/interface/verbs/prepare.py` the loop over `by_run` becomes:

```python
    by_run: dict[str, list[str]] = {}
    todo: dict[str, list[str]] = {}
    for run_id, flow in cells:
        by_run.setdefault(run_id, []).append(flow)
        todo.setdefault(flow, []).append(run_id)
    tagged = set(tagged_runs(todo, {name: one.tagger for name, one in flows.items()}))
    for run_id, named in by_run.items():
        step_of = {
            "tag": [tag] if run_id in tagged else [],
            "caption": [describe],
            "sheet": [sheet_of(flow) for flow in named],
        }
        steps = [step for verb in PREPARE for step in step_of[verb]]
        collected.extend(across(steps, lambda step: step(run_id)))
```

`PREPARE` and `tagged_runs` join its import from `isekai.foundation.run`.

The old `steps` list with `any(flows[flow].tagger for flow in named)` goes. A run is in `tagged` exactly when `any(...)` held, since `todo` holds a run under each flow its cells name. The lines before and after the loop are as they are.

### D5

The definition of `PREPARE` that `0196` writes in `isekai/interface/progress.py`, its comment and each other line there that names it go. `jobs.py` drops `PREPARE` from its import from `isekai.interface.progress` and takes it from `isekai.foundation.run`, so `jobs.PREPARE` is still read by `_Job.describe` and by the guard.

`TAG`, `CAPTION` and `SHEET` stay in `progress.py`: they are the words a line prints, which `0196` holds, and `REACHED` keeps keying by them. The test of the declared names that `0196` adds reads `PREPARE`, since its table of names holds it; the test takes the name from `isekai.foundation.run` in place of `isekai.interface.progress`, and its assertion stays.

### D6

| case | file | proves |
|---|---|---|
| `test_a_rows_kind_is_what_its_newest_stage_folder_says` | `tests/test_ui_library.py` | each stage folder, as the newest file of a collection, gives Home's row its word: captions `caption`, wd14 `tag`, tags `tag`, sheets `sheet`, review `review`, prompts `prompt`, outputs `render` |
| `test_prepare_plans_tag_for_the_runs_a_tagged_flow_names` | `tests/test_ui_jobs.py` | with no flow tagged the plan has no tag step; with `{FLOW: ["r1", "r2"], other: ["r2", "r1"]}` and only `other` tagged the steps are tag over `("r2", "r1")`, caption over `("r1", "r2")`, then each flow's sheet in order; a flow with no runs gives no step, and `plan({}, {})` is `[]` |
| `test_prepare_tags_a_photograph_any_of_whose_flows_tags` | `tests/test_pipeline_cli.py` | one photograph assigned `other-v1`, which `_untagged_flows` leaves untagged, and `summon-anime-wai`, named in that order, is tagged, captioned, then sheeted in `other-v1` and in `summon-anime-wai` |
| `test_prepares_order_is_tag_caption_sheet_and_the_records_verbs` | `tests/test_run_directory.py` | `PREPARE == ("tag", "caption", "sheet")` and each verb of it is a verb of `PRODUCERS` |
| `test_tagged_runs_names_each_run_a_tagged_flow_lists_once_in_its_order` | `tests/test_run_directory.py` | the examples of [D3](#d3): `{"a": ["r1", "r2"], "b": ["r2", "r3"]}` with only `b` tagged gives `("r2", "r3")`; with `a` `["r1", "r2"]`, `b` `["r2", "r1"]` and only `b` tagged it gives `("r2", "r1")`; with both tagged `("r1", "r2")`; with none, or with the tagged flow's runs empty, `()` |

The cases of the words, the plan and the verb pass on today's code. The cases of the foundation read names that do not exist until [D3](#d3), and fail on the import until it.

`tools.mutate` runs over `plan` and over the lines from `by_run: dict` to the `collected.extend(across(steps` of `run_prepare`, with `tests/test_ui_jobs.py` and `tests/test_pipeline_cli.py`, before a line moves and again on the new lines, and over `tagged_runs` once it is written. The ranges are printed at the time, for the chain before this version moves the lines.

### D7

| phase | what | the tests that hold it |
|---|---|---|
| 1 | the guard and its twin, on the code as it is | the guard, passing |
| 2 | the kinds' words held, then `_KINDS` read from the record | the case of the words; the guard |
| 3 | the cases of Prepare, then the move, the readers and the pruning of `progress.py` | the cases; the mutation runs; the suite |
| 4 | D73 and the README | `tests/test_docs.py` |

### D8

D73's bold sentence gains the names it now holds, its *Accepts* names the tables that stay written and held by a test, and its *Made by* adds `0201`. `isekai/foundation/README.md`'s row of `producers.py` names `PREPARE` and `tagged_runs`. The derived *Imported by* tables do not move: `producers.py` imports nothing of `isekai`, and `jobs.py` and `prepare.py` already import `run.py`.

## Names

| names | home after | read by |
|---|---|---|
| `PREPARE`, `tagged_runs` | `isekai/foundation/producers.py`, re-exported by `isekai/foundation/run.py` | `plan` of `jobs.py`, `run_prepare`, `jobs.PREPARE`, the guard, `tests/test_run_directory.py` |
| `_WORDS` | `isekai/interface/ui/library.py` | `_KINDS` |
| `_off_the_record`, `_tables` | `tests/test_run_directory.py` | the guard and its twin |

## Tests

The tests added are those of the table below, and none is deleted or merged, so no `I16` table is due. No end-to-end run is added; each test is the lowest layer that can fail for its behaviour (T1), and none adds a step to another (T2). The guard and its twin hold the tables as data, the cases of [D6](#d6) hold the words and the plan as units, and the verb's case runs `dispatch` on a temporary directory as its neighbours do.

| measure | command | count |
|---|---|---|
| guard and twin | `git grep -c -e "^def test_each_stage_tables_keys_are_the_records" -e "^def test_a_table_with_a_key_the_record_lacks_is_named" -- tests/test_run_directory.py` | `tests/test_run_directory.py:2` |
| cases of the foundation | `git grep -c -e "^def test_prepares_order_is_tag_caption_sheet" -e "^def test_tagged_runs_names_each_run" -- tests/test_run_directory.py` | `tests/test_run_directory.py:2` |
| case of the words | `git grep -c -e "^def test_a_rows_kind_is_what_its_newest_stage_folder_says" -- tests/test_ui_library.py` | `tests/test_ui_library.py:1` |
| case of the plan | `git grep -c -e "^def test_prepare_plans_tag_for_the_runs_a_tagged_flow_names" -- tests/test_ui_jobs.py` | `tests/test_ui_jobs.py:1` |
| case of the verb | `git grep -c -e "^def test_prepare_tags_a_photograph_any_of_whose_flows_tags" -- tests/test_pipeline_cli.py` | `tests/test_pipeline_cli.py:1` |

`tests/test_progress.py`, which `0196` adds, changes an import line and no assertion ([D5](#d5)).

The proof that no behaviour moves is the suite as it stands, the cases above, `tools.mutate` over the lines of `plan` and of the verb's steps, the standing mutants, and `tests/test_layers.py`, `tests/test_ratchets.py`, `tests/test_docs.py` and `tests/test_derive_wire.py`.

## Dependencies

None.

## Risks / Trade-offs

- The code this reads is the chain's: `progress.py` and its `PREPARE` are `0196`'s. A HALT CHECK in the first phase and in the third checks the base, and halts if it differs.
- The guard reads `generate` as a literal, the verb of the paid stages. A new paid stage with another verb fails it, which names the table to edit.
- `plan`'s tag step and the verb's tagging read one function, so a mutation of either is caught by the cases of one reader and the suite of the other.
- A line range of `tools.mutate` names the lines of the tree at the time, and an earlier version of the chain moves them; each task prints its range before it runs.
- `ruff format` may wrap a line the listings give on one. That is layout, not a change.

## Verdict

Ready to build. Each phase ends with its tests passing; the order and the rule leave the readers once nothing spells them.
