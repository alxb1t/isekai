# Design — v0.16, the flow registry

**Verdict: `feasible`.** Every edit is to code the suite already exercises, and the two largest — the
manifest fold and the run-layout restructure — fail **loudly**: the digest pin turns red on any change
to `flows/summon-v1/`, and ~60 hard-coded path assertions across 8 test files fail on any change to the
layout. Nothing here fails silently except one case, D7, which is given a detector before anything
moves.

**Three caveats, all settled below rather than left as conditions.** The freeze covers only files
directly in the flow directory (D1), so the fold must be flat or it means less than its own sentence.
`run-directory`'s living spec **states no requirement about stage directory names** (D6), so the
restructure is bound by nothing until this change writes the requirements. And the manifest's digest
moves against a test whose message forbids exactly that (D2) — an exception, recorded here and nowhere
else.

**Two decisions in the design record are overturned by this change, and both say so in both places**
(`flow-registry.md` §1c, `run-directory.md` §4): a caption belongs to a flow rather than to
`(input, briefing)`, and a flow declares no briefing names.

See [`proposal.md`](proposal.md) for why.

## Context

```
  main @ 483e575, clean, v0.15.0 tagged
  600 tests · 9 capabilities / 174 scenarios · openspec/changes/ holds only archive/

  flows/summon-v1/     flow.json · graph.json                      2 files
  schemas/             identity.v1.json · identity.v1.briefing.md  at the root
  briefings/           caption.md                                  at the root

  flow.json            10 keys; "models" is 12 bare destination paths
  build_graph          11 roles / 10 call sites, 0 guarded    generate.py:273-323
  upload_image         unconditional, BEFORE the first lookup generate.py:361
  --flow               3 of 6 verbs, single string, falls back to tracked_flows()
  the run layout       6 string values in run.py:93-98; 7 SHAPES across 5 files
  RUNS_ROOT            .data/runs — DOES NOT EXIST. Zero live runs.
```

Constraints this change works under:

- **The registry is append-only.** A flow that enters `flows/` is never deleted, is pinned, and is
  bound into the provisioning union. Nothing that is not a product flow may be placed there.
- **The suite is offline.** No scenario declares `e2e`; every acceptance row here runs on a laptop.
- **No phase is metered.** There are no live runs to migrate or re-render, so no pod is created.
- **Nothing checks the import graph**, by decision. D8's claim is held by a `grep` in `tasks.md`.

## Goals / Non-Goals

**Goals**

- A flow directory is the complete, frozen specification — schema, both briefings, graph, manifest.
- The code asks a flow what it has instead of assuming; a malformed flow fails `uv run pytest`.
- A flow shares nothing with another flow.
- The run layout is input-first, flow-second, so adding a flow adds one subtree.

**Non-Goals**

- **The input generalisation.** `input.json` / `input.<ext>` / a declared `kind` stay unscheduled; the
  frame keeps its `photo` block. Renaming the run id's *shape* is in; generalising what it holds is not.
- **The provisioning union.** `scripts/models.json` stays a flat union and keeps its shape. This change
  makes a flow *pin* what it uses (D4); it does not change what downloads.
- **Flow retirement**, deferred with the union.
- **A second flow.** `conjure-v1` is v0.17, and this change carries only a `tmp_path` fixture (D9).
- **An import-graph test.** Refused at v0.15's grilling and not reopened.

## Decisions

### D1 · The three files land flat, because the freeze only sees flat

`manifest_digest` (`flow.py:217-229`) walks `directory.iterdir()` filtered through **`path.is_file()`**.
A nested shape — `flows/summon-v1/schemas/`, `briefings/` — is invisible to it: the digest would not
move, the gate would stay green, and the freeze would silently stop covering the schema and both
briefings.

**Chosen: flat.** `image-generation/spec.md:45` already asks for it — *"altering a dial, a prompt
fragment **or any other declared value** fails the suite"* — and once folded, these are declared values.

**Consequence, accepted and recorded:** the digest moves. See D2.

**Acceptance instead of a comment:** a new test asserts that adding a sixth file to a flow directory
moves its digest, so the property is checked rather than believed.

### D2 · The re-pin is an exception, recorded here, and the test message does not learn about it

