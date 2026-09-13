# PRODUCT — the engineered shape

**Round 5, N43 onward. Opened 2026-09-13.** What the pipeline is *as software*: its seams, its facades,
and the one contract they share. Every section cites the law in [`OPEN.md`](OPEN.md) that licenses it.

> **This does not supersede [`ARCHITECTURE.md`](ARCHITECTURE.md) and does not edit it.**
> `ARCHITECTURE.md` is the **measured** shape — four stages, every box cited to a finding.
> This is the **engineered** shape. One is evidence, the other is design, and merging them would put an
> unmeasured decision beside a cited number as though they had the same standing.

**Nothing here is built on this branch.** It is what the changes cut on `main` are written against, under
[`../../CLAUDE.md`](../../CLAUDE.md) § *How a change is cut here*.

---

## 1 · The shape

```
   CLI  convert.py photo.jpg          UI  upload · monitor · review · trigger
   stdlib, on the guarded graph           off the graph — free to need wheels
        │                                          │
        └──────────────────┬───────────────────────┘          L1 · L2
                           ▼
                     ORCHESTRATOR              stdlib source, lazy third-party
                           │                   imports no front end, ever
      ┌────────┬───────────┼───────────┬────────────┐
      ▼        ▼           ▼           ▼            ▼
   ① VLM    ② LLM     ③ REVIEW   ④ GENERATE    ⑤ EVALUATE
    see      sort      correct       draw          judge
      │        │           │           │             │
      └────────┴─────┬─────┴───────────┴─────────────┘
                     ▼
              runs/<photo-id>/          ← the ONLY coupling between layers:
              append-only, numbered        a path and a schema · L11 · L12
```

**Four properties, and every decision below is bound by them.** Each layer is a facade; **no layer knows
another exists**; the directory path is a convention rather than a value anyone passes; and **the
orchestrator pushes** — layers are driven, never chained.

---

## 2 · The five contracts

Each is stated in four terms, because a facade asserted in fewer is a facade by assertion.
**`../../CLAUDE.md`'s seam rule is the test**: *a parameter is a seam only if something else is actually
passed through it.*

### ① VLM — SEE

| | |
|---|---|
| **takes** | a photograph, and the criteria schema it should address |
| **returns** | **descriptive prose** that addresses every criterion, **including the ones it sees nothing for** |
| **may assume** | nothing about flows, vocabularies or what happens next |
| **must not break** | the prose is the *only* output; it never emits tags, and it never sees a flow id |
| **second implementation** | **yes, two measured** — JoyCaption **0.518**, the agent session **0.795** (F42) |

**The briefing must ask about every criterion *and license absence in the same breath*, and this is not
a stylistic preference.** F43: *"do not leave one blank"* produced **nineteen invented identity marks on
seven of ten subjects** and dropped the score from 0.518 to **0.307**. F44: licensing it to write
*"no tattoos are visible"* stopped the confabulation — **and then rendered tattoos**, because CLIP has
no negation.

> **The two findings are not in tension; they name the seam.** ① must be *allowed* to state absence, and
> ② is where absence *dies*. A component converts a licensed absence into an empty field, and that
> component is the reason this is a seam rather than plumbing.

**Its ceiling is its eyes, and no briefing reaches past that.** `00003`'s eyes are green; JoyCaption
returned brown, blue, brown, light brown, blue, brown and brown across seven prompts and never once said
green. **Rank a reader's failures into omission and perception before trying to prompt around them** —
only the first kind is reachable.

### ② LLM — SORT

| | |
|---|---|
| **takes** | prose, a **schema**, and a **vocabulary** |
| **returns** | a filled sheet — fields only, **never an assembled prompt** (L9) |
| **may assume** | nothing about which flow asked, or how many will consume the result |
| **must not break** | **no absence clause survives it** (F44); no tag outside the vocabulary survives it (F28) |
| **second implementation** | **yes, two measured** — Qwen3-8B + mapper **0.482**, Claude by hand **0.575** |

**One generic algorithm — *prose + schema + vocabulary → filled sheet* — and zero Danbooru knowledge.**
That is what makes a photoreal flow possible without touching this layer at all.

