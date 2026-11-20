# The render listing — design

Move the render group's listing, and `run_view.rendered` with it, into `isekai/foundation/layout.py`, behind `run.py`'s front, with every old name still bound where a reader or a test needs it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The listing lives in the paid stage, `isekai/pipeline/generate.py`: `is_render`, `is_sidecar`, `rendered_seeds`, `sidecars` and `render_groups`. Each reads foundation names alone: `is_seed`, `SIDECAR`, `OUTPUTS` and `Run`. The stage reads `rendered_seeds` in `shortfall` and further down, and `render_groups` in `source_seeds`.

`run_view.py`, `compare_view.py`, `render.py` and `ui/library.py` import the listing from the stage. `run_view.rendered` lists each flow's groups and seeds from the same names, and the evaluator imports it. `layout.py` already imports `artifacts.py` and `rundir.py`, and `run.py` re-exports its names ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)).

```
before                                     after

evaluation ─▶ interface/run_view ─┐        evaluation ──────────────┐
interface/compare_view ───────────┤        interface/run_view ──────┤
interface/render ─────────────────┼─▶ pipeline/generate     │       ▼
interface/ui/library ─────────────┘   (the listing)         └─▶ foundation/run ─▶ foundation/layout
                                                                   (re-exports)     (the listing)
                                           interface/render ──▶ pipeline/generate: duration, shortfall
                                           interface/ui/library ▶ pipeline/generate: lacks
```

The change is a patch under [CONTRIBUTING](../../../CONTRIBUTING.md): no format version moves, no requirement changes, no verb or flag changes. It carries `skip_specs: true`.

## Goals / Non-Goals

**Goals**
- `layout.py` holds the listing and `rendered`; `run.py` re-exports each under `__all__`.
- `run_view.py` and `compare_view.py` import nothing from `isekai.pipeline.generate`; the evaluator imports nothing from `isekai.interface.run_view`.
- No file under `tests/` changes but one mutant's `path` in `tests/mutants.json`.

