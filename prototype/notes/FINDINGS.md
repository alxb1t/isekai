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

## F8 · The hair statistic: the mode is indicted, the mean is the diagnostic · T2 ✅

Known-answer test on s1's hair — shift the photograph's own pixels by an amount we chose, ask each
candidate what it sees. No labels needed.

| case | mode | mean | median | cluster2 | want |
|---|---:|---:|---:|---:|---|
| identical | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| L +15 | 16.37 | 14.64 | 14.76 | 12.53 | ~15 |
| L −15 | **8.39** | 11.63 | 12.24 | 15.16 | ~15 |
| b +15 | **20.40** | 6.61 | 6.91 | 7.13 | small |
| **posterised (cel-shaded)** | **26.80** | 0.51 | 9.15 | 3.34 | true shift **0.51** |
| *reported hair L\** | **4.3** | 40.8 | 41.0 | 55.5 | blonde |

**The posterisation row is the whole Fotor penalty, reproduced on our own photograph.** Cel-shading it
moves the actual colour by **0.51** and moves the mode by **26.80**. That is a 50× overstatement, and
it is what F2's `hair_colour_delta_e` = 74.9 was mostly made of.

**An honesty note that changed the conclusion.** The first version of this test added the mean
difference back after quantising, so the case was "colour kept" *by construction* — which made `mean`
score zero by definition. Circular. It was rerun without the correction and the true shift is now
printed beside the candidates. **So this test indicts the mode; it does not select its replacement.**

**The selection rests on the other rows**: the mode under-reports L−15 by half (8.39 for a shift of
15), over-reports b+15 by 3× (20.40 against ~6.6 for everything else), and describes blonde hair as
**L\* 4.3**. The mean tracks every known shift within ~1–3 and reports a plausible L\* 40.8.

**Use the mean as the prototype diagnostic.** With its limitation stated: a mean of a dark base and a
bright underlayer is a colour that appears nowhere in the image, so it is a good *comparison* and a
poor *description*. It is not blind to the case that objection is about — dropping the underlayer
entirely registers ΔE 6.2–15.5 across the three subjects tested, all far above the 2.3 JND.

**`cluster2` is the right long-term shape and is not ready.** Returning only the larger of two
centres is unstable — it caught the underlayer drop at 22.3 and 12.7 on the multi-tone subjects and
missed it at 3.2 on s1. A real version reports **both centres and their shares**, which is what the
multi-tone subjects were put in the baseline to force.

---

## F9 · The style is reachable with dials — and the register was doing denoise's job · T3 ✅

**Pod `4i9yfjciuhse7a`, ~30 min, ~$0.36, 13 renders across four rounds, one seed throughout.**
Subject `s4_multitone_bob` for rounds 1–3, then three more subjects to test generalisation.

### Round 1 said none of the obvious levers works

| variant | posterise | linework | hair ΔE |
|---|---:|---:|---:|
| photo | 0.6371 | 0.0049 | 0.00 |
| 1_control (shipped dials) | 0.4956 | 0.0023 | 7.01 |
| 2_negative *(+realistic, photorealistic)* | 0.4648 | **0.0061** | 11.62 |
| 3_lineart *(0.2→0.6)* | 0.5191 | 0.0014 | 7.54 |
| 4_tile *(0.2→0.9)* | 0.5858 | **0.0002** | 9.35 |
| 5_denoise *(0.65→0.45)* | 0.5946 | 0.0011 | 3.63 |
| FOTOR | **0.8379** | **0.0255** | 6.36 |

Two surprises. **Lineart at 0.6 made linework *worse*** (0.0014 vs 0.0023) — raising MistoLine does not
add lines. **Tile at 0.9 crushed it to 0.0002** — tile is a *de-stylizing* force, pulling toward the
photograph's own smooth structure. The card's recommendation is wrong for this product.

### Round 2: the lever I had not tested was the **positive** prompt

The ladder varied the negative, the legs and denoise. It never touched the positive — which carried
`soft lighting` (literally asking for soft) and the quality ladder, which on Illustrious pulls toward
heavy painterly rendering. Replacing it with Danbooru's own vocabulary for the target —
`flat color, cel shading, thick outlines` — plus tile **off**, lineart 0.6, negative restored, denoise
0.8, gave `9_combo`: **linework 0.0105**, 4.5× the control and the flattest thing this project has
made. **It is unmistakably cel.** And hair ΔE went to **23.73** — the identity was gone.

### Round 3: sweeping denoise under the flat register found the frontier — and it is not where it was

| flat register, tile 0, lineart 0.6 | posterise | linework | hair ΔE |
|---|---:|---:|---:|
| denoise 0.45 | **0.6322** | **0.0051** | **2.34** |
| denoise 0.55 | 0.5938 | 0.0044 | 7.76 |
| denoise 0.65 | 0.5087 | 0.0044 | 14.94 |
| denoise 0.80 *(9_combo)* | 0.4582 | 0.0105 | 23.73 |

**denoise 0.45 with the flat register is the best render this project has produced**, on every axis at
once: posterisation matching the photograph's, linework above it, and hair ΔE **2.34 — below the 2.3
just-noticeable difference**. By eye the necklace **and its pendant**, the earrings, the brown bob, the
oatmeal tee and the grey studio background are all back, and it is flat cel.

### **The finding: the register and denoise were doing each other's jobs**

The shipped graph had **no register pushing toward flat anime**, so the only thing making a render look
non-photographic was **denoise** — and denoise buys style by *destroying content*, which is why
accessories, garment colour and backgrounds vanished. Give the prompt the styling job and denoise is
freed to do identity preservation, which is what it is actually good at.

That is why the fix is **denoise DOWN, not up** — the opposite of the intuition, and the opposite of
what round 1 was built to test.

### Generalisation: real on identity, partial on style

Same config, denoise 0.45, three more subjects:

| subject | linework old → new | hair ΔE old → new | Fotor linework |
|---|---|---|---:|
| s1 blonde | 0.0005 → **0.0147** *(30×)* | 3.63 → 5.45 | 0.0404 |
| s2 brunette | 0.0015 → 0.0021 | 10.00 → **4.35** | 0.0240 |
| s3 balayage | 0.0059 → **0.0030** *(worse)* | 4.39 → **2.54** | 0.0252 |

**Hair colour improved on 2 of 3 and dramatically on s4. Linework improved on 1 of 3.** s1 by eye
recovers the hoop earrings, the lace cami *with its button placket and hem*, and the meadow with its
flowers and hillside — all lost at the shipped dials. **We are still 2–10× behind Fotor on linework
everywhere**, so the style gap is narrowed and not closed.

### Honest notes

- **The session exceeded the cost half of its ceiling.** ~30 min at $0.72/hr ≈ **$0.36** against
  *"45 min / ~$0.30"*. The two halves are inconsistent — 45 min at this rate is $0.54 — so they cannot
  both bind. Flagged rather than quietly reported against the favourable half.
- **One subject, one seed, for rounds 1–3.** The frontier table is four points on one photograph. It
  is a candidate, not a measurement.
- **`s4` is a poor subject for posterisation**: its flat grey studio background puts the photograph
  itself at 0.6371, so that column reads differently for it than for the others.
- Fotor's own hair ΔE on s1 is **20.95** — it saturates blonde hair considerably. On that axis we beat
  it, which is worth remembering when the eye says Fotor wins everything.

---

## F10 · **"Anime" is not one target** — and the operator prefers the register we were calling a defect

Reviewing the ladder by eye, the operator picked **`8_notile`** as the best output of the whole session,
**including above Fotor**. Also liked: `7_denoise08`, `6_positive`, `2_negative`.

That changes what the style axis is for. F7 and F9 implicitly treated **more linework = better**,
because Fotor was the reference. If the target is a *rendered anime illustration* rather than a *flat
TV screencap*, then linework is **a coordinate to hit, not a quantity to maximise**.

```
   photograph ──▶ ANIME ILLUSTRATION ──▶ FLAT CEL SCREENCAP
                  8_notile                Fotor
                  polished, shaded,       flat fills, hard
                  clean edges             outlines
                  ▲
                  └─ the operator's preference
```

**Two registers, both legitimate products.** The project has been treating "not flat cel" as a defect
since v0.10. It is a defect only relative to a target nobody had chosen. **Choose the target before
tuning further** — otherwise "better" is undefined and every dial search optimises toward whichever
reference happened to be on screen.

**What is a defect either way, and is unchanged:** the lost necklace, earrings, garment colour and
background. That is *identity*, not style, and F9's low-denoise direction is what fixes it.

---

## F11 · The chosen register works — but **not at the denoise it was chosen at** · T6/T6b ✅

**Pod `kdok6n056xz0f0`, 16 renders, ~8 min of GPU, ≈$0.13.** Six subjects at `notile` d0.65 and d0.45,
two at d0.35, three seeds at d0.45.

**hair ΔE — lower is closer**

| subject | shipped (v0.12) | notile d0.65 *(the pick)* | notile d0.45 | notile d0.35 | FOTOR |
|---|---:|---:|---:|---:|---:|
| s1 blonde | 3.63 | 6.34 | **3.41** | **2.91** | 20.95 |
| s2 brunette | 10.00 | 10.35 | **4.38** | — | 7.35 |
| s3 balayage | 4.39 | 6.62 | **3.61** | — | 6.47 |
| s4 bob | 6.05 | 9.84 | **4.24** | **2.57** | 6.36 |
| s5 small face | **1.94** | 13.21 | 5.89 | — | 9.17 |
| s6 landscape | 5.68 | 6.65 | **4.21** | — | 7.71 |

### The uncomfortable part, stated first

**`notile` at d0.65 — the render the operator picked as best of the session — has the worst measured
identity of the three configs.** It is worse than the shipped dials on **five of six** subjects, by up
to 3.4× (s5: 13.21 against 1.94). The *look* was chosen; the identity was never measured. That is
exactly the gap the evaluator exists to close, and here it closed it against the operator's own pick.

### And the resolution

**`notile` at d0.45 keeps the register and fixes the identity.** It beats the shipped dials on **five of
six** subjects and beats d0.65 on **six of six**. By eye on s4 the hair is brown rather than olive-green,
the tee is oatmeal rather than teal, the trousers are maroon, and the earrings are present — while the
polished-illustration look the operator chose is unchanged.

**The candidate setup:** `tile 0.0` · `denoise 0.45` · everything else as shipped.

### Notes

- **s5 is the exception**: the shipped dials win on hair (1.94 vs 5.89). It is the tiny-face subject
  (~1.3% of canvas), and it is also the subject whose refusal path has never fired. Worth its own look.
- **Seed stability at d0.45 (s4, three seeds)**: hair ΔE 2.66 / 4.03 / 4.24, linework 0.0021–0.0027,
  posterisation 0.545–0.587. Real spread on hair — a single render is worth about ±1.5 ΔE — so
  per-subject claims need more than one seed.
- **Linework did not consistently improve** (better on s1 and s6, worse on s3, s4, s5). Per F10 that is
  a coordinate, not a target: the chosen register is the illustration one, and it is being hit.
- **d0.35 is better than d0.45 on both subjects tested** (2.91 vs 3.41, 2.57 vs 4.24). The frontier may
  not have bottomed out. It is also where "anime" starts becoming "a filtered photograph", which is a
  judgement rather than a measurement.

---

## F12 · The register generalises. The failures that remain are not the ones we were measuring. · T6c ✅

**Pod `jp77ucxtifd89i`, 20 renders — 10 synthetic portraits × 2 seeds, ~9 min, ≈$0.15.** Not the
adversarial baseline six; just the portraits on hand, deliberately diverse. Sheet:
`prototype/derived/gallery_notile_d045.png`.

**What holds, across all ten:**

- **The register is consistent.** Every render is the same polished anime-illustration look. It is not
  subject-dependent, which is the thing a one-subject finding could not tell us.
- **Garment and composition retention is strong** — the lace cami *with its buttons and hem*, a sherpa
  collar, white sneakers, a tube top, a full-length lace robe, and a **choker with its pendant** all
  survive. This is the failure that started the whole investigation, and at this setup it is largely
  fixed.
- **Seed variation is modest.** The two draws per subject look alike. The setup is stable, which is what
  makes a committed baseline meaningful.

**What still fails — and none of it is on any axis we measure:**

| failure | measured by |
|---|---|
| **eye colour drifts** — brown → green or blue, repeatedly | nothing |
| **body proportions are idealised** — chest enlargement is systematic and visible on at least four subjects | nothing |
| **faces converge** toward one anime face across different people | `face_styleid`, badly (F4: it rewards *not* stylizing, so it cannot separate "stylized well" from "stylized into someone else") |
| **backgrounds simplify** — flowers thin out, textures flatten | nothing |

**This is F6 arriving from the other direction.** We built four axes; the surviving defects sit almost
entirely outside them. The idealisation one is the sharpest: the vault has recorded *"the quality ladder
pushes toward idealisation and idealised faces are more generic"* as an unmeasured worry since v0.10.
It is no longer a worry, it is visible in four of ten renders, and there is still no axis for it.

**Reading for the decision.** The setup is good and the identity failures that remain are *attribute*
failures a ControlNet+adapter stack is not positioned to fix — they come from the base model's prior
asserting itself over whatever the conditioning does not pin. That is the structural argument for the
instruction-edit architecture, arrived at from our own renders rather than from Fotor's.

---

## F13 · The Qwen output was not a preservation failure. It was a **register overshoot**.

The operator's recollection was *"I did not like the Qwen output"*. Measured, that verdict is about
**style**, and it points the opposite way from how it reads.

| | posterisation | linework |
|---|---:|---:|
| the photograph | 0.267 | 0.038 |
| `notile d0.45` (ours) | 0.272 | 0.014 |
| **FOTOR** | 0.460 | **0.040** |
| **QWEN, as recovered** | 0.675 | **0.075** |

