---
version: v0.25
---

# 0035 — the flow skills

Skills that let an AI agent run the flows for the operator with little context: `run-flows` takes a directory of
photographs through review and the GPU to a comparison page, and `compare-renders` builds the page alone.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the batch layout, the skills' steps and stop points, the verb and the script behind them |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | the `compare` verb, a render session that always tears down, skills whose commands parse |

## Why

**Datasets for the portfolio and for the evaluation are made by running every verb by hand, or by asking an agent
to.** An agent does not know the CLI, looks it up in the source, and still makes mistakes; each lookup and each
page of output spends its context.

**Two steps need more than instructions.** The comparison page cannot be written without reading the run
directories, which is what an agent must not do; and a render session left between `up.sh` and `down.sh` bills.

## What Changes

- **Two skills in `.claude/skills/`** — `run-flows` and `compare-renders` — naming exact commands, where to stop
  for the operator, and what never to read ([D1](design.md#d1)).
- **A new verb, `compare`**, writes the comparison page into the batch directory and prints only its path
  ([D2](design.md#d2)).
- **`infra/render.sh`** runs a whole render session, with a trap that always tears the pod down
  ([D3](design.md#d3)).
- **`CLAUDE.md`'s pod rule**: a pod goes up for a metered phase or the operator's explicit go in the session, and a
  teardown the MCP confirms after a non-204 removes the record files ([D4](design.md#d4)).
- **The tagger's native abort at exit is fixed** ([D5](design.md#d5)).
- **A test holds every command a skill names against the parser** ([D6](design.md#d6)).

## Capabilities

### New Capabilities

- `agent-skills`: the skills an agent follows to run the flows, and the check that keeps their commands true.

### Modified Capabilities

- `cli` · *A comparison page shows every run's photograph beside its renders* — added.
- `pod-image` · *A render session always tears its pod down* — added.

## Impact

- **Files:** `.claude/skills/` (new), `isekai/interface/` (`cli.py`, a new `compare_view.py`), `infra/render.sh`
  (new), `isekai/boundary/wd14.py`, `tests/`, `CLAUDE.md`, `README.md`, `docs/data-flow.md`, the `cli` spec's
  preamble, `CHANGELOG.md`.
- **Behaviour:** a new verb and a new script; nothing an existing verb writes changes.
- **Dependencies:** none.

## Not in this change

- **Stripping EXIF** — privacy is a later version, and the portfolio uses synthetic portraits.
- **`AGENTS.md`**, and a skill for new drafts of the same photographs.
- **A batch verb or a status verb** — the skills chain the existing verbs.
- **Polling the review surface** — the operator says "approved".
- **`down.sh` reading a 404 as gone** — `v0.24.1` keeps the record files on a 404 on purpose.