`tests/test_flow.py:253` fails on any digest change with *"Add the new flow rather than updating this
digest."* This change updates `PINNED` anyway.

**Alternatives considered.** (a) `summon-v2` for an otherwise identical configuration — refused: the
`-vN` suffix means *the configuration changed*, and here it did not; the id would lie about the one
thing it exists to tell the truth about. (b) A silent manifest migration — refused: *an immutable thing
is never migrated*, everywhere else in this record. (c) Re-basing the digest on a canonical projection
of declared content — refused: it would let a flow's *meaning* change while its digest held, which is
the property that makes the freeze trustworthy. (d) **An explicit exception — chosen.**

**The distinction being made:** *the flow's configuration did not change; its manifest's format did.*
**`manifest_version: 2` is that distinction in data** (D3), so the exception is machine-readable rather
than only prose.

**Consequence, accepted:** `test_flow.py:256`'s message keeps forbidding the bypass and gains no
"unless" clause. **A test message that explains how to evade itself is one that gets evaded.** The
exception lives in this file and in a comment beside `PINNED` naming this change.

### D3 · `flow.json` is eight keys and names none of its siblings

```
  flow · manifest_version · inputs · vocabulary · prompt · dials · nodes · models
```

`"schema"` goes with the fold. **`"graph"` goes with it** — a key that can only ever hold one value is
not a declaration. The five filenames are fixed; `load_flow`'s refusal becomes *"`summon-v1/` has no
`graph.json`"*, the same sentence with one fewer indirection.

**`schema_version` → `manifest_version`, bumped to 2.** It never meant the schema's version; it is the
version of `flow.json`'s own format (`flow.py:180`). Once `Schema.version` is deleted it would be the
only thing in the system called a *schema version* while meaning something else.

**Alternative:** declare all four siblings, twelve keys, keeping `flow.py:196`'s idiom. Rejected — four
keys that can only hold one value each are four new ways for a manifest to be wrong.

**Risk:** *declare, never compute* can be read against fixed filenames. It does not apply — that rule is
about **values that could differ**, not about a naming convention — but the reading exists and is
recorded here rather than glossed.

### D4 · A flow pins its model digests, because today it does not and that breaks the freeze

`"models"` is 12 bare destination paths; the digests are in `scripts/models.json`; `test_flow.py:138`
binds them **by path string**. So re-pinning `checkpoints/waiIllustriousSDXL_v170.safetensors` to
different bytes makes `summon-v1` render differently **under the same flow id, with the gate green** —
the exact failure L4 exists to prevent, on the 6.9 GB that decides what the image looks like.

**Chosen:** `"models": [{dest, sha256}, …]`, and the gate compares digests, not only paths.

**Why here and not later:** `flow.json`'s format changes **once**, under D2's deliberately expensive
exception. Adding digests afterwards is a second format change and a second exception.

**Consequence, accepted:** the digest now exists in two files. That is the shape of the defect this
change deletes from the vocabulary pin, so it is **only** acceptable with the gate check that holds them
equal — the provisioning manifests are *derived, never transcribed*
(`scripts/derive_manifest.py:3`), and the flow's copy is held against them by a test naming the flow.

### D5 · A flow shares nothing — caption and sheet sharing are deleted, not relocated

The record's plan was `captions/<briefing-name>/`, a briefing **name** declared in `flow.json`, a
`{name, sha256}` record and a reader that verifies the digest and refuses on mismatch.

**Refused.** What it buys is priced: a caption is **$0.0159/photo naive and $0.0013 cached and
batched**. Thirty flows over one photograph is **$0.48 at worst, ~$0.04 in practice**, against a
**$0.036** GPU boot.

**What it cost:** a directory level above the flow split · a declared name that can disagree with the
bytes beside it · a refusal path that exists only because of sharing · resume keyed on a pair.

**And it deletes the defect this version was cut to fix.** Resume no-ops on *any* caption today, so a
second flow inherits a reading written for a different question. With captions inside the flow, **two
flows never touch the same directory** — the bug cannot occur rather than being fixed.

**Sheet sharing goes by the same argument.** `_matching_flows` (`cli.py:190`) is its only mechanism, has
one caller, and is **the only production reader of both `Flow.schema` and `Schema.version`** — three of
this change's deletions collapse into one.

