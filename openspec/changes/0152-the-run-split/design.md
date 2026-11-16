# The run split — design

`run.py` becomes a front over the siblings `names.py`, `rundir.py`, `layout.py` and `failures.py`; every name stays importable from `isekai.foundation.run`, and no path, record, refusal or command text changes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`isekai/foundation/run.py` is one file of clusters with no cycle between them: the id and its names, `Run` and its frame, numbering and completion, the seeds, the edit files, the failure budgets, the command text, the migration state and the provenance records. It is a listed row of the file ratchet ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).

Reads cross the clusters: `rendered_at` calls `stage_command`, and `photo_of` calls `migrate_command`. Both commands read `RUNS_ROOT`, which a test patches on `isekai.foundation.run`. Every importer reads its names from `isekai.foundation.run`, and the entry point imports with site-packages off, so a sibling stays on the standard library and the foundation.

## Goals / Non-Goals

Goals: the clusters that need nothing of the command text move into siblings; `run.py` re-exports every name; the file's ratchet row goes; the documents say where each name lives.

Non-Goals: an importer, a name, the `RUNS_ROOT` patch, `refusal_for`'s parameters, the library's and the session's names, the runs' predicate, the loaders' extract, a refusal at the last number an artifact's name can spell.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `run.py` stays the front and re-exports every name of its siblings under `__all__`; a sibling never imports it | no importer changes, and `RUNS_ROOT` and `DATA_ROOT` keep their module | a `run/` package: it renames a ratchet key, strands the `RUNS_ROOT` patch and moves `DATA_ROOT` |
| [D2](#d2) | each name goes to the home the table of D2 gives | the clusters have no cycle between them; the order of the modules is the order of the table | a split by size: it cuts a cluster |
| [D3](#d3) | the roots, `open_run`, `find_run`, `rendered_at`, the command text with `refusal_for`, the migration state and the provenance records stay in `run.py` | `rendered_at` reads `stage_command`, which reads the patched `RUNS_ROOT`; moved below it they close a cycle | moving `rendered_at` into `layout.py`: it imports the front |
| [D4](#d4) | a moved block keeps its text, comments and docstrings; its imports are what the block reads | a body's mutants keep their text, and the replay proves them | rewording a docstring on the way |
| [D5](#d5) | `Kind` goes to `failures.py`; `_laid_out` and `is_seed` stay in `layout.py`, and `run.py` imports `_laid_out` by its own name | `Kind` is the failure shape's word; `rendered_at` and `edit_at` both read `_laid_out` | a renamed `_laid_out`: a name changed on a move |
| [D6](#d6) | `run.py` keeps its imports of `os` and `write_atomically`, and `__all__` lists every public name of today's file but `T` | a test reads `os` as an attribute of the module; `T` is a typing helper no importer reads | dropping `os`: it strands the `fsync` patch of `tests/test_generate.py` |
| [D7](#d7) | the UI's artifact tripwire lists `artifact_name` under `isekai.foundation.layout` too, its assertion unchanged, and a new twin holds the row | the guard would narrow without the row; nothing fails when the row is removed without the twin | an edit of the existing twin's expected list: an assertion changes |
| [D8](#d8) | the file's ratchet row goes in phase 2, where `run.py` falls to 800 lines or fewer; `refusal_for`'s row and the patch row stay | the ratchet reads a row whose offender no longer offends as red, so phase 2 ends green only without it | removing it in phase 4: phase 2 ends red |
| [D9](#d9) | a new decision, D61, says the run directory is `run.py` and its siblings are imported through it; D21 names `failures.py` | the documents a version makes false are amended in its diff, and a rule gets a decision | a rule left in a README |
| [D10](#d10) | each moving phase is proved by `tools.mutate` over the lines it moves, before and on their new home; a survivor is killed by a test or named in [Equivalent mutants](#equivalent-mutants); the moved entries of `tests/mutants.json` take their new path, their text unchanged | `CONTRIBUTING.md`'s rule, and an entry is an address, not an assertion | a proof by the suite alone: it does not hold every line |

### D1

`run.py` imports each name a sibling defines and lists it in `__all__`, as [`interface/verbs/__init__.py`](../../../isekai/interface/verbs/__init__.py) does for the verbs. The graph has no cycle, so the layer guard's cycle rule holds:

```
names.py ◀── rundir.py ◀── layout.py
   ▲             ▲
   │             └──────── failures.py      (also imports names.py)
   └── run.py imports all four; none of them imports run.py
```

Each sibling imports `artifacts.py`, `refusal.py` and the siblings to its left, and nothing else of the package. The entry point's `-S` guard holds because each imports the standard library alone.

### D2

| home | names |
|---|---|
| `names.py` | `ID_DIGEST_CHARS`, `ID_SEPARATOR`, `ID_SLUG_CHARS`, `_UNSAFE`, `_SIGNATURES`, `SIGNATURE_BYTES`, `FRAME_NAME`, `CAPTIONS`, `WD14`, `TAGS`, `PHOTO`, `DESCRIPTION`, `PHOTOGRAPH_VERBS`, `SHEETS`, `REVIEW`, `PROMPTS`, `OUTPUTS`, `SOURCES`, `APPROVED`, `ARTIFACT`, `ERROR`, `slug`, `digest_of`, `run_id`, `media_type` |
| `rundir.py` | `_PHOTO_FIELDS`, `Run`, `assign` |
| `layout.py` | `versions`, `latest`, `next_version`, `artifact_name`, `is_version`, `approval_of`, `sheet_of`, `group_of`, `_DIGITS`, `_SEED_DIGITS`, `is_seed`, `_laid_out`, `EDIT_STEM`, `EDIT_COMPOSITE`, `EDIT_RECORD`, `EDIT_PLACEMENT`, `is_edit_file`, `edit_stem`, `edit_files`, `placement_file`, `edit_numbers`, `next_edit`, `delete_edits`, `edit_at`, `latest_artifact`, `is_approved`, `approved_versions` |
| `failures.py` | `Kind`, `BUDGETS`, `T`, `Attempt`, `attempts`, `failure_named`, `failures_alone`, `record_failure`, `_spent`, `exhausted`, `check_budget`, `across`, `StageFailure` |
| `run.py` | `DATA_ROOT`, `RUNS_ROOT`, `REPOSITORY`, `_run_for`, `open_run`, `find_run`, `_photo_bytes`, `rendered_at`, `NEW_VERSION`, `stage_command`, `migrate_command`, `unmigrated`, `photo_of`, `refusal_for`, `instructions_record`, `constant_record` |

A sibling imports only from the rows above its own; `run.py` imports from all of them.

### D3

`stage_command` reads `RUNS_ROOT`, a name one test patches on `isekai.foundation.run`; `open_run`, `find_run` and `migrate_command` read it from their own module. `rendered_at` calls `stage_command` and `photo_of` calls `migrate_command`, so both stay with it. `refusal_for` calls `stage_command` and stays for the same reason.

### D4

A block moves whole: its comments, docstrings and body are the text of the cut's base. Its imports are each name the block reads, from the module that now holds it. The only new text in a sibling is its module docstring and its import block.

### D5

`rendered_at` imports `_laid_out` and `is_seed` from `layout.py`, and `edit_at` reads them in the same file. `_run_for` reads `Run._photo_record`, a method of `rundir.py`'s class. No name changes.

### D6

`__all__` is written once, in phase 1, listing every public name of the cut's base, including those still defined in `run.py`; later phases add imports and no entries. The check is the one command of phase 1's task 1.6, which reads the names of the cut's base.

### D7

`tests/test_ui.py`'s `_ARTIFACT_WRITERS` gains a row `"isekai.foundation.layout": frozenset({"artifact_name"})`. The existing twin writes `named.py` importing from `isekai.foundation.run` and keeps its expected list. A new twin, bound `structural: twin of test_the_invariant_holds_no_module_of_the_surface_names_an_artifact`, writes `laid.py` importing `artifact_name` from `isekai.foundation.layout` and expects `(["laid.py: artifact_name"], 1)` (cut decision C6).

### D8

After phase 1 `run.py` is still past 800 lines, so its row stands. After phase 2 it is not, and the ratchet reads the row as stale. Phase 2 removes the row and the table's count goes from 7 to 6; the series' plan put the row in the last phase, which cannot end phase 2 green (cut decision C5).

### D9

D61 is added after D60 in `docs/decisions.md`:

```
### D61 · The run directory is run.py, its siblings imported through it

**The run directory is `isekai/foundation/run.py`. It re-exports every name of `names.py`, `rundir.py`, `layout.py` and `failures.py` under `__all__`, and a module outside the foundation imports a run's names from `isekai.foundation.run`, never from a sibling. A sibling imports no `run.py` and stays on the standard library and the foundation.**

- **Why:** the run directory was one file of clusters and a listed row of the ratchet ([D56](#d56--size-and-patches-are-held-by-ratchets)). A front that re-exports changes no importer, keeps `RUNS_ROOT` and `DATA_ROOT` in one module and leaves the layer guard's cycle rule nothing to find.
- **Accepts:** the roots, `open_run`, `rendered_at`, the command text and the provenance records stay in `run.py`, because `rendered_at` reads `stage_command`, which reads the patched `RUNS_ROOT`. Review holds that an importer reads the front; no test does. Reopen when `RUNS_ROOT` is no longer patched.
- **Made by:** `0152`.
```

D21's sentence ends "The numbers are `BUDGETS` of `failures.py`, read through `run.py`."

### D10

Phase 1 opens with the run over its ranges in `run.py`; phases 2 and 3 open with the tests' baseline, since no range of `run.py` holds once the phase before has shifted it, and each phase closes with the run on the new modules, which covers the same mutants. `tools.mutate` copies tracked files only, so `git add -N` names each new module before its closing run. Each closing run is one run per range, so none outlasts the plan check's 600 seconds. The test sets:

| phase | test files the runs name |
|---|---|
| 1 | `tests/test_run_directory.py`, `tests/test_assign.py`, `tests/test_package_paths.py`, `tests/test_resume.py`, `tests/test_artifact_bytes.py`, `tests/test_migrate.py` |
| 2 | `tests/test_run_directory.py`, `tests/test_edit.py`, `tests/test_edit_placement.py`, `tests/test_edit_session.py`, `tests/test_review.py`, `tests/test_ui_api.py` |
| 3 | `tests/test_run_directory.py`, `tests/test_caption.py`, `tests/test_tagging.py`, `tests/test_sheet_stage.py`, `tests/test_resume.py`, `tests/test_edit_session.py` |

The opening run's ranges are the cut's base's, so the sub-task that holds them is checked at `HEAD` by the section below. `tools.mutate` mutates function bodies only, so the constants of `names.py` are held by the replay (FN-4b), not by a range.

## Where things go

```
run.py ──▶ names.py · rundir.py · layout.py · failures.py ──▶ artifacts.py · refusal.py
importers ──▶ run.py        (never a sibling)
```

## Survivors at the cut

The cut ran each phase's ranges of the cut's base once, with the test files of D10's table. These mutants survived. The build kills each with a test of the function through a caller that binds an existing scenario of the `run-directory` spec, in `tests/test_run_directory.py` or the caller's own test file, or names it in [Equivalent mutants](#equivalent-mutants).

| phase | survivor |
|---|---|
| 1 | `run.py:251` `digest`'s return; `run.py:281` and `run.py:287` the `require` calls of the photograph's fields; `run.py:321` `flows`' empty return; `run.py:433`, `run.py:435`, `run.py:437` and `run.py:444` the returns of `assign` |
| 2 | `run.py:586` `is_edit_file`'s `return False` as `return None` |
| 3 | `run.py:857` the budget of one in the plural test of `check_budget`; `run.py:883` `StageFailure.__init__`'s `super().__init__(detail)` |

## Equivalent mutants

A survivor the build cannot kill with a test is named here, one row each: `path:line · mutant · why no test can tell it`. None named at the cut.

| survivor | why equivalent |
|---|---|

## Tests

The change adds the twin of D7 to `tests/test_ui.py`, a unit test of the tripwire's scanner, and a test besides only to kill a survivor, in `tests/test_run_directory.py` or its caller's file, bound to an existing scenario of the `run-directory` spec. It edits `tests/test_ratchets.py` (a row goes) and `tests/mutants.json` (paths move), deletes and merges no test, so no `I16` table is owed. It adds no end-to-end run: the suite reads each moved name through its importers. `tests/record/` is read by the gate and edited by no task.

| measure | now | command |
|---|---|---|
| tests of the tripwire's file | `test_ui.py` 18 | `git grep -c -E "^(async )?def test_" -- tests/test_ui.py` |
| tests of the run directory | `test_run_directory.py` 71 | `git grep -c -E "^(async )?def test_" -- tests/test_run_directory.py` |
| end-to-end runs added | none | none planned |

## Dependencies

None.

## Risks / Trade-offs

- A name left out of `__all__` fails at its first importer; the suite imports each, and the phase-1 check compares the lists.
- A sibling that reads a name of the front, such as `RUNS_ROOT`, closes a cycle the layer guard turns red.
- The derived *Imported by* rows list each new module under every foundation file it imports; versions cut from one `main` that each add such a module edit one line.
- An importer that reads a sibling directly passes every test; the decision D61 and review hold it.
- A mutation run over a moved span takes minutes; it is out of the gate.

## Verdict

Ready to build. Each block keeps its text, so the suite and the mutation runs are the proof.