**Invoked once per distinct (schema, vocabulary) pair** under L9, its result written to every flow that
shares one. Four Illustrious flows cost one call.

### ③ REVIEW — CORRECT

| | |
|---|---|
| **takes** | a sheet and its vocabulary |
| **returns** | **a new, approved sheet version** — never an edit in place (L12) |
| **may assume** | that it is the only writer of approved sheets |
| **must not break** | **saving is not approving** (L13); fields only (L9); the sheet on disk stays the source of truth |
| **second implementation** | **no — one, and this contract is a seam by assertion** |

**Stated honestly rather than dressed up.** There is one implementation and no dispatch, so the contract
is **invariants, not a registry** — inventing one here would be the dispatch mechanism with nothing to
dispatch that `../../CLAUDE.md` already rules against.

**Its substance is N41's four requirements, and each is a measured trap, not a preference:**

1. **Autocomplete shows the post count.** `narrow waist` (9,411) renders an *exaggerated* waist;
   `medium breasts` (770,389) renders ordinary. A picker offering them as equals walks the operator into
   that trap every time.
2. **A live token count against the 77-token CLIP window.** Sheets already run 80–122 estimated tokens
   and **nothing currently says so** — every one is silently chunked and averaged.
3. **The table is the only editable surface** — which L9 now guarantees structurally, since the prompt
   is not stored in a sheet at all.
4. **The sheet on disk is the source of truth.** Written on approve; never existing only in a browser.

**And it is the most valuable stage in the pipeline: 0.35** — the open route unreviewed delivers
**0.568** of the reviewed sheet's attributes through to the render; reviewed delivers **0.917** (F44).

### ④ GENERATE — DRAW

| | |
|---|---|
| **takes** | a photograph, the per-flow sheets, and a list of `Request(flow, count)` |
| **returns** | images with provenance — flow id, seed, sheet version, **graph digest** |
| **may assume** | that every sheet it is handed has been approved |
| **must not break** | **dials are never jittered** (L4); **teardown is `finally`** (L5); **assembly happens before the session opens** (L10) |
| **second implementation** | **yes — `A` and `D` today, seven more parked in the operator's ideas note** |

**A flow is a directory, not a file.** Manifest (declares, never computes — L8) + code (`assemble`,
`render`) + its own model manifest (L20).

```
  flows/<flow-id>/
    flow.yaml          requires · schema+vocabulary · dials · evaluation bar
    models.json        L20 — this flow's artifacts, pinned and digested
    <code>             assemble(sheet) -> prompt   ·   render(prompt, photo, seed) -> image
```

**Two operations, and the split is load-bearing.** `assemble` is **pure, local and free**; `render`
needs the session. Under L6 a run is a batch, so **assembling every prompt before the session opens
catches a malformed sheet for free rather than after $0.036 of boot** — and makes the whole of prompt
construction unit-testable offline, which is what keeps this suite green without a GPU.

**The graph digest in provenance is not bookkeeping.** Under L12 an output's path is
`outputs/<flow>/<sheet-version>/<seed>.png`, which uniquely identifies a configuration **only because L3
holds** — a flow id never silently changes behaviour. The digest is what *proves* it held rather than
assuming it.

### ⑤ EVALUATE — JUDGE

| | |
|---|---|
| **takes** | a **cohort**: photographs, their renders, and the ground-truth grouping |
| **returns** | per-image axes, and a **cohort-level identity result with its bracket** |
| **may assume** | that the cohort is complete before it is asked anything |
| **must not break** | **identity is refused below cohort size, never estimated** (L15); a withheld axis is **named**, never silently omitted (L16) |
| **second implementation** | **yes, two live at once** — `glintr100` and SFace, and **plurality is the measurement** |

**It is the proof, not a product feature** (Q5, amended):

```
  the PROOF     a synthetic cohort, published, reproducible by anyone who clones
  the PRODUCT   a photograph in, images out — no identity number is shown
  the PRIVATE   real cohorts — measured, never published (D14)
```

