# Photo to Anime — Repository Guide

This is a **learning + portfolio** project. The human is doing this to *learn how to run
and set up open models*, not to ship fast. Optimize for understanding.

## How we work here (read every session)
- **The human writes every line of code.** Do NOT write code into files. Instead:
  suggest the next step, show small illustrative snippets in chat to explain, then let
  the human type it. Review what they wrote.
- **Test-first (TDD) for any deterministic logic.** From v0.2 on, for logic we control
  (model dispatch, per-model workflow injection, multipart build, polling, CLI parsing) we
  **write the failing test first, then implement to green.** Suggest the test before the
  implementation; let the human type both. The suite doubles as executable documentation —
  name tests as behavioural sentences (`test_dispatch_selects_animagine_workflow`).
- **Test the seam, not the GPU.** The HTTP transport to ComfyUI is an injectable dependency:
  tests pass a `FakeComfyClient`, production passes the real `urllib` client — no network, no
  GPU in tests. Actual diffusion / image quality / identity fidelity is verified **live on a
  pod**, judged by eye — never mocked or asserted.
- **Golden fixtures.** Capture the real workflow JSON and a real `/history` response once,
  freeze under `tests/fixtures/`, and mock against those ("discover the real shape once →
  freeze → test against it"). `pytest` is a **dev-only** dependency; the runtime stays
  zero-dep (stdlib only). CI runs `pytest` on every push (fast, free, no GPU).
- Work the plan phase by phase; after each step, say what comes next.
- When the human asks a question, TEACH — explain the *why*, not just the *how*.
- When we learn something transferable, write a vault note (see below) and explain it back.

## Where the plan and notes live
The human keeps an Obsidian vault where the implementation plan lives and where transferable
knowledge is filed. The machine-specific paths are in a gitignored `.env` (copy `.env.example`
and fill in). Read `.env` to resolve them:
- `VAULT_PLAN` — the implementation plan (source of truth for the phases; read it first)
- `VAULT_SCHEMA` — the vault's own CLAUDE.md (the note-writing schema to follow)
- `VAULT_LAB_DIR` — this Lab project (operational log / tasks / overview)
- `VAULT_LEARNING_DIR` — where Learning notes (transferable knowledge) go

When writing a note: follow `VAULT_SCHEMA`, create/update the Learning page under
`VAULT_LEARNING_DIR`, back-link it from the Lab project's `overview.md` (Related knowledge),
and append a `graduate` entry to the Lab `log.md`.

If `.env` is absent, ask the human for the vault paths (or proceed code-only without notes).

## What this project is
Reproducible, provider-agnostic, on-demand GPU pipeline: photo of a person → anime image,
using open models in ComfyUI, deployed on a rented RunPod GPU (per-second billing; the Docker
image runs directly as the pod). The hard constraint is **identity preservation** — the result
must stay recognizably the same person.

Three model paths, selectable at the CLI (`convert.py --model {qwen,animagine,animagine-i2i}`),
each owning its own workflow JSON + injection adapter (strategy pattern):
- **qwen** (v0.1, ✅ done) — **Qwen-Image-Edit** instruction-edit model; identity preserved "for
  free" via denoise-1 image-conditioning.
- **animagine** (v0.2, ✅ done) — **Animagine XL 4.0** (SDXL anime) **+ InstantID + InsightFace**;
  identity is an *injected* signal (face embedding + keypoints) on top of from-noise SDXL.
- **animagine-i2i** (v0.3, 🔨 active) — same Animagine base + InstantID, but **img2img** (latent
  init from the photo via `VAEEncode`, `denoise < 1`) so the photo's composition survives — pose,
  hair, eyes, clothes, **tattoo**. `denoise` is the identity↔style dial. Reuses the `animagine`
  injection adapter (the node-trace is unchanged). The ControlNet stack (OpenPose/Lineart/Depth/
  tile) is an additive tuning layer, deferred.

Each version extends the previous — nothing is removed, all models stay available. Built
**test-first (TDD)** with the ComfyUI client fully mocked (see "How we work here"). `VAULT_PLAN`
(the v0.3 plan) is the source of truth for the phases — read it first each session.
