# The review parts — design

Cut the review stage's drafts, approval and cancel into `drafts.py`, `approval.py` and `cancelling.py` beside the records, shorten `approve`, and give `draft_across` a keyword `seed`, so the stage leaves the ratchet tables. Verdict: feasible, in the phases of [tasks](tasks.md); every importer still reads its names through the front door, so a moved byte fails a test.

## Context

[0198](../0198-the-review-base/design.md) made `isekai/pipeline/review/` a package. Its `records.py` holds the draft's read and write and the helpers the parts share, its `budget.py` the token budget, and its `__init__.py` the front door with the drafts, the approval and the cancel still in it. This version moves each of the three into a module of its own.

Importers and tests read the stage by one name, `isekai.pipeline.review`, and a test patches `create` and `write` on `isekai.pipeline.review.records`. No one outside the stage reads a private name of it.

```
before (after 0198)                    after
review/__init__.py                     review/__init__.py ── front door: Status, state, re-exports
  Status · state                         records.py   ── draft read/write, DISCARD, shared helpers
  drafts · approval · cancel             budget.py    ── the token budget
review/records.py                        drafts.py    ── review, revise, draft_from, refusals
review/budget.py                         approval.py  ── approve and its helpers
                                         cancelling.py── discard, cancel and their helpers

imports:  front door ──▶ parts ──▶ records          approval ──▶ budget
          no part imports another part, nor the front door
```

`approve` is longer than the ceiling for a function, and `draft_across` in `isekai/interface/drafting.py` takes more positional parameters than the ceiling allows. Both are rows of `tests/test_ratchets.py`, as is the front door among the long files.

## Goals / Non-Goals

