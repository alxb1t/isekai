---
version: v0.18
---

## Why

**Stage ③ is where the measured value of this pipeline sits, and it has no surface.** The unreviewed
route carries 0.568 of a sheet's attributes into the render and the reviewed one carries 0.917 — the
whole of that gap is a person correcting tags. Today the only way to correct them is `$EDITOR` on a
JSON file, which cannot tell the operator that a tag exists, how it is canonically spelled, or how many
posts stand behind it. **Editing a sheet in a text editor is not review, it is spellchecking.**

**The three facts a correction needs are already in the repository and none of them reaches a human.**
`vocabulary.search()` ranks 8,106 tags by post count in 254 µs and has one caller, a test.
`assemble()` builds the exact string the text encoder reads and nothing counts it before a render.
`Vocabulary.counts` holds the number that predicts how strongly a tag lands. A surface that shows all
three is the smallest thing that turns ③ from transcription into judgement.

**Now, because the version after this one measures review and cannot measure what nobody does.** v0.19
scores the corrected sheet against the photograph; the correction has to be cheap enough to do on every
input first. And the one forced pipeline-side change here — extracting the argv-free half of `wiring()`
so a server cannot skip the run-root containment guard — opens the exact function whose guard is
bypassable by case on darwin. Extracting a guard to make it unskippable while leaving it broken ships a
hardening that does not hold.

## What Changes

- **`isekai ui <ids…> --flow F`** — a new verb that resolves a batch, refuses everything it can refuse,
  prints a URL and blocks. One FastAPI process on localhost serving a built Vue bundle and six
  endpoints. **Scope is ③ alone**: no upload, no captioning, no generate button, **so nothing in the
  browser spends money.**
- **The UI is a sibling of the CLI, not a client of it.** Both front ends call `wiring` and the stage
  functions directly, as the suite already does across 169 call lines. **No subprocesses**, which
  overturns the mechanism the architecture record settled on 2026-09-16.
- **`review.save_draft()`** — the one owner of an in-place draft update, refusing a payload whose field
  set differs from the draft it replaces.
- **`review.token_budget()`** returning `TokenBudget(total, per_field, overhead)` — the count taken over
  the assembled positive prompt, so prefix, trailer and separators fall out of one rule. The existing
  `estimate_tokens` and `approve()`'s warning are untouched.
- **`wiring_from(*, runs, server)`** — the argv-free constructor, so a front end that never sees a
  `Namespace` cannot bypass `_check_run_root`. `reader` and `sorter` become optional.
- **BREAKING — none.** Every existing verb, signature and artifact shape is unchanged.
- **The run-root containment check compares by inode identity rather than by path text**, closing
  `security/S1`: `Path.resolve()` does not fold case on darwin, so a lowercased spelling of a path
  inside the working tree evaded the guard entirely.
- **Two refusal strings in `review.py` are repaired** — `:112` names `python -m isekai sheet`, which
  exits 2 because `--flow` is required, and `:224` names the stage-first `review/<flow>/` that v0.16
  deleted.
- **The nine living specs gain `## Purpose`.** All nine currently fail `openspec validate --specs
  --strict` and report `requirements 0`, so the tooling has been blind to 174 scenario keys. Two lines
  per file, no prose written — the paragraph is already there.
- **`ui/dist/` and `ui/node_modules/` join `.data/` and `models/` as ignored roots**, and `CLAUDE.md`'s
  boundary paragraph names how each of the four fails differently.

## Capabilities

### New Capabilities

- `ui`: the browser surface for stage ③ — how the batch is established, what refuses before the URL is
  printed, the six endpoints, and the invariant that the server never constructs an artifact.

### Modified Capabilities

- `review`: gains the draft-update and token-budget behaviours the surface reads and writes.
- `run-directory`: the containment refusal is stated as an identity property rather than a textual one.
- `cli`: the serving verb takes exactly one flow — a third argument shape beside the stage verbs and
  `show`.

## Impact

| | |
|---|---|
| **`isekai/interface/ui/`** | new — four modules: the entry, the batch, the app, the bundle |
| **`ui/`** | new — the Vue 3 source, seven of the design's eleven frames; `dist/` and `node_modules/` ignored |
| **`isekai/pipeline/review.py`** | two public functions added, two refusal strings repaired; `approve()` and `estimate_tokens` **not touched**, so all 26 `approve` call sites stand |
| **`isekai/interface/wiring.py`** | `wiring_from()` extracted, `_check_run_root` reimplemented on `(st_dev, st_ino)`, `reader`/`sorter` optional |
| **`isekai/interface/cli.py`** | one verb, one function-local import — the `-S` guard walks this file's module-level imports |
| **`pyproject.toml`** | `[project.optional-dependencies] ui = ["fastapi", "uvicorn"]`; `dependencies = []` untouched |
| **`openspec/specs/*/spec.md`** | nine files gain `## Purpose`; verified to turn `0 passed, 9 failed` into nine valid specs |
| **node** | a **system** dependency — the repo's second, after the `claude` binary; `require_binary()` is the refusal shape it copies |
| **not touched** | `generate.py`, `shared/fields.py`, stage ②'s artifact, `cli.py`'s `_run_for`/`_flows_for`, the evaluation sub-system, the pod — **verified by `git grep`, not assumed** |
| **money** | **one metered phase, and it halts for the operator first.** Phases 1–12 are free — the walkthrough runs against a copy of the existing v0.17 run data. The acceptance is three of the operator's own photographs through ①②③④: six hosted-model calls and **one pod session, ceiling 45 minutes and ~$0.30**, planned at ~$0.07 |
