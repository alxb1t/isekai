# The base — design

Test files gain the cases that pin what a refactor of the foundation, the session's record and the delete would move; no product file changes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The audit ran each test against mutants of the product and found the cases that stay green. Version `v0.86.1` is the base. The facts below were re-read at the cut, on a tree where `0128-the-guards-hold` is merged.

| gap | where it lives at the cut |
|---|---|
| the budget is held from above only | `isekai/foundation/run.py:826`, `tests/test_run_directory.py` |
| `attempts` filters by version, no test gives it two | `isekai/foundation/run.py:751` |
| the slug's bound and alphabet, the record's outside path | `isekai/foundation/run.py:93`, `:207`, `:1025` |
| the session's record is never read after an end | `isekai/interface/render.py:1108`, `:1262`, `:1269`, `:1274`, `:1282`, `:1314` |
| the deletes return lists no test pins whole | `isekai/pipeline/review.py:626-651`, `isekai/pipeline/edit.py:349`, `isekai/interface/ui/app.py:1552` |
| three of five "rendered" sites have no test | `isekai/pipeline/review.py:498`, `:1142`, `:1272-1274` |
| the CLI's discards refuse with a few files checked | `isekai/interface/cli.py:851-857` |

```
 tests/ ──▶ isekai/foundation   run.py                (phases 1, 2)
        ──▶ isekai/interface    render.py             (phase 3)
        ──▶ isekai/pipeline     review.py generate.py (phases 4, 5)
        ──▶ isekai/interface    cli.py ui/app.py      (phases 4, 6)
```

## Goals / Non-Goals

