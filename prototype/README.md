# Prototype — start here

**Branch `v0.13_prototype`. Does not merge.** A workshop for answering empirical questions cheaply
before a change is cut. Tuning by eye is allowed here and nowhere else: the rule that dials are settled
by numbers binds *versions*, and a branch that never merges settles nothing.

> **All seven notes live in [`notes/`](notes/)** — method, reference, plan and record, indexed in
> [`notes/README.md`](notes/README.md). This file stays at the root as the task list and its history.
>
> ### Reading order
> **Resuming cold on 2026-09-13? Jump to § *[Start here tomorrow](#start-here-tomorrow--2026-09-13)*** —
> it names the three documents to read, the plan, and what is actually open.
>
> 0. **[`notes/ARCHITECTURE.md`](notes/ARCHITECTURE.md)** — **the shape of the whole thing**, photograph to
>    anime image, in four stages: the abstract version, the open stack, the closed one, and where each
>    stage's ceiling is. Settled 2026-09-12
> 1. **[`notes/HANDOFF.md`](notes/HANDOFF.md)** — **start here in a fresh thread.** What exists now, the settled
>    configuration, the laws, and what is still open. This file is the ledger behind it.
> 2. **this file** — the task list and its history: every question asked, and what closed it
> 3. **[`notes/IDENTITY.md`](notes/IDENTITY.md)** — **how we know the anime image is the same person.** The
>    methodology, its proof, and the two traps that produced a wrong answer first. Written to be
>    exported
> 4. **[`notes/CRITERIA.md`](notes/CRITERIA.md)** — round 2's design: the sheet, the seven scored criteria, both bars
> 5. **[`notes/ILLUSTRIOUS.md`](notes/ILLUSTRIOUS.md)** — what the base was trained on, and what to prompt it with
> 6. **[`notes/FINDINGS.md`](notes/FINDINGS.md)** — F1–F41, the full evidence, newest at the bottom
> 7. **[`notes/READER.md`](notes/READER.md)** · **[`notes/JOYCAPTION.md`](notes/JOYCAPTION.md)** — who can
>    read a photograph into a sheet, and the plan for trialling the leading candidate. **Round 4, closed**
> 7b. **[`notes/ROUTER.md`](notes/ROUTER.md)** — **how prose becomes a sheet with an open model**: 0.033 →
>    0.482 across four configurations, and why the enum grammar was a trap
> 8. **[`archive/SUMMARY.md`](archive/SUMMARY.md)** — round 1's close: the flows compared, and what
>    not to retry
> 9. **[`archive/GPU.md`](archive/GPU.md)** — settled: keep the card, and a render is not where the
>    money goes

---

## Status: round 4 complete. JoyCaption is in the stack — as the describer, not the reader.

**2026-09-12 · 46 findings · 19 pod sessions · ≈$3.17 · every round-4 task closed but the UI.**
**The stack is open end to end, and identity now survives an encoder we did not train against.**
**It fails the 0.60 reader bar at 0.518 and is kept for the one thing it does reproducibly: see.**
Verdict and reasoning in § *[Round 4 closed](#round-4-closed--joycaption-fails-the-bar-it-was-given-and-earns-a-different-job)*.

```
  photo ─▶ VLM reads it into a 16-field criteria sheet ─▶ operator reviews
                                                              │
        InstantID (face) ─┐                                    │
        OpenPose (skeleton)├──▶ WAI-illustrious-SDXL ──▶ hires ─▶ anime image
        the sheet ─────────┘    cn 0.8 · cfg 5           0.35
```

**Every dial was chosen by measurement, then the whole configuration was confirmed twice over:** on ten
portraits no dial was tuned against (**F40**, 8/10 at chance 10%), and on **seventeen photographs of
real people** (**F41**, **14/17 at chance 5.9%** — the strongest result here, against its hardest floor).
The operator's eye agreed with the instrument on every one of the three runs.

**What made that sayable is the instrument round 3 built.** Identity had been the honest hole since round
1: one scoreboard rewarded not stylizing, the next was blind to identity entirely. The fix was not a
better metric but a different question — *given this render, which of the N photographs did it come
from* — which is stylization-invariant because every candidate is equally stylized.
**[`notes/IDENTITY.md`](notes/IDENTITY.md)** is that method, written to be exported.

**Two caveats stand, and neither is hidden.** `A`'s identity number is an **upper bound**, because the
recognizer is the one InstantID optimises against; `D`'s is clean, which is what makes the gap readable.
And **full-body framing costs identity** — a small face in frame, reproduced in three independent sets.

---

### Round 1's status, kept as history

**2026-09-07 · 23 findings · 8 pod sessions · ≈$1.80 · every task below closed.**

We set out to fix a pipeline whose renders lost identity, and to find out whether the fix was **dials or
architecture**. Two flows were taken end to end and **both were rejected.**

| flow | what it is | verdict |
|---|---|---|
| **`notile-d045`** | Illustrious img2img · tile ControlNet **off** · denoise **0.45** | **rejected — too soft.** Median linework **0.0030** across ten portraits, ~10x below its own inputs. Keeps garments and composition, loses **every accessory** |
| **`qwen-flatcel`** | Qwen-Image-Edit 2511 · Lightning · 8 steps, cfg 2.0 | **rejected — style disliked.** Preserves accessories, background and even tattoo *placement*, but at **0.065 linework — 1.6x Fotor's and 2.2x the photograph's.** "Bold lines" |

Both are recorded with scored baselines and stated style targets in [`styles/`](styles/). **Neither is
being promoted to `main`.** That is a legitimate outcome for a spike.

### Why each was rejected

**`notile-d045` is soft because of the architecture, not the tuning.** `decisions` §2 `i2i` seeds the
latent from the photograph at `denoise < 1`, so the sampler must reconcile a photographic latent with an
anime prior. The output is an *interpolation between them* — exactly what F7 measured and named
**off-axis**: as graduated as a photograph, with **fewer edges than either endpoint**. Blur is a failure
mode neither endpoint has, and no dial in the sweep removed it.

**`qwen-flatcel` preserves well and draws wrong.** It is the better architecture for preservation — F17
shows the two flows occupy **disjoint regions**, a reachability result rather than a trade-off — but its
register is not the one wanted. F15 showed the instruction is a weak lever; F21 showed the step schedule
cannot fix its 4.8x inconsistency either.

### The operator's preference split them against their own numbers

The style he liked belonged to the flow that loses identity. The identity he wanted belonged to the flow
whose style he disliked. **Neither available architecture delivers both halves** — and F22 argues the
thing that would is a **trained style adapter**, which is what Fotor has and what the open ecosystem
does not provide for this direction.

---

## Start here tomorrow — 2026-09-13

**Written 2026-09-12 at the end of the session, for a thread that has none of its context.**
Nothing is mid-flight: the RunPod account is empty (MCP-confirmed twice), every render is on local disk,
and the working tree is clean apart from the uncommitted work listed at the end of this section.

### Read these three, in this order

1. **[`notes/ARCHITECTURE.md`](notes/ARCHITECTURE.md)** — the whole pipeline in four stages, with three
   diagrams: abstract, the open stack, the closed one. **§5 is where each stage's ceiling is**, and §6 is
   the open work already ranked.
2. **[`notes/HANDOFF.md`](notes/HANDOFF.md)** — the settled dials, the laws, and round 4's six settled
   points at the top. Its **§6c is marked stale** and kept only as the record of what round 4 planned.
3. **this file's § *Round 4 closed*** — the verdict and its reasoning.

Then, only as needed: **[`notes/ROUTER.md`](notes/ROUTER.md)** if you are touching stage ②,
**[`notes/IDENTITY.md`](notes/IDENTITY.md)** if you are touching the identity number,
**[`notes/FINDINGS.md`](notes/FINDINGS.md)** F42–F46 for today's evidence.

### What the plan is

**The operator's stated intent for 2026-09-13, in his order:**

1. **Finish the open tasks** — listed and ranked below.
2. **Then close the prototype**, and hold a **grilling session on integrating it into the actual
   product.** That is a `mattpocock-skills:grilling` session against the productisation plan, not a
   coding task, and `ARCHITECTURE.md` is the document it will be run against.

> **The prototype's job was to answer empirical questions cheaply before a change is cut.** Four rounds,
> 46 findings, 19 pod sessions, ~$3.17. **Productisation means cutting a change under
> `openspec/changes/<id>/` with four artifacts** — and `../CLAUDE.md` § *How a change is cut here* is the
> contract that governs it. **Nothing in this branch merges.** It reaches a release only by being
> restated inside a change.

### What is actually open, ranked

| | task | cost | why this rank |
|---|---|---|---|
| 1 | **N41 · the review UI** | a feature | **Measured at 0.35** — the gap between the open route unreviewed (0.568) and reviewed (0.917). The only unbuilt stage. Requirements are in § *Carried out of round 4* |
| 2 | **A phone-camera set** | data | **The only true unknown.** Every input across four rounds is generated or professionally shot; the product's actual input has never been tested. Blocked on the operator gathering photographs |
| 3 | **N40 · `pose` in the router**, 0.37 vs Claude's 0.80 | hours, $0 | curation of `tagmap.PHRASES`, not capability. Per-field enums are the other half |
| 4 | **A better VLM** — `Qwen3-VL`, Apache-2.0 | a download | **Stage ①'s ceiling bounds everything after it.** Would separate how much of JoyCaption's 0.518 is its Danbooru training from how much is its eyes |
| 5 | `face_likeness` on N38's twenty renders | $0 | turns F45 from an eye into a number |
| 6 | SFace alignment | a pinned landmark model | tightens `9/17 … 14/17`. **Deliberately last** — it refines a number and changes no verdict |

**Explicitly dropped, do not retry:** prose as a render prompt (F45 — the base reads it and renders it in
the wrong register; the register is the problem, not the wording), and the enum grammar as a router
(F46/`ROUTER.md` §2 — it converts a visible failure into an invisible one).

### What exists now that did not this morning

| file | what it is |
|---|---|
| `joycaption.py` | the VLM seam: pinned bytes, two sight gates, both caption modes, five HTML instruments |
| `router.py` | stage ②'s harness. `--model` swaps a candidate; scores `invented` (F28) and `absence_leaks` (F44) |
| `tagmap.py` | the deterministic mapper — exact → suffix → curated → containment |
| `prose_render.py` | the six-arm render runner, reading prompts from a reviewed `prompts.json` |
| `sface.py` | the independent recognizer, behind a known-answer gate |
| `styles/joycaption_models.json` · `styles/sface_models.json` | pinned digests and licences |
| `notes/ARCHITECTURE.md` · `notes/ROUTER.md` | the two new notes |
| `evaluations/2026-09-12/descriptive_and_booru/` | 26 renders, plan, prompts, captions, four HTML pages, `report.md` |

**Weights on disk, all pinned and digest-verified:** JoyCaption 5.40 GiB + Qwen3-8B 5.2 GB (via Ollama) +
SFace 37 MB. `models/` and `prototype/evaluations/` are gitignored.

### Uncommitted, and it is a record rather than a release

```
  M  README.md  notes/{ARCHITECTURE,FINDINGS,HANDOFF,IDENTITY,JOYCAPTION,READER,README}.md
  ?? joycaption.py  router.py  tagmap.py  prose_render.py  sface.py
  ?? notes/ARCHITECTURE.md  notes/ROUTER.md
  ?? styles/joycaption_models.json  styles/sface_models.json
```

**The gate, honestly:** `isekai/` + `tests/` + `convert.py` are format/lint/type clean and 434 tests pass;
every file added today is clean. **`prototype/archive/*` and `prototype/style_axis.py` carry 109
pre-existing lint errors and 18 unformatted files** — none of them touched today, and `prototype/` has
never been gate-clean on this branch. Flagged rather than fixed: cleaning archived round-1 runners risks
the findings they reproduce.

### Three traps that cost real time today

- **A `raw.githubusercontent.com` URL serves a git-LFS *pointer*, not the model** — a valid 133-byte file
  whose first bytes are `version http`. **Check the magic byte after any model download.** Fetch LFS
  content through `media.githubusercontent.com/media/`.
- **`ollama create` wants roughly twice the file in free disk**, and fails at the validation step after
  copying. A 13 GB import needed more than 20 GiB free.
- **Python buffers stdout when redirected**, so a long background run's log looks empty. Use `python -u`
  or watch the filesystem instead of the log.

---

## Round 1 tasks — all closed

- [x] **T0** external-render seam — score a render this pipeline did not produce · `b0dac41`
- [x] **T1** style axis calibration — buildable, and it takes **two** numbers · F7
- [x] **T2** hair statistic — the mode indicted by a known-answer test, the mean adopted · F8
- [x] **T3/T4** the dial ladder — found the register, and the frontier it moves · F9
- [x] **T5** choose the target register — `notile`, rendered illustration
- [x] **T6/T6b/T6c** the register across six subjects, its frontier, ten diverse portraits · F11, F12
- [x] **T7** style presets — `notile-d045` and `qwen-flatcel` recorded in [`styles/`](styles/)
- [x] **T10a–T10f** Qwen provisioned, instruction swept, sampling path swept, gallery rendered · F15, F17, F18
- [x] **T11** the tattoo question — `xor` confirmed from outside our own stack · F23
- [x] **T12** the missing axes — three of four validated, one honestly rejected · F14
- [x] **T13** style LoRA — it applies, it fights Lightning, it pushes the wrong way · F19
- [x] **T14** the 8-step-native Lightning — did **not** fix consistency · F21
- [x] **Fotor determinism test** — stochastic, 42x the JPEG floor · F20
- [x] **Fotor architecture** — the moat is a style library, not an architecture · F22
- [x] **closing summary** — [`archive/SUMMARY.md`](archive/SUMMARY.md)

**Parked deliberately**, each with its reason in [`archive/SUMMARY.md`](archive/SUMMARY.md): train a photo→anime style
LoRA · Flux.1 Kontext dev (its VAE is gated) · the within-base known-answer probe (T8, $0, never run) ·
`s5`'s refusal path.

---

## Round 2 — the from-noise flow

**Rendered 2026-09-08. The style bar is cleared 3x over; the identity bar is the open question.**

One pod session, 15:05–15:15, ten minutes, ~$0.05. Six subjects, one seed. Full evidence in
[`notes/FINDINGS.md`](notes/FINDINGS.md) **F24**.

| flow | linework ↑ | posterisation | spread |
|---|---:|---:|---:|
| the photograph — **the bar** | 0.0077 | 0.411 | 6.10x |
| `notile-d045` — round 1, rejected as soft | 0.0043 | 0.466 | 9.07x |
| **`fromnoise-v1`** | **0.0240** | 0.296 | **1.28x** |
| `qwen-flatcel` — round 1, rejected on style | 0.0545 | 0.606 | 2.97x |

**The softness was the architecture, exactly as `archive/SUMMARY.md` predicted.** Take the photograph out of the
latent and linework goes to **5.6x** `notile-d045`'s and **3.1x the photograph's own**. The 1.28x spread
was not predicted and inverts `archive/SUMMARY.md` #11: the most consistent flow is the one whose latent does not
start from a photograph.

**And the identity bar passes too, on the operator's eye** — *"holistically I do have a feeling the
anime images are based on the photo"*. Criteria adherence is high: pose, hair, eyes and clothes survive,
`00003`'s freckles render, and `00072`'s choker, chain and heart pendant all render — the accessories
`notile-d045` lost every single time. Recorded in each sheet's verdict block.

**Round 1 ended on a split; this does not.** One flow meets both bars — the style bar by measurement,
the identity bar by eye. That is the first time in either round.

**What is left is improvement, not rescue — and it is cheap, because nothing in this graph has been
swept.** `ip_weight` 0.9, `cn_strength` 0.5, OpenPose 0.6: every one set for an img2img graph whose
latent already carried the face, none revisited since the photograph left it.

### The question

**Does the softness disappear when the photograph leaves the latent?**

```
   round 1:   photo -> VAE -> latent -> +45% noise -> denoise -> render
                                 ^ the photograph's structure is STILL IN HERE,
                                   and the sampler must reconcile it with an
                                   anime prior -> an interpolation -> soft

   round 2:   pure noise -> denoise -> render
                              ^ InstantID face embedding
                              ^ OpenPose skeleton
                              ^ a hand-written criteria sheet, in the prompt
              the photograph never enters the latent
```

Architecturally this is **v0.2's deleted `animagine` from-noise path plus a tagger**. It is the *third*
path v0.8 deleted as "superseded" that we have found reason to revisit — all three asserted by eye, with
no evaluator in existence at the time.

### Tasks

- [x] **N0 · settle the identity criteria** — the sheet, the scored six, and both bars, decided
      2026-09-08 and written up in **[`notes/CRITERIA.md`](notes/CRITERIA.md)** before any render.
- [x] **N1 · ~~recover the graph~~ — not needed.** `animagine.json` does not have to be recovered: the
      shipped `workflows/pipeline.json` becomes from-noise with **four edits**, and every node type is
      already on the image. See `notes/CRITERIA.md` §7.
- [x] **N2 · build the variant** — `prototype/styles/fromnoise-v1.json`: empty latent, `denoise 1.0`,
      `cfg 5 → 7` (from noise the prompt carries the criteria, so text adherence is worth more than it
      was), **InstantID kept**, **OpenPose kept**, **tile and lineart dropped**. 17 nodes, every link
      live, every node type already on the shipped image. Driven by `prototype/fromnoise.py`, which
      reads each subject's prompt out of its sheet and refuses to run a graph that is not from-noise.
      Verified end to end against `FakeComfyClient` — no pod, no spend.
- [x] **N2b · operator review of the ten sheets** — reviewed 2026-09-08. `00059` joined the run for
      the **small face**, and its sheet drops `nsfw` from the negative so the wardrobe does not fight
      the prompt. Negatives are per sheet, so that change is visible rather than global.
- [x] **N3 · one session ⚠️ GPU** — done 2026-09-08, 15:05–15:15, ~$0.05. Pod `2qw...` terminated and
      the teardown confirmed by the RunPod MCP: zero pods on the account.
- [x] **N4 · measure the style bar** — `prototype/archive/n4_measure.py`, four flows on six subjects. **Cleared.**
- [x] **N4b · the identity bar** — **passed**, on the operator's eye, 2026-09-08. Recorded in each
      rendered sheet's verdict block; the per-criterion rows stay blank because the judgement given was
      whole-image, and back-filling six ticks nobody made would fake a measurement.
- [x] **N5 · decide** — **`fromnoise-v1` is the flow.** Both bars met by one architecture, which neither
      round 1 candidate managed. It is not promoted to `main`; promoting one is a change's job.
- [x] **N6 · the face ladder ⚠️ GPU** — done 2026-09-08, 15:34–15:43, ~$0.05. 7 arms x 3 subjects,
      one change each · **F25**. Pod `5vg...` terminated, teardown confirmed by the MCP: zero pods.
      **`ip_weight` is a ceiling, not a default** — 1.2 streaks, 1.5 collapses, and the operator
      rejected both on sight (*"not clean"*), so the eye and the axes closed the dial together.
      **`cn_strength`
      0.5 → 0.8 is the free lever**: holds linework, best posterisation of any dial arm, no artifacts.
      `cfg 7` vindicated by measurement. Also measured, and load-bearing for every arm: a **determinism
      floor** of mean |Δ| ≈ 2/255 across pods, against arm deltas of 10–41.
- [x] **N8 · the combined configuration ⚠️ GPU** — done 2026-09-08, 16:41–16:44, ~$0.03 (plus ~$0.08
      wasted on a pod with no public IP — see F26). `cfg 5` + `cn_strength 0.8`, sheets rewritten in
      **booru tags** with a new **gaze** field, six subjects · **F26**. Teardown confirmed by the MCP.
      **Posterisation 0.296 → 0.332**, up on 5 of 6. **Booru tags are the clearest prompt win in either
      round**: `00050` reproduces the photograph's pose, arm support and all, and `00003`'s gaze is
      fixed. The operator likes every render in the column.
- [x] **N9 · the leg ablation ⚠️ GPU** — done 2026-09-08, 18:58–19:13, ~$0.10. 4 arms x 6 subjects,
      enriched sheets · **F27**. Teardown confirmed by the MCP. **The operator's hypothesis is right and
      the culprit is InstantID**: dropping it moves posterisation **0.358 → 0.518 and clears Fotor's
      0.460 for the first time in either round**, while dropping OpenPose instead moves it to 0.371.
      One leg was most of the style deficit; the other is nearly free. The six prompt improvements are
      separably worth **+8%**, and **`medium breasts` fixed the age drift** that three attempts on the
      age tag could not.
- [x] **N9b · the operator's verdict, 2026-09-08** — **two workflows, both wanted.** `A` (both legs) is
      the best: *"I see face identity and pose is preserved just fine"*, and InstantID's value is now
      visible to him. `D` (prompt only) is kept as a deliberate alternative: *"less identity preserved
      but the anime style is the maximum"*. `C` is rejected against `A`.
- [x] **N12 · canonicalise every sheet** — done 2026-09-08. All ten rewritten in canonical Danbooru
      vocabulary, `1girl` restored for flow `D` (which has no face embedding to carry gender), and both
      flows re-rendered on them ⚠️ GPU, 20:05–20:10, ~$0.04. Teardown confirmed.
- [x] **N13 · the criteria evaluator** — `prototype/criteria_eval.py`, approved and built · **F29**.
      `wd-swinv2-tagger-v3`, pinned in `prototype/styles/wd14_models.json`, verified by digest against
      the prototype's own manifest because the tracked one correctly refuses it. Known-answer gate
      passed at **0.47** against a **0.40** floor stated first. **`D` scores 0.77 to `A`'s 0.73** — and
      the finding is that the scoreboard **cannot see identity at all**, so it does not overturn the
      operator's verdict.
- [x] **N15 · research what Illustrious was actually trained on** — done 2026-09-08, $0 ·
      **[`notes/ILLUSTRIOUS.md`](notes/ILLUSTRIOUS.md)**, primary source the Illustrious paper. Confirms the
      operator's memory (10–20 M images against Animagine's 8.4 M), gives the **trained caption schema**
      and the **trained quality ladder**, and closes the skin question: `pale skin` means *bleached*,
      not fair. Two fixes applied free — skin tags corrected across all ten sheets, and **`worst detail`
      removed from the negative** as an invented tag by F28's own test.
- [→] **N14 · the axis nobody has built** — **carried into round 3 as N27**, which restates it with the
      two flows separated and asks the evaluator question per flow. **Still the open problem, and still
      unsolved** — moving it renumbers it, it does not close it. F29: round 1 measured only
      similarity-to-photograph and the least-stylized render won by construction; round 2 measures only
      adherence-to-description and the flow that never reads the photograph wins by construction.
      **Nothing has ever measured *is this the same person* in a way that survives stylization.**
- [→] **N9c · judge B and D on identity.** **Carried into round 3 as N27's first step** — it is $0, needs
      no pod, and the renders are already on disk. The numbers cannot do it: booru has no vocabulary for
      a particular face, which is exactly what dropping InstantID trades away.
      `prototype/derived/2026-09-08/n9_ablation_contact_sheet.html`.
- [x] **N10 · the age drift** — **fixed by `medium breasts`**, not by any wording of the age tag. Skin's
      real drift case is **`00014` (`fair skin`)**, still never isolated; it is now enriched, so a
      re-read of the N9 renders may close it without a pod.
- [x] **N11 · `infra/up.sh`'s IP poll is bounded** — 180s, and it tears the pod down itself on
      timeout · **F31**. Also: `RUNPOD_GPU_TYPE` now accepts a **preference list**, because the pinned
      Blackwell card exists in **only two datacenters** and a single hardcoded GPU was a single point of
      failure. Both changes are prototype-branch only.
- [x] **N18 · the quality ladder's position, and both flows side by side** — done 2026-09-09,
      12:25–12:34, ~$0.11 · **F34**. Teardown confirmed. **WAI's page beats the community guide on WAI's
      own model**: moving the quality tags to the front is **+0.007**, and `newest` inside the ladder a
      further **+0.006** — the first prompt *addition* to help since the definitional fixes. **It also
      corrects F32**, whose `newest` arm was malformed (placed last, bundled with `general`) — an
      arm-design error rather than a property of the tag. Flow A's best is now **0.363**, still 21% short
      of Fotor; **flow D sits at 0.507, above the bar**, and the transform does nothing for it.
- [x] **N19 · the hires pass** — done 2026-09-09, 12:56–13:12, ~$0.20 · **F35**. Teardown confirmed.
      R-ESRGAN 4x+ Anime6B, pinned in `prototype/styles/upscaler_models.json` and digest-verified on the
      volume. **The first change to move both axes at once.** Flow `D` + hires reaches posterisation
      **0.528** (above Fotor's 0.460) and linework **0.0376** (93% of Fotor's) — the closest anything
      here has come on both axes together. Flow `A` gains **+43% linework** and stays 19% short on
      posterisation. **A measurement caveat worth carrying:** hires renders are 1536x2208 and every
      reference is 1024x1472; read natively, linework's sign flips. Read at the photograph's canvas, as
      `style_axis.py` intends, it does not.
- [x] **N21 · the first real photographs** — 2026-09-09, two sessions, ~$0.16 · **F36**. Both teardowns
      confirmed. Flow `A` and `D`, with and without hires, on three photographs of one real person —
      including a case no synthetic posed: **the same subject with different hair colour** across
      photographs. First pass exposed three *transcription* defects (`pale skin` → bleached again,
      `messy hair` overshooting, a background too thin to stop the base inventing one); **all three were
      fixed for free and all three landed.** Sheets and renders are gitignored (D14).
- [x] **N20 · the style LoRA — dropped 2026-09-10, and not carried into round 3.** Round 1's parked
      lever, parked for two rounds and now closed: **no style LoRA will be trained in this prototype.**
      The reasoning is in round 3's § *What was dropped, and why that is not a loss*.
- [x] ~~**N19 · the hires pass**~~ — **superseded by the N19 above, which shipped (F35).** The original statement, kept:
      the last structural lever, and WAI's own recommendation: R-ESRGAN 4x+
      Anime6B, 20 steps, denoise 0.35–0.5. Needs the upscaler on the pod plus two graph nodes, so it is a
      provisioning change as well as a graph one. **Every documented prompt lever is now spent.**
- [x] **N17 · is our GPU the right one** — researched 2026-09-08, $0 · **[`archive/GPU.md`](archive/GPU.md)**.
      **It is, and the card is not where the money goes**: a render costs **$0.0044** of GPU time and a
      session's boot costs **$0.036** — eight times as much. Cheaper cards are proportionally slower, so
      $/render is a wash while wall-clock triples. `L4` added to the preference list anyway, because it
      is a **different host pool in the same datacenter** and therefore a free second chance at a public
      IP. Open and free: **measure VRAM** with `nvidia-smi` during any future render — 16 GB cards are
      unproven for flow `A` until someone does.
- [x] **N16 · the five prompt arms** — done 2026-09-09, 08:39–08:55, ~$0.19 · **F32**. Teardown
      confirmed. **All four documented prompt changes made the render worse**; only the two
      *definitional* fixes (correct skin tag, `worst detail` removed) helped, worth **+0.013**.
      **Underscores are 0.013 worse than spaces** — the operator's instinct, tested and falsified.
      Posterisation's determinism floor established at **0.0020**, so every effect is 6–10x noise.
      `1_baseline` is the best-known configuration and has the fewest ideas in it.
- [x] ~~**N16 · BLOCKED on infrastructure**~~ — **the block cleared and N16 ran (F32).** The original statement, kept:
      `archive/prompt_arms.py` is built
      and dry-runs clean; all ten sheets are canonical with skin corrected and `worst detail` removed.
      **EU-RO-1 stopped issuing public IPs at ~21:20 on 2026-09-08** and the only alternative datacenter
      for this GPU is `EUR-IS-1` at `LOW` stock, which would need a new volume and a full re-provision.
      Retry EU-RO-1 first; the condition is almost certainly transient.
- [x] ~~**N11 · put a timeout on `infra/up.sh`'s IP poll.**~~ It waited seven minutes for a public IP that
      was never coming, billing throughout, and looked like it was working. The one thing in this
      repository that can bill indefinitely without erroring.

### The bar, stated before the render

There are **two** bars, and a flow must clear both. Round 1's conclusion was that the operator's
preference split the flows against their own numbers; a single-bar round 2 walks back into that.

**Style.** Median linework at or above the photograph's own, against `notile-d045`'s **0.0030** and
inputs running 0.005–0.078. Anything that merely beats 0.0030 without reaching the photograph is the
same failure at a smaller scale.

**Identity.** **5 of the 6 scored criteria survive, and pose and hair silhouette are mandatory.**
Stated in full, with why 6-of-6 was rejected, in [`notes/CRITERIA.md`](notes/CRITERIA.md) §4.

**Hand-written tags on purpose.** There is no point integrating WD14 if the flow does not render
cleanly, and a typed description removes the tagger as a second variable. The tagger is step 2 and is
already researched.

### The style bar, restated — 2026-09-10

**The bar above is round 2's, pre-registered, and it is kept verbatim.** A bar stated before a render is
not editable after it; what follows supersedes it going forward and does not rewrite it.

**The third-party stylizer is no longer the reference, and nothing replaces it.** It was round 1's
lighthouse and it did its job — it calibrated the style axis when we had no idea what "flat enough"
meant, and F20/F22 got real answers out of it. Round 2 then reached the register the operator wants.
**A reference you have passed is not a target; it is a rearview mirror**, and `A`'s "19% short of 0.460"
was being read as a deficit when the operator's own verdict on those renders was that they are what he
wants. The artifacts are in [`archive/fotor/`](archive/) — kept, not deleted — and **nothing live reads
them.**

**What the bar is now: our own last number.** Both axes are *absolute* — they describe the render and
nothing else, no photograph and no reference image — so they can be read against the configuration we
chose. From **F35**, at the photograph's canvas:

| | posterisation | linework |
|---|---:|---:|
| `A` + hires 0.50 | **0.373** | **0.0181** |
| `D` + hires 0.35 | **0.528** | **0.0376** |

> **A change that drops either axis by more than its determinism floor is a regression, and is
> reverted.** The floors are **posterisation ±0.0020** and **linework ±0.0003** — so the numbers above are
> a real gate, not a formality. A change that moves neither axis beyond its floor is **style-free**, and
> is then judged on identity alone (N27) rather than argued about on style.

**The cost, stated plainly.** This removes the only *external* calibration the style axis ever had. The
axes do not need one to be read — that is what absolute means — but the sanity anchor is gone, and a slow
drift of both flows in the same direction would no longer have anything outside the project to catch it.
The accepted mitigation is that **the operator's eye is the anchor**, which has been true of identity all
along (N14) and is now true of style as well.

### What round 2 changes downstream — decide knowingly

**Settled 2026-09-08 in [`notes/CRITERIA.md`](notes/CRITERIA.md).** The scored criteria are **pose · hair
silhouette · hair colour · eyes · clothes · marks**. Background drops out entirely; accessories, body
shape, expression and skin tone stay in the prompt but are judged by eye, each for a stated reason.

**And the ground truth moved.** Because the tags are hand-written, the evaluator scores the render
against **the criteria sheet**, not against the photograph. That kills F16's inverted metric at the root
— no colour distance to a photograph appears in the scored set, so correct stylization is never
punished — and it makes the broken shared-mask assumption stop mattering, since an attribute check needs
no pixel alignment. The cost, stated in `notes/CRITERIA.md` §1: the scoreboard now measures **prompt
adherence**, and inherits whatever the human transcription got wrong.

---

## Round 3 — the identity question, answered

**Both flows already cleared their bars when this round opened**, so it was never about rescue. It asked
**why they work** — which lever is load-bearing, and how we would know if one stopped being. Five
questions closed on the 10th, N26 and N27 on the 11th.

**Two items are carried forward rather than left open**, and both are about making the *instruments*
honest rather than the product better: an **independent recognizer**, and the **JoyCaption trial**.

**Round 2 closed with three items still carrying work. Two are here; one was dropped on purpose** — and
neither the carrying nor the dropping is silent:

| round 2 | round 3 | why it moved |
|---|---|---|
| **N14** the axis nobody has built | **N27** | restated with the two flows separated — and **answered**, F37/F40/F41 |
| **N9c** judge `A`/`D` on identity | **N27**, as its first step | $0, no pod, renders already on disk |
| **N20** the style LoRA | **dropped** | not renumbered, not forgotten — the deficit it existed to close was measured against a retired reference |

**N31 joins them from HANDOFF §6c** — the reader's `body shape` blind spot, $0, and it comes
before N26 so that a briefing bug in the incumbent reader is not scored as a reason to replace it.

### What was dropped, and why that is not a loss

**No style LoRA will be trained in this prototype** — round 1's `N20`, parked for two rounds, closed
2026-09-10 by the operator's decision. It is worth writing down *why*, because it was carried for two
rounds as "the last remaining lever" and a future reader will otherwise assume it was forgotten.

**It existed to close a deficit that no longer exists.** Every statement of it traced back to flow `A`
being "19% short on posterisation" — a number measured against a third-party stylizer that this round
retired. Against the bar that replaced it, `A`'s own last measurement, there is no shortfall to close;
the operator's verdict on those renders is that they are what he wants. **A LoRA is therefore not a fix,
it is a different look** — a product decision, and not one this prototype is for.

**And the cost was never small.** F19 measured a style LoRA fighting the sampler and pushing the wrong
way; F22's redirect assumed a corpus that would have to be gathered, licence-checked and scored on the
style axis before a single GPU hour. That is a project, not a lever.

What survives is the *finding*, not the task: `archive/styles/raena_lora.json` and `archive/qwen_lora.py`
keep F19 reproducible, and `archive/SUMMARY.md` keeps round 1's reasoning for parking it. **Nothing here
needs re-deriving if the question ever reopens outside this prototype.**

---

**N27 comes first in practice.** An evaluator decides which arms are worth $0.0044 each, and every
previous round that built the scoreboard second measured the wrong thing — F16 in round 1, F29 in round 2.

```
   ✅ N25  pose tags          flow A keeps both                      F38
   ✅ N26  reader survey      JoyCaption leads — notes/READER.md
   ✅ N27  identity, scored   14/17 on REAL faces at chance 5.9%     F41
   ✅ N28  hires for A        yes, at 0.35 — and it changed a
                              settled value                          F39
   ✅ N29  held-out ten       it generalises, 8/10                    F40
   ✅ N31  reader re-briefed

   ROUND 3 IS CLOSED. Flow A is validated end to end:
     InstantID + OpenPose + full criteria sheet (pose tags IN)
     cn_strength 0.8 · cfg 5 · hires 0.35
   Every dial chosen by measurement, then confirmed on inputs none of
   it was chosen against — and finally on photographs of real people.

   CARRIED FORWARD, both "make it honest" jobs:
     · an INDEPENDENT recognizer — A's identity number is an upper
       bound until one exists. D's is clean. No GPU, real provisioning.
     · the JoyCaption TRIAL — notes/JOYCAPTION.md plans it, bar stated
```

**Flow `A` is decided as of 2026-09-10:** InstantID + OpenPose + the full criteria sheet including its
pose tags, `cn_strength 0.8`, `cfg 5`, and the hires pass at denoise **0.35**. Every dial in it has now
been chosen by measurement on at least two axes.

- [x] **N25 · does flow `A` need pose tags at all? — ANSWERED 2026-09-10: it needs both.** One pod
      session, 30 renders, ~$0.17, teardown confirmed by the MCP · **F38**. Ten deliberately varied
      poses, three arms, one variable: the `pose` field, dropped from the **prompt** and never from the
      sheet.

      | arm | PCK ↑ | joint-angle error ↓ |
      |---|---:|---:|
      | `1_a_control` — tags + skeleton | **0.821** | **9.4°** |
      | `2_a_no_pose` — skeleton alone | 0.801 | 12.6° |
      | `3_d` — tags alone, no skeleton | 0.218 | 15.9° |

      **They complement rather than compete.** The skeleton places the body; the tags disambiguate the
      limbs it gets wrong. Without them `arms_up` drops an arm the photograph holds behind the head —
      a shoulder off by **124°**, which is a different pose rather than a displaced one.

      **The operator judged the contact sheet before the instrument existed**, named six subjects where
      the control wins, and that expectation was written into the scorer *before* it ran. It agreed on
      five; on `arms_on_hips_legs_wide` it disagreed, the per-joint detail showed the control's left
      elbow off by 65.9° while everything else landed, and **the operator reviewed it and agreed with the
      instrument** — the first time a measurement has corrected the eye here, and it only counts because
      the expectation was recorded first.

      **Left open deliberately:** `framing` was held constant in every arm, so whether DWPose carries the
      *crop* is untested and is a separate question. `legs_crossed` is the worst subject for every arm,
      and part of that is DWPose's own uncertainty on a self-occluding floor pose rather than the render.

- [x] **N26 · is there an open model that reads a photograph as well as the agent session does? —
      SURVEYED 2026-09-11, $0** · **[`notes/READER.md`](notes/READER.md)**. Desk research; nothing run.

      **JoyCaption Beta One is the lead candidate and the only one built for this vocabulary.**
      Apache-2.0, Llama 3.1 + LLaVA, 8B, **~17 GB at bf16 or 4.92 GB at Q4_K** — and it ships a
      **Danbooru tag mode**, one of four booru modes among eleven. Crucially it is trained on
      photographs *as well as* illustrations, which is exactly the property WD14 lacks.

      **Qwen3-VL-8B is the like-for-like control** (Apache-2.0, no booru training, driven by our briefing
      alone). Running both isolates *what the Danbooru vocabulary knowledge is actually worth*: if they
      score the same, it is decorative.

      **Two things the survey settled that were open:**

      - **There is no Danbooru tagger trained on photographs.** Searched for directly; DeepDanbooru,
        Danbooru's own autotagger and every WD14 variant are anime-trained. **The WD14-shaped hole
        cannot be filled by a better tagger, only by a VLM** — so the obvious "WD14 for tags, VLM for the
        rest" hybrid is not available. WD14 scores `pose` 0.08 and `marks` 0.00 on photographs.
      - **No new evaluation harness is needed.** `vlm_reader.py` already scores a draft against the
        operator's reviewed sheets, with floors stated before the incumbent ran. **Any candidate that
        writes `<id>.json` into the drafts directory gets a number directly comparable to the agent's
        0.78**, against WD14's 0.47 and the 0.60 floor.

      **Left open deliberately — the trial, which is a separate task.** This was scoped as *a survey, not
      a bake-off*, and it stayed one. Before anything is trialled: confirm JoyCaption's licence from the
      weights themselves (the repository says Apache-2.0, the model card does not say) into
      `scripts/eval_licences.md`, and **state the bar before the run**, as the incumbent's 0.60 was.

- [x] **N27 · what does "the identity transferred" actually mean, and how is it scored — CLOSED
      2026-09-11.** Carried round 2's **N14** and **N9c**, and N14 had been open since round 1. **It was
      the honest hole in the project and it is now instrumented, validated three times, and agreed with
      by eye every time.**

      > Round 1 instrumented similarity-to-photograph, so the least-stylized render won by construction.
      > Round 2 instrumented adherence-to-description, so the flow that never reads the photograph won by
      > construction. **Both scoreboards were complete on their own terms and both missed the same axis.**

      **The fix was not a better metric but a different question** — *given this render, which of the N
      photographs did it come from* — which is stylization-invariant because every candidate in the
      comparison is equally stylized. Method in **[`notes/IDENTITY.md`](notes/IDENTITY.md)**, written to
      be exported.

      | | subjects | chance | flow `A` | margin | |
      |---|---:|---:|---:|---:|---|
      | tuned-on six | 6 | 16.7% | 5/6 | +0.0485 | **F37** |
      | held-out ten | 10 | 10.0% | 8/10 | +0.1170 | **F40** |
      | **real seventeen** | **17** | **5.9%** | **14/17** | **+0.1172** | **F41** |

      **All four sub-items are closed:**

      1. ✅ **Pose geometry** — `pose_geometry.py`, `IDENTITY.md` §10, first used in **F38**. PCK for
         *placement*, joint-angle error for *configuration*; each is a trap alone.
      2. ✅ **Held-out subjects** — **F40**, 8/10 at chance 10%.
      3. ✅ **Real photographs** — **F41**, 14/17 at chance 5.9%, the strongest result in the project.
      4. ⚠️ **An independent recognizer — NOT done, and it is the standing caveat.** `glintr100` is the
         encoder InstantID optimises against, so **`A`'s numbers are an upper bound rather than an
         estimate**. `D`'s are clean — it never touches that encoder — which is the only reason the gap
         is readable. Both locally pinned face encoders are entangled with this generator; the other is
         *more* so, its training pairs having been stylized with InstantID itself. **This needs a model
         from a different architecture and training set fetched, licence-checked and digest-pinned. No
         GPU. Carried to the next round.**

      **Two things this round proved about the method, not the product:**

      - **The eye came first every time and the instrument had to reproduce it** — F1 is the record of
         doing it the other way and getting a coin flip. On F38 the instrument then *corrected* the eye
         on one subject, and that only counted because the expectation was written down first.
      - **F41 predicted an instrument's behaviour in advance and was right.** `D` was predicted to score
         worse on the real set than on the portfolio, because these descriptions are less distinctive and
         F40 had shown `D`'s hits came from demographics rather than faces. It fell from 4/10 to 2/17.

- [x] **N28 · does flow `A` need the hires pass? — ANSWERED 2026-09-10: yes, at denoise 0.35.** One pod
      session, 10 renders, ~$0.10, teardown confirmed · **F39**.

      | axis | control | + hires 0.35 | floor |
      |---|---:|---:|---|
      | linework ↑ | 0.0112 | **0.0133** (+18%) | ±0.0003 |
      | posterisation ↑ | 0.8261 | 0.8214 (−0.0047) | ±0.0020 |
      | pose · angle error ↓ | 9.4° | **8.7°** | — |
      | pose · PCK ↑ | 0.821 | **0.830** | — |

      **Two thirds of it were already answered and had never been put in one table** — F35 had style,
      F37 identity, and F38's scorer ran on F35's own renders for nothing. That is what made the pod
      session ten renders rather than thirty, and it is the habit worth keeping: *score what exists
      before rendering more.*

      **The pod session tested a hypothesis the free measurement raised**, not one it had answered: F35's
      `00050`, the hardest pose in that set, went 38.7° → 57.0° with hires, so *does hires degrade
      already-hard poses?* **Falsified.** On ten hard poses it marginally improves them, and
      `sitting_on_knees` — the closest analogue — went 16.2° → **10.2°**.

      **⚠️ This changed a settled value.** `A`'s hires denoise is now **0.35, not 0.50**. The old number
      came from F35, which measured style alone because neither identity instrument existed yet. Across
      all four axes 0.35 wins three and loses posterisation by 0.014. `notes/HANDOFF.md`'s configuration
      table is updated. **A settled value is settled against the axes that existed when it was set.**

- [x] **N29 · the held-out portraits — ANSWERED 2026-09-10: the flow generalises.** One pod session,
      20 renders, ~$0.18, teardown confirmed · **F40**. The decided flow, run as decided, on ten inputs
      no dial was ever chosen against.

      | | tuned-on six (F37) | **held-out ten** |
      |---|---|---|
      | chance | 1/6 | 1/10 |
      | flow `A` top-1 | 5/6 | **8/10** |
      | mean margin | +0.0485 | **+0.1170** |

      **The margin more than doubled against a harder chance floor.** Two rounds of tuning did not fit
      ten faces.

      **The sharpest result is `14_00`.** `D` rendered the older woman as a young silver-haired anime
      character; `A` kept her age. The tags were identical — `grey hair` is a *fantasy hair colour* on
      Danbooru meaning silver-haired character, not older person. **The vocabulary cannot say "this
      older woman"; the face embedding could.** That is why flow `A` exists rather than `D`.

      **Pose was mostly inconclusive and the reason was predicted before the render:** eight of ten are
      headshots, so DWPose has no limbs and dropped 10 of 17 keypoints each. PCK still separates on the
      visible head-and-shoulder points — `A` 0.647–0.875 on every subject, **`D` 0.000 on six of ten**.

      **A confound this set introduced into the test itself:** `D` scored 4/10 (p = 0.0128) with a
      *negative* margin, and the four are the demographically most distinctive sheets. A diverse set
      lets a description-only flow be matched back by attributes rather than by face. Property of the
      test set, not the flow — and the negative margin is what exposed it.

      **Still open:** `A`'s number is an upper bound until N27's independent recognizer exists. The
      small-face limit reproduced — full-body framing costs identity, in both rounds and both sets.

- [x] **N31 · re-brief the reader on `body shape` — DONE 2026-09-10.** `vlm_reader.py`'s briefing now
      instructs the reader to give the field a value and says why, in the same edit that added the
      `count` field. Verified by the ten pose drafts, every one of which filled it. The original
      statement, kept:

      It scores **0.00 on real photographs** —
      the reader declines to guess a breast-size tag from a corseted torso, which is a *briefing* failure
      rather than a model failure and is fixable by editing `vlm_reader.py --schema` alone.

      **It costs more than a blank field.** `medium breasts` is the tag **F26** measured as fixing the
      age drift that three separate attempts at the age tag could not — so the field the reader declines
      to fill is the sheet's highest-leverage one. And **F36's law applies**: most apparent model
      failures are description failures, and every one of them was fixed in the sheet rather than in a
      dial.

      Distinct from **N26**, which surveys *replacement* readers. This fixes the reader we have, and it
      should be done first: a briefing bug in the incumbent would otherwise be scored as a reason to
      replace it.

### Round 3 closed — what it established

**Six questions, six answers, ~$0.77 across five pod sessions.** The findings are F37–F41; this is what
they amount to.

**About the product:**

| | |
|---|---|
| **flow `A` keeps its pose tags** | the skeleton places the body, the tags disambiguate the limbs it gets wrong. Without them `arms_up` drops an arm — a shoulder off by **124°**, a different pose rather than a displaced one · **F38** |
| **flow `A` takes the hires pass at 0.35** | not the 0.50 that was settled. Three axes to one, and the old number came from F35 measuring style alone · **F39** |
| **it generalises** | 8/10 on faces no dial was tuned against · **F40** |
| **it works on real people** | **14/17 at chance 5.9%**, the hardest floor here · **F41** |
| **the vocabulary has a ceiling the embedding does not** | `D` rendered an older woman as a young silver-haired anime character; `A` kept her age, on identical tags. `grey hair` on Danbooru *means* silver-haired character · **F40** |

**About the method, which is the part that transfers:**

- **Ask "which one", not "how similar".** Both earlier scoreboards failed the same way — one rewarded
  not stylizing, the other was blind to identity. N-way identification is stylization-invariant because
  every candidate is equally stylized. **[`notes/IDENTITY.md`](notes/IDENTITY.md)**.
- **Two measures, because each is a trap alone.** PCK describes *placement*, joint angles describe
  *configuration*. Flow `D` scored the best angle error of any arm on `sitting_on_knees` **at a PCK of
  0.000** — a plausible body in entirely the wrong place · **F38**.
- **State the bar before the run.** Every result here is readable only because its floor was written
  first. F1 is the record of doing it the other way and getting a coin flip.
- **The eye first, then the instrument.** On F38 the instrument *corrected* the eye on one subject —
  and that only counted because the expectation had been recorded beforehand.
- **Score what exists before rendering more.** Two thirds of N28 was already answered across three
  sessions and had never been put in one table. Doing that shrank its pod session from 30 renders to 10.
- **A diverse test set inflates a description-only flow.** N-way identification assumes the candidates
  are interchangeable; the more diverse the set, the less they are · **F40**, confirmed by **F41**
  predicting the effect's *absence* in advance.

**Known limits, all reproduced rather than suspected:**

- **Full-body framing costs identity** — a small face in frame. Three independent sets: `00059`,
  then `15_01`/`16_01`, then `full_height_4`/`male_full_height`.
- **`A`'s identity number is an upper bound** — `glintr100` is the encoder InstantID optimises against.
  `D`'s is clean, which is the only reason the gap is readable.
- **Nothing here tests a phone snapshot.** Every photograph in every set is generated or professionally
  shot. That is the product's actual input and it remains untested.

**Carried forward, both about honesty rather than capability:** an **independent recognizer**
(no GPU, real provisioning) and the **JoyCaption trial** — planned with its bar already stated in
**[`notes/JOYCAPTION.md`](notes/JOYCAPTION.md)**, candidates surveyed in
**[`notes/READER.md`](notes/READER.md)**.

---

## Round 4 — the open reader

**Opened 2026-09-12. One question, and it is about reproducibility rather than quality.**

The reader that turns a photograph into a criteria sheet is an **agent session**. It scores 0.78, which is
good, and it is **not reproducible by anyone without the transcript that produced it** — a closed,
unversioned, un-pinnable component at step one of a repository whose thesis is open models end to end.

```
  photo ─▶ READER ─▶ draft.json ─▶ adopt ─▶ ★ operator reviews ★ ─▶ build ─▶ render
             │
             ├─ now    an agent session       0.78 · not reproducible
             └─ trial  JoyCaption Beta One    Apache-2.0 · 5.8 GB · local · pinned
```

**The plan is already written and its bar is already stated:** [`notes/JOYCAPTION.md`](notes/JOYCAPTION.md)
— the artifacts, the hosting, the two phases, five traps, and what would make it fail.
[`notes/READER.md`](notes/READER.md) is the survey that chose the candidate over Qwen3-VL, InternVL3 and
Molmo. **Read both before touching anything.** What follows is the task list, and before it the four
places the plan is wrong — every one found on disk on 2026-09-12, before anything was downloaded.

### Four corrections the plan needs before it is followed

**Checked on disk, 2026-09-12, $0.** The plan was written on the 11th and three of these are things that
changed under it; the fourth it never had.

| # | what the plan says | what is true |
|---|---|---|
| **1** | §2: *"LM Studio, already installed — no new dependency"* | **LM Studio is not installed.** `~/.lmstudio/` and the `lms` CLI are there, and `/Applications/LM Studio.app` is not — `lms ls` dies with `ENOENT` trying to spawn it. **Ollama 0.33.1 is installed and answering on `127.0.0.1:11434`**, with no models pulled. **The host is Ollama**, by the operator's decision of 2026-09-12 — and see N33 for the risk that came with it |
| **2** | §4: *"the ten synthetic and three real subjects"* = 13 | **The three real photographs are deleted.** `real_photo_1..3` were withdrawn 2026-09-11 and their images removed from `inputs/real/` — the sheets are kept only so F36 and F40 stay reproducible (`sheets/real/_withdrawn_2026-09-11/README.md`). The runnable set is **10**, unless real subjects are drawn from N30's seventeen |
| **3** | §3: the bar is *0.78, measured the same way* | **Only the ten synthetic portraits can give a like-for-like.** The 17 real, 10 portfolio and 10 pose sheets were written by `sheet.py adopt` **from the incumbent's own drafts**, one minute apart — the reference *is* the incumbent's output plus the operator's edits. Scoring JoyCaption on those 34 measures *agreement with the incumbent, as corrected*, which is worth having and is **not** the same number as 0.78 |
| **4** ✅ | §1: two sha256 digests | **Both are truncated to four bytes** and verify nothing. The manifest needs the full digests, and hashing a 4.92 GB file must be **streamed** — `criteria_eval.verified()` does `path.read_bytes()`, which is fine at 467 MB and not on a 16 GiB machine at 4.9 GB. **Closed by N32** — full digests pinned, hash streamed |

**The machine, measured rather than assumed:** MacBookPro18,1, **16 GiB RAM**, **43 GiB free**. Q4_K plus
the projector is 5.80 GB and fits; Q8_0 is 9.42 GB, fits on disk, and is tight in RAM — it stays the
quantisation check of §7 and not the first thing tried.

### Tasks

```
   ✅ N32  pin + licence         pinned, licence NOT Apache-2.0, bytes verified
   ✅ N33  host + prove sight    Ollama, two-FROM Modelfile. It SEES: 17/17 incl. 3/3 men
   ◐  N34  the client            built, and the normalisation pass is NOT — see below
   ✅ N35  phase 0              0.501 · 85% canonical · every §6 trap confirmed
   ✅ N36  phase 1              0.518 best of three arms — and one arm did harm
   ✅ N37  the decision         FAILS the 0.60 bar as a reader · KEPT as the describer
   ✅ N38  render-test          20 renders, ~$0.26 · prose is dead · the review step is 0.35
```

- [x] **N32 — pinned, licence-checked and byte-verified — 2026-09-12.** `$0`. **Closed below.**
      `prototype/styles/joycaption_models.json`, on `wd14_models.json`'s pattern exactly: `pinned`, `why`,
      `not_in_eval_models_json`, `publishers`, and per entry `dest` / `sha256` / `bytes` / `sources`.
      From **`concedo/llama-joycaption-beta-one-hf-llava-mmproj-gguf`** and nowhere else — `READER.md`'s
      warning is that the two most-cited quantisations ship **no `mmproj`** and are silently blind.
      Full digests come from the repository's own metadata, not from `JOYCAPTION.md`'s truncated table.
      The licence goes in the manifest's `why`, with the URL and the date read, which is where `wd14`'s
      Apache-2.0 is recorded — **not** `scripts/eval_licences.md`, which is tracked and belongs to
      `eval_models.json`. `concedo`'s requantisation declares no licence of its own; that gap is the thing
      to write down.
- [x] **N33 — DONE 2026-09-12. It sees.** `$0`. Ollama's undocumented two-`FROM` Modelfile pairs the
      projector; `ollama show` lists `vision` and a 434 M-parameter CLIP projector, and its blob store
      is content-addressed so **its two layers carry our pinned digests**. The falsifiable gate:
      **17/17 on sex over the seventeen real photographs, including 3/3 on the men** — a blind model
      scores 0/3 there, so sight is proven. **Gate 1 failed its stated bar**, 6/10 on eye colour
      against 8/10, above the 4/10 blind floor; every miss was green or grey and it never once said
      either word. Kept as a FAILED bar rather than rewritten. Original text below.
- [x] ~~N33 — stand up the host, and prove the model can see.~~ `$0`. **Ollama, by the operator's
      decision of 2026-09-12**, at 0.33.1 and already answering on `127.0.0.1:11434`. The requirement is
      **one local HTTP endpoint that accepts an image**, so the client stays stdlib `urllib` and no Python
      dependency is added.

      **And the risk that came with the choice, found 2026-09-12 before starting:** Ollama's current
      `docs/import.mdx` and `docs/modelfile.mdx` **do not mention `mmproj`, a projector, or vision
      anywhere.** The documented GGUF import path covers a text model and a safetensors adapter. The
      two-`FROM` Modelfile that paired a LLaVA quant with its projector is undocumented now, and may or
      may not still work on 0.33's engine. **Cheapest order: try the two-`FROM` Modelfile against the
      local pinned files (two minutes), then `ollama pull hf.co/concedo/…` to see whether Ollama detects
      the projector in the repository itself** — the second is worse for us because nothing we can verify
      against the manifest ever lands on disk. If neither pairs it, the blocker is **hosting, not the
      model** (`JOYCAPTION.md` §7 says exactly this), and the options are LM Studio after all or
      `llama-server` from llama.cpp — the latter a binary tool rather than a Python dependency, and still
      an ask, not an assumption.

      Then the gate,
      and it has to be falsifiable because the failure is silent: **a LLaVA GGUF without its projector
      answers fluently and describes nothing.** Two different photographs must produce two different
      answers, and a question about a detail present in only one of them must fail on the other. A model
      that passes a single "describe this" prompt has proven nothing.
- [◐] **N34 — the client is built; the normalisation pass is NOT.** `$0`. `prototype/joycaption.py`
      carries the transport, both sight gates, the booru probe, both caption modes, the evaluation
      runner and five HTML instruments. **The §6 cleanup was counted and never applied** — underscores,
      `meta:`/`photo (medium)`, and the `own` family were all measured (49 dead-or-meta tags of 333)
      and the fix was done by hand during routing instead. **It belongs in the router, which does not
      exist yet**, and N38 added a second job to it: strip absence clauses. Carried, not dropped.
- [x] ~~N34 — the client, and the normalisation pass that belongs in it.~~ `$0`.
      `prototype/joycaption.py`: stdlib `urllib` against localhost, writing `<id>.json` into
      `derived/vlm_drafts/` under a per-phase directory so no run overwrites the incumbent's drafts.
      `JOYCAPTION.md` §6's first three traps are a deterministic cleanup — underscores (F32: −0.013,
      six times the determinism floor), meta tags (`photo (medium)` **instructs an anime model to render a
      photograph**), non-canonical variants (`hands on hips` is not in the vocabulary; `hands on own hips`
      is, at 25,548). It goes **here and not in `sheet.py`**, which serves every reader.
