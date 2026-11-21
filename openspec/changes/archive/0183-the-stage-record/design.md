# The stage record — design

A stage is one row of a record in the foundation, and the foundation's tables that name a stage are read from it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The foundation spells a stage in several tables. `BUDGETS` is in `isekai/foundation/failures.py`, and `DESCRIPTION`, `PHOTOGRAPH_VERBS` and the stage folders' words (`CAPTIONS`, `WD14`, `TAGS`, `SHEETS`, `REVIEW`, `PROMPTS`, `OUTPUTS`) are in `isekai/foundation/names.py`. `run.py` re-exports each name, and every importer reads it from there ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)).

Every reader of these tables iterates one or tests membership in it; none indexes a fixed length. Every value is a string or an integer, so one record can sit in the foundation and import nothing.

```
foundation/producers.py   Producer · PRODUCERS            imports nothing of isekai
        ▲        ▲
        │        └──────────────┐
foundation/names.py        foundation/failures.py
  folder words, DESCRIPTION,      BUDGETS
  PHOTOGRAPH_VERBS
        ▲                       ▲
        └──────── run.py ───────┘   re-exports every name, old and new
```

The budget's key is also the `stage` field of a failure record on disk, so a row's key cannot change. `review` has a folder and no budget: it calls no model and records no failure.

`tools.mutate` mutates a line of a function body and refuses any other with exit 2, so the record's rows, which sit at module level, hold no mutant. The standing mutant `FN-1` finds the wd14 budget by its text in `failures.py`; the text moves into the record.

## Goals / Non-Goals

