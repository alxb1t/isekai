# Criteria sheets

**Split by what the sheet depicts, 2026-09-10:**

```
  sheets/
    synthetic/   ten portraits of people who do not exist  — TRACKED
    real/        three photographs of one real person      — GITIGNORED (D14)
```

The split is a **privacy boundary, not filing**. `.gitignore` names the *directory* rather than a name
glob, because the glob it replaced (`<name>_*.md`) would have stopped matching the moment the files moved
and failed silently and open — a real person's transcription becoming committable with nothing saying so.
A sheet added to `real/` is ignored by virtue of where it is.

`prototype/paths.py`'s **`sheet_path(sid)`** finds a sheet in whichever pool holds it, so no caller names
a pool: a subject id already says which one it is in.

## The ten synthetic portraits

One sheet per subject, transcribed by eye on **2026-09-08** against the thirteen-field schema in
[`../CRITERIA.md`](../CRITERIA.md) §2, and **reviewed by the operator the same day**.

These are the **ground truth** for round 2. `CRITERIA.md` §1 relocated it here from the photograph, which
means every number the evaluator produces inherits whatever this transcription got wrong.

**Each sheet carries its own negative prompt.** Nine declare the shipped one, which keeps them comparable
to round 1's baselines; `00059` drops `nsfw`, and says so beside the text. The runner reads whichever the
sheet declares, so that change is per subject and visible rather than global and silent.

| subject | framing | why it is in the set |
|---|---|---|
| [`00003`](synthetic/00003.md) | upper body | **freckles** — the clearest `marks` case |
| [`00004`](synthetic/00004.md) | headshot | the only close-up; tests whether framing carries at all |
| [`00014`](synthetic/00014.md) | upper body | **silhouette** — an asymmetric deep-part bob, and thick brows |
| [`00022`](synthetic/00022.md) | upper body | the control: plain backdrop, no accessories |
| [`00033`](synthetic/00033.md) | upper body | **age band**, and an asymmetric arm pose |
| [`00035`](synthetic/00035.md) | full body | a hard seated pose, knees up and foreshortened |
| [`00050`](synthetic/00050.md) | full body | **phenotype**, and the hardest pose in the set |
| [`00059`](synthetic/00059.md) | full body | **the small face** — the hardest case InstantID has; `nsfw` dropped |
| [`00060`](synthetic/00060.md) | full body | held back — a near-duplicate of 00059 in wardrobe and register |
| [`00072`](synthetic/00072.md) | upper body | **eye colour**, and the densest accessories |

## The six, if one session is all round 2 gets

**00003 · 00014 · 00033 · 00050 · 00059 · 00072.** Between them: three framings, five hair silhouettes,
three phenotypes, the freckles, the densest accessories, the age-band case, three hard poses — and one
**small face**, which asks a question none of the others can.

`00059` is the only subject whose head is a small fraction of the frame. If her face degrades and no
other does, that is a **resolution floor on identity** rather than a verdict on from-noise, and it would
bind every full-body render the product ever makes. Her `nsfw`-free negative makes her style numbers
incomparable to the other five; her verdict is read on the face.

`00060` is held back as the near-duplicate. If a seventh render is ever wanted, it is the cheapest one.

## The three real photographs

`real/real_photo_{1,2,3}.md`, from `outputs/original/real_photo/`. **Written 2026-09-09, gitignored, and
never tracked** — a transcription of a real person's appearance is the same kind of artifact as their
photograph, and D14 covers both.

They are the harder set and the more informative one. **F36: three transcription defects on the first
pass produced three visible render failures, and fixing the *sheet* fixed all three with no dial
touched.** They also contain a case no synthetic subject posed — **the same subject with different hair
colour** across two photographs.

**The subject's own name is nowhere in this repository.** The sheets, the renders, the drafts and the
source directory were all renamed to `real_photo*` on 2026-09-10. The one place it survives is
`openspec/changes/archive/0010-illustrious-base/`, which is an archived change — the record of a released
version, and not something to rewrite.