**The bracket travels with the number.** `glintr100` is the encoder InstantID optimises against, so
flow `A`'s figure is an upper bound; SFace, independent, gave **9/17** where `glintr100` gave **14/17**
on the same crops (F46). **Report `9/17 … 14/17`, never one encoder's figure.**

**And the question it asks is N-way identification, not similarity.** *"How similar is this render to its
photograph"* has no zero point across photograph→drawing and its optimum is a render that did not
stylize — the failure that made round 1's scoreboard a coin flip. *"Which of the N photographs did this
render come from"* is stylization-invariant, because every candidate is equally stylized.

---

## 3 · The vocabulary is a module, not a layer — L23

> **L23 · The vocabulary is a shared module. Layers import it; flows declare which one.**
> It is not a stage: it has no artifact, no place in the pipeline order, and no position in the run
> directory. **So importing it is not layer-to-layer coupling** — it is the same kind of dependency as
> `ciede2000.py`, and `isekai/labels.py` already reads a CSV with the stdlib, so it is stdlib-clean.

**Four things, one object:**

| | what | where it is today |
|---|---|---|
| the tag list | 8,106 canonical tags | `models/wd14/selected_tags.csv` |
| post counts | the strength-of-effect predictor | the same file |
| per-field enums | `gaze` = 20 values all beginning `looking` | **N40, uncurated** |
| phrase → field+tag | exact → suffix → curated → containment | `prototype/tagmap.py` |

**Why the vocabulary owns `tagmap` and the LLM layer does not.** The deciding test is which one it
outlives:

```
   swap Qwen → Claude              tagmap still needed    model changes, map survives
   swap Illustrious → photoreal    tagmap is useless      vocabulary changes, map dies
```

`blonde → blonde hair` is a fact about **Danbooru**, not about Qwen.

**Three layers need it and one famously does not.** ② fills from it, ③ autocompletes from its post
counts, ④ may validate against it at assembly. **⑤ does not** — and conflating them is a known trap:
`selected_tags.csv` and the WD14 *model* ship in one download and are different things. The file
answers *is this a real tag*; the model reads a **render** and emits tags, and it **cannot read
photographs** — 0.47 on photographs against 0.73 on renders, with `pose` at 0.08 and `marks` at 0.00
(F29).

**One honest caveat on the file itself.** `selected_tags.csv` is the set WD14 *predicts* — a subset of
Danbooru above some post threshold. `sheet.py` currently prints *"not a Danbooru tag"*, which
**overclaims**; the honest statement is *not in WD14's prediction set, and therefore probably too rare
for the base to have learnt*.

---

## 4 · The run directory — N44

**The only coupling the design permits**, so it is the thing most worth getting exactly right.

```
  runs/<photo-id>/
    run.json                        the frame — id, source digest, created, schema
    source.jpg                      THE PHOTOGRAPH ITSELF — a copy, never a pointer
    status.json                     in-flight progress ONLY · a hint · L11
    caption/001.json                ①
    sheets/<flow>/001.json          ② draft
                  002.json          ③ approved — highest number wins · L12
    prompts/<flow>/002.json         ④a assembled BEFORE the session · L10
    outputs/<flow>/002/<seed>.png   ④b
                      <seed>.json   provenance — flow, seed, sheet version, graph digest
    eval/<flow>/002/<seed>.json     ⑤ per-image axes
```

### What a photo-id is

**A content-hash prefix and a readable slug:** `a3f9c1_selfie_2` — the first six hex of the
photograph's sha256, then a sanitised filename stem.

**Each half earns its place.** The hash makes the id **stable and collision-free across uploads**: two
different photographs named `IMG_0042.jpg` get different directories, which a filename stem alone could
not do. The slug makes the directory **legible in `ls`**, which a bare hash could not do.

**And re-uploading the same photograph is a resume, not a duplicate.** Same bytes → same hash → same
directory → **L12's append-only rule takes over**, so the second upload continues the first run rather
than starting a parallel one. That is a property worth having deliberately rather than discovering.

**Six hex characters is 16.7M values**, and the full digest is in `run.json` regardless. If the corpus
ever grows to where a birthday collision is plausible, **lengthen the prefix** — the id is derived, so
nothing but directory names changes.