**Consequence, accepted and recorded:** two flows asking the same question of one input now get two
independent readings that may differ. An evaluator comparing those flows carries a small **caption-noise
confound** on top of the graph difference it means to measure. Comparing two flows end to end is the
honest comparison; it is still a thing that was free before and is not now.

### D6 · The layout restructure needs new requirements, because nothing states the old one

`openspec/specs/run-directory/spec.md` — all 313 lines — covers identity, the frame, provenance,
numbering, atomicity, listings, failures, budgets, schema refusal and containment. **It states nothing
about stage directory names.** So the restructure breaks no stated requirement and is bound by nothing.

**Chosen:** this change adds requirements naming the shape — input above, flow below, captions inside
the flow — and the run id's form. Otherwise the most invasive edit in the version is the least
specified.

**What holds it in the suite:** ~60 hard-coded path assertions across 8 test files, one of which
(`test_review.py:374`) hard-codes the *depth* as `parent.parent.parent`. They fail loudly and are
rewritten in the phase that moves the layout.

### D7 · The one edit that could fail quietly, and it gets a detector first

`isekai/boundary/claude_cli.py:267` records a briefing's path **relative to `ROOT`**, so after the fold
every producer record silently starts writing `flows/summon-v1/caption.briefing.md`.
`tests/test_caption.py:197` pins the old literal against a **real** record and fails loudly — good. But
`tests/test_run_directory.py:324` and `:335` pin the same literal while **constructing the record
themselves**, so they stay green while asserting a path the code no longer writes.

**Chosen:** phase 1 rewrites those two to read a record the code produced, **before** anything moves —
a detector while the anchor is still correct, the same shape v0.15 used for `DATA_ROOT`.

### D8 · `validate` moves to `shared/fields.py`, and the last stage→stage import dies

`review.py:56` imports and calls `sheet.validate` — the sixth of six such edges and the only one v0.15
did not close.

**What decided it is a fact the question did not have:** `validate`'s refusals read `schema.version`
(`sheet.py:160`), which this change deletes. **The function is edited either way**, so moving it is
three import lines — `sheet.py`, `review.py`, `tests/test_sheet_schema.py:20` — on top of an edit that
is already happening.

**Not `foundation/flow.py`**, beside `Schema` and `assemble()`: `shared/vocabulary.py:33` already
imports `foundation.refusal`, so a vocabulary-dependent function in `foundation` would make the two
groups depend on each other in both directions. **`shared` already imports `foundation`**, so this adds
no new direction.

**Acceptance instead of a test:** `grep -rn 'from isekai.pipeline' isekai/pipeline/` returns nothing.
Nothing in the gate checks the import graph, by decision — so the claim goes from *false and unenforced*
to *true and unenforced*, and the grep is named in `tasks.md`.

### D9 · Four roles required, seven guarded — and the fixture flow lives in `tests/`

`build_graph` performs 11 lookups across 10 call sites, none guarded, and `load_flow` checks only that
the **key** `nodes` exists. All four `tracked_flows()` loops in `test_flow.py` skip `nodes` entirely, so
a new flow declaring seven roles passes the whole gate and dies on a rented pod — after
`upload_image` (`generate.py:361`) has already spent it.

**Chosen:** `REQUIRED_NODES = {positive, negative, latent, sampler}`, checked in `load_flow` the way
`REQUIRED_PROMPT` (`flow.py:56`) already checks the prompt's fragments; the other seven guarded.
`photo`, `scale`, `identity` and `openpose` go for a sheet-only flow — and so do `clip_skip`,
`hires_resize` and `hires_sampler` for any flow without a hires pass, which is an ordinary cheaper flow.

**Alternatives.** (a) Every role optional with only a structural `nodes`↔`graph.json` check — refused:
it trades a loud offline refusal for a silent bad render. (b) A role→patch table — refused: the right
shape for thirty flows, too much new structure for one.

**The fixture is a `tmp_path` scratch, never a directory in `flows/`.** Anything in `flows/` becomes a
product flow: pinned (`test_flow.py:264` asserts the pinned set *is* the tracked set), bound into the
provisioning union (`:133`, `:142`), selectable, and **undeletable** under the append-only rule.