- [x] **N35 — DONE 2026-09-12. 0.501 on the independent three.** `$0`. 333 tags over ten photographs,
      **85% canonical**. **All four of `JOYCAPTION.md` §6's predicted traps confirmed**: underscores on
      all 333, `copyright:original` + `meta:photoshop_(medium)` on all ten, `photo_(medium)` on eight,
      and six of the `own` family (`hands on hips` for `hands on own hips`). One new one, measured:
      **it hedges rather than decides** — `blonde hair` *and* `brown hair` on the same subject,
      `long hair` *and* `medium hair`, three background colours at once. Original text below.
- [x] ~~N35 — phase 0: the raw Danbooru tag dump.~~ `$0`. JoyCaption's own booru mode, over the ten
      synthetic portraits and — knowing correction 3 — N30's seventeen real ones as a second, separately
      reported arm. Scored by `vlm_reader.py` **unchanged**; it already does recall per field against the
      reviewed sheets, with the 0.60 mean and 0.40 per-field floors stated before the incumbent ran.
- [x] **N36 — DONE 2026-09-12. Three arms, and the sharpest arm did harm.** `$0`. Briefing it
      *neutrally* with the sixteen fields is the best of five prompts at **0.518** — and it ignored the
      field structure and returned a flat bag anyway. Briefing it **pointedly** with the seven identity
      criteria and *"do not leave one blank"* **fell to 0.307 and invented nineteen identity marks on
      seven of ten subjects**. The agent briefing passed verbatim collapsed to 0.093. Original text below.
