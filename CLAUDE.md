# isekai — shared context for Claude Code

A self-hosted, headless pipeline: **photo of a person → anime image of that same person** (open models
via ComfyUI on an on-demand RunPod GPU, deployed as our own Docker image). The hard constraint is
**identity preservation** — the result must stay recognizably *the same person*. Everything runs on open
models; the runtime is zero-dependency (stdlib `urllib`) and the ComfyUI transport is an injectable seam.

> **This file is shared, role-independent context — what is *true* about this repo. It is not a script.**
> What you should *do* comes from the **prompt/task you were given** (build a phase, review the branch diff,
> run a security pass, apply fixes). If your prompt conflicts with this file, **the prompt wins.** Read this
> for the facts; follow your prompt for the actions — don't infer a workflow from this file alone.

---

## The contract lives in-tree — read it first

This repo follows the **MinionsFactory SDD standard**. The authority for what is being built, and how far
along it is, is **in this repository** — not in a document you have to be told about.

1. **`openspec/specs/<capability>/spec.md`** — the **living spec**: the behaviour this repo already has,
   stated as keyed scenarios. Five capabilities: `model-registry`, `workflow-injection`,
   `workflow-mutation`, `comfy-transport`, `cli`. Every `#### Scenario:` carries a `- **Key:**` and a
   `- **Layers:**` bullet, and the key is `<capability>:<requirement-slug>:<scenario-slug>` — so a key
   locates its own file.
2. **`openspec/changes/<NNNN-name>/`** — the **active change**, which is the unit of work *and* the unit of
   release. Each carries four artifacts: `proposal.md` (with a `version: vX.Y` frontmatter key),
   `design.md`, `tasks.md`, and a `specs/` delta. **This is the source of truth for current scope.**
   Released changes move to `openspec/changes/archive/` — they are never deleted.
3. **Progress lives in `tasks.md`**, in its `## Progress` checklist. **The current phase is the first
   unchecked box.** That is the only progress marker that counts; a phase checks its own box in its own
   commit.