### Who creates it, and the sharpening that falls out

**The orchestrator creates the frame; a layer writes only its own file.** A layer that calls `mkdir` is
a layer that knows the layout.

> **So a layer is handed the path of its own artifact, never the run root.** That is stronger than a
> convention: a layer *cannot* read its neighbours' outputs, because it was never told where they are.
> **"No layer knows another exists" stops being a rule anyone has to follow.**

### Schema versions — per artifact, and a different axis from L12

**Two kinds of version, and conflating them would be the bug.**

| | what it numbers | mechanism |
|---|---|---|
| **L12's number** | **content** — draft 001, approved 002 | the filename |
| **`schema`** | **format** — what the keys mean | a field inside the artifact |

Every artifact carries `{"schema": {"name": ..., "version": N}, ...}`, and **a reader refuses an
unknown version rather than parsing it best-effort.** `Refusal` already exists in
`isekai/evaluate.py` and is exactly this. A best-effort parse of a format you do not know is how a run
produces numbers that look fine and mean nothing.

### The photograph is copied in, not pointed at

**L11 says the artifacts are the state, and a run that points at a file someone later moved is not
reconstructable from disk.** So `source.jpg` is a copy, and its digest in `run.json` is what proves the
copy is its original.

**The cost is honest and small:** N42's phone photographs are 10 MB for ten. N30's ran 21–28 MB *each*,
which is the case worth remembering — and that same size is what made 34 renders take 27 minutes against
the ~17 the GPU time predicted, because **the upload, not the GPU, dominated the session**. Any
downscaling is the generation layer's business, not the orchestrator's.

### Failure is recorded in place, and is not an artifact

Under **L14** a batch does not halt on one item. **A stage that fails writes `<stage>/<nnn>.error.json`
where its artifact would have gone.**

**An error file is a record, never a completion.** L11's resume rule reads *"find the first missing
artifact"*, and an error is not an artifact — so a retry simply writes the next number, and the failed
attempt stays. **That is L12 applied to failures**: the record of what went wrong survives the fix.

### A batch is a convenience, not state

**Under L6 a run is a batch spanning many photograph directories**, but each directory is independently
resumable, so **the batch list carries no state that the directories do not already hold.** Record it
for convenience — `batches/<timestamp>.json`, a list of photo-ids — and **lose it without consequence**,
exactly as `status.json` may be lost. If the batch file were load-bearing, L11 would be false.

### One thing N44 cannot settle

**Where a cohort-level result lives.** Under Q5-as-amended, identity is a **cohort** measurement and a
cohort spans many photograph directories — so `eval/<flow>/…` inside one directory can only ever hold
that image's own axes. **The cohort object is N46's question**, and it is the last structural unknown.

---

## 5 · The orchestrator — N45

### The order is code; the position is disk

**The five stages are hardcoded in sequence.** A dependency graph over five stages with exactly one
valid topological sort is a dispatch mechanism with nothing to dispatch — the shape `../../CLAUDE.md`
already rules against.

**Where a run *is*, though, is never held in memory.** Under **L11** the orchestrator reads the
directory and derives its position from what is present:

| stage | done when | cost of redoing it |
|---|---|---|
| ① VLM | `caption/<n>.json` exists | a local model call |
| ② LLM | `sheets/<flow>/<n>.json` exists | a local model call |
| ③ REVIEW | the highest sheet is **approved** | **a human** |
| ④a assemble | `prompts/<flow>/<n>.json` exists | free |
| ④b render | `outputs/<flow>/<n>/<seed>.png` exists | **money** |
| ⑤ evaluate | `eval/<flow>/<n>/<seed>.json` exists | free, local |

**Resume is therefore "find the first stage with neither an artifact nor a live error", and there is no
state machine to corrupt.** A crashed orchestrator, a closed laptop and a week-long pause are the same
event.

### L12, refined — the active artifact is the highest **approved** number

**The rule as first written was defective, and re-running a stage is what exposed it.** *"Highest number
wins"* means generating a fresh draft from a new caption would **silently demote a sheet the operator had
carefully reviewed** — the 0.35, lost to a numbering convention.

