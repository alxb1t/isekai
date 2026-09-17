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
- **The runtime is stdlib-only** — the ComfyUI transport is `urllib`, and nothing in
  `python -m isekai`'s import graph may need a wheel. Face detection runs *in the image*, never as a
  runtime dep.
- **A selectable implementation is a measured one.** Nothing enters the registry on the strength of
  being written; it enters on a measurement against the bar its capability states, and it is removed
  only by the version that retires it. This replaces the older rule *"there is one path"* rather than
  restoring it: a **count** would forbid the flow registry v0.16 adds, and — the reason the rule
  existed — a count also permits an *unmeasured* single path, which is exactly what the graph v0.14
  deleted was. Four selectable models were how the product was *found*; carrying three dead ones was
  the cost of not deciding, and carrying one unmeasured one was the cost of counting instead of
  measuring.

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
and seed drawing takes an injected `random.Random`. No test hits a GPU or the network — which is why every scenario declares `Layers: unit`
and none declares `e2e`. Diffusion quality and identity fidelity are verified **live on a pod, by eye**,
never mocked and never asserted.

---

## Engineering conventions

The active change's **`design.md`** is authoritative, with this file behind it — read it. It *is* the
decision record: the reasoning that settled a decision, and the measurement behind it, are written there
and nowhere else. In brief, the load-bearing seams are:

- **A parameter is a seam only if something else is actually passed through it.** That is why `client` is a
  parameter of `generate.render` — `FakeComfyClient` is what makes the whole suite offline — and why `rng`
  is one, while the reader and the sorter are seams because each has a real double. A one-entry registry
  is a dispatch mechanism with nothing to dispatch.
- **The flow manifest declares; nothing computes.** `flows/<id>/flow.json` names every node the render
  path edits, by role — `flow.node("sampler")`, `flow.node("photo")` — so no node is ever located by
  class at runtime. That is what lets a broken flow be caught by the suite rather than by a boot, and
  it is not optional: `summon-v1` has two `KSampler` nodes and two `ImageScale` nodes, so a class
  lookup is ambiguous against the graph that actually ships.
- **`isekai/shared/image.py`** — what an image *is*: the JPEG/PNG header walk, the EXIF transpose the
  loader will apply, and `working_resolution`, the render target the image's own dimensions imply. It
  touches no ComfyUI graph; the caller writes the target into the node the manifest names. It is
  `image` rather than `photo` because half its callers hand it a render.
- **`isekai/pipeline/generate.py`** — assembly, seed drawing and the render. Assembly happens before
  any endpoint is acquired, for the whole batch, so a malformed sheet costs nothing rather than a boot.
- **`ComfyTransport`** (`isekai/boundary/comfy_types.py`, implemented in `comfy_client.py`) — the
  network boundary, and the only one.
- **The run owns the layout, not the stages.** The stage directory names live in
  `isekai/foundation/run.py` and the `Schema` type in `isekai/foundation/flow.py`, and **no stage
  imports another** — the last such edge closed when `validate` moved to `isekai/shared/fields.py`,
  which is behaviour rather than layout. The layout itself is **input above, flow below**:
  `runs/<input-id>/<flow-id>/{captions,sheets,review,prompts,outputs}/`, so adding a flow adds one
  subtree and no flow can read another's artifacts.

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

