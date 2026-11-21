# The review base — design

Make `review` a package entered by its front door, with the draft's records and the token budget in modules beside it. Verdict: feasible, in the phases of [tasks](tasks.md); every importer reads its names through the front door, so a moved byte fails a test.

## Context

`isekai/pipeline/review.py` holds stage ③: `review`, `revise` and `draft_from` write a draft; `approve` turns one into an approval; `cancel` and `discard` take one back. Beside them sit the readers and writers all three share, and the token budget the page shows while a sheet is edited.

Importers read the stage by its module's name: `isekai/interface/drafting.py`, `isekai/interface/ui/app.py`, `isekai/interface/ui/library.py`, `isekai/interface/ui/routes/images.py`, `isekai/interface/ui/routes/reviewing.py`, `isekai/interface/ui/shapes.py`, `isekai/interface/verbs/drafts.py` and `isekai/interface/verbs/runner.py`, and many tests. A test patches `create`, which `_publish` reads, and another patches `write`, which `_write_draft` and `save_draft` read.

```
before                               after
pipeline/review.py                   pipeline/review/
  drafts · approval · cancel           __init__.py ── front door: drafts, approval, cancel, Status,
  records · shared helpers                              and every name the module held
  token budget                         records.py  ── draft read/write, _publish, shared helpers
                                       budget.py   ── the token budget
```

The deriver of `ui/src/wire.ts` reads a package as its `__init__.py` and names a type by its module's stem, so `Status` defined in the front door is still `ReviewStatus`.

## Goals / Non-Goals

