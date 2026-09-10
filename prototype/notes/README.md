# Notes — the reasoning, separated from the code

**Created 2026-09-10.** Five documents that hold *why*, kept apart from the scripts that hold *how*.
`../README.md` stays at the prototype's root as its index; everything below is the substance it points at.

They divide into three kinds, and the kind decides how to read one:

```
  METHOD      IDENTITY.md · CRITERIA.md      how a thing is measured, and why that way
  REFERENCE   ILLUSTRIOUS.md                 what the base model was trained on
  RECORD      FINDINGS.md · HANDOFF.md       what happened, and where the work stands
```

| note | what it is | read it when |
|---|---|---|
| **[`HANDOFF.md`](HANDOFF.md)** | the state of the work — the settled configuration, the laws, what is open | **first, in a fresh thread** |
| **[`IDENTITY.md`](IDENTITY.md)** | **how we know the anime image is the same person.** The method, its proof, its limits, and the two traps that produced a confident wrong answer first | you need to trust, reproduce or export the identity number |
| **[`CRITERIA.md`](CRITERIA.md)** | the criteria sheet: the fifteen fields, the seven scored ones, and why the sheet rather than the photograph is the ground truth | you are editing a sheet or the evaluator |
| **[`ILLUSTRIOUS.md`](ILLUSTRIOUS.md)** | what Illustrious was trained on — caption schema, quality ladder, skin tags, and WAI v17's own published settings | you are about to change a prompt |
| **[`FINDINGS.md`](FINDINGS.md)** | F1–F37, the full evidence, newest at the bottom | you want the measurement behind a claim |

**`IDENTITY.md` is written to be exported.** It states its reasoning from the beginning rather than
assuming the rest of this directory, and its last section generalises the method away from this pipeline.
The others assume their neighbours.

**A finding is never edited to match a later result.** `FINDINGS.md` is append-only; when a finding is
corrected, the correction is a new entry that names the old one — F34 correcting F32's malformed arm is
the worked example. A superseded claim is struck through and kept, never deleted, because the record of
being wrong is what makes the record of being right worth anything.
