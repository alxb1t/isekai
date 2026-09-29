---
version: v0.31
backlog: [0028·frame-id, 0028·kind-name, 0028·sidecar-name, 0030·sheet-budget]
---

# 0048 — the run files

A run's files say what they are and when they are out of date. `read` refuses a file whose schema names another
kind; a render's record takes a name no version listing reads; the sheet records its failures, so its budget binds;
`sheet` names a newer tag list than the one its kept sheet was filled from. **The feature is the last.**

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the kind check, the record's name, the sheet's failures, the warning |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `run-directory`, `sheet` |

## Why

**A file is read as whatever its place implies.** `read` checks the declared version and never the kind, so a sheet
copied over a caption is read as a caption.

**A render's record looks like a version.** `outputs/NNN/123.json` matches the pattern every version listing uses.

**The sheet's budget never binds.** The stage checks it and records nothing, against the requirement that every
failure is recorded.

**`sheet` calls an out-of-date sheet complete.** After `tag --new-version`, a kept sheet was filled from an older
tag list, and nothing says so.

## What Changes

- **`read` refuses a file whose schema names another kind**, naming both, before it checks the version
  ([D1](design.md#d1)).
- **The frame's `id` is documented as the id at creation**; the directory's name is the run's id
  ([D2](design.md#d2)).
- **A render's record is `<seed>.render.json`, and `ARTIFACT` reads only the `draft` and `approved` labels**
  ([D3](design.md#d3)).
- **The sheet records a damaged tag list and a tag outside the vocabulary as permanent failures**; an absent tag
  list is refused with no record ([D4](design.md#d4)).
- **`sheet` warns when it keeps a sheet filled from a tag list older than the flow's latest** ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `run-directory`: ADDED *A run file is read only as the kind it declares*.
- `run-directory`: MODIFIED *Every "is this done?" test is a directory listing* — gains a render's record, never read
  as a version.
- `run-directory`: MODIFIED *A failure is recorded as an attempt, never as a completion* — gains the sheet's permanent
  failures, and an absent tag list recording nothing.
- `sheet`: ADDED *A kept sheet filled from a superseded tag list is named*.

## Impact

- **Files:** `isekai/foundation/artifacts.py`, `isekai/foundation/run.py`, `isekai/pipeline/generate.py`,
  `isekai/pipeline/sheet.py`, `isekai/interface/cli.py`, and their tests.
- **Behaviour:** a file of another kind is refused; a new render's record has a new name; a damaged tag list leaves
  a record the operator deletes; `sheet` may print a warning.
- **Formats:** no run file kind or manifest version moves. An old run's `<seed>.json` stays, read by nothing.
- **Dependencies:** none.
- **Spend:** none.

## Not in this change

- **A warning for a re-pinned vocabulary** — `approve` already refuses a tag the new vocabulary lacks.
- **A newer sheet reaching an approved flow's review** — `op·review-newer-sheet`, with the UI work.
- **`show` listing failure records** — `op·show-skips`, the next change to `run_view.py`.
- **Renaming an old run's records.**
