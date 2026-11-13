# The paydown — design

The runner gains a replay mode, the audit's mutants become a file the replay runs, and the cards left open on the series close. Tools, tests, a design-spec paragraph and one comment under `isekai/`. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The audit ran each test against mutants of the product. The series then closed its findings, and no one has run the mutants against the fixes. `tools/mutate.py` is the runner; it cannot replay them. The facts below were read at the cut, on the branch's base. `0134-linux-green`, the version this one builds after, merged into the default branch during the cut, so the proposal lists no `after:`; the build starts from a tree that has merged it.

| gap | where it lives at the cut |
|---|---|
| the runner edits one line of a function body with its own operators and refuses a file that is not Python | `tools/mutate.py` `sites`, `collect` |
| the runner's copy has no `.git`; tests that ask git fail there at the baseline | `tests/test_run_directory.py`, `tests/test_spec_prose.py`, `tests/test_changelog.py` |
| the runner's copy links `models`, `ui/node_modules` and `ui/dist` | `tools/mutate.py` `LINKED`, `copy_tree` |
| no test runs `run_mutants` under a `--timeout` below the baseline | `tools/mutate.py` `run_mutants`, `mutant_timeout` |
| a discard beside another draft's source copy, and a damaged sheet read by the hub, have no test | `isekai/pipeline/review.py` `discard`, `isekai/interface/ui/library.py` `stage` |
| the patch scanner builds one alias map a file | `tests/test_ratchets.py` `_bound_modules`, `_patches` |
| the prose cards are one line each | `isekai/interface/ui/app.py` `_BAKE_DIGITS`, `ui/design/spec.md` |

```
 tools/mutate.py ──▶ tests/mutants.json ──▶ make mutants        (phases 1, 2, 3)
 tests/test_review.py  tests/test_ui_library.py                 (phase 4)
 tests/test_ratchets.py                                         (phase 5)
 app.py comment · ui/design/spec.md                             (phase 6)
```

## Goals / Non-Goals

