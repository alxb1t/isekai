---
version: v0.7
---

# Proposal — 0001-mf-standard

**Change:** 0001-mf-standard · **Version:** v0.7 · **Source:** `<vault>/findings/teardown.md` (round 1, HEAD `434dfe6`)

> This change did not come through the planning line (`mf-order` → `mf-gauge` → `mf-blueprint` → `mf-forge`), so
> it has no PRD. Its requirements are the **gap list of the compliance rubric**, measured by `mf-teardown`; that
> report is the authority a PRD would otherwise be, and the re-run of that same report is the acceptance test.

## Why

`isekai` cannot be run by the MinionsFactory orchestrator today. The round-1 teardown measured **9 open gaps —
4 blocking, 5 required** — and withheld 4 further criteria it could not even assess. Two independent defects sit
underneath most of that:

1. **The gate is invisible to the loop.** The gate array itself is good — five axes, correctly ordered, no
   waivers anywhere in the repo — but it lives at `minions.toml` in the repo root, and the orchestrator reads
   `.minions/minions.toml` and no other path. Everything the loop wants to know about how this repo verifies
   itself is therefore unreadable to it, which is also why 4 criteria came back *not measured* rather than
   passing or failing.
2. **There is no in-tree contract.** The repo has no `openspec/` tree at all. Progress lives in a private vault
   (`overview.md` `current_phase`, a plan's Progress ledger, `log.md`) under a phase model the standard has
   retired. The loop converges against an in-tree `openspec/changes/<id>/` contract; with none present there is
   nothing for it to converge on, and 86 passing tests are bound to no stated behaviour.

Neither is a defect in the *code*. The Python toolchain is sound, the runtime is genuinely stdlib-only, the vault
wiring and `.env.example` hygiene are already correct, and `gate:no-gaming` passes with zero waivers of any kind.
This is a **wiring and contract** milestone, not a rewrite.

## What (scope)

1. **Relocate the gate config** to `.minions/minions.toml`, tracked, array unchanged — and ignore run artifacts
   under `.minions/` while keeping the config itself tracked. *(`wiring:gate-config`, `wiring:gitignore`)*
2. **Pin the toolchain**: a concrete `.python-version` consistent with `requires-python`, and an explicit ruff
   lint `select` covering at least `E`, `F`, `I`. *(`py:pinned-runtime`, `py:lint-select`)*
3. **Mirror the gate in a `Makefile`** `gate` target running the same commands in the same order, so the gate a
   human types and the gate the orchestrator runs cannot drift. *(`gate:make-mirrors`)*
4. **Stand up the SDD tree**: `openspec/changes/` with `archive/`, and this change carrying all four artifacts.
   *(`sdd:changes-tree`, `sdd:active-change-contract`)*
5. **Backfill `openspec/specs/`** with the behaviour the repo **already has**, across five capabilities —
   `model-registry`, `workflow-injection`, `workflow-mutation`, `comfy-transport`, `cli` — every scenario keyed
   and layered. *(`sdd:specs-tree`, `sdd:scenario-shape`)*
6. **Bind the tests to the specs**: register `spec` and `spec_exempt` markers in the pytest manifest and mark all
   86 existing tests with one of them. *(`sdd:test-binding`)*
7. **Rewrite `CLAUDE.md`** onto the in-tree contract: drop the retired `implementation_plans/vX.Y_…` model as the
   source of truth, describe progress where it will actually live, and make its gate account match the array
   command for command. *(`wiring:claude-md`)*

## Approach

Ordered cheapest-first, and **each phase leaves the gate green and gets its own commit**. The relocation (1)
comes early because it converts 4 not-measured criteria into measurable ones — nothing downstream can be
confirmed until the orchestrator can read the array. `CLAUDE.md` (7) comes **last**, because its (J) clauses
assert what the repo's contract and gate *actually are*, and both are still moving until every phase before it
has landed.

The spec backfill is **descriptive, not prescriptive**: it states behaviour that already ships and already has
tests. No scenario in it may describe behaviour the code does not have — if writing a scenario reveals a real
bug, that is a finding for the backlog, not a silent edit to make the spec true.

## Out of scope

- **Any change to pipeline behaviour.** No new `--model`, no dial changes, no workflow JSON edits. If the gate
  goes red, the fix is the wiring, never the code under test.

  **One approved exception, recorded rather than smuggled.** Writing the `model-registry` spec surfaced a stray
  `$` in the unknown-model exit message (`isekai/models.py:30`, rendering `unknown model $'midjourney'`) — a
  shell-style `${…}` leaking into an f-string. It shipped because the existing test asserted only that the
  process exits, never what it said. The human elected to **fix it before the backfill**, in its own commit,
  test-first, so the scenario could state the behaviour plainly with no defect note attached. That is the whole
  exception: a one-character correction plus the regression test that now pins the message. It does not license
  further source edits in later phases — the backfill stays descriptive, and any further mismatch it turns up is
  raised for the same explicit call rather than fixed in passing.
- **`sdd:checker-in-gate`.** It is `advisory` precisely because it is unsatisfiable by any target repo today —
  MinionsFactory ships no packaging metadata, so the checker cannot be installed here. It stays open and does
  not withhold `compliant`.
- **Retiring the vault.** `VAULT_PROJECT_DIR`, the research files and `log.md` keep working. What changes is
  which of them is the **source of truth for progress** — that moves in-tree.
- **v0.7 `mf-retrofit`.** This milestone is done by hand, deliberately, so the standard is understood before it
  is automated.

## Success criteria

A fresh `mf-teardown` run against this branch reports:

- `verdict: compliant` — which by the rubric's rule means **`open_blocking: 0` and `open_required: 0`**;
- the 4 previously-withheld criteria (`gate:covers-axes`, `gate:contract-agrees`, `py:gate-commands`,
  `sdd:checker-in-gate`) **measured** rather than withheld, because the array is readable at the path the
  orchestrator uses;
- at most one open gap, `sdd:checker-in-gate` at `advisory`, for the stated reason above;
- and the full gate — `uv sync --locked`, `ruff format --check`, `ruff check`, `ty check`, `pytest` — green at
  each phase commit, with all 86 tests still passing and bound.
