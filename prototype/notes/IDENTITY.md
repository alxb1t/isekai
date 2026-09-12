# How we measure whether the anime image is the same person

**The methodology, written 2026-09-10 against its first run.** This note is meant to survive export out
of the prototype, so it states the reasoning from the beginning rather than assuming the surrounding
findings. Where it cites one — `F4`, `F29` — that is provenance, not a prerequisite.

---

## 1 · The question, and why two obvious answers are wrong

The product is *photo of a person → anime image of that same person*. **A beautiful anime image of
someone else is a failed run.** So the one number the project most needs is: **did the identity
transfer?**

Two scoreboards were built before this one. Both were internally complete and both answered a different
question than the one asked.

**Attempt 1 — measure similarity to the photograph.** Embed the photo's face, embed the render's face,
report the cosine. The failure is structural, not a tuning problem:

```
  cosine(photo, render)  falls monotonically as stylization rises
        │
        └─▶ its maximum is a render that did not stylize at all
            i.e. the metric's ideal output is the input photograph
```

Anything optimised against it drifts toward photorealism. This is `F4`, and `F16` is the same disease on
the colour axes: a distance to a photograph **punishes correct stylization**.

**Attempt 2 — measure adherence to a written description.** Transcribe the photo into a criteria sheet
(hair colour, eye colour, clothes, marks…), then read the render with a tagger and score recall against
the sheet. Better — it is stylization-invariant, because it compares tags to tags. But it is blind to
identity by construction:

> Two different people can satisfy every attribute on the sheet. `blonde hair, green eyes, freckles,
> camisole` describes thousands of people.

The proof that this is not theoretical: on that scoreboard the flow that **never reads the photograph**
scored *higher* than the flow that does — 0.77 to 0.73 (`F29`). It was not wrong; it was measuring
description-adherence, and the description-only flow is better at description-adherence. It simply could
not see the axis that separates them.

**So: nothing had ever measured *is this the same person* in a way that survives stylization.**

---

## 2 · The reframe

Do not ask **"how similar is this render to its photograph?"** — an absolute score, and stylization
poisons it.

Ask instead:

> ### Given this render, which of the N photographs did it come from?

```
  render of subject 00003
        │
        ├─▶ cosine against photo 00003   +0.2550   ← correct
        ├─▶ cosine against photo 00059   +0.1986
        ├─▶ cosine against photo 00072   +0.1540
        ├─▶ cosine against photo 00033   …
        ├─▶ cosine against photo 00014   …
        └─▶ cosine against photo 00050   …
                                                    rank of correct = 1  → a hit
                                          chance = 1/6 = 16.7%
```

**Why this repairs the flaw.** Every candidate in the comparison is *equally stylized* — they are all the
same render, judged against six different photographs. A metric that merely punishes stylization pushes
all six numbers down **and leaves the ordering untouched.** Only something that actually responds to
identity can reorder them.

Three further properties, each of which the pairwise score lacked:

| property | why it matters |
|---|---|
| **the answer is known in advance** | the instrument is falsifiable *before* it is trusted. This project's first evaluator was built before the thing it judged and came back a coin flip (`F1`) |
| **chance has a stated floor** | 1/N. Written down before any number is seen, so "better than nothing" cannot be decided after the fact |
| **it compares flows fairly** | if a flow's renders cannot be matched above chance, that is what the flow trades away — as a number, not an opinion |

---

## 3 · The machinery

```
  photo  ─┐
          ├─▶ ① one canvas ─▶ ② find face box ─▶ ③ crop → 112×112 ─▶ ④ embed
  render ─┘      resize          detector             normalise         512-d vector
                                                                             │
                        ┌────────────────────────────────────────────────────┘
                        ▼
          ⑤ cosine of one render against ALL N photographs → rank
                        │
                        ▼
          ⑥ top-1 · margin · exact binomial p
```

