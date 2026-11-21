# The session plan — design

Move the plan of a render session to `isekai/interface/plan.py` and bind each name back in `render.py`. Verdict: feasible, in the phases of [tasks](tasks.md); the existing suite reads every moved name through `render`, so a moved byte fails a test.

## Context

`isekai/interface/render.py` holds the runner and the plan. The runner opens a GPU session, runs `generate` per flow and keeps the record. The plan decides what the session would do: `load_timing` reads `config/render.json`, `estimate` and `estimated` turn recorded durations into a limit, `short` finds what each approval lacks, `edits_of` reads the pending edits, and `Quote` carries the result to the page.

The plan is read here: `_session` and `quote` in `render.py`, `isekai/interface/ui/routes/rendering.py` (`render.Quote`, `render.Short`, `render.short`, `render.edits_of`, `render.Edits`), and `isekai/interface/verbs/edits.py` (`pending_edits`). `tests/test_render.py`, `tests/test_edit_session.py` and `tests/test_ui_api.py` read the names as `render.<name>`.

Tests patch a name the plan's callers read: `monkeypatch.setattr(render_module, "load_timing", …)` in `tests/test_ui_api.py`, and `monkeypatch.setattr(render, "session_id", …)` in `tests/test_render.py`. `quote` reads the first and `Record` the second, as globals of `render`.

```
before                              after
render.py                           render.py  ── session, quote, Record, _limit, _asked …
  session · quote · Record            │  from plan import <each name>
  timing · estimate · short           ▼
  edits · Quote · Line              plan.py  ── timing, estimate, short, edits, Line, Quote
```

## Goals / Non-Goals