- [x] ~~N36 — phase 1: our sixteen-field schema, verbatim.~~ `$0`. The briefing `vlm_reader.py --schema`
      prints, word for word — `JOYCAPTION.md` §8 is right that changing it makes the comparison unfair, so
      **any rewrite is a second arm, never a correction.** Same photographs, same scorer, same sitting as
      N35, because the comparison *between* the two phases is the finding: **is JoyCaption a tagger we
      route, or a reader we brief?** Its model card warns instruction-following is its weak point, so this
      is a real question.
- [x] **N37 — DECIDED 2026-09-12. It fails as a reader and is kept as the describer.** `$0`. See
      § *Round 4 closed* below for the decision and its reasoning. Original text below.
- [x] ~~N37 — the decision.~~ `$0`. Against §3's bar: **≥0.78 replaces** the agent session · **0.60–0.78**
      becomes the first-draft generator the operator reviews · **<0.60 fails**, as WD14 did at 0.47. And
      against §5's fork, which chooses the integration: a briefed reader is a drop-in, a tag dump needs a
      `tag → field` router that is real and maintained work. The middle band is **not** a consolation
      prize — `CRITERIA.md`'s architecture already has the review step.
- [x] **N38 — DONE 2026-09-12. 20 renders, one session, ~$0.26.** It grew past a render-test into the
      round's most informative run: **[`evaluations/2026-09-12/descriptive_and_booru/`](evaluations/2026-09-12/descriptive_and_booru/)**,
      plan and prediction written first, verdict in its `report.md`. Prose is dead as a prompt; an
      absence clause is a presence instruction; the review step is worth 0.35. Original text below.
