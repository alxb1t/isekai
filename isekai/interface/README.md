# `interface/` — what an operator touches

The two front ends. The verb line, the composition behind them both, the
read-only account of a run, the comparison page of a collection, and the browser
surface for stage ③.
`isekai/__main__.py` stays at the package root because `runpy` pins that path; it
is a shim over `cli.py` and holds nothing else.

**`ui/` is a sibling of `cli.py`, not a client of it.** Both reach the pipeline
the same way — `wiring_from()` and the stage functions, called directly — so
neither is privileged. The CLI imports `isekai.interface.ui` inside the handlers of
`ui`, `migrate` and `discard`, never at module scope, and the UI imports no CLI module.

## Files

| file | does |
|---|---|
| `cli.py` | parses a verb, resolves the flows it was given against `flows/`, dispatches per flow — `tag` and `caption` once per photograph, naming none — and `prepare` over cells, each photograph through both and its sheets in turn — and reports every refusal together, or with `--progress json` a JSON line per item; `import` and `assign` compose `pipeline/importing.py` and the run's own `assign`; `discard` deletes a render and its thumbnails |
| `wiring.py` | composes the modules — resolves the reader and the two taggers, with no flow, verifies the vocabulary before it is read, and builds the transport and the vocabulary and field-map thunks, with or without a parser |
| `drafting.py` | drafts a flow from an image for `draft` and the page — its own flow a revision, another from the image's approval, assigning a flow with no sheet and filling it from the source's tags first; and copies an approval across for `approve --from`, its sheet filled first |
| `render.py` | the `render` verb: finds what each approval lacks, less each `--without`, or takes the requests, assembles every prompt, estimates the session's limit and its quote, opens a GPU session through `boundary/gpu.py` stopping at that limit, waits for the endpoint, runs `generate` per flow, reports each step with `--progress json`, and writes the prose to the collection's log |
| `run_view.py` | the `show` verb: a run's artifacts, active versions, producers and failure records, and the names below a flow it does not read. Decides nothing |
| `compare_view.py` | the `compare` verb: one page of every run's photograph beside each flow's renders, written into the collection directory. Reads, decides nothing |
| `ui/__init__.py` | the `ui` verb: opens the library `ISEKAI_LIBRARY` names, sweeps import's staging, reads the offered flows, prints the address, serves until stopped, and `drop_thumbnails` and `render_running` for the `discard` verb |
| `ui/library.py` | the library, its collections and each source × offered flow's stage, all read from folders, each source's not-cleaned mark, each approval's rendered seeds, each collection's session records, and the thumbnails in the library's `.cache/`. **Imports no web framework**, which keeps it testable in the main suite |
| `ui/bundle.py` | builds the browser bundle when it is absent; refuses naming `npm install` rather than fetching |
| `ui/jobs.py` | Prepare and Render as jobs, a slot per kind, side by side: one `prepare` child, each photograph through `tag` → `caption` → its sheets, after a probe of the model server; `gpunit volume up` → `render` → `volume down` unless kept; Stop and server stop sending SIGINT |
| `ui/billing.py` | what may be billing, read from gpunit's records in `.gpunit/`: the pod alert, the window's quiet item and the band; gpunit asked at start, every half minute while needed, and on Check again |
| `ui/events.py` | the event stream: a snapshot on connect, then each `job`, `cell` and `billing` change, to every open page |
| `ui/app.py` | the endpoints, which `create_app` declares, and the bundle's `index.html` for every other path; the only module in the package that imports FastAPI or uvicorn |

## Imported by

**Derived.** `uv run python -m tools.derive_imported_by` writes this table from the import graph of `tools/import_graph.py`, the one the layer guards read, and a test re-derives it. It names importers in `isekai/`, `evaluation/` and `tools/`, never a test.

| file | inside `isekai/` | outside |
|---|---|---|
| `cli.py` | `__main__.py` | — |
| `wiring.py` | `cli.py`, `render.py`, `ui/__init__.py`, `ui/app.py`, `ui/library.py`, `verbs/common.py`, `verbs/drafts.py`, `verbs/edits.py`, `verbs/library.py` | `evaluation/record.py`, `tools/derive_field_map.py` |
| `drafting.py` | `cli.py`, `ui/app.py`, `verbs/drafts.py` | — |
| `render.py` | `cli.py`, `ui/app.py`, `ui/jobs.py`, `ui/library.py`, `verbs/edits.py` | — |
| `run_view.py` | `cli.py` | `evaluation/__main__.py`, `evaluation/recall.py` |
| `compare_view.py` | `render.py`, `verbs/library.py` | — |
| `ui/` | `cli.py`, `verbs/drafts.py`, `verbs/library.py` | — |
| `verbs/` | `cli.py` | — |

> The file is `run_view.py`; the **verb is still `show`**, and the entry-point
> tests pin it.

> `cli.py` imports `isekai.interface.ui` **inside its handler**, not at module
> scope. `tests/test_pipeline_cli.py` imports the entry point under `-S`, with
> site-packages off the path: a top-level import here would put FastAPI on
> `python -m isekai`'s import graph and turn that guard red for every verb.

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
