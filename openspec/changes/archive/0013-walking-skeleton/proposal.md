---
version: v0.13
---

# The walking skeleton

## Why

**`main`'s pipeline is one command over one graph, and every criterion it draws is typed into the
graph's own JSON.** `convert.py photo.jpg` renders a photograph through img2img with a positive
prompt committed to `workflows/pipeline.json` — so the subject of the image is whatever string was
last edited into node 3. Nothing reads the photograph, nothing describes the person in it, and there
is no place for a human to correct what a reader got wrong.

A prototype answered what the shape should be instead: a photograph is **read into prose**, the prose
is **sorted into a sheet of canonical tags**, a human **corrects the sheet**, and the sheet is
**assembled into a prompt**. Two of those numbers are worth restating here because they are what this
change is built on: sorting into a *constrained* vocabulary rather than free text is worth **9.6x**,
and the human correcting the sheet carries **0.568 → 0.917** of the sheet's attributes through to the
render.

**This version builds that path end to end on one flow, and changes nothing about the existing one.**
The risk it carries is the architecture — four boundaries that have never been passed anything — so it
crosses each once while each is still thin, rather than deepening any of them.

## What Changes

- **A new command surface, `python -m isekai <verb>`, in a new module.** Six verbs:
  `caption` · `sheet` · `review` · `approve` · `generate` · `show`. It is additive: `convert.py`,
  `isekai/cli.py` and the graph they drive are **not touched**.
- **A run directory, `.data/runs/<photo-id>/`, which is the only thing the four stages share.** A
  content-hash id, the photograph copied in rather than pointed at, append-only numbered artifacts,
  and every "is this done?" answerable by a directory listing.
- **Stage ① — read a photograph into prose.** `claude -p` with a single tool. The reader is told
  nothing about schemas, flows or what happens next, and is licensed to state absence.
- **Stage ② — sort prose into a sheet of canonical tags.** `claude -p` with a JSON schema, then a
  deterministic mapper onto the vocabulary. No absence clause and no out-of-vocabulary tag survives it.
- **Stage ③ — `review` then `approve`.** `review` copies the sheet into a separate, editable
  directory; `approve` validates every tag and renames. **②'s output is never edited**, which is now a
  property of the layout rather than a rule.
- **Stage ④ — assemble every prompt locally, then render.** Assembly is pure and free, so a malformed
  sheet is caught before a GPU is rented.
- **Idempotence, atomic writes, and retry budgets.** A command whose artifact exists is a no-op; every
  artifact is written temp-then-rename; an error file records its attempt's kind in its filename, and a
  stage at its budget refuses rather than spending again.
- **The vocabulary becomes a provisioned artifact.** `models/wd14/selected_tags.csv` — 8,106 canonical
  tags with post counts — is gitignored today, so a fresh clone cannot fill a sheet at all. It gains
  its own pinned, digested manifest.
- **One shared manifest module.** `scripts/manifest.py` carries the types and both digest strategies;
  the three derivers become a table of what to pin plus a `derive()`. Their output stays byte-identical.
- **A flow is a directory and is immutable.** `flows/summon-v1/` declares its dials; changing one
  creates a new flow id rather than editing this one, and the gate holds the manifest by equality.

### Deviations from `CLAUDE.md`, stated rather than left to be noticed

1. ***"There is one path. A version may replace it; it may not add a second."*** — **v0.13 carries
   both**, scoped to this version alone. The replacement is proved before the proven thing is
   destroyed; v0.14 is the deletion. `convert.py photo.jpg` still works, unchanged, for the whole of
   this version.
2. **The one-path bullet is replaced by an entry gate, not a count.** An implementation becomes
   selectable by passing a prototype round and a measured bar, and is removed by the version that
   retires it. "One" was a count written because four models were carried and three were dead; a gate
   makes a dead implementation impossible by construction.
3. ***Design reasoning lives in `design.md` "and nowhere else"*** — still true of this change, and
   `design.md` carries it.

## Capabilities

### New Capabilities

- `run-directory`: the layout every stage couples through — the photo-id, the frame, append-only
  numbering, approval in the filename, atomic writes, error files with their kind and attempt, retry
  budgets, schema refusal, and what "done" means for each stage.
- `caption`: stage ① — a photograph in, descriptive prose out, with no knowledge of schemas or flows.
- `sheet`: stage ② — prose, a schema and a vocabulary in, a filled sheet of canonical tags out.
- `review`: stage ③ — the editable copy, the validation, and the rename that is approval.
- `image-generation`: stage ④ — the flow manifest, prompt assembly, rendering, and provenance.

### Modified Capabilities

- `cli`: gains requirements for the six new subcommands, their flags and their refusals. **No existing
  `cli` requirement changes** — `convert.py`'s surface is untouched.
- `model-provisioning`: gains the vocabulary as a provisioned artifact and the shared derivation
  module. Existing pinning, digest and fallback requirements are unchanged.

## Impact

**New:** `isekai/__main__.py` · `isekai/vocabulary.py` · `isekai/refusal.py` · `isekai/run.py` ·
the four stage modules · `scripts/manifest.py` · `scripts/derive_vocabulary.py` ·
`scripts/vocabulary.json` · `schemas/identity.v1.json` and its briefing · `briefings/caption.md` ·
`flows/summon-v1/`.

**Touched:** `isekai/evaluate.py` — `Refusal` moves to its own module and is re-exported, so both
existing importers keep working and no behaviour changes. `scripts/derive_manifest.py` and
`scripts/derive_eval_manifest.py` — the shared names move out; both must still produce byte-identical
output. `eval_licences.md` — one row for the vocabulary.

**Not touched:** `convert.py` · `isekai/cli.py` · `isekai/workflow.py` · `isekai/mutate.py` ·
`isekai/overrides.py` · `isekai/pipeline.py` · `workflows/pipeline.json`. The new path **imports**
the header parser and the transport; it edits neither.

**Dependencies:** none added — `dependencies = []` holds, and the new entry point gets its own
stdlib-only subprocess guard beside the existing one. **New runtime requirement:** the `claude`
binary on `PATH`, and a subscription. A clone without one cannot run stages ① and ②; the README says
work in progress for exactly this reason, and v0.15's open models are what remove it.
