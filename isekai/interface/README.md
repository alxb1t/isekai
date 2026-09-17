# `interface/` — what an operator touches

The verb line, the composition behind it, and the read-only account of a run.
`isekai/__main__.py` stays at the package root because `runpy` pins that path; it
is a shim over `cli.py` and holds nothing else.

## Files

| file | does |
|---|---|
| `cli.py` | parses a verb, names the flows, dispatches, and reports every refusal together |
| `wiring.py` | composes the modules — resolves what a verb needs and hands out the pieces, with or without a parser |
| `run_view.py` | the `show` verb: a run's artifacts, active versions and producers. Reads everything, decides nothing |

## Imported by

| file | inside `isekai/` | outside |
|---|---|---|
| `cli.py` | `isekai/__main__.py` | four test modules |
| `wiring.py` | `cli.py` | three test modules |
| `run_view.py` | `cli.py` | `tests/test_run_view.py` |

> The file is `run_view.py`; the **verb is still `show`**, and the entry-point
> tests pin it.

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
