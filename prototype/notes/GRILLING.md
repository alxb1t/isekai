# GRILLING — the briefing for a fresh thread

**Written 2026-09-13 at the close of round 5, for a thread that has none of this context.**
**Read this first. It is the only file that assumes nothing.**

---

## 1 · What this session is for

The prototype is finished. Four rounds and **F0–F46**, 19 pod sessions, ≈$3.17 — plus **F47** and one
more session from round 5 itself, for ≈$3.30 across 20. A pipeline that
takes a photograph and returns an anime image of the same person — **measured, on studio photographs,
on held-out synthetic portraits, and on phone snapshots.**

**Round 5 turned that into a design.** Eleven open questions were settled, **twenty-four laws plus one
refinement (L12a)** were
written, and five notes were produced. **None of it has been attacked yet**, and that is what this
session is.

> **The job: find what round 5 got wrong, assumed, or forgot — before a change is cut against it.**
> Everything below is a claim. **Design decisions are fair game. Measurements are not** — §7 draws
> that line precisely.

**What the session must produce**, in the operator's own terms: well-defined documentation of the
architecture; each module's solution; **the API of each layer and each module**; **error-state
handling**; **resumption handling**; the **data flow with diagrams**; and the **roadmap**. Documentation
a human reads and an agent can build from.

**And then, separately:** a second grilling session scoped to **v0.13 alone**, whose output is a cut
change under `openspec/changes/0013-<slug>/` and a build.

---

## 2 · Reading order

| | file | what it is |
|---|---|---|
| 0 | **this file** | the briefing — state, laws, and where to press |
| 1 | [`OPEN.md`](OPEN.md) | **the eleven questions and how each was settled**, with the evidence. L1–L22 are defined here |
| 2 | [`PRODUCT.md`](PRODUCT.md) | **the engineered shape** — the five facade contracts, the run directory, the orchestrator, the cohort. L12a, L23, L24 are defined here |
| 3 | [`MIGRATION.md`](MIGRATION.md) | what on `main` dies, survives, moves — 152 scenarios inventoried |
| 4 | [`ROADMAP.md`](ROADMAP.md) | v0.13 → v0.19, and **every carried item from four rounds dispositioned** |
| 5 | [`PARKED.md`](PARKED.md) | P1–P8 — what was raised and deliberately deferred, each with why |
| 6 | [`FINDINGS.md`](FINDINGS.md) | **F0–F47, append-only.** The evidence behind every number quoted anywhere |
| 7 | [`IDENTITY.md`](IDENTITY.md) | how identity is measured, and the two traps that gave a confident wrong answer first |
| 8 | [`ARCHITECTURE.md`](ARCHITECTURE.md) · [`CRITERIA.md`](CRITERIA.md) · [`ILLUSTRIOUS.md`](ILLUSTRIOUS.md) · [`ROUTER.md`](ROUTER.md) · [`JOYCAPTION.md`](JOYCAPTION.md) · [`READER.md`](READER.md) · [`CONFIGURATION.md`](CONFIGURATION.md) | the measured record from rounds 1–4 |

**And one file outside this directory binds everything:** [`../../CLAUDE.md`](../../CLAUDE.md) — the
repository's own contract. **Where it and these notes disagree, say so loudly**; §6 lists the two places
they deliberately do.

### Two documents are stale in a way that will mislead you

- **[`ARCHITECTURE.md`](ARCHITECTURE.md) says "four stages" and calls layer ④ "DIFFUSION".** Round 5
  made it **five layers** and renamed ④ to **GENERATION** (L3's registry; the grade path performs no
  redraw at all). **The note was deliberately not edited** — it is the *measured* shape, every box cited
  to a finding, and editing evidence to match a later design is what this repository forbids.
  **`PRODUCT.md` is the current shape.**