**① One canvas.** Every image is resized to a single working canvas before anything reads it. Both style
axes in this project are resolution-sensitive, and reading high-resolution renders at native size once
flipped a measurement's *sign* (`F35`). A render is embedded **once**, at the canvas it was rendered for,
so its vector cannot depend on which photograph it is later compared against.

**② Find the face.** A face-detection model returns the highest-confidence box. We use an anime-trained
detector, and the surprise is that it also works on photographs — but that was **checked before it was
relied on**, not assumed. See §6.

**③ Crop and standardise.** The box is cropped and resized to 112×112, then scaled to [−1, 1]. This is
the input format the recognizer was trained on; feeding it anything else silently produces numbers that
look fine and mean nothing.

**④ Embed.** An ArcFace-family face recognizer (`glintr100`) turns the crop into **512 numbers**. It was
trained with a loss that pulls two images *of the same person* together and pushes *different people*
apart. That training objective is the entire reason this works: the vector encodes facial identity, not
appearance in general.

**⑤ Compare by direction.** Cosine similarity — the angle between two vectors, ignoring their length.
**Length must be divided out explicitly**; see the trap in §7, which is not optional.

**⑥ Score the ranking.** Two numbers, because one is not enough:

- **top-1** — how often the correct photograph ranks first. The headline. Chance is 1/N.
- **margin** — the correct photograph's cosine *minus the best wrong one's*, averaged over subjects.
  This catches what top-1 hides. A flow can score above chance on hit-count while its margin is
  **negative** — meaning that on average the wrong photograph scores higher. No hit-count rescues that.
- **p** — the exact one-sided binomial tail: the probability of getting at least this many hits by pure
  guessing. Computed exactly rather than approximated, because at small N a normal approximation is its
  own overclaim.

---

## 4 · What it found

**First run: 6 subjects × 5 arms = 30 renders, against 6 photographs. Chance 16.7%, stated first.**

Two flows were compared. `A` reads the photograph (a face embedding plus a pose skeleton drive the
render). `D` never reads it — it renders from the written criteria sheet alone.

| arm | flow | top-1 | margin | p | verdict |
|---|---|---:|---:|---:|---|
| no hires | **A** | 4/6 | +0.0180 | 0.0087 | identity present |
| hires 0.35 | **A** | **5/6** | **+0.0485** | **0.0007** | identity present |
| hires 0.50 | **A** | 4/6 | +0.0273 | 0.0087 | identity present |
| no hires | **D** | 2/6 | **−0.0625** | 0.2632 | indistinguishable from guessing |
| hires 0.35 | **D** | 2/6 | **−0.0472** | 0.2632 | indistinguishable from guessing |

### The comparison across other photographs, in full

This is the part worth reading in detail, because the table above is a summary of it. Each row is one
render ranked against all six photographs.

**Flow `A`, hires 0.35** — the correct photograph's cosine, against the best wrong one:

| subject | rank of correct | correct | best wrong | |
|---|:-:|---:|---:|---|
| `00003` | **1** | +0.2550 | +0.1986 | comfortable |
| `00014` | **1** | +0.2368 | +0.2271 | **won by 0.0097** — a real hit, and a thin one |
| `00033` | **1** | +0.3031 | +0.0707 | the clearest in the set |
| `00050` | 2 | +0.1066 | +0.2129 | **missed** — another subject's photo scored higher |
| `00059` | **1** | +0.1769 | +0.1591 | thin |
| `00072` | **1** | +0.2352 | +0.1540 | comfortable |

**Flow `D`, hires 0.35** — the same six renders' worth of work, with the photograph never read:

| subject | rank of correct | correct | best wrong |
|---|:-:|---:|---:|
| `00003` | 4 | **−0.0553** | +0.0837 |
| `00014` | 3 | **−0.0080** | +0.0398 |
| `00033` | **1** | +0.1143 | +0.0230 |
| `00050` | 5 | **−0.0935** | +0.0851 |
| `00059` | 3 | +0.0098 | +0.0717 |
| `00072` | **1** | +0.1634 | +0.1107 |

