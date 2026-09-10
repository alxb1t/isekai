# Identity criteria — what we extract, what we score, and what neither

**Round 2's design note. Written 2026-09-08, before any render.** It settles the question
[`README.md`](../README.md) left open under *"What round 2 changes downstream"*: if the photograph never
enters the latent, what does "the same person" even mean, and what reads it back out.

Read [`archive/SUMMARY.md`](../archive/SUMMARY.md) first. This note assumes its eleven findings, and in particular #2 and
#3 — the metrics were inverted, and only one side of the trade-off was instrumented.

---

## 1. The pivot: the sheet is the ground truth, not the photograph

Round 2 hand-writes a description of each subject. That is not merely a convenience to remove the
tagger as a variable — it **relocates the ground truth**.

```
   round 1     photo ──────────────────────────────▶ render
                       the evaluator compared these two, pixel to pixel
                       └─▶ F16's disease: colour distance to a photograph
                           penalises correct stylization, so the flow that
                           stylizes least wins by construction

   round 2     photo ──▶ criteria sheet ──▶ prompt ──▶ render
                 │        (discrete text)                  │
                 └── a human reads ──┘                     │
                                     └── the evaluator compares these ──┘
                       "blue eyes" against "blue eyes" is register-free:
                       a drawing and a photograph can both be blue-eyed
```

**Decided 2026-09-08: the evaluator scores the render against the sheet.** Not against the photograph.

What this buys:

- **The inverted metric disappears at the root.** No ΔE to a photograph appears anywhere in the scored
  set, so a render is never punished for being flat, saturated or cel-shaded — the exact failure that
  made round 1's scoreboard a coin flip.
- **The broken shared-mask assumption stops mattering.** README warned that a from-noise render will not
  align to the photograph's pixel grid, so every region axis collapses. An attribute check needs no
  alignment: it needs to read the render, alone, and say what colour the hair is.
- **Refusals get cheap and honest.** An attribute the reader cannot find is *unread*, which is a third
  outcome and not a low score — the same discipline `Refusal` already enforces in `isekai/evaluate.py`.

What this costs, stated plainly so it is never quietly forgotten:

> **The scoreboard now measures prompt adherence, not identity.** Sheet and render agreeing proves the
> generator did what it was told. It proves the render resembles the person **only to the extent that the
> transcription was faithful.** The transcription is a human act, performed once, by eye, and it is not
> itself verified by anything. Every number below inherits that.

That trade is accepted for round 2 because round 2 is answering an architectural question — *does the
softness go when the photograph leaves the latent* — and a transcription error costs one subject, not
the verdict.

---

## 2. The sheet

Thirteen fields per subject. **All thirteen are written and all thirteen go into the prompt.** Only six
are scored; the rest are recorded because they shape the render and a reader needs them to interpret it.

| # | field | example | in prompt | scored |
|---|---|---|---|:-:|
| 1 | **framing** | `upper body`, `full body`, `portrait` | yes | — |
| 2 | **pose** | `sitting, on stairs, knee up, arm support` | yes | **✓** |
| 3 | **gaze** | `looking at viewer`, `looking to the side` | yes | **✓** |
| 4 | **hair silhouette** | `wavy bob, side part, hair over one eye` | yes | **✓** |
| 5 | **hair colour** | `blonde, dark roots` | yes | **✓** |
| 6 | **eye colour** | `blue eyes` | yes | **✓** |
| 7 | **clothes** | `white lace camisole, blue denim shorts` | yes | **✓** |
| 8 | **marks** | `freckles`, `mole under eye`, `glasses`, `tattoo on forearm` | yes | **✓** |
| 9 | **accessories** | `hoop earrings, black choker, heart necklace` | yes | — |
| 10 | **eyebrows** | `thick eyebrows` | yes | — |
| 11 | **age band** | `mature female`, `young woman` | yes | — |
| 12 | **skin / ancestry** | `tan skin`, `pale skin` | yes | — |
| 13 | **body shape** | `slim`, `athletic` | yes | — |
| 14 | **expression** | `light smile`, `closed-mouth smile` | yes | — |
| 15 | **background** | `outdoors, flower field, blue sky`, `simple background` | yes | — |