- **`HANDOFF.md` no longer exists.** It claimed to be the entry point and its §6c briefed round 4.
  **Pruned and retitled [`CONFIGURATION.md`](CONFIGURATION.md) on 2026-09-13** — the briefing half was
  deleted, the half nothing else carried was kept: **the settled dials with the finding behind each,
  the bars, the determinism floors, and the infrastructure traps.** Under **L8** that table is what
  v0.13's first flow manifest is built from.

---

## 3 · The state, in one page

```
   CLI  convert.py photo.jpg          UI  upload · monitor · review · trigger
   stdlib, on the guarded graph           off the graph — free to need wheels
        │                                          │
        └──────────────────┬───────────────────────┘          L1 · L2
                           ▼
                     ORCHESTRATOR              order is CODE · position is DISK
      ┌────────┬───────────┼───────────┬────────────┐
      ▼        ▼           ▼           ▼            ▼
   ① VLM    ② LLM     ③ REVIEW   ④ GENERATE    ⑤ EVALUATE
    see      sort      correct       draw          judge
    prose    sheet     approve     flows A,D      cohort
      │        │           │           │             │
      └────────┴─────┬─────┴───────────┴─────────────┘
                     ▼
              runs/<photo-id>/     append-only · numbered · the ONLY coupling
```

**The product** is a photograph in, **many anime images out** — one per selected flow, optionally several
seeds each — with a **human review step in the middle** worth a measured **0.35**.

**What is proven, with the finding that proves it:**

| claim | number | where |
|---|---|---|
| identity survives, held-out synthetic | 8/10 at chance 10% | **F40** |
| identity survives, 17 real photographs | 14/17 at chance 5.9% | **F41** |
| identity survives an encoder we did not train against | 9/17, p≈0.0000 | **F46** |
| **identity survives phone snapshots** | **8/10 at chance 10%** | **F47** |
| **the number measures a PERSON, not a photograph** | **10/10 person-level, p=0.0000** | **F47** |
| the review step is worth | 0.568 → **0.917** | **F44** |
| flow `D` carries no identity — **the control** | 2/10 vs 2.6 expected, p=0.22 | **F47** |

---

## 4 · The twenty-four laws and one refinement, consolidated

**They are split across two files and this is the only complete index.** L1–L22 are defined in
[`OPEN.md`](OPEN.md); **L12a, L23 and L24** in [`PRODUCT.md`](PRODUCT.md).

| | law | from |
|---|---|---|
| **L1** | a facade admits a wheel-needing implementation only through the `eval_backends` posture | Q1 |
| **L2** | the import-graph rule is **directional** — a front end may import the orchestrator, never the reverse | Q1 |
| **L3** | one pipeline; each layer is a facade with a selector; **a selectable implementation is a measured one** | Q2 |
| **L4** | a variation draws a new seed and changes **no dial** | Q2 |
| **L5** | the generation facade is session-scoped; **teardown is control flow, not discipline** | Q3 |
| **L6** | a run is a **batch** | Q3 |
| **L7** | the generation layer depends on an **endpoint**, never on a provider | Q3 |
| **L8** | a flow **declares and does not instruct** — inputs, schema+vocabulary, dials, bar | Q10 |
| **L9** | **one sheet per flow**; a sheet stores fields only, never the assembled prompt | Q10 |
| **L10** | prompt assembly belongs to the flow, **runs before the session**, writes an artifact | Q10 |
| **L11** | **the artifacts are the state**; `status.json` is a hint and is never read to decide | Q4 |
| **L12** | every stage's output is **append-only and numbered** | Q4 |
| **L12a** | the active version is the highest **approved** one — a draft never becomes active by being written | N45 |
| **L13** | a reviewed sheet is never overwritten without force; **saving is not approving** | Q4 |
| **L14** | a batch does not halt on one failure; **⑤ is its own pass** | Q4 |
| **L15** | identity is a **cohort** measurement — below cohort size it is refused, never estimated | Q5 |
| **L16** | per-image evaluation reports every axis it can, **with identity named as withheld** | Q5 |
| **L17** | **one capability per layer** — the living spec goes 6 → ~9 | Q6 |
| **L18** | the old flow is **deleted, not deprecated** | Q6 |
| **L19** | the repository is Apache-2.0, public, and **distributes no model weights** — a manifest points | Q7 |
| **L20** | a manifest belongs to an **implementation**, not a layer | Q8 |
| **L21** | every manifest is re-derivable byte-identically, by **one** shared deriver | Q8 |
| **L22** | every model is pinned to a revision and a digest — **no exception for a hosted runtime** | Q8 |
| **L23** | **the vocabulary is a shared module**, not a layer — layers import it, flows declare which one | N43 |
| **L24** | the published table shows **every subject, including every failure** | N46 |

