# `isekai/` — the package

Six groups and one file. `__main__.py` is the entry point `python -m isekai`
resolves to and is a shim over `interface/cli.py`; everything else is filed by
what it is, not by what calls it.

| directory | is | files |
|---|---|---|
| [`foundation/`](foundation/README.md) | what a run, a flow and a refusal are | 3 |
| [`pipeline/`](pipeline/README.md) | the four staged verbs, and `tagging.py`, which is not one | 5 |
| [`shared/`](shared/README.md) | primitives with no domain of their own | 4 |
| [`boundary/`](boundary/README.md) | everything that leaves this process | 7 |
| [`evaluation/`](evaluation/README.md) | scoring a render against its photograph | 5 |
| [`interface/`](interface/README.md) | what an operator touches | 3 + `ui/` (3) |

**These counts are `ls` and nothing else.** Two of them were wrong before v0.20
touched them — `boundary/` read 5 against 6 files and `interface/ui/` read 4
against 3 — the same drift that left `CLAUDE.md` miscounting the living spec's
capabilities through two versions. Count; do not trust the row.

**The groups do not re-export.** Every `__init__.py` here holds a docstring and no
code, so a module is imported by its own path and a group never becomes a place
two modules can reach each other through.

**A group is a filing decision, not a layering rule.** The *module* graph has no
cycles and never has; the *group* graph does, and drawing it as a stack would be a
lie. `foundation` holds `refusal`, which everything raises, so `boundary` imports
back into it; `shared/vocabulary.py` reaches `boundary/provision.py` for its
manifest and — lazily, at call time — `evaluation/eval_models.py`. Every
cross-group edge that exists today, by source:

```
  interface   ──▶ pipeline · foundation · shared · boundary
  pipeline    ──▶ foundation · shared · boundary
  evaluation  ──▶ foundation · shared · boundary
  foundation  ──▶ shared · boundary
  shared      ──▶ foundation · boundary · evaluation (lazy)
  boundary    ──▶ foundation
```

Read it as *what each group is allowed to know about*, and check the module graph
— not this table — when the question is whether something is acyclic.

**Two rules the layout is holding, not describing.** The runtime is stdlib-only:
nothing in `python -m isekai`'s import graph may need a wheel, and a subprocess
guard under `-S` proves it. And five files anchor a repository path on their own
`__file__`; `tests/test_package_paths.py` pins every one of them to the directory
holding `pyproject.toml`, with a falsification twin each.

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