**Non-Goals**
- Any change of an answer: `render_groups` keeps `str.isdigit`.
- A builder for a render's file name, one rule for "rendered", or `rendered_at` and `edit_at`.
- The evaluator's import of `trackable`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `is_render`, `is_sidecar`, `rendered_seeds`, `sidecars`, `render_groups` and `rendered` move to `layout.py` with body, signature, docstring and default unchanged; `run.py` re-exports each | each reads foundation names alone; D62 says a module outside the foundation imports a run's names from `run.py` | a new module; leaving `rendered` in `run_view.py` |
| [D2](#d2) | `lacks`, `shortfall`, `duration`, `source_seeds` and `discard_render` stay in `generate.py` | each reads an approval or deletes | moving the stage's own readers |
| [D3](#d3) | `render_groups` keeps `str.isdigit` | a move changes no answer; the folder it should not list is a later change's question | three ASCII digits now |
| [D4](#d4) | A name an old home still reads is imported plain; one it no longer reads is bound as `X as X`; `sidecars` is bound in `generate.py` in phase 1 and goes in phase 2 | a test patches `rendered_seeds` on the stage's module; tests import `is_render` and `is_sidecar` from it; a re-bind nothing reads is dead | a re-bind of `sidecars` kept; `__all__` in `generate.py` |
| [D5](#d5) | The importers switch in this change: `render.py` and `ui/library.py` read the listing from `isekai.foundation.run` and keep the stage's own names; the evaluator reads `rendered` from `run.py` | a module above the stage imports it only to list a folder | leaving the switch to a later change |
| [D6](#d6) | The evaluator's import of `trackable` stays, and no layer rule for `evaluation/` is added | the evaluator's tests patch the wiring's roots, which `trackable` reads at call time | moving `trackable` here |
| [D7](#d7) | The mutant `FN-9`'s `path` becomes `isekai/foundation/layout.py`, its `find` and `replace` unchanged; the standing mutants run once with no survivor | the mutated line moves; no line of logic changes | a run over a line range |
| [D8](#d8) | `docs/decisions.md` gains D69 and amends no decision | the rule a later change reads, and what this one leaves | folding the rule into D62 |

### D1

The listing functions and `rendered` are cut from `generate.py` and `run_view.py` and pasted into `layout.py` as they stand. `layout.py` adds `SIDECAR` to its import from `artifacts.py`, `Sequence` to its `collections.abc` import, and `FLOWS_DIR` and `load_flow` from `isekai.foundation.flow`. `flow.py` imports the refusal alone of the foundation, so `layout.py` and `flow.py` make no cycle, and `flow.py` is standard library only, which the entry point needs with site-packages off.

`rendered` keeps `flows_dir: Path = FLOWS_DIR` as its default and its signature, because `Wiring` has a flows root and the docstring says why.

### D2

`lacks` and `shortfall` read an approval, `duration` reads a record, `source_seeds` refuses with a remedy that names flows and `discard_render` deletes. None is a listing, so none moves, and `render.py` and `ui/library.py` keep importing what they import from the stage today.

### D3

`render_groups` lists a folder named by `str.isdigit`; the layout's own test, `_laid_out`, wants three ASCII digits. The two differ, and the move keeps the first as it is. A folder named by a superscript digit is a later change's question.

### D4

After phase 1 `generate.py` reads `rendered_seeds` and `render_groups` and binds them plain. It no longer reads `is_render`, `is_sidecar` or `sidecars`, so it binds them as `from isekai.foundation.run import is_render as is_render`, the form ruff reads as a re-export. `render.py`'s import of `sidecars` from the stage is the one reader of that bind; phase 2 switches it, and the bind goes.

`run_view.py` still reads `rendered` in `report`, so it imports it plain from `run.py`. A test that imports `rendered` from `run_view.py` still finds it.

### D5

After this change `run_view.py` and `compare_view.py` import nothing from `isekai.pipeline.generate`. `render.py` imports `duration` and `shortfall` from it, and `ui/library.py` imports `lacks`. The evaluator reads `rendered` from `isekai.foundation.run`, as it reads `OUTPUTS` and `Run` already.

### D6

`evaluation/record.py` imports `trackable` from the wiring. The evaluator's CLI tests patch the wiring's `REPOSITORY` and `DATA_ROOT`, which `trackable` reads at call time, so a move of `trackable` changes what they patch. `tests/test_layers.py` gives `evaluation` no layer, so no rule is added for it.

### D7

`FN-9` mutates the line `return path.suffix == suffix and is_seed(path.stem)`, which moves with `is_render`. Its `path` follows it; its `find` occurs once in `layout.py`. The mutants run once over the whole file `tests/mutants.json`, never over a line range, because no line of logic changes.

### D8

The text of D69, inserted after D68 in `docs/decisions.md`:

```markdown
### D69 · A render group's files are listed in foundation/layout.py, and a module above the pipeline reads the listing from the foundation

**`isekai/foundation/layout.py` lists a render group: `is_render`, `is_sidecar`, `rendered_seeds`, `sidecars` and `render_groups`, and `rendered`, which lists each flow's seeds by approval. A module outside the foundation reads them from `isekai.foundation.run`, never from the paid stage. The stage keeps what reads an approval or deletes: `lacks`, `shortfall`, `duration`, `source_seeds` and `discard_render`.**

- **Why:** `run_view.py`, `compare_view.py`, `render.py` and `ui/library.py` imported the paid stage to list a folder, and `review` may not import it. The names read foundation names alone. A move that re-binds changes no test.
- **Accepts:** a render's image and record are still named by hand where they are read. The other definitions of "rendered", in `review.py`, `surface.py` and `rendered_at`, stand. `render_groups` lists a folder by `str.isdigit`, where the layout's own test is three ASCII digits. The evaluator still imports `trackable` from the wiring. Reopen when a module builds a render's file name from the layout.
- **Made by:** `0174`.
```

## Tests

This change adds no test and removes none. The suite as it stands is the proof, and one mutant's `path` moves ([D7](#d7)).

| measure | count | command |
|---|---|---|
| files under `tests/` the change touches | `tests/mutants.json` alone | `git diff --name-only 0f170216 -- tests`, `0f170216` the commit the branch was cut from |
| end-to-end runs the change adds | none | `git diff --name-only 0f170216 -- tests/e2e` prints nothing |

No test is deleted or merged, so the table of removed tests is empty.

## Dependencies

None.

## Risks / Trade-offs

- **`layout.py` now imports `flow.py`.** The entry point imports with site-packages off. `flow.py` imports the standard library and the refusal alone; `tests/test_pipeline_cli.py` holds the guard.
- **A test patches `rendered_seeds` on the stage's module and on the library's.** Each module still reads its own binding, in `generate.py` and in `ui/library.py`, so both patches still reach code that runs.
- **An import the stage no longer reads fails the lint.** `OUTPUTS` and `is_seed` in `generate.py` go with the functions that read them; `ruff` names any other.
- **The *Imported by* tables are derived.** A hand edit is overwritten, so each phase that moves an import runs the deriver.
- **`sidecars` stays bound in `generate.py` for a while.** It is bound there until `render.py` switches; phase 2 removes the bind.

## Verdict

Ready to build. Each phase is a move the suite already holds, and no test is added.