---

## 5 · Where to press — eight places round 5 is thinnest

**Ranked by how much damage a wrong answer does. These are volunteered, not extracted.**

1. **v0.13 may be more than one change can hold.** It carries the run directory, the orchestrator, three
   layers, the living-spec restructure 6→9, **and** the deletion of the old flow. `../../CLAUDE.md`
   binds one version to one branch, not one change — **splitting it is legitimate and unexplored.**

2. **Atomic writes are not specified, and L11 depends on them.** *"The artifact exists"* means *"the
   stage is done"* — but **a crash mid-write leaves a truncated file that exists.** Resume would then
   skip a stage that never finished. **Nothing in round 5 says write-to-temp-then-rename.** This is a
   real hole in the design, found while writing this briefing and not yet fixed anywhere.

3. **Resume has never been exercised.** L11–L14 were reasoned, not tested. **L12a was a defect found by
   accident** — *"highest number wins"* would have silently demoted a reviewed sheet. **If one law in
   that group was wrong, press on the rest.**

4. **The Claude integration at ①② in v0.13 is unspecified.** Batching, prompt caching, retries, rate
   limits and failure modes are all absent. `ARCHITECTURE.md` §4 has *cost* numbers ($0.0026/photo with
   caching and Batch) and **no integration design at all.**

5. **The cohort object is new, thin, and has no precedent.** `cohorts/<name>/cohort.json` was invented in
   N46 with no scenario, no test and nothing on `main` resembling it — unlike the run directory, which
   at least echoes `outputs/<subject>/`.

6. **A schema bump can only refuse; migration is unaddressed.** Artifacts carry `{"schema": {...}}` and a
   reader refuses an unknown version. **What happens to existing runs when a schema changes is not
   written anywhere.**

7. **The verification bar is unstated.** P6 is scheduled at v0.16, but **what sibling mean rank counts as
   a pass was never declared**. This repository's own discipline is that a bar is stated *before* the
   run — F47's 2.75 is a result, not a threshold.

8. **No version owns spend awareness, and v0.15 is where money starts being spent.** P4 is parked by
   decision, but v0.15 introduces `session()` and batch. **An unwritten limit is what produced three
   orphaned pods and ~$0.26 of unwatched billing in round 3.**

**One inconsistency was found and fixed during this audit, and it is worth knowing the shape of.**
`ROUTER.md` §1 and `ARCHITECTURE.md` §4 both labelled **0.568** as the *closed* stack's rendered score.
It is `3_booru` — **the open pipeline unreviewed** — and it is the same 0.568 that is the floor of
**the 0.35**. **The number was right and its label was wrong**, which is the dangerous kind: nothing
about the review layer's justification changes, but a table said the closed stack had been measured
where it never was. **Both lines now carry the correction rather than a silent edit.**

**Two more worth a question each:** what happens when a flow's manifest is **invalid** or names a
vocabulary that does not exist (unaddressed); and what the published benchmark does when a flow
**regresses** — L24 says publish every failure, but says nothing about publishing a *decline*.

---

## 5b · Round 5 has already been wrong three times — press accordingly

**Volunteered, because a reader who knows the failure rate presses harder than one who assumes
competence.** None of these was caught by review; each was caught by accident, days or hours later.