- [x] ~~N38 — render-test the winning sheet. ⚠️ GPU, conditional on N37.~~ Only if N37 adopts or
      first-drafts. **The agreement score is a proxy and the product is the image**: a 0.69 sheet may
      render well and a 0.90 sheet may miss the one tag that mattered. One session, flow `A` at the settled
      configuration, the reviewed sheet against the JoyCaption-seeded sheet on the same subjects and seed.
      Budget ~10 renders, ~$0.10 inside the 60-minute / ~$0.75 ceiling. **Downscale the inputs first** —
      N30's real photographs are 21–28 MB each and the uploads, not the GPU, made 34 renders take 27
      minutes.

### N32 closed — the bytes are pinned, and the licence is not what both notes said

**2026-09-12 · `$0`, no pod, no GPU.** `prototype/styles/joycaption_models.json` ·
`prototype/joycaption.py --verify` · 5.40 GiB on disk at `models/joycaption/`.

```
  PINNED   revision acfe6bf78ae4e411cd5c7c8f4a71ba01f26a5b97 in every source URL
  OK       Llama-Joycaption-Beta-One-Hf-Llava-Q4_K.gguf            4.58 GiB
  OK       llama-joycaption-beta-one-llava-mmproj-model-f16.gguf    0.82 GiB
  --       Q8_0 (7.95 GiB) and F16 (14.97 GiB) — digests recorded, NOT fetched
```

