# Design — 0046 the terse specs

How the specs are rewritten to one rule without changing a requirement's meaning, title or key, and how a test keeps
them that way. **Verdict: feasible** — prose in MODIFIED blocks, checked by the binding checker, the new guard and
converge's meaning review.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`9995b54`):

- **The specs** (a read of `main` before v0.30.2, which added one scenario): 14 capabilities, 42,108 words, 135
  requirements, 388 scenarios; a requirement body averages 144 words, `sheet`'s 286. `pod-image`, `evaluation`,
  `agent-skills` and `comfy-transport`'s bodies are terse already. No spec links a decision or has a diagram.
- **History:** version numbers at `cli/spec.md:315`, `comfy-transport/spec.md:20-21`, `image-generation/spec.md:24` and
  `:385`, `ui/spec.md:142-144`; a commit hash at `comfy-transport/spec.md:21`; about 43 paragraphs narrate past states
  or defend old wording. About 8 cite measured figures.
- **Stray lines:** `</content>` at `model-provisioning/spec.md:290`; a blockquote at `comfy-transport/spec.md:72-74`,
  between requirements. Nine lines exceed 120 characters, none in `ui` or `evaluation`.
- **`0044·R10`:** `pod-image/spec.md`'s *No `isekai` pod goes unseen* fails the listing on "a pod this project named"
  with no image, and so does its scenario, while *a terminated pod is not listed* and `infra/pods.sh:23` drop
  TERMINATED pods first.
- **The machinery:** a delta's MODIFIED block replaces a requirement by title at release, and OpenSpec 1.11 refuses
  one that drops or renames a scenario. `tests/test_spec_bindings.py` reads each active delta's sections (`:36-68`)
  and holds every key. `## Purpose` is edited in `openspec/specs/` in place. No test checks a link in a spec.
- **`CLAUDE.md`:** *How a change is cut here* is `:72-143`; *The living spec* is `:103-113`.
- **Decisions to link:** `docs/decisions.md` headings are `### D<n> · <title>`, linked as `#d<n>--<slug>`, e.g.
  `D18 · Runs stay out of what git tracks` (`:220`).

## Goals / Non-Goals

**Goals:** every rewritten requirement readable in one pass, with its meaning, title and keys unchanged; a stated rule;
a guard for what can be checked.

**Non-Goals:** `ui` and `evaluation`; retitling; changing a SHALL; reading a scenario against the code.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | *How a spec reads* in `CLAUDE.md`, after *The living spec*, with the `run-directory` before → after | the next delta follows a stated rule | a rule in a skill, which a reader of the repo never sees |
| [D2](#d2) | each requirement that breaks the rule becomes a MODIFIED block in `specs/<capability>/spec.md`, titles and keys kept | OpenSpec folds it at release; keys hold every test | editing `openspec/specs/` in place, which bypasses the delta |
| [D3](#d3) | `## Purpose`, the `</content>` line and the blockquote are edited in `openspec/specs/` in place | a delta cannot carry text outside a requirement | — |
| [D4](#d4) | the no-image rule and its scenario name a live pod | the listing drops TERMINATED pods first | — |
| [D5](#d5) | a guard test reads the *effective* spec and fails on a version, a change id, a commit hash, or a line over 120 characters; `ui` is exempt from the history rule until it is rewritten | deltas reach `openspec/specs/` only at release, so the effective spec is what the release will fold | a guard over `openspec/specs/` alone, red for the whole build |

### D1

**The rule.** After `CLAUDE.md:113`, a paragraph headed ***How a spec reads***:

- A requirement is one SHALL paragraph: what the system does, testable. Then one *why* line, in the present tense; a
  decision in force is linked, not retold.
- A scenario has one WHEN, one THEN and at most two AND, each on one line where it fits. It carries no reasons.
- A flow, a state or a layout gets an ASCII diagram.
- No history: no version, no change id, no "used to", no "this change". A figure stays only when it is the rule.
- `## Purpose` is one or two sentences.

Its example is `run-directory`'s *A run root is under the ignored root or outside the repository*: 282 words before;
after, one SHALL paragraph and one *why* linking
[D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks).

### D2

**The rewrite.** For each capability in its phase:

```
openspec/specs/<cap>/spec.md ──read──▶ each requirement ──breaks the rule?──▶ no: left alone
                                                              │ yes
                                                              ▼
            specs/<cap>/spec.md  ◀── MODIFIED block: same title, same scenario titles and keys,
            (this change)            one SHALL paragraph + one why, scenarios without reasons
```

- **Meaning:** every SHALL clause survives, in fewer words. A clause whose meaning would change is left as it is and
  named in the phase's commit.
- **Links:** a *why* that a decision holds links it, relative to `openspec/specs/<cap>/`:
  `../../../docs/decisions.md#d<n>--<slug>`.
- **Figures:** measured figures go; a number that is the rule stays.
- **Diagrams:** a requirement describing a flow, a state or a layout gets one, in a fenced block.

### D3

**Outside the requirements.** In `openspec/specs/<cap>/spec.md`, in the phase that rewrites the capability: `## Purpose`
is one or two sentences with no history; `model-provisioning/spec.md:290`'s `</content>` and
`comfy-transport/spec.md:72-74`'s blockquote are deleted.

### D4

**`0044·R10`.** Written at the cut in `specs/pod-image/spec.md`: "or a pod this project named carries no image" →
"or a live pod this project named carries no image", and the scenario's WHEN → "a pod named for this project, and not
terminated, carries no image". Phase 1's rewrite of `pod-image` keeps the sentence and the scenario.

### D5

**The guard.** A new `tests/test_spec_prose.py`:

- **The effective spec:** for each capability, the living `spec.md` with every active delta's MODIFIED blocks in place
  of the requirements they name and its ADDED blocks appended — the sections `tests/test_spec_bindings.py` reads.
- **The rules:** no isekai version (`v0.<n>`), no change id (`00<nn>` followed by a slug or `design`), no commit hash
  (a backticked run of 7 to 12 hex characters), no line over 120 characters. `ui` is exempt from the version,
  change-id and commit rules until the UI work rewrites it.
- **Twins:** each rule catches a planted line in a temporary tree.

It lands in the last phase, once every capability's rewrite is in the delta.

## Dependencies

None.

## Risks / Trade-offs

- **A rewrite changes a meaning** → converge's review compares each MODIFIED block with the living text it replaces;
  the keys and the binding checker hold the scenarios.
- **A hex run in a spec is not a commit** → the guard names the line; the rewrite spells it differently.
- **The delta files are large** → one phase per group of capabilities keeps each diff readable.

## Verdict

**feasible** — a prose rewrite in the delta, a rule, and a guard.
