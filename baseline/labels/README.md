# The blind pairwise labelling pass

**Forty judgements, made by eye, before any score for these renders exists.**

`sheet.csv` carries forty within-subject pairs — four labelled subjects × ten pairs each — and **no
metric value of any kind**. There is no column a score could sit in, and a test asserts that the
`Pair` type has no field one could be written into: a sheet that *could* carry a score is one
revision away from carrying one.

## Why it is shaped this way

- **Pairwise**, because "is A or B more like them?" is stable where a 1–5 rating drifts across a
  sitting.
- **Within-subject**, because "does subject 1's render preserve identity more than subject 4's" is a
  question with no meaning. Every pair draws both renders from one subject.
- **Order and sides randomised** from a seeded RNG, so the sheet is reproducible from the recipe and a
  systematic preference for the left-hand column is not confounded with a preference for
  lower-numbered renders.
- **`s5` and `s6` are absent.** They are the refusal-path subjects; a subject whose axes are expected
  to refuse cannot calibrate anything.

## How to fill it in

Put `a`, `b`, or `tie` in the `choice` column of every row — **forty rows, none blank**. The question
for each row is only:

> Which of these two renders looks more like the person in the photograph?

`tie` is allowed on purpose. Forcing a preference the operator does not have manufactures a signal
rather than measuring one, and ties are excluded from the agreement figures rather than scored as a
half.

A row left blank is **refused**, not skipped: a correlation computed over "the rows that happened to
parse" reports a count that does not match the sheet, and at forty judgements the count is exactly
what a reader discounts the figure by.

## What proves this was blind

**Git ordering, and nothing else.** This sheet is committed before any score for these renders is
computed, and the filled sheet is committed in **its own commit** that touches no score file.
`correlate` asks git when each path first appeared and **refuses** to correlate unless the labels
demonstrably came first — including the case where labels and scores arrive in the same commit, which
cannot show which came first.

A timestamp written inside the sheet would be authored by the same person being checked, and a promise
from the person being checked is not a check.

## The consequence, accepted rather than hidden

**A single holistic label cannot attribute a disagreement to one axis.** The operator's felt sense of
identity is holistic, and forcing it through a face crop would measure something they do not care
about. So if face and hair correlate differently against the same label, that difference is itself a
finding rather than a defect in the labelling.

## Re-running the sheet is forbidden after scores are seen

`tasks.md` states it and it is repeated here because it is the one rule no code can enforce:
**re-running the labelling after seeing the scores is forbidden.** The release criterion is that the
correlation was *computed*, never that it was good.
