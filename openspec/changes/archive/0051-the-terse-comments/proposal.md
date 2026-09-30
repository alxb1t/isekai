---
version: v0.31.3
backlog: [0049·R7]
---

# 0051 — the terse comments

No comment or docstring carries history. Change ids, design citations, isekai versions and history narratives leave
every comment and docstring outside `ui/` and `evaluation/`; a plain `D27` goes in where `docs/decisions.md` holds
the reason. `CLAUDE.md` gains the rule, and a guard keeps it.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the rule, the rewrite, the guard, the meaning check |
| [tasks](tasks.md) | the phases, one tree each |

## Why

**Comments cite what a reader cannot follow.** "0040 design D2" points into an archived change, and "since v0.16"
narrates what `git log` already holds. The reason in force lives in `docs/decisions.md`, and nothing links a comment
to it.

**Nothing keeps it so.** The specs have a history guard; the code has none.

## What Changes

- **Every comment and docstring in `isekai/`, `tools/`, `infra/`, `tests/`, `start.sh` and the `Dockerfile` loses its
  history**, naming a decision in force as a plain D-id; so do the `spec_exempt` reasons and one refusal in
  `isekai/boundary/wd14.py` ([D1](design.md#d1), [D2](design.md#d2)).
- **`CLAUDE.md`'s *Engineering conventions* gains the comment rule** ([D3](design.md#d3)).
- **A guard test fails on history in a comment or a docstring** ([D4](design.md#d4)).
- **The importer rows of three package READMEs name every importer** ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — comments, docstrings, a convention, a structural test and README rows; no behaviour moves.

## Impact

- **Files:** every commented file under the named trees, `CLAUDE.md`, `tests/test_spec_prose.py`, and
  `isekai/foundation/README.md`, `isekai/shared/README.md`, `isekai/boundary/README.md`.
- **Behaviour:** one refusal's words, in `isekai/boundary/wd14.py`. Every other module's code, docstrings aside, is
  the same before and after.
- **Formats:** none. The baked files' comments change; the pinned image is rebuilt with the next image rebuild.
- **Dependencies:** none.
- **Spend:** none.

## Not in this change

- **`ui/` and `evaluation/`** — with the UI work and the evaluation minor.
- **Rewording a comment beyond its history.**
- **Rebuilding the image** — with the next image rebuild.
