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
| `wiring.py` | composes the modules — builds the reader, the sorter, the transport and the vocabulary thunk, with or without a parser |
| `run_view.py` | the `show` verb: a run's artifacts, active versions and producers. Reads everything, decides nothing |
| `ui/__init__.py` | the `ui` verb: establishes the batch, prints the address, serves until stopped |
| `ui/batch.py` | the batch and the whole startup refusal order. **Imports no web framework**, which is what keeps that order testable in the main suite |
| `ui/bundle.py` | builds the browser bundle when it is absent; refuses naming `npm install` rather than fetching |
| `ui/app.py` | the six endpoints, and the only module in the package that imports the `[ui]` extra |

## Imported by

| file | inside `isekai/` | outside |
|---|---|---|
| `cli.py` | `isekai/__main__.py` | four test modules |
| `wiring.py` | `cli.py` | four test modules |
| `run_view.py` | `cli.py` | `tests/test_run_view.py` |
| `ui/` | `cli.py`, **inside the handler** | `tests/test_ui.py`, `tests/test_ui_api.py` |

> The file is `run_view.py`; the **verb is still `show`**, and the entry-point
> tests pin it.

> `cli.py` imports `isekai.interface.ui` **inside its handler**, not at module
> scope. `tests/test_pipeline_cli.py` imports the entry point under `-S`, with
> site-packages off the path: a top-level import here would put FastAPI on
> `python -m isekai`'s import graph and turn that guard red for every verb.

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