**Three of `D`'s six correct-cosines are negative** — the render is not merely unlike its source
photograph, it is *actively pointing away from it*. That is a stronger statement than the 2/6 hit count,
and it is why margin is reported beside top-1.

### The reading

**`A` carries identity.** Four to five of six against a 1-in-6 chance, with a positive margin in every
arm, at p between 0.0087 and 0.0007.

**`D` does not, and that is by design rather than a defect.** `D` exists to render the strongest anime
style from a written description; it was never given the photograph. The value of measuring it is that
"less identity" stops being a claim and becomes a number — and that the two scoreboards now tell a
coherent story instead of contradicting each other:

| | attribute adherence | face likeness |
|---|---:|---:|
| `A` | 0.73 | **identity present** |
| `D` | **0.77** | guessing |

`D` matches the *description* better and the *person* not at all. Both numbers are correct; they measure
different axes.

**A secondary finding, free:** the high-resolution second pass does not cost identity — the best arm in
the whole table is `A` + hires 0.35. That is one subject of difference at N=6 and must not be
over-read, but the direction contradicts the worry that a second sampler pass washes the face out.

---

## 5 · The crucial detail: absolute similarity is low, and only order survives

```
  same person, two photographs       cosine ≈ 0.4 – 0.7    ← what this recognizer normally does
  photograph → its own anime render  cosine ≈ 0.10 – 0.30  ← ours
  photograph → a different person's  cosine ≈ 0.07 – 0.21
```

**Read as an absolute score, 0.25 is a poor match and the honest conclusion would be "identity was
lost."** That conclusion would be wrong, and it is precisely the conclusion attempt 1 reached.

The domain gap is real — a drawing is not a photograph and the recognizer knows it — and it compresses
every score toward zero. What survives is the **ordering**. The signal is thin (`00014` won by 0.0097)
but it points the right way across subjects, and consistency across subjects is what the p-value
measures.

> **This is the load-bearing idea of the whole method. Never read the absolute cosine as a grade. It is
> only ever a ranking key.**

---

## 6 · What this does and does not establish

**Establishes:** the render carries enough of the person's facial signature that a recognizer picks the
correct photograph out of N, far more often than chance. That is strong evidence of identity
preservation, and it is stylization-invariant in a way no earlier measurement was.

**Four limits, each of which bounds a specific claim:**

**Circularity, and it is not symmetric.** The recognizer used here is the same family the identity
adapter injects with — the flow was optimised *against this loss*. So a high score for `A` is partly the
adapter being marked by its own examiner.

- **`D`'s result is clean.** `D` never touches the encoder, so `D`'s failure is real evidence.
- **`A`'s result is an upper bound.** `A − D` is the *most* the identity adapter could be worth, not an
  estimate of what it is worth.
- **~~Removing this needs a second, independent recognizer~~ — done 2026-09-12, F46.** It needed one and
  it now has one. **SFace** (OpenCV Zoo, Apache-2.0, pinned in `../styles/sface_models.json`): a
  different architecture, corpus and loss, and a 128-d embedding against `glintr100`'s 512-d. On F41's
  seventeen real subjects, **both encoders reading the same crops**:

  | encoder | top-1 | chance | mean margin | p |
  |---|---:|---:|---:|---:|
  | `glintr100` — entangled | 14/17 | 5.9% | +0.1172 | 0.0000 |
  | **SFace — independent** | **9/17** | 5.9% | **+0.0072** | 0.0000 |

  **Identity survives independent examination**, p ≈ 0.0000 — so `A` is no longer self-graded. **And the
  inflation was real and is almost entirely in the margin**: 1.6x on hits, **16.3x on margin**. That is
  what "upper bound" meant, now quantified rather than suspected.

  **The replacement caveat, smaller and one-directional.** SFace runs **unaligned** — it expects a
  5-point landmark-aligned crop and gets a bounding box — so **9/17 is a lower bound** as surely as 14/17
  is an upper one. Preprocessing and crop margin were both ruled out first; `glintr100` on the identical
  crops ranks the known-answer pair 1 of 136 where SFace ranks it 2, which is what exonerates the crop
  and indicts alignment. **Read independent identity as bracketed, `9/17 … 14/17`, not pinned.**

