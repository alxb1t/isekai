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
  interface ──▶ boundary      wiring.py, inside load_vocabulary(), except
                              DigestMismatch, which it imports at module scope;
                              provision.py is on the entry point's graph through
                              ollama.py and wiring.py
  interface ──▶ interface/ui  `run_ui` and `run_discard` of interface/verbs/ and
                              `_migrate` of cli.py — within the group, and listed
                              because collapsing it away is what hid it before
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
verb and the hub's route both call it. `migrate` is `foundation/migrate.py`'s,
which imports `artifacts.py`, `run.py` and `refusal.py`: it moves the run's layout,
and `cli.py`'s verb walks each runs root, reaching the library's collections
through `interface/ui/`'s `collection_runs` inside the handler. `--progress json`
is `Reporter` of `interface/verbs/common.py`. **Prepare and Render reach the CLI by process, never
by import**: `interface/ui/jobs.py` runs `python -m isekai prepare`
over the cells, each photograph tagged, captioned and sheeted in turn, and
`python -m isekai render` between `python -m gpunit volume up` and `volume down`,
as children, so the CLI stays the one path a stage runs through, and
`interface/ui/events.py` streams what they report to the page as `/events`.
Every other write the server makes runs in its own process, through the function
that owns it: stage ③'s review functions, import's reader, `sheet()` for a
target's first sheet when a draft is made from another flow, filled from the
photograph's tags — `interface/drafting.py`'s `draft_across` runs it, the same
sequence the CLI's `draft` runs (D4) — and, for a deleted render, the library's
`drop_thumbnails`, the render stage's `discard_render` and review's `withdraw`;
the CLI's `discard` calls them too, but drops the render's thumbnails and not each
edit image's.

**The edit's pieces.** `ink` is `shared/ink.py`'s, which `run_ink` of `interface/verbs/edits.py` calls; the maths of an edit is
`shared/tattoo.py`'s, over arrays, and Pillow and numpy are imported inside both modules' functions. The edit stage is
`pipeline/edit.py`, which `run_edit` of `interface/verbs/edits.py` and `interface/render.py`'s session both call, and which imports no
stage: the transport helpers it shares with `pipeline/generate.py` — `submit_and_wait` and `read_runtime` — moved to
`boundary/comfy/prompt.py`, behind the package's front door, for that reason
([D51](decisions.md#d51--an-edit-is-one-flat-directory-pinned-by-its-digest)). A session runs a pending edit as
`edit --pending` lines, so the render verb creates the pod and an edit rents nothing of its own (D36).
`wiring.py` imports `boundary/ollama.py` for the probe a job asks first.

**The placement's pieces.** `chain` is `shared/chain.py`'s, over arrays, importing only `foundation/refusal.py`; its
`place` carries an ink layer through the stages' splines and `flatten` puts it on white. The ink view, the stage-1
file, `preview` and `composite` are `pipeline/tattoos.py`'s, with the tattoo library: it imports `shared/chain.py`,
`shared/ink.py` and `shared/tattoo.py` and no stage, and the tattoo routes of `interface/ui/app.py` call it, writing no
file of their own ([D52](decisions.md#d52--the-tattoo-library-is-kept-whole-until-a-tattoo-is-removed)). A bake's
route calls `composite` and then `request_placed` of `pipeline/edit.py`, which writes the composite, the placement
record and the edit's record ([D53](decisions.md#d53--a-placement-is-recorded-beside-its-edit)). Pillow, and numpy in
`chain`, are imported inside functions, so neither module puts a wheel on the entry point's graph.

**The proposal's pieces.** `unpack` is `boundary/unpack.py`'s and imports `boundary/provision.py`, which it leaves
unedited because the pod image copies it; `pose` and `sam2` are `boundary/pose.py`'s and `boundary/sam2.py`'s, each
importing `provision`, `unpack`, `wd14`'s `silence_onnxruntime` and `foundation/refusal.py`, with `onnxruntime`, numpy
and Pillow imported inside their functions. `proposal` is `shared/proposal.py`'s, the geometry over arrays, importing no
other module of the package. `proposing` is `pipeline/proposing.py`'s: it imports `pose`, `sam2` and `proposal` and no
stage. `interface/wiring.py` opens `pose` and `sam2` once into a `Proposer`, and the propose route of
`interface/ui/app.py` calls it in the server's process and writes no file
([D54](decisions.md#d54--automatic-pairs-run-on-the-operators-machine-and-are-kept-nowhere)).

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
`boundary/comfy/` and `pipeline/generate.py` import them rather than define them. `edit` is the same
(`foundation/edit.py`): the registry of an edit, loaded and pinned as a flow is, and `graph_digest` lives in `flow`.

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
  its own path. `interface/ui/`, `interface/verbs/` and `boundary/comfy/` are not
  groups: each is a sub-package with a front door, its `__init__.py`, and nothing outside it imports
  past that door. `tests/test_layers.py` holds both rules.

## How the components interact

The graph above says what may import what; this says who builds, who calls, and
what carries data at run time.

```
  python -m isekai <verb>       interface/verbs/
          │                           │ its rows
          ▼                           │
  interface/cli.py ◀──────────────────┘
          │
          ├──builds──▶ interface/wiring.py ──▶ a Wiring
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
  to the UI its `ui` verb starts (`run_ui` of `interface/verbs/library.py`). The UI builds one collection's
  wiring per request through `wiring_from`, so the runs-root guard holds for each
  collection, and no module under `interface/ui/` imports `cli.py`. Review holds both.
- **Each front end calls the stage functions directly.**
- **A stage reads and writes its run directory.** No stage imports another stage;
  `tests/test_layers.py::test_no_stage_imports_another` holds this. Every run
  file's JSON is written through `foundation/artifacts.py`'s `write`;
  `tests/test_artifact_bytes.py::test_only_the_contract_writes_a_run_file` holds
  that. The photograph's copy and a render's image are bytes, written by
  `foundation/atomic_write.py`; `foundation/migrate.py` copies a description's
  files byte for byte into a partial directory it renames whole.
- **A stage reaches a model, the GPU or the network through `boundary/`.**
- **`foundation`'s run, artifacts, flow and refusal are what every layer uses.**
- **`StageFailure` lives in `foundation/run.py`, not `refusal.py`.** `refusal.py`
  imports nothing, the class needs `Kind`, and `run.py` already imports
  `refusal.py`, so the move would be a cycle.