```
   linework:  notile 0.014 ──▶ photo 0.038 ──▶ FOTOR 0.040 ──▶ QWEN 0.075
                  under              the target ▲              overshoot ▲
```

**Qwen did not fail to reach the register. It went past it** — nearly 2× Fotor's linework — landing in
heavy inked manga line-art rather than cel-shaded anime. And the instruction it was given says so in as
many words: *"Anime style, **clean line art**, cel shading, vibrant colors."* It was asked for line art
and it delivered line art.

**What it preserved is the finding.** In one render it kept the entire kitchen behind the subject — the
extractor hood, the microwave, red cabinets, a fridge covered in magnets and photographs, a ceiling fan,
a light switch — plus the necklace, an earring, the lace trim, her eye colour and her smile. **More than
Fotor preserves.** That is instruction-edit behaviour: whatever the instruction does not mention, stays.

### And it kept the tattoos

The subject's chest ink came through — placement, motif and colour. [decisions] §2 `xor` records *"good
anime XOR faithful tattoo — global CN cannot pin a local detail"*, and the tattoo is the project's
largest parked feature on the strength of it.

**That claim is about a global ControlNet, and it stands.** What this shows is that the constraint is
**architectural, not physical** — a different architecture is not bound by it. The tattoo problem may be
a *base* problem rather than an unsolved one.

### So the next move is a string, not a rebuild

> **Corrected by F15, 2026-09-07.** This section's hypothesis — that the register overshoot was caused
> by the instruction — **was tested and is not supported.** Six instructions moved linework barely at
> all; the *sampling path* moved it 3.6x. The prediction was worth making and the sweep was the right
> test; it returned a negative. The paragraph is left standing rather than edited, because a
> prediction rewritten after its result is not a prediction.

The register is a prompt, and the prompt is the cheapest thing in this project to change — it is exactly
the lever that produced the Illustrious win in F9. **Qwen is the right architecture with the wrong
instruction**, and testing that costs one instruction sweep.

**The blocker is storage, not capability**: the Qwen stack is 28.89 GiB against 20.74 GiB free on a
37.25 GiB volume. The operator has approved growing it.

---

## F14 · Three of four missing axes now exist. The fourth did not validate. · T12 ✅

Built **before** the architecture they will judge, on pairs whose answers are already known — the same
discipline as T1. All four are **absolute and cross-base valid**, which is not a nicety: the face
embeddings refuse across bases (F1), so a three-way Illustrious / Fotor / Qwen comparison lives
*entirely* on axes of this kind.

**s1 (a meadow behind the subject — a background with real detail)**

| | background detail *(ratio, ~1 good)* | background colour *(ΔE)* | garment colour *(ΔE)* |
|---|---:|---:|---:|
| shipped dials | **0.009** | 8.27 | 9.44 |
| notile d0.45 | 0.525 | **1.98** | 6.50 |
| FOTOR | **1.008** | 8.60 | **2.99** |

**`background_detail` is the axis this whole investigation needed.** The shipped dials score **0.009** —
the meadow was dissolved to a wash, which is precisely what the eye saw and no axis could say. Fotor
scores **1.008**: it kept the background pixel-for-pixel in detail terms. `notile` sits between at 0.525.

The other two behave sensibly and disagree usefully: `notile` keeps the background *colour* best (1.98)
while Fotor keeps the *garment* colour best (2.99) and saturates the greens (8.60). Two tools, two
different failures — which is the trade-off an unaveraged report exists to show.

### The guard the validation forced

Background edge density across the six photographs runs **0.0001** (a flat wall, s6) to **0.0227** (a
meadow, s5). On `s4`'s flat studio backdrop it is **0.0021**, so the first version of this axis divided
noise by noise and returned 1.138 for a render that had turned the backdrop teal.

**This is F3's flat-histogram failure in different clothes**, and it gets F3's answer: a floor. Below
`MIN_EDGE_DENSITY = 0.005` the axis **refuses**. That silences `background_detail` on two of six
subjects, and a refusal on two subjects is worth more than a number on six.

### `accessory_detail` did not validate, and is demoted

The band where a necklace and earrings live, derived from the photo's own face mask. On s1 it tracked
the eye exactly (shipped **0.006** — the hoops are gone; Fotor **1.185** — kept). On s4 it scored
**0.902** for a render whose necklace is plainly missing, because a bob falls into both ear zones and
the hair supplies the edges the necklace no longer does.

**A proxy that works when the region is clean and lies when it is not is not an axis.** It is renamed
`accessory_detail?`, still computed, never reported as a result — the same shelf as T1's `flat_fraction`
and `unique_ratio`.

**So accessory retention remains unmeasured**, and it is one of the things Qwen visibly does best
(F13: a necklace, an earring, lace trim). The three-way comparison will have to say so rather than
score it.

---

## F15 · The instruction is a weak lever. The **sampling path** is the strong one — and it brackets the target. · T10a/T10b ✅

**Pod `c6xbkziy7hl8yg`, ~35 min, ≈$0.42** — the 28.89 GiB Qwen stack provisioned onto the grown 80 GB
volume (all four files verified against digests derived from Hugging Face before the pod existed), then
6 instructions × 2 subjects at 4-step Lightning, then 1 instruction × 2 subjects at the full 20-step
path.

**All 13 node types the recovered graph needs exist on the shipped image**, and `CLIPLoader` accepts
`qwen_image`. Nothing had to be built to run a two-year-old deleted graph.

### The instruction sweep returned a negative

Six instructions on s1, linework: **0.0574 – 0.0776**. Fotor is **0.0404**, the photograph **0.0299**.
Every instruction overshot, including *"no heavy black linework"* (0.0748) and the bare *"Make this an
anime screencap"* (0.0574). **Dropping the phrase F13 blamed changed almost nothing.**

### Because the register is set by the sampling path

| s1 | posterisation | linework | hair ΔE | bg detail | bg colour |
|---|---:|---:|---:|---:|---:|
| the photograph | 0.266 | 0.0299 | — | 1.000 | — |
| FOTOR | 0.460 | **0.0404** | 20.95 | 1.008 | 8.60 |
| notile d0.45 | 0.272 | 0.0136 | **3.41** | 0.525 | **1.98** |
| qwen **Lightning 4-step** | 0.448 | **0.0721** | 22.94 | 2.507 | 14.24 |
| qwen **full 20-step** | 0.397 | **0.0198** | 17.12 | **1.110** | 6.74 |

| s4 | posterisation | linework | hair ΔE | garment ΔE |
|---|---:|---:|---:|---:|
| the photograph | 0.637 | 0.0049 | — | — |
| FOTOR | 0.838 | **0.0255** | 6.36 | 5.82 |
| notile d0.45 | 0.545 | 0.0021 | 4.24 | 5.70 |
| qwen **Lightning** | 0.881 | 0.0348 | 5.85 | 5.62 |
| qwen **full** | 0.699 | **0.0054** | **2.80** | 7.59 |

**Same instruction, same subject: linework 0.0721 → 0.0198, a 3.6× move.** No instruction came close to
that. The register is controlled by steps / cfg / the Lightning LoRA, not by the words.

### And the two settings bracket the target rather than reaching it

- **4-step Lightning over-transforms** — inked manga, linework 1.8× Fotor's.
- **20-step full under-transforms** — by eye, s4 is *the photograph, lightly retouched*: the necklace,
  its pendant, both earrings, the hair, the tee, the maroon trousers and the grey studio are all
  perfectly kept, and it is barely anime at all. The numbers agree: linework **0.0054** against the
  photograph's 0.0049.

```
   linework:  qwen full 0.020 ── photo 0.030 ── FOTOR 0.040 ── qwen lightning 0.072
                       under              the target ▲                 over
```

**The target sits between two settings we have already run.** That is a much better position than
either "it does not work" or "it needs a different model".

### What Qwen is unambiguously better at

At full quality, on the axes that survive a cross-base comparison: **hair ΔE 2.80 on s4** — better than
our 4.24 and Fotor's 6.36 — and **background detail 1.110 on s1**, matching Fotor's 1.008 where our own
best is 0.525. It keeps things. That was never the question.

### Three limits on all of the above

- **The 20-step comparison moves three variables at once** — steps 4→20, cfg 1.0→2.5, and the Lightning
  LoRA off. Attribution between them is not available from this data.
- **Only one instruction was run at 20 steps.** *"The instruction is a weak lever"* is established at
  Lightning and assumed, not shown, at full.
- **Two subjects.** s1's hair ΔE stays poor at 17.12 even at full quality, so "Qwen keeps things" is not
  uniform across subjects.

---

## F16 · Colour distance to a photograph penalises correct stylization — F4's disease, on the colour axes

