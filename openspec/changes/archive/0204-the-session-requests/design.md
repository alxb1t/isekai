# The session requests — design

The group of `render.py` that parses a render's requests and builds its argv moves to `isekai/interface/requests.py`, the wide signatures of `_asked` and `Record.__init__` narrow, and the documents say what is true. Verdict: ready to build, in the phases of [tasks](tasks.md); the suite reads every moved name that has a reader through `render`, so a moved byte fails a test.

## Context

`isekai/interface/render.py` holds the runner, the session's record and the **group**: `REQUEST`, `Generate`, `Request`, `parse_request`, `in_session_sources`, `again`, `without_flags`, `_taken`, `run_ids`, `_asked`, `_requested` and `_edit_argv`. The group reads the operator's `<flow>=<count|source>` arguments, plans each request's `Line`, and builds the retry command and the `edit --pending` argv. It calls nothing that stays in `render.py`, and no test patches a name of it.

Outside readers reach a group name through `render`: `ui/jobs.py` and `tests/test_ui_jobs.py` import `without_flags`, and `ui/routes/rendering.py` and `tests/test_render.py` call `render.run_ids`. `quote`, `run_session` and `_session` read the rest as globals of `render`. `_asked` and `Record.__init__` are listed wide functions: `_asked` has one call, in `_session`, and no test calls either past its fourth positional parameter.

The change is cut on the base the versions before it leave. The session plan moves `Line` and `Edits` to `isekai/interface/plan.py`, which the group reads, and the child lines' declaration leaves `_edit_argv` called with `ARGUMENT` of `isekai/interface/progress.py`; the function itself is as it was. A task checks that `plan.py` holds both names before anything moves.

```
before                              after
render.py                           render.py ── runner, Record, quote, _session, _rendered
  runner · Record · quote             │  imports each name it reads
  the group · _session · _rendered    ▼
                                    requests.py ── the group, imports plan.py,
                                                   the foundation, compare_view, wiring
```

A patch meets each condition of [CONTRIBUTING](../../../CONTRIBUTING.md): no format version moves; no behaviour is fixed; no verb or flag is deprecated; and no argv byte, refusal text or record changes for the same inputs.

## Goals / Non-Goals

- **Goals:** the group is in `requests.py`, unchanged; each name `render.py` or an outside reader needs stays importable from `render`; `render.py` leaves the long files; `_asked` and `Record.__init__` leave the wide functions; the principles name why `_session` and `_rendered` stay listed.
- **Non-Goals:** one function for the free pass and the paid loop; a default for a keyword; `quote` or `Record` leaving `render.py`; a decision in force, a scenario, a spec delta, or any file under `ui/`, `tools/` or `evaluation/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `isekai/interface/requests.py` holds the group unchanged and imports `plan.py`, the foundation, `compare_view` and `wiring`, never `render.py` | Q331: no test patches a name of the group, it calls nothing that stays in `render.py`, and `render.py` imports it, so the reverse would close a cycle | leaving it in `render.py`, which keeps the file long; a package, for one module |
| [D2](#d2) | `Generate`, `parse_request`, `in_session_sources`, `again`, `_taken`, `run_ids`, `_asked` and `_edit_argv` are imported plainly in `render.py`, and `without_flags` is bound back as `without_flags as without_flags` | Q331: `render.py` reads the names it imports plainly; `ui/jobs.py` and a test read `without_flags` through it and `render.py` does not | repointing the readers of `without_flags`, which edits a test; binding `REQUEST`, `Request` and `_requested`, which nothing reads |
| [D3](#d3) | `_asked`'s `generate` and `Record.__init__`'s `planned`, `others` and `order` become keyword-only | Q332: no test passes either function a positional past its fourth, so the call in `_session` is the only one edited | a default for each, which changes what a call may omit |
| [D4](#d4) | `_session` and `_rendered` keep their rows, and the principles name each with its reason; no batch function is written | Q333: the free pass and the paid loop differ in their wiring, flags, server place and failure, a helper buys a row at the risk of the argv's bytes, and a queue of work appended after each paid line reshapes the loop | one function for both passes, which this version does not take |
| [D5](#d5) | The move phase also re-keys `_asked`'s wide row to `requests.py`, removes `render.py`'s long-file row and derives the *Imported by* tables | C32: the ratchet and `tests/test_docs.py` read a row naming the old place as red, so the move cannot be green without them | the brief's phase order, which ends the move on a red gate |
| [D6](#d6) | The standing mutants in `_asked`, `CL-4a` and `CL-4b`, name `isekai/interface/requests.py` | Q331: a mutant is found by its path and its exact text, which move with `_asked` and stay as they are | a new mutant, or leaving the entries stale |

### D1

`requests.py` opens with a docstring saying it holds the requests a render names and the argv `generate` and `edit` run with, and that it never imports `render.py`. It imports `re`, `shlex`, `Callable`, `Mapping`, `Sequence`, `dataclass`, `Path`, `Refusal`, `Run`, `command`, `render_groups`, `rendered_seeds`, `runs_in`, `load_flow`, `COLLECTION_PHOTOS`, `Wiring`, `Edits` and `Line`, each from where `render.py` took it, and `Edits` and `Line` from `isekai.interface.plan`. The names follow in the order `render.py` has them, with docstrings, comments and bodies as they are, so `CL-4a` and `CL-4b` find their text at the same indentation.

`tests/test_layers.py` counts lazy imports and refuses a cycle inside a layer. `requests.py` reads only `plan.py` and `wiring.py` of its own layer, and neither reads it, so no edge is new.

### D2

`render.py` imports the eight plainly because it reads them: `Generate` as an annotation in `run_session`, `_session` and `_rendered`, `run_ids` in `quote` and `_session`, and the rest in `_session` and `run_session`. `without_flags` is read only by `again`, which has left, so a ruff fix would drop a plain import. It is bound as `without_flags as without_flags`, once, under a comment that `ui/jobs.py` and a test import it from here, the form `record_running` takes in the same file.

`REQUEST` is read by `parse_request`, `Request` by the group alone, and `_requested` by `_asked`; none is bound back.

### D3

`_asked` ends `verb: Sequence[str], *, generate: Generate`, so its positional parameters fit the ratchet's ceiling. `Record.__init__` ends `asked: Mapping[str, int], *, planned=(), others=(), order=()`. The product call in `_session` passes `planned=` and `others=`, and already passes `order=`. The tests' calls pass the folder, the name, the limit and the asked images, and at most `order=`.

### D4

The bullet is added to *Free work first* of `docs/principles.md`, whose free pass `_session` runs and whose paid loop `_rendered` runs. It reads:

```
- **Known breaks:** `interface/render.py`'s `_session` and `_rendered` are the free pass
  and the paid loop, a long and a wide function each. The two differ in their wiring,
  their flags, where the server sits in the argv and what a failure does: the free pass
  stops at the first, the paid loop goes on. One helper for both would save a row and
  put the argv's bytes at risk, and a queue of work appended after each paid line would
  reshape the loop.
