# The module graph

What imports what inside `isekai/`, and why the shape is what it is. This is the
one drawing of this graph in the repository. The group READMEs keep their file
tables, which are local facts; the graph is not a local fact, and two drawings of
it is how the previous one acquired its errors.

**The layers are the rule** ([principles](principles.md#the-code-is-layered)):
imports point down, and nothing in the package imports `evaluation`. The module
graph has no cycles. Today's upward imports, the group cycles below, and the lazy
`shared → evaluation` and `boundary → evaluation` edges below are the rule's known
breaks, removed by the change that moves those imports.

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

**A lazy edge is not a weaker edge, it is a different one.** The `-S` guard goes
red when a chain of module-scope imports from the entry point reaches a wheel. The
lazy edges above are between this package's own modules and reach no wheel, so
moving one leaves the guard green; review holds them.

## The cycles, and why each one exists

There are no module cycles. The subpackage cycles are module-level, and this is
all of them — each named here with the reason it exists, because a cycle without
a stated reason is indistinguishable from a mistake:

```
  foundation ⇄ shared       run ──▶ atomic_write ;  fields ──▶ flow
  foundation ⇄ boundary     flow ──▶ comfy_types ;  comfy_types ──▶ refusal
```

**`foundation ⇄ shared`.** `atomic_write` is a primitive: it takes a path and
bytes and writes both or neither, and it knows nothing about a run. `run →
atomic_write` points up, from `foundation` into `shared`: a known break of the
layers, removed by the change that moves those imports. `fields → flow` points
down: `fields` answers *is this filled sheet exactly the schema's fields*, and a
schema belongs to a flow. The cycle is between the *groups*; no module here
imports a module that imports it back.

**`foundation ⇄ boundary`.** `refusal` is what everything in this package raises,
so every module that can fail imports it — including the ones at the boundary.
`flow` reaches the other way because the flow manifest names the nodes of a
ComfyUI graph, and `comfy_types` is what a graph *is*. Again: distinct modules,
opposite directions, one group pair, no module cycle.

## Reading this graph

The layers are the rule: a group imports from itself and the layers below it
([principles](principles.md#the-code-is-layered)). An edge that points up, or into
`evaluation`, is a known break. Go to the module graph when the question is
whether something is acyclic; the group graph cannot answer that.

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

  Each wheel-needing tree is reached from inside a function or behind a lazy
  import: `fastapi`/`uvicorn` from `interface/ui/app.py`; `[eval]` from
  `evaluation/eval_backends.py`, which also reaches `numpy`, `Pillow` and
  `onnxruntime` (`_numpy()`, `_pil()`, `OnnxSession.__init__`); the tagger's stack
  from `boundary/wd14.py`. The mechanisms differ, and the difference matters to
  anyone reading this as a rule to apply. `eval_backends.py` and `wd14.py` reach theirs by an
  `import_module` call **inside a function**, so the module that reaches them
  imports cleanly without the wheel. `app.py` does not: it imports `uvicorn` and
  `fastapi` at module scope, and the laziness sits one level up —
  `interface/ui/__init__.py`'s `serve()` imports `app.py` inside the function,
  and nothing else imports `app.py` outside the suite.

  **The `-S` guard in `tests/test_pipeline_cli.py` holds this, and
  `tests/test_wd14.py`'s source scan holds it for `boundary/wd14.py`.** While the
  packages were an extra CI never installed, a module-scope import would have
  failed outright; installed by default, it resolves silently.
- **A group never becomes a place two modules reach each other through.** A
  group's `__init__.py` holds a docstring and no code, so a module is imported by
  its own path. `interface/ui/__init__.py` is the exception and is not a group: it
  is a subpackage with a front door, and `serve()` is that door.

## How the components interact

The graph above says what may import what; this says who builds, who calls, and
what carries data at run time.

```
  python -m isekai <verb>
          │
          ▼
  interface/cli.py ──builds──▶ interface/wiring.py ──▶ a Wiring
          │                                              │
          │ the `ui` verb: serve(wired, …)               │
          │               ▼                              │
          │        interface/ui/ ◀───────────────────────┘
          │               │
          ▼               ▼
      pipeline/ stages ──────reads and writes──────▶ the run directory
          │
          ▼
      boundary/ ──▶ Ollama · the WD14 session · ComfyUI · downloads
```

- **The CLI builds the components** through `interface/wiring.py` and hands them
  to the review UI its `ui` verb starts (`cli.py`'s `_ui`). The UI builds none:
  nothing under `interface/ui/` calls a builder in `wiring.py`, and no module
  there imports `cli.py`. Review holds both.
- **Each front end calls the stage functions directly.**
- **A stage reads and writes its run directory.** No stage imports another stage;
  review holds this until the layer test lands.
- **A stage reaches a model, the GPU or the network through `boundary/`.**
- **`foundation`'s run, flow and refusal are what every layer uses.**
- **`StageFailure` lives in `foundation/run.py`, not `refusal.py`.** `refusal.py`
  imports nothing, the class needs `Kind`, and `run.py` already imports
  `refusal.py`, so the move would be a cycle.