### Background is prompted and not scored, and those are different questions

Added 2026-09-08 on the operator's proposal. §3 dropped background from the *scored* set because
from-noise cannot preserve one — nothing survives from the photograph to compare against, so the axis
would measure nothing. **Prompting it is a different act.** A scene the model is told to draw is a scene
it draws; one it is not told about is one the base invents, which is the same argument that earned
`gaze` its field.

It is the most expensive field on the sheet in tokens, and the prompts were already past CLIP's 77-token
window before it was added — see the caution below.

### The token budget is now the binding constraint

Measured 2026-09-08, before the enrichment: the six rendered sheets ran **82 to 99** estimated CLIP
tokens against a **77-token window**, so every one of them was already being chunked and averaged by
ComfyUI. After the enrichment they run **80 to 111**.

**"Extract the maximum from the photograph" has a ceiling**, and this is where it is. Past the window
each additional tag pulls a little less, and the effect compounds with `cfg 5`, where every tag already
pulls less than it did at 7. That is not a reason to stop adding fields — it is a reason to expect
diminishing returns, to rank fields rather than only append them, and to read a disappointing render as
possibly a budget result rather than a bad tag.

### `1girl` is back, and only in the prototype

The shipped graph deleted `1girl` in v0.10 for a stated reason: the gender it asserted now comes from
InstantID's face embedding, a mechanism already in the graph, and v0.8's defect was closed by a
falsifiable check. **Flow `D` has no InstantID.** With no face embedding and no photograph in the latent,
nothing anchors the subject at all — and the operator's own reference note records that Danbooru
front-loads a count tag as *"the single strongest compositional anchor"*.

So the sheets lead with `1girl, solo`. **That is a prototype deviation, not a proposal for `main`**, and
if flow `A` is ever promoted the tag has to be re-argued against v0.10's evidence rather than inherited
from here.

### The quality string leads, in the publisher's exact form

**Adopted 2026-09-09 on the measurement in F34**, and on the operator's eye: *"WAI's string indeed looks
very good on both A and D."* Every sheet's prompt now begins

```
masterpiece, best quality, amazing quality, newest, 1girl, solo, ...
```

Two sources disagreed. The Illustrious community guide puts quality tags last, which is what we did;
**WAI's own model page says to start the prompt with them**, and includes `newest` as the string's fourth
element. On WAI's checkpoint the publisher won, by **+0.013** posterisation — position worth +0.007 and
`newest` worth a further +0.006, both several times the determinism floor.

**It is applied to both flows even though it only measurably helps one.** Flow `D` came back −0.004,
inside the noise and in the wrong direction, because `D` already sits above the style bar and has no
deficit to close. The operator judged it good on both, and one prompt across both flows is worth more
than a marginal number.

### Every field is written in Danbooru vocabulary, not prose

Added 2026-09-08, after N6. `00050`'s pose read *"sitting on a step, legs bent to one side, one arm
resting on knee, other arm behind, leaning back"* — a sentence, aimed at a base trained on tags. It is now
`sitting, on stairs, knee up, hand on own knee, arm support, leaning back`: six tags the model has seen,
in place of one sentence it has not.

### Gaze earns a field because omitting it does not omit a gaze

**The operator's observation, 2026-09-08 — and there was already an experiment on disk to test it.** Two
of the six rendered sheets carried `looking at viewer` inside their pose field; four did not. Both tagged
subjects render looking at the viewer, and the complaint landed on `00003`, which had no gaze tag.
**Nothing invented its gaze; nothing told it one.**

An untagged criterion is not one the model leaves alone — it is one the base's prior fills in. That is a
different argument from the one behind every other field here, and it is why `gaze` is scored while
`expression`, which is equally constant across this set, is not.