- Goal: each part is a module that imports `records.py`, and `approval.py` also `budget.py`, and no other part ([D55](../../../docs/decisions.md#d55--a-stage-may-be-a-package)).
- Goal: each name an importer or a test reads is importable from `isekai.pipeline.review`, the one that is defined there, `Status`, still defined there.
- Goal: `approve` is 100 lines or fewer, and `draft_across` is no wide function.
- Goal: `tests/test_ratchets.py` holds no row that names the stage, and no file of the package passes 800 lines.
- Non-goal: the upload session, `Status`, a message, a record, a scenario or a spec delta; any file under `ui/`, `tools/` or `evaluation/`; `ui/src/wire.ts`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `drafts.py`, `approval.py` and `cancelling.py` each import `records.py`; `approval.py` also `budget.py`; the front door imports each part | D55 lets a stage's modules import each other, and a part that imports a part, or the front door, closes a cycle the layer test finds | a part that reads another's helper, which the next move would pull apart |
| [D2](#d2) | Each name goes to the part that reads it, by the [Names](#names) table | one reader per name, so no part reaches into another | splitting a part's helpers across modules |
| [D3](#d3) | `DISCARD` moves to `records.py`; `CANCEL` goes with `_cancelling`; `_DRAFT_AGAIN` with the drafts | the drafts, the approval and the cancel all name the discard command; each of the others has one reader | a copy of `DISCARD` in each part, which each edit would have to keep equal |
| [D4](#d4) | `Status` and `state` stay in the front door | `state` returns `Status`, a part may not import the front door, and the wire's deriver names the page's type by the module that defines `Status` | moving both, which renames `ReviewStatus` on the page |
| [D5](#d5) | `approve` takes its over-window warning from `_window_warnings`, directly above it in `approval.py`; the lines move verbatim | `approve` is past the ceiling, and the warning is one block with one output | splitting the approved body's build, which several lines read as one local |
| [D6](#d6) | `draft_across` takes `seed` after a bare `*`, and `draft_from_image` passes `seed=seed` | the ratchet does not count a keyword-only parameter, and the function has one caller | a dataclass for the arguments |
| [D7](#d7) | The front door re-binds each name it re-exports `X as X`, one statement each, and imports plainly what it reads | ruff reads `X as X` as a re-export, so F401 does not name it ([0198 D7](../0198-the-review-base/design.md#d7)) | an `__all__`, which no module of the stage declares |
| [D8](#d8) | Phases land the approval, the drafts, then the cancel; each phase takes the rows, keys and paths its move turns red | a phase ends green, and the approval leaves the front door well under the file ceiling | one phase of every part, which cannot be checked apart |
| [D9](#d9) | The standing mutants of the front door follow their text | a mutant is found by its path and its exact text | a new mutant, or a stale entry |
| [D10](#d10) | D77 is amended where it lives | A7: a decision in force is edited where it lives | leaving the base's *Accepts* standing over a front door that no longer holds the parts |

### D1

`approval.py` reads `ENCODER_WINDOW`, `estimate_tokens` and `token_budget` from `budget.py`, which imports no part. `records.py` and `budget.py` import neither the front door nor a part. The front door imports each part so each name stays importable; the parts never import it.

### D2

The drafts read approvals through `_approval` and write drafts through `_write_draft`. The cancel reads `_approval`, `_first_image`, `_draft_command`, `_again`, `_write_draft`, `draft_image` and `is_copy`; the approval reads `_again`, `_publish`, `_recopy`, `_differs`, `came_from`, `is_copy`, `same_fields` and `copied_renders`. All are in `records.py`, and no part reads a name another part defines.

### D3

`DISCARD = ("--discard",)` moves with its comment to `records.py`, after `STAGE`. `_refuse_edited` and `_discarding` of the drafts, `_refuse_unchanged` of the approval and `_cancelling` of the cancel read it. `CANCEL = ("--cancel",)` is read by `_cancelling` alone, and `_DRAFT_AGAIN` by the drafts alone; each moves with its comment.

### D4

The front door keeps the module docstring, `Status`, `state` and the imports it reads. Everything else it holds is a re-export.

### D5

The block from `warnings: list[str] = []` through the `if estimate > ENCODER_WINDOW:` append becomes one function, which returns the list:

```
def _window_warnings(
    run: Run, flow: str, fields: Mapping[str, Sequence[str]], schema: Schema,
    definition: Flow | None,
) -> list[str]:
```

`approve` assigns `warnings = _window_warnings(run, flow, fields, schema, definition)` where the block was. The `estimate = (…)` expression, its `else token_budget(fields, schema, definition).total` line and the message keep their text, so the standing mutant `PB-2` finds its line.

The mutation pre-flight of [CONTRIBUTING](../../../CONTRIBUTING.md) runs over `approve` before it is cut, and over `_window_warnings` and `approve` after, one run a range, on `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py` and `tests/test_artifact_bytes.py`. A survivor is killed by a case in `tests/test_review.py`.

### D6

After the move `draft_across(run, target, source, version, vocabulary, field_map, *, seed)`. Its positional parameters are then within the ceiling. Its docstring and call order stay.

### D7

The front door re-exports the names an importer or a test reads, and no private one: `Cancelled`, `Revision`, `approve`, `cancel`, `cancellable`, `discard`, `draft_from`, `drafting_approval`, `drafting_sheet`, `refuse_drafts`, `refuse_revision`, `review`, `revise`, `waiting_edit`, `save_draft`, `came_from`, `draft_image`, `ENCODER_WINDOW`, `estimate_tokens`, `TokenBudget` and `token_budget`. It also keeps `DRAFT`, `current_draft` and `source_copy` of `isekai.foundation.run` and `withdraw` and `_holds_render` of `isekai.foundation.discard`, which tests import through it. `Status` and `state` are defined there. A private name of `records.py` the front door imported in 0198 is dropped: nothing outside the stage reads it.

### D8

The approval goes first: it carries the pre-flight and the long function's and the long file's rows, and leaves the front door under 800 lines. The drafts go second with `draft_across` and the byte writers' key, and the cancel last.

### D9

| finding | text of | path now | path after |
|---|---|---|---|
| PB-2 | `approve` | `isekai/pipeline/review/__init__.py` | `isekai/pipeline/review/approval.py` |
| PB-5 | `draft_from` | `isekai/pipeline/review/__init__.py` | `isekai/pipeline/review/drafts.py` |
| PB-14 | `discard` | `isekai/pipeline/review/__init__.py` | `isekai/pipeline/review/cancelling.py` |

Each `find` and `replace` is unchanged. `PB-2`'s `find` is a line of `_window_warnings`, which stays in `approval.py`.

### D10

D77's rule gains the parts and its *Accepts* changes. Its text after, in place of its rule and *Accepts*:

```
**`isekai/pipeline/review/` is the review stage. `__init__.py` is its front door: it defines `Status` and `state` and re-exports every name an importer or a test reads. `records.py` holds the draft's read and write with the helpers the parts share, `budget.py` the token budget, and `drafts.py`, `approval.py` and `cancelling.py` the three parts. A part imports `records.py`, `approval.py` also `budget.py`, and no other part. A test patches a name of the stage on the module that reads it, `isekai.pipeline.review.records` for `create` and `write`.**

- **Accepts:** a private name of the stage is not importable from the front door, and a name two parts read lives in `records.py`. Reopen when a part needs a name another defines.
- **Made by:** `0198`, `0199`.
```

## Names

| module | names | read outside the stage |
|---|---|---|
| `records.py` | the list of [0198 D2](../0198-the-review-base/design.md#d2) and `DISCARD` | `save_draft`, `came_from`, `draft_image`, as in 0198 |
| `drafts.py` | `review`, `revise`, `_DRAFT_AGAIN`, `draft_from`, `drafting_sheet`, `drafting_approval`, `_held_way`, `waiting_edit`, `_refuse_edited`, `_waiting_number`, `_discarding`, `_edited`, `Revision`, `refuse_drafts`, `refuse_revision` | `interface/drafting.py`, `interface/ui/routes/reviewing.py`, `interface/verbs/drafts.py`, `interface/verbs/runner.py`, tests |
| `approval.py` | `_window_warnings`, `approve`, `_NOT_COPIED`, `_copy_approval`, `_refuse_unchanged`, `_resheet` | `interface/drafting.py`, `interface/ui/app.py`, `interface/verbs/runner.py`, tests |
| `cancelling.py` | `CANCEL`, `Cancelled`, `discard`, `cancellable`, `cancel`, `_at_draft`, `_cancelling`, `_derived` | `interface/ui/routes/reviewing.py`, `interface/verbs/runner.py`, tests |
| front door | `Status`, `state`, and the re-exports of [D7](#d7) | the importers above |

## Tests

No test is added except a case for a survivor of the pre-flight in [D5](#d5), none is removed, and no assertion changes; no end-to-end run is added. `tests/test_ratchets.py`, `tests/test_artifact_bytes.py` and `tests/mutants.json` change rows, a key and paths; `tests/test_docs.py` and `tests/test_derive_wire.py` change nothing and hold the derived tables and `ui/src/wire.ts`.

| measure | command | before | after |
|---|---|---|---|
| tests in the review file | `git grep -c -e "^def test_" -- tests/test_review.py` | `tests/test_review.py:108` | `tests/test_review.py:108`, one more for each survivor killed |
| tests in the ratchets file | `git grep -c -e "^def test_" -- tests/test_ratchets.py` | `tests/test_ratchets.py:15` | `tests/test_ratchets.py:15` |

The proof is the suite, the standing mutants, the pre-flight, `tests/test_ratchets.py`, which holds that no file or function of the stage is past a ceiling and no row is stale, `tests/test_layers.py`, which holds that no part closes a cycle, and `tests/test_derive_wire.py`. No test is deleted or merged, so no `I16` table is due.

## Dependencies

None.

## Risks / Trade-offs

- A part that reads a name of another closes no cycle but breaks [D1](#d1). The layer test finds a cycle through the front door; a part-to-part import is found by the **Verify** of each part's phase.
- The front door must drop its row without going stale. Its file is under 800 lines once the approval leaves; the approval's phase checks it with a **HALT CHECK**.
- A name a test reads through the front door and D7 missed fails with `ImportError` in that test. The last phase imports each name D7 lists.
- `approve` may still pass 100 lines if 0198 lengthened it. The approval's phase checks it with a **HALT CHECK**.
- A patch of `create` or `write` still reaches `records.py`, which `_publish` and `_write_draft` read. No part reads either name.

## Verdict

Feasible. Each phase ends with its tests passing and the front door importing.
