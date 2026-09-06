# The correlation — v0.12's actual product

**This table is what v0.12 ships.** Not the scores: the answer to whether any of them tracks the
operator's eye.

Forty blind pairwise judgements, recorded and committed **before any score for these renders existed**
— `correlate` confirmed that against git before it would read them — correlated against each axis
**separately, never rolled up**, with the count of judgements printed beside every figure.

## The result

| axis | kind | agreement | agreed / used | 95% CI | binomial *p* |
|---|---|---:|---:|---|---:|
| `face_styleid` | relative | **0.450** | 18 / 40 | 0.295 – 0.605 | 0.636 |
| `face_arcface` | relative, falsify-only | **0.625** | 25 / 40 | 0.470 – 0.780 | 0.154 |
| `pose_pck` | absolute | **0.286** | 4 / 14 | 0.024 – 0.548 | 0.180 |
| `hair_colour_delta_e` | absolute | **0.425** | 17 / 40 | 0.270 – 0.580 | 0.430 |
| `hair_mask_area` | absolute | **undefined** | 0 / 40 | — | — |

*Agreement* is the fraction of pairs where the axis ranked the same render higher than the operator
did. **0.5 is a coin flip.** Higher is agreement; **lower than 0.5 is systematic disagreement**, which
is not the same as noise and is worth more than it looks.

## What this says

**No axis is shown to track the operator's eye. Every 95% confidence interval contains 0.5, and every
*p* is far above any threshold anyone would accept.** At n=40 the interval is roughly ±0.155 wide, so
this experiment could only have detected a very strong effect — and it did not find one.

Read individually:

- **`face_styleid`, the primary face axis, lands at 0.450 — below a coin flip.** This is the headline.
  StyleID separates *different people* well enough (AUC 0.847 in phase 8's probe), and it still cannot
  say which of two renders **of the same person** looks more like them. Those are different questions,
  and this version is what established that the second one is the hard one.
- **`face_arcface` is the highest at 0.625, and it is the axis allowed to claim the least.** It is the
  encoder the generator injects identity with, marked falsify-only for exactly that reason, and *p* =
  0.154 does not license reading it as a result. If it survives replication at a real n it would be a
  genuinely awkward finding — that the contaminated sanity channel beats the purpose-built metric — and
  it is recorded here so that a later version can go looking.
- **`hair_colour_delta_e` at 0.425** is below chance. The metric returns one dominant colour and two of
  the four labelled subjects have two-tone hair, which is the limitation `design.md` D5 named in
  advance and put those subjects in the batch to catch.
- **`pose_pck` is undefined in practice.** Phase 8 found it saturated — PCK median 1.000 across all
  thirty renders — so 26 of the 40 pairs are exact metric ties and only 14 could be scored at all. The
  0.286 over those 14 is noise from a rounding difference, not a measurement.
- **`hair_mask_area` cannot participate by construction, and that is a design defect this table
  exposes.** The axis reports how much of the canvas the photograph's hair mask covers — context for
  the colour distance rather than a comparison — so it is *identical for every render of a subject* and
  every within-subject pair is a tie. It should not have been listed as a correlatable axis. It is left
  in the table rather than quietly dropped, because it is the table that revealed the mistake.

## Per subject

Ten pairs each, so **these are anecdotes, not measurements**, and are shown only because a difference
between subjects is the kind of thing a later version should look for.

| axis | control blonde | control brunette | multitone balayage | multitone bob |
|---|---:|---:|---:|---:|
| `face_styleid` | 0.50 | 0.40 | 0.30 | 0.60 |
| `face_arcface` | 0.60 | 0.60 | 0.40 | 0.90 |
| `hair_colour_delta_e` | 0.60 | 0.20 | 0.30 | 0.60 |

The multi-tone subjects are not obviously worse than the controls on the hair axis, which is not what
D5 predicted. At ten pairs apiece, that is not evidence of anything either.

## This is a successful version

`design.md` D17, written before any of this ran: **the release criterion is that the correlation was
computed, never that it was good.** It was computed. It says the instrument does not work yet.

That is worth what it cost. The whole purpose of building the evaluator *before* using it was to avoid
tuning a pipeline against a number that turns out to be noise — and had v0.13 opened by searching
`cn_strength` against `face_styleid`, it would have been optimising against a coin flip, at real money,
and the result would have looked plausible. **This version cost ~$0.24 and prevented that.**

## The operator's own tendency

24 of the 40 choices were `b`, 16 were `a`, and there were no ties. The sheet randomised which render
of each pair was shown as `a`, so a 24/16 split is unremarkable at this n — but it is recorded because
a *strong* side bias would have been a defect in the labelling rather than a finding about the metrics.

## What would make this answerable

Not more axes. **More judgements, and renders that differ more.** At fixed dials the five renders of a
subject differ only in their sampler seed, and the operator was frequently choosing between two images
that are genuinely close — which compresses the signal any metric could have. A version that wants a
real answer needs pairs drawn across a *dial sweep*, where the renders differ by construction, and it
needs an n where ±0.05 is resolvable rather than ±0.155.