**Gaze is constant across these ten inputs** — all are camera-facing portraits — so it cannot be
*validated as a discriminator* here. It is scored as adherence, which §1 makes every criterion anyway.

Fields 1, 2 and 3 fix the **canvas, composition and gaze**, all three of which from-noise will otherwise
invent. That is not identity, but pose PCK and any by-eye comparison both need it pinned.

### Why these seven are the scored set

Because each is either **machinery that already validated** or a **discrete check a reader can make on a
drawing without a photograph beside it** — and because between them they carry what the eye uses to say
*that's her*. Silhouette and pose first, then colour, then the small marks.

### Ancestry enters the sheet, as neutral descriptive tags

**Decided 2026-09-08.** `00050` and `00072` are visibly different phenotypes, and an anime base left to
itself renders one default face for both. InstantID encodes phenotype and is staying in the graph, but at
`denoise 1.0` its authority is untested — if it turns out weak, an unprompted sheet would leave us unable
to tell a weak adapter from an absent instruction. Neutral descriptive terms only (skin tone, hair, and
where it is genuinely descriptive, origin); booru's vocabulary here is crude in places and we are not
obliged to use all of it.

---

## 3. What was proposed and demoted, with the reason

The operator's opening list was ten items. Seven survive into the sheet unchanged; three are demoted out
of the scored set and one is added to it. Recorded so the demotions are not silently re-litigated.

| criterion | disposition | why |
|---|---|---|
| **face points** — eyes, nose, lips | sheet: no · prompt: no · scored: **no** | Carried by **mechanism**: InstantID's embedding and keypoints, which is where it belongs. There is no cheap axis for facial geometry on a drawing, and writing "almond eyes, straight nose" into a prompt is a weak lever pointed at a strong mechanism |
| **face angle** | folded into **pose** | OpenPose and InstantID's keypoints both carry it, and PCK already measures it. A separate axis would double-count one quantity |
| **face expression** | sheet **yes**, scored **no** | All ten synthetics are neutral model-face. Across *this* input set it discriminates nothing, so scoring it would add a column that is constant. Cheap to prompt, worthless to measure — here |
| **body shape** | sheet **yes**, scored **no** | Illustrious's prior toward idealised proportions overrides the tag. F12 already found idealisation in **4 of 10** renders. Scoring a criterion the base is known to overwrite measures the base, not the flow |
| **skin colour** | sheet **yes** (as *skin / ancestry*), scored **no** | Measurable, but only within one register — anime flattens skin, so distance to a photograph carries F16's disease. If it is ever scored it must be as an **ordering** across subjects, never as a distance to the input |
| **accessories** | sheet **yes**, scored **no** | **Not measurable today.** The `accessory_detail` proxy failed validation in F14, defeated by a bob falling into the ear zones. It is also the single thing that most separated the three flows in round 1 — so it is prompted, and judged **by eye**, and the gap is named rather than papered over |
| **background** | dropped entirely | From-noise cannot preserve a background. Measuring it would measure nothing |
| **hair silhouette** | **added, and scored** | Not in the opening list, which had length and colour. At anime scale the eye reads **silhouette first**: `00014`'s asymmetric wavy bob and `00035`'s short curls are each the recognisable thing about that subject, and "shoulder-length" describes both |
| **marks** — freckles, moles, tattoos, glasses | **added, and scored** | Highest identity signal per token in the whole sheet, and booru has exact tags. `00003` is unmistakably freckled and nothing in the opening list captured her |
| **eyebrows** · **age band** | **added**, sheet only | Age drift (adults rendering as teenagers) is the most identity-destroying failure anime bases have. Eyebrows are one tag and `00014` is defined by hers |

---

## 4. The bar, stated before the render

Round 2 now has **two** bars, and both are written down before any GPU is booted.

**The style bar — restated 2026-09-08, on the other axis.**

> **[Superseded 2026-09-10 — see `README.md` § *The style bar, restated*. The bar is now each flow's own
> last measured number, and the third-party reference is retired. Kept verbatim below because it was
> stated before its render.]**
>
> **Median posterisation at or above Fotor's 0.460.** Linework is a floor, not the target:
> `fromnoise-v1` already runs 3x the photograph's, and every arm the operator rejected in N6 had *more*
> of it than the two he chose.