**All four digests in the repository were checked against the Hub's own LFS metadata before anything was
downloaded, and both fetched files then verified against them.** `JOYCAPTION.md` §1's two were truncated to
four bytes and verified nothing; the full ones confirm its prefixes were right. The manifest **pins the
revision** in every source URL where `wd14_models.json` resolves through `main` — a digest catches a
repository that moved, a pinned revision stops it moving.

**The licence is the finding, and it corrects two notes.** Read four layers deep:

| layer | declared |
|---|---|
| `fpgaminer/joycaption` — the **code** | **Apache-2.0**, SPDX, via the GitHub licence API |
| `fancyfeast/…-hf-llava` — the **weights** | **no `license` field.** The README's *"open weights, no restrictions"* is prose |
| `meta-llama/Llama-3.1-8B-Instruct` — the **base LLM** | **`llama3.1`**, and `gated: manual` |
| `google/siglip2-so400m-patch14-384` — the **vision tower** | `apache-2.0` |
| `concedo/…-mmproj-gguf` — **this requantisation** | **none**, and its README states no terms |

**`READER.md` and `JOYCAPTION.md` both call it "Apache-2.0". That is true of the code and not established
for the weights** — the Llama 3.1 Community License carries naming, acceptable-use and 700M-MAU terms, and
a fine-tune of a Llama 3.1 checkpoint derives from it. The upstream author's "no restrictions" cannot grant
more than he received. **Fine for a prototype that renders locally and distributes nothing; not a settled
position for anything that ships.** Both notes are corrected and the full record is in the manifest and
`JOYCAPTION.md` §9 — deliberately **not** in `scripts/eval_licences.md`, which is tracked and belongs to
`eval_models.json`, on `wd14_models.json`'s precedent.

