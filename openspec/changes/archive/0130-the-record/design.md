# The record — design

Whole outputs are pinned by a program that writes them and a test that re-derives them: the graphs, the run, the verbs' flags, the routes' answers and the child's done line. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The refactor that follows moves code between files, and the gate must say when an output moved. What it pins today, and what this change adds, by phase:

```
phase 1  the graphs   one flow's graph, by a digest        every flow's graph and the edit's, whole
phase 2  the run      twelve goldens, kept by hand         every path of one offline pass
phase 3  the verbs    no flag is pinned                    each verb's flags, walked from the parser
phase 4  the routes   no test requests some routes         each route without a child: status and shape
phase 5  the wire     a hand-typed line in each reader     the CLI's own line, fed to each reader
```

The change is built after `0129-the-refactors-rails` releases, and adds tests beside the guards that change writes. A task here names a function or a string, never a line.

## Goals / Non-Goals

Goals:

- An output the refactor may move is pinned whole, or by its structure where its text varies, and a test goes red when it moves.
- The files are written by one program, and a person re-derives them with one command.
- A reader of the child's lines is fed the line the CLI writes, not a copy typed beside the reader.

Non-Goals:

- No product file moves: no `.py` under `isekai/` or `evaluation/` changes, and no document is edited.
- No requirement, scenario, format version or decision of `docs/decisions.md` is added or amended.
- No route that needs a running child is recorded: Prepare, render, the session routes and the event stream.
- No test is deleted or merged.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The record is `tests/record.py`, run as `python -m tests.record`, writing `tests/record/*.json`; a test re-derives each file into a temporary directory and compares | the writer needs the suite's doubles, and tests reach tools, never the reverse | a tool under `tools/`; files kept by hand, as the goldens are |
| [D2](#d2) | One offline pass drives `isekai.interface.cli.main` verb by verb, over every flow, on a factory named by `ISEKAI_WIRING` | [D41](../../../docs/decisions.md#d41--the-test-seam-is-a-factory-named-in-the-environment) is the seam the browser tests use, and `--flow` repeats | calling the stages directly, which pins the stages and not the verbs |
| [D3](#d3) | The environment is set by a context manager inside `tests/record.py`, and no test patches a name of a module | the writer runs outside pytest, and a patch of a module's own names is a counted offender | `monkeypatch.setenv`, which the writer cannot use |
| [D4](#d4) | The run is pinned whole: a JSON file with its duration `0.0` and the pass's directory `<root>`, a PNG by its pixels, any other file by its bytes | the duration reads `time.monotonic`, an encoder's compression is a platform's, and the photograph is copied unchanged | digests of every file's bytes, which a zlib change turns red |
| [D5](#d5) | The verbs are pinned by structure: each flag, positional and exclusive group walked from the parser, a default inside the repository written repo-relative, no help text | argparse's help text follows the terminal's width, and the runs root is an absolute path into the checkout | the text of `--help`, which differs by terminal and Python patch level |
| [D6](#d6) | The routes are pinned by shape: the status, and the answer's keys with their types, never a value; a non-JSON answer by its media type | a value can carry a time, and an image's bytes are an encoder's | the answers whole |
| [D7](#d7) | Each route not left to a child has one call in an ordered table over the pass's library, and a test fails on a route no call covers | a route added later must be recorded before it ships | a list of routes kept apart from the app |
| [D8](#d8) | The CLI's done lines are recorded, and the session's, the cell's and the job's readers are fed those lines | the one literal carried across the child's wire is typed twice today, so one side moves alone | a constant imported by the CLI, which would move a product file |
| [D9](#d9) | A file of `tests/record/` changes only when a person runs the writer; a red re-derive prints the command and the files that differ | a test that rewrites what it reads can never be red | an `--update` flag on the test |
| [D10](#d10) | The phases rate `moderate`; the build runs on Sonnet 5.5 high and is converged on Codex checkers | fixtures and tables to place, in small functions with twins | — |

### D1

`tests/record.py` holds `FILES`, a mapping from a file's name to the function of the pass that returns its value, `derive(done)` returning each file's text by name, `write(directory)` and `main()`. A file's text is `json.dumps(value, indent=2, sort_keys=True)` and a newline. `recorded(name)` reads a committed file's JSON, for the tests that feed a reader.

`write` runs `offline` once in a temporary directory and calls `derive` on what it returns; a test does the same under `tmp_path_factory`. `derive` evaluates `FILES` in the order they were registered.

```
python -m tests.record ──▶ main() ──▶ write(tests/record/) ──▶ offline(tmp) ──▶ derive(done) ──▶ FILES
tests/test_record.py   ──▶ offline(tmp_path) ──▶ derive(done) ──▶ compared with tests/record/<name>.json
```

### D2

`offline(root)` runs the pass under `root` and returns what the files read.

```
ada.jpg ─▶ caption ─▶ tag                          the photograph's verbs name no flow
        ─▶ assign ─▶ sheet ─▶ review ─▶ approve ─▶ generate --seed 42
                       each over every flow, `--flow` repeated
then:  request an edit of the first flow's render ─▶ edit --pending <run>/<flow>
```

The photograph is `jpeg_bytes(1200, 900)`, written to `lib/<collection>/sources/` and run under `lib/<collection>/runs/`, so the routes of [D7](#d7) read a copy of the same library.

The factory `tests.record:wiring` returns `tests.e2e.wiring.fake`'s wiring with the pass's client in place of its own. The client is a module variable of `tests/record.py`, since the factory is called with the runs root alone.

The render client is a `FakeComfyClient` answering a flat PNG of the colour `SKIN`, a square of the side `SIDE`, the render of `tests/test_edit_session.py`'s `_request`; the edit client is a `RecordingComfyClient` answering a flat crop. The render's graphs are the render client's submissions, in the order of `FLOWS`; the edit's graph is the last submission of the edit client.

The edit request restates `tests/test_edit_session.py`'s `_request` without its render: it reads the pass's own render of the first flow, `outputs/001/42.png`, and writes a composite with the tattoo's square multiplied in under `root`, outside the runs, then calls `request` with `seed=5` and `random.Random(1)`.

### D3

`using(client)` is a context manager that sets `ISEKAI_WIRING` to `tests.record:wiring` through `os.environ` and the client in the module variable, and restores both. The pass never uses `monkeypatch`, so `python -m tests.record` runs where pytest does not.

### D4

`run.json` maps each path under the runs root, relative to it and sorted, to its entry.

| file | entry | because |
|---|---|---|
| `*.json` | `{"json": body}` with every `duration` set to `0.0` and each string holding the pass's directory rewritten to `<root>`, the resolved spelling first and the given one after | the render's and the edit's duration read the clock; a path is the machine's, and macOS spells a temporary directory under `/var` and under `/private/var` |
| `*.png` | `{"pixels": sha256}` of the mode, the size and the decoded pixel bytes | the pixels are the product; the compression is the platform's |
| any other file | `{"bytes": sha256}` of the file | the photograph is copied unchanged, and its digest names its run |

### D5

`verbs.json` maps each verb to its positionals, its options and its exclusive groups. An argument is `{dest, flags, nargs, required, default, choices, type, metavar, action}`, `type` and `action` by name.

A default that is a `Path` under the repository is written relative to it. One outside the repository is refused, because it names a machine. No help text is read.

### D6

`shape(value)` returns a mapping's keys with the shape of each value, a list as its first element's shape in brackets (`[]` when empty), and any other value as its type's name: `str`, `int`, `float`, `bool`, `null`. `routes.json` maps `"<METHOD> <template>"` to `{"status": n}` plus `"shape"` for a JSON answer or `"media_type"` for another. A key that holds data, such as a digest, is a value a refactor does not move, and stays.

### D7

`CALLS` is an ordered list of `Call(method, template, fill, body)`: `template` is the route as `create_app` declares it, `fill` the mapping that fills its braces, `body` the request's JSON or files. Both take `done` (the collection, a run's digest, a flow, a seed) and `seen`, the answers of the calls before it by their keys, since a staging's id is the answer of the call that opened it.

The calls go to a `TestClient` of `create_app` over a copy of the pass's library, made under `root`, so the calls change nothing `run.json` reads. The app is built as `tests/test_ui_api.py`'s `_client` builds one, on `tests.e2e.wiring.fake`'s wiring, so the billing check has the browser tests' gpunit stand-in.

The order is the run order: a call that reads what another creates goes after it, and a call that deletes goes after the calls that read what it deletes. A call that reads a staged file, its thumbnail or its delete follows a poll of the file's `GET` until it answers 200, with a deadline, since an upload is read on a thread. Each call that consumes a staging — the commit, a tattoo's creation, the deletes — has a staging of its own. `CHILD_ROUTES` names the routes left to the version that hardens the jobs, each as `"<METHOD> <template>"`:

| route | why it waits |
|---|---|
| `POST /api/c/{collection}/prepare` | runs a child |
| `POST /api/render` | runs a child |
| `GET /api/sessions/running` | reads a running render |
| `GET /api/c/{collection}/sessions/{name}` | reads a render's record |
| `GET /events` | streams a running job |

A test lists the routes of `app.routes` that answer a method, which leaves out the mount of `/assets`, and fails on one that is in neither `CALLS` nor `CHILD_ROUTES`, and on a recorded status of 500 or more.

### D8

`wire.json` holds the lines the CLI prints under `--progress json`: the sheet's done line and the render's done line, each as the pass's run prints it. The sheet's line is read by `cell_event` and by `_Job.complete`, and by `progress_line`, which the session reads it through; the render's line is read by the session's `_Images`. A reader's test loads the line with `recorded("wire")`, so the CLI and its readers cannot move apart.

### D9

`differing(directory, derived)` returns the names whose committed text is not the derived text, a missing file and an extra file included. The re-derive test asserts it empty, with the message `run uv run python -m tests.record and read the diff`.

### D10

Each phase ends on a green `make check`. The build is Sonnet 5.5 high whole, as the series' other versions are.

## The files

What each record file holds, and the phase that writes it.

| file | holds | phase |
|---|---|---|
| `tests/record/graphs.json` | `{"flows": {<flow id>: <graph>}, "edit": <graph>}`, each graph as submitted | 1 |
| `tests/record/run.json` | the run's every path, by [D4](#d4) | 2 |
| `tests/record/verbs.json` | each verb, by [D5](#d5) | 3 |
| `tests/record/routes.json` | each recorded route, by [D6](#d6) | 4 |
| `tests/record/wire.json` | the sheet's and the render's done lines | 5 |

## Tests

Counts are those of `uv run pytest --collect-only -qq --ignore=tests/e2e` over the files below, at the base, and the same command prints them after. Each case of the re-derive test counts as a test.

| file | tests before | tests added |
|---|---|---|
| `tests/test_record.py` | 0, the file is created | 17 |
| `tests/test_resume.py` | 22 | 1 |
| `tests/test_progress.py` | 3 | 1 |
| `tests/test_ui_jobs.py` | 33 | 1 |

The tests added are the ones the tasks name. `tests/test_record.py` holds the pass, the re-derive over each file with its twin, a test of each function of the writer, the route guards and no more. The re-derive of each file is the guard, and `differing`'s test is its twin.

Each new test carries one `spec_exempt`, in the form the exemption check holds: a guard `structural: <the rule it holds>`, a twin `structural: twin of <the guard's name>`, and a test of a function `structural: <what the function does>`. `test_a_second_pass_over_the_same_runs_moves_nothing` binds `cli:resume:second-pass-is-inert`.

| layer | added | removed | command |
|---|---|---|---|
| unit and integration | the sum of the column above | 0 | the command above |
| end-to-end | 0 | 0 | `uv run pytest --collect-only -qq tests/e2e` |

No end-to-end test is added (`T1`): the pass runs the CLI in process, and the routes run on a `TestClient`. The tests added to existing files extend files that reach the same state (`T2`).

Each reader's test is a unit test of the reader over a recorded line, and each twin is a unit test of its guard, never a browser test (`T6`). No test is deleted or merged, so there is no table of what carries each one's assertions (`T5`).

Added with no test of their own: `tests/record.py` and the files it writes, `tests/record/graphs.json`, `tests/record/run.json`, `tests/record/verbs.json`, `tests/record/routes.json` and `tests/record/wire.json`. Read and not edited: `tests/test_edit_session.py` for the edit request, `tests/test_ui_api.py` for the app's client and `tests/e2e/wiring.py` for the wiring the pass and the app's client build on.

## Dependencies

None.

## Risks / Trade-offs

- A record file holds the pixels of a PNG and the bytes of a JPEG that Pillow wrote for the photograph, as `tests/golden/run.json` does. A different JPEG encoder on Linux turns the re-derive red, and a patch re-derives it at once.
- A route's answer whose keys depend on the clock or the machine would make the record flaky. The build reads each recorded shape before it keeps the file, and a key that varies is a halt, never a normalisation of the product.
- A comment, docstring or exemption reason in `tests/record.py` that cites a version or a change id is red under the history guard of the series' first versions. A test names what it holds, never when it was added.
- The pass runs once per test session as a fixture, so the re-derive over each file costs one pass. A pass that grows slow gets the `slow` marker, which `make check` skips, and the file's own phase keeps a fast case.
- `tests/record.py` and the directory `tests/record/` share a name. The module wins, because the directory holds no `__init__.py`, and `tests/record/` holds data alone.
- The recorded routes answer on doubles. A route whose answer differs on the real wiring is outside this record, as every browser test's is.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). No decision of `docs/decisions.md` is added or amended, and no requirement is touched.