- **The obvious candidate was disqualified, and still is.** The other face encoder already pinned here is
  a CLIP image encoder with a style LoRA merged, and its own documentation records that *"its training
  pairs were stylized with InstantID and IP-Adapter — this exact generator family."* It is **more**
  entangled than `glintr100`, not less.

**Small N.** Six subjects. Every p-value is exact rather than approximated, but 5/6 versus 4/6 is one
subject and is not significant on its own. Only the flow-level `A` vs `D` separation is.

**It measures the face, and identity is more than a face.** Hair silhouette, body proportion and marks
are part of "the same person" and none of them is in this number. **Pose is now covered** — see §10,
added 2026-09-10 — and the attribute scoreboard covers some of the rest.

**~~Generated faces only.~~ Answered 2026-09-11 (F41).** The method was run on **seventeen photographs
of real people** at chance 1/17 = 5.9%: **14/17, margin +0.1172**. The margin held at its held-out level
against a floor nearly twice as hard, and the three misses were all explicable — one subject in
sunglasses, two at full-body framing where the face is a small fraction of frame. **The small-face limit
has now reproduced in three independent sets and should be treated as a property of the flow.**

What is still untested is the product's *actual* input: every photograph in that set was professionally
shot. A phone snapshot is a different thing.

**~~Tuned-on subjects.~~ Answered 2026-09-10 (F40).** The method was re-run on ten portraits no dial was
chosen against, at chance 1/10 rather than 1/6: **8/10 with a mean margin of +0.1170**, against 5/6 and
+0.0485 on the tuned-on set. The result strengthened on harder data. Photographs of *real* people remain
untested.

**A confound that only appears on a demographically diverse set, and it inflates the weaker flow.** In
F40 the description-only flow scored 4/10 at p = 0.0128 — significant on hit count — while its mean
margin stayed *negative*. The four it matched were the subjects whose written description was most
distinctive in the set: the only red-haired one, the only man, the two with distinctive short black hair.
**It was being matched back by demographic attributes, not by face.** On a set of six similar young women
the same flow scored 2/6, which is noise.

> **N-way identification assumes the N candidates are otherwise interchangeable.** They never quite are,
> and the more diverse the set the less they are. The negative margin is what exposes it — another case
> where reporting top-1 alone would have produced a confident wrong answer.

---

## 7 · Two traps, both of which produced a confident wrong answer first

**The recognizer's output is not unit-length, whatever the docstring says.** The first execution reported
"cosine" margins of **±21** — impossible, since a cosine lives in [−1, 1]. Cause: the ONNX head emits raw
features at L2 ≈ 16–18, and the code was taking a plain dot product, which ranks by vector **magnitude**
as much as by direction. **The tell was a number outside its own possible range, not a wrong-looking
result** — had the magnitudes happened to be near 1, this would have shipped silently. Always divide by
both norms; always sanity-check that a bounded quantity is inside its bounds.

**A detector that returns 200 OK is not a detector that works.** The face detector here is trained on
drawings, and it was about to be pointed at photographs. Rather than assume, the run has a **gate that
gets its floor stated in advance** — every image must yield a face, because an arm scored on four of six
renders is not comparable to one scored on six — and the gate runs *before* any identification number is
computed. It passed at 36/36. Had it failed, the finding would have been "no open detector crosses the
domain gap", which is a real answer rather than a wasted step.

---

## 8 · Running it

```bash
# detection gate only — no identification number is computed
PYTHONPATH=. uv run --extra eval python prototype/face_likeness.py --gate

# the full run
PYTHONPATH=. uv run --extra eval python prototype/face_likeness.py
```

