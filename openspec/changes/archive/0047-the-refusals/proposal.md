---
version: v0.30.4
backlog: [0027·entry-for-message, 0030·R4, 0032·R2, 0032·multi-flow-refusal, 0033·R5, op·log-since]
---

# 0047 — the refusals

Every refusal names a command that works, one flow's refusal keeps the others, and nothing a batch skips goes
unsaid. `tag` names the next verb for an untagged flow; every verb collects refusals per flow; `generate` refuses a
named flow that is not approved; `show` marks a frame it cannot read; the Ollama refusals name the provisioning step;
an undeclared artifact is a refusal; the host-key check reads the log's last lines.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each refusal's shape, and the host-key read |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `caption`, `cli`, `image-generation`, `model-provisioning`, `tagging` |

## Why

**Some refusals name a remedy that fails, and some failures are not refusals.** `tag` tells a lone untagged flow to
"drop `--flow`", which argparse refuses; the Ollama refusals send an operator to a build that fails without the
model's files; an artifact missing from `config/vocabulary.json` ends `tag`, `sheet`, `approve` and `ui` in a
traceback; a frame `show` cannot read refuses the whole report.

**Some flows are dropped without a word.** One flow's refusal abandons the input's other flows in `caption`,
`sheet`, `review` and `approve`; `generate` skips a named, unapproved flow beside an approved one.

**The host-key check can refuse a healthy pod.** Its read of the pod's log by `since` stalled on a live boot.

## What Changes

- **`tag` given only untagged flows says it has nothing to do and names `sheet`** ([D1](design.md#d1)).
- **Every stage verb collects refusals per flow** ([D2](design.md#d2)).
- **`generate` refuses a named flow with no approved sheet, whatever its siblings** ([D3](design.md#d3)).
- **`show` marks a frame it cannot read and lists the rest** ([D4](design.md#d4)).
- **The Ollama refusals name the provisioning command first** ([D5](design.md#d5)).
- **An undeclared artifact is a refusal naming the manifest searched** ([D6](design.md#d6)).
- **The host-key check reads the log's last container lines** ([D7](design.md#d7)).
- **The binding checker demands a test for a key once it is in the living spec**, so a cut adding a scenario stays
  green ([D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tagging`: MODIFIED *Both taggers run for a flow that declares the tagger, …* — gains a command naming only
  untagged flows.
- `cli`: MODIFIED *Every stage verb requires the flows it acts on, and takes more than one* — gains one flow's refusal
  leaving the others.
- `cli`: MODIFIED *Inspection prints the run directory with its provenance* — gains a frame it cannot read, marked.
- `image-generation`: MODIFIED *Only an approved sheet is rendered* — `every-approved-flow-renders` names the flows
  the invocation names.
- `caption`: MODIFIED *A hosted model that is not running or not installed is refused before any attempt is spent* —
  gains a model with no readable record naming the files first.
- `model-provisioning`: MODIFIED *The tag vocabulary and the model it indexes are provisioned from one manifest* —
  gains an undeclared artifact, refused.

## Impact

- **Files:** `isekai/interface/cli.py`, `isekai/interface/run_view.py`, `isekai/interface/wiring.py`,
  `isekai/pipeline/generate.py`, `isekai/boundary/ollama.py`, `isekai/boundary/wd14.py`, `isekai/shared/vocabulary.py`,
  `isekai/foundation/run.py`, `infra/up.sh`, `tests/test_spec_bindings.py`, and their tests.
- **Behaviour:** refusals change their words and reach flows they skipped; a render session now refuses a batch
  with any named flow unapproved on any run, before anything is rented.
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** none.
- **Spend:** none; the host-key read is proved at the next metered session.

## Not in this change

- **`show` listing failure records and the directories it does not read** — `op·show-skips`, the next change to
  `run_view.py`.
- **A message from `generate` without `--server`** — `render.sh`'s free first step.
- **Rendering an approved flow the invocation does not name.**
