# Inputs — what round 3 reads, and how to choose more

**Created 2026-09-10.** Two pools, and the split is not filing — it is what the images are *for*.

```
  prototype/inputs/
    real/        photographs of real people   — the case the product exists for
    synthetic/   generated portraits          — the held-out set (N29)
```

**This directory is not the only input tree, and that is deliberate.** Round 2's ten portraits and six
baseline subjects stay where they are:

| set | where | status |
|---|---|---|
| round 2's ten portraits | `inputs/synthetic/` (repo root) | **tuned on** — every dial in the graph was chosen against these |
| round 2's six baselines | `inputs/baseline/` (repo root) | **tuned on** — the style axis was calibrated here |
| **round 3's ten portraits** | `prototype/inputs/synthetic/` | **held out** — the flow has never seen them |
| **the real photographs** | `prototype/inputs/real/` | the case the product exists for |

A single directory holding both would make the tuned-on / held-out boundary invisible at exactly the
moment it matters. N29's whole value is that it asks *did two rounds of dials generalise, or were they
fitted to ten faces* — and that question cannot be asked once the two sets are mixed.

---

## Everything here is gitignored

Both pools, always. Real photographs are covered by `design.md` **D14**; the generated ones are large and
reproducible from `synthetic_portraits`. **This README is the one tracked file** — see `.gitignore`, which
ignores the *contents* rather than the directory so that the negation can work.

**A criteria sheet is the same kind of artifact as the photograph it describes.** `prototype/sheets/real/`
is gitignored as a directory for the same reason. If you add a subject, its sheet goes there and nowhere
else.

---

## Choosing real photographs

Public photographs are fine for private testing, and two rules make the question go away rather than
leaving it small.

**1 · Take them from model-released stock, not from a search engine.** Unsplash and Pexels photographs
carry a signed release from the subject covering commercial use. Same effort as a search, and it removes
the question instead of arguing about it. This matters more here than for most projects because
**InstantID computes a face embedding** — biometric data under GDPR Art. 9 — and *"the output was never
published"* does not change the fact that the processing happened. The pods run in EU-RO-1.

**2 · Never use a celebrity.** This is a *methodological* trap before it is anything else. Illustrious and
SDXL have famous faces memorised in the prior, so a celebrity photograph renders a recognisable face
**with or without InstantID** — which makes flow `A` and flow `D` indistinguishable, and those two flows
are the entire comparison N25 and N27 exist to make. A celebrity in the set does not merely add noise; it
produces a confident wrong answer.

**3 · Prefer two or three photographs of the same person over one each of three people.** It is the only
way to ask whether the flow renders *this* person rather than *a* person — the question N14 says nothing
in this project has ever measured. The real set had exactly one such case (the same subject with different
hair colour across two photographs, **F36**) and it was the most informative input the prototype has had.

---

## What makes a good test photograph here

**Realness is not the axis. Coverage of the hard cases is.** Each row below is a failure mode this project
has already found, with what the current set can and cannot say about it.

| axis | why it is hard | coverage today |
|---|---|---|
| **small face in frame** | InstantID's worst case. If the face degrades and nothing else does, that is a **resolution floor on identity**, and it binds every full-body render the product ever makes | one subject (`00059`) |
| **skin tone range** | the tag vocabulary is narrow and misleading — `pale skin` means *bleached*, not fair (**F15**), and getting it wrong was one of F36's three defects | two tones |
| **occlusion — hands near the face** | InsightFace and DWPose disagree about what a hand over a jaw is | never tested |
| **non-frontal gaze and turned head** | `pose` is the reader's weakest field on **both** real and synthetic input (0.57 / 0.58), which points at a vocabulary limit rather than a reading limit | mostly frontal |
| **the same person, twice** | the only way to separate *this person* from *a person* | **thin — down to one subject** |
| **hair that changes between photographs** | the case no synthetic posed, and the one that exposed the `messy hair` overshoot | one pair, now broken |

A set of six chosen against this table is worth more than twenty chosen for being photographs.

---

## `real_photo_2` was withdrawn

The operator deleted it on **2026-09-10**. What that means for anyone reading a finding:

- **Its renders and its sheet stay on disk.** F36 was measured on all three subjects, and deleting them
  would make a recorded finding unreproducible.
- **It is out of `real_photo.py`'s `SUBJECTS`**, so nothing tries to read a photograph that is gone. The
  runner now builds 8 arms across 2 subjects rather than 12 across 3.
- **The id is not reused.** A later subject numbered `real_photo_2` would silently inherit its render
  directories and be compared against the wrong face. Number the next one `real_photo_4`.
- Two 2026-09-09 contact sheets each show one broken image where its photograph was. That is left as it
  is: regenerating them would drop the row and lose the record of a run that included it.
