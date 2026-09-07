# Findings

Newest at the bottom. One entry per thing learned. **Numbers, not impressions** — and where an
impression is all we have, it says so.

---

## F0 · The comparison set

Six baseline subjects from v0.12 (`inputs/baseline/`, digests in `baseline/README.md`) put through
Fotor's *AI Art Effects*.

| | |
|---|---|
| tool | Fotor, web, free trial |
| effect | **TODO — human to record the exact effect name** |
| date | 2026-09-07 |
| delivered | JPEG, 1968×2880, no watermark, ~2.4× upscaled from our 832×1216 input |
| have | `s1_control_blonde`, `s2_control_brunette` |
| missing | `s3`, `s4`, `s5`, `s6` |

**Fotor is non-deterministic and will change.** This is a dated snapshot, not a reproducible
baseline. Pixels are not committed; digests and the recipe are the record.

---

## F1 · The evaluator can score a foreign render — and refuses the face axes by design

`evaluate.py` takes a run directory and reads `run.json`. A foreign render has none, and
fabricating one would put a false `base` and meaningless `dials` into the record whose only job is
to say where a number came from. `prototype/external_eval.py` wires `score_render` by hand and
passes the generator as **unknown**.

That makes `refuse_embedding_axes_across_bases` fire on both face axes — *"an embedding is readable
only within one base"*. **The refusal is correct.** `--force-embeddings` suppresses it and tags the
output `EXPLORATORY`, because *"the axis refused"* and *"the axis refused and would have said X"*
are different amounts of information at prototype time.

## F2 · Every axis ranks us above Fotor. The eye ranks the reverse.

| axis | s1 isekai (5) | s1 Fotor | s2 isekai (5) | s2 Fotor |
|---|---|---|---|---|
| `face_styleid` * | 0.465 – 0.552 | **0.267** | 0.569 – 0.691 | **0.189** |
| `face_arcface` * | 0.448 – 0.486 | **0.127** | 0.432 – 0.608 | **0.130** |
| `hair_colour_delta_e` ↓ | 16.4 – 39.8 | **74.9** | 2.8 – 3.8 | **11.3** |
| `pose_pck` | 0.988 – 1.000 | 0.988 | 0.987 – 1.000 | 0.974 |
| guard IoU | 0.943 – 0.978 | **0.938** | — | **0.897** |

\* EXPLORATORY, see F1.

**A confident, unanimous, wrong answer** — worth more than a null. A noisy instrument says *collect
more data*; an inverted one says *you are measuring something else*, and lets you name it.

**Good news in the same table: the shared-mask trick survives cross-tool.** Guard IoU 0.938 / 0.897
against our own 0.943–0.978. Alignment was the risk most likely to void this comparison, and it is
dead.

## F3 · `hair_colour_delta_e` uses a statistic that is invalid on photographs

It takes the **mode** of a 32-level-per-channel RGB histogram under the hair mask.

| | winning bin | its L\* |
|---|---|---|
| the photograph | **1.21%** of 179,400 px (next four: 0.97, 0.87, 0.80, 0.78%) | **4.5** ← near-black, on blonde hair |
| Fotor (flat cel) | **9.89%** | 83.1 |
| isekai | 2.08% | 29.7 |

A photograph's hair is a continuous gradient, so no bin dominates and the "mode" is arbitrary — here
it landed on a shadow. Flat cel art has a *genuine* mode. **So the axis compares a noise bin against
a real one, and systematically penalises the more stylized image.** Means tell a different story:
photo **41.4**, isekai **43.3**, Fotor **62.1**.

The mode is valid on flat art and invalid on photographs — and the photograph is always the
reference side.

## F4 · The face axis rewards *not stylizing*

Our faces keep photographic proportions and shading; Fotor's are properly stylized. A face embedding
always prefers the less-stylized image, because the domain gap is smaller.

**Maximising `face_styleid` drives toward the input photograph.** The metric's optimum is not doing
the product.

This also re-reads v0.12's `face_styleid` = 0.450 (below chance) as **systematic disagreement**
rather than noise, which `baseline/correlation/README.md` flagged as *"worth more than it looks"*.

