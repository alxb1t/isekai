---
version: v0.22.4
---

# 0026 — the architecture in the repo

The repository's architecture moves into `docs/`, its false self-claims are swept, and `CLAUDE.md` imports
the principles. Prose only: no behaviour changes.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the sweep's sites ([D1](design.md#d1)), and every choice that settles how |
| [tasks](tasks.md) | the phases, in build order |
| [payload/](payload/) | the drafts, word for word, that `docs/` is written from — the review's reference ([D3](design.md#d3)) |
| `specs/` | the living-spec sentences that are false of the code today, corrected |

## Why

**The builders never saw the principles.** They lived outside the repository, so no agent session had them,
and the word *principles* appears nowhere in the tree. A rule outside the builder's context drifted, whatever
it said.

**The repository describes itself wrongly.** The architecture review found false self-claims across code,
tests, `README.md`, `CLAUDE.md`, `docs/arc/` and the living specs. Most are of these kinds: a retired
mechanism still described, an exclusivity claim (*"the only"*), a count.

**Docs go first**, so every later version is built with the principles in context and written under the
rules that stop these claims.

## What Changes

- **The sweep.** Every false self-claim [D1](design.md#d1) lists is corrected where it sits — code comments,
  docstrings, the CLI's help text, tests' docstrings, `pyproject.toml`, READMEs, `CLAUDE.md`, `docs/`, and the
  living specs' preambles.
- **`docs/` is written and flattened.** `docs/principles.md`, `docs/decisions.md` and `docs/README.md` are
  written from [payload/](payload/). `docs/arc/`'s `modules.md` and `data-flow.md` move up into `docs/`, lose
  their false claims, and `docs/modules.md` gains how the components interact.
- **`docs/decisions.md` gains the product scope** the operator's notebook held and the repository did not
  ([D7](design.md#d7)).
- **`CLAUDE.md` imports `docs/principles.md`** and keeps only process: its design rules move out, the
  change-id rule becomes *the next free number*, and it states what a patch may hold ([D8](design.md#d8)).
- **The group READMEs point at `docs/`** instead of *"the design record"* ([D9](design.md#d9)).
- **`README.md` stops restating the architecture.** It keeps what the project is, how to run it, and the
  machine topology, and links to `docs/` ([D10](design.md#d10)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

Prose inside the requirement bodies. No SHALL changes, and no scenario is added or removed
([D2](design.md#d2)).

- `cli` · *The pipeline surface is the only entry point, and its verbs are subcommands* — *"the stdlib-only
  guard"* becomes the entry point's import guard.
- `cli` · *The rendering verb takes many photographs and either a count or explicit seeds* — *"Reading and
  sorting are cheap"* becomes reading and filling a sheet.
- `image-generation` · *A failure is recorded as the kind it was, and one flow's failure is its own* — the
  scenario's clause *"a later invocation of that stage attempts the work"* becomes the refusal the build
  gives, and the rationale says what the kind buys at a budget of one.
- `model-provisioning` · *The manifest declares every artifact the shipped graph requires* — *"while
  `summon-v1` is the only flow"* is deleted.
- `ui` · *A tag artifact that is absent is silent* — *"a flow that declares no hosted model"*, a state the
  loader refuses, leaves the list of legitimate absences.

## Impact

- **Files:** `docs/` (new layout), `CLAUDE.md`, `README.md`, the group READMEs under `isekai/`, docstrings and
  comments in `isekai/`, `scripts/derive_field_map.py`, `tests/` docstrings, `pyproject.toml`, and the
  `## Purpose` preambles of `comfy-transport`, `model-provisioning` and `sheet`.
- **Behaviour:** none. The observable edits are the `caption` and `sheet` verbs' help text, the parser's
  description, and `scripts/derive_field_map.py --help`, which prints its module docstring.
- **Patch conditions:** met — no format version moves, no behaviour is fixed, nothing is deprecated, the
  product is unchanged ([D11](design.md#d11)).
- **Dependencies:** none.

## Not in this change

- **No check is added.** The gate-list check, the field-map check in CI, the principles' *held by* names and
  the layer test belong to the seams patch.
- **No test for the notebook-path rule.** None exists; the rule lands in `CLAUDE.md` held by review
  ([D8](design.md#d8)).
- **Sites a later version rewrites** — the refusal remedies, the approval states, the attempt number, the
  transport's failure classification. Each is left as it is.
- **Evaluation.** `evaluate.py`'s unreadable run (`EPISTEMICS-2`) and every evaluation finding go to the
  evaluation minor.
- **Seen at the cut and not settled into this change:** `cli/spec.md`'s *"reading, sorting, reviewing"* in the
  flow-selection requirement — trigger: the caption/tag split, which adds a stage verb to that list; and
  `ui/spec.md`'s *"look behind the sorter"* — trigger: the full audit of scenarios against the code, which
  follows this sweep.