**And a second projector trap, in the same repository chain.** The source repository's own README says:

> *"Download the main model (`…-Q4_K.gguf`) and the mmproj (`Llama-Joycaption-Beta-One-Hf-Llava-F16.gguf`)"*

**`…-Hf-Llava-F16.gguf` is the 16 GB full-precision *text* model, not the projector.** Following that
instruction downloads 21 GB and still has no vision. It is recorded under `not_fetched` for exactly one
reason: so it is never confused with the projector again. Twice now the projector is where this model goes
wrong — §1's warning was two quantisations shipping none at all.

**`prototype/joycaption.py` streams the hash.** `criteria_eval.verified()` does `path.read_bytes()`, which
is right at 467 MB and a risk of swapping at 4.92 GB on 16 GiB. Size is checked before the digest, because
a truncated download is the failure that actually happens and saying so is free.

**What is *not* proven, and the file says so when it runs:** that the model can see. A digest proves the
bytes are the bytes we pinned; a projector-less LLaVA answers fluently and describes nothing. **N33's gate
has to be falsifiable**, and it is next.

### The bar, and why it is quoted rather than restated

**It is in [`notes/JOYCAPTION.md`](notes/JOYCAPTION.md) §3, written on 2026-09-11 before a byte was
downloaded**, and it is not repeated in full here so there is exactly one copy of it to adjust. The whole
point of F1 — this project's record of stating a bar *after* the run and getting a coin flip — is that the
number has to be older than the result.

**What the trial cannot decide, and should not be read as deciding:** whether JoyCaption is a *good
captioner*. It is being measured on one job — structured extraction into a closed vocabulary against
sixteen named fields — and a model can be excellent at prose description and fail this.

### What round 4 changes downstream — decide knowingly

- **If JoyCaption replaces the agent session**, `vlm_reader.py`'s `INSTRUCTIONS` stops being *the*
      reader's briefing and becomes *one* reader's briefing. That is `JOYCAPTION.md` §8's third open item
      and it is a real edit, not a rename.
- **If it becomes the first draft instead**, nothing downstream changes at all — `adopt`, `check`,
      the operator's review and `build` are untouched, and the win is that step one is now pinnable.
- **Either way the reproducibility claim changes shape.** A pinned GGUF with a recorded digest is
      reproducible *by anyone with the file*; it is not reproducible *bit-for-bit across hosts*, because
      llama.cpp sampling and quantisation are not the same thing as a deterministic tagger. Worth stating
      before it is claimed.

### Not scheduled this round, and each with its reason

- **N39 — Qwen3-VL-8B as the control.** `READER.md` §4's second item: no booru training, driven purely by
  our briefing. **If it ties JoyCaption, the Danbooru vocabulary training is decorative** and the field is
  wide open. Worth knowing, and it is a second trial rather than part of this one.
- **N27b — an independent recognizer.** Still open and still the honest gap: `A`'s identity numbers are an
  **upper bound** because `glintr100` is the encoder InstantID optimises against. Needs a face encoder from
  a different architecture and training set, fetched, licence-checked and digest-pinned. `$0`, no GPU.
- **A phone-camera set.** Every photograph in every round so far is generated or professionally shot.
  **That is the product's actual input and it remains untested.** Blocked on data, not on work.

---

### Round 4 closed — JoyCaption fails the bar it was given and earns a different job

**2026-09-12 · one pod session, 20 renders, ~$0.26 · seven prompts tried · every task closed but one.**

**Against `JOYCAPTION.md` §3's bar, stated 2026-09-11 and not moved: it fails.** Seven prompts, and the
best agreement on the three references that are independent of the incumbent is **0.518**, against the
agent session's reproduced **0.795** and a floor of **0.60**. It clears WD14's 0.47 and nothing else.

| what was asked | best score | bar |
|---|---:|---:|
| its own Danbooru tag mode | 0.501 | — |
| our sixteen fields, neutrally | **0.518** | 0.60 |
| its prose, hand-routed to a sheet | 0.489 | 0.60 |
| the seven identity criteria, pointedly | **0.307** ↓ | 0.60 |
| the agent's briefing verbatim | 0.093 | 0.60 |
| *the agent session, same measure* | *0.795* | |

**The gap is perception, not briefing, and that is why no prompt closed it.** `00003`'s eyes are green in
its reviewed sheet and in the photograph, which was checked by eye. JoyCaption returned **brown, blue,
brown, light brown, blue, brown and brown** across seven prompts — it has never once said green, and on
one subject two prompts of the same model at temperature 0 disagreed with *each other*. A briefing can
fix a field nobody asked for; it cannot fix a colour the vision tower does not resolve.

### And it is kept — as the describer, not the reader

**The operator's decision, 2026-09-12: JoyCaption has a place in the stack.** Not the place the trial was
designed to test.

```
  photo ─▶ JoyCaption ────▶ prose ─▶ ROUTER ─▶ 16-field sheet ─▶ ★ REVIEW ★ ─▶ render
           open · pinned            open, or                      the 0.35
           Apache-2.0 code          Claude / OpenRouter
           Llama-3.1 weights        as the alternative
```

- **Stage 1 is open and pinned.** 5.40 GiB, digests in `styles/joycaption_models.json`, hosted on Ollama.
  The *seeing* is now reproducible by anyone with the file, which was round 4's entire motivation.
- **Stage 2 is a router, and it has two jobs.** Sort prose into sixteen fields, **and strip absence
  clauses** — the second job was discovered by N38 and is not optional. Claude or an OpenRouter model
  stays the alternative by the operator's decision; an open model is preferred and untested.
- **Stage 3 is the review step, and it is worth 0.35.** Measured: the open route unreviewed delivers
  **0.568** of the reviewed sheet's attributes through to the render; the reviewed sheet delivers
  **0.917**.

**What this buys and what it costs, stated plainly.** It buys an open, pinnable, digest-verified
perception stage. It costs a component that did not exist before, and it does not beat the agent session
on quality — it beats it on reproducibility, which was always the argument.

### Four laws, and two of them are new

- **F42 · a briefing fixes omissions and cannot fix perception.** Every field JoyCaption scored badly on
  *for not being asked* improved when asked — `marks`, `gaze`, `framing`. Eye colour did not move across
  seven prompts. **Rank a reader's failures into omission and perception before trying to prompt around
  them**; only the first kind is reachable.
