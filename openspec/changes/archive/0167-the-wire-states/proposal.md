---
bump: patch
version: 0.87.23
---

# The wire states

A cell's stage, a job's state and a file's state get a name where the server writes them, and `shapes.py` reads it.

Reading map: [design](design.md) holds where each name lives and what stays a `str`, [tasks](tasks.md) its phases.

## Why

`shapes.py` declares a cell's stage, a job's state and a file's state as `str`, and [D66](../../../docs/decisions.md#d66--the-refusals-are-classes-and-the-streams-events-have-a-table-of-their-own) accepts that until the page's types are derived. The walker in `tests/test_ui_shapes.py` reads a `Literal` by its values' type names, never the values, so an inline `Literal` in `shapes.py` would be a claim no test holds. `ty` holds a literal written to a `Literal` field, so a name at the code that writes the set is held by the gate.

The derived page types read these declarations next. Left as `str`, each word the page compares would be typed as any string.

## What Changes

- `isekai/interface/ui/library.py` gains `Stage`, the words a cell's stage takes, and `Cell.stage` reads it.
- `isekai/interface/ui/jobs.py` gains `State`, the words a job's state takes, and `_Job.state` reads it.
- `isekai/pipeline/importing.py` gains `Upload`, every state a file is published in, beside `State`. A new `_record` builds a file's record from a state typed by `Upload`, and `Reader._set` takes the state apart from its other fields.
- `isekai/interface/ui/shapes.py` reads these names for `HubCell.stage`, `Job.state` and `FileState.state`, and keys `Snapshot.jobs` by `jobs.Kind`.
- `docs/decisions.md` narrows D66's *Accepts* line to what stays `str`; the `ui/shapes.py` row of `isekai/interface/README.md` says which value sets are named; the `importing.py` row of `isekai/pipeline/README.md` is derived again.

Every behaviour is unchanged: the records, the keys' order and the words are the ones the code wrote before.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement fits, so the change carries `skip_specs: true` and `specs/.gitkeep`.

## Impact

- Code: `isekai/interface/ui/library.py`, `isekai/interface/ui/jobs.py`, `isekai/interface/ui/shapes.py`, `isekai/pipeline/importing.py`.
- Documents: `docs/decisions.md`, `isekai/interface/README.md`, `isekai/pipeline/README.md`.
- Tests, run and none edited: `tests/test_ui_shapes.py`, `tests/test_ui_library.py`, `tests/test_ui_jobs.py`, `tests/test_ui_api.py`, `tests/test_importing.py`, `tests/test_layers.py`, `tests/test_docs.py` and `tests/test_spec_prose.py`. `uv run ty check` in the gate is the check on the new names.
- Nothing of the record or the page changes, and no format version moves.

## Not in this change

- The billing volume's state, a session's outcome, and a cell event's stage and state: each stays `str` ([D4](design.md#d4)).
- A `TypedDict` for the importer's record, and a tuple in `shapes.py`.
- A record entry, or any file under `ui/src/`.
- The tool that derives the page's types from `shapes.py`, and the page's use of them: each comes when the page's types are derived.
