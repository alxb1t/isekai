# The module graph

What imports what inside `isekai/`, and why the shape is what it is. This is the
one drawing of this graph in the repository. The group READMEs keep their file
tables, which are local facts; the graph is not a local fact, and two drawings of
it is how the previous one acquired its errors.

**The module graph has no cycles and never has; the group graph does, and drawing
it as a stack would be a lie.** That sentence is the whole point of this file. A
group is a filing decision — *what is this thing* — and not a layer. Reading the
group edges as a stack makes the edges below look like violations when none of
them is.

## The edges, by source

```
Module-level, cross-group:
  interface   ──▶ boundary · foundation · pipeline · shared
  pipeline    ──▶ boundary · foundation · shared
  evaluation  ──▶ boundary · foundation · shared
  foundation  ──▶ boundary · shared
  boundary    ──▶ foundation · shared
  shared      ──▶ foundation

Lazy — the import sits inside a function, so the edge does not exist at
import time:
  shared    ──▶ boundary      vocabulary.py, inside load()
  shared    ──▶ evaluation    vocabulary.py, inside load()
  boundary  ──▶ evaluation    wd14.py, inside verified_paths()
  interface ──▶ interface/ui  cli.py, inside the `ui` handler — within the
                              group, and listed because collapsing it away
                              is what hid it before
```

**A lazy edge is not a weaker edge, it is a different one.** Neither `boundary`,
nor `evaluation`, nor the surface's `fastapi`/`uvicorn` may sit at module scope on
`python -m isekai`'s import graph, and a `-S` subprocess guard in the suite is
what proves it. Move any of those imports to module scope and that guard goes red
— which is the designed outcome, not a nuisance.

## The cycles, and why each one exists

There are no module cycles. The subpackage cycles are module-level, and this is
all of them — each named here with the reason it exists, because a cycle without
a stated reason is indistinguishable from a mistake:

```
  foundation ⇄ shared       run ──▶ atomic_write ;  fields ──▶ flow
  foundation ⇄ boundary     flow ──▶ comfy_types ;  comfy_types ──▶ refusal
```

**`foundation ⇄ shared`.** `atomic_write` is a primitive: it takes a path and
bytes and writes both or neither, and it knows nothing about a run. `run` writes
every artifact through it, so `foundation` reaches down into `shared`. In the
other direction, `fields` answers *is this filled sheet exactly the schema's
fields* — and a schema belongs to a flow, so it has to know what a flow is. Both
edges point at whatever is more primitive than the module reaching for it. The
cycle is between the *groups*; no module here imports a module that imports it
back.

**`foundation ⇄ boundary`.** `refusal` is what everything in this package raises,
so every module that can fail imports it — including the ones at the boundary.
`flow` reaches the other way because the flow manifest names the nodes of a
ComfyUI graph, and `comfy_types` is what a graph *is*. Again: distinct modules,
opposite directions, one group pair, no module cycle.

## Reading this graph

Read the group edges as *what each group is allowed to know about*, and go to the
module graph when the question is whether something is acyclic. The group graph
cannot answer that question and never could.

Rules the graph is holding rather than describing:

- **The entry point imports no third-party package at module scope.** This rule
  used to read *the runtime is stdlib-only*, backed by `dependencies = []`, and
  v0.22.3 retired that: the local tagger runs on every `caption` for every flow,
  so `uv sync` — which makes the environment match exactly what it is told and
  removes extras it is not told about — was stripping it on every gate run.
  `onnxruntime`, `numpy`, `Pillow`, `fastapi` and `uvicorn` are declared
  dependencies now. **What survives is the claim the graph actually holds**, and
  it is worth more than the one it replaces: no wheel is reached on the import
  graph of `python -m isekai`, only on the path of the verb that needs it — which
  is why `isekai show` works on a checkout that has provisioned nothing.

  Each wheel-needing tree is still reached from a single named module —
  `fastapi`/`uvicorn` from `interface/ui/app.py`, `[eval]` from
  `evaluation/eval_backends.py`, the tagger's stack from `boundary/wd14.py` — but
  by two different mechanisms, and the difference matters to anyone reading this
  as a rule to apply. `eval_backends.py` and `wd14.py` reach theirs by an
  `import_module` call **inside a function**, so the module that reaches them
  imports cleanly without the wheel. `app.py` does not: it imports `uvicorn` and
  `fastapi` at module scope, and the laziness sits one level up —
  `interface/ui/__init__.py`'s `serve()` imports `app.py` inside the function,
  and nothing else imports `app.py` outside the suite.

  **The `-S` guard in `tests/test_pipeline_cli.py` is now the only thing holding
  this.** While the packages were an extra CI never installed, a module-scope
  import would have failed outright; installed by default, it resolves silently,
  so the guard is the check rather than a belt over a brace.
- **A group never becomes a place two modules reach each other through.** A
  group's `__init__.py` holds a docstring and no code, so a module is imported by
  its own path. `interface/ui/__init__.py` is the exception and is not a group: it
  is a subpackage with a front door, and `serve()` is that door.
