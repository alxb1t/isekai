# The serve seams — design

What a test replaces in `serve` and in the bundle's build becomes a keyword parameter that defaults to what the product uses. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The tests patch names of the UI package's `app.py` and `bundle.py`, and the ratchet lists a row for each ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)):

| module | the patched name | where it is read | the test that patches it |
|---|---|---|---|
| `isekai.interface.ui.app` | `run` | `serve`, `isekai/interface/ui/__init__.py` | `test_serve_returns_130_for_keyboard_interrupt` of `tests/test_ui.py` |
| `isekai.interface.ui.bundle` | `BINARY`, `BUILD_TIMEOUT` | `ensure_built`, `isekai/interface/ui/bundle.py` | `test_a_build_that_does_not_finish_is_stopped_and_named` of `tests/test_ui.py` |

The same serve test also patches the library's `root` and `ensure_built` of `isekai.interface.ui`, which `serve` reads as well. `serve` has one caller, `run_ui` in `isekai/interface/verbs/library.py`, which passes `wired` and `port`, and `ensure_built` is called by `serve` alone, with no argument. The server's `run` is imported inside `serve` because that import is the only line that needs a web framework, which the `-S` guard in `tests/test_pipeline_cli.py` holds.

## Goals / Non-Goals

Goals:

- The rows of `isekai.interface.ui.app` and `isekai.interface.ui.bundle` leave `PATCHED_MODULES`, and `PATCHED_ROWS` is set to 19.
- Each test passes a fake where it patched, and no assertion changes, so `asked == ["root", "ensure_built"]` still holds.
- D61 says what the decision now covers, and its *Accepts* is closed.

Non-goals:

- A `Wiring`-style object or a class for the collaborators: a parameter is the smallest seam that removes the row.
- The rows that stay, named in [the proposal](proposal.md#not-in-this-change).
- Any new decision: D61 is amended, as its own *Accepts* foresaw.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `ensure_built` takes `binary` and `timeout`, keyword-only, defaulting to `BINARY` and `BUILD_TIMEOUT` | a caller that passes nothing runs the product's build, and the constants stay where `tests/e2e/conftest.py` reads about them | a module-level hook the test sets, which is the patch again |
| [D2](#d2) | `serve` takes `root` and `ensure_built` as callables defaulting to `library.root` and `ensure_built`, and `run` as a callable defaulting to `None` | the serve test's stand-ins record that they were asked, so a callable keeps its assertion; the server's `run` cannot be a default, because its module is imported inside `serve` | `root: Path`, which cannot record that it was asked; `run=` defaulting to `app.run`, which imports a web framework at module scope |
| [D3](#d3) | a phase for each seam, each ending with its row gone, then a phase for the decision | the tests and the row of a seam cannot be green apart, since a row with no patch is stale; each phase is green alone | the brief's steps, the seams, the tests, the ratchet and the documents, a phase each: the phase that switches the tests ends with a stale row |
| [D4](#d4) | D61 is amended in place, and the version adds no decision | D61 names this reopening, and a decision in force is edited where it lives | a new decision, which would retell D61 |

### D1

`ensure_built(source: Path = SOURCE, *, binary: str = BINARY, timeout: float = BUILD_TIMEOUT)`. The body reads `binary` where it read `BINARY` and `timeout` where it read `BUILD_TIMEOUT`, in the `shutil.which` call, the argv of `subprocess.Popen`, `build.communicate` and each message. The messages print the same text for the defaults, and a whole-number `timeout` prints as `3`, so `"3 seconds"` still reads.

### D2

`serve(wired, *, port, root=library.root, ensure_built=ensure_built, run=None)`, `root` and `ensure_built` typed `Callable[[], Path]` and `run` typed `Callable[..., None] | None`. The body calls `root()` where it called `library.root()`, and its call of `ensure_built()` reads the parameter. It imports `create_app` and `run as run_app` from `isekai.interface.ui.app` where it imported `run`, and serves with `(run or run_app)(app, host=HOST, port=port)`. The module keeps its imports of `ensure_built` and `library`, which the defaults read.

### D3

The order is the bundle first, `serve` second: `serve`'s default for `ensure_built` is the function the first phase changes, and the second phase leaves it as it is. The last phase holds the decision and the last green run, with the standing mutants.

### D4

The bold sentence of D61 says `serve` takes the library's root, `ensure_built` and the server's `run` the same way, and `ensure_built` takes the binary and the timeout; its *Accepts* is closed because no patched name of the server's `app.py` stands, and its *Made by* gains `0185`.

## Tests

The change adds and removes no test. It moves a fake from a patch to an argument, so the count of tests is the base's.

| measure | count | command |
|---|---|---|
| tests in `tests/test_ui.py` | 19 | `git grep -c -e "^def test_" -- tests/test_ui.py` |
| patches of `bundle` and `app_module` in `tests/test_ui.py`, before | 4 | `git grep -c -E "setattr\((bundle\|app_module), " -- tests/test_ui.py` |
| the same patches, after | 0 | the same command, which prints nothing |
| tests in `tests/test_ratchets.py` | the base's | none added or removed: the edit is to the rows of its tables, which `test_no_patched_module_is_unlisted` reads |
| end-to-end runs added | 0 | none: each test is a unit or an integration test at the lowest layer that holds it (`T1`) |

No test is deleted or merged, so there is no `I16` table. The patches of `ui.library`'s `_shrunk` and `_upright` in `tests/test_ui_api.py`, of `ui.events`'s `frame` and of `serve` in `tests/test_pipeline_cli.py` stay: they are rows this change leaves.

## Dependencies

None.

## Risks / Trade-offs

- A default binds when its function is defined, so a test that still patched `BINARY`, `BUILD_TIMEOUT`, `library.root` or `ensure_built` after its phase would run the real one. Each phase's `Verify:` finds the remaining patch.
- The first phase ends with `PATCHED_ROWS = 20` because the build of `0184-the-evaluator-seams` leaves it at 21. A base without that version fails the halt check of the first phase, which says so before an edit.
- A test that took `monkeypatch` for a patch alone keeps an unused fixture if it is not dropped. Both tests use `monkeypatch` for another call, so each keeps it.

## Verdict

Ready to build. Small phases, a seam and its row gone each, then the decision.