The operator picked `40_qwen_sweep/5_recovered_keepall/s1` as good anime. Its measured scores say
otherwise: **linework 0.0706** (against Fotor's 0.0404) and **hair ΔE 22.91**. By eye the hair is blonde
and right, the gold hoops are there, the lace placket and hem are there, the meadow and treeline are
there.

**s1's hair, mean L\*:**

| | L\* | hair ΔE |
|---|---:|---:|
| the photograph | 41.4 | — |
| `notile d0.45` — barely stylized | 43.3 | **3.41** |
| FOTOR — brightened | 62.1 | 20.95 |
| QWEN — brightened | — | 22.91 |

**Anime hair *is* brighter and flatter.** So a colour distance measured against a photograph will always
prefer the least-anime render. That is **F4 exactly** — *the metric rewards not stylizing* — appearing on
the colour axes rather than the face one, and it was not anticipated when they were built (T2, T12).

### The rule this forces

> **Colour ΔE is valid *within* one style register and systematically unfair *across* registers.**

A three-way Illustrious / Fotor / Qwen table on colour ΔE would flatter the least-stylized entrant by
construction. `notile d0.45` is the least stylized of the three. **The table would have looked
decisive and been wrong**, which is the failure mode this project keeps catching one step before it
ships.

**What survives cross-register:** `background_detail` (a ratio of like quantities, and stylization does
not systematically add or remove background edges the way it brightens hair) and the two style measures
themselves, which are *descriptions* rather than scores. **What does not:** `hair_colour`,
`garment_colour`, `background_colour`.

**Not fixed here.** The candidate fix is to normalise colour distance by the render's own stylization —
compare against what a correctly-stylized version of that colour would be, rather than against the
photograph's. That needs a model of "what stylization does to a colour", which is a version's work and
not a prototype's. **Until then the cross-register comparison is reported per axis with this caveat
attached, or not reported.**

### And a caution on the style axis itself

It was calibrated on three points assuming **Fotor is the target** (F7). The operator now rates a
Qwen render at linework 0.0706 as good — above Fotor's 0.0404. So the target is a **band, not a point**,
and its upper edge is unmeasured. Do not treat "further from Fotor's coordinate" as "worse" without
asking the operator.

---

## F17 · The thesis is answered — and it is a **reachability** result, not a trade-off · T10d ✅

**Pod `0ur2whpfighgo8`, 14 renders, ~16 min, ≈$0.19.** Seven sampling settings × two subjects, one
instruction held fixed.

| s1 | linework | posterisation | bg detail | hair ΔE |
|---|---:|---:|---:|---:|
| the photograph | 0.0299 | 0.266 | 1.000 | — |
| **FOTOR** | **0.0404** | **0.460** | **1.008** | 20.95 |
| ours — notile d0.65 | 0.0038 | 0.230 | **0.064** | 6.34 |
| ours — notile d0.45 | 0.0136 | 0.272 | **0.525** | 3.41 |
| ours — notile d0.35 | 0.0150 | 0.314 | **0.598** | 2.91 |
| qwen f_full_20_cfg4 | 0.0295 | 0.404 | 1.370 | 21.84 |
| qwen d_full_8_cfg25 | 0.0320 | 0.396 | 1.492 | 25.73 |
| qwen e_full_12_cfg25 | 0.0351 | 0.399 | 1.675 | 24.03 |
| qwen g_full_20_cfg25 | 0.0376 | 0.393 | 1.812 | 23.28 |
| qwen c_light_8_cfg2 | 0.0645 | 0.438 | 2.275 | 22.48 |
| qwen a_light_4_cfg1 | 0.0716 | 0.419 | 2.765 | 22.90 |
| qwen b_light_8_cfg1 | 0.0776 | 0.432 | 2.955 | 22.27 |

### The two architectures occupy disjoint regions

```
   ours:   linework 0.004 – 0.015    bg detail 0.06 – 0.60     ← a small box, low-left
   FOTOR:  linework 0.040           bg detail 1.008
   qwen:   linework 0.030 – 0.078    bg detail 1.37 – 2.96     ← somewhere else entirely
```

**There is no overlap.** Our most faithful setting retains **0.598** of the photograph's background
detail; Qwen's *least* faithful setting retains **1.370**, at twice the stylization. This is not a
trade-off curve with two positions on it — **our stack cannot reach where Fotor and Qwen live at any
dial setting we have found.**

That is the architecture thesis, answered, on our own axes, from our own renders. And it is a stronger
result than a trade-off would have been: a trade-off could be tuned around, a reachability gap cannot.

**Both architectures' curves slope the same way** — more stylization comes *with* more retention, not
instead of it. Our own "trade-off" along `denoise` was never style-against-identity; it was
distance-from-photograph against everything, which is what F9 found from the other side.

### A correction F15 flagged in advance

F15 said *"the instruction is a weak lever"* and marked it **shown at Lightning, assumed at full**.
It is now shown false at full: the same sampling setting (20 steps, cfg 2.5) gives linework **0.0198**
with `4_tv_anime` and **0.0376** with `5_recovered_keepall` — nearly 2×.

**Both levers work.** The sampling path spans 0.030–0.078; the instruction spans ~0.020–0.038 at a fixed
path. They are roughly independent, which is more control than either finding alone suggested.

### What `bg detail > 1` means, said plainly

Qwen scores **1.37–2.96** where the photograph is 1.000. It is not merely preserving the background —
it is **redrawing it with anime linework**, adding edges the photograph never had. Reading that as
"better preservation" would be wrong. The axis measures *detail survived*, and detail can be added.
Fotor's 1.008 is the number that means "kept, not embellished".

### By eye, on the contact sheet

Every Qwen setting keeps the **gold hoops**, the **lace placket and hem**, the **meadow with its
flowers**, the **treeline**, the **hills** and the **blue eyes**. `notile d0.45` keeps none of the
accessories and washes the background out. The Lightning settings (a, b, c) read as **flat cel**; the
full settings (d–g) read as **painterly illustration**.

**Hair ΔE is unusable here** — every Qwen setting scores 21.8–25.7 and Fotor 20.95, indistinguishable,
because F16's disease dominates: all of them brighten blonde hair and our least-stylized render does
not.

---

## F18 · `qwen-flatcel` across ten portraits — the two architectures fail in **different shapes** · T10e/T10f ✅

**Pod `2oiozb2bppxama`, 11 renders, ≈$0.12.** The operator's pick (`c_light_8_cfg2`) on every synthetic
portrait. Sheet: `prototype/derived/gallery_qwen_c_light_8_cfg2.png`.

| subject | linework | posterisation | bg detail | bg colour ΔE | garment ΔE |
|---|---:|---:|---:|---:|---:|
| 00003 | 0.0657 | 0.436 | 2.274 | 20.7 | 4.8 |
| 00004 | 0.0619 | 0.651 | 3.528 | 15.6 | 9.1 |
| 00014 | 0.0415 | 0.890 | — | 5.0 | 8.8 |
| 00022 | 0.0420 | 0.478 | — | **28.0** | **38.4** |
| 00033 | 0.0433 | 0.771 | — | 11.7 | 6.4 |
| 00035 | **0.1134** | 0.753 | — | 5.4 | 4.1 |
| 00050 | 0.0714 | 0.414 | **7.367** | 20.1 | 8.6 |
| 00059 | 0.0277 | 0.585 | 0.840 | 2.0 | 2.1 |
| 00060 | 0.0506 | 0.535 | 2.152 | 7.0 | 1.8 |
| 00072 | 0.0824 | 0.628 | — | 14.6 | 10.8 |

**The register generalises** — flat cel on all ten by eye. But linework spans **0.028 – 0.113**, a 4×
range where `notile`'s spanned about 2×. **This preset is less consistent than the other one**, which is
the cost of running at 8 Lightning steps.

### What it keeps, and it is a lot

By eye across the ten: a **necklace and gold hoops** (00033), a **choker with its heart pendant plus two
layered necklaces** (00072), **white sneakers and ripped jeans** (00035), a **belt** (00022), a
**sherpa collar over a white top** (00004), a **concrete wall** (00050), an **ornate doorway** (00059),
a **hedge and pavement** (00035), **coastal buildings** (00004). `notile` kept **none** of the
accessories on any subject.

### And three failures that are a different *kind* from ours

- **00014: the background was replaced outright** — a neutral studio became a tropical beach with palm
  trees and ocean. Not simplified: **invented**.
- **00060: hair went blonde → red**, and large teal earrings appeared that are not in the photograph.
- **00004 and 00072: eye colour drifted.**

```
   ours  (notile):  failures are SYSTEMATIC and MILD
                    -- accessories always lost, backgrounds always washed out
   qwen (flatcel):  failures are OCCASIONAL and DRAMATIC
                    -- usually keeps everything, then replaces a whole background
```

**That is the honest characterisation of the architecture choice, and neither shape is strictly better.**
A systematic failure is predictable and can be designed around; a dramatic one is rare and unshippable
when it lands. Which matters more is a product decision, not a measurement.

### What the numbers cannot say here

`background_detail` scored on only **5 of 10** — the rest are studio backdrops below the denominator
floor (F14). `bg colour` and `garment colour` are reported but must not be used to rank this preset
against `notile`: F16 establishes they penalise correct stylization, and this preset is far more
stylized. **00022's garment ΔE of 38.4 is the loudest number in the table and it is uninterpretable** —
it may be a real failure or it may be F16.

**Accessory retention — the thing this preset is visibly best at — remains unmeasured** (F14). The
record says so in words because the proxy did not validate.

---

## F19 · The style LoRA applies, and it fights Lightning · T13 ✅

`raena_qwen_image_lora_v0.1` (Civitai 1914845, `baseModel: Qwen` — i.e. Qwen-*Image*, not Edit),
0.27 GiB, verified against its published digest. s1:

| setting | linework | posterisation | bg detail | bg colour ΔE |
|---|---:|---:|---:|---:|
| FOTOR | 0.0404 | 0.460 | **1.008** | 8.60 |
| a — LoRA **off**, Lightning 8 | 0.0657 | 0.436 | 2.274 | **20.7** |
| b — 0.5, Lightning 8 | 0.0734 | 0.420 | 2.574 | 14.0 |
| c — 0.8, Lightning 8 | 0.0779 | 0.410 | 2.856 | 13.7 |
| d — 1.0, Lightning 8 | 0.0674 | 0.389 | 2.563 | **13.3** |
| f — LoRA **off**, full 12 | 0.0351 | 0.399 | 1.675 | 15.8 |
| g — 1.0, full 12 | **0.0167** | 0.334 | 0.957 | 6.8 |
| h — 1.0 + trained words, full 12 | **0.0109** | 0.315 | 0.596 | **5.5** |

**Both questions the sweep existed to answer come back yes.**

1. **It applies.** A Qwen-*Image* LoRA does affect Qwen-Image-*Edit* — on the full path it moves linework
   **0.0351 → 0.0167 → 0.0109**, a 3× swing, and bg colour ΔE from 15.8 to 5.5. The backbone is shared
   enough.
2. **It fights Lightning.** Under Lightning the same LoRA at the same strength barely moves the register
   at all (0.0657 → 0.0674). Lightning dominates whatever else is in the chain.

**Its direction is away from flat cel, toward painterly** — every full-path setting *reduces* linework.
That is the opposite of the register the operator chose, so as a route to a Fotor-like look it is the
wrong instrument.

**But it is not useless.** Stacked with Lightning it leaves the flat-cel register intact and improves
colour fidelity markedly — bg colour ΔE **20.7 → 13.3** at strength 1.0, the best of the Lightning
group. The operator's preference for the LoRA renders is consistent with that: same register, truer
colour.

**Licence note.** `allowCommercialUse: Image, RentCivit, Rent`; `derivatives: True`. Usable for a
portfolio that publishes scores and recipes rather than weights.

---

## F20 · Fotor is **stochastic**. The translation-network hypothesis is dead, and our Fotor numbers have unmeasured variance.

The operator ran the same photograph through Fotor twice. By eye: *"almost the same, they differ in
very very small details."* Measured, they differ by far more than that.

| | |
|---|---:|
| mean absolute pixel difference | **17.36** / 255 |
| median | 6 |
| pixels differing by > 8 levels | **50.6 %** |
| pixels differing by > 64 levels | **8.8 %** |
| **JPEG re-encode floor** (same image, q95) | **0.415** |

**The two draws differ by 42× the encoding noise floor**, and the difference is spread across the whole
frame rather than sitting in one place. A deterministic image-to-image translation network would be
pixel-identical, or differ at the floor. **Fotor regenerates the image every time.**

### What that kills, and what it opens

**Dead: the AnimeGAN-class hypothesis.** Fotor is not a network that transforms pixels locally and
preserves geometry by construction. It is generative and seeded.

**And that reframes its most striking number.** F17 made much of Fotor's `background_detail` landing at
**1.008** — reproducing the photograph's edge density almost exactly — against Qwen's 1.4–7.4 and our
0.06–0.60. That is **not** because it copies pixels. It regenerates and *lands there*, which makes it a
property of the model's learned style rather than of a preserving architecture.

**That is encouraging rather than deflating**: a target a stochastic generator hits is a target other
stochastic generators can be tuned toward. It is a model-choice and tuning problem, not an
architectural wall.

### The methodological correction

**Every Fotor number in F14, F17 and F18 is a single draw from a stochastic process, and we have been
treating them as fixed reference points.** Two draws on one subject give the first estimate of that
spread:

| axis | draw 1 | draw 2 | spread |
|---|---:|---:|---:|
| linework | 0.0651 | 0.0615 | 5.5 % |
| posterisation | 0.539 | 0.565 | 4.7 % |
| bg colour ΔE | 3.68 | 3.57 | 3.0 % |
| **garment colour ΔE** | **4.47** | **3.60** | **19.4 %** |

The style axes are stable to ~5 %, which is small against the gaps F17 reports — **the disjoint-regions
conclusion survives comfortably.** The colour axes are not: 19 % on garment means differences under
about a fifth are noise, and F18's alarming garment ΔE of 38.4 on `00022` still cannot be read, now for
a second reason.

**One draw per subject was the wrong design** and it was chosen before anyone knew Fotor was seeded.
Any future comparison against it needs 3+ draws, exactly as F11 forced for our own renders.

---

## F21 · The 8-step-native LoRA does not fix the inconsistency. It is Qwen's, not ours. · T14 ✅

**Pod `yu6fk20hd3hfsh`, 10 renders, ≈$0.14.** The same ten portraits, the same instruction and sampling
path, with `Lightning-8steps-V1.0` in place of the 4-step LoRA we had been running at 8 steps.

**The prediction was recorded in the script before the render.** It resolves on the second branch.

| | 4-step LoRA @ 8 steps | **8-step native @ 8 steps** |
|---|---:|---:|
| linework min / med / max | 0.0277 / 0.0619 / 0.1134 | 0.0222 / 0.0560 / 0.1064 |
| **linework spread** | **4.09×** | **4.80×** |
| posterisation spread | 2.15× | 2.62× |
| bg detail max | 7.367 | 4.098 |

**The spread did not narrow toward 2×. It widened slightly, to 4.80×.** So the inconsistency is **not**
a mismatch we introduced by running a 4-step LoRA at 8 steps — it is a property of Qwen-Image-Edit at
this task, and it stands as a real mark against `qwen-flatcel` for a product that ships five variations
per photograph.

**The third prediction held**, which is the reassuring part: the median barely moved (0.0619 → 0.0560)
and stayed far from Fotor's 0.040. Step distillation changes fidelity and consistency, not style — as
stated in advance. Had the median jumped to Fotor's coordinate, the measurement would have been suspect.

**One thing did improve**: the worst-case background embellishment fell from 7.367 to 4.098. Less extreme
edge-adding at the tail, with the same median. Worth having, not worth switching for on its own.

**Cost of the negative: ≈$0.14.** It closes the cheapest remaining hypothesis about the preset's weakest
property, and it means any future fix for consistency has to come from somewhere other than the step
schedule.

---

## F22 · Fotor's catalogue says the moat is a **style library**, not an architecture

The operator's screenshot of Fotor's *AI Art Effects* shows dozens of tightly branded looks — *Animal
Crossing Style*, *Kawaii Anime*, *Cartoon PlotSnap*, *Caricature Art*, *Music Box*, *Vector
Illustration* — across tabs for Cartoon, Sketch and more. The effect used for our comparison is the one
simply called **Anime**.

**Only one architecture ships that catalogue economically:**

| shape | verdict |
|---|---|
| per-style **prompt** on one model | could not hit *"Animal Crossing Style"* reliably or consistently |
| per-style **fine-tuned model** | dozens of full models to host. Nobody does this |
| **one base + per-style LoRA** | ~200 MB per style, hot-swapped, distinct and reliable. **This** |

**It fits every measurement we have.** F20 says stochastic, so a diffusion base rather than a translation
network. F17 says `background_detail` **1.008** — reproducing the photograph's edge density — where our
Qwen *adds* edges at 1.4–7.4, and a trained style adapter is exactly what controls that. The register is
consistent per style, which is a LoRA and not a prompt. A free tier and fast turnaround fit a small
adapter swapping on a shared base.

### The consequence, and it redirects the project

**They are not doing something structurally cleverer than us.** They have an edit base — possibly one we
can run — and they **trained the adapters that do not exist publicly**.

The Civitai search established the gap directly: for Qwen-Image-Edit the community trains **anime→real**
almost exclusively, and the one photo→anime candidate is licence-blocked for a portfolio. **Fotor's
answer to that same gap was to train their own.**

```
   what we lack  ≠  a better model
   what we lack  =  a trained style LoRA for the direction we want
```

That moves *"train our own"* from fallback to **the answer** — and it is the strongest portfolio story
available: *the open ecosystem only went one direction, so I trained the other, and I had an evaluator to
prove it worked.*

**Still unknown: which base.** One unused clue — Fotor's output is always capped at **2880 on the long
side** (1968×2880 portrait, 2880×1915 landscape), a fixed production policy that suggests
generate-then-upscale rather than a research pipeline.

---

## F23 · Fotor does not solve the tattoo. It solves **tattoo presence**. `xor` survives contact with a commercial product.

A heavily tattooed subject — full irezumi coverage, neck to hips, both sleeves — through Fotor's *Anime*
effect. Photo 800×1200, canvas 1024×1536, linework **0.0126 → 0.0264**, posterisation 0.314 → 0.371,
background colour ΔE **4.47**.

**What it kept:** the coverage and its **placement** — neck piece, chest, both full sleeves, stomach,
hips — the approximate **palette** (orange, teal, blue, red), the black bikini and its straps, the desert
with its mountains and scrub, black hair, the general proportions. The read *"heavily tattooed woman in a
desert"* survives completely.

**What it lost:** **the motifs, as motifs.** The photograph has readable subjects — a large mask/face
centrepiece across the chest, a dragon, eyes, geometric panels, script. The render has *tattoo-textured
noise*: plausible swirls, florals and vague creatures that read as irezumi at a glance and contain **none
of her actual tattoos**.

### This is `xor`, confirmed from the outside

[decisions] §2 `xor` records *"good anime XOR faithful tattoo — global CN cannot pin a local detail"*, and
the catalogue's own finding was sharper: *"the gap is not 'can a model put a tattoo on an arm
convincingly' — it can, well. **The gap is specificity: can it put *this* tattoo there.**"*

**A commercial product, with what F22 argues is a purpose-trained style LoRA, hits exactly that wall.**
So `xor` is **not an artefact of our ControlNet stack**. It is a property of the task at anime
stylization levels: fine ink detail sits below the representational budget of the style.

That partially rehabilitates our own architecture. We are not uniquely bad at tattoos. **Nobody is good
at them.**

### And the caveat on "Qwen solved it"

F13 recorded Qwen keeping a subject's chest ink recognisably, and it did. But that render came from the
**under-transforming** end of F15's bracket — the setting whose s4 output was *"the photograph, lightly
retouched"*, at linework 0.0198 against the photograph's 0.030.

**Qwen preserved the tattoo by barely stylizing.** Which is `xor` a third time, now measured on a third
system. The amount of ink fidelity available is coupled to how little the render is transformed, and the
coupling is the finding rather than any one system's failure.

**What this does not close:** whether a *subject-trained* LoRA carrying the ink vocabulary (the parked
route in [ideas]) escapes the trade-off. Nothing here tests that — it tests only that no
general-purpose stylizer, ours or commercial, carries specific ink through a strong style transfer.

---

## F24 — the blur was the architecture. From noise, the style bar is cleared 3x over

**2026-09-08 · one pod session, 15:05–15:15, 10 minutes, ~$0.05 · six synthetic subjects, one seed ·
`prototype/renders/n3_fromnoise/` · re-measurable with `prototype/n4_measure.py`.**

Round 1's `notile-d045` was rejected for softness, and `SUMMARY.md` blamed the architecture rather than
the tuning: `i2i` seeds the latent from the photograph, so the sampler must reconcile a photographic
latent with an anime prior and returns an interpolation between them. **That prediction is now tested.**
Take the photograph out of the latent, keep InstantID and OpenPose as conditioning, and hand-write the
subject from a criteria sheet.

The bar was stated in `CRITERIA.md` §4 before the pod was booted: **median linework at or above the
photograph's own.**

| flow | linework ↑ | posterisation | linework spread |
|---|---:|---:|---:|
| the photograph | 0.0077 | 0.411 | 6.10x |
| **`notile-d045`** · round 1's Illustrious img2img | 0.0043 | 0.466 | 9.07x |
| **`fromnoise-v1`** · this round | **0.0240** | 0.296 | **1.28x** |
| **`qwen-flatcel`** · round 1's Qwen edit path | 0.0545 | 0.606 | 2.97x |

Medians over the same six subjects, each render read at its own photograph's canvas.

**The bar is cleared, and not narrowly.** `fromnoise-v1` runs **3.1x the photograph's own linework** and
**5.6x `notile-d045`'s**, and it beats the photograph on five of the six subjects individually. The
softness was the architecture. F7's off-axis diagnosis was right about the cause and right about the fix.

### The consistency result was not predicted, and it inverts SUMMARY #11

**1.28x spread across six subjects** — 0.0205 to 0.0263. Against `notile-d045`'s 9.07x, `qwen-flatcel`'s
2.97x, and the input photographs' own 6.10x.

`SUMMARY.md` #11 recorded *"consistency is Qwen's, not ours"*, from F21's finding that the 8-step-native
Lightning LoRA widened Qwen's spread rather than narrowing it. **That conclusion was about the wrong
axis.** The flow that varies least is the one whose latent does not start from a photograph — and it
varies less than the photographs themselves, which is the tell. An img2img flow inherits its inputs'
variance by construction; a from-noise flow does not.

### It is still off-axis, in the opposite direction

**Posterisation 0.296, against the photograph's 0.411.** These renders are *less* flat than their own
inputs, and far less flat than `qwen-flatcel`'s 0.606. By eye that is exactly what they are: glossy,
gradient-rich rendered illustration with strong lines — not flat cel.

Round 1's failure was *photographic flatness with no lines*. This one is *strong lines with less
flatness than a photograph*. **Both are off-axis; they are off it in different directions**, and only
this one has the deficit on the axis nobody has yet found a lever for. Whether the operator wants flat
cel at all is a question the register was never asked; `notile` was chosen in T5 as "rendered
illustration", and this is a more strongly drawn version of that choice.

### What the sheet bought, and what it did not

**Criteria adherence is high.** Across the six: pose, hair silhouette, hair colour and eye colour survive
on all six by eye. `00072`'s choker, chain and heart pendant all render — **the accessories
`notile-d045` lost every single time**. `00003`'s freckles render. Clothes drift twice: `00033`'s white
tank comes back light blue, and `00059`'s sheer lace robe comes back opaque satin.

**And the operator's verdict on the identity bar is a pass.** Side by side with the photographs:
*"holistically I do have a feeling the anime images are based on the photo"*, *"they do preserve the
identity criteria from the photo original"*, and the register is *"really good style anime"*. Recorded
in each sheet's verdict block; **the bar passes holistically**, with the per-criterion rows left blank
because a whole-image judgement is what was given.

That overturns a claim in this finding's first draft. Reading the six renders alone, the assistant judged
the faces generic and called `CRITERIA.md` §6's open question answered against InstantID. **The operator,
comparing against the photographs, does not see that** — and on identity the operator is the instrument
this project has. What survives of the observation is narrower and still worth acting on: nothing in the
graph has been swept, and `ip_weight` still sits at the 0.9 an img2img graph wanted, where the latent was
already carrying the face. **Whether InstantID has more to give at `denoise 1.0` is untested, not
answered.**

Two systematic drifts, both on unscored fields, both worth recording:

- **Skin tone drifts darker.** `00014` declared `fair skin` and renders markedly tanned; the tag is
  being outvoted. (`00003` was named here in this finding's first draft and should not have been: its
  own tag reads `light skin, sun-tanned`, so a tanned render is the tag being *obeyed*. F25's skin arm
  inherited the error and is inconclusive because of it.)
- **Age drifts younger, on every subject.** `00003` reads early teens against a declared `young woman`,
  and `00033`'s declared `mature female` reads a decade younger than her photograph. This is the failure
  `CRITERIA.md` §3 named when it added the age band, and adding the tag did not prevent it.

### What this changes

**Round 1 ended on a split and round 2 does not.** Round 1: the style he liked lost identity, the identity
he wanted had a style he disliked, and F17 showed the two architectures occupied disjoint regions — a
reachability result that could not be tuned around. Here **both bars are met by one flow**: the style bar
by measurement, the identity bar by the operator's eye. That is the first time in either round that has
happened, and it is what makes this the flow rather than a third rejected candidate.

What is left is improvement rather than rescue, and it is unusually cheap, because **nothing in this
graph has been swept.** `ip_weight` is at 0.9, `cn_strength` at 0.5 and the OpenPose leg at 0.6 — every
one of them set for an img2img graph whose latent already carried the face, and none revisited since the
photograph left it. `cfg` was moved to 7 by argument, not by measurement.

---

## F25 — ip_weight is at its ceiling, and the free lever is the other half of InstantID

**2026-09-08 · one pod session, 15:34–15:43, 9 minutes, ~$0.05 · 7 arms x 3 subjects = 21 renders ·
`prototype/renders/n6_face/` · `prototype/face_ladder.py`, one change per arm.**

F24 left every dial in `fromnoise-v1` unswept: `ip_weight` 0.9, `cn_strength` 0.5 and the OpenPose leg
0.6 were all chosen for an img2img graph whose latent already carried the face, and `cfg` was moved to 7
by argument rather than measurement. From noise, InstantID is the only carrier of the face, so its two
dials are the most under-argued numbers in the file. This is round 1's `ladder.py` discipline applied to
them: **one change each, never two**, every arm against a control that reproduces F24 exactly.

### First, the control found a determinism floor

`1_control` re-renders F24's graph, seed and prompt on a **second pod**. It came back bit-identical on
one subject of three, and on the other two differed at **mean |Δ| ≈ 2/255, with linework moving 0.0003 —
about 1%.** Perceptually the same image; numerically not the same bits. Same class of test as F20's on
Fotor, and a far quieter answer: Fotor was stochastic at **42x** the JPEG floor, ours is GPU float
nondeterminism.

**That number is what makes the rest of this finding readable.** Every arm below moved the render by
mean |Δ| of 10 to 41 — **5x to 20x the floor.** No arm is noise.

### The ladder

| arm | change | median linework | median posterisation | mean \|Δ\| vs control |
|---|---|---:|---:|---:|
| `1_control` | — | **0.0233** | 0.264 | 0.0 |
| `2_ip_1.2` | `ip_weight` 0.9 → 1.2 | 0.0182 | 0.268 | 22.8 |
| `3_ip_1.5` | `ip_weight` 0.9 → 1.5 | **0.0097** | 0.241 | 37.9 |
| `4_cn_0.8` | `cn_strength` 0.5 → 0.8 | 0.0223 | **0.288** | 22.1 |
| `5_cfg_5` | `cfg` 7 → 5 | 0.0167 | 0.303 | 20.0 |
| `6_skin` | skin tag at emphasis 1.4 | 0.0270 | 0.270 | 17.7 |
| `7_age` | age tag at emphasis 1.4 | **0.0287** | 0.285 | 15.6 |

### ip_weight up is the wrong direction, and it fails visibly

**0.9 is at or past the ceiling.** At 1.2 the render acquires vertical streaking and a hard seam along
the jaw and neck — the face is arguably closer in proportion, and the image is damaged. At 1.5 it
collapses: colour cast, washed-out contrast, smearing, and on `00003` **linework 0.0018 — below round
1's rejected `notile-d045` at 0.0043.** Pushing the adapter harder does not buy identity; it buys
artifacts, and it spends the style bar to do it.

That closes the question F24 left open in the assistant's reading and the operator's alike: **InstantID
does not have more to give on this dial.** Whatever raises face fidelity from here, it is not
`ip_weight`.

**And the operator rejected both arms on sight** — *"those values seem to make the anime not clean"*.
The eye and the two axes agree, which is the first time in this repository that a dial has been closed
by both at once. Both arms were dropped from the contact sheet the same day; the renders stay on disk
and the evidence stays here, because a comparison table is for choosing between live candidates.

### `cn_strength` is the free lever

**0.5 → 0.8 holds the style bar and improves the face.** Median linework 0.0223 against the control's
0.0233 — inside a whisker of it — and the **highest posterisation of any dial arm at 0.288**, which is
movement toward the flat-cel register that F24 named as this flow's remaining deficit. On `00003` it
*raised* linework to 0.0283, the second-best single reading in the whole ladder, with visibly cleaner
facial structure and **no artifacts of the kind arms 2 and 3 produced.**

The asymmetry is the finding, and it is a mechanism story rather than a tuning one. `ip_weight` weights
the **face embedding**; `cn_strength` weights the **keypoint ControlNet**. They are two mechanisms, not
one dial under two names — and from noise, pushing *geometry* is free where pushing *appearance* is
ruinous. That is consistent with everything `xor` has said in this repository: structure transfers
through a style change, appearance does not.

### cfg 7 was right, and it was right by argument

`5_cfg_5` drops median linework to 0.0167, a 28% loss against the control. F24's `cfg 5 → 7` was made on
reasoning — from noise the prompt carries the criteria, so text adherence is worth more — and never
measured. **It is now measured, and the reasoning held.**

### The emphasis arms: one clean negative, one that cannot be read

Both raised linework (0.0270 and 0.0287, the two highest medians in the ladder), so **prompt emphasis
sharpens this flow** — an unlooked-for result and a lever for the register, not the face.

- **`7_age` is a clean negative.** `(young woman:1.4)` did not make the subject read older. The age drift
  F24 recorded survives a 40% emphasis on the exact tag that was supposed to prevent it, which means the
  base's prior is not being outvoted by weighting alone.
- **`6_skin` cannot be read, and the fault is in the arm.** `00003`'s skin field is literally
  `light skin, sun-tanned`, so weighting it weights the tan; `00050` declares `tan skin`. Neither is the
  drift case. **The subject where skin renders against its tag is `00014` (`fair skin`), and `00014` is
  not in this ladder.** The arm tested the wrong subjects and its result means nothing. Recorded rather
  than quietly dropped, because the same mistake corrected F24's own claim above.

### What is now the best-known configuration

`ip_weight` **0.9** (unchanged, and now known to be a ceiling rather than a default), `cn_strength`
**0.8**, `cfg` **7**. Untested together — every arm here is one change from the control, so a combined
run is a new render and not an inference.

---

## F26 — the bar was on the wrong axis, and the operator's eye found it

**2026-09-08 · two pod sessions, 16:32–16:40 (wasted) and 16:41–16:44 · six subjects ·
`prototype/renders/n8_combined/` · `prototype/combined.py`.**

Shown N6's contact sheet, the operator picked `5_cfg_5` as the best-looking anime and `4_cn_0.8` second,
and rejected the rest. **Ranked by posterisation those are 1st and 2nd of seven, and the arm he called
worst is 7th. Ranked by linework his favourite is 6th of seven.**

| arm | posterisation | linework | the operator |
|---|---:|---:|---|
| `5_cfg_5` | **0.303** | 0.0167 | **liked most** |
| `4_cn_0.8` | **0.288** | 0.0223 | **liked** |
| `7_age` | 0.285 | 0.0287 | rejected |
| `6_skin` | 0.270 | 0.0270 | rejected — "bluring" |
| `2_ip_1.2` | 0.268 | 0.0182 | rejected |
| `1_control` | 0.264 | 0.0233 | — |
| `3_ip_1.5` | **0.241** | 0.0097 | **rejected, worst** |

**Posterisation orders his preference; linework does not.** The two arms he called blurry have the
*highest* linework in the ladder — which is the axis behaving exactly as `style_axis.py`'s own docstring
warns a *different* candidate did, conflating a quality with its opposite.

### Why the wrong axis was being quoted

Round 2 inherited round 1's bar without re-deriving it. **Round 1's failure was blur, so linework was
its axis** — F7 measured our renders at 60x below the photograph and everything followed from that. **Round
2's failure is insufficient flatness**, and F24 said so in the same paragraph that quoted linework as the
bar. The bar is now *median posterisation at or above Fotor's 0.460*, and linework is a floor rather than
a target (`CRITERIA.md` §4).

This is the third time in this repository an axis has been caught rewarding the wrong thing — F4 on the
face axis, F16 on colour distance, and now the round-2 bar. **In all three the operator's eye was the
instrument that caught it**, which is an argument for the contact sheet as a standing part of the loop
rather than a one-off.

### N8: the two picks together, on sheets rewritten in booru tags

Two changes at once, which every ladder here has refused — the operator's call, and the cost was written
into `combined.py` before the render: this run cannot say which half did what.

| | posterisation | linework |
|---|---:|---:|
| the photograph | 0.413 | 0.0108 |
| **N3** — cn 0.5, cfg 7, prose sheets | 0.296 | 0.0240 |
| **N8** — cn 0.8, cfg 5, booru sheets | **0.332** | 0.0151 |
| Fotor — the bar | 0.460 | 0.0404 |

**Posterisation up 12%, on 5 of 6 subjects.** Still 28% short of Fotor. Linework fell to 0.0151 and is
still 1.4x the photograph's, so the floor holds.

### Booru pose tags work, and the evidence is the subject that prompted them

`00050`'s pose was prose: *"sitting on a step, legs bent to one side, one arm resting on knee, other arm
behind, leaning back"*, and N3 rendered her upright with her legs down the steps. Rewritten as `sitting,
on stairs, knee up, hand on own knee, arm support, leaning back` — six tags the base was trained on —
**N8 reproduces the photograph's pose, arm support and all.** The single clearest prompt win in either
round.

### The gaze tag worked

`00003` was the subject whose eyes looked the wrong way, and its sheet now carries `looking at viewer`.
**The operator, comparing against the photograph: the render looks straight back at him, as the
photograph does.** The natural experiment that motivated the field survives its first deliberate test.

**This finding's first draft recorded the opposite**, from the assistant reading the render alone and
judging the irises still off-axis. It was wrong, and on gaze — as on identity in F24 — the operator
comparing against the photograph is the instrument this project has. Two axis corrections in this
finding, and both went the same way.

What the combined run still cannot settle is the *strength* of the lever: N8 moved cfg 7 → 5 in the same
render, and lower cfg weakens every tag. The tag worked **at a weakened setting**, which is a stronger
result than it looks, but the separated arm — same sheets, cfg 7 against cfg 5 — is the one that would
say by how much.

### Also unfixed, and now on their third recording

Skin still renders darker than the tag on the subjects that declare fair, and **age still renders young**
— `00003` reads early teens against `young woman` at cfg 5 as it did at cfg 7 and as it did under a 1.4
emphasis in N6. Three settings, one result: **weighting and re-wording do not move the base's age prior.**
Whatever fixes it is not in the prompt.

### One session was wasted, and it is recorded rather than netted out

The first pod of this pair came up `RUNNING` with `runtime: null` and no public IP — RunPod's SSH proxy
only, which is a restricted shell and will not carry a port forward. `infra/up.sh` polls for
`publicIp` and a mapped `:22`, so it waited seven minutes for something that was never coming, and the
pod billed for all of it. Terminated, confirmed empty, and recreated; the second pod had direct SSH and
the whole run took **three minutes**.

**`up.sh` has no timeout on that poll.** It is the one piece of infrastructure in this repository that
can bill indefinitely while looking like it is working.

---

## F27 — InstantID was suppressing the style, and dropping it clears the bar

**2026-09-08 · one pod session, 18:58–19:13, 14 minutes, ~$0.10 · 4 arms x 6 subjects = 24 renders ·
`prototype/renders/n9_ablation/` · `prototype/ablation.py`.**

**The operator's hypothesis**, after N8 showed booru tags carrying pose and gaze on their own: *are
InstantID and OpenPose now fighting the prompt rather than helping it?* The prediction was written into
the runner before the pod was booted — if the legs fight, dropping them improves adherence; if they
carry, dropping them loses the pose and the face and the tags do not recover it.

**They fight. Overwhelmingly, and it is InstantID.**

| arm | posterisation ↑ | linework | linework spread |
|---|---:|---:|---:|
| the photograph | 0.413 | 0.0108 | 6.10x |
| N8 — both legs, sheets before enrichment | 0.332 | 0.0151 | 2.74x |
| **A** — both legs, enriched sheets | 0.358 | 0.0139 | 2.45x |
| **B** — **no InstantID**, OpenPose kept | **0.518** | 0.0316 | 2.34x |
| **C** — no OpenPose, InstantID kept | 0.371 | 0.0147 | 2.94x |
| **D** — **prompt only**, neither leg | **0.577** | 0.0320 | **2.09x** |
| **Fotor — the style bar** | **0.460** | 0.0404 | — |

**Removing InstantID moves posterisation 0.358 → 0.518, and clears Fotor's 0.460 for the first time in
either round.** Removing OpenPose instead moves it 0.358 → 0.371 — barely outside the determinism floor.
The two legs are not comparable forces: **one of them was most of the style deficit and the other is
nearly free.**

Linework more than doubles at the same time (0.0139 → 0.0316), which puts it within reach of Fotor's
0.0404 rather than 3x past the photograph's. Both axes move the same way, which is the first time in this
round they have agreed.

### Why this was invisible for two rounds

`ip_weight` and `cn_strength` were swept in N6 and the sweep found a ceiling and a free lever. **Neither
arm asked what the node costs when it is absent** — a ladder over a dial cannot find the dial's own floor.
It took the operator's architectural question to ask it, and the answer was larger than every dial result
in either round put together.

This also explains N6 in retrospect. `3_ip_1.5` had the **worst** posterisation of the seven arms at
0.241; `1_control` at 0.9 was second worst at 0.264. The whole `ip_weight` axis was ordered by *how much
InstantID was suppressing the register* — which is the same finding, seen from inside a range too narrow
to reach zero.

### The enrichment paid too, and it is separable

N8 → A is the operator's six prompt improvements with nothing else changed: background, midriff, precise
accessories, hair parting, the smile fix, and `medium breasts` for the age drift. **Posterisation
0.332 → 0.358, +8%**, and by eye every added tag lands — flower field, mountains and blue sky on `00003`,
the navel, the lace, the light smile.

**And `medium breasts` moved the age.** The drift that survived cfg 7, cfg 5 and a 1.4 emphasis on the age
tag itself is gone at `00003`, which now reads adult. Three attempts on the tag that names the thing all
failed; one attempt on a *body* tag worked. The operator proposed it.

### What is not settled, and it is the whole question

**These arms were not judged on identity.** B and D produce cleaner anime by both axes and by eye — and
booru has no vocabulary for *a particular face*. Two subjects with the same tags get the same face, and
that is precisely what dropping InstantID buys the style with.

`D` also changes what the product is: **nothing reads the photograph at render time.** `LoadImage` and
`ImageScale` are orphaned in that graph — 10 nodes, 8 reachable — and the render is reproducible from the
sheet alone. `photo -> anime` becomes `photo -> sheet -> anime`, where the photograph's only job is to be
read once, by a human.

**B is the interesting middle** and was not on the operator's list: the photograph still supplies the
skeleton, the face is left to the tags, and it clears the style bar anyway at 0.518. Whether its identity
is acceptable is a question only the eye answers.

### A seam held under pressure, and is worth recording

`pipeline.run` could not drive three of these four arms: its provenance record calls
`find_node(class_type="ApplyInstantIDAdvanced")`, whose exactly-one contract is violated by a graph that
has deliberately removed the node. **The contract was not weakened for a prototype** —
`ablation.py` submits directly and writes its own `arm.json` — because that seam is load-bearing in the
shipped path. The failure was loud, immediate, and cost one render.

---

## F28 — every tag that worked is a real Danbooru tag; every tag that failed is not

**2026-09-08 · $0, no pod · an audit of the six rendered sheets against the canonical Danbooru
vocabulary, prompted by the operator's own reference note.**

His note states the rule outright: *"A model only knows a tag if it appeared enough in training.
Rare/niche tags silently do nothing — prefer the canonical Danbooru wiki name over a synonym."* The
sheets were written before that note was consulted, and **74 distinct non-canonical tags** appear across
the six — roughly half of every prompt.

**Then the pattern.** Sorting the tag results of F26 and F27 by whether the tag exists on Danbooru:

| worked, and dramatically | canonical? | | failed, repeatedly | canonical? |
|---|:-:|---|---|:-:|
| `hand on own knee` | ✅ | | `centre part` — parting never landed | ❌ |
| `arm support` | ✅ | | `voluminous`, `tousled` — `00033`'s hair volume | ❌ |
| `knee up`, `leaning back` | ✅ | | `fair skin`, `light skin`, `tan skin` | ❌ |
| `looking at viewer` — fixed the gaze | ✅ | | `young woman` — age, three attempts | ❌ |
| `midriff`, `navel` | ✅ | | `blue-green eyes`, `hazel eyes` | ❌ |
| `medium breasts` — **fixed the age** | ✅ | | `natural eyebrows`, `defined eyebrows` | ❌ |
| `flower field`, `mountain`, `blue sky` | ✅ | | `chin-length wavy bob` | ❌ |
| `freckles` | ✅ | | `black sheer lace long robe` | ❌ |

**Not one exception in either column.** The three drifts this round could not fix — hair volume, skin
tone, and age — were each addressed with a tag the model has never seen; and the age drift fell the
moment it was attacked with `medium breasts`, which is canonical, after three failures against
`young woman`, which is not. The canonical alternatives exist and were simply not used: `pale skin`,
`dark skin`, `mature female`, `bob cut`, `parted bangs`.

This is not proof — nothing here is a controlled arm, and a non-canonical tag is not *inert*, it is
tokenised and contributes something. But it orders every tag result in two rounds without a
counter-example, and the fix costs one rewrite and no GPU.

### It is also the precondition for the evaluator

`CRITERIA.md` §1 made the sheet the ground truth, and §5 left six of the seven criteria unmeasured
pending a reader. **The natural reader is a WD14-class tagger** — an ONNX model that reads an image and
emits *Danbooru tags*, which is the same vocabulary the sheet is written in. Scoring becomes a set
comparison in one vocabulary rather than a translation between two.

**A tagger cannot score `blue-green eyes` or `black sheer lace long robe`, because it cannot emit
them.** So the tag question and the evaluation question are the same question, and canonicalising the
sheets is the first step of both.

---

## F29 — the criteria evaluator exists, and it says D wins. It also cannot see identity

**2026-09-08 · one pod session, 20:05–20:10, 5 minutes, ~$0.04, plus $0 of local scoring ·
`prototype/criteria_eval.py`, `prototype/renders/n12_canonical/`.**

The operator approved a WD14-class tagger and asked for the two kept flows scored across the seven
criteria. Sheets were canonicalised first (F28), then `A` and `D` re-rendered on them, then scored.

**The instrument.** `SmilingWolf/wd-swinv2-tagger-v3`, ONNX, Apache-2.0, pinned by digest in
`prototype/styles/wd14_models.json`. It reads an image and emits **Danbooru tags** — the vocabulary the
sheets are written in — so a score is a set comparison inside one vocabulary rather than a translation
between two. Per criterion: **recall against the sheet**, the share of declared tags the reader found.
Recall and not F1, because a render carrying extra true tags is not a fidelity failure.

`isekai.eval_models.resolve` refused the artifact, correctly, because it is not in the tracked
`eval_models.json`. **That refusal was not weakened**: the prototype verifies the same bytes against its
own manifest instead.

### The known-answer gate passed, and the mean hid most of the story

Floor stated before the run at **0.40**, deliberately low because the reader was trained on drawings and
a photograph is out of its distribution.

| | pose | gaze | hair sil. | hair col. | eye col. | clothes | marks | mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **the photographs** | **0.08** | 1.00 | **0.18** | 0.58 | 0.50 | 0.56 | **0.00** | **0.47** |

**Pass on the mean, and three columns are unreadable.** `pose`, `hair silhouette` and `marks` are near
zero *on the photographs the sheets were written from*. That is the reader being out of distribution
rather than the sheets being wrong — every one of those flows scores far higher on the renders below,
which are drawings. But it means **the pose column is the least trustworthy number in this finding**, and
pose is one of the two mandatory criteria.

### The scores

| | pose | gaze | hair sil. | hair col. | eye col. | clothes | marks | **mean** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **A · both legs** | 0.48 | 1.00 | 0.47 | 0.67 | **1.00** | 0.73 | 1.00 | 0.73 |
| **D · prompt only** | **0.54** | 1.00 | **0.62** | **0.75** | 0.83 | **0.87** | 1.00 | **0.77** |

**D wins on five of seven and on the mean.** `A` wins only on eye colour. Both are perfect on gaze and
marks — `looking at viewer` and `freckles` land every time.

**And D follows the pose tags better than the flow with OpenPose in it.** 0.54 against 0.48, on the
column that is least trustworthy, but pointing the same way F27 did: the legs compete with the tags
rather than reinforcing them.

### What this scoreboard cannot see, and it is the thing the project is named for

**These numbers measure adherence to a description. They cannot measure whether the render is the same
person.** A flow that draws a well-executed generic woman matching every tag scores 1.00. `CRITERIA.md`
§1 accepted that trade knowingly — it is what killed F16's inverted metric — and here is the bill.

So **F29 does not overturn the operator's verdict that `A` is the better flow.** He judged `A` on face
identity, comparing against the photographs; this instrument is blind to exactly that, and the one
column where `A` wins outright — eye colour, 1.00 against 0.83 — is the most face-adjacent criterion on
the sheet. The two readings are not in conflict; they are measuring different things, and only one of
them is measuring the product.

**This is F5's disease inverted.** Round 1 instrumented only similarity-to-photograph and nothing
measured style, so the least-stylized render won by construction. Round 2 now instruments only
adherence-to-description, and **the flow that ignores the photograph entirely wins by construction.**
Both scoreboards were complete on their own terms and both were missing the same axis: nothing here has
ever measured *is this the same person* in a way that survives stylization.

That axis is still open, and it is the honest next problem.

---

## F30 — a contact sheet showed the same image in two columns for two sessions

**2026-09-08 · $0 · caught by the operator, not by the tool.**

`contact_sheet.py` named each thumbnail `<subject>_<render.parent.parent.name>` — the arm directory. That
is unique **within** one run and not **across** runs, so `n9_ablation/1_full` and `n12_canonical/1_full`
both wrote `00003_1_full.jpg`. The second overwrote the first, and the before-and-after sheet showed
**the same picture in both columns** while its click-through links pointed at the two genuinely different
renders.

The renders were never wrong (`26418fb9…` against `45b38f95…`); only the picture of them was. And the
failure mode is the worst shape a comparison tool has: **it silently answers "no difference" to the exact
question it was built to ask.** A sheet built to show whether the canonical rewrite changed anything
reported that it changed nothing.

Fixed by naming from the whole path below `renders/`, and every sheet now carries a check: 102 images
across four sheets, 102 distinct files, zero byte-identical pairs.

**Worth recording beyond the bug.** F26, F27 and F29 all turned on the operator reading a contact sheet,
and this one was reading back a stale file for two of its columns. The instrument that has caught three
broken axes needed catching itself, and the thing that caught it was a person noticing two columns that
should have differed did not.

---

## F31 — a datacenter stopped issuing public IPs, and the pinned GPU exists in two places

**2026-09-08 evening · no renders · roughly $0.26 of pods that could not be used.**

Five pod sessions worked during the day. From about 21:20 every pod in **EU-RO-1** came up `RUNNING` with
`runtime: null` and `ssh.direct: null` — **no public IP, only RunPod's SSH proxy**, which is a restricted
shell that cannot carry the `-L 8188` forward this pipeline is built on.

```
  15:05 ✅   15:34 ✅   16:32 ❌   16:41 ✅   18:58 ✅   20:05 ✅
  ────────────────────────────────────────────────────────────────
  21:20 ❌   21:25 ❌   21:28 ❌   21:32 ❌   21:47 ❌
```

**Nothing on our side changed.** Same `.env`, same `:latest` image, same GPU, and no client change between the interleaved successes and failures. The one
mid-day failure at 16:32 had the identical signature and succeeded on immediate retry; by 21:20 it was
every attempt. Consistent with a **public-IP pool exhausting** rather than GPU scarcity — the two are
separate pools, and the GPU still reported `MEDIUM` stock throughout, which is why pods created
successfully and then arrived unreachable.

`create-pod` has **no parameter to request a public IP.** It is a property of whichever host you land on,
so there is nothing to ask for and nothing to retry differently.

### It is not just us, and there is no incident to wait on

RunPod's status page records **no incident for EU-RO-1** that day; the nearest entry is an SSH Proxy and
Serverless degradation on **5–6 September**, a different component three days earlier.

But a published case study of **2026-08-20** reports the same shape independently: **eight bounded GPU
launches, six of which never produced a verified public SSH/runtime endpoint** within their admission
window, across RTX 5090, Secure A40 and Secure A100 pools. Its author records that *"RunPod did not
provide us with provider-side telemetry establishing a root cause"* and classifies them as
**endpoint-admission failures**, unable to separate the daemon, the networking layer and the admission
path.

So: a known, reproducible, undiagnosed platform behaviour that RunPod does not track as an incident.
**Nothing is being fixed on a timeline we can watch**, which is why retrying is the correct response —
the failure is per-allocation, not per-datacenter, so each attempt is a fresh draw.

That case study proposes a **five-gate fail-closed readiness sequence**. Three of its gates — verify
*ready* separately from *running*, require a real TCP mapping to `:22`, and delete on a readiness
deadline — are what the `up.sh` fix below turned out to be, arrived at independently. The other two,
**pinning the SSH host key** and **health-checking the GPU before downloading models**, we do not have
anywhere. All five are carried in `.minions/v0.13_backlog.md` as **B1**, deferred to a version rather
than to this prototype. The gates are that author's proposal, **not official RunPod guidance**, and the
backlog entry says so.

### The fix that mattered: `up.sh` could bill forever

The IP poll was an **unbounded `while true`**. A pod that never gets an IP is never detected, so the
script waits and the meter runs — it looked like it was working. It is now bounded at 180s and **tears
the pod down itself** on timeout, because a bounded wait that leaves the meter running has not solved the
problem it was added for. That guard caught four of the five evening failures at ~3 minutes each instead
of at whatever the operator eventually noticed.

### And the constraint nobody had written down

`get-gpu-type` on the pinned card:

| datacenter | availability | STANDARD volumes? |
|---|---|---|
| **EU-RO-1** | MEDIUM | yes — our 80 GB volume is here |
| **EUR-IS-1** | LOW | yes |
| *everywhere else* | **none** | — |

**`NVIDIA RTX PRO 4500 Blackwell` exists in exactly two datacenters.** That is a single point of failure
nothing in this repository recorded, and it turns "just move datacenter" into a much smaller decision
than it sounds: there is one alternative, and it is `LOW`.

Two consequences, both now fixed in the tooling:

- **`RUNPOD_GPU_TYPE` accepts a comma-separated preference list**, and `up.sh` sends it as
  `gpuTypeIds`. RunPod places on whichever is available. Every entry must work with the image's cu128
  PyTorch — cu128 covers sm_80 through sm_120, so Ada and Ampere cards qualify; CLAUDE.md's constraint is
  that **cu124 fails on Blackwell**, not that the image is Blackwell-only.
- **Network volumes are datacenter-bound**, so the volume is what pins the location. Moving means a new
  volume and a full 16.5 GiB re-provision.

### A sequencing mistake, recorded because the order is the lesson

A 30 GB volume was created in **EU-NL-1** before checking whether the GPU existed there. It does not —
`create pod: could not find any pods with required specifications`, then `no instances currently
available` once the GPU list was widened. The volume was empty, was deleted within ten minutes, and cost
pennies.

**Check the destination has the compute before creating the storage that pins you to it.** The `probe`
rule already says *keep the old thing declared until the new one is proven*; what this adds is that
proving it starts with the cheapest read-only query, not with the first irreversible create.

---

## F32 — every prompt change the research argued for made the render worse

**2026-09-09 · one pod session, 08:39–08:55, ~$0.19 including the morning's failed allocations ·
5 arms x 6 subjects = 30 renders · `prototype/renders/n16_prompt/` · `prototype/prompt_arms.py`.**

`ILLUSTRIOUS.md` read the Illustrious paper and the community guides and ranked six prompt changes. Four
were testable as arms. **All four lost, and stacking them lost most.**

| arm | posterisation ↑ | linework | Δ vs baseline |
|---|---:|---:|---:|
| **`1_baseline`** — skin tags corrected, `worst detail` removed | **0.350** | 0.0165 | — |
| `2_negative` — the community Illustrious negative | 0.333 | 0.0171 | **−0.017** |
| `3_schema` — the paper's `rating` and `year modifier` slots | 0.339 | 0.0166 | **−0.012** |
| `4_underscore` — every tag in Danbooru's stored spelling | 0.338 | 0.0186 | **−0.013** |
| `5_all` — everything stacked | **0.329** | 0.0142 | **−0.021** |
| *N12, before the two definitional fixes* | 0.337 | — | −0.013 |

**These are 6x to 10x the determinism floor.** That floor had only ever been measured for linework
(±0.0003); it is established here for posterisation from the same cross-pod pair — **max |Δ| 0.0020,
median 0.0012** — so none of these effects is noise.

### The two definitional fixes were the only thing that helped

Baseline is N12 plus exactly two changes: `pale skin` → the correct tag per the Danbooru wiki, and
`worst detail` removed from the negative as a tag on no ladder and in no vocabulary. **That pair is worth
+0.013**, and it is the whole of this session's gain. Both were corrections of things that were *wrong*,
not attempts to be cleverer.

### Underscores: the operator's instinct, tested and falsified

He suspected Danbooru's stored spelling would work better, and `ILLUSTRIOUS.md` §4 could not settle it —
the paper's only relevant sentence is about the separator *between* tags, and the two community guides
contradict each other. **Measured: `long_hair` is 0.013 worse than `long hair`**, 6x the floor.

Not a large effect, and it is one base at one setting. But it is the answer that was asked for, and it
went the other way. **The guide recommending underscores is wrong for this model** — or at least for this
finetune, at these dials, on these prompts.

### The long negative is the biggest single loss, and that is the surprise

The community negative is *better sourced* than ours: it is built from `worst quality` and `bad quality`,
which are real rungs of the paper's trained ladder, plus `old` and `oldest`, which are real year
modifiers. Ours is WAI's short form. **The better-sourced negative renders worse by 0.017.**

The likely reason is token budget rather than vocabulary. Our prompts already sit at 59–93 estimated CLIP
tokens against a 77-token window; the long negative adds thirteen tags to the *negative* encoder, which
has the same window. **A negative that is more correct per-token can still be worse if it pushes the
whole conditioning past what the encoder holds.**

### `rating` and `year modifier` did not pay either — but this arm was malformed

These are the paper's own caption slots, unfilled by us until now, and `newest` was chosen specifically
because modern anime illustration is flatter and posterisation is the axis we are short on. **It moved
the wrong way, −0.012.**

> **Corrected by F34.** This arm bundled `general` with `newest` *and* placed `newest` at the very end,
> after the quality ladder. WAI's published string puts `newest` **inside** the ladder, at the front.
> Tested that way it is worth **+0.006**. The −0.012 here is real for what it tested; what it tested was
> not what the publisher recommends, and the arm design was the assistant's error. Whatever `newest` selects for in this finetune, it is not flatness.

### What this says about the method, which is the part worth keeping

`ILLUSTRIOUS.md` is good research and its central claim survived — **F28's canonical-vocabulary finding
is what the baseline's gain rests on.** But its §7 ranked six changes as "worth doing", and the four that
could be tested all lost.

**The difference between the two halves is that one fixed errors and the other pursued improvements.**
Correcting `pale skin` and deleting `worst detail` removed things that were demonstrably wrong. Adding a
longer negative, filling schema slots and re-spelling tags were all *plausible from documentation* and
none survived contact with the axis.

That is the third time this round a documented, reasonable-sounding prompt change has failed a
measurement — after the age tag at three settings (F26) and the `6_skin` emphasis arm (F25). **Prompt
folklore is cheap to generate and expensive to trust**, and the only reliable filter has been rendering
it.

**`1_baseline` is now the best-known configuration**, and it is the one with the fewest ideas in it.

---

## F33 — the pod blocker has a workaround: expose ComfyUI over HTTP, no public IP needed

**2026-09-09 · $0 beyond the session it was added in.**

F31 left us blocked: pods reach `RUNNING` with no public IP, and the SSH proxy cannot carry the
`-L 8188` forward the pipeline was built on. RunPod's support triage pointed at the answer — **an
HTTP-exposed port is served by their proxy and needs no public IP at all**:

```
  ports: ["22/tcp", "8188/http"]   ->   https://<pod id>-8188.proxy.runpod.net
```

`infra/up.sh` now requests both ports and polls for **either** a public IP **or** a working proxy,
taking whichever arrives first. The deadline moved 180s → 420s, because the IP check answers in seconds
while the proxy cannot answer until the image has pulled *and* ComfyUI has started.

Two details that are easy to get wrong and were:

- **`curl` needs `--fail`.** Without it curl exits 0 on the proxy's own 502 while ComfyUI is still
  starting, and the script announces a pod that cannot serve a render.
- **The jq body is single-quoted shell.** A comment containing an apostrophe (`RunPod's`) terminated the
  quote and broke pod creation before the API call — caught for free, at $0, because the failure was
  local.

### Amended 2026-09-09: the proxy does not work for our client

**This finding's first draft said the workaround works. It was verified with `curl` and never with a
render, and that gap is the whole error.**

```
curl  https://<pod>-8188.proxy.runpod.net/system_stats   ->  HTTP 200
a stdlib urllib client against the same URL             ->  Cloudflare error 1010
```

**1010 is a user-agent block.** The proxy sits behind Cloudflare, and both this repository's
`ComfyTransport` and `synthetic_portraits`'s transport are **stdlib `urllib` by design** — the
stdlib-only runtime rule is why — so both send `Python-urllib/3.x` and both are refused. `curl` passes.
Found when the portfolio run failed against a real pod on 2026-09-09.

So the fallback in `up.sh` **announces a pod it cannot actually drive**. The port exposure and the poll
are still right; what is missing is that the client cannot use the endpoint.

**The fix is one line and untested**: send a browser-like `User-Agent` on the transport's requests. It
adds no dependency. **It must be proven by an actual render, not by a status probe** — which is exactly
the mistake being corrected here.

Until then: **the proxy is a diagnostic channel, not a way in.** The SSH tunnel remains the only working
path, and the no-public-IP blocker of F31 is therefore **still open**.

### A second probe in this session proved nothing either

`GET /object_info/<NodeName>` returns **HTTP 200 for nodes that do not exist.** Three custom nodes were
checked that way on a pod that had none of them, and all three "passed". The real check fetches the full
`/object_info` and looks for the key. `check_graph` in the prototype runners is unaffected — it validates
the graph locally — but every pod-side node probe in these sessions was worthless.

**Both mistakes have the same shape: a cheap check that returns success for the wrong reason.**

### The cost of the workaround is a public endpoint

RunPod's docs are explicit: *"your service becomes publicly accessible"*, and *"the Pod ID provides only
obscurity, not security."* **ComfyUI has no authentication**, so for the pod's lifetime anyone holding
the id can drive it — submit graphs, read outputs, consume the GPU. An SSH tunnel was private to one
machine; this is not.

Acceptable here only because sessions are minutes long and torn down immediately, and because `up.sh`
prefers the tunnel whenever a public IP exists. **It is not a posture to leave running**, and a version
that adopts it should put authentication in front of ComfyUI first.

### It was not needed on first use, which is itself the finding

The session that added it drew a host **with** a public IP, at 08:39 UTC on 2026-09-09 — after eight
consecutive failures across two datacenters and two GPU pools. So EU-RO-1 either recovered or the
allocation got lucky, and **the underlying issue is unresolved and unexplained.** The proxy path stays as
a fallback that costs nothing when SSH works.

---

## F34 — the publisher was right about the ladder, and the earlier `newest` test was mine to get wrong

**2026-09-09 · one pod session, 12:25–12:34, ~$0.11 · 5 arms x 6 subjects = 30 renders ·
`prototype/renders/n18_position/` · `prototype/ladder_position.py`.**

`ILLUSTRIOUS.md` §6b found the sources disagree on where quality tags belong: the Illustrious community
guide says last, which is what we do; **WAI's own page says "always start your positive prompt with"**
them. This tests the publisher against the guide, on the publisher's checkpoint — and separates the two
changes F32 had bundled.

| arm | flow | posterisation ↑ | linework |
|---|---|---:|---:|
| `1_baseline` — quality tags last | A | 0.350 | 0.0165 |
| `2_front` — the same three tags moved to the front | A | **0.357** | 0.0150 |
| `3_wai` — + `newest`, the publisher's exact string | A | **0.363** | 0.0145 |
| `4_d_baseline` — quality tags last | **D** | **0.507** | 0.0280 |
| `5_d_wai` — publisher's string at the front | **D** | 0.503 | 0.0255 |
| *Fotor — the style bar* | | *0.460* | *0.0404* |

Against a determinism floor of **0.0020**:

- **Position alone: +0.007**, 3.5x the floor. **WAI's page beats the community guide on WAI's model.**
- **`newest` alone, correctly placed: +0.006**, 3x the floor.
- **Together: +0.013** — the first prompt *addition* to help since F28's definitional fixes.

### The `newest` result is a correction to F32, and the fault was in the arm

F32 concluded that all four documented prompt changes lost. Three of those stand. **The fourth does
not.** N16's `3_schema` arm put `newest` at the very end, after the ladder, bundled with a `general`
rating tag — and lost 0.012. Placed the way the publisher writes it, inside the ladder at the front, the
same tag **gains 0.006**.

**That was an arm-design error, not a property of the tag.** The lesson F32 drew — that
publisher-sourced corrections win where plausible additions lose — survives and is in fact strengthened:
this is a publisher-sourced correction, and it won. What needs amending is the claim that the change
itself was tested. It was not.

### Flow D does not want it, and does not need it

`5_d_wai` vs `4_d_baseline` is **−0.004**, about twice the floor and in the wrong direction — call it
neutral to mildly negative. **Flow D is already at 0.507, above Fotor's 0.460**, so there is no deficit
for the ladder to close there. The transform helps the flow that is short of the bar and does nothing for
the flow that has cleared it.

### The two flows, finally measured side by side on identical prompts

**D beats A by +0.156 on posterisation** — 0.507 against 0.350, on the same sheets, same seed, same
dials. That is the F27 result reproduced on canonical prompts and it is not close.

The standing summary is unchanged and worth restating because the numbers keep pointing one way while
the operator's eye points the other: **D is the flatter, more anime-looking render and A is the one that
preserves identity.** Neither axis in this repository can see identity, so the numbers will keep
preferring D. That is N14, still open.

### Where flow A now stands

`3_wai` at **0.363** is the best flow-A configuration measured, and still **21% short of Fotor's 0.460**.
Every documented prompt lever is now spent: F32 closed three, this closes the fourth, and
`ILLUSTRIOUS.md` §7 has nothing left that is a prompt change. **The remaining gap is structural** — the
hires pass WAI assumes and we have never run, or a style LoRA.

---

## F35 — the hires pass is the first thing to move both axes at once

**2026-09-09 · one pod session, 12:56–13:12, ~$0.20 · 3 arms x 6 subjects = 18 renders ·
`prototype/renders/n19_hires/` · `prototype/hires.py`.**

The last structural lever, and the publisher's own: *"Upscale with R-ESRGAN 4x+ Anime6B, 20 steps, and
a Denoising strength of 0.35~0.5"*. A second sampler pass over the upscaled first-pass render, at
**1024x1472 → 1.5x → 1536x2208**. The two no-hires references already existed at the identical prompt in
`n18_position` and were reused rather than re-rendered.

| | posterisation ↑ | linework ↑ |
|---|---:|---:|
| **A** no hires | 0.363 | 0.0145 |
| **A** hires 0.35 | 0.359 | **0.0208** |
| **A** hires 0.50 | **0.373** | 0.0181 |
| **D** no hires | 0.503 | 0.0255 |
| **D** hires 0.35 | **0.528** | **0.0376** |
| *Fotor — the bar* | *0.460* | *0.0404* |

- **Flow A:** posterisation −0.004 at denoise 0.35 and **+0.010** at 0.50; linework **+43%** and **+25%**.
- **Flow D:** **+0.025** posterisation and **+47%** linework, both far past the 0.0020 floor.

**`D` + hires is the closest anything in this project has come to Fotor on both axes at once** —
posterisation 0.528 *above* Fotor's 0.460, and linework 0.0376 at **93%** of its 0.0404.

### The measurement was nearly reported wrong, and the reason is worth keeping

The hires renders are **1536x2208**; every reference is **1024x1472**. Both style axes are
resolution-sensitive, and the first pass at these numbers read each image at its **native** size.

Re-read at the photograph's own canvas — which is what `style_axis.py` was built to do and what every
earlier number in this project used — **posterisation barely moved, and linework moved a great deal**:

| | native read | canvas read |
|---|---:|---:|
| A hires 0.35, linework | 0.0138 | **0.0208** |
| D hires 0.35, linework | 0.0284 | **0.0376** |

Read natively, hires looked like a **linework loss**. Read correctly, it is a **43–47% gain**. The sign
flipped. Posterisation was robust; linework was not, which makes sense — it counts pixels on a strong
luminance gradient, and that is a per-pixel quantity that changes when the pixel grid does.

**Nothing in the tooling caught this**, because `load_canvas_pixels` is a thing a caller has to choose to
use, and the quick measurement scripts written this session did not. Every comparison in this repository
that spans two resolutions is exposed to the same error.

### What this changes

`ILLUSTRIOUS.md` §7 listed the hires pass as the one remaining structural lever. **It paid**, and it is
the only change in two rounds to improve both axes together rather than trading one for the other.

Flow `A` at 0.373 is still **19% short of Fotor** on posterisation, and hires does not close that — its
gift to `A` is linework. Flow `D` no longer has a style deficit at all on these axes.

**The prompt is spent, the dials are spent, and the hires pass is now spent.** What is left is a style
LoRA — round 1's parked lever — or accepting that `A`'s register is what this architecture gives.

---

## F36 — the first real photographs, and `pale skin` bit twice

**2026-09-09 · one pod session, 14:16–14:21, ~$0.06 · 3 photographs x 2 arms = 6 renders ·
`prototype/renders/n21_real_photo/` · `prototype/real_photo.py`. Renders, sheets and photographs are all
gitignored (design.md D14).**

Every render in round 2 has been of a **synthetic** subject — SDXL-generated, evenly lit, frontal, one
face, no lens. The product's input is a phone photograph. This is the first time the settled flow met one:
flow `A` exactly as F34 and F35 left it, with and without the hires pass at denoise 0.50.

**Three photographs of one person, three sheets** — and a case no synthetic posed: **the hair colour
differs between them.** `real_photo_3` is blonde, the other two brown, months apart. Each sheet describes *its
own photograph* rather than the person, which is what `CRITERIA.md` §1 means by the sheet being the
ground truth, and is why the per-photograph sheet is the right unit rather than a per-person one.

### What carried

Pose, framing, garment, accessories and background all land. The lace-up corset, the pearl necklace, the
crossed arms, the beach at sunset, the raised arm — all present. `nose piercing`, a one-tag identity
signature of exactly the kind F28 predicts works, renders clearly on `real_photo_2`. Tattoo **presence**
appears on the arm, with the design wrong, exactly as F23 said it would be.

### What did not, and one cause repeats

**`pale skin` produced chalk-white, waxy skin on all three.** This is the *same mistake* `ILLUSTRIOUS.md`
§6 corrected for the synthetics: the Danbooru wiki defines `pale skin` as *"significantly lighter than the
usual Eurasian skintone, or skin which appears 'bleached'"*. The subject is fair, not bleached. **The
right tag is no skin tag at all** — Danbooru's default *is* the usual Eurasian tone, and every skin tag is
a deviation from it.

That correction was made, written down, and then not applied when the next sheets were written. **A
finding recorded in a note is not a finding applied to the next artifact.**

**`messy hair` overshot the same way.** It produced wild, windswept, near-vertical hair against a
photograph with calm hair. `messy hair` is canonical, but it is stronger than the thing being described;
`wavy hair` alone was the honest tag.

**`indoors` alone under-specified the background** on `real_photo_2` and the model invented a flat green door.
An unfilled slot is filled by the base — the argument that earned `gaze` its own field, appearing again in
a field that *was* filled, just not enough.

**And the face does not read as her.** That is the one thing no tag can fix and no axis here can measure —
N14, unchanged. The renders are of a person matching the description, which is what this architecture
builds.

### The honest read

**A real photograph is harder than a synthetic one**, and the gap is not in the flow — it is in the
sheet. Every failure above is a transcription defect: a tag too strong, a tag that should have been
absent, a field left thin. The synthetics were easy partly because *the assistant wrote both the subject
and its description*, from images generated to be frontal and evenly lit.

### The fixes were applied and all three landed — second session, 14:29–14:38, ~$0.10

Three edits, no dial touched: **`pale skin` removed from all three sheets**, **`messy hair` → dropped in
favour of `wavy hair` alone**, and **`real_photo_2`'s background filled out** to `indoors, kitchen, wooden
wall`. Then both kept flows rendered, with and without hires — 12 renders. The pre-fix set is kept at
`ladder/n21_real_photo_v1/` so the contact sheet can show before against after.

**Every one worked by eye.** The chalk skin is gone and the render reads as fair rather than bleached;
the hair is a calm wavy bob instead of a windswept explosion; the invented green door is replaced by the
kitchen the photograph actually has, with the wooden wall and the units in it. The corset's lacing, the
pearl necklace, the nose piercing and the arm tattoo's presence all survive.

**The flow was never the problem.** Three transcription defects produced three visible failures, and
correcting the transcription corrected all three — on the first attempt, at the cost of one pod session
and no change to any dial. That is the strongest evidence yet for `CRITERIA.md` §1's central bet: with
the sheet as the ground truth, **most of what looks like a model failure is a description failure**, and
description failures are free to fix.

**What did not change is the face.** It is a well-executed anime face carrying the declared attributes,
and it is not recognisably hers. No tag fixes that and no axis here measures it — N14, unchanged, and now
demonstrated on a real subject rather than a synthetic one.

---

## F37 — identity is measurable after all, once you stop asking how similar and start asking which one

**2026-09-10 · $0, no pod · 6 subjects × 5 arms = 30 renders, all already on disk ·
`prototype/face_likeness.py` · run at `prototype/evaluations/2026-09-10/t1_face_likeness/` ·
method written up in `IDENTITY.md`.**

**N14 has been open since round 1 and this closes the measurement half of it.** Two scoreboards existed.
F4/F16: a cosine to the photograph falls as stylization rises, so its optimum is the input image. F29:
adherence-to-description is stylization-invariant but blind to identity, which is why the flow that never
reads the photograph scored *above* the flow that does, 0.77 to 0.73. Both complete on their own terms,
both missing the same axis.

**The fix is not a better metric, it is a different question.** Not *how similar is this render to its
photograph* — an absolute score stylization poisons — but **given this render, which of the six
photographs did it come from**. Every candidate in that comparison is equally stylized, so a metric that
merely punishes stylization pushes all six numbers down and leaves the *ranking* untouched. Chance is
1/6 = 16.7%, stated before the run.

| arm | flow | top-1 | mean margin | exact p |
|---|---|---:|---:|---:|
| no hires | **A** | 4/6 | +0.0180 | 0.0087 |
| hires 0.35 | **A** | **5/6** | **+0.0485** | **0.0007** |
| hires 0.50 | **A** | 4/6 | +0.0273 | 0.0087 |
| no hires | **D** | 2/6 | **−0.0625** | 0.2632 |
| hires 0.35 | **D** | 2/6 | **−0.0472** | 0.2632 |

**Flow `A` carries identity.** Positive margin in every arm, p as low as 0.0007.

**Flow `D` is guessing, and the margin says it more clearly than the hit count.** 2/6 reads as "twice
chance" and is what guessing produces 26% of the time. But `D`'s mean margin is **negative** — averaged
over subjects the wrong photograph out-scores the right one — and **three of its six correct-cosines are
negative outright**. That is not a weak match, it is a wrong one. `D` renders a person who fits the
description; it does not render *this* person. Which is what `D` is for, now stated as a number.

**The absolute cosines are low and must never be read as grades.** Same-person photographs score 0.4–0.7
on this recognizer; photo→its-own-render runs **0.10–0.30**, and photo→someone-else's runs 0.07–0.21. Read
absolutely, 0.25 is a poor match and the honest conclusion is "identity lost" — which is exactly the
conclusion F4 reached. **Only the ordering survives the domain gap**, and `00014` won its rank by 0.0097.

**The circularity is real and it is asymmetric — this is the part to carry.** `glintr100` is the encoder
InstantID injects with, so `A` is being marked by its own examiner. `D` never touches it. Therefore
**`D`'s failure is clean evidence and `A`'s success is an upper bound**: `A − D` is the most InstantID
could be worth, not an estimate of what it is worth. Removing that needs a second recognizer the pipeline
was never trained against, and that has not been done.

**Free secondary result, and it feeds N28:** the hires pass does not cost identity. `A` + hires 0.35 is
the best arm in the table. One subject of difference at N=6, so the size means nothing — but the
direction contradicts the worry that a second sampler pass washes the face out.

**And a defect this run caught in itself.** The first execution reported "cosine" margins of **±21**,
impossible for a quantity bounded by ±1. `ArcFaceEncoder`'s docstring claims a unit-normalised embedding
and the ONNX head does not emit one — raw features measure L2 ≈ 16–18 — so the dot product was ranking by
vector *magnitude* as much as by direction. Fixed by calling `isekai.evaluate.cosine`, which normalises
both sides itself; the shipped code is correct and only that docstring overclaims. **The tell was a
number outside its own possible range, not a wrong-looking answer** — had the magnitudes happened to sit
near 1, this would have shipped silently.

**Limits, stated with the result.** Six subjects, all of them the set every dial was tuned on. It
measures the *face* — hair silhouette, proportion, marks and pose are part of "the same person" and none
is in this number. Untested on held-out subjects (N29) and on photographs of real people.

---

## F38 — the skeleton and the tags complement each other, and it takes two measures to see it

**2026-09-10 · one pod session, 30 renders, ~$0.17 · `prototype/pose_ablation.py` ·
`prototype/renders/2026-09-10/n25_pose/` · scored $0 on CPU by
`prototype/pose_geometry.py`. Teardown confirmed by the RunPod MCP: zero pods.**

**N25 asked whether flow `A` needs pose tags at all.** It places the body twice --
a DWPose skeleton conditions the render, and the sheet's `pose` field says the
same thing in Danbooru tags -- and F27 had established that the legs compete with
the tags, so a tag the skeleton already carries is paid for in style. Ten
deliberately varied poses, three arms, one variable: the `pose` field, dropped
from the **prompt** and never from the sheet.

**The answer is keep both.** They are not redundant and they are not fighting:

| arm | PCK ↑ | joint-angle error ↓ |
|---|---:|---:|
| `1_a_control` — tags + skeleton | **0.821** | **9.4°** |
| `2_a_no_pose` — skeleton alone | 0.801 | 12.6° |
| `3_d` — tags alone, no skeleton | 0.218 | 15.9° |

**The skeleton places the body; the tags disambiguate the limbs it gets wrong.**
`arms_up` is the worked example and it is not marginal -- without the tags the
model drops an arm the photograph holds behind the head:

    2_a_no_pose   r_shoulder off by 124.2°     1_a_control   r_shoulder off by 13.0°
                  r_elbow    off by 107.1°                   r_elbow    off by  6.5°

That is a *different pose*, not a displaced one, which is precisely the
distinction the second measure exists to make.

### It takes two measures, and `D` is the proof

**PCK alone would have repeated F4's mistake in a new place.** An anime figure has
different proportions from a photograph -- longer legs, smaller head -- so a
perfect pose match still displaces every keypoint, and a position score penalises
correct stylization. Joint angles are proportion-invariant: longer legs held the
same way have the same knee angle.

**But angles alone are just as wrong, and `3_d` shows both failures at once.** Its
PCK is **0.218** -- catastrophic, because with no skeleton the body lands anywhere
in frame -- while its angle error is 15.9°, not far off the arms that have one.
`D` renders a *plausible body in the wrong place*. On `sitting_on_knees` the same
thing inverts: `D` scores the **best angle error of any arm (9.3°) at a PCK of
0.000**. Nothing landed where it should, and reading angles alone there would have
produced a confident wrong answer.

**Angles describe the configuration, PCK describes the placement, and neither
alone can say what the other says.**

### The ordering is the methodological point

**The operator judged the contact sheet before this instrument existed**, and named
six subjects where the control wins. That expectation was written into
`pose_geometry.py`'s docstring *before* it was run, with the rule stated: if the
instrument ranks the ablation above the control, the instrument is wrong.

It agreed on five of six. The sixth, `arms_on_hips_legs_wide`, disagreed --
instrument 9.6° for the ablation against 17.3° for the control -- and the
per-joint detail explained it rather than excusing it: the control's **left elbow
is off by 65.9°** while everything else lands well. The eye was reading silhouette
and stance; the instrument weights eight joints equally. **The operator reviewed
that and agreed with the instrument**, which is the first time in this project a
measurement has corrected the eye rather than the other way round -- and it only
counts because the expectation was recorded first.

### Carried

- **Flow `A` keeps its pose tags.** The `pose` field stays in the prompt. The
  ablation block stays in every sheet, because it is what makes this reproducible.
- **`framing` was held constant in every arm** and is still untested. `full body`
  is on all ten sheets, so it explained nothing here; whether DWPose carries the
  crop is a real question and a separate one.
- **`legs_crossed` is the worst subject for every arm** (0.562 PCK, 19.6–23.2°).
  A floor-sitting, self-occluding pose is where DWPose itself is least certain, so
  part of that number is the instrument rather than the render.
- **The pose set doubles as a labelled dataset.** Ten filenames are ten pose
  labels, which is what made this cost nothing beyond the renders.

---

## F39 — flow `A` takes the hires pass, and at 0.35 rather than the 0.50 that was settled

**2026-09-10 · one pod session, 10 renders, ~$0.10 · `prototype/pose_ablation.py --only
4_a_hires_035` · teardown confirmed by the RunPod MCP: zero pods. Scored $0 on CPU.**

**Two thirds of N28 were already answered and nobody had noticed**, because the axes were measured in
different sessions and never put in one table. F35 had the style numbers, F37 the identification
numbers, and F38's scorer could be run on F35's own renders for nothing. Doing that first is what made
the pod session ten renders instead of thirty.

### The pair, on ten hard poses

`1_a_control` from N25 is the control -- identical seed, prompt and dials, already on disk -- so this
session rendered only the hires half and the pair differs by the second sampler pass alone.

| axis | control | + hires 0.35 | Δ | floor |
|---|---:|---:|---:|---|
| linework ↑ | 0.0112 | **0.0133** | **+18%** | ±0.0003 |
| posterisation ↑ | 0.8261 | 0.8214 | −0.0047 | ±0.0020 |
| pose · angle error ↓ | 9.4° | **8.7°** | −0.7° | — |
| pose · PCK ↑ | 0.821 | **0.830** | +0.009 | — |

**The hypothesis this session existed to test is falsified, and that is the result.** Scoring F35's six
subjects on the pose instrument had shown hires costing nothing on five and a great deal on one --
`00050`, the hardest pose in that set, 38.7° to 57.0°. The question was whether hires degrades poses
that are already hard. **On ten hard poses it does not; it marginally improves them**, and the one
subject that moved meaningfully moved the *right* way: `sitting_on_knees`, 16.2° → 10.2°. `00050` was an
outlier, not a pattern.

### The denoise, and a settled value that was settled on one axis

**`A`'s hires denoise changes from 0.50 to 0.35.** The old value came from F35, which measured style and
nothing else, because neither identity instrument existed yet. With all four axes:

| | linework | posterisation | face id | pose |
|---|---|---|---|---|
| **0.35** | **+43%** | −0.004 | **5/6** | **ties no-hires** |
| 0.50 | +25% | **+0.010** | 4/6 | −1.0° |

**0.50 wins one axis by 0.014 and loses three.** That it survived as the settled value for a day is the
ordinary way a number outlives its evidence: it was correct when chosen, the evidence base widened
underneath it, and nothing re-read it. **A settled value is settled against the axes that existed when
it was set.**

### Carried

- **Posterisation reads ~0.82 here against F35's ~0.36**, and the two are not comparable. These subjects
  stand on plain grey studio backdrops, so a large share of every frame sits in a handful of colour
  bins. **The delta is comparable; the absolute value is not.** Any future run that mixes backdrops
  needs this said again.
- **`legs_crossed` is the worst subject for both arms and unchanged by hires** (19.6°). A self-occluding
  floor pose is where DWPose is least certain of its own keypoints, so part of that number is the
  instrument.
- **The free-measurement-first habit paid twice today.** Both N28's scope and its denoise decision came
  out of scoring renders that already existed. Neither needed a pod, and the pod that was booted asked a
  question the existing data had raised rather than one it had already answered.

---

## F40 — the flow generalises: better on held-out faces than on the ones it was tuned on

**2026-09-10 · one pod session, 20 renders, ~$0.18 · `prototype/portfolio.py` ·
`prototype/renders/2026-09-10/n29_portfolio/` · teardown confirmed by the RunPod MCP: zero pods.
Scored $0 on CPU.**

**Every number in this project before today came from subjects every dial was chosen on.** Ten synthetic
portraits and six baselines, tuned across two rounds. Whether that generalised or was fitted to those
faces was unanswerable, and it is the question a prototype most owes its reader. These ten portraits are
the first inputs the flow had never seen, and the flow ran **as decided** -- no sweep, no variable moved.

### It generalises, and the identity number went UP

| | tuned-on six (F37) | **held-out ten** |
|---|---|---|
| chance | 1/6 = 16.7% | 1/10 = 10.0% |
| flow `A` top-1 | 5/6 | **8/10** |
| flow `A` mean margin | +0.0485 | **+0.1170** |
| p | 0.0007 | **0.0000** |

**The margin more than doubled against a harder chance floor.** Two rounds of tuning did not fit ten
faces.

**The two misses are the failure mode already on record.** `15_01` and `16_01` are the only full-body
shots, so the face is a small fraction of frame -- and both were confused with the same wrong subject.
That is `00059`'s small-face problem from round 2, reappearing unchanged on new data. **A limit that
reproduces is a property; one that appears once is noise.**

### The sharpest single result: `14_00`, where the vocabulary could not say it and the embedding could

The set carries four attributes the tuned-on ten never had -- **age** (grey hair, visible lines),
**dark skin**, **eyewear**, and a **male** subject. Three predictions were recorded before the render:

| prediction | outcome |
|---|---|
| `14_00` loses the age -- `grey hair` is a *fantasy hair colour* on Danbooru (529,760 posts) meaning silver-haired character, not older person | **half right, and the half is the finding** |
| `10_01`'s cornrows simplify -- `cornrows` is not in the vocabulary at all | **right**, both flows rendered a single side braid |
| the tight headshots render wider than the photograph | **wrong**, framing held |

**Flow `D` rendered `14_00` as a young silver-haired anime woman. Flow `A` kept the age.** The tags were
identical -- `mature female`, `wrinkled skin`, `grey hair` -- so the difference is entirely the face
embedding. **The Danbooru vocabulary cannot express "this older woman"; InstantID carried what the tags
could not.** That is the clearest demonstration in either round of why flow `A` exists rather than `D`.

### Pose: mostly inconclusive here, and the reason was predicted

| | `A` | `D` |
|---|---:|---:|
| PCK | **0.771** | 0.142 |
| joint-angle error | 19.8° **(n=2)** | 15.0° (n=2) |

**Eight of the ten produced no joint angles at all.** They are headshots; DWPose has no elbow, hip or
knee to read and dropped 10 of 17 keypoints on each. `15_01` and `16_01` are the only full-body
subjects, so the angle column is n=2 and nothing should be drawn from it.

**PCK still separates, and cleanly**, because it scored the seven head-and-shoulder keypoints that were
visible: `A` runs 0.647–0.875 on every subject while **`D` scores 0.000 on six of ten**. The head lands
where the photograph put it under `A` and nowhere near it under `D`.

This was written into the runner's docstring before the render rather than explained afterwards. **An
instrument that cannot see enough to answer is a result; silence is not.**

### A confound this set introduces into the identification test itself

**`D` scored 4/10 with p = 0.0128 -- significant on hit count -- while its mean margin is negative.** The
four it got are `02_00` (red hair and freckles), `06_01` (black bob), `08_00` (black pixie) and `19_01`
(the man): the subjects whose *sheet* is most demographically distinctive within this set. On round 2's
six similar young women `D` scored 2/6 with a negative margin, which is noise.

**A demographically diverse set lets a description-only flow be matched back by attributes rather than by
face**, and that inflates `D` without any identity being preserved. It is a property of the test set, not
of the flow. **Any future run on a diverse set has to expect it**, and the negative margin is what
exposes it -- another case where reporting one number would have produced a confident wrong answer.

### Carried

- **Flow `A` is validated end to end**: every dial chosen by measurement, the whole configuration then
  confirmed on inputs none of it was chosen against, across a demographic range round 2 never covered.
- **`A`'s number remains an upper bound** until an independent recognizer exists -- `glintr100` is the
  encoder InstantID optimises against. `D`'s is clean, which is the only remaining reason to render it.
- **The small-face limit is real and reproducible.** Full-body framing costs identity, in both rounds and
  on both subject sets.

---

<!-- next: F41 -->