**Cost: nothing.** Every model is pinned and byte-verified locally, and it runs on CPU. No GPU, no
network, no pod.

Each run writes a **self-contained directory** — `prototype/evaluations/<UTC date>/<run name>/`:

```
  photos/         copies of the source photographs
  renders/<arm>/  copies of every render scored
  manifest.json   the source path and sha256 of all 36 copies
  detection.json  the face box found in each image, or why none was
  results.json    per-subject rankings, cosines, and the arm summaries
  report.md       the finding, in prose
```

**Copies rather than references, deliberately.** A results file that points into a working tree stops
being readable the moment that tree is reorganised. The manifest's digests keep *"is this still the
render that finding was measured on"* answerable years later. The cost is bulk — about 90 MB for 36
images — and it is not committed to git.

---

## 9 · If you are exporting this

The method is not specific to this pipeline, this base model, or anime. It applies wherever a generator
transforms an image of a person into a different visual domain and someone needs to know whether it is
still the same person. What you need:

1. **N source images**, one per identity, N ≥ 6 so chance is low enough to see through.
2. **A face detector that works in both domains** — verify this first, with a stated floor.
3. **A face recognizer** whose training objective is identity, not appearance.
4. **The discipline of ranking, not scoring** — §2 and §5 are the method; everything else is plumbing.
5. **A recognizer the generator was not optimised against**, if you want the number to be more than an
   upper bound. See §6.

The scripts referenced here (`prototype/face_likeness.py`) carry the same reasoning in their docstrings,
so the code and this note do not need to be kept in sync by hand — they cite the same section numbers.


---

## 10 · The second layer: pose geometry

**Added 2026-09-10, and it is a different instrument for a different question.** §1–§7 measure the
*face*; this measures whether the body stands the way the photograph's did. It needs no ranking trick,
because keypoint coordinates are geometric rather than appearance-based — a skeleton is a skeleton
whether it was drawn or photographed, so there is no domain gap to see through.

**Two measures, and each is a trap without the other.**

```
  PCK          fraction of keypoints landing within 5% of the person box's
               diagonal of where the photograph put them
               → describes PLACEMENT

  joint angle  elbow · shoulder · knee · hip, mean absolute error in degrees
               → describes CONFIGURATION
```

**Why not PCK alone.** An anime figure has different proportions — longer legs, smaller head — so a
*perfect* pose match still displaces every keypoint. A position score therefore penalises correct
stylization, which is F4's disease in a new place. Joint angles are proportion-invariant: longer legs
held the same way have the same knee angle.

**Why not angles alone.** A body can be correctly *configured* and in entirely the wrong place. The
proof is in the data rather than in the argument: on `sitting_on_knees`, the prompt-only flow scored the
**best joint-angle error of any arm (9.3°) at a PCK of 0.000**. Nothing landed where it should. Reading
angles alone would have called that the winner.

> **Angles say what the body is doing. PCK says where it is. Report both, and be suspicious of any
> subject where they disagree — that disagreement is usually the finding.**

**The shoulder angle is measured against the hip**, not against the neck, so "arm raised" and "arm
hanging" sit 180° apart rather than a few degrees. That choice is what made the `arms_up` failure
legible as 124° rather than as a modest error.

**Keypoints below 0.3 confidence are dropped and the drop is counted.** A guess scored is noise reported
as a measurement. Self-occluding poses — someone sitting cross-legged on the floor — drop the most, and
that is the instrument being honest about its own limit rather than the render being bad.

**Run it:**

```bash
PYTHONPATH=. uv run --extra eval python prototype/pose_geometry.py
```

**F38 is the first result**, and it carries the methodological point worth exporting with the method:
the operator's verdict was recorded *before* the instrument ran, the instrument agreed on five of six
subjects, and on the sixth the operator reviewed the per-joint detail and **changed his mind**. An
instrument that can correct the eye is only worth having if the eye's expectation was written down
first.