## F5 · Only one side of the trade-off is instrumented

Four axes all measure similarity-to-photograph. **Nothing measures style.** So a less-stylized render
wins by construction and nothing pushes back.

```
   identity ◀──────── the trade-off ────────▶ style
   4 axes                             NOTHING
```

And the corollary, which rules out the obvious fix: **identity preservation is not a similarity
measure.** Any single *how much did it keep* score is maximised by returning the original. The
product needs the output to be **different** (anime) and **the same** (her) at once, so no one number
holds both. The per-attribute metrics stay unaveraged; the holistic instrument is a judge.

## F6 · The eye's verdict and the axes' verdicts are not the same claim

The operator judges **holistically**. The axes are **per-attribute**. Fotor wins on accessories,
garment detail, background retention and being a good drawing — and **none of those is measured**.

The axes are not lying about their own narrow questions. Those questions do not add up to the
operator's. Any labelling done here must therefore be **per-axis** (*"which better preserves the hair
colour"*), not *"which is better"*.

---

## F7 · A style axis is buildable — and it takes **two** numbers, not one · T1 ✅

Calibrated on the three points whose order is not in dispute, before any tuning.

| | posterisation ↑ | linework ↑ |
|---|---|---|
| | *share of px in the 32 commonest colour bins* | *share of px on a strong luminance gradient* |
| **s1** photo | 0.2662 | 0.0299 |
| s1 isekai (5) | 0.2698 – 0.2885 | **0.0005 – 0.0051** |
| s1 **FOTOR** | **0.4599** | **0.0404** |
| **s2** photo | 0.2445 | 0.0161 |
| s2 isekai (5) | 0.2185 – 0.3189 | **0.0005 – 0.0015** |
| s2 **FOTOR** | **0.5413** | **0.0240** |

**Resampling is not the confound.** Fotor reaches the canvas by a downscale from 1968×2880 where ours
arrives natively. Sending the photograph down that same path moves every measure by **< 0.4%**
(`resampling_control`, built into the script so the objection is answered by a command).

**Two candidates tried and dropped**, recorded so they are not re-tried: `flat_fraction` orders the
three correctly but **conflates cel flatness with blur** — both score high, for opposite reasons;
`unique_ratio` does not order them at all.

### The finding underneath the finding: **isekai is not under-stylized. It is off-axis.**

```
   linework ▲
            │  FOTOR ●            flat cel: posterised AND drawn
     0.04   │
            │
     0.03   │  photo ●            photographic: graduated, textured
            │
     0.02   │
            │
     0.01   │
            │
     0.00   │  isekai ●           neither: as graduated as a photograph,
            └──────────────────▶   with the lines wiped off
              0.25       0.50
                 posterisation
```

- **posterisation**: isekai ≈ **the photograph** (0.270 vs 0.266). Its colour distribution is as
  continuous as a photo's. It is not flattening at all. Fotor is **1.7–2.2×** higher.
- **linework**: isekai is **below the photograph** — 0.0005 vs 0.0299, a **60×** deficit, and it holds
  at every gradient threshold from 8 to 64. Fotor is *above* the photograph (0.0404 vs 0.0299).

So the render is not sitting between photograph and anime. **It is softer than the photograph and no
flatter.** "Semi-realistic" was generous: it is a *blurred* photograph-like image, and blur is a
failure mode neither endpoint has.

### What this predicts for the pod session

Two independent deficits, so probably two different levers:

| deficit | lever to test |
|---|---|
| **no linework** | lineart CN 0.2 → 0.6 — the only leg that draws edges. Currently near-off |
| **no posterisation** | the register: `realistic, photorealistic` restored to the negative, and the flat-anime register generally. Possibly `denoise` |

**And a free acceptance test for the tuning:** a candidate dial set has to move isekai *up and right*
on that plot. Both numbers are computable on a laptop the moment a render lands, with no labels and
no judge — so the pod session has an objective readout for the first time, on the axis the project
never had.

---

<!-- next: F8 from T3 (pod session 1) -->
