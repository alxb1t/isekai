# `interface/` — what an operator touches

The two front ends. The verb line, the composition behind them both, the
read-only account of a run, the comparison page of a batch, and the browser
surface for stage ③.
`isekai/__main__.py` stays at the package root because `runpy` pins that path; it
is a shim over `cli.py` and holds nothing else.

**`ui/` is a sibling of `cli.py`, not a client of it.** Both reach the pipeline
the same way — `wiring_from()` and the stage functions, called directly — so
neither is privileged and neither goes through the other.

## Files

| file | does |
|---|---|
| `cli.py` | parses a verb, resolves the flows it was given against `flows/`, dispatches per flow, and reports every refusal together |
| `wiring.py` | composes the modules — resolves the reader and the two taggers per flow, verifies the vocabulary before it is read, and builds the transport and the vocabulary and field-map thunks, with or without a parser |
| `render.py` | the `render` verb: assembles every prompt, opens a GPU session through `boundary/gpu.py` under a ceiling watchdog, waits for the endpoint, runs `generate` per flow, and writes it all to the batch's log |
| `run_view.py` | the `show` verb: a run's artifacts, active versions, producers and failure records, and the names below a flow it does not read. Decides nothing |
| `compare_view.py` | the `compare` verb: one page of every run's photograph beside each flow's renders, written into the batch directory. Reads, decides nothing |
| `ui/__init__.py` | the `ui` verb: opens the library `ISEKAI_LIBRARY` names, prints the address, serves until stopped |
| `ui/library.py` | the library, its batches and each source × flow's stage, all read from folders. **Imports no web framework**, which keeps it testable in the main suite |
| `ui/bundle.py` | builds the browser bundle when it is absent; refuses naming `npm install` rather than fetching |
| `ui/app.py` | the endpoints — `GET /api/library`, `/api/b/{batch}/hub`, `/api/b/{batch}/review/{digest}/{flow}` with `/photo`, `PUT …/draft`, `POST …/approve`, `/api/tags`, `/api/fields`, and the bundle's `index.html` for every other path — and the only module in the package that imports FastAPI or uvicorn |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `cli.py` | `__main__.py` | `tests/test_compare.py`, `tests/test_generate.py`, `tests/test_pipeline_cli.py`, `tests/test_render.py`, `tests/test_resume.py`, `tests/test_run_directory.py`, `tests/test_tagging.py`, `tests/test_ui_api.py` |
| `wiring.py` | `cli.py`, `render.py`, `ui/__init__.py`, `ui/app.py`, `ui/library.py` | `evaluation/record.py`, `tools/derive_field_map.py`, `tests/conftest.py`, `tests/e2e/wiring.py`, `tests/test_compare.py`, `tests/test_evaluation_cli.py`, `tests/test_field_map.py`, `tests/test_generate.py`, `tests/test_package_paths.py`, `tests/test_pipeline_cli.py`, `tests/test_recall_cli.py`, `tests/test_resume.py`, `tests/test_run_directory.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_ui_api.py`, `tests/test_vocabulary.py`, `tests/test_vocabulary_manifest.py` |
| `render.py` | `cli.py` | `tests/test_render.py` |
| `run_view.py` | `cli.py` | `evaluation/__main__.py`, `evaluation/recall.py`, `tests/test_run_view.py` |
| `compare_view.py` | `cli.py`, `render.py` | `tests/test_compare.py` |
| `ui/` | `cli.py` | `tests/test_ui.py`, `tests/test_ui_api.py`, `tests/test_ui_library.py` |

> The file is `run_view.py`; the **verb is still `show`**, and the entry-point
> tests pin it.

> `cli.py` imports `isekai.interface.ui` **inside its handler**, not at module
> scope. `tests/test_pipeline_cli.py` imports the entry point under `-S`, with
> site-packages off the path: a top-level import here would put FastAPI on
> `python -m isekai`'s import graph and turn that guard red for every verb.

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