| what was claimed | what was true | how it was caught |
|---|---|---|
| **L12** — *"the highest number is active"* | it would have **silently demoted a reviewed sheet** — the 0.35, lost to a numbering convention | answering an unrelated question about re-running a stage (**→ L12a**) |
| **"EXIF orientation is unhandled"** — recorded as a defect in Q9 | `isekai/workflow.py:315` **already transposes, for both codecs** | reading the file for a different reason. **It was asserted from a function's return signature without reading its body** |
| **0.568 labelled the closed stack's score** in `ROUTER.md` §1 and `ARCHITECTURE.md` §4 | it is `3_booru` — **the open pipeline unreviewed**, and the floor of the 0.35 | a consistency audit run at the operator's request, **after** round 5 was declared complete |

**The pattern across all three: a claim was made from something adjacent to the evidence** — a
signature, a table cell, a plausible rule — **rather than from the evidence.** The corrections are
recorded in place rather than silently applied, which is the only reason the third was findable.

> **So the useful question is not "is this right" but "what is this claim actually resting on".**
> Every number in these notes traces to a finding; **every design decision traces to an argument in
> [`OPEN.md`](OPEN.md), and arguments are what you are here to break.**

---

## 6 · Where these notes deliberately contradict `../../CLAUDE.md`

**Both are amendments a change must actually make. Neither is an oversight.**

1. **"There is one path… it may not add a second"** → replaced by **L3**. The generation layer is a
   registry of flows. **The rule's purpose is preserved and arguably strengthened**: the original
   existed because four selectable models were carried and three were dead, and L3's entry gate — *a
   prototype round, then the evaluation bar* — makes a dead implementation impossible by construction.
2. **"the whole required surface is `convert.py photo.jpg`"** → still true, but Q1 shape **B** adds
   per-stage subcommands and a second front end (the UI). **`convert.py`'s stdlib-only import graph is
   untouched**, because L2 makes the rule directional.

**Unchanged and binding:** the five-command gate; **never weaken the gate to pass**; state lives on
disk; deps minimal and human-gated; the metered-phase protocol and the 60 min / $0.75 ceiling; never
commit a secret or a real absolute path.

---

## 7 · What may be relitigated, and what may not

**Fair game — every design decision in round 5.** All 24 laws and L12a, the run directory layout, the roadmap
order, the v0.13 scope, the facade boundaries, the cohort object. **None of it has been built or
tested.**

**Not fair game — the measurements.** `FINDINGS.md` is **append-only**; a superseded claim is struck
through and kept, because *the record of being wrong is what makes the record of being right worth
anything.* **A finding is never edited to match a later result.** Challenge what a number *means*;
do not rewrite the number.

**Four measured facts that bound any redesign:**

- **F24** — taking the photograph out of the latent is what removed the blur. **img2img is dead here.**
- **F28/F43** — canonical booru tags work, invented ones do nothing, and **an invented *canonical* tag
  does something wrong** and passes validation on its way to the prompt.
- **F44** — **an absence clause is a presence instruction.** CLIP has no negation; the router is the
  seam where absence dies.
- **F45** — **the prompt's job is style; the legs' job is identity.** A bad sheet degrades attributes,
  not likeness.

**And one whole avenue is closed:** **prose as a render prompt.** 0.675 and 0.510 against a reviewed
sheet's 0.917. **The register is the problem, not the wording — do not retry it with better prose.**

---

## 8 · Housekeeping a fresh thread needs

- **The working tree is uncommitted.** Round 5's five notes, F47, three new prototype scripts
  (`same_person.py`, `phone_report.py`, and edits to `face_likeness.py` / `sheet.py`) are all unstaged.
- **`prototype/` has never been gate-clean on this branch** — 109 pre-existing lint errors in
  `archive/` and `style_axis.py`, none of them touched by round 5. `isekai/` + `tests/` + `convert.py`
  are clean and **434 tests pass**.
- **No pod is running.** The RunPod account was MCP-confirmed empty at the close of N42's session.
- **This branch never merges.** Every line reaches a release by being restated inside a change.