**The living spec** is `openspec/specs/<capability>/spec.md` — nine capabilities, each a contract
with one owner: `cli`, `run-directory`, `caption`, `sheet`, `review`, `image-generation`,
`comfy-transport`, `evaluation`, `model-provisioning`. (`workflow-injection` and `workflow-mutation`
were the old path's, and v0.14 removes them; they leave the living spec when that change is
archived, which is `mf-release`'s act.) Every `#### Scenario:` carries a
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

- **`isekai/__main__.py`** — the path `runpy` resolves for `python -m isekai <verb>`, and a shim
  over `interface/cli.py`. It is the only entry point.
  **`isekai/`** — the package, filed into **six group directories**, each with its own `README.md`
  naming its files and who imports them (and `isekai/README.md` over the six). Every `__init__.py`
  holds a docstring and **no code**: a group never becomes a place two modules reach each other
  through.
  **`foundation/`** — `run.py`'s run directory and the layout names, `flow.py`'s manifest loader and
  the `Schema` type, `refusal.py`. **`pipeline/`** — the four staged verbs, `caption` · `sheet` ·
  `review` · `generate`. **`shared/`** — `image.py`'s header reader, `vocabulary.py`,
  `fields.py`'s sheet validation, `atomic_write.py`. **`boundary/`** — the ComfyUI transport (`comfy_types.py`, `comfy_client.py`,
  `multipart.py`), `claude_cli.py`, and `provision.py`: the manifest's reader, the byte verification,
  the skip/abort/fetch policy and the graph↔manifest binding. `provision.py` is **not** in the entry
  point's import graph, so the stdlib-only runtime rule is untouched either way.
  **`evaluation/`** — the scorer and the only importer of the `[eval]` extra. **`interface/`** —
  `cli.py`'s parser and dispatch, `wiring.py`'s composition, `run_view.py` behind the `show` verb.
  **`tests/`** — the suite and its fakes.
  **`flows/<id>/`** — one flow, and **five flat files**: `flow.json`, the manifest that declares its
  inputs, vocabulary, models, dials, prompt fragments and the graph id of every node the render path
  edits; `graph.json`, the API graph; `schema.json`, the sheet's field list; and the two briefings,
  `caption.briefing.md` and `sheet.briefing.md`. The manifest names none of its siblings — a key that
  can only ever hold one value is not a declaration — and they sit *directly* in the directory,
  because the digest that freezes a flow covers regular files only, so a nested layout would leave
  three of the five outside the freeze with the gate green. A flow is immutable — editing any of the
  five is not a variant of a flow, it is an untested flow — it shares nothing with another flow, and
  `flows/summon-v1/` is the only one. **`infra/`** — `up.sh` / `down.sh`,
  the pod lifecycle. **`scripts/`** — `models.json`, the pinned and checksummed manifest of every
  model artifact the graph needs and the source of truth for what the stack *is*;
  `download_models.sh`, the thin driver that provisions it, run *on the pod*; and
  `derive_manifest.py`, which re-derives every revision and digest — the manifest is its output, so
  a re-run must leave the file byte-identical. Beside them and never merged into them:
  `eval_models.json`, the same thing for the artifacts the **evaluator** loads locally, derived the
  same way by `derive_eval_manifest.py` and under the same byte-identical rule; and
  `eval_licences.md`, where each of those artifacts' licences is recorded with the URL and the date
  it was read. Three destinations appear in **both** manifests, byte for byte — `glintr100` and the
  two DWPose artifacts — and a test fails if the two files ever disagree about them.
  **`Dockerfile`** — the image that *is* the pod.
- **`openspec/`** — the living specs and the changes. Authoritative for what is being built and how far
  along it is.
- **`.minions/`** — run artefacts, **gitignored**; `minions.toml`, the gate command list, is the one
  tracked file in it. `git check-ignore` reports the *directory* as not ignored precisely because of that
  one file — always check a file path.
- **`.data/`** — **everything a run produces or consumes**, and **gitignored**: the staged pipeline's
  runs under `.data/runs/<input-id>/<flow-id>/` (or wherever `--runs` points), beside its inputs and
  outputs.
  The reason is not tidiness. A run directory holds a *copy of the photograph* — that is what makes a
  run reconstructable from disk — so `runs/` contains personal photographs **by construction**. Under
  a top-level `runs/` the standing rule that no personal photograph is committed would depend on one
  `.gitignore` line staying correct forever; under one ignored root it is structurally true instead,
  because there is nothing generated outside it to get wrong.
- **`models/` deliberately stays outside `.data/`**, and the boundary is named so the rule does not
  drift into meaning "everything untracked". The two fail differently: `.data/` is captured or
  generated and its loss is the loss of work, while `models/` is fetched from a pinned manifest and
  verified, so its loss costs a re-download that is byte-identical by construction.
