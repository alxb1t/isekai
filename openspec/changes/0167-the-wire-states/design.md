# The wire states — design

A cell's stage, a job's state and a file's state are named where the server writes them, and `shapes.py` reads the names. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`shapes.py` declares a cell's stage, a job's state and a file's state as `str`. Each is written by literals alone, so the checker can hold every word if the field that takes it is a `Literal`.

```
 value set        written at                         field today            field after
 cell stage       library.py stage()                 Cell.stage: str|None   Cell.stage: Stage|None
 job state        jobs.py, the job's own methods     _Job.state: str        _Job.state: State
 file state       importing.py Reader                dict[str, Any] record  _set's state: Upload
 snapshot's jobs  stream.py, over KINDS              dict[str, Job|None]    dict[jobs.Kind, Job|None]
```

Facts the design stands on, each read at the cut:

- A cell's stage is `assigned`, `tagged`, `sheet`, `draft`, `approved`, `rendered` or `unreadable`, each written by a literal, a conditional `x if c else y` of literals, or `None` (`isekai/interface/ui/library.py:652-703`).
- A job's state is `running`, `failed`, `stopped` or `done`, each written by a literal or a conditional of literals (`isekai/interface/ui/jobs.py:193`, `isekai/interface/ui/jobs.py:525-582`).
- `importing.State` names `ready`, `converted`, `not cleaned` and `skipped`, and types `Staged.state`. `waiting`, `converting` and `refused` are literals in dicts of type `dict[str, Any]` (`isekai/pipeline/importing.py:77`, `isekai/pipeline/importing.py:193-325`).
- `ty` holds a literal and a conditional of literals written to a `Literal` field; `Staged(…, "converted" if converted else "ready")` already passes it (`isekai/pipeline/importing.py:162`).
- `ty` 0.0.64 accepts `Literal[State, "waiting", "converting", "refused"]` and flattens it to its members; a word outside them is refused. A probe at the cut ran it.
- The walker reads a `Literal` by its values' type names, a union as `None` and one other arm, and a `dict` by its value type alone, so the new names pass every recorded sample (`tests/test_ui_shapes.py:85-126`).
- `shapes.py` already reaches `library.py` and `importing.py` through `jobs.py`; no module imports `shapes.py`, so no cycle forms, and one *Imported by* row moves: the `importing.py` row of `isekai/pipeline/README.md` (`isekai/interface/ui/jobs.py:50`, `isekai/interface/ui/library.py:69`).
- `library.py` and `importing.py` are listed long files, which may grow; `jobs.py` and `shapes.py` stay under 800 lines (`tests/test_ratchets.py:455-456`).

## Goals / Non-Goals

Goals:

- A cell's stage, a job's state and a file's state each have one name, in the module that writes them, held by `ty` at each write.
- `shapes.py` restates none of them.
- Behaviour is unchanged: the same words, the same records, the same keys in the same order.

Non-goals:

