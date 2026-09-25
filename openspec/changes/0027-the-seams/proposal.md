---
version: v0.22.5
---

# 0027 — the seams

The code is brought in line with its layers and held there by a test. Every import points down, the ComfyUI
transport becomes one package with a front door, and the gate and the encoder window are declared once.
Structural: no behaviour changes.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | every choice that settles how, and the facts at `9b3fca2` it rests on |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | a requirement body that names a module this change removes, corrected |

## Why

**The layers are a rule nothing holds.** `docs/principles.md` says imports point only down, and these point
up or into `evaluation`: `foundation/flow.py` into `boundary`, `foundation/run.py` into
`shared`, `shared/vocabulary.py` into `boundary` and `evaluation`, `boundary/wd14.py` into `evaluation`.
No test would notice another.

**The front ends own rules about the work.** The CLI decides which transport failures are transient, and
the review UI decides what state a sheet is in. `docs/principles.md` records both as known breaks of
*composing is all a front end does*.

**Facts are written twice.** The gate's commands are listed in `.minions/minions.toml`, `Makefile`,
`CLAUDE.md` and `README.md`, with no test holding them equal. The encoder window is `77` in
`pipeline/review.py` and again in `ui/src/types.ts`.

**Some checks are silent.** The vocabulary-dependent tests skip wherever the vocabulary is missing, the
operator's machine included, so the committed field map can drift unnoticed. Nothing checks that the tests
a principle names still exist.

## What Changes

- **The gate lives in `Makefile` alone.** `.minions/minions.toml` is deleted and `.minions/` is ignored whole.
  `CLAUDE.md`, `README.md`, CI and `scripts/typecheck_ui.sh` point at `make gate` and list no command
  ([D1](design.md#d1)).
- **The encoder window is declared once**, in `pipeline/review.py`. The review UI reads it from the token
  budget the server sends ([D2](design.md#d2)).
- **The checks.** `tests/test_layers.py` holds the layers; `tests/test_principles.py` holds the principles'
  *held by* names; the vocabulary-dependent tests fail when the vocabulary is missing, except where CI
  declares it absent ([D3](design.md#d3), [D4](design.md#d4), [D5](design.md#d5)).
- **The upward imports move.** `atomic_write` and the graph type go to `foundation`
  ([D6](design.md#d6)). Pin verification leaves `evaluation` for `boundary/provision.py`, and the front end
  verifies the vocabulary before `shared` reads it ([D7](design.md#d7), [D8](design.md#d8)).
- **The ComfyUI transport becomes `boundary/comfy/`**, a package with a front door, and the failure
  classification moves out of `interface/cli.py` into the client, word for word ([D9](design.md#d9)).
- **The approval state moves into `pipeline/review.py`**, unchanged; `review.is_complete`, which nothing in
  production calls, is deleted ([D11](design.md#d11)).
- **The docs follow the code** — `docs/modules.md`, `docs/principles.md`, `CLAUDE.md`, `README.md`, the group
  READMEs and the `comfy-transport` and `run-directory` spec preambles ([D12](design.md#d12)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

Prose inside a requirement body. No SHALL changes, and no scenario is added or removed
([D10](design.md#d10)).

- `comfy-transport` · *Hand-built multipart encoding* — the note under its scenarios names
  `comfy_client.history()`, a module this change removes; it becomes `ComfyClient.history()`.

## Impact

- **Files:** `isekai/` (the moves), `ui/src/` (the window), `tests/` (new checks, rebound imports),
  `Makefile`, `.gitignore`, `.github/workflows/ci.yml`, `scripts/typecheck_ui.sh`,
  `scripts/derive_field_map.py`, `probe/loader_probe.py`, `docs/`, `CLAUDE.md`, `README.md`, the group
  READMEs, and the preambles of `comfy-transport` and `run-directory`.
- **Behaviour:** none for the pipeline — every refusal text, failure kind and artifact byte stays. The
  token-budget payload gains a `window` field. Moving the code also moves these: the review UI's token bar
  shows `—` for the window while the budget is still loading, and `probe/loader_probe.py` now receives
  `Unreachable` rather than a raw `URLError` ([D2](design.md#d2), [D9](design.md#d9)).
- **Patch conditions:** met ([D14](design.md#d14)).
- **Dependencies:** none.

## Not in this change

- **The run files' shapes.** Declaring every file's shape once, with a typed reader and writer per kind, is
  its own patch, the next one.
- **Reconciling the definitions of *draft*.** `state()` moves unchanged; the approval defects
  (`STATE-1` to `-3`) belong to the defects patch.
- **The transport's own defects.** Every HTTP error status recorded as transient, tracebacks from a
  malformed response, no timeout, a poll with no deadline, a failed upload that records nothing, and
  `entry_for` naming `eval_models.json` for every manifest — each moves as it is and waits for the defects
  patch.
- **The multipart hardening** — a random boundary, a collision scan, escaped filenames. Moving the file does
  not fire it; it changes the bytes on the wire, which no requirement asks for. Trigger: the next change to
  the encoder's content.
- **The layout of `scripts/`**, and a `make derive` target — the tree reorganisation's.
- **Privacy** — its principle and its decisions are out of scope until after the evaluation minor.
- **Splitting `generate`'s free and metered halves**, and teaching `generate` or `show` the re-opened state.