**And `flow.inputs` gets its first production reader.** It is declared (`flow.py:115`), populated
(`:206`) and read only by `tests/test_flow.py:62` today. `upload_image` becomes conditional on
`"photo" in flow.inputs`.

### D10 · The run id keeps twelve hex and changes its separator

`run_id` (`run.py:143`) writes `<12 hex>-<slug>`; the design record drew `<6 hex>_<slug>`, and nothing
recorded the difference.

**Twelve stays.** Six is a birthday collision at roughly 4,800 inputs, and the record's remedy —
*"lengthen the prefix"* — is a migration it refuses to build mechanisms for elsewhere. A collision is
not unsafe: `_run_for` (`run.py:207`) checks the frame's *full* digest and refuses rather than mixing
two people's photographs. It is a hand-rename nobody should be asked for.

**The separator becomes `_`.** `slug()` maps every unsafe character to a hyphen, so
`0bfdc0612d98-cowboy-shoot-1` gives a reader no way to see where the digest ends. **A slug can never
contain an underscore.** Nothing parses the id — `startswith` on the prefix is its only use — so this is
readability alone, and it is affordable **only in this version**, which is already rewriting every
hard-coded layout assertion.

### D11 · Resume owes exactly the PNG assumption and no more

`rendered_seeds` (`generate.py:227`) filters `iterdir()` on `path.suffix == ".png"`, so resume is
PNG-shaped. The output *path* already generalises. **This change makes the predicate ask the flow what
it produces and stops there** — a video flow is unscheduled, and this is the one line that keeps it
cheap when it arrives.

**Found beside it, and deliberately not fixed here:** the provenance `<seed>.json` is written two lines
*after* the `.png` (`generate.py:385`, `:387`), and `rendered_seeds` keys on the PNG alone — so a crash
between them leaves a seed resume considers done forever, with no provenance.
`test_generate.py:552` monkeypatches `fsync` during the **PNG** write and never exercises that window.
**Recorded in Open Questions with what it blocks.**

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| the fold lands nested and the freeze quietly narrows | D1; plus a test asserting a sixth file moves the digest |
| the digest re-pin becomes a habit | D2: the test message gains no escape clause, and the exception is named in one commit |
| the model digest becomes a second declaration that drifts | D4: the gate compares it to the derived manifest; without that check the change is worse than not doing it |
| a producer-record path changes under a green test | D7: the two constructing tests are rewritten **first**, before anything moves |
| the layout edit is large and partly unspecified | D6 writes the requirements; ~60 assertions fail loudly; the phase lands alone |
| a path in a file no gate command reads | an acceptance row is a `git grep` over **all** tracked files — v0.15 shipped a broken `Dockerfile` COPY exactly this way |
| the version is large | argued and kept whole at the grilling; phase ordering is what keeps it reviewable |

## Migration Plan

**None required, and that is a finding rather than an assumption.** `RUNS_ROOT` is `.data/runs`
(`run.py:53`) and **that directory does not exist** — there are zero live runs. The only corpus is 5
runs, 39 MB, at `.data/v0.13/runs`, reachable only with `--runs`, written by the walking skeleton on
2026-09-14, whose render filenames are dates rather than seeds. **They stay where they are, under the
old shape, and nothing reads them.**

No pod is created and none may be. Rollback is `git revert`; nothing on disk outside the repository is
touched.

## Open Questions

**None that affect this change.**

Deferred, each with what it blocks:

- **A flow declaring two briefings** — a video flow wants an `identity` reading of a photograph and a
  `motion` reading of the operator's text, which needs a key under `<flow-id>/captions/`. No flow
  declares two. **Blocks: the first multi-briefing flow.**
- **A crash between a render and its provenance** (D11) leaves a permanently skipped seed with no
  provenance. **Blocks: nothing — but it is a paid artifact losing its record.**
- **A `KeyError` escaping the render's failure recording.** A declared role naming a node id absent from
  `graph.json` raises from the enclosing subscript, and `except Refusal` (`generate.py:373`) does not
  catch it. **Blocks: nothing; it is a worse message, not a wrong result.**
- **The provisioning union and flow retirement**, unchanged by this change. **Block: catalogue scale.**
- **The input generalisation** — `input.json`, `input.<ext>`, a declared `kind`. **Blocks: the first
  text flow.**
