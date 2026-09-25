# `interface/` — what an operator touches

The two front ends. The verb line, the composition behind them both, the
read-only account of a run, and the browser surface for stage ③.
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
| `run_view.py` | the `show` verb: a run's artifacts, active versions and producers. Reads everything, decides nothing |
| `ui/__init__.py` | the `ui` verb: establishes the batch, prints the address, serves until stopped |
| `ui/batch.py` | the batch and the whole startup refusal order. **Imports no web framework**, which is what keeps that order testable in the main suite |
| `ui/bundle.py` | builds the browser bundle when it is absent; refuses naming `npm install` rather than fetching |
| `ui/app.py` | the endpoints — `GET /api/batch`, `/api/tags`, `/api/fields`, `/api/inputs/{id}`, `/api/inputs/{id}/photo`, `PUT /api/inputs/{id}/draft`, `POST /api/inputs/{id}/approve`, and the bundle mounted at `/` — and the only module in the package that imports FastAPI or uvicorn |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `cli.py` | `__main__.py` | `tests/test_generate.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_run_directory.py`, `tests/test_tagging.py` |
| `wiring.py` | `cli.py`, `ui/__init__.py`, `ui/batch.py` | `scripts/derive_field_map.py`, `tests/test_field_map.py`, `tests/test_generate.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_run_directory.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_ui_api.py`, `tests/test_vocabulary.py`, `tests/test_vocabulary_manifest.py` |
| `run_view.py` | `cli.py` | `tests/test_run_view.py` |
| `ui/` | `cli.py` | `tests/test_ui.py`, `tests/test_ui_api.py` |

> The file is `run_view.py`; the **verb is still `show`**, and the entry-point
> tests pin it.

> `cli.py` imports `isekai.interface.ui` **inside its handler**, not at module
> scope. `tests/test_pipeline_cli.py` imports the entry point under `-S`, with
> site-packages off the path: a top-level import here would put FastAPI on
> `python -m isekai`'s import graph and turn that guard red for every verb.

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