- Goal: `review.py` is `review/__init__.py`, and each name it held is importable from `isekai.pipeline.review`.
- Goal: `records.py` and `budget.py` hold the names of [D2](#d2) and [D3](#d3), unchanged but for `_write_draft`'s parameters.
- Goal: a test that patches a name of the stage patches it on the module that reads it.
- Goal: the long-file and long-function rows are keyed to the front door, and `_write_draft` is no wide function.
- Non-goal: the parts. The drafts, the approval and the cancel stay in the front door.
- Non-goal: a message, a record, a scenario or a spec delta; any file under `ui/`, `tools/` or `evaluation/`; `ui/src/wire.ts`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `review.py` becomes `review/__init__.py`; the front door re-exports every name and defines `Status` | importers and tests import the stage by one name; the deriver names the page's type by the module that defines `Status` | a front door that moves `Status`, which renames `ReviewStatus` on the page |
| [D2](#d2) | `records.py` holds the draft's read and write, `_publish` and the helpers the parts share | the parts the next version cuts import it and no part upward | the helpers left in the front door, which the parts would import back |
| [D3](#d3) | `budget.py` holds the token budget | it reads a flow and a schema and no record; the page reads it apart from the drafts | leaving it with `approve`, its one caller in the stage |
| [D4](#d4) | `_write_draft` takes `renders`, `version` and `image` by keyword | the ratchet counts positional parameters, and a keyword-only one is not counted, so its wide row goes | a dataclass for the arguments, a change to every caller's shape |
| [D5](#d5) | The tests that patch import `isekai.pipeline.review.records`; the patched row is renamed | a patch must name the module that reads the name, and the ratchet refuses a new row | patching the front door, which `_publish` and `_write_draft` do not read |
| [D6](#d6) | Phases keep the brief's order, but the patches and the ratchet rows land in the records' phase | the move turns both red until they change, and a phase ends green | a phase of its own for each, red at its end |
| [D7](#d7) | A name the front door no longer reads is re-bound `X as X`; one it reads is imported plain | ruff reads `X as X` as a re-export, so F401 does not name it | an `__all__`, which no module of the stage declares |
| [D8](#d8) | The standing mutants of `review.py` follow their text | a mutant is found by its path and its exact text | a new mutant, or a stale entry |
| [D9](#d9) | A decision, D75, says what a stage package's front door holds and where a patch goes | A7: a decision in force is edited where it lives | leaving it in this design, which is frozen at the archive |

### D1

`git mv isekai/pipeline/review.py isekai/pipeline/review/__init__.py` keeps the file's history. The module docstring, `STAGE`'s consumers and every name stay. D55 already says a stage may be a package whose `__init__.py` is its front door.

### D2

`records.py` imports no part and not the front door, so the front door imports it and the reverse would close a cycle. The files it names are the run's, by `isekai.foundation`.

```
records.py   STAGE · _first_image · _draft_command · _approval · _write_draft · save_draft ·
             _publish · _again · _recopy · _differs · same_fields · draft_image · came_from ·
             is_copy · copied_renders
```

Each is read by more than one part, by a caller outside the stage, or is a writer of a record: `_write_draft`, `save_draft` and `_publish`. `save_draft` is the one owner of a draft's update. `_resheet`, `_refuse_unchanged`, `_copy_approval` and `_NOT_COPIED` serve `approve` alone and stay.

### D3

`ENCODER_WINDOW`, `estimate_tokens`, `TokenBudget` and `token_budget` move with the comment of `ENCODER_WINDOW`. `approve` reads three of them and the front door re-exports `TokenBudget`, which `isekai/interface/ui/routes/reviewing.py` imports.

### D4

After the move `_write_draft(run, flow, came_from, source, carried, sheet_version, *, renders=None, version=None, image=None)`. Its callers are `review` (the approved branch passes `renders`), `revise`, `draft_from` and `cancel`. Each names the keyword; no value changes.

### D5

`monkeypatch.setattr(<module>, "create", …)` and `"write"` change the name in the module they are given. After the move `records.py` reads both as globals and the front door reads neither, so each test imports `isekai.pipeline.review.records as review_records` and patches through it. The `PATCHED_MODULES` row `isekai.pipeline.review` becomes `isekai.pipeline.review.records`, its number as it stands.

### D6

The package phase is the move and every row, path and table that names the old file. The budget phase moves the smaller piece first, to prove the form. The records phase also holds the keyword-only parameters, the patching tests and the ratchet rows they turn red; the last phase is the decision and the prose.

### D7

The front door reads `STAGE`, `_approval`, `_write_draft`, `_publish`, `_again`, `_recopy`, `_differs`, `same_fields`, `draft_image`, `came_from`, `is_copy`, `copied_renders`, `_first_image`, `_draft_command`, `ENCODER_WINDOW`, `estimate_tokens` and `token_budget`: plain. It reads `save_draft` and `TokenBudget` nowhere: `X as X`, one statement each, as `_holds_render` is.

### D8

| finding | text of | path after |
|---|---|---|
| PB-14 | `discard` | `isekai/pipeline/review/__init__.py` |
| PB-5 | `draft_from` | `isekai/pipeline/review/__init__.py` |
| PB-2 | `approve` | `isekai/pipeline/review/__init__.py` |
| PB-1a, PB-1b | `token_budget` | `isekai/pipeline/review/budget.py` |
| PB-3a, PB-3b | `_publish` | `isekai/pipeline/review/records.py` |

The package phase sets each to the front door; the budget phase and the records phase move the entries whose text left it.

### D9

D75 is the next free id at the cut, and `mf-integrate` renumbers it where another version took it first. The next version amends its *Accepts*. Its text, in the shape of D74:

```
### D75 · review is a package entered by its front door, and a patch names the module that reads the name

**`isekai/pipeline/review/` is the review stage. `__init__.py` is its front door: it re-exports every name the module held and defines `Status`. `records.py` holds the draft's read and write — `save_draft`, `_write_draft` and `_publish` — with the helpers the stage's parts share, and `budget.py` the token budget. A test patches a name of the stage on the module that reads it, `isekai.pipeline.review.records` for `create` and `write`.**

- **Why:** a patch of a name in a module that no longer reads it changes nothing, and the wire's deriver names a type by its module, so a moved `Status` renames the page's `ReviewStatus`. The front door keeps every importer and every test import as it was.
- **Accepts:** the drafts, the approval and the cancel stay in the front door, `approve` stays a listed long function, `draft_across` a listed wide one, and the front door a listed long file. Reopen when the parts leave it.
- **Made by:** `0198`.
```

## Names

| group | names | read outside the stage |
|---|---|---|
| front door | `Status`, `state`, `Cancelled`, `Revision`, `review`, `revise`, `draft_from`, `drafting_sheet`, `drafting_approval`, `refuse_drafts`, `refuse_revision`, `waiting_edit`, `discard`, `cancellable`, `cancel`, `approve` | the importers above |
| records | the list of [D2](#d2) | `save_draft`: `ui/app.py`, tests · `came_from`: `ui/library.py`, `ui/routes/reviewing.py` · `draft_image`: `ui/routes/reviewing.py` |
| budget | `ENCODER_WINDOW`, `estimate_tokens`, `TokenBudget`, `token_budget` | `ui/routes/images.py`, `ui/routes/reviewing.py`, tests |

## Tests

No test is added, changed in an assertion or removed, and no end-to-end run is added. `tests/test_review.py` and `tests/test_ui_api.py` change an import and each use of its alias; `tests/test_ratchets.py`, `tests/test_artifact_bytes.py` and `tests/mutants.json` change a key or a path; `tests/test_docs.py` and `tests/test_derive_wire.py` change nothing and hold the derived tables and `ui/src/wire.ts`.

| measure | command | before | after |
|---|---|---|---|
| tests in the review file | `git grep -c -e "^def test_" -- tests/test_review.py` | `tests/test_review.py:108` | `tests/test_review.py:108` |
| tests in the UI api file | `git grep -c -e "^def test_" -- tests/test_ui_api.py` | `tests/test_ui_api.py:115` | `tests/test_ui_api.py:115` |

The proof is the suite, the standing mutants, `tests/test_ratchets.py`, which holds that the front door is still listed and each patched name is still read, and `tests/test_derive_wire.py`, which holds `ui/src/wire.ts`. No test is deleted or merged, so no `I16` table is due.

## Dependencies

None.

## Risks / Trade-offs

- `records.py` imports nothing of the front door. A name moved there that reads one back would close a cycle, which `tests/test_layers.py` finds.
- The front door must stay over the long-file ceiling after the moves; the row would be red if it did not. The records phase checks it with a **HALT CHECK**.
- A moved dataclass changes its `__module__`. `TokenBudget` is read by `isekai/interface/ui/routes/reviewing.py` for its fields, and `shapes.py` names none.
- A patch the front door no longer reaches fails with `AttributeError`, not silently; the tests that patch are the ones that change.
- `_write_draft` keeps the order of its parameters. A caller that passed one positionally and was missed fails with `TypeError`, in a test that reaches it.

## Verdict

Feasible. Each phase ends with its tests passing and the front door importing.
