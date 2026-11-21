# `interface/` — what an operator touches

The two front ends. The verb line, the composition behind them both, the
read-only account of a run, the comparison page of a collection, and the browser
surface for stage ③.
`isekai/__main__.py` stays at the package root because `runpy` pins that path; it
is a shim over `cli.py` and holds nothing else.

**`ui/` is a sibling of `cli.py` and `verbs/`, not a client of them.** Both reach
the pipeline the same way — `wiring_from()` and the stage functions, called
directly — so neither is privileged. The verb line imports `isekai.interface.ui`
inside `run_ui` and `run_discard` of `verbs/` and `_migrate` of `cli.py`, never at
module scope, and the UI imports no CLI module.

**A verb is a row of `verbs/`, declared once** ([D58](../../docs/decisions.md#d58--a-verb-is-declared-once-in-its-familys-module)).
`cli.py` imports names from `verbs/__init__.py` alone; a module of `verbs/` imports its siblings by their own name.

## Files

| file | does |
|---|---|
| `cli.py` | holds `ROWS`, builds the parser from each row's arguments, resolves the flows a verb was given against `flows/`, dispatches a row's run or per flow — `tag` and `caption` once per photograph, naming none — and reports every refusal together, or with `--progress json` a JSON line per item; it keeps `migrate` and `render`'s run, bound to `_dispatch_argv` |
| `verbs/__init__.py` | the package's front door: the rows, `_per_item` and the shared names `cli.py` reads |
| `verbs/runner.py` | the flow stages' runner: `_per_item` returns the work one identifier gets for a stage, `assign` or `show`, with a builder per stage and `assign`'s own work; the approve builder refuses a cancel beside a render session |
| `verbs/common.py` | `Verb`, the argument types and shared arguments, the reporter, and the run helpers every family reads |
| `verbs/library.py` | `import`, `compare` and `ui`: `import` composes `pipeline/importing.py`, `compare` writes the page, `ui` serves the library |
| `verbs/drafts.py` | `draft` and `discard`: `discard` deletes a render or an edit and each image's thumbnail, refusing beside a render session |
| `verbs/edits.py` | `ink` and `edit`, with `--pending`'s run |
| `verbs/session.py` | `render`'s arguments and its row; the run is `render.py`'s, bound in `cli.py` |
| `verbs/prepare.py` | `prepare` over cells, each photograph through `tag`, `caption` and its sheets in turn |
| `verbs/generate.py` | `generate`: assembles every prompt locally, then renders |
| `verbs/stages.py` | the arguments and rows of `assign`, `caption`, `tag`, `sheet`, `review`, `approve` and `show` |
| `wiring.py` | composes the modules — resolves the reader and the two taggers, with no flow, verifies the vocabulary before it is read, and builds the transport and the vocabulary and field-map thunks, with or without a parser |
| `drafting.py` | drafts a flow from an image for `draft` and the page — its own flow a revision, another from the image's approval, assigning a flow with no sheet and filling it from the source's tags first; and copies an approval across for `approve --from`, its sheet filled first |
| `render.py` | the `render` verb: finds what each approval lacks, less each `--without`, or takes the requests, assembles every prompt, estimates the session's limit and its quote, opens a GPU session through `boundary/gpu.py` stopping at that limit, waits for the endpoint, runs `generate` per flow, reports each step with `--progress json`, and writes the prose to the collection's log |
| `progress.py` | declares the lines a child prints and `--progress json`: the item, step and image lines, their stage, state and step names and the flag; holds `emit`, `progress_line`, `Steps` and `_Images`. **Imports the standard library alone** |
| `run_view.py` | the `show` verb: a run's artifacts, active versions, producers and failure records, and the names below a flow it does not read. Decides nothing |
| `compare_view.py` | the `compare` verb: one page of every run's photograph beside each flow's renders, written into the collection directory. Reads, decides nothing |
| `ui/__init__.py` | the `ui` verb: opens the library `ISEKAI_LIBRARY` names, sweeps import's staging, reads the offered flows, prints the address, serves until stopped, and `render_running` for the `discard` verb |
| `ui/library.py` | the library, its collections and each source × offered flow's stage, all read from folders, each source's not-cleaned mark, each approval's rendered seeds and the thumbnails in the library's `.cache/`; the collection's names, its session records' read side and a thumbnail's path, drop and digest are `foundation/library.py`'s, re-bound here (D68). **Imports no web framework**, which keeps it testable in the main suite |
| `ui/bundle.py` | builds the browser bundle when it is absent; refuses naming `npm install` rather than fetching |
| `ui/jobs.py` | Prepare and Render as jobs, a slot per kind, side by side: one `prepare` child, each photograph through `tag` → `caption` → its sheets, after a probe of the model server; `gpunit volume up` → `render` → `volume down` unless kept; Stop and server stop sending SIGINT |
| `ui/billing.py` | what may be billing, read from gpunit's records in `.gpunit/`: the pod alert, the window's quiet item and the band; gpunit asked at start, every half minute while needed, and on Check again |
| `ui/events.py` | the event stream: a snapshot on connect, then each `job`, `cell`, `billing` and `file` change, to every open page; the snapshot also carries each staging's files |
| `ui/surface.py` | what the routes share, as `Surface`: the folders, the wiring, the flows, the jobs, billing, imports, the broadcast, the shared vocabulary, the upload limit and the seams a test replaces (the file response, `save_draft`, `approve`, the precondition check and the draft lock), and the lookups every route makes over them. **Imports no web framework** |
| `ui/shapes.py` | each JSON answer of the hub, staging, images, vocabulary, review, tattoo, place and render routes as a `TypedDict`, `ANSWERS` keyed as the record is for the answers it records, and `UNRECORDED` for those it lacks, `Refused` and `DraftRefused` for the refusals, and `EVENTS` for the stream's events; a test holds each and no route reads it. A cell's stage, a job's state and kind and a file's state are the `Literal` of the module that writes them, and `ty` holds each write. **Imports no web framework** |
| `ui/routes/` | the hub, staging, images, sources, vocabulary, tattoo library, place, render and jobs, review, and events routes, each a class over one `Surface` with a `ROUTES` table of `Route` rows and a `mount(app, surface)` ([D59](../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface)); `table.py` registers a table on the app, `keys.py` and `common.py` hold what the resources share. They import FastAPI and are mounted by `ui/app.py` |
| `ui/app.py` | the guard on every request, the refusal handler, the catch-alls and the bundle's `index.html` for every other path; it takes the seams a test replaces and the jobs' factory, builds the `Surface`, mounts each resource of `ui/routes/` and imports uvicorn |

## Imported by

**Derived.** `uv run python -m tools.derive_imported_by` writes this table from the import graph of `tools/import_graph.py`, the one the layer guards read, and a test re-derives it. It names importers in `isekai/`, `evaluation/` and `tools/`, never a test.

| file | inside `isekai/` | outside |
|---|---|---|
| `cli.py` | `__main__.py` | — |
| `wiring.py` | `cli.py`, `plan.py`, `render.py`, `ui/__init__.py`, `ui/app.py`, `ui/library.py`, `ui/routes/place.py`, `ui/surface.py`, `verbs/common.py`, `verbs/drafts.py`, `verbs/edits.py`, `verbs/generate.py`, `verbs/library.py`, `verbs/prepare.py`, `verbs/runner.py` | `evaluation/record.py`, `tools/derive_field_map.py` |
| `drafting.py` | `ui/routes/reviewing.py`, `verbs/drafts.py`, `verbs/runner.py` | — |
| `render.py` | `cli.py`, `ui/jobs.py`, `ui/routes/rendering.py`, `verbs/edits.py` | — |
| `progress.py` | `render.py`, `ui/jobs.py`, `verbs/common.py`, `verbs/edits.py`, `verbs/generate.py`, `verbs/prepare.py`, `verbs/runner.py`, `verbs/session.py` | — |
| `run_view.py` | `verbs/runner.py` | — |
| `compare_view.py` | `render.py`, `verbs/library.py` | — |
| `ui/` | `cli.py`, `verbs/drafts.py`, `verbs/library.py` | — |
| `verbs/` | `cli.py` | — |

> The file is `run_view.py`; the **verb is still `show`**, and the entry-point
> tests pin it.

> `verbs/library.py` and `verbs/drafts.py` import `isekai.interface.ui` **inside
> `run_ui` and `run_discard`**, and `cli.py` inside `_migrate`, not at module
> scope. `tests/test_pipeline_cli.py` imports the entry point under `-S`, with
> site-packages off the path: a top-level import here would put FastAPI on
> `python -m isekai`'s import graph and turn that guard red for every verb.

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
