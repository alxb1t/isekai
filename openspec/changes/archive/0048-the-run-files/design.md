# Design — 0048 the run files

How a run file is checked for its kind, how a render's record is named, how the sheet records its failures, and how
`sheet` names a superseded tag list. **Verdict: feasible** — each a few lines in one module, each held by a test.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`69bfd67`):

- **`isekai/foundation/artifacts.py`:** `read` (`:358-387`) checks the schema block's `version` and never its `name`,
  as its docstring (`:363`) and `require`'s (`:399`) say. `Artifact` holds `name` and `version` (`:303-315`); every
  kind is at version 1, and `DRAFT_FILE` and `APPROVED_FILE` share the name `review` (`:326`).
- **The frame:** `Frame` (`artifacts.py:172-177`) requires `id`; `open_run` writes `"id": identifier`
  (`isekai/foundation/run.py:380`). Every `Run` takes its id from its directory's name.
- **`isekai/foundation/run.py`:** `ARTIFACT` (`:136`) reads any lowercase label; the only labels written are `draft`
  and `approved`. The `BUDGETS` comment (`:146-174`) says the sheet records no failure. `record_failure` (`:503`),
  `check_budget` (`:554`) and `refusal_for` (`:608`) are the recorded-failure path `caption` and the taggers use.
- **`isekai/pipeline/generate.py`:** the render's record is `directory / f"{seed}.json"` (`:510`), written before the
  image (`:529`). No code reads a record; `rendered_seeds` lists the images.
- **`isekai/pipeline/sheet.py`:** `sheet` returns `None` when a sheet exists and no new version is asked
  (`:122-123`). The untagged branch checks the budget (`:127`), where nothing can fail.
- **The sheet's refusals:** `_from_tag_list` refuses an absent list (`:164`), checks the budget (`:170`), then reads
  the list (`:173`) and its entries (`:185`); `validate` (`:137`) refuses a tag outside the vocabulary. None is
  recorded. The producer's `from` is the list's number (`:198`).
- **`isekai/interface/cli.py`:** `sheet_flow` (`:533-549`) hands `sheet`'s path to `_say` (`:632-637`), which prints
  "sheet is already complete" for `None`. `approve_flow` (`:560-564`) prints each warning as `warning: …` on stderr.
- **Tests:** `tests/test_generate.py:1293` and `:1624` name the record `42.json`, and `tests/test_resume.py:642`
  writes a decoy `42.json`. `tests/test_sheet_stage.py:155-174` asserts a damaged list's refusal starts with
  `001.json: `; `tests/stages.py:149-183` returns `sheet`'s path to every sheet test.
- **A read-only prototype** of the kind check and the rename turned no other test red.

## Goals / Non-Goals

**Goals:** a file of another kind is refused; no render record reads as a version; every sheet failure is recorded;
an out-of-date kept sheet is named.

**Non-Goals:** a warning for a re-pinned vocabulary; a newer sheet reaching an approved flow's review; `show` listing
failure records; renaming an old run's records.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `read` refuses a schema `name` other than the kind's, before the version | a copied file is read as whatever its place implies; the kind is the first thing a file says | checking after the version, which calls a sheet a caption from a newer build |
| [D2](#d2) | `Frame`'s docstring says `id` is the id at creation and the directory's name is the run's id | nothing reads it; after a rename it is a true record | dropping `id`, which changes every frame for no reader |
| [D3](#d3) | the record is `<seed>.render.json`; `ARTIFACT`'s label is `draft` or `approved` | `123.render.json` still matches a free label; `draft` and `approved` are the only labels written | the rename alone; a guard that nothing lists `outputs/` |
| [D4](#d4) | the sheet records a damaged tag list and a tag outside the vocabulary as permanent, through `refusal_for`; an absent list records nothing; the untagged branch checks no budget | the failure requirement demands the record; the stage is deterministic ([D21](../../../docs/decisions.md#d21--retries-follow-what-can-fail)) | dropping the budget, which needs an exemption like review's |
| [D5](#d5) | `sheet` returns its path and its warnings, as `approve` does; a kept sheet filled from a list below the flow's latest warns | the silent spot is "already complete"; the rule is the stage's | a warning in `show`, `review` or `generate` |

### D1

**The kind.** In `read`, after the schema block is an object: `schema.get("name")` other than `kind.name` refuses
`<file>: declares kind '<name>' and this build reads it as '<kind>'; <remedy>`, with no "upgrade isekai" — a kind is
not a newer build's. The version check follows, unchanged. The docstrings of `read` and `require` say both are
checked. A draft read as an approval passes: they are one kind.

### D2

**The frame's `id`.** `Frame`'s docstring, before → after:

```
The run's frame: what the run is, written once when it is created.
→
The run's frame, written once when the run is created. `id` is the id it was created with; the directory's name
is the run's id, and a rename leaves `id` as it was.
```

### D3

**The record's name.** `provenance = directory / f"{seed}.render.json"`. `ARTIFACT` becomes
`^(?P<version>\d{3})(?:\.(?P<label>draft|approved))?\.json$`, its comment naming `draft` and `approved`. `RENDER_FILE` stays
version 1: a filename is not a key ([D32](../../../docs/decisions.md#d32--a-run-files-version-moves-only-when-an-old-file-could-be-misread)).
An old run's `<seed>.json` stays, read by nothing.

### D4

**The sheet's failures.** In `sheet.py`, the tagged branch's reads, entry checks and `validate` run inside one guard
after `check_budget`. A `Refusal` there writes `record_failure(directory, version, "permanent", {"stage": "sheet",
"detail": <its message>})` and raises `refusal_for` with the `sheets` area and the `sheet` verb — naming the record,
its deletion and the command to run. The absent-list refusal stays before the guard. The untagged branch loses its
`check_budget`. The `BUDGETS` comment says the sheet records every failure as permanent.

```
tag list absent ──▶ refuse, name `tag`; no record
       │ present
       ▼
check_budget ──▶ a record exists ──▶ refuse, name it
       │ none
       ▼
read · entries · validate ──▶ refused ──▶ record permanent ──▶ refuse, name record + deletion
       │ ok
       ▼
write the sheet
```

### D5

**The warning.** `sheet` returns `(path, warnings)`. On the kept path of a tagged flow it reads the latest sheet with
`read`; a refusal there, a producer without an integer `from`, or a `from` at the latest `wd14/` number gives no
warning. Otherwise one warning: `<run>/<flow>: sheet 001 was filled from wd14/001.json, and wd14/002.json is newer;
run \`python -m isekai sheet --flow <flow> --new-version <run>\``. `sheet_flow` prints each as `approve_flow` does,
then calls `_say`. `tests/stages.py`'s `sheet` returns the path alone; the warning's tests call the stage.

## Dependencies

None.

## Risks / Trade-offs

- **A file with an unknown label disappears from `show`** → the stages write none; `op·show-skips` names any file
  `show` does not read.
- **A damaged tag list now costs a deletion** → the refusal names the record and the command; the stage is free.
- **An old run's `123.json` still reads as version 123** → nothing lists `outputs/`; the name is fixed for new runs.

## Verdict

**feasible** — a comparison, a name, a guard and a warning, each in one module, each held by a test.
