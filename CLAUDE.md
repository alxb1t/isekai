# isekai — shared context for Claude Code

A self-hosted, headless pipeline: **photo of a person → anime image of that same person**, using open
models on an on-demand RunPod GPU running our own ComfyUI image. It exists to learn — and to show — how
open image models are run end to end, from container to rented GPU to CLI.

**The method this repo runs is OpenSpec SDD** — work is defined as a change before it is built, the
living spec is test-backed, and a release folds one into the other. `## How a change is cut here`, below,
is the in-tree statement of that contract. Everything else in this file is what is true of **this
repository in particular**.

Hard constraints that shape the code here:

- **Identity preservation is the product.** A beautiful anime image of someone else is a failed run.
- **The runtime is stdlib-only** — the ComfyUI transport is `urllib`, and nothing in `convert.py`'s import
  graph may need a wheel. Face detection runs *in the image*, never as a runtime dep.
- **There is one path. A version may replace it; it may not add a second.** Four selectable models were
  how the product was *found*; carrying three dead ones was the cost of not deciding.

> **This file is shared, role-independent context — what is *true* about this repo. It is not a script.**
> What you should *do* comes from the **prompt/task you were given**. If your prompt conflicts with this
> file, **the prompt wins.** Read this for the facts; follow your prompt for the actions — don't infer a
> workflow from this file alone.

---

## The quality gate — this repo's five commands

**These** are the commands this repo declares, in `.minions/minions.toml`'s `gate` array, in order:

- `uv sync --locked` — environment, from the tracked lock; not a quality axis, hence first
- `uv run ruff format --check .` — format, in check mode (a rewrite is not the check)
- `uv run ruff check .` — lint
- `uv run ty check` — strict types
- `uv run pytest` — tests

`Makefile`'s `gate` target, `README.md` and CI (`.github/workflows/ci.yml`) mirror that array; the array is
the one that is run. Change one, change all four.

All five green, or the phase is not done. **Never weaken the gate to pass** — see the guardrails.

Beyond the array, **image-as-code phases also run `bash -n` on shell scripts and `docker build --check`**.
That is a convention for those phases, not an entry in the array; adding it to one means adding it to the
`Makefile` in the same commit.

**The suite runs offline and deterministically.** The ComfyUI transport is faked behind a `ComfyTransport`
Protocol (`FakeComfyClient`), the suite reads the shipped graph itself rather than a fixture copy of it,
and mutation takes an injected `random.Random`. No test hits a GPU or the network — which is why every scenario declares `Layers: unit`
and none declares `e2e`. Diffusion quality and identity fidelity are verified **live on a pod, by eye**,
never mocked and never asserted.

---

## Engineering conventions

The active change's **`design.md`** is authoritative, with this file behind it — read it. It *is* the
decision record: the reasoning that settled a decision, and the measurement behind it, are written there
and nowhere else. In brief, the load-bearing seams are:

- **A parameter is a seam only if something else is actually passed through it.** That is why `client` is a
  parameter of `pipeline.run` — `FakeComfyClient` is what makes the whole suite offline — and `workflow` is
  one, keeping file I/O in the CLI, while `inject` and `mutate` are **imported**: neither ever had a second
  implementation or a test double. A one-entry registry is a dispatch mechanism with nothing to dispatch.
- **Injection** (`isekai/workflow.py`) — a plain function that wires the photo into the graph, and nothing
  else. The positive prompt is committed to the graph, so there is nothing to place. The non-obvious fact a
  future tagger will need: `KSampler.positive` may point at `ApplyInstantIDAdvanced` directly **or** through
  a stack of `ControlNetApplyAdvanced` nodes, so the encoder must be found by following the link, never by
  class lookup.
- **`mutate(workflow, rng)`** (`isekai/mutate.py`) — variation, kept *separate from* injection: injection
  wires, mutation jitters dials. The `rng` is injected, which is the whole reason it is testable.
- **`apply_overrides`** (`isekai/overrides.py`) — the user's **base** dial values. The order is
  **load → override → mutate**: `mutate` jitters *around* the base the user set, never over it.
- **`ComfyTransport`** (`isekai/comfy_client.py`) — the network boundary, and the only one.

**Tests are bound to the spec.** Every test carries `@pytest.mark.spec("<key>")` naming the scenario it
proves, or `@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural. Both are registered in
`[tool.pytest.ini_options] markers` — registration is load-bearing, because pytest silently ignores an
unregistered marker, so an unregistered one would bind nothing while looking exactly like a binding.
Behaviour gets a scenario first; a new test gets a binding.

---

## How a change is cut here

Work is defined before it is built, as a change under `openspec/changes/<id>/`. A change is the unit of
work **and** the unit of release.

A change is **four artifacts, always all four**: `proposal.md` · `specs/` · `design.md` · `tasks.md`.

1. **Settle the decisions first.** A change is cut from decisions argued against a person, not from a first
   draft. The verdict — `feasible` / `feasible-with-caveats` / `needs-precursor` /
   `infeasible-as-specified` — is recorded in the change's `design.md`.
2. **Scaffold by hand** — `openspec` 1.11 ships no `new`/`scaffold` command, so the directory is created
   directly. The id is `<digits>-<lowercase-slug>`, and version → id is `(major × 100) + minor`,
   zero-padded: `v0.7` → `0007`, `v0.10` → `0010`, which stays monotonic past 1.0. (`0001-mf-standard`
   predates this rule and keeps its id — an id is never renamed once commits carry it as a trailer.)
3. **Author** each artifact against `openspec instructions <proposal|specs|design|tasks> --change
   <NNNN-slug>`, one at a time, fetching each immediately before writing it. `proposal.md` additionally opens with `version: vX.Y`
   frontmatter — **the CLI neither emits nor checks that key; it is on the author.**
4. **A change that changes no requirement** declares the absence rather than inventing one: `skip_specs:
   true` in the change's tracked `.openspec.yaml`, plus `specs/.gitkeep`. The two are mutually exclusive.
   Never write a requirement solely to satisfy the validator.
5. **Finish on a green check** — `openspec validate <NNNN-slug> --strict`.

**Progress lives in `tasks.md`**, in its `## Progress` checklist, and **the current phase is the first
unchecked box**. A phase is advanced by a commit **and** a ticked box, in that phase's own commit — either
alone is not an advance.