The first version of this bar said *median linework at or above the photograph's own*, and it was
inherited from round 1 without being re-derived. **Round 1's failure was blur, so linework was its axis.
Round 2's failure is insufficient flatness** — and F24 said exactly that in the same breath as quoting the
wrong number. N6 settled it: ranked by posterisation the operator's two picks are 1st and 2nd of seven and
the arm he called worst is 7th; ranked by linework his favourite is **6th of seven**. Posterisation orders
his preference, linework does not. See F26.

**The identity bar**, decided 2026-09-08:

> **6 of the 7 scored criteria must survive, and pose and hair silhouette are mandatory.**
> One criterion may drift. A render that loses pose or hair silhouette fails regardless of its count,
> because those are what the eye reads first — a render that keeps clothes, colour, marks and eyes while
> inventing a new haircut is not the person, whatever the tally says.

The operator set this at **5 of 6**; 6 of 7 is that rule carried across the new `gaze` field
mechanically, at the same proportion, and not a second decision. A clean sweep was rejected as a bar: F12 and F18 both found eye colour drifting in *img2img*, where the
photograph was still in the latent. Demanding from noise what the stronger conditioning did not deliver
would produce a verdict of "failed" that teaches nothing.

A flow must clear **both** bars. Round 1's whole conclusion was that the operator's preference split the
two flows against their own numbers; a single-bar round 2 would walk straight back into that.

---

## 5. How the seven get read — and the gate on the reader

**Round 2 instruments one of the six and judges five by eye.** That is deliberate, and it mirrors
README's own reasoning about the tagger: *there is no point integrating a reader if the flow does not
render cleanly.*

| criterion | round 2 | round 2b, only if round 2 clears both bars |
|---|---|---|
| **pose** | **instrumented.** `DwPoseReader` PCK, photo against render. Validated in round 1, and the shared working resolution keeps the coordinates comparable | unchanged |
| **hair silhouette** | by eye | needs an anime hair mask. `SegformerParser` is photo-only by design (D7) and must not be pointed at a drawing |
| **hair colour** | by eye | as above — the colour machinery in `archive/hair_colour.py` exists; the *mask on the anime side* does not |
| **eye colour** | by eye | `AnimeFaceDetector` is already pinned and shipped; an iris sample inside its box is the cheapest real axis available |
| **clothes** | by eye | attribute read, not a mask |
| **marks** | by eye | attribute read |
| **gaze** | by eye | iris position inside `AnimeFaceDetector`'s box — cheapest of the seven |

### The instrument we should build, and what it must pass first

A sheet-based scoreboard wants an **attribute reader**: something handed the anime render alone that
returns the six fields as text, which is then compared to the sheet. That is register-free by
construction and needs no anime segmenter — it is the natural instrument for §1's pivot, and a VLM is the
obvious candidate.

**It does not get trusted on arrival.** Round 1's first finding was that an evaluator built before the
thing it judges came back a coin flip. So, before any reader's output is allowed into a table:

1. **A known-answer test on the photographs.** Point it at the ten synthetics — the images the sheet was
   written from — and compare its reading to the sheet. A reader that cannot recover the six fields from
   a *photograph* has no business being asked about a drawing.
2. **A stated agreement floor**, written before the test runs, not chosen after seeing the numbers.
3. **Refusal is a first-class outcome.** "I cannot see the eyes" is not "wrong eyes", and the report must
   distinguish them, as `Refusal` already does.

Adding a reader means adding a dependency. **Guardrails: argue for it and wait for approval before
installing.** Nothing here authorises that; this note only records what the reader would have to be.

---

## 6. Open, and honestly unresolved

- **The transcription is unverified.** §1's cost. A second person, or a second pass on a different day,
  would tell us how much of the score is the sheet's wobble. Not planned; named.
