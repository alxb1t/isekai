# The library's names — design

One new module, `isekai/foundation/library.py`, holds the collection's names and the session's read side; every name is re-bound at its old home. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`isekai/interface/ui/library.py` is 886 lines. It holds the constants `VARIABLE`, `DEFAULT`, `RUNS`, `LOG` and `CACHE`, `root`, `is_collection`, `listed`, `collection` and the session's read side (`running`, `render_running`, `session`, `_session`). It imports `record_running` from the render verb and `SOURCES` from the importer.

`render.py` holds `UNSUPPORTED`, which `Record.open` also reads, and `record_running`, which takes its lock as `fcntl.flock` through the module. `compare_view.py` holds the names of a collection's folders, and `render.py` imports one of them.

The foundation has no `library.py`. Its rule is that imports point only down, held by the layers' test. A test imports the run directory's module with site-packages off the path, so the new module stays on the standard library and the foundation.

```
before                                    after
foundation/  (no library)                 foundation/library.py   names, root, is_collection,
                                                                  listed, collection, session reads
pipeline/importing.py   SOURCES           -> re-bound (plain)
interface/compare_view.py  two names      -> re-bound as COLLECTION_RUNS, COLLECTION_PHOTOS
interface/render.py     record_running    -> re-bound (import X as X); UNSUPPORTED read plain
interface/ui/library.py                   -> re-binds each name; imports no render verb
```

## Goals / Non-Goals

Goals: the names in the foundation; no importer changes; no file under `tests/` changes; the documents the move makes false amended in this diff.

