# Design — 0027 the seams

How the layers are made true and held by a test, without changing what the system does.
**Verdict: `feasible`.** Every file, symbol and line below was re-checked at `main` `9b3fca2`.

## Context

- **These imports break the layers** of `docs/principles.md`'s *The code is layered*. They are the edges
  [D3](#d3)'s allowlist starts with:

  | importer | imports | kind |
  |---|---|---|
  | `isekai/foundation/flow.py:41` | `isekai.boundary.comfy_types` (`Workflow`) | module scope |
  | `isekai/foundation/run.py:42` | `isekai.shared.atomic_write` (`write_atomically`) | module scope |
  | `isekai/shared/vocabulary.py:119` | `isekai.boundary.provision` | lazy, in `load()` |
  | `isekai/shared/vocabulary.py:120` | `isekai.evaluation.eval_models` (`resolve`) | lazy, in `load()` |
  | `isekai/boundary/wd14.py:242` | `isekai.evaluation.eval_models` (`entry_for`, `resolve`) | lazy, in `verified_paths()` |

- **Already true, and held by nothing:** no pipeline stage imports another, and no module cycle exists.
  `isekai/` has no relative import and no `import isekai.…` statement; every import is `from isekai.… import`.
- **The gate's commands are written in** `.minions/minions.toml:1-8`, `Makefile:10-16`, `CLAUDE.md:42-48`
  and `README.md:300-305`, and CI runs `make gate` (`.github/workflows/ci.yml:45-46`). No test
  reads any of them. The MinionsFactory skills run `make gate`; none reads the toml.
- **`ENCODER_WINDOW = 77` is written at** `isekai/pipeline/review.py:67` **and at** `ui/src/types.ts:104`,
  read by `ui/src/components/TokenBudget.vue` and `ui/src/components/RunManifest.vue`.
- **The vocabulary-dependent tests skip wherever `models/wd14/selected_tags.csv` is missing**: the
  `provisioned` fixture at `tests/test_field_map.py:32-40`, `tests/test_vocabulary.py:82-86`, and
  `tests/test_wd14.py:67-75`.
- **`interface/wiring.py` is already the only production caller of the vocabulary loader** (`:36`, `:232`);
  `interface/cli.py` and `interface/ui/batch.py` import only the `Vocabulary` type.
- **The CLI's transport wrapper is exercised by tests through fakes**, not through `ComfyClient`:
  `tests/test_generate.py:715-740` imports `cli._Reporting`, and `tests/test_resume.py:545-578` injects a
  fake client that raises `URLError` through `dispatch`.
- **`review.is_complete` has no production caller** — only `tests/test_review.py:172` and `:202`.
- **Line numbers are `9b3fca2`'s.** A builder re-resolves each by the text it names.

## Goals / Non-Goals

**Goals**

- Every import in `isekai/` points down a layer, and a test fails on one that does not.
- The CLI and the review UI compose and do nothing else.
- The gate and the encoder window are each declared once.
- The vocabulary-dependent checks cannot skip silently on the operator's machine.

**Non-Goals**

- Any change to a refusal's text, a failure's kind, or a byte a run writes.
- The run files' shapes, the approval defects, and the transport's own defects — see the proposal's
  *Not in this change*.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the gate lives in `Makefile` alone; `.minions/minions.toml` is deleted | one declaration needs no check; no skill reads the toml | a test holding the copies equal |
| [D2](#d2) | `ENCODER_WINDOW` stays in `review.py`; the budget payload carries it | the browser decides nothing about the window | a test holding both copies equal |
| [D3](#d3) | `tests/test_layers.py`, an AST scan, lands first with an exact allowlist | each phase's gate proves its edge gone | the test last, written to fit the result |
| [D4](#d4) | `tests/test_principles.py` resolves every test a *held by* line names | a renamed test silently orphans its principle | checking the prose names too |
| [D5](#d5) | the vocabulary checks fail when the file is missing, unless CI declares it absent | the operator's machine runs the gate at every phase and release | fetching the vocabulary in CI |
| [D6](#d6) | `atomic_write` and `Workflow` move into `foundation` | both are used by `foundation` and know nothing above it | re-exporting them from the old paths |
| [D7](#d7) | `resolve`, `entry_for` and their exceptions move into `boundary/provision.py` | they only wrap `provision`'s own checks | a second resolver per consumer |
| [D8](#d8) | `wiring.load_vocabulary` verifies; `vocabulary.load` only reads | `shared` parses, the boundary verifies, the front end composes | verifying inside `shared` |
| [D9](#d9) | the transport becomes `boundary/comfy/`; the client classifies its own failures | a rule about the work belongs to the component that owns it | leaving the classification in the CLI |
| [D10](#d10) | a prose delta; preambles edited in place | a delta cannot carry a `## Purpose` | leaving a false module name |
| [D11](#d11) | `state()` moves into `review.py` unchanged; `is_complete` is deleted | the UI owns no approval rule; reconciling the definitions changes behaviour | fixing the draft definitions here |
| [D12](#d12) | the docs follow each move; `docs/` and `CLAUDE.md` last | a group README names files, so it moves with them | one docs sweep at the end for everything |
| [D13](#d13) | phases: declare once, checks, foundation, pins, transport, approval, docs | the checks land before the moves they hold | the moves first |
| [D14](#d14) | this is a patch | it meets every patch condition | a minor |

### D1

**The gate lives in `Makefile` alone.**

- Delete `.minions/minions.toml`. `.gitignore:4-9` becomes one line, `.minions/`, with a one-line comment:
  MinionsFactory's run artefacts, all of them local.
- **The per-command notes move into `Makefile`**, as comments above each command: what `CLAUDE.md:42-48`
  says of each today. `Makefile:1-6`'s header says the recipe is the gate's one declaration, that CI and the
  MinionsFactory skills run it, and that `make -n gate` prints it.
- **Every other copy points at it and lists no command:**

  | file | before | after |
  |---|---|---|
  | `CLAUDE.md:38-53` | the list, and *"the array is the one that is run … three copies"* | *the gate is `make gate`; `make -n gate` prints what it runs; the notes on each command are the `Makefile`'s* |
  | `CLAUDE.md:57-59` | *"not an entry in the array … adding it to the `Makefile`"* | the same convention, naming the `Makefile` alone |
  | `CLAUDE.md:168-170` | *"`minions.toml`, the gate command list, is the one tracked file in it"* | *`.minions/` — MinionsFactory's run artefacts, gitignored whole* |
  | `README.md:289-310` | the list, and *"declared once, as the `gate` array"* | *run `make gate`; `make -n gate` prints its commands*; the `npm install` note on the browser half stays |
  | `README.md:352` | *`.minions/minions.toml # the gate array`* | the line is deleted |
  | `.github/workflows/ci.yml:41-44` | *"declared once, as the `gate` array in .minions/minions.toml"* | *the gate is the `Makefile`'s `gate` target* |
  | `scripts/typecheck_ui.sh:7-11` | *"what the `gate` array in .minions/minions.toml names"* | *what the `Makefile`'s `gate` target runs* |
  | `pyproject.toml:57` | *"none of the commands in the array installs it"* | *none of the gate's commands installs it* |

### D2

**`ENCODER_WINDOW` is declared once**, at `isekai/pipeline/review.py:67`.

- `isekai/interface/ui/app.py`'s `_budget` (`:457-463`) adds `"window": ENCODER_WINDOW`, imported from
  `isekai.pipeline.review`.
- `ui/src/types.ts`: `Budget` gains `window: number`; `ApprovedSheet` gains `window: number`; the constant and
  its comment (`:101-104`) are deleted.
- `ui/src/components/TokenBudget.vue` reads `budget.window`. **With no budget yet it shows `—` for the window,
  as it already does for the total** — the one visible difference, in the loading frame only.
- `ui/src/ReviewApp.vue`'s `openManifest` (`:227-242`) sets `window: body.budget.window`;
  `ui/src/components/RunManifest.vue` compares each sheet's `tokens` with its own `window`, and its note names
  the first over-budget sheet's `window`.
- A test in `tests/test_ui_api.py` asserts the budget's `window` equals `review.ENCODER_WINDOW`, bound
  `spec_exempt("structural: the encoder window is declared once, and the browser reads it from the budget")`.

### D3

**`tests/test_layers.py` holds the layers.** It parses every `*.py` under a root with `ast`, including imports
inside functions, and resolves each `from isekai.X import n` to `isekai.X.n` when that is a module, to
`isekai.X` otherwise. The layer order is `foundation`, `shared`, `boundary`, `pipeline`, `interface`,
lowest first.

| rule | scope |
|---|---|
| an import never names a higher layer | modules under `isekai/` |
| nothing outside `isekai/evaluation/` imports `isekai.evaluation` | modules under `isekai/` |
| no module in `isekai/pipeline/` imports another module in `isekai/pipeline/` | every stage |
| no import cycle among the modules of one layer | each layer |
| `isekai/__init__.py` and each layer's `__init__.py` hold only a docstring | the root and every layer |
| a sub-package inside a layer is imported only through its `__init__.py` from outside it | importers under `isekai/`, `probe/`, `scripts/`, and `evaluate.py` |

- **`isekai/__main__.py` sits above every layer**: the shim `runpy` resolves, it may import `interface`.
- **Exempt:** `tests/` — a component's own tests may reach inside it, and they cannot be told apart by path —
  and `isekai/evaluation/`'s own `__init__.py` and sub-structure, which the tree reorganisation moves.
- **The allowlist** is the [Context](#context) table's edges, as `(importer path, imported module)` pairs.
  **It is exact:** an allowed edge that no longer exists fails `test_the_allowlist_names_only_imports_that_exist`,
  so the phase that moves an import deletes its entry. [D13](#d13)'s docs phase deletes the allowlist, its test,
  and every reference to it.
- **Each rule ships with a twin** that builds a small package under `tmp_path` breaking that rule and asserts
  the check reports it.
- The rule tests, by name — [D12](#d12) cites them in `docs/principles.md`:
  `test_every_import_points_down`, `test_nothing_in_the_package_imports_evaluation`,
  `test_no_stage_imports_another`, `test_no_import_cycle_inside_a_layer`,
  `test_a_layer_init_holds_only_a_docstring`, `test_a_subpackage_is_reached_only_through_its_front_door`.
- Every test here is `spec_exempt("structural: …")` — the layers are not behaviour.

### D4

**`tests/test_principles.py` holds the *held by* lines of `docs/principles.md`.**

- A principle is a `### ` section. Its `- **Held by:**` bullet runs until the next top-level `- **` bullet
  or heading, sub-bullets included.
- Every `` `tests/<file>.py::<name>` `` in it must name a function `<name>` defined at module level in
  `tests/<file>.py`. Prose names — `FakeReader`, *review* — are not checked.
- Every principle has exactly one *Held by* bullet.
- Twins: a principles text naming a test that does not exist, and one with a principle lacking the bullet;
  each is reported. `spec_exempt`, as [D3](#d3).

### D5

**The vocabulary checks are strict wherever CI has not declared the vocabulary absent.**

- `tests/conftest.py` gains `require_vocabulary(path)`: it returns if `path` exists; skips if the environment
  variable `ISEKAI_VOCABULARY` is `absent`; and otherwise fails, naming `VOCABULARY_REMEDY`
  (`bash scripts/download_models.sh scripts/vocabulary.json`).
- It replaces the skips at `tests/test_field_map.py:33-40`, `tests/test_vocabulary.py:85-86` and
  `tests/test_wd14.py:69-75`, with the comments that say a missing file skips.
- `.github/workflows/ci.yml`'s `Gate` step sets `ISEKAI_VOCABULARY: absent`, with a comment: CI fetches
  nothing from Hugging Face. The skips on the operator's gitignored `.data/v0.20` runs
  (`tests/test_field_map.py:372-373`, `:440-441`) stay.
- Twins in `tests/test_vocabulary.py`: a missing file with the variable unset fails; with it set to `absent`,
  it skips. `spec_exempt`.

### D6

**`foundation` imports nothing above it.**

- `git mv isekai/shared/atomic_write.py isekai/foundation/atomic_write.py`, content unchanged.
  Importers: `isekai/foundation/run.py:42`, `isekai/pipeline/generate.py:63`,
  `tests/test_run_directory.py:17` and its comment at `:214`.
- `Workflow = dict[str, Any]` moves from `isekai/boundary/comfy_types.py:7` to `isekai/foundation/flow.py`,
  which owns the graph. Importers: `isekai/boundary/comfy_types.py` (for its Protocol),
  `isekai/boundary/comfy_client.py:8`, `isekai/pipeline/generate.py:39`, `isekai/interface/cli.py:50-55`,
  and `tests/conftest.py:7`, `tests/fakes.py:3`, `tests/test_generate.py:19`, `tests/test_image.py:6`,
  `tests/test_infra.py:13`, `tests/test_manifest_binding.py:3`.
- **No re-export.** A name is imported from the module that defines it.

### D7

**Pin verification is `boundary/provision.py`'s.** `entry_for`, `resolve`, `UnknownArtifact`,
`UnpinnedArtifact` and `EscapingDestination` move from `isekai/evaluation/eval_models.py:56-124`,
docstrings and texts unchanged.

- **`resolve(dest, models_dir, manifest)` takes the manifest; it no longer defaults to the eval manifest**,
  which `boundary` cannot import. `isekai/evaluation/eval_backends.py`'s calls at `:159`, `:374` and `:545`
  pass `load_eval_manifest()`, which is what the default loaded.
- **`entry_for`'s refusal keeps its text**, `f"{dest} is not declared in eval_models.json"` — written as a
  literal, since `EVAL_MANIFEST_PATH` stays in `evaluation`. That it names the wrong file for the vocabulary's
  manifest is a recorded defect for the defects patch, not a fix here.
- `isekai/boundary/wd14.py:241-242` imports `entry_for` and `resolve` from `isekai.boundary.provision`, still
  inside `verified_paths()`.
- `eval_models.py` keeps `EVAL_MANIFEST_PATH`, `SHARED_WITH_THE_GRAPH`, `RECOGNIZER`, `load_eval_manifest` and
  `shared_entries_that_differ`.
- Tests: `tests/test_eval_manifest.py:17-27` imports the moved names from `provision`;
  `tests/test_wd14.py:41` and `:255` patch `provision.resolve`.

### D8

**The front end verifies the vocabulary; `shared` only reads it.**

- `isekai/shared/vocabulary.py`'s `load` becomes `load(path, entry)`: it reads the file at `path` and takes
  the revision and digest from `entry`, a `Mapping[str, Any]`. It imports nothing from `boundary` or
  `evaluation`. `VOCABULARY_DEST`, `DEFAULT_MODELS_DIR` and `VOCABULARY_REMEDY` stay.
- `isekai/interface/wiring.py` gains `load_vocabulary(models_dir=DEFAULT_MODELS_DIR)`: it loads the vocabulary
  manifest, calls `provision.resolve`, turns a `FileNotFoundError` into the same `Refusal` text
  `vocabulary.py:128-134` raises today, finds the entry, and calls `vocabulary.load`. **It imports
  `provision` inside the function**, so `provision.py` stays off `python -m isekai`'s import graph, as the
  `model-provisioning` preamble states. `wiring_from` keeps `vocabulary=load_vocabulary`.
- **`scripts/derive_field_map.py:625` calls `wiring.load_vocabulary()`**, so the verify-then-load pair is
  written once. The grilling said *its own two calls*; the operator settled this form at the cut, since it
  keeps that decision's reason.
- Tests calling the old loader call `wiring.load_vocabulary`: `tests/test_field_map.py:35-40`,
  `tests/test_vocabulary.py:83-87`, `tests/test_vocabulary_manifest.py:35` and `:290`.

### D9

**The ComfyUI transport is one package, `isekai/boundary/comfy/`, with a front door.**

```
isekai/boundary/comfy/
├── __init__.py    the front door: ComfyTransport, ComfyClient, Unreachable, Image
├── contract.py    ComfyTransport (the Protocol), Image, Unreachable   ← comfy_types.py
├── client.py      ComfyClient, and the failure classification          ← comfy_client.py + cli.py:569-586
└── multipart.py   build_multipart, private to the package              ← boundary/multipart.py
```

- `git mv` each file, so its history follows. `contract.py` imports `Workflow` from `isekai.foundation.flow`.
- **The classification moves word for word.** `_reported()` (`isekai/interface/cli.py:569-586`) moves into
  `client.py`, and every `ComfyClient` method runs inside it: a `urllib.error.URLError` or `OSError`
  becomes `Unreachable`, with the same text. `_Reporting` (`cli.py:542-565`) and its use at `:522` are
  deleted; `render` receives `wired.client` directly.
- **Importers use the front door:** `isekai/pipeline/generate.py:39`, `isekai/interface/wiring.py:25-26`,
  `isekai/interface/cli.py:50-55`, `probe/loader_probe.py:37`, `tests/fakes.py:3`. Only the package's own
  tests import a module inside it: `tests/test_multipart.py:3` imports `isekai.boundary.comfy.multipart`.
- **Tests that exercised the wrapper drive a real `ComfyClient`**, with `urllib.request.urlopen` patched to
  raise `URLError`: `tests/test_generate.py:715-740` (drop the `_Reporting` import at `:42`) and
  `tests/test_resume.py:545-578`. Their assertions and bindings stay.
- **Pays `comfy-transport:boundary`.** `test_multipart_content_type_declares_the_boundary`
  (`tests/test_multipart.py:6-9`) builds a body with a field and a file, and asserts that the boundary its
  content type declares opens each part and closes the body.
- `probe/loader_probe.py` now receives `Unreachable`, a `Refusal`, where it received a raw `URLError`. It is
  operator tooling that no test runs.

### D10

**A prose delta, and the preambles edited in place.**

- [specs/comfy-transport/spec.md](specs/comfy-transport/spec.md): the note under *Hand-built multipart
  encoding*'s scenarios names `comfy_client.history()`; it becomes `ComfyClient.history()`. No SHALL changes.
- Preambles, which a delta cannot carry: `openspec/specs/comfy-transport/spec.md:8-10` (*Source*) and `:13`
  name `comfy_types.py`, `comfy_client.py` and `multipart.py`; `openspec/specs/run-directory/spec.md:11`
  names `isekai/shared/atomic_write.py`.

### D11

**The approval state is the pipeline's.**

- `Status` (`isekai/interface/ui/batch.py:48-51`) and the body of `Batch.state` (`:136-159`) move into
  `isekai/pipeline/review.py` as `state(directory) -> Status`, docstring and logic unchanged.
  `Batch.state(held)` stays as one line that passes the review directory to it, so `isekai/interface/ui/app.py`
  is unchanged.
- `isekai/interface/run_view.py:101` calls `run.is_approved(name)` instead of comparing the label itself.
- `review.is_complete` (`isekai/pipeline/review.py:78-85`) is deleted. `tests/test_review.py:172` asserts
  `state(directory) == "draft"`, and `:202` asserts `state(directory) == "approved"`; the tests keep their
  names and bindings, so `docs/principles.md`'s *held by* line for *A person approves every sheet* names a
  test of `review.state`.
- `draft_versions`, `approve`'s choice of draft, and `Batch.draft_path` are untouched; their disagreement is
  the defects patch's.

### D12

**The docs follow the code.**

- **In the phase that moves a file:** its group README's file table and importer table —
  `isekai/README.md`, `isekai/foundation/README.md`, `isekai/shared/README.md`, `isekai/boundary/README.md`,
  `isekai/evaluation/README.md`, `isekai/interface/README.md`.
- **In the docs phase:**
  - `docs/modules.md` — *The edges, by source*, the lazy edges, *The cycles* and *Reading this graph* are
    rewritten to the new graph: no cross-layer cycle, no lazy edge out of a layer, `boundary/comfy/` beside
    `interface/ui/` as a sub-package with a front door, and `tests/test_layers.py` holding what review held.
  - `docs/principles.md`:

    | principle | before | after |
    |---|---|---|
    | *Only a front end composes* | *Known breaks:* the CLI's transport classification; the UI's approval states | the bullet is deleted |
    | *The code is layered* | *Held by: not yet …* | *Held by:* [D3](#d3)'s rule tests, by name |
    | *Configuration is declared …* | *Known breaks:* the gate list; the window twice; the field map skips *"where the vocabulary is not provisioned, which includes CI"* | the sampling options, and: the field map's re-derivation skips in CI, which declares the vocabulary absent; the network derivers are never re-run |
    | *The run directory is the only channel …* | *not yet … no test forbids an import between stages* | `tests/test_layers.py::test_no_stage_imports_another`; the shapes stay *not yet* |

  - [D10](#d10)'s preambles; `CLAUDE.md` and `README.md` per [D1](#d1).
  - **`v0.22.3 review/R10`, residual:** `CLAUDE.md:63`, `:102` and `:127` are re-flowed to the file's wrap.

### D13

**Phases**, each green alone:

```
1 declare once   D1 · D2
2 checks         D3 (allowlist: Context's edges) · D4 · D5
3 foundation     D6                        allowlist − flow.py, run.py
4 pins           D7 · D8                   allowlist − vocabulary.py ×2, wd14.py
5 transport      D9
6 approval       D11
7 docs           D10 · D12 · the allowlist deleted
```

### D14

**This is a patch.** It meets each condition `CLAUDE.md` states:

| condition | met because |
|---|---|
| no format version moves | no `flows/` file, manifest or artifact writer changes; `MANIFEST_VERSION` and `SCHEMA_VERSION` are untouched |
| a behaviour fix is required by an existing requirement | no behaviour is fixed; the delta corrects a module name |
| nothing deprecates a verb or a flag | no verb or flag changes |
| nothing changes the product | the sheet, the prompt and the image are untouched; the budget payload gains a field |

## Dependencies

None.

## Risks / Trade-offs

- **A move changes behaviour by accident** — an exception now caught in a new place, an import order. →
  Every refusal text moves verbatim, and the tests that pin them — `tests/test_generate.py:715-740`,
  `tests/test_resume.py:545-578`, `tests/test_vocabulary_manifest.py:290` — keep their assertions.
- **`ComfyClient` classifying its own failures also classifies an `OSError` from reading the local photograph
  in `upload_image`.** → The CLI's wrapper did the same; moving it word for word keeps it. The defects patch
  owns the transport's classification.
- **A fresh clone's gate fails until the vocabulary is fetched.** → Deliberate ([D5](#d5)); the failure names
  the command.
- **The AST scan misses an import spelled another way** — `importlib`, `__import__`. → `isekai/` has none
  that load its own modules; its `import_module` calls load third-party wheels.
- **The allowlist outlives the moves.** → It is exact, and the docs phase deletes it with its test.

## Verdict

**`feasible`.** Structural, every site re-checked at `9b3fca2`, no refusal text or artifact byte changes,
and every test that pins a moved behaviour keeps its assertion.
