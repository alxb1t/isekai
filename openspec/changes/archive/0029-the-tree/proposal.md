---
version: v0.22.7
---

# 0029 — the tree

`scripts/` is retired into `config/` and `tools/`, the evaluation sub-system leaves the package for a
top-level `evaluation/`, `probe/` and the licence record are deleted, and `make derive` re-runs the derivers.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the layout, the commands, and every choice that settles how |
| [tasks](tasks.md) | the phases, in build order |
| [specs/](specs/model-provisioning/spec.md) | the licence requirement, removed |

## Why

**`scripts/` mixes kinds of thing.** It holds the files the pipeline reads (`models.json`,
`vocabulary.json`, `field_map.json`, `joycaption.Modelfile`), the tools an operator or the gate runs (the
derivers, `download_models.sh`, `typecheck_ui.sh`), and the evaluator's own manifest.

**The evaluator is a sub-system, and it lives inside the package it measures.** `docs/principles.md` says it
sits beside the code it measures; it sits in `isekai/evaluation/`, with its CLI at the root as `evaluate.py`
and its calibration in `baseline/`.

**Some things are left over.** `probe/` is v0.11's loader probe: no live code uses it, and its measurement is
recorded in the archived change that made it. The licence record is out of scope for now.

## What Changes

```
config/      models.json · vocabulary.json · field_map.json · joycaption.Modelfile
tools/       derive_manifest.py · derive_vocabulary.py · derive_field_map.py · derive_eval_manifest.py
             · manifest.py · download_models.sh · typecheck_ui.sh
evaluation/  __main__.py (was evaluate.py) · evaluate.py · eval_backends.py · ciede2000.py
             · eval_models.py · labels.py · eval_models.json · baseline/
deleted      scripts/ · probe/ · scripts/eval_licences.md
```

- **Tools and the evaluator run as modules from the repository root** — `uv run python -m
  tools.derive_manifest`, `uv run --extra eval python -m evaluation` — with absolute imports
  ([D1](design.md#d1), [D2](design.md#d2)).
- **The printed commands follow**: the refusals name `config/` and `tools/` ([D3](design.md#d3)).
- **`field_map.json` records its new path**, so new sheets record a new name and digest for the same fields
  ([D4](design.md#d4)).
- **The image mirrors the repository's layout**, and tests hold the image to it ([D5](design.md#d5)).
- **`make derive`** re-runs the derivers in dependency order ([D6](design.md#d6)).
- **The evaluator's label ordering follows a moved file** (`--follow`), so moving the labels keeps their
  evidence ([D7](design.md#d7)).
- **The tests that assume the old tree are rewritten**, and a scope list naming a missing path fails
  ([D8](design.md#d8)).
- **`probe/` and the licence record are deleted** ([D9](design.md#d9), [D10](design.md#d10)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `model-provisioning` · *Every provisioned artifact's licence is recorded before it is relied on* —
  **removed**, with its scenario `model-provisioning:licences:vocabulary-terms-are-recorded`
  ([D10](design.md#d10)).

## Impact

- **Files:** `scripts/` (gone), `config/` and `tools/` (new), `isekai/evaluation/` and `baseline/` into
  `evaluation/`, the root `evaluate.py`, `probe/` (gone), `isekai/` (anchors, printed commands),
  `Dockerfile`, `start.sh`, `Makefile`, `pyproject.toml`, `.github/workflows/ci.yml`, `tests/`, `docs/`,
  `CLAUDE.md`, `README.md`, the group READMEs and the spec preambles.
- **Behaviour:** the paths and command shapes the refusals print; `field_map.json`'s recorded name and
  digest; the evaluator's `GitOrdering` follows a renamed file. Nothing else a run does changes.
- **The image:** its layout moves with the repository; the merge rebuilds `:latest`, and the first boot on
  it is its first live run ([D5](design.md#d5)).
- **Patch conditions:** met ([D14](design.md#d14)).
- **Dependencies:** none.

## Not in this change

- **Any other evaluator behaviour.** The evaluation minor rebuilds the evaluator; `evaluate` still cannot
  read a current run.
- **The AGPL guards** on the scorer's dependencies stay; a later version revisits licences and their tests.
- **The hardening `0009 S3` asks of the manifest.** Moving `models.json` changes no line of it.
- **A metered boot.** `0011:S4` still blocks every boot; the first one after this change is the image's live
  proof.
- **Another tool or directory out of the root**: `infra/`, `flows/`, `ui/` stay where they are.