Non-goals: see [proposal](proposal.md#not-in-this-change). Nothing is moved to bring `ui/library.py` under 800 lines.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | one module, `isekai/foundation/library.py`; its module scope imports the standard library and the foundation, `Run` from `isekai.foundation.run` | a pure move; the foundation imports nothing above it, and `SOURCES` and `UNSUPPORTED` are what the moved code read from above | a module for the collection and another for the session |
| [D2](#d2) | a name its old home still reads is imported plain; one it no longer reads is `import X as X` | fewer lines than an `__all__` block, and ruff reads the form as a re-export | `__all__` blocks |
| [D3](#d3) | `SOURCES` and `RUNS` keep their names; the module's docstring says which folder each is; `compare_view.py` re-binds them as `COLLECTION_PHOTOS` and `COLLECTION_RUNS` | a rename is not a move; `names.py`'s `SOURCES` is a flow's folder, told apart by its module | renaming either |
| [D4](#d4) | `record_running` keeps `import fcntl` and calls `fcntl.flock(...)`; `UNSUPPORTED` moves with it and `render.py` reads it plain | a test patches `flock` on the `fcntl` module and calls `render.record_running`; `from fcntl import flock` would leave that test passing while testing nothing | `from fcntl import flock` |
| [D5](#d5) | the long files' row of `ui/library.py` stays; the file ends near 804 lines | nothing more is moved to pass under; a move chosen for its line count is no move of a home | moving more out of the file |
| [D6](#d6) | the hand copies of `is_collection`'s test, `STAGING`, `Record`, `open_library`, `collection_runs` and the CLI's imports of the UI package stay | this version only moves; a switch is a change of code under test | switching a site |
| [D7](#d7) | the move is proved by the suite as it stands, by greps, and by one run of the standing mutants; no run over a line range | no line of logic changes and no mutant falls in a moved range | a mutation run per phase |
| [D8](#d8) | `docs/decisions.md` gains D68; the documents the move makes false are amended in the diff | a rule is a decision, and a reader finds the home by it | none |

### D1

The module holds, in this order: its docstring, the imports, the constants `VARIABLE`, `DEFAULT`, `RUNS`, `SOURCES`, `LOG`, `CACHE`, `UNSUPPORTED`, then `root`, `is_collection`, `listed`, `collection`, `record_running`, `running`, `render_running`, `session` and `_session`. The bodies move verbatim. `_session` moves with its callers, `running` and `session`, and is re-bound nowhere. The module is near 155 lines (est.).

### D2

Each re-bound name is plain or `X as X`. `ui/library.py` reads `CACHE`, `RUNS`, `SOURCES`, `VARIABLE`, `is_collection` and `listed`, so those are plain. It reads none of `DEFAULT`, `LOG`, `root`, `collection`, `running`, `render_running` and `session`, so those are `X as X`; tests and the routes reach them through the module (`library.root`, `library.running`), and `ui/jobs.py` imports `LOG` and `RUNS`. `importing.py` reads `SOURCES`, so its import is plain. `render.py` reads `UNSUPPORTED` and no longer reads `record_running`. Ruff's `I` puts each `as` import on its own line: `uv run ruff check --fix` orders them.

### D3

`compare_view.py` reads both names, so its imports are aliases that bind them. The comment above `COLLECTION_PHOTOS`, which cites D40, goes with the old name. The foundation module's docstring says `RUNS` is a collection's runs root and `SOURCES` its photographs' folder.

### D4

`errno` is read by `UNSUPPORTED` alone in `render.py`, so its import goes; `import fcntl` stays, since `Record.open` takes its lock there. The moved `UNSUPPORTED` and `record_running` take `errno` and `fcntl` in the new module. The new module never writes `from fcntl import flock`: a patch of `flock` on the `fcntl` module would miss it.

### D5

`tests/test_ratchets.py` lists `isekai/interface/ui/library.py` among its long files and checks the keys and the count alone. The file ends near 804 lines (est.), against a ceiling of 800. A file at 800 or fewer turns the ratchet red, because its row names an offender that no longer offends: task 2.4 holds that premise.

### D6

Out of the version, each for its own: see [proposal](proposal.md#not-in-this-change). The CLI's lazy imports of the UI package stay: `collection_runs` and `serve` need `trackable`, and `drop_thumbnails` the thumbnail cache, so none can be met from the foundation.

### D7

The greps in tasks 1.1–2.3 hold that `record_running` takes its lock through the module, that `render.py` defines it no more and that `ui/library.py` imports no render verb. The standing mutants run once, in task 3.4: no entry of `tests/mutants.json` sits in a moved range.

### D8

The text of D68, for `docs/decisions.md`, after D67 and before `## Infrastructure`:

```
### D68 · The collection's names and the session's read side are foundation/library.py, re-bound at their old homes

**`isekai/foundation/library.py` holds the library's folder names and a collection's, `root`, `is_collection`, `listed` and `collection`, and the read side of a collection's session records: `UNSUPPORTED`, `record_running`, `running`, `render_running` and `session`. Each name is re-bound at its old home, so no importer changes; a name the old home no longer reads is bound as `import X as X`. The module imports the standard library and the foundation, `Run` through `run.py`.**

- **Why:** the code read these names from above, `SOURCES` from the importer and `record_running` from the render verb, so nothing below the interface could meet a collection, and `ui/library.py` was a listed long file ([D56](#d56--size-and-patches-are-held-by-ratchets)). A move that re-binds changes no importer and no test.
- **Accepts:** `ui/library.py` stays a listed long file, at its row. `pipeline/importing.py` and `interface/verbs/library.py` keep their hand copy of `is_collection`'s test. `isekai/README.md`'s file list names no `foundation/library.py`, and no test holds that list. The CLI's imports of the UI package stay. Reopen when the base's seams lift them.
- **Made by:** `0173`.
```

The foundation README's *Files* row and *Imported by* row for `library.py` are added by hand and then derived, since the deriver fills only a row that exists. The foundation's role line in `ARCHITECTURE.md` and `docs/principles.md` gains the library's names. `isekai/README.md`'s file list stays.

## Tests

The change adds and removes no test and runs no end-to-end test. The suite as it stands is the proof, and the readers of a moved name stay bound.

| measure | value | command |
|---|---|---|
| tests added or removed, files under `tests/` changed | none | `git diff --name-only main...HEAD -- tests` prints nothing |
| end-to-end runs added | none | `git diff --name-only main...HEAD -- tests/e2e` prints nothing |

`I16` table: no test is deleted or merged.

| reader of a moved name | where | stays bound by |
|---|---|---|
| `render.record_running`, after a patch of `fcntl.flock` | `tests/test_render.py:1411` | `render.py` re-binds `record_running`; the moved body calls `fcntl.flock(` |
| a patch of `ui.library.root` | `tests/test_ui.py:508` | `ui/library.py` re-binds `root`; `ui/__init__.py` reads `library.root()` |
| `library.root`, `library.collection`, `library.listed` | `tests/test_ui_library.py:71-124` | the same re-binds |
| `library.CACHE` | `tests/test_ui_library.py:592` | plain import |
| `library.render_running`, `library.is_collection` | `isekai/interface/ui/__init__.py:47`, `:58` | re-binds |
| `render_running`, through the UI front | `isekai/interface/verbs/drafts.py:72` | `ui/__init__.py` as it stands |
| `library.running`, `library.session`, `library.is_collection`, `library.listed` | `isekai/interface/ui/routes/rendering.py:132-229` | re-binds |
| `library.collection`, `library.RUNS` | `isekai/interface/ui/surface.py:179-180` | re-bind, plain import |
| `LOG`, `RUNS` | `isekai/interface/ui/jobs.py:50` | re-bind, plain import |
| `COLLECTION_PHOTOS` | `isekai/interface/render.py:65` | `compare_view.py` re-binds it |

## Dependencies

None.

## Risks / Trade-offs

- `ui/library.py` may end at 800 lines or fewer, which turns its ratchet row red. The estimate is 804 ([D5](#d5)); task 2.4 halts the build there, because the plan has no other move to make.
- A re-bound name unused in its old home is read by ruff as a re-export only in the `X as X` form: a plain import of it fails `ruff check` with `F401`.
- Versions that each add a module importing `refusal.py`, `artifacts.py` or `run.py` edit the same derived row of the foundation README. The integrate step merges that by rule.

## Verdict

Ready to build. Phases: the collection, the session, the documents; each ends on a green gate.
