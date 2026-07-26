# Photo to Anime — Repository Guide

This is a **learning + portfolio** project. The human is doing this to *learn how to run
and set up open models*, not to ship fast. Optimize for understanding.

## How we work here (read every session)
- **The human writes every line of code.** Do NOT write code into files. Instead:
  suggest the next step, show small illustrative snippets in chat to explain, then let
  the human type it. Review what they wrote.
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
using open models (Qwen-Image-Edit in ComfyUI), deployed on a rented RunPod GPU (per-second
billing; the Docker image runs directly as the pod).