- **`hair_mask_area` is still broken** — it reports the photograph's own area, so every within-subject
  pair ties. Carried over from `0012:R3` and unfixed.
- **Accessory retention still has no measurement**, and it is still the axis that most separates the
  flows. F14 is the last word on it.
- **Whether InstantID has authority at `denoise 1.0`** is untested. If all six subjects come back with
  the same face despite the ancestry tags, that is the finding, and it is a bigger one than the blur.

---

## 7. What the graph edit actually is

Recorded here because [`README.md`](../README.md)'s **N1** overstates it. `workflows/animagine.json` does
not need recovering: the shipped graph becomes from-noise with **four edits**, and every node type
involved is already on the image.

```
  node  9   VAEEncode           ──▶  EmptyLatentImage   (the photograph leaves the latent)
  node 10   KSampler.denoise    ──▶  1.0
  node 14   ControlNetApply     ──▶  removed   (tile — conditions on the photo's appearance)
  node 21   ControlNetApply     ──▶  removed   (lineart — same)

  kept:  node  8  ApplyInstantIDAdvanced   ── the face
         node 18  ControlNetApply/DWPose   ── the skeleton
         node 22  ImageScale               ── the working resolution, so PCK stays comparable
         node 23  CLIPSetLastLayer         ── clip skip 2
```

Node 22 stays even though nothing samples the photograph any more: it is what fixes the canvas both
images are read at, and pose PCK needs that.

### The whole graph, as it stands

Seventeen nodes. `EmptyLatentImage` is the only thing that starts the image; everything the
photograph still touches enters as **conditioning**, never as pixels in the latent.

```
  the model lane               the photograph lane         the latent lane
  ──────────────               ───────────────────         ───────────────
  [1] CheckpointLoader         [2] LoadImage              [9] EmptyLatentImage
      waiIllustriousSDXL_v170       │                          1024 x 1472
   │ MODEL  │ CLIP  │ VAE           ▼                          batch 1
   │        │       │          [22] ImageScale                      │
   │        ▼       │          lanczos, short side 1024, /64        │
   │   [23] clip skip −2            │                               │
   │        ├─▶ [3] POSITIVE ◀ sheet├─▶ [8].image     the FACE      │
   │        └─▶ [4] negative ◀ sheet└─▶ [16] DWPreprocessor         │
   │             │      │                body+hand+face, 512        │
   │             │      │                 └─▶ [18].image  the POSE  │
   │             ▼      ▼                                           │
   └──────▶ [8] ApplyInstantIDAdvanced        ip 0.9 · cn 0.5       │
                 ▲ [5] ip-adapter.bin  ▲ [6] InsightFace (CPU)      │
                 ▲ [7] ControlNet instantid                         │
                 │                                                  │
                 ├─ MODEL ───────────────────────────┐              │
                 ▼ cond+ / cond−                     │              │
            [18] ControlNetApplyAdvanced             │              │
                 ▲ [17] ControlNet openpose          │              │
                 │ strength 0.6, 0% → 100%           │              │
                 ▼ cond+ / cond−                     ▼              ▼
            [10] KSampler ◀─────────────────────────┴──────────────┘
                 denoise 1.0 · cfg 7 · 28 steps · euler_ancestral / normal
                 │
                 ▼
            [11] VAEDecode ◀── VAE from [1]
                 │
                 ▼
            [12] SaveImage → fromnoise_*.png
```

Three details the picture is carrying that prose keeps losing:

- **`[8]` emits three things, and they go two ways.** Its `MODEL` runs straight to the sampler, while
  its two conditionings pass *through* `[18]`. The InstantID adapter is a model patch and a conditioning
  edit at once, which is why it cannot simply be reordered with the ControlNet leg.
- **`[22]` feeds two consumers and no sampler.** It is the last place the photograph exists as pixels.
- **`[3]` and `[4]` are both read from the sheet.** Nine sheets declare the shipped negative; `00059`
  declares one without `nsfw`. The negative is per subject precisely so that is visible here.
