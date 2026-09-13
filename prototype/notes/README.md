# Notes — the reasoning, separated from the code

**Created 2026-09-10; sixteen documents as of 2026-09-13.** They hold *why*, kept apart from the scripts
that hold *how*.
`../README.md` stays at the prototype's root as its index; everything below is the substance it points at.

They divide into three kinds, and the kind decides how to read one:

```
  SHAPE       ARCHITECTURE.md                what the whole pipeline is, end to end
  METHOD      IDENTITY.md · CRITERIA.md      how a thing is measured, and why that way
  REFERENCE   ILLUSTRIOUS.md · READER.md     what the base was trained on; who can
                                             read a photograph into a sheet
  PLAN        JOYCAPTION.md                  what we were about to do, and the bar
                                             stated before we did it
  DESIGN      PRODUCT.md                     the engineered shape: facades, seams,
                                             contracts
              MIGRATION.md                   what on `main` dies, survives, moves
              ROADMAP.md                     the versions, in order, and every
                                             carried item dispositioned
              OPEN.md · PARKED.md            what had to be settled first, and what
                                             was deferred instead
  RECORD      FINDINGS.md · CONFIGURATION.md       what happened, and where the work stands
              ROUTER.md                      how prose becomes a sheet, measured
```

| note | what it is | read it when |
|---|---|---|
| **[`ARCHITECTURE.md`](ARCHITECTURE.md)** | **the whole pipeline in four stages** — abstract, then the open stack, then the closed one, then where each stage's ceiling is | you want the shape of the thing, or are deciding what to build next |
| **[`ROUTER.md`](ROUTER.md)** | prose → criteria sheet with an open model: the four configurations, why the enum grammar was not the answer, and what the mapper actually does | you are changing stage ② or judging an open router |
| **[`CONFIGURATION.md`](CONFIGURATION.md)** | the state of the work at the close of round 4 — the settled dials, rounds 1–3's laws | after `GRILLING.md`; **no longer the entry point** |
| **[`IDENTITY.md`](IDENTITY.md)** | **how we know the anime image is the same person.** The method, its proof, its limits, and the two traps that produced a confident wrong answer first | you need to trust, reproduce or export the identity number |
| **[`CRITERIA.md`](CRITERIA.md)** | the criteria sheet: the fifteen fields, the seven scored ones, and why the sheet rather than the photograph is the ground truth | you are editing a sheet or the evaluator |
| **[`ILLUSTRIOUS.md`](ILLUSTRIOUS.md)** | what Illustrious was trained on — caption schema, quality ladder, skin tags, and WAI v17's own published settings | you are about to change a prompt |
| **[`READER.md`](READER.md)** | the open candidates for reading a photograph into a criteria sheet — licences, sizes, and the numbers each has to beat | you are replacing the agent session at step one |
| **[`JOYCAPTION.md`](JOYCAPTION.md)** | the plan for trialling JoyCaption as the photograph reader — artifacts, hosting, two phases, and the bar written before the run. **§9 carries the amendments the run produced, including the licence** | before running the trial, or to judge its result honestly |
| **[`PRODUCT.md`](PRODUCT.md)** | **the engineered shape** — the five facades and their contracts, stated in what each takes, returns, may assume and must not break, plus the vocabulary module. Cites the law behind every decision | you are building a layer, or arguing with where a seam went |
| **[`MIGRATION.md`](MIGRATION.md)** | **what on `main` dies, survives and moves** — the inventory behind L18, scenario by scenario, with the four things that must change rather than move | you are cutting the change that replaces the old flow |
| **[`GRILLING.md`](GRILLING.md)** | **the entry point — read first in a fresh thread.** Round 5's state in one page, the 24 laws consolidated, **where the design is thinnest**, and what may and may not be relitigated | **always, before anything else** |
| **[`ROADMAP.md`](ROADMAP.md)** | **the versions, in order** — v0.13 to v0.18, what each delivers and leaves broken, and **every carried item from four rounds dispositioned** | you are deciding what to build next, or cutting a change |
| **[`OPEN.md`](OPEN.md)** | **round 5's open questions, worked one at a time.** Each closes into a decision with its evidence and the laws it creates. **The gate on `PRODUCT.md`, `MIGRATION.md` and `ROADMAP.md`** | you are about to write, or argue with, any part of the product architecture |
| **[`PARKED.md`](PARKED.md)** | what round 5 raised and will not answer — research to run, prototypes to spike, optimisations found but not taken. Each entry states what it is, why it was parked, what would make it worth doing, and what it would change | something looks unaddressed and you want to know whether it was missed or deferred |
| **[`FINDINGS.md`](FINDINGS.md)** | **F0–F47, the full evidence**, newest at the bottom, append-only | you want the measurement behind a claim |

**`IDENTITY.md` is written to be exported.** It states its reasoning from the beginning rather than
assuming the rest of this directory, and its last section generalises the method away from this pipeline.
The others assume their neighbours.

**A finding is never edited to match a later result.** `FINDINGS.md` is append-only; when a finding is
corrected, the correction is a new entry that names the old one — F34 correcting F32's malformed arm is
the worked example. A superseded claim is struck through and kept, never deleted, because the record of
being wrong is what makes the record of being right worth anything.