**Goals**
- Every mutant the audit named on these files dies, each by the test the table in [Tests](#tests) names.
- A delete's returned list equals what left the tree.

**Non-Goals**
- A product edit, a scenario, a requirement, a new package.
- A test of a difference between the CLI and the app: it would bless a defect ([D6](#d6)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The budget is held from below by a case over `caption`, `wd14` and `tags`, and `attempts` by versions sharing a directory | the audit's `>= budget - 1` mutant ships green today | a case per stage; a case on `caption` alone |
| [D2](#d2) | The slug's bound and alphabet, the record's path and a stray directory each get the case that kills their mutant | each mutant survives the suite | none |
| [D3](#d3) | The session's record is read back at every end, and a lost create and a failed teardown are pinned as `running` | `Record.close` ends no outcome on purpose | pinning an invented outcome |
| [D4](#d4) | A delete's list is pinned as equal to the tree difference; an ordered literal only where the code orders | a hand-written list repeats the code | hand-written lists everywhere |
| [D5](#d5) | "Rendered" is pinned only where every site agrees: both files rendered; none, or failure records alone, not | a lone file is the refactor's decision | pinning each site's lone-file answer |
| [D6](#d6) | Only what both front ends share is pinned | a test of today's difference blesses a defect or flips inside a refactor | `xfail(strict=True)` |
| [D7](#d7) | A new case rides in an existing test that carries its key; where no scenario fits it carries a `structural:` exemption | a patch adds no scenario | a mis-bound key |
| [D8](#d8) | The audit's equivalent survivors are named and left | no test can reach them without a product edit | a product edit |

### D1

The retry rule is `isekai/foundation/run.py:_spent`. A parametrized case takes `("caption", 3)`, `("wd14", 1)` and `("tags", 3)`: it writes a record short of the budget and `check_budget` returns, then writes the budget's own record and `check_budget` refuses. For `wd14` the first half writes none and the second half reads `BUDGETS["wd14"]`, so dropping that entry raises: the mutant dies in this test alone.

A further case writes a stage's budget of records against version 1 and asks about version 2: `attempts` is empty and `check_budget` returns. A permanent record at version 1 does not bar version 2.

The deleted `test_a_tagger_below_its_budget_attempts_again_rather_than_raising_keyerror` writes no record, so it returns before the budget is read: it cannot fail. The new case carries its key.

### D2

| case | where | before → after |
|---|---|---|
| a stem `a_b` | the slug's cases | `slug("a_b")` → `a-b` |
| a stem of `a` × 31, `-`, `b` × 8 | the slug's cases | the cut falls on a separator → `a` × 31 |
| a stem of `a` × 40 | the slug's cases | → `a` × 32, the bound |
| an instruction file outside the repository | the caption's producer test | `path` → the file's name, `other.md` |
| a stray empty directory | a second pass over the runs root | `tree` sees it, `snapshot` does not |

The stray directory is proven by hand, once, while building: create an empty directory in the runs root between the passes and the test goes red. No test of `tree` is added.

### D3

| end | record after it |
|---|---|
| a flow raises | `failed`, the exception's text, teardown `done` |
| a SIGTERM | `stopped`, no message, teardown `done` |
| the watchdog's limit | `stopped`, the limit's sentence |
| a flow exits non-zero | `failed`, `a flow failed; the collection's log names it` |
| every flow done | `done`, no message |
| a lost create | pod `lost`, outcome `failed`, the provider's sentence, ended |
| a failed teardown | teardown `failed`, outcome `failed`, the teardown's sentence, ended |

The last two end through `refuse` in `isekai/interface/render.py`, which calls `record.end("failed", message)`; `Record.close` ends no outcome itself, and that stays true. An earlier reading that both stay `running` was wrong, and the plan pins what the product does. The tests for them keep their `structural:` exemption, which the guards' table holds, and bind no key.

### D4

`discard_render`, `discard_edit`, `withdraw` and the CLI's `discard` return or print what they delete. The pin is a test of that claim: the sorted paths returned equal `set(before) - set(after)` over `tests/conftest.py:tree` of the run. Where the code fixes an order — `delete_edits` takes image, record, placement, composite, edit by edit — the case pins the literal list too, leaving out a file the case does not write: edit 3 of `_chain` has no image, edit 2 of the placement case has no image.

The ordered cases are `test_edit_discard_an_edit_takes_the_edits_made_from_it_and_the_render_stays`, `test_edit_discard_a_pending_edit_is_named_by_the_path_its_image_will_have` and `test_placement_discard_an_edit_takes_its_placement_and_the_chain_made_from_it`.

The app's delete returns `{"deleted": True}`. The pin is that its run tree equals the tree the CLI's `discard` leaves on a copy of the same collection.

### D5

| site | both files | none | failure records alone |
|---|---|---|---|
| `isekai/pipeline/review.py:498` `refuse_revision` | revises | refuses, naming the seed | refuses, naming the seed |
| `isekai/pipeline/review.py:1142` `_refuse_unchanged` | refuses | approves | approves |
| `isekai/pipeline/review.py:1272-1274` `copied_renders` | seeds listed | the approval's own | the approval's own |
| `isekai/interface/ui/library.py:681` and `:672` `stage` | `rendered` | `approved` | `approved` |

A lone image or a lone sidecar is left unpinned: the sites disagree today, and the refactor settles one definition.

### D6

These differences stay unpinned: the app's guard asks the job slot only, so a terminal render does not stop it; the CLI's render discard drops the render's thumbnails and the app's drops each edit's too; `approve --cancel` has no guard. Version 1000 is invisible to `versions`, and the lock guard never covers a plain `runs/` folder: each needs a product edit, and no debt card is written by the cut.

### D7

| new case | key |
|---|---|
| the budget's boundary, and versions sharing a directory | `run-directory:budget:at-budget-the-stage-refuses`, `tagging:budget:each-tagger-has-its-own-budget` |
| the revision of a seed no render wrote | `structural: a revision refuses a seed no render wrote` |
| a revision's seeds not rendered | `review:revise:new-seeds-alone-are-a-change` |
| a copy of a group holding no render | `review:copy-from:the-copy-carries-the-seeds` |
| the cell's stage over a group with no render | `ui:hub:a-cells-stage-comes-from-its-run` |

The rest are steps in tests that keep their marks. `0128`'s table lists `test_a_lost_create_exits_3_and_a_failed_teardown_names_gpunit_down` and `test_a_failed_body_is_named_beside_a_failed_teardown`: they stay exempt and unbound, so no row leaves the table.

### D8

`isekai/foundation/artifacts.py:541` changed an indent, which no reader sees. `isekai/foundation/run.py:287` is unreachable: `_photo_record` is called only with `"name"` and `"sha256"`, which `photo_record` has required as strings. The mutant of `isekai/foundation/run.py:185`, a dropped `"wd14": 1`, counts as killed only by the [D1](#d1) case alone.

## Tests

Every case is a unit test, so none needs a browser. Each new test fails with the product's mutant in place ([D1](#d1)–[D5](#d5)); each other case is a step in a test that keeps its key.

| test file | what it gains | phase |
|---|---|---|
| `tests/test_run_directory.py` | the budget case, the versions case, the slug's cases | 1, 2 |
| `tests/test_caption.py` | the instruction record's path | 2 |
| `tests/test_resume.py`, `tests/test_migrate.py` | a tree read in place of a snapshot | 2 |
| `tests/test_render.py` | the session record read back at each end | 3 |
| `tests/test_edit_session.py` | the record of a done bake and a failed flow, the edit discard's whole lists, the refusal's whole tree | 3, 4, 6 |
| `tests/test_generate.py`, `tests/test_edit_placement.py` | the whole list a discard returns | 4 |
| `tests/test_review.py` | `withdraw`'s lists, the cases of the "rendered" sites | 4, 5 |
| `tests/test_ui_api.py` | the route's tree held equal to the CLI's | 4 |
| `tests/test_ui_library.py` | the cell's stage over a group | 5 |
| `tests/test_pipeline_cli.py` | the refusal's whole tree | 6 |

| mutant, at the cut | killed by |
|---|---|
| `isekai/foundation/run.py:826` `>= BUDGETS[stage]` → `>= BUDGETS[stage] - 1` | the budget case, 1.2 |
| `isekai/foundation/run.py:185` drop `"wd14": 1` | the budget case, 1.2, alone |
| `isekai/foundation/run.py:751` drop `named[0] == version` | the versions case, 1.4 |
| `isekai/foundation/run.py:207` drop `[:ID_SLUG_CHARS].strip("-")` | the slug's cases, 2.2 |
| `isekai/foundation/run.py:93` `[^a-z0-9]+` → `[^a-z0-9_]+` | the slug's cases, 2.2 |
| `isekai/foundation/run.py:1025` `resolved.name` → `str(resolved)` | the caption's producer test, 2.3 |
| `isekai/interface/render.py:1282` `failed` → `done` | the failed teardown's record, 3.4 |
| `isekai/interface/render.py:1269` `stopped` → `done` | the SIGTERM's record, 3.2 |
| `isekai/interface/render.py:1108` the limit's note dropped | the ceiling's record, 3.3 |
| `isekai/interface/render.py:1274` `lost` → `ready` | the lost create's record, 3.4 |
| `isekai/interface/render.py:1314` `failed` → `done` | the raised flow's record, 3.2 |
| `isekai/interface/render.py:1262` the failed flow's outcome | the failed flow's record, 3.5 |

Replay each by hand, or with `tools/mutate.py` where `0131-the-nets-holes` has landed it: apply the change to a scratch copy, run the named test, expect red, discard the copy. The replay is for converge; no task edits the product.

The `I16` table, one deletion:

| deleted test | carried by |
|---|---|
| `test_a_tagger_below_its_budget_attempts_again_rather_than_raising_keyerror` | `test_a_stage_attempts_until_its_budget_and_refuses_at_it`, which carries `tagging:budget:each-tagger-has-its-own-budget` and covers the `wd14` and `tags` stages |

## Dependencies

None.

## Risks / Trade-offs

- **A list pinned as the tree difference repeats the code's reading of what it removed.** It would pass if the code removed too little and returned too little. Mitigation: the app's tree is also held equal to the CLI's, and the cases that fix an order pin the literal list.
- **`0130-the-record` and `0131-the-nets-holes` edit `tests/test_resume.py`, `tests/test_caption.py`, `tests/test_pipeline_cli.py` and `tests/conftest.py`.** Tasks name tests, never lines; a moved test is found by name.
- **A new exempt test keeps a behaviour out of the spec.** One case does ([D7](#d7)); the spec audit owns its scenario.
- **`0128`'s binding guard reads a skipped key.** No case here is skipped.

## Verdict

Ready to build. Each phase ends on a green `make check`, the last on a green gate. Nothing irreversible; no product file moves.
