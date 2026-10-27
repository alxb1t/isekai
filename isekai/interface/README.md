# `interface/` — what an operator touches

The two front ends. The verb line, the composition behind them both, the
read-only account of a run, the comparison page of a collection, and the browser
surface for stage ③.
`isekai/__main__.py` stays at the package root because `runpy` pins that path; it
is a shim over `cli.py` and holds nothing else.

**`ui/` is a sibling of `cli.py`, not a client of it.** Both reach the pipeline
the same way — `wiring_from()` and the stage functions, called directly — so
neither is privileged and neither goes through the other.

## Files

| file | does |
|---|---|
| `cli.py` | parses a verb, resolves the flows it was given against `flows/`, dispatches per flow, and reports every refusal together, or with `--progress json` a JSON line per item; `import` and `assign` compose `pipeline/importing.py` and the run's own `assign` |
| `wiring.py` | composes the modules — resolves the reader and the two taggers per flow, verifies the vocabulary before it is read, and builds the transport and the vocabulary and field-map thunks, with or without a parser |
| `drafting.py` | drafts a flow from another flow's approval for `review --from` and the page, assigning a flow with no sheet and filling it from the source's tags first |
| `render.py` | the `render` verb: finds what each approval lacks or takes the requests, assembles every prompt, estimates the session's limit and its quote, opens a GPU session through `boundary/gpu.py` stopping at that limit, waits for the endpoint, runs `generate` per flow, reports each step with `--progress json`, and writes the prose to the collection's log |
| `run_view.py` | the `show` verb: a run's artifacts, active versions, producers and failure records, and the names below a flow it does not read. Decides nothing |
| `compare_view.py` | the `compare` verb: one page of every run's photograph beside each flow's renders, written into the collection directory. Reads, decides nothing |
| `ui/__init__.py` | the `ui` verb: opens the library `ISEKAI_LIBRARY` names, sweeps import's staging, reads the offered flows, prints the address, serves until stopped |
| `ui/library.py` | the library, its collections and each source × offered flow's stage, all read from folders, each source's not-cleaned mark, each approval's rendered seeds, each collection's session records, and the thumbnails in the library's `.cache/`. **Imports no web framework**, which keeps it testable in the main suite |
| `ui/bundle.py` | builds the browser bundle when it is absent; refuses naming `npm install` rather than fetching |
| `ui/jobs.py` | Prepare and Render as jobs, a slot per kind, side by side: `tag` → `caption` → `sheet` run as CLI children per flow after a probe of the model server; `gpunit volume up` → `render` → `volume down` unless kept; Stop and server stop sending SIGINT |
| `ui/billing.py` | what may be billing, read from gpunit's records in `.gpunit/`: the pod alert, the window's quiet item and the band; gpunit asked at start, every half minute while needed, and on Check again |
| `ui/events.py` | the event stream: a snapshot on connect, then each `job`, `cell` and `billing` change, to every open page |
| `ui/app.py` | the endpoints — `GET /api/library`, `/api/c/{collection}/hub`, `POST /api/c/{collection}/assign`, `/api/c/{collection}/review/{digest}/{flow}` with `/photo`, `PUT …/draft`, `POST …/approve`, `POST …/cancel`, `POST …/discard`, `POST …/draft-from`, `POST /api/c/{collection}/revise`, `POST /api/c/{collection}/prepare`, `GET /api/c/{collection}/render`, `POST /api/render/quote`, `POST /api/render`, `GET /api/sessions/running`, `GET /api/c/{collection}/sessions/{id}`, `POST /api/jobs/{kind}/stop`, `POST /api/billing/check`, `GET /api/c/{collection}/renders` with `…/renders/{digest}/{flow}/{version}/{seed}` and its `/image`, `/thumb` and `/compare`, with an optional `/{other}/{other_seed}`, `GET /events` with `?collection=` and `?staging=`, either or both, the import's `POST /api/staging` with `PUT …/{id}/files/{name}` and its `/thumb`, `DELETE …/{id}` and `POST …/{id}/commit`, `/api/tags`, `/api/fields`, and the bundle's `index.html` for every other path — and the only module in the package that imports FastAPI or uvicorn |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `cli.py` | `__main__.py` | `tests/test_assign.py`, `tests/test_compare.py`, `tests/test_generate.py`, `tests/test_importing.py`, `tests/test_pipeline_cli.py`, `tests/test_progress.py`, `tests/test_render.py`, `tests/test_resume.py`, `tests/test_run_directory.py`, `tests/test_tagging.py`, `tests/test_ui_api.py` |
| `wiring.py` | `cli.py`, `render.py`, `ui/__init__.py`, `ui/app.py`, `ui/library.py` | `evaluation/record.py`, `tools/derive_field_map.py`, `tests/conftest.py`, `tests/e2e/wiring.py`, `tests/stages.py`, `tests/test_assign.py`, `tests/test_compare.py`, `tests/test_evaluation_cli.py`, `tests/test_field_map.py`, `tests/test_generate.py`, `tests/test_package_paths.py`, `tests/test_pipeline_cli.py`, `tests/test_recall_cli.py`, `tests/test_resume.py`, `tests/test_run_directory.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_ui_api.py`, `tests/test_vocabulary.py`, `tests/test_vocabulary_manifest.py` |
| `drafting.py` | `cli.py`, `ui/app.py` | — |
| `render.py` | `cli.py`, `ui/app.py`, `ui/jobs.py`, `ui/library.py` | `tests/test_infra.py`, `tests/test_render.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py` |
| `run_view.py` | `cli.py` | `evaluation/__main__.py`, `evaluation/recall.py`, `tests/test_run_view.py` |
| `compare_view.py` | `cli.py`, `render.py` | `tests/test_compare.py` |
| `ui/` | `cli.py` | `tests/test_ui.py`, `tests/test_ui_api.py`, `tests/test_ui_billing.py`, `tests/test_ui_jobs.py`, `tests/test_ui_library.py` |

> The file is `run_view.py`; the **verb is still `show`**, and the entry-point
> tests pin it.

> `cli.py` imports `isekai.interface.ui` **inside its handler**, not at module
> scope. `tests/test_pipeline_cli.py` imports the entry point under `-S`, with
> site-packages off the path: a top-level import here would put FastAPI on
> `python -m isekai`'s import graph and turn that guard red for every verb.

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
