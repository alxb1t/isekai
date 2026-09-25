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

**The groups do not re-export.** Every group's `__init__.py` holds a docstring and
no code, so a module is imported by its own path and a group never becomes a place
two modules can reach each other through. `interface/ui/__init__.py` is a
subpackage's front door, not a group's, and holds `serve()`.

**The layers are the rule** ([principles](../docs/principles.md#the-code-is-layered)):
each group but `evaluation` is a layer, imports point down, and nothing in the
package imports `evaluation`. The module graph has no cycles. Today's upward
imports, group cycles, and imports from `shared` and `boundary` into `evaluation`
are known breaks, removed by the change that moves those imports.

**The graph itself is drawn in [`docs/modules.md`](../docs/modules.md)**,
and only there — every cross-group edge, which of them are lazy, the subpackage
cycles and why each one exists. It is one drawing in one place because two
drawings is how the one that used to sit here acquired its errors: a module-level
edge missing outright, a laziness annotated backwards, and `interface/ui`
collapsed away. The file tables below stay, because a file table is a local fact
and a graph is not.

**Two rules the layout is holding, not describing.** The entry point imports no
third-party package at module scope: nothing in `python -m isekai`'s import graph
may need a wheel, and a subprocess guard under `-S` proves it -- the wheels a run
does need are declared dependencies as of v0.22.3, reached from inside the verb
that needs them, and that guard is what checks this. And a set of constants
anchors a repository path on its own `__file__` -- `run.DATA_ROOT`,
`run.REPOSITORY`, `flow.FLOWS_DIR`, `provision.MANIFEST_PATH`,
`provision.VOCABULARY_MANIFEST_PATH` and `eval_models.EVAL_MANIFEST_PATH`;
`tests/test_package_paths.py` pins every one of them to the directory holding
`pyproject.toml`. The falsification twin is **one**, not one each: every anchor's
suffix cancels against its own hops, so all of them reduce to the same wrong path
and parametrizing would advertise per-anchor coverage that does not exist.

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../docs/decisions.md)'s; neither restates the other.