```

`tests/test_principles.py` reads one *Held by* bullet a principle and runs that bullet to the next top-level bullet, so a bullet after it breaks nothing.

### D5

At the end of the move, `render.py` is under the long-file ceiling, so its row of `tests/test_ratchets.py` is red until it goes, and `FILE_ROWS` is set to the rows left, whatever they are when the phase runs. `_asked`'s row keeps its number and moves to `isekai/interface/requests.py::_asked`, and the keyword phase then deletes it. `requests.py` is a module the *Imported by* table of `isekai/interface/README.md` must list, so its row is added and `tools.derive_imported_by` fills it in the same phase.

### D6

`CL-4a` finds `    if not ids:\n        photos = shlex.quote` and `CL-4b` finds `        if request.by_count or late:\n            continue`. Each occurs once in `requests.py`, and `_asked` moves with its indentation.

## Tests

No test is added, changed or removed, and no end-to-end run is added: the move is verbatim and the suite reads each name that has a reader through `render`. The files under `tests/` that change are `tests/test_ratchets.py`, by its rows and their counts, and `tests/mutants.json`, by the `path` of `CL-4a` and `CL-4b`. No test file is deleted or merged, so no `I16` table is due.

| measure | command | at the cut | after |
|---|---|---|---|
| tests in the render file | `git grep -c -e "^def test_" -- tests/test_render.py` | `tests/test_render.py:69` | the same |
| tests in the edit-session file | `git grep -c -e "^def test_" -- tests/test_edit_session.py` | `tests/test_edit_session.py:27` | the same |
| tests in the ratchet file | `git grep -c -e "^def test_" -- tests/test_ratchets.py` | `tests/test_ratchets.py:15` | the same |

The proof is the suite, the standing mutants of `tests/mutants.json`, and `tests/test_ratchets.py`, `tests/test_layers.py` and `tests/test_docs.py`. A tool-run mutation over the moved lines is not planned: the brief's acceptance names the standing mutants alone, and a survivor would want a test, which the acceptance forbids.

## Dependencies

None.

## Risks / Trade-offs

- **`plan.py` lacks `Line` or `Edits`** → the versions before this one did not land as cut: a **HALT CHECK** stops the build before a line moves.
- **`render.py` stays over the ceiling after the move** → its row cannot go: a **HALT CHECK** stops the build and a rescue reads what the plan's move left in the file.
- **A dead import survives, or a live one goes** → `ruff check` and the suite name it; each name `render.py` still reads is imported by [D2](#d2).
- **A keyword-only parameter breaks a call** → the product call is edited in the same task, and no test passes either function a positional past the parameters named in [D3](#d3).

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the move with its ratchet and its tables, the keywords, then the documents.
