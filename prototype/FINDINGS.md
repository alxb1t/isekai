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
`prototype/out/gallery_notile_d045.png`.

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

<!-- next: F15 -->