- **Goals:** one row per stage; the tables read from it; the same values in the same order; each table held by a case that names its literal value.
- **Non-Goals:** the interface's tables, the sequence inside a stage, `refusal_for`, the pipeline's own `STAGE` constants, the hub cell's `Stage`, the wire, and any file under `ui/`, `tools/` or `evaluation/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The record is `isekai/foundation/producers.py`: a frozen `Producer(key, folder, scope, verb, budget)` per stage, in `PRODUCERS`, in the order a run passes through them | one row says what a stage is; every field is a string or an integer, so the foundation can hold it and import nothing | a `StrEnum` of stages (an importer would learn the stage by its member, and the folder would still be a literal); a record that imports `names.py` (it could not be read back by `names.py`); the names `STAGES`, `Stage` and `STAGE` (taken) |
| [D2](#d2) | `run.py` re-exports `Producer` and `PRODUCERS` under `__all__`, and its docstring names the sibling | a module outside the foundation imports a run's names from `run.py` | importing `producers.py` from outside the foundation |
| [D3](#d3) | `BUDGETS`, `DESCRIPTION`, `PHOTOGRAPH_VERBS` and the stage folders' words are read from the record and stay bound where they were, equal in value and order | no importer and no test changes; a review stage has no budget, so its row holds `None` and `BUDGETS` leaves it out | binding each folder word by position, which a reordered row would break silently |
| [D4](#d4) | The cases come first, in `tests/test_run_directory.py`, each marked `spec_exempt("structural: …")` | the change adds no scenario, and each case holds a table's value and not a behaviour; the file already holds the budgets' cases | a new test file (the file that holds the budgets holds the rest); a spec marker (no scenario states a table) |
| [D5](#d5) | The mutation runs are over `_spent`, `exhausted` and `check_budget`, which read the budget, before the derive and after it; the record's rows are held by the cases and by `FN-1` | `tools.mutate` finds no mutant at module level; decided by the cutter (C19) | a run over the rows (refused with exit 2); no run at all |
| [D6](#d6) | `FN-1` is anchored on the wd14 row of `producers.py`; `FN-2` stays, for its line is in `_spent`, which does not move | `FN-2`'s find text occurs once in `failures.py` before and after; decided by the cutter (C20) | re-pointing `FN-2` too, which would change a line that stands |
| [D7](#d7) | The foundation README's Files row and *Imported by* row for `producers.py` come in phase 2, and the table is derived again in phases 2 and 3, where the imports arrive | `tests/test_docs.py` re-derives the table, so a phase that adds an import ends red without it; decided by the cutter (C21) | deriving once, in the documents' phase |
| [D8](#d8) | D73 records the record; D21's sentence and D62's list of siblings are amended, and the README, the principles and the architecture say it | D21 named the numbers' home and D62 the siblings, and both would read false; decided by the cutter (C22) | leaving D21 and D62 as they stand |

### D1

`isekai/foundation/producers.py`, whole:

```python
"""The stage record: each stage a run passes through, declared once.

A row names a stage's key, the folder its artifacts sit in, whether that folder is
under `photo/` or under a flow, the verb that runs it and the attempts it may spend.
`names.py` and `failures.py` read their tables from it, and `run.py` re-exports both
names (D62).

Imports nothing of `isekai`: stdlib only, and on `python -m isekai`'s import graph.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Producer:
    """One stage: its key, its folder, where the folder sits, its verb and its budget.

    The key is the budget's key and the `stage` field of a failure record on disk, so
    it never changes. A budget of None is a stage with no attempt to spend.
    """

    key: str
    folder: str
    scope: Literal["photo", "flow"]
    verb: str
    budget: int | None


# What each stage may spend before it costs a person's attention instead. Reading
# and sorting are cheap and flaky, so they get three; assembling and rendering get
# one, because a render that has failed once should be looked at rather than paid
# for again. `review` calls no model and records no failure, so it has no budget.
#
# The two taggers are split on the same axis rather than sharing a number.
# `tags` is a hosted model over HTTP, so it is flaky in exactly the way `caption`
# is and gets its three. `wd14` is a local pass over a
# digest-verified graph, and what can still fail there is **this photograph's own
# bytes** -- a header no decoder can read. That is permanent by construction, so
# one attempt is the whole budget, exactly as `assemble` and `render` are one.
#
# The two file conditions that would fail identically for every input -- an
# absent model, bytes that disagree with the pin -- are deliberately **not**
# counted here. They are conditions about this build rather than about a
# photograph, so the tagger is opened before the stage's `try` and refuses the
# batch once instead of writing one error record per input for a single fix.
#
# **`sheet` is one for `wd14`'s reason.** It reached a hosted model once and had
# three; it is now a dictionary lookup over an artifact already on disk, so there
# is no transient failure left for a second attempt to catch -- which is exactly
# what the `wd14` row already records for the other local producer. The stage
# records every failure as permanent, so a second attempt waits on a deletion.
#
# In the order a run passes through the stages.
PRODUCERS: tuple[Producer, ...] = (
    Producer("caption", "captions", "photo", "caption", 3),
    Producer("wd14", "wd14", "photo", "tag", 1),
    Producer("tags", "tags", "photo", "tag", 3),
    Producer("sheet", "sheets", "flow", "sheet", 1),
    Producer("review", "review", "flow", "review", None),
    Producer("assemble", "prompts", "flow", "generate", 1),
    Producer("render", "outputs", "flow", "generate", 1),
)
```

### D2

In `isekai/foundation/run.py`:

- the import goes between those of `names` and `refusal`: `from isekai.foundation.producers import PRODUCERS, Producer`;
- `__all__` gains `"PRODUCERS"` between `"PHOTOGRAPH_VERBS"` and `"PROMPTS"`, and `"Producer"` between `"Kind"` and `"RenderRef"`;
- the docstring's sentence on the siblings, wrapped to the docstring's width, reads: `The siblings `names.py`, `rundir.py`, `layout.py`, `failures.py` and `producers.py` hold the identity and the names, the run and its frame, the numbering and the edit files, the failure budgets, and the stage record.`

### D3

In `isekai/foundation/failures.py`, the import goes between those of `names` and `refusal`, and the comment and the `BUDGETS` literal become:

```python
# What each stage may spend, read from the record (`producers.py` says why each
# number is what it is). A missing entry is not a missing feature, it is a crash:
# `BUDGETS[stage]` below is a bare lookup, and `across()` and `main()` both catch
# only `Refusal`, so an unlisted stage name escapes as a raw traceback.
BUDGETS: Mapping[str, int] = {
    key: budget
    for key, budget in ((producer.key, producer.budget) for producer in PRODUCERS)
    if budget is not None
}
```

The comprehension narrows a name, `budget`, and not an attribute, so the typecheck needs no cast. This block replaces the old lines 24 to 59, the comment and the literal; `_spent`, `exhausted` and `check_budget` are unchanged and move up.

In `isekai/foundation/names.py`, the import goes before `Refusal`'s: `from isekai.foundation.producers import PRODUCERS`. The comment above the stage names gains one line after its sentence on `approved` and `draft`: `# The folders' words are read from `PRODUCERS`, which declares each stage once.` The assignments from `CAPTIONS = "captions"` to `OUTPUTS = "outputs"` become:

```python
_FOLDER = {producer.key: producer.folder for producer in PRODUCERS}
CAPTIONS = _FOLDER["caption"]
WD14 = _FOLDER["wd14"]
TAGS = _FOLDER["tags"]
PHOTO = "photo"
DESCRIPTION = tuple(
    producer.folder for producer in PRODUCERS if producer.scope == PHOTO
)
# The verbs that write the description, and so name no flow.
PHOTOGRAPH_VERBS = tuple(
    dict.fromkeys(producer.verb for producer in PRODUCERS if producer.scope == PHOTO)
)
SHEETS = _FOLDER["sheet"]
REVIEW = _FOLDER["review"]
PROMPTS = _FOLDER["assemble"]
OUTPUTS = _FOLDER["render"]
```

`SOURCES`, `APPROVED` and `DRAFT` stay as written. Each key of `_FOLDER` is a key of the record, so a lookup by key does not depend on a row's place.

### D4

The first case is written and passes before any line moves, in `tests/test_run_directory.py` after `test_the_rendering_stages_budget_is_one`:

```python
@pytest.mark.spec_exempt(
    "structural: the stage tables hold their literal values and order"
)
def test_the_stage_tables_hold_their_literal_values_and_order() -> None:
    assert list(BUDGETS.items()) == [
        ("caption", 3),
        ("wd14", 1),
        ("tags", 3),
        ("sheet", 1),
        ("assemble", 1),
        ("render", 1),
    ]
    assert DESCRIPTION == ("captions", "wd14", "tags")
    assert PHOTOGRAPH_VERBS == ("caption", "tag")
    assert (CAPTIONS, WD14, TAGS, SHEETS, REVIEW, PROMPTS, OUTPUTS) == (
        "captions",
        "wd14",
        "tags",
        "sheets",
        "review",
        "prompts",
        "outputs",
    )
```

Its imports from `isekai.foundation.run` gain `CAPTIONS`, `PHOTOGRAPH_VERBS`, `SHEETS` and `TAGS`. The record's cases follow it in phase 2, with `PRODUCERS` imported:

```python
@pytest.mark.spec_exempt("structural: the record lists the stages in run order")
def test_the_record_lists_the_stages_in_run_order() -> None:
    rows = [(p.key, p.folder, p.scope, p.verb, p.budget) for p in PRODUCERS]
    assert rows == [
        ("caption", "captions", "photo", "caption", 3),
        ("wd14", "wd14", "photo", "tag", 1),
        ("tags", "tags", "photo", "tag", 3),
        ("sheet", "sheets", "flow", "sheet", 1),
        ("review", "review", "flow", "review", None),
        ("assemble", "prompts", "flow", "generate", 1),
        ("render", "outputs", "flow", "generate", 1),
    ]


@pytest.mark.spec_exempt("structural: the stage tables are read from the record")
def test_the_stage_tables_are_read_from_the_record() -> None:
    photo = [p for p in PRODUCERS if p.scope == PHOTO]
    assert list(BUDGETS.items()) == [
        (p.key, p.budget) for p in PRODUCERS if p.budget is not None
    ]
    assert DESCRIPTION == tuple(p.folder for p in photo)
    assert PHOTOGRAPH_VERBS == tuple(dict.fromkeys(p.verb for p in photo))
    assert [CAPTIONS, WD14, TAGS, SHEETS, REVIEW, PROMPTS, OUTPUTS] == [
        p.folder for p in PRODUCERS
    ]
```

The rows case holds the record before the derive, and the tables case holds that the tables follow it once the derive is in. Neither case alone fails when a row moves a table; the literal case of phase 1 does.

### D5

The opening run is in phase 1, on the lines as they stand, and the closing run is in phase 3, on the lines the derive gives. The tool is run one range at a time, on `tests/test_run_directory.py` alone, as `FN-2` is.

| function | opening lines of `failures.py` | closing lines |
|---|---|---|
| `_spent` | 163-167 | 137-141 |
| `exhausted` | 172 | 146 |
| `check_budget` | 184-200 | 158-174 |

The new block of [D3](#d3) ends on line 33 where the old literal ended on line 59, and the import adds a line before it, so each closing line is its opening line less 26. A rescue re-fits them if the module's length differs.

### D6

`tests/mutants.json`, the entry `FN-1`, becomes:

```json
  {
    "finding": "FN-1",
    "path": "isekai/foundation/producers.py",
    "find": "    Producer(\"wd14\", \"wd14\", \"photo\", \"tag\", 1),",
    "replace": "    Producer(\"wd14\", \"wd14\", \"photo\", \"tag\", None),",
    "tests": ["tests/test_run_directory.py"],
    "why": "the wd14 stage has no budget entry"
  },
```

The literal case of phase 1 and the budget cases that name `wd14` kill it. `FN-2` and `FN-6` keep their paths and text.

### D7

The Files row, after the `names.py` row of `isekai/foundation/README.md`:

```
| `producers.py` | the stage record: a frozen `Producer` for each stage a run passes through, in `PRODUCERS`, with its key, folder, scope, verb and budget; it imports nothing of `isekai` |
```

The *Imported by* row is typed with its file's name alone, `` | `producers.py` | | | ``, after the `names.py` row; `uv run python -m tools.derive_imported_by` writes the rest. Once `run.py` imports the record the row names `run.py`; once `failures.py` and `names.py` do, it names `failures.py`, `names.py` and `run.py`. No other derived row moves, for the record imports no `refusal.py`.

### D8

`docs/decisions.md`, after D72 and before `## Infrastructure`:

```
### D73 · A stage is declared once, in isekai/foundation/producers.py

**`isekai/foundation/producers.py` declares each stage a run passes through as a frozen `Producer(key, folder, scope, verb, budget)`, in `PRODUCERS`, in the order a run passes them: caption, wd14, tags, sheet, review, assemble, render. `BUDGETS` of `failures.py`, and `DESCRIPTION`, `PHOTOGRAPH_VERBS` and the stage folders' words of `names.py`, are read from it, and `run.py` re-exports `Producer` and `PRODUCERS`. The module imports nothing of `isekai`.**

- **Why:** a stage was spelled in several literals that no test held to agree, and a new stage edited each of them. One row says what a stage is, and a table that names it is read from the row. The key is the budget's key and the `stage` of a failure record on disk, so it never changes.
- **Accepts:** the tables above the foundation, the sequence inside a stage, the pipeline's own `STAGE` constants and the hub cell's `Stage` stay as they are, and `review` has a row with no budget. Reopen when the interface's tables are read from the record.
- **Made by:** `0183`.
```

D21's last sentence becomes `The numbers are the `budget` of each row of `PRODUCERS` in `producers.py`, read as `BUDGETS` of `failures.py` through `run.py`.` and its *Made by* gains `0183`. D62's bold sentence names `names.py`, `rundir.py`, `layout.py`, `failures.py` and `producers.py`, and its *Made by* gains `0183`.

In `isekai/foundation/README.md` the opening lines become:

```
The types every other group is built on, and the record that declares a stage. Nothing here knows about an
endpoint or a score; everything here is imported by something that does.
```

The `names.py` row reads `a run's id, the names of its layout, read from the stage record, and the draft's label`; in the `failures.py` row `the budgets` reads `the budgets, read from the stage record`. In `docs/principles.md` and `ARCHITECTURE.md` the foundation's bullet reads `…the command text a refusal prints, the stage record, and the library's collection names and its session records' read side.`

## Tests

The change adds unit cases and removes none, and adds no end-to-end run. A table's value is a unit of the foundation (`T1`), and the cases sit in `tests/test_run_directory.py` beside the budgets' own (`T2`).

| layer | adds | removes | the command that counts them once built |
|---|---|---|---|
| unit | the literal-value case, the rows case and the tables-from-the-record case of [D4](#d4) | none | `git grep -c -e "^def test_the_stage_tables_" -e "^def test_the_record_lists_" -- tests/test_run_directory.py` |
| end-to-end | none, on no engine | none | `git grep -l -F "isekai.foundation.producers" -- tests/e2e` |
| mutants | the entry `FN-1` of `tests/mutants.json`, anchored on the record's wd14 row | none | `git grep -c -F "isekai/foundation/producers.py" -- tests/mutants.json` |

No test is deleted or merged, so the table of `T5` is empty. Each case is marked `spec_exempt("structural: …")`: `skip_specs` adds no scenario, and no scenario states a table's value.

## Equivalent mutants

None at the cut. A survivor in a table's value is killed by a further assertion in the literal case of [D4](#d4), and one in the retry rule or the refusal's words by a new case beside the budget's own, bound to `run-directory:budget:at-budget-the-stage-refuses`, with no existing assertion changed. One that no assertion can kill is named here, with its reason.

## Dependencies

None.

## Risks / Trade-offs

- A row's edit now moves a table at once, and the literal case fails on it: that is its job, and the cost of a new stage is the row and the case's literals.
- `DESCRIPTION` and `PHOTOGRAPH_VERBS` become `tuple[str, ...]` where they were tuples of fixed length; the readers iterate or test membership, and a test slices `DESCRIPTION[:2]`.
- `0182-the-render-guard`, which this change follows, edits the `library.py` rows of the foundation README and D72's *Accepts*. This change edits other lines of both files and names its rows by text, not by number.
- The ranges of [D5](#d5) hold only while `failures.py` is as this design reads it; a change that edits it first makes the opening run fail at once, not silently.

## Verdict

Feasible: the record imports nothing, the tables keep their names, values and order, and the cases hold them before and after. Ready to build.