> **L12a · For an artifact with an approval concept, the active version is the highest *approved* one;
> a draft never becomes active by being written.** For artifacts with no such concept — captions,
> prompts, outputs — the highest number is active.

**This is what makes L13's *"saving is not approving"* mean something structurally** rather than being a
rule the UI is trusted to honour.

### The cascade is explicit, never automatic

**Re-running ① does not re-run ②, and re-running ② does not render anything.** Each stage is invoked;
none triggers its successor.

**The reason is money, and it is not hypothetical.** Under **L6** a run is a batch, so an automatic
cascade from *"swap the VLM on this photograph"* could reach twenty renders and a pod boot without
anyone asking for it. **That is P4's problem — the orchestrator does not know what it is spending —
arriving through the back door**, and an explicit cascade is the cheapest possible defence against it.

### Adding a flow to a photograph that already has outputs

```
   caption/001.json        REUSED — the caption is flow-neutral (L9)
   sheets/<new-flow>/001   GENERATED — stage ② runs for the new (schema, vocabulary)
   ★ REVIEW ★              REQUIRED — the operator's decision, 2026-09-13
   outputs/<new-flow>/…    rendered only for the flow that was added
```

**Nothing belonging to the existing flows is touched**, which is L12 doing exactly what it was written
for: a run is never finished, and adding a flow next week is an append rather than a migration.

### Re-running a stage with a different implementation

**It adds a version and invalidates nothing.** Swapping JoyCaption for Claude on one photograph writes
`caption/002.json` beside `001`; the sheets built from `001` remain valid, because **what they were
built from is recorded in their own provenance.**

> **This is the comparison harness, and it costs nothing extra.** It is not a feature that had to be
> designed — it is what **L12** plus per-artifact provenance already *is*. Every artifact records which
> implementation produced it, so *"did Claude's caption make a better sheet than JoyCaption's"* is
> answerable from the directory, by the evaluator, without a single new concept.
>
> **The feature on top of it is parked as P5**; the property is free and lives here.

### What the orchestrator must not know

- **Which implementation is configured** for any layer — it invokes a facade, and the facade selects.
- **What a flow does** — it reads the flow's manifest for *requirements* (L8) and never for behaviour.
- **Where any layer's neighbours wrote their files** — it hands each layer **the path of that layer's
  own artifact** (§4), which is what makes decoupling a property rather than a rule.

---

## 6 · The evaluation facade and the cohort — N46

### A cohort is a named, persistent set — not a batch

**A batch is transient (§4); a cohort must be citable and re-runnable.** The benchmark is the
repository's evidence that identity survives, so *"the photographs that happened to be in that run"*
cannot be what it rests on.

```
  cohorts/<name>/cohort.json      the set: photo-ids, source digests, ground-truth grouping
                                   e.g. synthetic-v1
```

**The grouping is part of the cohort, not of the evaluator.** N42 established why: the same-person
grouping is **held by a human and by nobody else** — an agent session that had written sixteen fields
for each of ten photographs still got it wrong, 3 of 4 (F47). A cohort without its grouping cannot ask
the verification question at all.

**Two kinds of cohort, and the split is Q5-as-amended:**

| | tracked? | why |
|---|---|---|
| `synthetic-v1` | **yes — published** | the proof, reproducible by anyone who clones |
| `phone-2026-09` · `real-n30` | **no — gitignored** | photographs of real people (D14) |

### Where a cohort-level result lives

**A sibling of `runs/`, because it spans many photograph directories:**

```
  benchmarks/<cohort>/<date>/
    report.md         the table, every subject, prose
    results.json      per-arm top-1, margins, p, full rankings
    manifest.json     digests of every photograph, every render, every model
    images/           DOWNSCALED jpegs for the README table
```

**Per-image axes stay where they are** — `runs/<photo-id>/eval/<flow>/<n>/<seed>.json` (§4). The
benchmark *references* them; it does not relocate them. **One artifact, one home.**

### The renders ship, and the size is managed rather than argued about

**The operator's requirement, 2026-09-13:** the public README carries a table of synthetic photographs,
their anime outputs and the evaluation — it is the portfolio.

