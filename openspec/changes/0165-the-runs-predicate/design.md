# The runs predicate — design

One rule, a run is a folder holding its frame file, is written once in `rundir.py` and called by the sites that each wrote it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A **run** is a folder of a runs root that holds its frame, `run.json`, as a file. The front-end sites of the diagram ask that of a folder, each in its own words, and every caller of them already imports `isekai.foundation.run`.

```
before   render.run_ids   compare._runs   cli._migrate   verbs.run_or_photo   verbs.parse_cells   ui/library._runs
              each:  (folder / FRAME_NAME).is_file()

after    each ─▶ runs_in(root)  or  run_at(root, id) ─▶ rundir.py ─▶ re-exported by run.py (D62)
```

| evidence | command | at HEAD |
|---|---|---|
| the front end tests the frame itself | `git grep -n -F "FRAME_NAME).is_file()" -- isekai/interface` | six lines, one per site |
| the foundation has no listing | `git grep -n -e "^def runs_in" -e "^def run_at" -- isekai/foundation/rundir.py` | nothing |

## Goals / Non-Goals

- Goal: one place decides which folder is a run, so a change to the rule is one edit.
- Goal: behaviour unchanged. No existing test's assertion changes.
- Non-goal: a new module, a scenario, a spec delta, a ratchet row, or a change to a derived *Imported by* row.
- Non-goal: the sites that differ by design ([D4](#d4)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `runs_in(root)` and `run_at(root, id)` live in `isekai/foundation/rundir.py`; `run.py` re-exports both | `rundir.py` owns `Run` and its frame; a front end imports a run's names from `run.py` ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)) | a method of `Run`: a `Run` exists only after the rule says so |
| [D2](#d2) | `runs_in` returns the runs by id, `[]` for a root that is no directory; `run_at` returns a `Run` or `None`; each tests the frame with `is_file` | the sites answer so today | a refusal for an absent root: one site refuses, in its own words, before it calls |
| [D3](#d3) | the sites call them and keep what is their own | the hub, each refusal and each result's type stay as they are | one helper for the library's key too: only the library keys by digest |
| [D4](#d4) | resume's `_run_for`, evaluation's `runs_in`, `_laid_out` and the remedy `rendered_at` picks stay as they are | each differs by design or asks about one path | folding evaluation in: its bound recall test makes `run.json` a directory and expects unreadable rows |
| [D5](#d5) | the change adds no module and no scenario; `skip_specs: true`, and the rule's cases carry `spec_exempt` | nothing observable moves, and `rundir.py` is already a row of the foundation README | a scenario for the rule: a patch adds none |
| [D6](#d6) | each site's mutation run is one run over one line range, before its switch and again after | a refactor is pre-flighted over the lines it rewrites | one run over a file: a survivor's place is lost |
| [D7](#d7) | [docs D65](../../../docs/decisions.md) records the rule and its exceptions | a change that adds a decision in force names the page that holds it | recording it here alone: this file freezes at the archive |

### D1

`runs_in` and `run_at` are plain functions of `rundir.py`: stdlib and the foundation only, on `python -m isekai`'s import graph. They add no import to the module, so no derived row of the foundation README moves.

### D2

```python
def runs_in(root: Path) -> list[Run]:
    """Return the runs under `root`, by id; a root that is no directory holds none."""
    if not root.is_dir():
        return []
    return [
        Run(path.name, path)
        for path in sorted(root.iterdir())
        if (path / FRAME_NAME).is_file()
    ]


def run_at(root: Path, identifier: str) -> Run | None:
    """Return the run `identifier` names under `root`, or None where it names none."""
    path = root / identifier
    return Run(identifier, path) if (path / FRAME_NAME).is_file() else None
```

A frame that is a directory, a folder with no frame and a file beside the folders are no run. The list is built whole before a caller walks it, as `_migrate` builds its names today.

### D3

Each site loses its `FRAME_NAME` import and gains `runs_in` or `run_at` from `isekai.foundation.run`; none reads `FRAME_NAME` otherwise.

| site | at HEAD | after | its tests |
|---|---|---|---|
| `run_ids` in `isekai/interface/render.py` | `:203-209` | `return [run.id for run in runs_in(runs)]` | `tests/test_render.py` |
| `_runs` in `isekai/interface/compare_view.py` | `:106-121` | the refusal of a root with no `runs/` stays; `return runs_in(root)` | `tests/test_compare.py` |
| `_migrate` in `isekai/interface/cli.py` | `:191-196` | `for run in runs_in(root):`, `where` names `run.id`, `migrate(run)` | `tests/test_migrate.py` |
| `run_or_photo` in `isekai/interface/verbs/common.py` | `:289-292` | `found = run_at(wired.runs_root, identifier)`; `if found is not None: return found` | `tests/test_pipeline_cli.py` |
| `parse_cells` in `isekai/interface/verbs/common.py` | `:328-333` | `if run_at(wired.runs_root, run_id) is None:` | `tests/test_pipeline_cli.py` |
| `_runs` in `isekai/interface/ui/library.py` | `:797-806` | `{run.id[:ID_DIGEST_CHARS]: run for run in runs_in(runs) if run.id[ID_DIGEST_CHARS:].startswith(ID_SEPARATOR)}` | `tests/test_ui_library.py` |

A root that is absent answers as it does today: `run_ids` and `_migrate` list none, the library's `_runs` is `{}`, the compare page refuses naming `runs/`, and `run_or_photo` and `parse_cells` find no run.

### D4

Resume's `_run_for` lists by the photograph's digest and passes over a folder with no frame, so `open_run` writes one in place. Evaluation's `runs_in` globs every folder holding anything named `run.json`, so that a frame that is no file is a run that does not read; `tests/test_recall_cli.py` binds that reading. `_laid_out` in `isekai/foundation/layout.py` and the `is_file` test in `rendered_at` ask about one path. No task edits any of them, nor a file under `evaluation/`.

### D5

The rule's cases stand on no scenario, so each carries `@pytest.mark.spec_exempt("structural: ...")` as the layer guards do. `tests/test_ratchets.py` keeps its rows: `render.py` and `ui/library.py` stay past their ceiling.

### D6

A mutation run is `uv run python -m tools.mutate <path:lo-hi> --tests <file>` over one range. A survivor that is no equivalent mutant gets its case, in the site's test file, before the site is switched. No run names `tests/test_ui_api.py`, so no draft-lock test is left out.

### D7

`docs/decisions.md` gains this block at the end of `## Runs`, after D43:

```markdown
### D65 · A run is a folder holding its frame file

**A run is a folder of a runs root that holds its frame, `run.json`, as a file. `runs_in(root)` lists the runs of a root by id and `run_at(root, id)` returns the run a folder names; both are in `isekai/foundation/rundir.py`, and a front end reads them through `isekai.foundation.run`. A site that lists or finds a run calls them and tests no frame of its own.**

- **Why:** the front end's sites each asked of a folder whether it was a run, in their own words, so a change to the rule was an edit in each. The library keeps its separator filter and its key over `runs_in`, so the hub is unchanged.
- **Accepts:** resume and evaluation differ by design. Resume's `_run_for` finds a run by its photograph's digest and passes over a folder with no frame, so `open_run` writes one in place. Evaluation's `runs_in` lists every folder holding anything named `run.json`, so a frame that is no file is a run that does not read and its renders are unreadable rows. `_laid_out` and the remedy `rendered_at` picks ask about one path. Reopen when a front-end site tests a frame itself, or the evaluators list by the rule.
- **Made by:** `0165`.
```

## Tests

Adds unit tests to `tests/test_run_directory.py`, each `spec_exempt`; removes none, so no table of removed tests; adds no end-to-end run, since the rule reads a directory and no browser shows more (the lowest layer that can fail). The command that lists them after phase 1 is `uv run pytest tests/test_run_directory.py --collect-only -q -k "runs_in or run_at"`.

| test | holds |
|---|---|
| `test_runs_in_lists_a_folder_that_holds_a_frame_file` | a folder with `run.json` is a `Run` of that name and path |
| `test_runs_in_leaves_out_a_folder_whose_frame_is_a_directory` | a `run.json` directory makes no run |
| `test_runs_in_leaves_out_a_folder_with_no_frame` | an empty folder makes no run |
| `test_runs_in_leaves_out_a_file_beside_the_folders` | a plain file in the root makes no run |
| `test_runs_in_lists_the_runs_by_id` | folders made out of order come back sorted |
| `test_runs_in_holds_none_of_a_root_that_is_no_directory` | an absent root and a file give `[]` |
| `test_run_at_finds_the_run_a_folder_with_a_frame_names` | `run_at` returns that `Run` |
| `test_run_at_finds_no_run_where_the_frame_is_no_file` | a frame directory, no frame, no folder and an absent root give `None` |

The sites' own tests, `tests/test_render.py`, `tests/test_compare.py`, `tests/test_migrate.py`, `tests/test_pipeline_cli.py` and `tests/test_ui_library.py`, stay as they are; a case is added to one only where a mutation survivor needs it ([D6](#d6)).

## Dependencies

None.

## Risks / Trade-offs

- A function of evaluation shares the name `runs_in`. They differ on purpose ([D4](#d4)), and D65 says so. Neither imports the other.
- The mutation runs may find survivors in a site the tests reach only through a verb; the case goes in the site's test file, and no existing assertion changes.
- A site's `FRAME_NAME` import left behind turns the lint red; each switch removes it in the same task.

## Verdict

Feasible. Each site already applies the rule; the change names it once and calls it from each.