- **Everything a run reads or writes is inside the repository.** No path outside the repo is resolved by
  anything tracked here. Research notes and the running log live in the operator's own notebook; nothing
  in this repo reaches into it, and its location is not recorded here.

## The path

One flow, `summon-v1`, on a **WAI-illustrious-SDXL v17.0** (Illustrious/SDXL anime) base, driven in
four staged verbs — `caption` → `sheet` → `review`/`approve` → `generate`. **Every one of them takes
`--flow`, required and repeatable**, because the flow is what supplies the briefing the stage reads,
the schema it fills against and the directory it writes into. The stages before the last are free and
local; only `generate` needs an endpoint, and assembly happens for the whole batch before one is
acquired, so a malformed sheet costs nothing rather than a boot.

Identity is carried by mechanisms rather than by a sentence someone types:

- **Face** — InstantID + InsightFace: face embedding and keypoints. `ip_weight` 0.9 and
  `identity_cn_strength` 0.8 are its dials.
- **Composition** — **from noise**: `EmptyLatentImage` at `denoise` 1.0. Taking the photograph out of
  the latent is what removed the blur (F24), and img2img is a closed avenue here.
- **Pose** — one ControlNet, OpenPose off `DWPreprocessor`, at `openpose_strength` 0.6.
- **Detail** — a hires pass: `RealESRGAN_x4plus_anime_6B` upscale, then a second sampler at
  `hires_scale` 1.5 and `hires_denoise` 0.35.
- **Register** — the prompts are **assembled per run** from an approved sheet, not committed to the
  graph: the flow's manifest carries a prefix, a trailer and the negative, and the subject's own
  canonical tags come from the sheet a human corrected. The correction is the single largest measured
  gain in this pipeline, which is why **only an approved artifact is ever rendered**.

Before any node reads the photo, an `ImageScale` node puts it on one working resolution, computed by
`isekai/shared/image.py` from the photo's own JPEG or PNG header: aspect preserved, short side at 1024, both
dimensions a multiple of 64, in both directions, and refused past 4:1 rather than clamped. No node
available here can derive that, and a header it cannot read refuses that photograph rather than
defaulting or ending the batch. `clip_skip` is -2, declared in the flow's manifest rather than
committed to the graph file, because every published WAI v17 sample generates at clip skip 2 and none
of its prose says so.

**Nothing locates a node by class.** The manifest names every node the render path edits, by role, and
`summon-v1` has two `KSampler` nodes and two `ImageScale` nodes — so a class lookup is ambiguous
against the graph that actually ships.

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
- **Some phases spend real money**, and the active change's `tasks.md` marks them (⚠️ GPU). The protocol
  names four things, because a rule that leaves any of them implicit is not a rule:
  1. **Who creates the pod** — `infra/up.sh`, and nothing else. Announce before you run it.
  2. **Who tears it down** — `infra/down.sh`. **Teardown is the act**: it is the call that stops the
     billing, and it belongs to the same session that created the pod.
  3. **Who confirms** — the RunPod MCP, by checking the pod is gone. **Confirmation is not the act.** A
     rule that only names the check has not said what stops the billing, and an unconfirmed teardown is
     not one you may report as done. Record what the MCP returned.
  4. **What happens when the MCP is unreachable** — it must be authorized from an *interactive* session,
     so it can be disconnected exactly when this rule is read. Then the **explicit human "go" is back,
     unchanged**, and holds for the whole session: announce, wait for the "go", spend, tear down, report.

  **The ceiling is 45 minutes and ~$0.30 for a single pod session** — numbers, not "promptly", so a human
  can hold you to it. Exceeding it is a halt, not a judgement call. And whichever route applies, the
  authority to spend comes from the **phase**, never from the agent: **a pod goes up only for a phase
  `tasks.md` marks metered.**
- **GPU renders live on the pod's ephemeral disk**; only the models volume persists. Download before
  teardown or the output is gone.
- **The Blackwell (sm_120) pod needs cu128 PyTorch** — cu124 gives "no kernel image". It is pinned in the
  image; keep it.