- **F43 · pressure on an identity field produces confabulated identity.** *"Do not leave one blank"* gave
  nineteen invented marks on seven of ten subjects and dropped the score from 0.518 to 0.307. **And it
  sharpens F28**: the law was *canonical tags work, invented ones do nothing*. `mole under eye` is
  canonical **and** invented — so an invented canonical tag does not do nothing, **it does something
  wrong**, and it passes `sheet.py check` on its way to the prompt. A blank gets reviewed; a plausible
  false tag does not.
- **F44 · an absence clause is a presence instruction.** Licensing the reader to say *"no tattoos are
  visible"* stopped it confabulating and then put `tattoos` in the positive prompt, because CLIP has no
  negation. The render came back with tattoos, freckles, piercings and scars on a subject who has none.
  Isolated by a control on the same photograph and seed. **A reader must be allowed to state absence; a
  prompt must never carry it. The router is the seam where that is stripped.**
- **F45 · the prompt's job is style; the legs' job is identity.** The operator's reading of all twenty
  renders is that InstantID and OpenPose held on every case, across four prompt registers including one
  out of distribution and two poisoned with hallucinated tattoos. **A bad sheet degrades attributes
  rather than likeness** — which is why a 0.568 sheet is still a usable picture of the right person.
  *Not instrumented:* `face_likeness` was not run on these twenty, and five subjects gives a 20% floor.

**And one instrument lesson.** The two style axes ranked the four arms almost backwards from
`criteria_eval`: the arm with the **best linework of the four had the worst attribute recall**. A render
can be more cel-shaded than the baseline and a worse picture of the person. **Posterisation and linework
describe the register and say nothing about whether it is the right person** — which is what
`IDENTITY.md` §1 already says about round 1's scoreboard, met again from a new direction.

---

## Carried out of round 4

- [x] **N39 — the harness is built. 2026-09-12.** `prototype/router.py`. Scores a prose→sheet mapper by
      `vlm_reader`'s measure against the reviewed sheets, and counts two failure modes: `invented`
      (F28) and **`absence_leaks`** (F44). **The incumbent now has a number: Claude by hand, 0.575, zero
      invented, zero leaks** — on the five evaluation captions, which is what any candidate must beat.
      One bug caught building it: **54 canonical tags contain negation words** — `no bra` (93,761),
      `eyes visible through hair` (62,070), `invisible chair` (11,163) — so the leak detector flags only
      absence language the vocabulary does *not* know. A real tag is never a leak, however it reads.
- [x] ~~N39 — the router, and an eval for it.~~ The component the decision above depends on and the one
      thing round 4 did not build. **There is no eval for a prose→sheet mapper**: `vlm_reader.py` scores a
      *reader*, and the only router number that exists is one hand-routing on five subjects — by a hand
      that is not a reproducible component either, which is the objection round 4 opened with. **Build the
      harness first, then candidates are a one-line swap and a table.** Two jobs: sixteen fields, and strip
      negation (F44). `$0`, no GPU.
- [◐] **N40 — yes, and the constraint matters more than the model. 2026-09-12.**
      **`Mistral-Small-3.2-24B` was abandoned on hardware, not licence.** `ollama create` copied 13 GB and
      then ran out of disk writing its validation temp, from 34 GiB free — Ollama's import wants roughly
      twice the file. And Q4_K_M is 13 GB on a **16 GiB** machine, so even once hosted it would page
      through every token: the test would have measured swap. Recorded so it is not retried on this
      machine without more RAM.

      **`qwen3:8b` — Apache-2.0 confirmed from the weights, 5.2 GB, runs comfortably.** Measured on the
      five evaluation captions:

      | router | mean | tags | invented | leaks |
      |---|---:|---:|---:|---:|
      | Claude, by hand — the incumbent | **0.575** | 105 | 0 | 0 |
      | **qwen3:8b + enum grammar** | **0.316** | 111 | **0** | 0 |
      | qwen3:8b, unconstrained | 0.033 | 88 | **68** | 0 |

      **Constraining the output is worth +0.283, a 9.6x improvement, and it removed all 68 invalid tags
      by construction rather than by validation.** `blonde` became unemittable. That is the reframe
      confirmed: **the vocabulary is closed, so this is a picking problem and not a knowledge problem** —
      and an 8B model with a grammar beats the same 8B model without one by an order of magnitude.

      **Unconstrained, its failures were surface and not semantic.** It correctly saw blonde hair, blue
      jeans, a hand on the chin, and then wrote `blonde` for `blonde hair`, `brown` for `brown eyes`,
      `body slightly angled to the right` for a pose. **It had simply never seen `selected_tags.csv`.**

      **Two fields already match the hand-routing** — `hair colour` 0.80 and `eye colour` 0.40, both
      exactly Claude's. The gap is three: `clothes` 0.24 vs 0.77, `pose` 0.27 vs 0.80, and **`gaze` 0.00
      vs 0.60**.

      **Next, and it is cheap: per-field enums.** The shared 8,106-tag enum constrains the vocabulary and
      not the *field*, so a third of the errors are real tags in the wrong slot — `framing` received
      `sunset, blowing, sunlight` and `gaze` received `front ponytail`. Derived per field from the
      vocabulary the sets are tiny: **`count` 5 · `framing` 13 · `gaze` 20 · `body shape` 51 ·
      `eye colour` 55 · `expression` 80 · `hair colour` 103**. At 20 values all beginning `looking`,
      `gaze` cannot receive a ponytail. `clothes`, `accessories` and `background` stay open-ended and keep
      the full enum. **A crude keyword derivation is not enough** — `marks` picked up `scarf` because it
      contains `scar`; the lists need curating, which is `JOYCAPTION.md` §5's *"real work, and it has to be
      maintained"*, now with numbers.

      **Two defects found and fixed, both worth knowing before anyone repeats this.**
      1. **Thinking tokens are drawn from the answer's budget.** Qwen3 is a hybrid reasoner; its thinking
         truncated the JSON mid-string on the third subject. `think: false` — routing is slot-filling.
      2. **A grammar stops invalid tokens and does not stop looping.** `full_height_2` emitted
         `"white robe"` forty times until it exhausted 2048 tokens, `done_reason: length`. A context-free
         grammar cannot express *no repeats*, so the bound goes on length: `maxItems: 10` — no field on
         any reviewed sheet here carries more than nine tags — plus `repeat_penalty`. At temperature 0
         there is no sampling noise to break a loop, so the penalty is the only thing acting inside one
         array.

      **Cost: the grammar is ~70s per subject against ~15s unconstrained.** Worth it at 9.6x, and worth
      measuring again if the per-field enums shrink the compile.
- [x] ~~N40 — can an open model be the router?~~ **`Mistral-Small-3.2-24B-Instruct` is already on the
      operator's disk at 14 GB and is Apache-2.0**, which makes it the first candidate for reasons of
      licence and availability rather than ranking. Alternatives: Qwen3-8B/14B (Apache-2.0), Phi-4 (MIT).
      **Gemma 3 is not a candidate** — the Gemma Terms of Use carry use restrictions and fail the stated
      open-licence bar; Llama 3.x carries the same 700M-MAU clause as JoyCaption's own base.
      **And the reframe that matters: this is not a knowledge problem.** The vocabulary is closed at 8,106
      tags, so a GBNF grammar over `selected_tags.csv` makes an invalid tag *structurally impossible*
      rather than caught afterwards — which is a stronger guarantee than any model gives, and lets a
      smaller one do the job. A deterministic `phrase → field+tag` map for the few hundred phrases that
      carry the seven scored fields may cover most of it with no model and no licence at all.
- [ ] **N41 — the review UI.** **A separate feature and explicitly out of the prototype's scope** — the
      operator's decision of 2026-09-12; nothing here is an unknown that needs a spike. Recorded so the
      idea is not lost, with the four requirements that came out of today's measurements:
      upload a photograph, see what JoyCaption saw and the tags an LLM built from it, **grouped by the
      sixteen fields with the seven scored ones marked**, and per-group add/delete with autocomplete.
      1. **Autocomplete must show the post count**, not just the tag — `narrow waist` (9,411) renders an
         exaggerated waist and `medium breasts` (770,389) renders ordinary. A picker that offers them as
         equals walks the operator into that trap every time.
      2. **Show the live token count against the 77-token window.** Sheets already run 80–122 estimated
         tokens and nothing says so; every one is silently chunked and averaged.
      3. **The table is the only editable surface** — which removes the `sheet.py build` footgun, where
         editing the prompt block gets silently overwritten.
      4. **The sheet on disk stays the source of truth.** Write on save; never let the sheet exist only in
         a browser.
      **And its value is now measured rather than assumed: it is the 0.35** between the open route
      unreviewed (0.568) and the reviewed sheet (0.917).
- [x] **N27b — DONE 2026-09-12. Identity survives an independent encoder · F46.** `$0`, no pod.
      **SFace: 9/17 at chance 5.9%, p ≈ 0.0000**, against `glintr100`'s 14/17 on the same crops — so `A` is
      no longer self-graded, and the entanglement inflated the **margin 16.3x** while inflating the hit
      count only 1.6x. `prototype/sface.py`, `prototype/styles/sface_models.json`.
      **One caveat replaces the other and it is one-directional:** SFace runs unaligned, so 9/17 is a
      *lower* bound — preprocessing (raw 0-255 RGB, settled over five variants) and crop margin (0.0
      already optimal) were ruled out first, and `glintr100` ranking the known-answer pair 1/136 where
      SFace ranks it 2/136 is what exonerates the crop and indicts alignment. Read it as bracketed:
      **9/17 … 14/17**. Original scope below.