**Tests are bound to the spec.** Every test carries `@pytest.mark.spec("<key>")` naming the scenario it
proves, or `@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural. Both markers are registered
in `[tool.pytest.ini_options] markers` — registration is load-bearing, because pytest silently ignores an
unregistered marker, and an unregistered one would bind nothing while looking exactly like a binding. When
you add a test, bind it; when you add behaviour, give it a scenario first.

### The vault holds the thinking, not the contract

A private Obsidian vault still carries the research, the findings reports and the running log. Its location
is in **`.env`** (gitignored) as **`VAULT_PROJECT_DIR`** — this repo is public and **must never contain the
vault's absolute path**. If `.env` is missing, copy `.env.example` → `.env` and ask the human to fill it in.

- `$VAULT_PROJECT_DIR/findings/` — role and audit reports, including `teardown.md` (the compliance gap
  report this repo's v0.7 milestone was driven by).
- `$VAULT_PROJECT_DIR/log.md` — the running log, **newest-first**.
- `$VAULT_PROJECT_DIR/backlog.md`, `release_log.md`, `overview.md` — supporting bookkeeping.
- `$VAULT_PROJECT_DIR/implementation_plans/` — **historical**. Versions up to v0.6 were planned this way,
  and those files remain a useful record of *why* things are as they are. They are **not** the source of
  truth for current work; `openspec/changes/` is.

Any vault writes stay **inside `$VAULT_PROJECT_DIR`** and follow the conventions already visible there.
`VAULT_PROJECT_DIR` is the only vault path this repo knows. If something in the vault conflicts with the
repo, the repo wins for *what is true now* — raise the conflict with the human rather than silently
diverging.

---

## What the pipeline is (the facts)

`convert.py` uploads a photo + injects a prompt into a ComfyUI workflow, runs it headless over an SSH tunnel
to the pod, and downloads the result. Models are **selectable at the CLI** (`--model …`), each owning its own
workflow JSON + injection adapter (a plain-function **Strategy**, resolved via a name→`Model` **registry**):

- **qwen** — **Qwen-Image-Edit** instruction-edit model; identity preserved "for free" via denoise-1
  image-conditioning.
- **animagine** — **Animagine XL 4.0** (SDXL anime) **+ InstantID + InsightFace**; identity is an *injected*
  signal (face embedding + keypoints) on top of a from-noise SDXL base.
- **animagine-i2i** — the Animagine base + InstantID, but **img2img** (latent init from the photo via
  `VAEEncode`, `denoise < 1`) so the photo's composition survives (pose, hair, eyes, clothes, tattoo).
  `denoise` is the identity↔style dial. Reuses the `animagine` injection adapter (node-trace unchanged).
- **animagine-i2i-cn** — `animagine-i2i` **+ a ControlNet stack** (tile → OpenPose → Lineart). Structural
  conditioning anchors pose/structure/detail. The CN apply nodes sit *in* the conditioning path, so injection
  uses a **generalized trace** (walk `.positive` to the first `CLIPTextEncode`) that serves all
  InstantID-family injectors.

A cross-cutting **workflow-mutation seam** `mutate(workflow, rng)` — *separate from* `inject_*` (injection
wires image+prompt; mutation varies dials) — takes an **injected `random.Random`** so it's deterministically
testable. `--seed` / `--variations` on the CLI; the seed used is printed (reproducibility contract).
`apply_overrides` sets the user's **base** dial values (`--denoise` / `--cfg` / `--ip-weight`) and `mutate`
jitters **around that base** — the order is load → override → mutate.

Each version extends the previous — nothing is removed, all models stay selectable. **The active change under
`openspec/changes/` is authoritative for what's being built now.**

---

## The quality gate (a phase is done only when it is green)

The gate is declared **once**, as the `gate` array in **`.minions/minions.toml`** — the path the orchestrator
reads, and no other. The root **`Makefile` `gate` target mirrors it**, same commands in the same order, so
the gate a human types and the gate the loop runs cannot drift apart. **Change one and you change both, in
the same commit.**

```bash
make gate
```

runs exactly these five, in this order:

1. `uv sync --locked`
2. `uv run ruff format --check .`
3. `uv run ruff check .`
4. `uv run ty check`
5. `uv run pytest`

That is the whole gate — all five green, or the phase is not done. Notes on the axes:

- **`pytest`** — **test-first (red → green)** for every unit of logic we control (model dispatch, per-model
  workflow injection, multipart build, polling, mutation seam, overrides, CLI parsing). The suite doubles as
  executable documentation — name tests as behavioural sentences, and bind each to its scenario key.
- **`ruff`** — `format --check` and `check` are **separate axes** and both must pass. The lint selection is
  explicit in `pyproject.toml`: `[tool.ruff.lint] select = ["E", "F", "I"]`. Note this is broader than ruff's
  default (`E4`/`E7`/`E9`/`F`) — in particular `E501` line-length is enforced, and the formatter does **not**
  wrap comments or docstrings, so those you wrap by hand.
- **`ty`** — type-check clean.
- **`uv sync --locked`** — the lockfile is authoritative and is **tracked**; the run fails rather than
  silently re-resolving.

Beyond the gate array, **image-as-code work also runs `bash -n` on shell scripts and `docker build --check`**.
These are a convention for those phases, not entries in the gate array — don't add them to the array without
adding them to the `Makefile` in the same commit.

The ComfyUI transport is **fully mocked** in tests (`FakeComfyClient` behind a `ComfyTransport` Protocol);
the workflow/API contract is **fixture-locked** (placeholder golden fixtures first, relocked to real node IDs
after the live GPU export). **No test hits a real GPU or the network** — which is why every scenario declares
`Layers: unit` and none declares `e2e`. Actual diffusion / image quality / identity fidelity is verified
**live on a pod, judged by eye** — never mocked or asserted. CI (`ci.yml`) runs ruff + ty + pytest on every
push.

---

## Guardrails (invariants — hold for every role)

- **Never commit `.env` or any secret** (RunPod key, volume id, the vault path). `.env` is gitignored; keep
  the vault path and all secrets there only. The committed `CLAUDE.md`/`.env.example` stay path-free.
- Runtime code is **stdlib-only** (the ComfyUI transport uses `urllib`). Face detection runs *in the image*
  (`insightface` + **CPU** `onnxruntime` / antelopev2 — never `onnxruntime-gpu`), not as a runtime Python dep
  of `convert.py`. pytest/ruff/ty stay dev-only. Don't add runtime deps unless the active change sanctions
  them.
- **Some phases spend real money.** The active change's `tasks.md` marks metered (⚠️ GPU) phases, and the
  stop-before-spending protocol holds: announce, wait for an explicit human "go", `up.sh` → tunnel →
  `convert.py` → `down.sh`, tear down, log cost. Respect it — **never bring up a paid pod on your own
  initiative.** GPU renders live on the pod's ephemeral disk; only the models volume persists —
  `scp`/download before teardown.
- The **Blackwell (sm_120) pod needs cu128 PyTorch** (cu124 gives "no kernel image"); this is pinned in the
  image — keep it.
- **`openspec/` is the single source of truth for "where are we."** The `## Progress` checklist in the active
  change's `tasks.md` is the progress marker, and the first unchecked box is the current phase. Keep it
  accurate in the phase's own commit — a fresh session relies on it. The vault's `log.md` and `backlog.md`
  stay useful as narrative and as a parking lot, but they do not define the state.
