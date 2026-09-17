# No spec delta

**This change alters no requirement and no scenario.** It adds an **instance** of something the living
spec already describes: `flows/conjure-v1/`. The registry's requirements are written over an **N-flow**
registry, not over `summon-v1`.

**Three multi-flow scenarios already exist, written by earlier versions, and none has ever been run:**

- `caption:output:caption-belongs-to-one-flow` — *"WHEN a second flow is added to a run that already has
  a caption"* (`openspec/specs/caption/spec.md`)
- `openspec/specs/cli/spec.md:197` — *"WHEN a stage verb is given more than one flow"*
- `openspec/specs/image-generation/spec.md:162` — *"WHEN a run has approved artifacts for more than one
  flow"*

**This change turns written requirements into tested ones without editing any of them.** That is the
opposite of a delta.

**Nothing constrains briefing content.** `openspec/specs/caption/spec.md:100` constrains what *reaches*
the reader — *"no schema, no field list, no vocabulary and no flow identifier"* — and never what the
standing instructions **say**. `conjure`'s briefing licenses inference on named axes and passes the
reader no schema, so the requirement is untouched. Likewise `openspec/specs/sheet/spec.md:153` describes
the schema's shape generically: a field's name, whether it is scored, and the suffix convention. A
21-field schema satisfies it exactly as a 16-field one does. **No spec hard-codes the flow inventory or
the field count.**

**One requirement is genuinely owed and is deliberately not written here.** Two flows named in one
invocation are not seed-matched: `seeds_for` draws per `(run, flow, version)` directory from one shared
`Random` (`isekai/pipeline/generate.py:389-393`, `isekai/interface/wiring.py:58`). **The behaviour is
deferred to the version that needs it** — a cohort cannot be compared across flows without it — and
**a requirement written without its behaviour is a red gate.** It travels with the fix, as one thing.
*Do not invent a requirement to satisfy the validator.*

`.openspec.yaml` declares `skip_specs: true` beside `schema: spec-driven`; both keys are load-bearing.

→ `proposal.md` — Capabilities · `design.md` — Non-Goals

> **Why this file is not `specs/README.md`.** The validator treats **every** file under `specs/` as a
> delta spec, so an explanation placed there fails `--strict` with *"skip_specs is set but spec files
> exist"*. `specs/` holds `.gitkeep` and nothing else.