- Goal: the timing, the estimate, the work, the edit queue's reading, what each approval lacks and the quote's data are in `plan.py`, unchanged.
- Goal: each moved name stays importable from `isekai.interface.render`, so no test, route or verb import changes.
- Goal: `quote` and `Record` read the names the tests patch as globals of `render`.
- Non-goal: a change to a line, a figure, a message or a parameter of the moved code.
- Non-goal: a decision in force, a scenario, a spec delta, or any file under `ui/`, `tools/` or `evaluation/`.
- Non-goal: a change to a ratchet row of `tests/test_ratchets.py`. `render.py` stays over the long-file ceiling until the requests leave it.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `isekai/interface/plan.py`, importing nothing of `render.py` | the plan reads folders and config, no process; `render.py` imports it, so the reverse would close a cycle | the foundation, which cannot read `Wiring`; `boundary/gpu.py`, which is not the plan's home (Q311) |
| [D2](#d2) | The code moves unchanged, and each name is bound back in `render.py` | the suite and the routes read the names on `render`; no import in `tests/` changes | repointing the readers |
| [D3](#d3) | `quote` and `Record` stay in `render.py`; `Quote`, the data `quote` builds, moves | the patched names are read by `quote` and `Record` as globals of `render`, and a patch of a name `plan.py` reads would not reach it | `Record` out, or `quote` with the timing passed in, which change a signature (Q311) |
| [D4](#d4) | `RENDER_CONFIG`, `RECENT` and `FLOOR_S` move with the code that reads them; `render.py` also keeps `HOLD_SECONDS` | `plan.py` cannot import `render.py`; `_limit` stays and reads the bound `FLOOR_S`; `tests/test_render.py` reads `render.HOLD_SECONDS` | `FLOOR_S` left in `render.py`, which `estimate` cannot read |
| [D5](#d5) | The standing mutant `RE-1` names `isekai/interface/plan.py` | a mutant is found by its path and its exact text, which move with `recent_edits` | a new mutant, or leaving the entry stale |

### D1

`plan.py` imports what the moved code reads from the standard library, `isekai.boundary.pod_start`, `isekai.foundation`, `isekai.interface.wiring` and `isekai.pipeline`. It imports no module of `isekai.interface` but `wiring`, so `tests/test_layers.py` finds no new edge a layer rule refuses.

### D2

A name `render.py` reads is imported plainly. One it does not read is imported `X as X`, the form `record_running` takes there, one statement each, with a comment that it moved to `plan.py` and stays importable from `render`. Docstrings, comments and bodies move as they are.

### D3

After the move `quote` calls `load_timing`, `short`, `edits_of` and `estimated`, and returns `Quote`, each a name bound in `render.py`. `_session` is as it was. A test that patches `load_timing` on `render` therefore still changes what `quote` reads.

### D4

`FLOOR_S` is `HOLD_SECONDS + 300`, so `plan.py` imports `HOLD_SECONDS` from `isekai.boundary.pod_start`. `render.py` imports `HOLD_SECONDS as HOLD_SECONDS` so a ruff fix does not drop the import the test reads. The mutant `CL-3a` finds `if asked < FLOOR_S:` in `_limit`, which stays.

### D5

`RE-1` finds the sort over `duration_of` in `recent_edits`. It occurs once in `plan.py`. Every other entry that names `render.py` finds text in code that stays.

## Names

What moves, in the order `plan.py` holds it. Phase 1 writes the first group; phase 2 appends the second after it.

| group | names | read by outside `plan.py` |
|---|---|---|
| 1 · constants | `RENDER_CONFIG`, `RECENT`, `FLOOR_S` | `FLOOR_S`: `_limit`, `tests/test_render.py` · `RECENT`: `tests/test_render.py` |
| 1 · timing | `Timing`, `load_timing` | `load_timing`: `quote`, `_session`, `ui/jobs.py`, tests · `Timing`: `tests/test_render.py` |
| 1 · estimate | `Estimate`, `recent`, `recent_edits`, `estimate`, `Work`, `estimated` | `estimated`: `quote`, `_session` · the rest: `tests/test_render.py` |
| 1 · edit queue | `Edits`, `edits_of`, `edit_records`, `pending_edits` | `Edits`, `edits_of`: `_session`, `routes/rendering.py`, `tests/test_edit_session.py` · `pending_edits`: `verbs/edits.py` |
| 2 · lines | `Line` | `_session`, `_asked`, `_requested` and `_rendered` of `render.py` |
| 2 · short | `NOTHING_SHORT`, `Short`, `_plan`, `_images`, `short`, `_unready` | `short`, `_plan`, `_images`: `quote`, `_session` · `Short`, `short`: `routes/rendering.py` · `NOTHING_SHORT`: tests |
| 2 · quote data | `Quote` | `quote`, `routes/rendering.py` |

Stays in `render.py`: `quote`, `Record`, `Records`, `Steps` and what 0196 binds back, `_limit`, `run_ids`, `Request`, `parse_request`, `in_session_sources`, `again`, `without_flags`, `_session`, `_asked`, `_requested`, `_edit_argv`, `_rendered` and the runner.

## Tests

No test is added, changed or removed, and no end-to-end run is added: the move is verbatim, and the suite reads each moved name through `render`. The one file under `tests/` that changes is `tests/mutants.json`, by one `path`.

| measure | command | before | after |
|---|---|---|---|
| tests in the render file | `git grep -c -e "^def test_" -- tests/test_render.py` | `tests/test_render.py:69` | `tests/test_render.py:69` |
| tests in the edit-session file | `git grep -c -e "^def test_" -- tests/test_edit_session.py` | `tests/test_edit_session.py:25` | `tests/test_edit_session.py:25` |

The proof is the suite, the standing mutants of `tests/mutants.json`, and `tests/test_ratchets.py`, which holds that `render.py` is still listed and its patched names are still read. No test is deleted or merged, so no `I16` table is due. A tool-run mutation over the moved lines is not planned: the brief's acceptance names the standing mutants alone.

## Dependencies

None.

## Risks / Trade-offs

- A moved dataclass changes its `__module__`. Nothing reads it: no test or route reprs a `Timing`, `Line` or `Quote`, and `shapes.py` names none.
- A name nobody imports through `render` is still bound back, so a later version removes a binding on its own evidence, never by accident.
- `render.py` falls under its former size but stays over the long-file ceiling at the cut; if it did not, `test_no_long_file_is_unlisted` would name the stale row and the build would halt on it.
- The quote's price and the session's limit come from the moved code. The existing figures in `tests/test_render.py` hold them; nothing here adds a path to money.

## Verdict

Feasible. Each phase ends with its tests passing and `render.py` still importing.