- A set the checker cannot hold, or no code of the server writes from a literal ([D4](#d4)).
- A `TypedDict` for the importer's record.
- The page's types, and the tool that derives them.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A value set is named in the module that writes it, and `shapes.py` imports the name | a restated copy is a second fact that needs a test to hold it equal | an inline `Literal` in `shapes.py` |
| [D2](#d2) | `library.Stage` and `jobs.State` are `Literal` aliases beside the field they type | each write is a literal or a conditional of two, which `ty` holds | `str` held by a comment |
| [D3](#d3) | `importing.Upload` is `Literal[State, "waiting", "converting", "refused"]`, and the record's state passes through a typed parameter | the writes sit in untyped dicts, so only a parameter makes `ty` hold them | a `TypedDict` for the record; the alias alone; every word written twice |
| [D4](#d4) | The billing volume's state, a session's outcome and a cell event's stage and state stay `str` | `ty` holds none of their writes: the first two are read from files and a process, the last two are a pod's progress words | a `Literal` no checker holds |
| [D5](#d5) | `Snapshot.jobs` is `dict[jobs.Kind, Job \| None]` | the builder runs over `KINDS`, a tuple of `Kind` | `dict[str, …]` |
| [D6](#d6) | The importer's rewritten lines are pre-flighted by `tools.mutate`, one run a range | `CONTRIBUTING.md` asks it of every rewrite of `isekai/` | no run, because the rewrite is typing |
| [D7](#d7) | D66's *Accepts* line is narrowed in place and no decision is added | the rule is D66's: the wire is declared once, and a name is part of a declaration | a new decision for these aliases |

### D1

`shapes.py` imports `library`, `jobs` and `importing` and writes `library.Stage`, `jobs.State`, `jobs.Kind` and `importing.Upload`. It declares no `Literal` for them. [D63](../../../docs/decisions.md#d63--the-wire-is-declared-in-shapespy-and-held-by-tests) holds the declarations against the record, and a `Literal` of strings passes any recorded `"str"`: only the checker holds the words.

### D2

`Stage` sits above `Cell` in `isekai/interface/ui/library.py`, `State` below `KINDS` in `isekai/interface/ui/jobs.py`:

```python
Stage = Literal[
    "assigned", "tagged", "sheet", "draft", "approved", "rendered", "unreadable"
]
State = Literal["running", "failed", "stopped", "done"]
```

`Cell.stage` becomes `Stage | None` and `_Job.state` becomes `State`. No construction changes: `Cell("rendered" if renders else "approved", …)` and `job.state = "stopped" if slot.stopping else "done"` are conditionals of literals. `REACHED` in `jobs.py` stays an inferred `dict[str, set[str]]`.

### D3

```python
State = Literal["ready", "converted", "not cleaned", "skipped"]
Upload = Literal[State, "waiting", "converting", "refused"]


def _record(name: str, state: Upload, fields: Mapping[str, object]) -> dict[str, Any]:
    return {"file": name, "state": state, **fields}
```

`Reader._set(upload, name, state, fields)` takes the state apart from its other fields, builds the record with `_record` and publishes `{"upload": upload, **record}`. `put` builds its `waiting` record with `_record`. `_run` holds the state and the fields in locals, and calls `_set` after the `finally` that removes the held folder, as it does today.

The rewritten text of the lines of `put`, of `_run`'s body and of `_set` is:

```python
        record = _record(name, "waiting", {})
```

```python
            self._set(upload, name, "refused", {"refusal": refusal})
```

```python
            self._set(upload, name, "converting", {})
            try:
                staged = read(held, self._staging, self._limit)
                state: Upload = staged.state
                fields: Mapping[str, object] = {
                    "name": staged.name,
                    "carries": list(staged.carries),
                    "copy_of": staged.copy_of,
                }
            except Refusal as refused:
                state, fields = "refused", {"refusal": str(refused)}
            except Exception as failed:
                # Anything else, a full disk or a decoder's own error, refuses this
                # file alone: the thread lives on to read the next.
                state, fields = "refused", {"refusal": _failed(name, failed)}
            finally:
                shutil.rmtree(held.parent, ignore_errors=True)
            self._set(upload, name, state, fields)

    def _set(
        self, upload: str, name: str, state: Upload, fields: Mapping[str, object]
    ) -> None:
        """Record and publish `upload`'s `state`, uploaded as `name`."""
        record = _record(name, state, fields)
        with self._lock:
            self._files[upload] = record
        self._publish({"upload": upload, **record})
```

`Mapping` joins the `collections.abc` import of the module. A copy of the module so written passes `ty` at the cut.

Each record is the dict the code built before: the keys `file` and `state` first, then the fields in their order, so `{"file": "a.heic", "state": "converted", "name": …}` is unchanged. `fields` is a `Mapping`, since `ty` refuses a `dict[str, str]` for a `dict[str, object]` parameter. A key of `fields` may be `name`, so the helpers take it as one argument, never `**fields`.

The `waiting`, `converting` and `refused` literals are held at the places that write them. The records stay `dict[str, Any]`, so the test callbacks typed `dict[str, object]` change nothing.

### D4

| set | stays | because |
|---|---|---|
| `BillingVolume.state` | `str` | written into an untyped `dict[str, Any]` in `isekai/interface/ui/billing.py`, and the page only compares it |
| `SessionRecord.outcome`, and the served session's | `str`, `str \| None` | read from a record on disk, and `None` for a session no process holds |
| `CellEvent.stage`, `CellEvent.state` | `str \| None` | a pod's progress line's words, copied; a cell's own stage is `Stage`, a different set |
| `Job.stage`, `JobStage.stage` | `str` | a job's verb, a different set |

D66's *Accepts* line names the first three. The page only compares the first two, and guards the `None` of the cell event where it reads it.

### D5

`KINDS` in `isekai/interface/ui/jobs.py` is `get_args(Kind)`, and `snapshot()` in `isekai/interface/ui/routes/stream.py` builds `{kind: slot(kind) for kind in KINDS}`. The walker ignores a `dict`'s key type, so the new key meets nothing but the declaration.

### D6

`CONTRIBUTING.md` asks `tools.mutate` of lines a change rewrites. Phase 2 rewrites lines of `put`, `_run` and `_set`, and adds `_record`.

A range with no mutant is refused, so a run names the statements that hold one: a call or a return. The annotation edits of the other files hold none.

The opening run, over the lines as they stand, killed each mutant it could reach. `tests/test_importing.py` leaves the `converting` publish alive, and `tests/test_ui_api.py`, which asserts the stream sees `converting`, kills it.

The closing runs are written against the layout phase 2 gives and name the same tests. `UB-14` in `tests/mutants.json` finds text on a `library.py` line this change does not touch, and replays as it did.

### D7

Under [D66](../../../docs/decisions.md#d66--the-refusals-are-classes-and-the-streams-events-have-a-table-of-their-own) the page's types are derived after the declarations. The change adds what D66 accepted as `str` to the declarations, so D66 names what is still `str`, and its *Made by* line names this change.

## Equivalent mutants

None. The opening run over the importer's lines left alive `shutil.rmtree(held.parent, ignore_errors=True)` and its `ignore_errors` flag, which this change does not rewrite: neither is in a range the phase runs.

## Tests

The change adds no test and removes none, so no scenario is bound and the table of removed tests is empty. It runs no end-to-end test. Each count is the output of `git diff --stat main...HEAD -- tests`, which prints nothing.

| layer | added | removed | the check that holds the names |
|---|---|---|---|
| unit | none | none | `uv run ty check`, over `isekai/` and `tests/` |
| shape | none | none | `tests/test_ui_shapes.py`, walking each declaration against the record |
| docs | none | none | `tests/test_docs.py`, re-deriving each *Imported by* table |
| end-to-end | none | none | none |

An existing test whose arrangement `ty` refuses is a halt: the plan is wrong, since no assertion may change.

## Dependencies

None.

## Risks / Trade-offs

- A test builds a `Cell` or a `_Job` with a `str` where `ty` wants a word. The cut read each construction in `isekai/interface/ui/library.py` and `tests/test_ui_library.py` and found literals alone; [1.1](tasks.md) holds the premise that `ty` is green first, and a red run after phase 1 halts the build.
- `_run` binds `state` and `fields` in each branch of its `try`. A branch that left one unbound would raise where the old code could not, and `ty` refuses a possibly unbound name.
- The closing mutation lines are written against the layout phase 2 gives, estimated at the cut from a copy. A line off by one fails at once or holds a neighbour's mutant, and a rescue re-fits the range.
- The page reads `string` for each of these words until its types are derived. That is today's state.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the cell's stage and the job's state, then the file's state, then the documents.
