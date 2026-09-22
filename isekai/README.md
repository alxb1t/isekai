# `isekai/` — the package

Six groups and one file. `__main__.py` is the entry point `python -m isekai`
resolves to and is a shim over `interface/cli.py`; everything else is filed by
what it is, not by what calls it.

| directory | is | files |
|---|---|---|
| [`foundation/`](foundation/README.md) | what a run, a flow and a refusal are | `refusal.py` · `run.py` · `flow.py` |
| [`pipeline/`](pipeline/README.md) | the staged verbs, and `tagging.py`, which is not one | `caption.py` · `tagging.py` · `sheet.py` · `review.py` · `generate.py` |
| [`shared/`](shared/README.md) | primitives with no domain of their own | `atomic_write.py` · `field_map.py` · `fields.py` · `image.py` · `vocabulary.py` |
| [`boundary/`](boundary/README.md) | everything that leaves this process | `comfy_types.py` · `comfy_client.py` · `multipart.py` · `ollama.py` · `provision.py` · `wd14.py` |
| [`evaluation/`](evaluation/README.md) | scoring a render against its photograph | `evaluate.py` · `eval_backends.py` · `ciede2000.py` · `eval_models.py` · `labels.py` |
| [`interface/`](interface/README.md) | what an operator touches | `cli.py` · `wiring.py` · `run_view.py` · `ui/` (`__init__.py` · `batch.py` · `bundle.py` · `app.py`) |

**The column names the files rather than counting them, and that is the fix for a
rot this repository has now watched twice.** It used to hold a number under a
disclaimer reading *"count; do not trust the row"* — and by v0.22 two of the
numbers were wrong again, `shared/` reading 4 against 5 and `boundary/` reading 7
against 6, the second in the opposite direction from the drift the disclaimer
described. A disclaimer does not stop a number from rotting; it only records that
someone expected it to. A list of names is self-counting and cannot rot the same
way, because adding a file without touching the row leaves a name missing rather
than a digit merely stale.

**The groups do not re-export.** Every `__init__.py` here holds a docstring and no
code, so a module is imported by its own path and a group never becomes a place
two modules can reach each other through.

**A group is a filing decision, not a layering rule.** The *module* graph has no
cycles and never has; the *group* graph does, and drawing it as a stack would be a
lie. `foundation` holds `refusal`, which everything raises, so `boundary` imports
back into it; `shared/vocabulary.py` reaches both `boundary/provision.py` and
`evaluation/eval_models.py` **lazily, at call time** — both imports sit inside
`load()`, so neither is an import-time edge. Every cross-group edge that exists
today, by source:

```
  interface   ──▶ pipeline · foundation · shared · boundary
  pipeline    ──▶ foundation · shared · boundary
  evaluation  ──▶ foundation · shared · boundary
  foundation  ──▶ shared · boundary
  shared      ──▶ foundation · boundary (lazy) · evaluation (lazy)
  boundary    ──▶ foundation · shared · evaluation (lazy)
```

Read it as *what each group is allowed to know about*, and check the module graph
— not this table — when the question is whether something is acyclic.

**Two rules the layout is holding, not describing.** The runtime is stdlib-only:
nothing in `python -m isekai`'s import graph may need a wheel, and a subprocess
guard under `-S` proves it. And a set of constants anchors a repository path on
its own `__file__` -- `run.DATA_ROOT`, `run.REPOSITORY`, `flow.FLOWS_DIR`,
`provision.MANIFEST_PATH`, `provision.VOCABULARY_MANIFEST_PATH` and
`eval_models.EVAL_MANIFEST_PATH`; `tests/test_package_paths.py` pins every one of
them to the directory holding `pyproject.toml`. The falsification twin is
**one**, not one each: every anchor's suffix cancels against its own hops, so all
of them reduce to the same wrong path and parametrizing would advertise
per-anchor coverage that does not exist.

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
