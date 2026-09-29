---
version: v0.30.3
backlog: [0044·R10]
---

# 0046 — the terse specs

Every living spec but `ui` and `evaluation` reads terse: one SHALL paragraph and one present-tense *why* per
requirement, decisions linked, scenarios stating a condition and an outcome, a diagram for any flow or state. Titles
and keys are kept. `CLAUDE.md` states how a spec reads, and a test keeps history out.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the rule, the rewrite, the guard, and the phases |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | a MODIFIED block per rewritten requirement, by capability |

## Why

**The older specs are long-form.** They carry paragraphs of history — versions, "this change", "used to" — bold
paragraphs defending old wording, measured figures, and reasons inside scenarios. A reader, human or agent, pays for
all of it to learn what the system does.

**Nothing states how a spec should read**, so a new delta copies whatever it sits beside.

## What Changes

- **`CLAUDE.md` gains *How a spec reads*** ([D1](design.md#d1)).
- **Every requirement in `agent-skills`, `caption`, `cli`, `comfy-transport`, `field-map`, `image-generation`,
  `model-provisioning`, `pod-image`, `review`, `run-directory`, `sheet` and `tagging` whose text breaks the rule is
  rewritten as a MODIFIED block; titles and keys are kept** ([D2](design.md#d2)).
- **Each of those capabilities' `## Purpose` is one or two sentences**, and the stray `</content>` line and
  blockquote go ([D3](design.md#d3)).
- **`0044·R10`:** the no-image rule names a live pod ([D4](design.md#d4)).
- **A guard test fails on a version, a change id or a commit hash in a spec, and on a line over 120 characters**
  ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-skills`, `caption`, `cli`, `comfy-transport`, `field-map`, `image-generation`, `model-provisioning`,
  `pod-image`, `review`, `run-directory`, `sheet`, `tagging`: MODIFIED — each rewritten requirement keeps its title,
  its scenarios' titles and keys, and its meaning.
- `pod-image`: MODIFIED *No `isekai` pod goes unseen* — the no-image rule and its scenario name a live pod.

## Impact

- **Files:** `CLAUDE.md`; the `## Purpose` sections of the capabilities above in `openspec/specs/`; the stray lines in
  `openspec/specs/model-provisioning/spec.md` and `openspec/specs/comfy-transport/spec.md`; a new guard test in
  `tests/`.
- **Behaviour:** none.
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** none.
- **Spend:** none.

## Not in this change

- **`ui` and `evaluation`** — each rewritten with the work that reshapes it.
- **Retitling a requirement or a scenario.**
- **Reading a scenario against the code** — after the portfolio.