**Git stores binary blobs permanently**, so the full-resolution renders must not go in. A hires render is
2112×1536 PNG; twenty of them is tens of megabytes, in the history of a repository whose whole point is
that people clone it.

> **Ship downscaled JPEGs; keep full-resolution renders gitignored; let the manifest's digests carry
> the proof.** N42's thirty thumbnails at 340px were **1.1 MB total**; at 768px — ample for a README
> table — a thirty-image cohort is a few megabytes. **The repository already distributes no model
> weights (L19); this is the same posture applied to renders.**

**Reproducibility does not depend on the shipped images.** `manifest.json` carries the digest of every
full-resolution render, every source photograph and every model — so a reader who re-runs the benchmark
can prove they got the same bytes, and the shipped JPEGs are an illustration rather than the evidence.

**Where the full-resolution renders live — a GitHub release asset, not a CDN.** The operator raised
hosting them externally, which would work; **release assets get the same result at lower cost.**

```
  git history      thumbnails only, a few MB     renders instantly, survives offline
  release asset    the full-resolution bundle    tied to the vX.Y.0 annotated tag,
                                                  outside git's object store
  manifest.json    digests of both               the proof travels with the repository
```

**Three costs a CDN carries and a release asset does not.** `../../CLAUDE.md` states that *everything a
run reads or writes is inside the repository* and that **no path outside the repo is resolved by
anything tracked here** — a CDN URL is precisely that path. **A digest proves bytes, not presence**, so
nothing in the manifest discipline protects a portfolio from a dead host two years on. And a bucket is
an account and a bill kept alive for a repository whose whole point is that it can be cloned.

**Release assets have none of those**: outside the object store so clones stay small, attached to the
tag this repository already cuts, and durable for as long as the repository is.

**DECIDED 2026-09-13: GitHub releases, no CDN.** Thumbnails in-repo so the README table renders on
GitHub without a fetch; the full-resolution bundle as a release asset. **The CDN option is closed
rather than left open** — it remains a one-field change if anything ever forces it, but nothing is
designed around it and no second host is kept alive on the strength of a maybe.

### The rule that makes it a benchmark rather than marketing — L24

> **L24 · The published table shows every subject in the cohort, including every failure.**
> If flow `A` scores 8 of 10, the table has **ten rows and two of them say so.**

**A portfolio that shows only its wins is not evidence, and this project has no standing to publish
one.** Its entire credibility rests on a findings file that is append-only and records being wrong —
where a superseded claim is struck through and kept, because *the record of being wrong is what makes
the record of being right worth anything.* **Selecting rows for a README would falsify that in the one
document most people would ever read.**

**And F47 is the worked example of why the rule pays.** Flow `A` scored 8/10 at the photograph level
and **10/10 at the person level**; the two "misses" had each ranked a *sibling photograph* of the
correct person first. **A table showing only the eight hits would have hidden the better result.**

### What the facade takes and returns

```
  evaluate(cohort, outputs) ──▶ per-image axes          attribute recall · pose PCK · style
                            ──▶ cohort identity         N-way top-1, margin, p — BRACKETED
                            ──▶ verification            sibling rank vs a permutation null
```

**The bracket is not optional.** `glintr100` is the encoder InstantID optimises against, so flow `A`'s
figure is an upper bound; SFace, independent, gave **9/17** where `glintr100` gave **14/17** on the same
crops (F46). **Under L3, plurality is the measurement for this layer** — the report carries
`9/17 … 14/17`, never one encoder's number.

**One control is owed and has never been run.** The sibling result partly inherits how tightly the
encoder clusters one person's photographs on its own. **Photograph→photograph sibling rank, with no
render involved,** separates the encoder's contribution from the pipeline's. It is free, needs no GPU,
and is recorded in F47's limits.

---

## 7 · Still to be written

| | |
|---|---|
| **N47** | [`MIGRATION.md`](MIGRATION.md) — what on `main` dies, survives, moves |
| **N48** | [`ROADMAP.md`](ROADMAP.md) — the versions, and every carried item dispositioned |