**The living spec** is `openspec/specs/<capability>/spec.md` — five capabilities: `model-registry`,
`workflow-injection`, `workflow-mutation`, `comfy-transport`, `cli`. Every `#### Scenario:` carries a
`- **Key:**` and a `- **Layers:**` bullet, and the key is
`<capability>:<requirement-slug>:<scenario-slug>` — so a key locates its own file. On release the delta is
folded in and the change moves to `openspec/changes/archive/`; archived changes are never deleted.

**The version line is one line in four places** — `proposal.md`'s `version: vX.Y`, `CHANGELOG.md`'s
`## [X.Y.0]`, `pyproject.toml`'s `version`, and the annotated tag `vX.Y.0`. All four agree or the release
halts. One branch per version. `CHANGELOG.md` follows Keep a Changelog + SemVer, with an entry appended
**per phase** under `## [Unreleased]` and cut at release.

Every commit is a Conventional Commit, **one phase = one commit**, staged **by name** and never with
`git add -A`. Each carries a `Change: <change-id>` git trailer, in the trailer block at the end of the
message and **contiguous** with any `Co-Authored-By:` line — a blank line between them silently breaks the
block.

The tooling is **operator tooling, recorded and not pinned**: `@fission-ai/openspec@1.11.0`, resolved on
`PATH`. It is deliberately **not** in the gate array — nothing in CI runs it, so a moving version can never
turn CI red. There is **no spec↔test binding checker in this repo**, so `spec` / `spec_exempt` bindings are
maintained by hand and reviewed, not enforced; that gap is known and open.

---

## Layout — where things live here

- **`convert.py`** — the CLI entry point. **`isekai/`** — the package: registry, injection, mutation,
  overrides, transport, pipeline. **`tests/`** — the suite and its fakes.
  **`workflows/`** — `pipeline.json`, the API graph the run loads, and `pipeline_ui.json`, the ComfyUI
  export it is regenerated from by hand. **`infra/`** — `up.sh` / `down.sh`,
  the pod lifecycle. **`scripts/`** — model download, run *on the pod*. **`Dockerfile`** — the image that
  *is* the pod.
- **`openspec/`** — the living specs and the changes. Authoritative for what is being built and how far
  along it is.
- **`.minions/`** — run artefacts, **gitignored**; `minions.toml`, the gate command list, is the one
  tracked file in it. `git check-ignore` reports the *directory* as not ignored precisely because of that
  one file — always check a file path.
- **Everything a run reads or writes is inside the repository.** No path outside the repo is resolved by
  anything tracked here. Research notes and the running log live in the operator's own notebook; nothing
  in this repo reaches into it, and its location is not recorded here.

## The path

One graph, `workflows/pipeline.json`, on an Animagine XL 4.0 (SDXL anime) base. Nothing about it is typed
at the command line: the whole required surface is `convert.py photo.jpg`. Identity is four axes, and each
is carried by a mechanism rather than by a sentence someone types:

- **Face** — InstantID + InsightFace: face embedding and keypoints. `ip_weight` is its dial.
- **Composition** — **img2img**: latent init from the photo (`VAEEncode`, `denoise < 1`). `denoise` is the
  identity↔style dial.
- **Pose and structure** — a **ControlNet stack** (tile → OpenPose → Lineart), each with its own tuned
  strength.
- **Register** — the positive prompt, **committed to the graph** and pinned by equality in the suite, so
  changing it is a deliberate test edit. `1girl, solo` is the Danbooru mode selector for this base; that
  `1girl` fixes the gender of every input photo is a known defect, recorded in `CHANGELOG.md` and owned by
  the version that changes the base.

---

## Guardrails (invariants — hold for every role)

- **Never commit a secret, or a *real* absolute path from the machine the run is on** — the RunPod API key,
  the volume id, the operator's home, or this repository's own root, transcribed out of a run artefact or a
  tool's output into tracked prose. `.env` is gitignored and holds all of it; `.env.example` declares shape
  only. A path a fixture *constructs* is not the target of this rule; a rendered one, carrying a real
  username, is.
- **Deps minimal + human-gated.** The runtime is stdlib-only. Any new dependency — argue for it and **wait
  for approval** before installing. pytest / ruff / ty stay dev-only.
- **Never weaken the gate to pass.** A deleted or skipped test, a blanket suppression, a loosened config —
  each is a *plan* problem, not a coding shortcut. **Halt and say so.**
- **State lives on disk.** Reconstruct "where are we" from the active change's `tasks.md` + git — never
  from memory.
- **Some phases spend real money.** The active change's `tasks.md` marks metered (⚠️ GPU) phases, and the
  stop-before-spending protocol holds: announce, wait for an explicit human "go", `up.sh` → tunnel →
  `convert.py` → `down.sh`, tear down, log the cost. **Never bring up a paid pod on your own initiative.**
- **GPU renders live on the pod's ephemeral disk**; only the models volume persists. Download before
  teardown or the output is gone.
- **The Blackwell (sm_120) pod needs cu128 PyTorch** — cu124 gives "no kernel image". It is pinned in the
  image; keep it.
