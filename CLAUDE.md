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

## The plan lives in a private vault — read it first

The full, canonical implementation plan is **not in this repo** (this repo is public — it must never
contain the vault's absolute path). The plan lives in a private Obsidian vault whose location is stored in
**`.env`** (gitignored) as **`VAULT_PROJECT_DIR`**.

1. Read `.env` and load `VAULT_PROJECT_DIR` — the absolute path to the vault project folder. If it is
   missing, copy `.env.example` → `.env` and ask the human to fill it in. **Never hardcode or print the real
   path in committed files.**
2. Read the **latest implementation plan** in `$VAULT_PROJECT_DIR/implementation_plans/` — the
   `vX.Y_implementation_plan.md` with the **highest version number** (ignore `archive/`). It is the source of
   truth for scope, decisions, architecture, the engineering conventions, the per-phase steps, **and the
   phase workflow contract**. Lower-versioned plans are completed predecessors — historical record only.
3. The plan tracks progress via its **Progress ledger** (bottom of the plan); the project's **`overview.md`**
   carries a machine-readable **`current_phase`** + per-phase flags in its frontmatter, and the newest entries
   sit at the **top** of `$VAULT_PROJECT_DIR/log.md` (this log is **newest-first**) — read these to see where
   the work stands. If the plan references a Phase-0 research file, read that too.

Plans and their research/findings files live in `$VAULT_PROJECT_DIR/implementation_plans/` (version-prefixed,
e.g. `v0.5_implementation_plan.md`, `v0.5_research.md`); the project's `overview.md`, `log.md`, `backlog.md`,
and `release_log.md` sit at `$VAULT_PROJECT_DIR/`. Do not re-derive decisions already settled in the plan. If
something there conflicts with reality, raise it with the human rather than silently diverging. Any vault
writes stay **inside `$VAULT_PROJECT_DIR`** and follow the conventions already visible in that folder (the
`log.md` / `overview.md` / `backlog.md` shapes) — `VAULT_PROJECT_DIR` is the only vault path this repo knows.

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

Each version extends the previous — nothing is removed, all models stay selectable. The active plan's scope
(e.g. new `--model` paths, multi-input plumbing) is authoritative for what's being built now.

---

## The quality gate (a phase is done only when all are green)

- `pytest` — all tests pass. **Test-first (red → green)** for every unit of logic we control (model dispatch,
  per-model workflow injection, multipart build, polling, mutation seam, CLI parsing). The suite doubles as
  executable documentation — name tests as behavioural sentences.
- `ruff check` (+ `ruff format`) — lint/format clean.
- `ty` — type-check clean.
- Image-as-code phases also: `bash -n` on shell scripts + `docker build --check` clean.

The ComfyUI transport is **fully mocked** in tests (`FakeComfyClient` behind a `ComfyTransport` Protocol);
the workflow/API contract is **fixture-locked** (placeholder golden fixtures first, relocked to real node IDs
after the live GPU export). **No test hits a real GPU or the network.** Actual diffusion / image quality /
identity fidelity is verified **live on a pod, judged by eye** — never mocked or asserted. CI (`ci.yml`) runs
ruff + ty + pytest on every push.

---

## Guardrails (invariants — hold for every role)

- **Never commit `.env` or any secret** (RunPod key, volume id, the vault path). `.env` is gitignored; keep
  the vault path and all secrets there only. The committed `CLAUDE.md`/`.env.example` stay path-free.
- Runtime code is **stdlib-only** (the ComfyUI transport uses `urllib`). Face detection runs *in the image*
  (`insightface` + **CPU** `onnxruntime` / antelopev2 — never `onnxruntime-gpu`), not as a runtime Python dep
  of `convert.py`. pytest/ruff/ty stay dev-only. Don't add runtime deps unless the plan sanctions them.
- **Some phases spend real money.** The plan marks metered (⚠️ GPU) phases and defines the
  stop-before-spending protocol (announce, wait for an explicit human "go", `up.sh` → tunnel → `convert.py` →
  `down.sh`, tear down, log cost). Respect it — **never bring up a paid pod on your own initiative.** GPU
  renders live on the pod's ephemeral disk; only the models volume persists — `scp`/download before teardown.
- The **Blackwell (sm_120) pod needs cu128 PyTorch** (cu124 gives "no kernel image"); this is pinned in the
  image — keep it.
- The **vault is the single source of truth** for "where are we." If your role updates it, keep it accurate
  (newest-first `log.md`, `overview.md` `current_phase`/flags, the plan's Progress ledger, `backlog.md`); a
  fresh session relies on it.
