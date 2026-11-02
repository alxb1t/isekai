---
bump: patch
version: 0.60.1
---

# 0088 — mf readiness

isekai made ready for an unattended `mf-ship`: a fresh worktree passes the gate, the release's changelog passes its
test, and review has the documents it reads. No format, verb or product moves.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision |
| [tasks](tasks.md) | the phases, in build order |

```
1 the worktree    make setup · the Worktrees, Workspace setup and Ship network lines · the no-proxy opener
2 the changelog   a fresh worktree proved · the test and the preamble follow the release
3 the documents   CODING_STANDARDS, CONTRIBUTING, ARCHITECTURE · AGENTS.md cut to instructions
4 the threat      THREAT_MODEL.md, named in AGENTS.md
5 the ruleset     a person protects main
```

## Why

**A run starts from a checkout that holds only tracked files, and nothing in this repository is ready for that.** The
gate refuses without `ui/node_modules/`, Chromium and the vocabulary, none of which a fresh worktree has. A run refuses
without `**Worktrees:**`. The release writes a changelog heading the repository's own test fails. Review reads a threat
model and standards that do not exist, so those sections read `inconclusive`. `main` takes a force-push.

## What Changes

- **`make setup`** restores what a fresh worktree lacks ([D1](design.md#d1)); `AGENTS.md` declares it and the run's
  lines ([D2](design.md#d2)); the browser tests' wait ignores a proxy ([D3](design.md#d3)).
- **The changelog's test** follows the release ([D4](design.md#d4)).
- **The rules move** out of `AGENTS.md` into `CODING_STANDARDS.md` and `CONTRIBUTING.md`, and the change cut is
  rewritten for today's line ([D5](design.md#d5)).
- **`ARCHITECTURE.md`** maps `docs/` ([D6](design.md#d6)); **`THREAT_MODEL.md`** is new ([D7](design.md#d7)).
- **A ruleset on `main`**, by a person ([D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: no living spec names the changelog's format, the gate's setup or these documents. `skip_specs: true`.

## Impact

- `Makefile`, `AGENTS.md`, `CHANGELOG.md`, `README.md`, `.github/workflows/ci.yml`.
- `tests/e2e/conftest.py`, `tests/test_changelog.py`, `tests/test_spec_prose.py`.
- New at the root: `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, `THREAT_MODEL.md`.
- The repository's rulesets on GitHub.

## Not in this change

- `mf-ship`, and the gate under a real worker: they wait for MinionsFactory's sandbox.
- `github.com` in `**Ship network:**`, unless that proof needs it.
- `openspec/config.yaml`: no station needs it.
- A pull-request rule on `main`: a release pushes to it.
- Any backlog card: the paydown is its own version.