- [x] ~~N27b — an independent recognizer, so `A`'s identity number stops being self-graded.~~ `$0`, no GPU.

      **The problem, precisely.** `face_likeness.py` measures identity with `glintr100`, and InstantID
      *injects* identity using that same encoder. The examiner is the thing being optimised against, so
      **flow `A`'s 14/17 is an upper bound rather than an estimate** — `IDENTITY.md` §"circularity" states
      it and `isekai/eval_backends.py`'s `ArcFaceEncoder` docstring says the axis "may only falsify".
      Flow `D` never touches InstantID, which is the only reason the `A − D` gap reads at all.

      ```
        photograph ──▶ glintr100 ──▶ embedding ──▶ InstantID conditions on it
                            │                              │
                            └──────▶ SCORES the render ◀────┘
                                 the same encoder, both ends
      ```

      **Only the recognizer is entangled, and that is a scoping correction.** The first sketch of this
      task said "swap the detector too". **Wrong:** `face_likeness.py` crops with deepghs'
      `anime_face_detection` (MIT), not with InsightFace's SCRFD, so the detector is already independent
      of InstantID. Replacing it with a photograph-trained detector like YuNet would put a *worse* crop
      on anime faces and buy nothing — the repo pins an anime-specific detector precisely because photo
      detectors fail there. **YuNet is dropped from this task.**

      **The candidate: `SFace` from OpenCV Zoo.** Checked 2026-09-12.

      | | |
      |---|---|
      | licence | **Apache-2.0**, per that directory's own `LICENSE` — *better* than the incumbent, which `scripts/eval_licences.md` records as a non-commercial-research deviation |
      | form | ONNX, 38,696,353 bytes, loads through the `OnnxSession` seam that already exists |
      | independence | different architecture, different training corpus, different loss (sigmoid-constrained hypersphere, IEEE 9318547), and a **128-d** embedding against `glintr100`'s **512-d** — the dimensionality alone is evidence they are not variants of one model |
      | digest | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`, and **git's own LFS pointer declares the same oid**, so the download verifies against the repository's record rather than only against itself |

      **Runners-up, and why not.** `FaceNet` (Inception-ResNet on VGGFace2, MIT) is genuinely independent
      and is a PyTorch checkpoint — a heavier integration than ONNX for the same answer. `AdaFace` shares
      IR-101 backbones and MS1MV training with ArcFace, so it is not independent enough. Anything else
      from `insightface` is the same family and disqualified by construction. And the other locally
      pinned encoder is **already disqualified**: `IDENTITY.md` records it as a CLIP encoder with a style
      LoRA whose training pairs were stylized *with InstantID and IP-Adapter* — more entangled, not less.

      **The trap this task must not fall into, and it has a known-answer test.** SFace's preprocessing is
      **not** ArcFace's: the incumbent feeds `(x − 127.5) / 127.5`, SFace expects raw 0–255. Feeding it
      the wrong range produces, in `IDENTITY.md` §4's own words, *"numbers that look fine and mean
      nothing"*. So the encoder is not trusted until it passes a known-answer test on real data:
      **`face_4` and `ful_height_1` are the same person** (recorded in `real_photo.py`'s `SAME_PERSON`),
      so SFace must score that pair far above the other 15 photograph pairs. **If it cannot, the
      preprocessing is wrong and no downstream number may be read.**

      **What the comparison actually asks, and it is not "a cleaner cosine".** Both encoders are
      photograph-trained and are being asked to embed an *anime* face. `glintr100` does that badly but
      **consistently**, which is why N-way identification works at all.

      > **The question is whether an independent encoder reproduces the same RANKING**, over F41's
      > seventeen real subjects at chance 5.9%. If SFace also puts the correct photograph first on ~14 of
      > 17, `A`'s result stops being self-graded. **If SFace produces noise on anime faces, the honest
      > outcome is "no independent signal is available" — and that is also a result**, because it would
      > say this project cannot currently de-bias its own identity number, which is worth knowing rather
      > than assuming.

      **Reads renders already on disk** — `evaluations/` and `renders/2026-09-11/n30_real/` — so it costs
      nothing and spends no pod. Deliverable: the two encoders' top-1, margin and p side by side on the
      same seventeen subjects, and a verdict on whether the entanglement caveat can be dropped.
- [ ] **`face_likeness` on N38's twenty renders.** Would turn F45 from an eye into a number. `$0`.
- [ ] **A phone-camera set.** Still the product's actual input and still untested. Blocked on data.

**Dropped deliberately:** **prose as a render prompt.** Dead on the instrument (0.675 and 0.510 against
0.917) and on the eye. The base *does* read prose — `"the image has a gray border"` produced a painted
grey frame — and renders it in a register the product does not want. **Do not retry it with a better
prose prompt; the register is the problem, not the wording.**

## Carried out of this branch

- **`.minions/v0.13_backlog.md` · B1 — pod readiness gates.** Deferred to a version, not to this
  prototype, on the operator's decision of 2026-09-08. The five-gate sequence a third-party case study
  proposes for RunPod's endpoint-admission failures; three of the five now exist in this branch's
  `infra/up.sh`, and **`main` has none of them**. Includes one item that is a real defect rather than an
  improvement: every SSH here uses `StrictHostKeyChecking=no`.
- **`.minions/` is gitignored and this branch never merges**, so that file carries nothing on its own.
  It reaches a release only by being exported to the operator's own backlog or restated inside a change.

## Housekeeping, in this order

- [x] **the prototype tree, tidied — 2026-09-10.** What is *current* is now legible from `ls` rather than
      from memory. `styles/` holds exactly the three files the live flows read; round 1's eleven graphs
      and manifests moved to [`archive/styles/`](archive/styles/) with their runners repointed, and two
      notes whose questions are closed — `GPU.md` (keep the card) and `SYNTHETIC_PORTRAITS_FIX.md`
      (fixed, the portraits generated) — moved beside them.

      **`renders/` and `derived/` are bucketed by UTC date.** Forty sibling run directories with nothing in
      the name to say which session made them is not a record:

      ```
        prototype/renders/2026-09-08/n9_ablation/<sid>/0.png
        prototype/derived/2026-09-09/n24_real_photo_final_contact_sheet.html
      ```

      `prototype/paths.py` is the seam. **`render_dir(name)` / `derived_dir()` write** and always mean today;
      **`resolve_render(path)` reads** and finds an undated `prototype/renders/<run>/…` under whichever
      bucket holds it. That is why `contact_sheet.py`'s forty column templates still name no date.
      **Two things under `derived/` are deliberately not dated** — `vlm_drafts/` and `reference_sheets/` —
      because they are named references other scripts open, not artifacts of a day.

      Two pre-existing defects surfaced and were fixed in the same pass: every contact sheet's
      click-through links were `../..`-relative and broke the moment a page moved a level deeper (the
      depth is now derived from where the page lands, and the nine old pages were rewritten), and
      `contact_sheet.py`'s `n21_real_photo` sheet pointed at a run directory that has never existed — it was
      renamed `n21_real_photo_v2` and the sheet was never updated. **252 links across nine pages, 0 broken.**
- [x] **the third-party stylizer, retired — 2026-09-10.** Its six source renders, their nine canvas
      resamples and round 1's two external-eval score files moved to
      [`archive/fotor/`](archive/fotor/), and **`prototype/fotor/` no longer exists**. `style_axis.py`
      lost its comparison row and its calibration prose; `contact_sheet.py` and `hires.py` lost the two
      places that named a competitor as a target. `archive/retention.py` and `archive/thesis.py` were
      repointed at `archive/fotor/canvas/` so both still run. **Nothing live reads it, and the style bar
      no longer names it** — see § *The style bar, restated*. F1–F36 are untouched: those findings
      genuinely were about it, and rewriting them would falsify the record.
- [x] **round 1's galleries, archived — 2026-09-10.** The two rejected flows' ten-portrait galleries and
      the sampling-path sheet moved to [`archive/galleries/`](archive/galleries/), which emptied
      `derived/2026-09-07/` entirely — that whole day was round 1. `derived/` now holds only the two date buckets
      round 2 produced, plus `vlm_drafts/` and `reference_sheets/`.
- [ ] **free the Qwen space** — 28.89 GiB, reversible: `archive/styles/qwen_models.json` records every digest and
      source.
- [ ] **do NOT destroy the volume yet.** `decisions` §4 `probe`: *keep the old thing declared until the
      new one is proven; the irreversible act is a version's last, never its first.* Resize only after
      round 2 works — and RunPod volumes cannot shrink, so that means destroy-and-recreate, once, at the
      end.

---

## Resuming cold

**If a pod comes up with no public IP** (F31), `infra/up.sh` prints RunPod's HTTP proxy URL —
**but the proxy does not work for our client.** Cloudflare 1010-blocks stdlib `urllib` by user-agent;
`curl` passes and the render client does not. **F31 is still open**, and the tunnel is the only way in.
F33 records the amendment and the one-line fix that has not been tried.

```bash
git checkout v0.13_prototype          # never merges
uv sync --extra eval                  # torch/transformers/onnxruntime, ~3 GB
PYTHONPATH=.                          # every prototype script needs this

bash infra/up.sh                      # boot; prints the SSH + tunnel commands
ssh -i ~/.ssh/id_ed25519_runpod -N -L 8188:localhost:8188 root@<ip> -p <port>
bash infra/down.sh                    # ALWAYS, then verify the account is empty
```

**Do not chain `down.sh` onto the render command.** Stopping the task kills the teardown with it, and a
pod outlived its job that way on 2026-09-07. Tear down as its own step, then verify.

| what | where |
|---|---|
| six baseline subjects | `inputs/baseline/*.png` — round 1's, digests in `baseline/README.md` |
| round 2's ten portraits | `inputs/synthetic/*.png` — **tuned on**, every dial chosen against these |
| round 3's held-out ten | `prototype/inputs/synthetic/portfolio/` — never tuned on (N29) |
| the ten pose studies | `prototype/inputs/synthetic/pose/` — filenames are the pose labels (N25) |
| **17 real photographs** | `prototype/inputs/real/` — **gitignored, D14**; sheets and renders too |
| v0.12's 30 renders + scores | `outputs/baseline/<subject>/{0..4}.{png,eval.json}` |
| pinned eval models (2.3 GB) | `models/` |
| **the pinned reader (5.40 GiB)** | `models/joycaption/` — manifest, licence and revision in `prototype/styles/joycaption_models.json`; verify with `PYTHONPATH=. uv run python prototype/joycaption.py --verify` |
| every prototype render | `prototype/renders/<UTC-date>/<run>/` (gitignored) |
| round 1's comparison images | `prototype/archive/fotor/` (gitignored; digests in `notes/FINDINGS.md` F0) — **history; nothing live reads them** |
| the two presets | `prototype/archive/styles/*.md` and `*.json` — round 1, archived |
| criteria sheets | `prototype/sheets/{synthetic,real}/` — mirrors the input tree; `real/` gitignored |
| round 2's graph | `prototype/styles/fromnoise-v1.json` |
| round 2's runner | `prototype/fromnoise.py` |
| round 2's renders | `prototype/renders/2026-09-08/n3_fromnoise/<sid>/0.png` (gitignored) |
| round 2's measurement | `prototype/archive/n4_measure.py` |
| the face ladder | `prototype/face_ladder.py` → `renders/2026-09-08/n6_face/<arm>/<sid>/` |
| contact sheets | `prototype/contact_sheet.py --sheet <name>` → `derived/<UTC-date>/<name>_contact_sheet.html` |
| the combined run | `prototype/combined.py` → `renders/2026-09-08/n8_combined/<sid>/` |

**Live measurement scripts**, all run as `PYTHONPATH=. uv run --extra eval python <script>`:

| script | what it does |
|---|---|
| `style_axis.py` | posterisation + linework — **the style bar is stated in these units** |
| `criteria_eval.py` | WD14 reads a render and scores it against its sheet |
| `contact_sheet.py` | the instrument the operator actually reads |

**Round 1's measurement is archived**, because round 2 never used it and round 3 will not either.
`archive/hair_colour.py` (the colour machinery and the known-answer test that indicted the mode, F8),
`archive/retention.py` (background detail / background colour / garment colour, F14) and
`archive/thesis.py` (retention plotted against stylization) all still run — but every one of them is
**referenced to the photograph**, which is F16's disease and exactly the thing N27 exists to replace.
Read their findings, not their numbers.

**[`archive/`](archive/)** holds everything whose question is closed — round 1's pod-session runners
and its graphs, round 1's photograph-referenced measurement, the runners of round 2's finished arms
(`n4_measure.py`, `prompt_arms.py`), and two settled notes (`GPU.md`, `SYNTHETIC_PORTRAITS_FIX.md`).
**Records rather than tools; each one's result is in `notes/FINDINGS.md`, and every one of them still runs.**
[`archive/README.md`](archive/README.md) is the index. Two are worth reading before writing a new
runner: `archive/qwen_graph.py`, for recovering and flattening a deleted ComfyUI subgraph export into
something submittable, and `archive/external_eval.py`, for scoring a foreign render without fabricating
provenance.

**What is left at `prototype/`'s root is what round 3 touches** — which is the point of putting the rest
here. The library layer is not obvious from the filenames and is worth stating: `fromnoise.py`,
`face_ladder.py`, `combined.py`, `ablation.py` and `ladder_position.py` each drove a finished arm **and**
export the constants or the graph builder every later runner imports (`GRAPH`, `SUGGESTED`, `INSTANTID`,
`CFG`, `CN_STRENGTH`, `build`). They are load-bearing, not leftovers, which is why they did not move.

**Read [`archive/SUMMARY.md`](archive/SUMMARY.md) before doing anything.** It carries what was tried and
failed, so it is not retried.
