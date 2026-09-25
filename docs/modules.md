# The module graph

What imports what inside `isekai/`, and why the shape is what it is. This is the
one drawing of this graph in the repository. The group READMEs keep their file
tables, which are local facts; the graph is not a local fact, and two drawings of
it is how the previous one acquired its errors.

**The layers are the rule** ([principles](principles.md#the-code-is-layered)):
imports point down, and nothing in the package imports `evaluation`. The module
graph has no cycles. `tests/test_layers.py` holds both, lazy imports included.

## The edges, by source

```
Module-level, cross-group:
  interface   ──▶ boundary · foundation · pipeline · shared
  pipeline    ──▶ boundary · foundation · shared
  evaluation  ──▶ boundary · foundation · shared
  boundary    ──▶ foundation · shared
  shared      ──▶ foundation
  foundation  ──▶ nothing above it

Lazy — the import sits inside a function, so the edge does not exist at
import time:
  interface ──▶ boundary      wiring.py, inside load_vocabulary(), which
                              keeps provision.py off the entry point's graph
  interface ──▶ interface/ui  cli.py, inside the `ui` handler — within the
                              group, and listed because collapsing it away
                              is what hid it before
```

Every lazy edge points down, as every module-level one does.

**`tests/test_layers.py` holds where the lazy edges point; review holds that they
stay lazy.** The `-S` guard goes red only when a chain of module-scope imports
from the entry point reaches a wheel. The lazy edges above are between this
package's own modules and reach no wheel, so moving one to module scope leaves
both green.

## The cycles

There are none. Every cross-group edge points down, so no two groups import each
other; `tests/test_layers.py::test_no_import_cycle_inside_a_layer` holds the
modules inside each group.

`foundation` owns what the groups above share without knowing about them:
`atomic_write` writes bytes to a path and knows nothing about a run, and
`flow` defines `Workflow`, the ComfyUI graph a flow manifest names the nodes of.
`boundary/comfy/` and `pipeline/generate.py` import them rather than define them.

## Reading this graph

The layers are the rule: a group imports from itself and the layers below it
([principles](principles.md#the-code-is-layered)). An edge that points up, or into
`evaluation`, fails `tests/test_layers.py`. Go to the module graph when the
question is whether something is acyclic; the group graph cannot answer that.

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
  anyone reading this as a rule to apply. `eval_backends.py` and `wd14.py` reach
  theirs by an `import_module` call **inside a function**, so the module that
  reaches them imports cleanly without the wheel. `app.py` does not: it imports
  `uvicorn` and `fastapi` at module scope, and the laziness sits one level up —
  `interface/ui/__init__.py`'s `serve()` imports `app.py` inside the function,
  and nothing else imports `app.py` outside the suite.

  **The `-S` guard in `tests/test_pipeline_cli.py` holds this, and
  `tests/test_wd14.py`'s source scan holds it for `boundary/wd14.py`.** While the
  packages were an extra CI never installed, a module-scope import would have
  failed outright; installed by default, it resolves silently.
- **A group never becomes a place two modules reach each other through.** A
  group's `__init__.py` holds a docstring and no code, so a module is imported by
  its own path. `interface/ui/` and `boundary/comfy/` are not groups: each is a
  sub-package with a front door, its `__init__.py`, and nothing outside it imports
  past that door. `tests/test_layers.py` holds both rules.

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
  `tests/test_layers.py::test_no_stage_imports_another` holds this.
- **A stage reaches a model, the GPU or the network through `boundary/`.**
- **`foundation`'s run, flow and refusal are what every layer uses.**
- **`StageFailure` lives in `foundation/run.py`, not `refusal.py`.** `refusal.py`
  imports nothing, the class needs `Kind`, and `run.py` already imports
  `refusal.py`, so the move would be a cycle.