**Goals**
- Every mutant of a finding the series closed dies, each by the guard [Tests](#tests) names, and stays dead: a file holds it.
- A copy of the tree answers git, and no test writes through a link into the operator's checkout.
- A card closes because its premise is gone or its fix is in, never because it was forgotten.

**Non-Goals**
- A product edit but one comment, a scenario, a requirement, a new package, a format version.
- A decision in force: none is added or amended, so `docs/decisions.md` is not edited.
- The replay in the gate. A replay takes minutes.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The runner's copy is a git repository of the tracked files and links `models/` alone | tests that ask git fail in a copy with no `.git`; `models/` is read and too big to copy; no test outside the browser's reads the other links | copying `ui/dist`; a read-only link; node ids only |
| [D2](#d2) | A run under a `--timeout` below the baseline is held by a test of `run_mutants` | deleting the line that lifts the limit leaves every test green | counting a timeout a survivor |
| [D3](#d3) | `--edits <json>` replays text edits in any file | the audit's mutants are text edits, some in specs and documents | an operator for each; a mutation package |
| [D4](#d4) | The audit's mutants live in `tests/mutants.json`, replayed by `make mutants`, outside the gate | a mutant that must stay dead is a file, not a memory | the gate; the change directory |
| [D5](#d5) | A survivor of the replay gets one test, or an `equivalent` reason | every entry dies, or is named equivalent in the file | an entry deleted |
| [D6](#d6) | The findings with no shipped test get one: a discard beside another draft's copy, a damaged sheet read by the hub | their mutants survive today | leaving them to the refactor |
| [D7](#d7) | The patch scanner binds an alias by its lexical scope | a reused local alias hides a patched module | the last binding of a file wins |
| [D8](#d8) | Prose edits pay the bake-digit and bake-view cards, and the cards whose premise is gone close with no edit | the rest are paid by D1, D2 and D7 | a fix to an archived change |
| [D9](#d9) | A new case rides in a test under its key, or carries a `structural:` exemption | a patch adds no scenario | a mis-bound key |

### D1

`copy_tree` copies each tracked file that exists, runs `git init -q` and `git add -A -f` in the copy, and only then links `models`. The index then equals the tracked files that exist, and the link is no tracked path. A git that fails is a `Refused`. `LINKED` becomes `("models",)`, and the docstring says a test that writes under `models/` writes through the link, so such a test is isolated; [CONTRIBUTING](../../../CONTRIBUTING.md) says the same beside the pre-flight.

The tests that ask git then pass at the baseline of a copy: the run directory's `git check-ignore` check, and the comment guard's and the changelog's `git ls-files`. An entry may name their files.

### D2

The test builds a small repository whose tests wait a short while, mutates a line whose mutant survives, and runs `main` with a `--timeout` far below the wait. It expects the verdict `survived` and exit 1. Without the `mutant_timeout` line in `run_mutants` the limit is the argument, the survivor outlasts it, and the verdict is `timeout` and the exit 0: the test fails.

### D3

The entry is an object in a JSON array:

| key | holds |
|---|---|
| `finding` | the audit's id, printed in the verdict line |
| `path` | a tracked file, any kind |
| `find` | text that occurs exactly once in the file |
| `replace` | the text put in its place, empty allowed |
| `tests` | a non-empty list of files or node ids, run with `-x -q` |
| `why`, `equivalent` | optional text; any other key is refused |

The rules:

| rule | result |
|---|---|
| a `find` that occurs none or more than once, an untracked `path`, a missing key | `Refused`, naming the finding, exit 2 |
| a `.py` file that no longer parses after the edit | verdict `invalid` |
| the tests of a distinct list run unmutated first | a red baseline is `Refused`, as now |
| each mutant's limit | `mutant_timeout` of its list's own baseline |
| the verdict line | `<verdict> <path>:<line> <finding>: <first line of find> -> <first line of replace>`, `<line>` that of the find, each first line stripped |
| the summary, the survivor lines, the exit codes | as for `path:lines`: `survivor <path>:<line> <finding>`, 0 none survived, 1 a survivor, 2 refused |
| every baseline | runs before any line prints, so a red one leaves stdout empty |
| an entry with `equivalent` | not run; printed `equivalent <path>:<line> <finding>: <reason>`; counts as none |
| `--edits` beside a target, `--tests` or `--all` | `Refused`: `--edits takes no target, --tests or --all` |
| no target and no `--edits` | `Refused`: `give a target or --edits` |

### D4

The cut copies the audit's entries into [mutants.json](mutants.json), each `tests` a list of files. Phase 3 copies every entry but `PB-14` and `UB-14` into `tests/mutants.json`: they survive until phase 4 writes their tests, and each phase ends green ([D6](#d6)). Phase 4 appends them.

The `mutants` target of the `Makefile` runs `uv run python -m tools.mutate --edits tests/mutants.json`, and is not part of `gate`. [CONTRIBUTING](../../../CONTRIBUTING.md) says a refactor version's pre-flight adds its own entries. MT-2's `find` is the form the series left after the guards reworded it: `spec_exempt("structural: the pins guide's path check")`.

### D5

A survivor is killed by a test in the file its entry names, red with the mutant in place and green without it. An entry carries `equivalent` only when no input tells the mutant from the line, and the reason says why, proven by reading the line. A survivor that gets neither is a halt: the plan is wrong about that finding.

The audit's own equivalent survivors, `isekai/foundation/artifacts.py:541` and `isekai/foundation/run.py:287`, are no entry: they are not among the mutants of the findings the series closed.

### D6

| mutant | test | key |
|---|---|---|
| `PB-14`: `discard` deletes every file beside the draft's copy | a new test writes the source copy of another draft beside the draft's own; after `discard` it is still there | `review:discard:a-drafted-draft-goes-alone` |
| `UB-14`: `stage` drops the check of the sheet | steps in the unreadable-file test: a sheet, a tag list and an approval each damaged to version 99 mark their cell `unreadable` and name the file | `ui:hub:an-unreadable-file-marks-its-cell` |

### D7

A name is bound by the innermost enclosing function that imports it, else by the module's own imports. An import in one function binds nowhere else, and one at module level binds in every function that does not import the name itself.

`patched_modules` and `resolved_patches` take each `setattr` against its scope. The twin builds tests that import different modules as `subject` and patch each, and every module is counted.

`names_read` keeps its file-wide map. A reused alias there reads a name as unread, which is red, never blind.

### D8

| card | state at the cut | closes by |
|---|---|---|
| `0131·S4` | `mutant_timeout` is held, its use in `run_mutants` is not | [D2](#d2) |
| `0131·S5` | the copy links `models`, `ui/node_modules`, `ui/dist` | [D1](#d1) |
| `0129·S1` | one alias map a file | [D7](#d7) |
| `0120·R4` | the comment above `_BAKE_DIGITS` says `int` refuses a longer spelling | a one-line comment |
| `0121·R4` | the bake-view paragraph omits *Place a tattoo* | a one-line edit of the paragraph |
| `0119·R4` | both comments already say a queued bake: `isekai/interface/render.py` `Quote.shorts`, `quoted()` in `isekai/interface/ui/app.py` | nothing: fixed already |
| `0119·S4` | the quote keeps a collection that holds a queued bake | nothing: fixed already |
| `0121·S3` | `ink_view` reads the skin point once, through `extract_ink_grey` | nothing: fixed already |
| `0126·R4` | the note is in an archived design | nothing: a record cannot be edited |
| `0133·R1` | the row is in an archived design | nothing: a record cannot be edited |

Each card that closes with no edit is a **HALT CHECK** of phase 6: its premise holds, or the plan is wrong. The release deletes the cards of `debt:` and leaves the debt file alone until then. `0124·S2` stays: it is a product edit.

### D9

| new case | key |
|---|---|
| a run under a short timeout reports a survivor | `structural: a survivor that outlasts --timeout is reported as one` |
| the copy is a repository and links `models` alone | the amended `structural:` reason of the copy's test |
| the replay's entries, refusals, verdicts and equivalents | `structural:` reasons, one a rule |
| a discard leaves another draft's copy | `review:discard:a-drafted-draft-goes-alone` |
| the hub marks a damaged sheet, tag list and approval | `ui:hub:an-unreadable-file-marks-its-cell` |
| the scanner's twin | `structural: twin of test_no_patched_module_is_unlisted` |

## Tests

Every case is a unit test: no browser, no end-to-end test is added, and none runs on an engine. The tests the change adds, by file, over what each file holds at the cut:

| file | tests at the cut, by `git grep -c -E '^def test_' -- <file>` | gains | phase |
|---|---|---|---|
| `tests/test_mutate.py` | 18 | the run under a short timeout, the copy's repository, the replay's cases | 1, 2 |
| `tests/test_review.py` | 96 | the discard beside another draft's copy | 4 |
| `tests/test_ui_library.py` | 27 | steps in the unreadable-file test | 4 |
| `tests/test_ratchets.py` | 14 | the twin of the scope | 5 |

The `tests/mutants.json` replay is not a test and is not in the gate. Each entry of [mutants.json](mutants.json) names the test files that must kill it. The mutants, where each lies at the cut and the phase that replays it:

| mutant | where at the cut | phase |
|---|---|---|
| `MT-1a` | `openspec/specs/pod-image/spec.md:336` | 3 |
| `MT-1b` | `openspec/specs/pod-image/spec.md:297` | 3 |
| `MT-2` | `tests/test_docs.py:76` | 3 |
| `MT-4a` | `tools/npm_ui.py:14` | 3 |
| `MT-4b` | `openspec/specs/pod-image/spec.md:297` | 3 |
| `MT-6` | `docs/principles.md:18` | 3 |
| `MT-7` | `isekai/foundation/run.py:66` | 3 |
| `UA-7` | `isekai/interface/ui/app.py:107` | 3 |
| `FN-1` | `isekai/foundation/run.py:185` | 3 |
| `FN-2` | `isekai/foundation/run.py:826` | 3 |
| `FN-4a` | `isekai/foundation/run.py:207` | 3 |
| `FN-4b` | `isekai/foundation/run.py:93` | 3 |
| `FN-5` | `isekai/foundation/run.py:1025` | 3 |
| `FN-6` | `isekai/foundation/run.py:751` | 3 |
| `FN-9` | `isekai/pipeline/generate.py:306` | 3 |
| `CL-2a` | `isekai/interface/render.py:1282` | 3 |
| `CL-2b` | `isekai/interface/render.py:1269` | 3 |
| `CL-2c` | `isekai/interface/render.py:1108` | 3 |
| `CL-2d` | `isekai/interface/render.py:1274` | 3 |
| `CL-2e` | `isekai/interface/render.py:1314` | 3 |
| `PB-14` | `isekai/pipeline/review.py:519` | 4 |
| `UB-14` | `isekai/interface/ui/library.py:695` | 4 |

No test is deleted or merged, so the `I16` table is empty.

## Dependencies

None.

## Risks / Trade-offs

- **The outcome of phase 3 is unknown until it runs.** An entry the series' tests do not kill is a survivor, and [D5](#d5) says what it gets.
- **A baseline may be red in a copy for a reason other than git.** A test that reads an untracked file outside `models/` fails there. The entry then names node ids in place of the file.
- **A `find` that moves makes the replay refuse.** The refusal names the finding, and the version that moved the text edits the entry. That is the price of a mutant held as text.
- **The replay runs whole test files, so `make mutants` takes minutes.** It is outside the gate for that reason.
- **The branch was cut before `0134-linux-green` merged.** The build starts from a tree that has merged the default branch, and each phase appends one bullet under `## [Unreleased]` of the changelog it brought.
- **The `Makefile` is a gate makefile.** The new target is not in `gate`, and phase 3's task quotes each line it adds.

## Verdict

Ready to build. Each phase ends on a green `make gate`, and phase 3 on a replay with no survivor. Nothing is irreversible: no product behaviour, format version, requirement or decision moves.
