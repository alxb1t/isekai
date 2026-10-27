# The module graph

What imports what inside `isekai/` and from `evaluation/` beside it, and why the
shape is what it is. This is the one drawing of this graph in the repository. The
group READMEs keep their file tables, which are local facts; the graph is not a
local fact, and two drawings of it is how the previous one acquired its errors.

**The layers are the rule** ([principles](principles.md#the-code-is-layered)):
imports point down, and nothing in the package imports `evaluation`. The module
graph has no cycles. `tests/test_layers.py` holds both, lazy imports included.

## The edges, by source

```
Module-level, cross-group:
  interface   ──▶ boundary · foundation · pipeline · shared
  pipeline    ──▶ boundary · foundation · shared
  evaluation  ──▶ boundary · foundation · interface · shared    (evaluation/, beside the package)
  boundary    ──▶ foundation · shared
  shared      ──▶ foundation
  foundation  ──▶ nothing above it

Lazy — the import sits inside a function, so the edge does not exist at
import time:
  interface ──▶ boundary      wiring.py, inside load_vocabulary(); provision.py
                              is on the entry point's graph through ollama.py
  interface ──▶ interface/ui  cli.py, inside the `ui` handler — within the
                              group, and listed because collapsing it away
                              is what hid it before
  interface ──▶ a named module  wiring.py, inside _named_wiring(), only when
                              ISEKAI_WIRING names it — the browser tests'
                              doubles (D41)
```

Every lazy edge points down, as every module-level one does.

**Where this version's pieces sit.** `import` is `pipeline/importing.py`, a stage
no other stage imports; the CLI's `import` verb and the surface's staging routes
both compose it, and `ui/library.py` reads `shared/image.py`'s `metadata_in` for the
not-cleaned mark.
`assign` is `foundation/run.py`'s, because a tick is the run's layout, and the CLI
verb and the hub's route both call it. `--progress json` is a reporter inside
`cli.py`. **Prepare and Render reach the CLI by process, never by import**:
`interface/ui/jobs.py` runs `python -m isekai tag | caption | sheet`, and
`python -m isekai render` between `python -m gpunit volume up` and `volume down`,
as children, so the CLI stays the one path a stage runs through, and
`interface/ui/events.py` streams what they report to the page as `/events`.
Every other write the server makes runs in its own process, through the function
that owns it: stage ③'s review functions, import's reader, and `sheet()` for a
target's first sheet when a draft is made from another flow —
`interface/drafting.py`'s `draft_across` runs it, the same sequence the CLI's
`draft` runs (D4).
`wiring.py` imports `boundary/ollama.py` for the probe a job asks first.

**`tests/test_layers.py` holds where the lazy edges point; review holds that they
stay lazy.** The `-S` guard goes red only when a chain of module-scope imports
from the entry point reaches a wheel. The lazy edges above are between this
package's own modules and reach no wheel, so moving one to module scope leaves
both green.

## The cycles

There are none. Every cross-group edge points down, so no two groups import each
other; `tests/test_layers.py::test_no_import_cycle_inside_a_layer` holds the
modules inside each group and inside `evaluation/`.

`foundation` owns what the groups above share without knowing about them:
`atomic_write` writes bytes to a path and knows nothing about a run, `artifacts`
declares what every run file holds, and `flow` defines `Workflow`, the ComfyUI
graph a flow manifest names the nodes of.
`boundary/comfy/` and `pipeline/generate.py` import them rather than define them.

## Reading this graph

The layers are the rule: a group imports from itself and the layers below it
([principles](principles.md#the-code-is-layered)). An edge that points up, or into
`evaluation`, fails `tests/test_layers.py`. Go to the module graph when the
question is whether something is acyclic; the group graph cannot answer that.

Rules the graph is holding rather than describing:

- **The entry point imports no third-party package at module scope.** This rule
  used to read *the runtime is stdlib-only*, backed by `dependencies = []`, and
  v0.22.3 retired that: the local tagger runs on every `tag` for every tagged flow,
  so `uv sync` — which makes the environment match exactly what it is told and
  removes extras it is not told about — was stripping it on every gate run.
  `onnxruntime`, `numpy`, `Pillow`, `pi-heif`, `fastapi`, `uvicorn` and `gpunit` are
  declared dependencies now. **What survives is the claim the graph actually holds**, and
  it is worth more than the one it replaces: no wheel is reached on the import
  graph of `python -m isekai`, only on the path of the verb that needs it — which
  is why `isekai show` works on a checkout that has provisioned nothing.

  Each wheel-needing tree is reached from inside a function or behind a lazy
  import: `fastapi`/`uvicorn` from `interface/ui/app.py`; the tagger's stack
  from `boundary/wd14.py`; Pillow and `pi_heif` from inside the functions of
  `pipeline/importing.py`; `gpunit` from inside `boundary/gpu.py`'s `open_session`
  and `bounds`, and `interface/render.py`'s session block. The mechanisms differ, and the difference matters to
  anyone reading this as a rule to apply. `wd14.py` reaches its stack by an
  `import_module` call **inside a function**, so the module imports cleanly
  without the wheel. `app.py` does not: it imports
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
      boundary/ ──▶ Ollama · the WD14 session · ComfyUI · the GPU session · downloads
```

- **The CLI builds the components** through `interface/wiring.py` and hands them
  to the UI its `ui` verb starts (`cli.py`'s `_ui`). The UI builds one collection's
  wiring per request through `wiring_from`, so the runs-root guard holds for each
  collection, and no module under `interface/ui/` imports `cli.py`. Review holds both.
- **Each front end calls the stage functions directly.**
- **A stage reads and writes its run directory.** No stage imports another stage;
  `tests/test_layers.py::test_no_stage_imports_another` holds this. Every run
  file's JSON is written through `foundation/artifacts.py`'s `write`;
  `tests/test_artifact_bytes.py::test_only_the_contract_writes_a_run_file` holds
  that. The photograph's copy and a render's image are bytes, written by
  `foundation/atomic_write.py`.
- **A stage reaches a model, the GPU or the network through `boundary/`.**
- **`foundation`'s run, artifacts, flow and refusal are what every layer uses.**
- **`StageFailure` lives in `foundation/run.py`, not `refusal.py`.** `refusal.py`
  imports nothing, the class needs `Kind`, and `run.py` already imports
  `refusal.py`, so the move would be a cycle.
