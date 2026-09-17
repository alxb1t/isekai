# `isekai/` — the package

Six groups and one file. `__main__.py` is the entry point `python -m isekai`
resolves to and is a shim over `interface/cli.py`; everything else is filed by
what it is, not by what calls it.

| directory | is | files |
|---|---|---|
| [`foundation/`](foundation/README.md) | what a run, a flow and a refusal are | 3 |
| [`pipeline/`](pipeline/README.md) | the four staged verbs | 4 |
| [`shared/`](shared/README.md) | primitives with no domain of their own | 3 |
| [`boundary/`](boundary/README.md) | everything that leaves this process | 5 |
| [`evaluation/`](evaluation/README.md) | scoring a render against its photograph | 5 |
| [`interface/`](interface/README.md) | what an operator touches | 3 |

**The groups do not re-export.** Every `__init__.py` here holds a docstring and no
code, so a module is imported by its own path and a group never becomes a place
two modules can reach each other through.

**The direction of travel** — no cycles, and one stage-to-stage edge:

```
  interface ──▶ pipeline ──▶ boundary
      │            │  │
      │            │  └────▶ shared
      └────────────┴───────▶ foundation

  evaluation ──▶ shared · boundary        (the [eval] extra's island)
```

**Two rules the layout is holding, not describing.** The runtime is stdlib-only:
nothing in `python -m isekai`'s import graph may need a wheel, and a subprocess
guard under `-S` proves it. And seven files anchor a repository path on their own
`__file__`; `tests/test_package_paths.py` pins every one of them to the directory
holding `pyproject.toml`, with a falsification twin each.

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
