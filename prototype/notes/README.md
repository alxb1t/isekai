# Notes — the reasoning, separated from the code

**Created 2026-09-10; ten documents as of 2026-09-12.** They hold *why*, kept apart from the scripts
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
  RECORD      FINDINGS.md · HANDOFF.md       what happened, and where the work stands
              ROUTER.md                      how prose becomes a sheet, measured
```

| note | what it is | read it when |
|---|---|---|
| **[`ARCHITECTURE.md`](ARCHITECTURE.md)** | **the whole pipeline in four stages** — abstract, then the open stack, then the closed one, then where each stage's ceiling is | you want the shape of the thing, or are deciding what to build next |
| **[`ROUTER.md`](ROUTER.md)** | prose → criteria sheet with an open model: the four configurations, why the enum grammar was not the answer, and what the mapper actually does | you are changing stage ② or judging an open router |
| **[`HANDOFF.md`](HANDOFF.md)** | the state of the work — the settled configuration, the laws, what is open | **first, in a fresh thread** |
| **[`IDENTITY.md`](IDENTITY.md)** | **how we know the anime image is the same person.** The method, its proof, its limits, and the two traps that produced a confident wrong answer first | you need to trust, reproduce or export the identity number |
| **[`CRITERIA.md`](CRITERIA.md)** | the criteria sheet: the fifteen fields, the seven scored ones, and why the sheet rather than the photograph is the ground truth | you are editing a sheet or the evaluator |
| **[`ILLUSTRIOUS.md`](ILLUSTRIOUS.md)** | what Illustrious was trained on — caption schema, quality ladder, skin tags, and WAI v17's own published settings | you are about to change a prompt |
| **[`READER.md`](READER.md)** | the open candidates for reading a photograph into a criteria sheet — licences, sizes, and the numbers each has to beat | you are replacing the agent session at step one |
| **[`JOYCAPTION.md`](JOYCAPTION.md)** | the plan for trialling JoyCaption as the photograph reader — artifacts, hosting, two phases, and the bar written before the run. **§9 carries the amendments the run produced, including the licence** | before running the trial, or to judge its result honestly |
| **[`FINDINGS.md`](FINDINGS.md)** | F1–F46, the full evidence, newest at the bottom | you want the measurement behind a claim |

**`IDENTITY.md` is written to be exported.** It states its reasoning from the beginning rather than
assuming the rest of this directory, and its last section generalises the method away from this pipeline.
The others assume their neighbours.

**A finding is never edited to match a later result.** `FINDINGS.md` is append-only; when a finding is
corrected, the correction is a new entry that names the old one — F34 correcting F32's malformed arm is
the worked example. A superseded claim is struck through and kept, never deleted, because the record of
being wrong is what makes the record of being right worth anything.
