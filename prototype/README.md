# Prototype — start here

**Branch `v0.13_prototype`. Does not merge.** A workshop for answering empirical questions cheaply
before a change is cut. Tuning by eye is allowed here and nowhere else: the rule that dials are settled
by numbers binds *versions*, and a branch that never merges settles nothing.

> ### Reading order
> 1. **[`HANDOFF.md`](HANDOFF.md)** — **start here in a fresh thread.** What exists now, the settled
>    configuration, the laws, and what is still open. This file is the ledger behind it.
> 2. **this file** — the task list and its history: every question asked, and what closed it
> 3. **[`CRITERIA.md`](CRITERIA.md)** — round 2's design: the sheet, the seven scored criteria, both bars
> 4. **[`ILLUSTRIOUS.md`](ILLUSTRIOUS.md)** — what the base was trained on, and what to prompt it with
> 5. **[`FINDINGS.md`](FINDINGS.md)** — F1–F36, the full evidence, newest at the bottom
> 6. **[`archive/SUMMARY.md`](archive/SUMMARY.md)** — round 1's close: the flows compared, and what
>    not to retry
> 7. **[`archive/GPU.md`](archive/GPU.md)** — settled: keep the card, and a render is not where the
>    money goes

---

## Status: round 1 complete. Both candidate flows rejected.

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
[`FINDINGS.md`](FINDINGS.md) **F24**.

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
      2026-09-08 and written up in **[`CRITERIA.md`](CRITERIA.md)** before any render.
- [x] **N1 · ~~recover the graph~~ — not needed.** `animagine.json` does not have to be recovered: the
      shipped `workflows/pipeline.json` becomes from-noise with **four edits**, and every node type is
      already on the image. See `CRITERIA.md` §7.
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
      **[`ILLUSTRIOUS.md`](ILLUSTRIOUS.md)**, primary source the Illustrious paper. Confirms the
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
- [→] **N20 · the style LoRA** — **carried into round 3 as N30.** Round 1's parked lever, still parked;
      prompt, dials and the hires pass are all spent.
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

### Round 3 — the session of 2026-09-10

**Seven questions, worked one at a time.** Both flows now clear their bars and the operator has said the
renders are what he wants; what is left is not rescue but **knowing why they work** — which of the levers
is load-bearing, and how we would tell if one stopped being.

**Round 2 closed with three items still carrying work, and all three are here** — nothing was dropped in
the renumbering, and nothing was closed by being moved:

| round 2 | round 3 | why it moved |
|---|---|---|
| **N14** the axis nobody has built | **N27** | restated with the two flows separated. Still unsolved |
| **N9c** judge `A`/`D` on identity | **N27**, as its first step | $0, no pod, renders already on disk |
| **N20** the style LoRA | **N30** | still parked — but for a *different reason* now; see N30 |

**N31 joins them from HANDOFF §6c** — the reader's `body shape` blind spot, $0, and it comes
before N26 so that a briefing bug in the incumbent reader is not scored as a reason to replace it.

**N27 comes first in practice.** An evaluator decides which arms are worth $0.0044 each, and every
previous round that built the scoreboard second measured the wrong thing — F16 in round 1, F29 in round 2.

```
   N27 evaluation  ──▶ decides what N25 and N28 have to measure
        │                (its first step is free: judge by eye, on disk)
        ├──▶ N25 pose tags   ─┐
        │                     ├──▶ ONE pod session, one boot
        └──▶ N28 hires for A ─┘
        │
        └──▶ N30 style LoRA — blocked ON N27: without an identity number
                              there is no way to tell what a LoRA costs
   N31 reader fix    — $0, and comes BEFORE N26 (fix the incumbent, then survey)
        └──▶ N26 VLM research — $0, independent, runs alongside everything
   N29 new portraits — needs N25/N28 settled, so its renders test a decided flow
```

- [ ] **N25 · does flow `A` need pose tags at all?** The open item HANDOFF §5 named and never ran.
      Flow `A` carries a DWPose skeleton *and* a `pose` field in the prompt; nobody has removed one and
      looked. Two facts make it worth the render: **pose is the VLM reader's weakest field on both real
      and synthetic photographs (0.57/0.58)** — the only field indifferent to input type, which points at
      a vocabulary limit rather than a reading limit — and **F27 measured that the legs compete with the
      tags**, so a tag the skeleton already carries is not free, it is paid for in style.

      **The two flows get two prompts, and that is the point.** `D` has no skeleton and *must* keep the
      pose tags; `A` may not need them. One prompt for both was never a decision, only an inheritance.

      **Design, settled before the render: strip the tags in the runner, never in the sheet.** The sheet
      is the evaluator's ground truth (`CRITERIA.md` §1). Emptying `2 · pose` in the sheet would remove
      the tags from the prompt *and* remove the scoreboard's knowledge of what the pose was — the
      question would become unaskable at the moment we started asking it. So `assemble()` takes a set of
      fields to drop, the sheet is untouched, and both renders are scored against the same `pose` row.

      Open sub-question: **`framing`** (`cowboy shot`, `upper body`) sits beside `pose` in `ORDER` and is
      a *crop* tag, not a body tag. DWPose keypoints land at the photograph's own coordinates, so the
      crop is arguably carried too — untested, and worth its own arm rather than being bundled.

- [ ] **N26 · is there an open model that reads a photograph as well as the agent session does?** ($0,
      research only.) The reader in `vlm_reader.py` is **an agent session, not a dependency** — it scored
      0.78 on ten synthetic photographs and 0.80 on three real ones, with ~1% invented tags. That is
      good, and it is also **not reproducible by anyone who does not have this transcript**, which is a
      problem for a repository whose thesis is *open models, end to end*.

      What to establish, and nothing more — this is a survey, not a bake-off:
      **local candidates** (Qwen2.5-VL, InternVL, Molmo, JoyCaption — the last is trained on booru-style
      description specifically); **hosted candidates** on OpenRouter, with their licence and cost;
      **the honest baseline**, which is that WD14 already exists here and **F29 measured it at 0.47 on
      photographs against 0.73 on renders, with `pose` at 0.08 and `marks` at 0.00** — it is a tagger for
      drawings and it cannot read a photograph. Any candidate has to beat that, not merely exist.

      **The distinction that keeps getting lost:** `selected_tags.csv` validates a sheet's vocabulary and
      the WD14 *model* reads a render. Neither is the photograph reader. Three different jobs.

- [ ] **N27 · what does "the identity transferred" actually mean, and how is it scored — per flow?**
      **Carries round 2's N14 and N9c**, which are closed there and live here. It is the honest hole in
      the project, and renumbering it has not made it smaller.

      > Round 1 instrumented similarity-to-photograph, so the least-stylized render won by construction.
      > Round 2 instruments adherence-to-description, so the flow that never reads the photograph wins by
      > construction — F29 scores `D` above `A` (0.77 vs 0.73) precisely because it is blind to the thing
      > that separates them. **Both scoreboards were complete on their own terms and both missed the
      > same axis.**

      Two questions, and they have different answers:

      **Does comparing `A` against the photograph make sense?** Partly. `A` reads the photograph, so a
      photograph-referenced measure is at least *askable* of it — but any pixel or colour distance
      punishes correct stylization, which is exactly F16's disease. What survives stylization is
      **geometry** (where the keypoints are) and **attributes** (what is true of the person), not pixels.

      **What is the mechanism for `D`?** `D` never reads the photograph, so photograph-referenced scoring
      is meaningless for it — but the criteria sheet *was* read from the photograph by a human, which
      makes the sheet a **transcription of the photograph** rather than an independent prompt. So the
      right question for both flows is the same one: **how many of the identity criteria visible in the
      photograph survive into the anime image** — with `A` free to be additionally scored on geometry,
      because it alone has a skeleton to be faithful to.

      The bar already stated: **6 of 7 criteria, pose and hair silhouette mandatory.** What is missing is
      an instrument that can read the criteria off *the photograph* as reliably as off the render — which
      is precisely what N26 is researching, and why the two are the same problem seen from two ends.

      **First step, and it costs nothing — this is round 2's N9c.** Judge `A` and `D` on identity *by
      eye*, on renders already on disk:
      `prototype/derived/2026-09-08/n9_ablation_contact_sheet.html`. No pod, no evaluator, no code. It
      comes first because **an instrument is built to agree with a judgement, and the judgement has to
      exist first** — F1 is the record of building an evaluator before the thing it judged and getting a
      coin flip back. What the eye finds here is what N27's mechanism has to reproduce.

- [ ] **N28 · does flow `A` need the hires pass?** `D` gains on both axes; `A`'s case is weaker, and
      the operator's eye says it looks fine without:

      | | posterisation | linework |
      |---|---:|---:|
      | `A` no hires | 0.363 | 0.0145 |
      | `A` + hires 0.50 | 0.373 (+0.010) | 0.0181 (**+25%**) |
      | *determinism floor* | *±0.0020* | *±0.0003* |

      **The gain is almost entirely linework; posterisation moves 0.010 — five times its floor, so it is
      real, but small.** Both deltas clear noise, which makes this a cost question rather than a
      measurement one. Whether
      that is worth a second sampler pass is a cost question the numbers alone do not settle, so it is
      being decided *after* N27 gives an identity number to weigh against the style one. Rides on N25's
      pod session at no extra boot cost.

- [ ] **N29 · the new synthetic portfolio portraits.** Generated 2026-09-10 — the `synthetic_portraits`
      blocker is closed and its note is in [`archive/`](archive/SYNTHETIC_PORTRAITS_FIX.md). Ten images,
      at **`prototype/inputs/synthetic/`**.

      **They are the first inputs this flow has not been tuned on** — the closest thing to a held-out set
      the prototype has, and the only chance to find out whether two rounds of dials generalise or were
      fitted to ten faces. **Run them after N25 and N28 settle**, so what they test is a decided flow
      rather than a moving one.

      **That is why round 2's ten stay at `inputs/synthetic/` and do not move into the new tree**
      (decided 2026-09-10). The two sets are *tuned-on* and *held-out*, and a directory that mixes them
      makes the distinction invisible at exactly the moment it matters. `fromnoise.PHOTOS` still points
      at the old path and every closed finding still reads.

      **Sourcing criteria are on disk** — [`inputs/README.md`](inputs/README.md) carries what makes a
      good test photograph here (six hard axes, and what the current set covers), why real photographs
      come from **model-released stock** rather than a search engine, and why a **celebrity is a
      methodological trap**: Illustrious has famous faces memorised, so one renders recognisably with or
      without InstantID — which makes `A` and `D` indistinguishable, the exact comparison N25 and N27
      exist to run.

      **Their ids are undecided, deliberately.** They arrive as
      `02_00_raw_photo_upper_body_portrait.png`, while every sheet, render directory and evaluator key in
      this prototype is built from a 5-digit id. Renaming them costs nothing *now* and would be guessing
      at how many deserve sheets; the id scheme is settled when N29 starts, not before.

- [ ] **N30 · the style LoRA — round 2's N20, still parked.** The last lever nobody has pulled. Prompt,
      dials and the hires pass are all spent, and F22 argued in round 1 that a **trained style adapter**
      is the thing that would close a register gap the open ecosystem does not otherwise provide for
      photo→anime.

      **It is parked rather than open, and the reason changed on 2026-09-10.** It was carried as "the
      only remaining lever for `A`'s 19% posterisation gap" — and that gap was measured against a
      third-party reference this project has now retired. **There is no gap.** `A` is what the operator
      wants. So a LoRA is no longer a fix for a deficit; it is a *different look*, which is a product
      decision and not a measurement one.

      What round 1 established, so it is not re-derived: it needs only **unpaired** style images, and
      **it must not be trained on our own renders** — F7 measured that style as soft and under-drawn, so
      the corpus would teach the deficiency. Any candidate corpus is scored on the style axis *before*
      any GPU time is spent. **Do not start this before N27**, or there is no way to tell whether a LoRA
      cost identity.

- [ ] **N31 · re-brief the reader on `body shape`** ($0, no pod). It scores **0.00 on real photographs** —
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

### The bar, stated before the render

There are **two** bars, and a flow must clear both. Round 1's conclusion was that the operator's
preference split the flows against their own numbers; a single-bar round 2 walks back into that.

**Style.** Median linework at or above the photograph's own, against `notile-d045`'s **0.0030** and
inputs running 0.005–0.078. Anything that merely beats 0.0030 without reaching the photograph is the
same failure at a smaller scale.

**Identity.** **5 of the 6 scored criteria survive, and pose and hair silhouette are mandatory.**
Stated in full, with why 6-of-6 was rejected, in [`CRITERIA.md`](CRITERIA.md) §4.

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

**Settled 2026-09-08 in [`CRITERIA.md`](CRITERIA.md).** The scored criteria are **pose · hair
silhouette · hair colour · eyes · clothes · marks**. Background drops out entirely; accessories, body
shape, expression and skin tone stay in the prompt but are judged by eye, each for a stated reason.

**And the ground truth moved.** Because the tags are hand-written, the evaluator scores the render
against **the criteria sheet**, not against the photograph. That kills F16's inverted metric at the root
— no colour distance to a photograph appears in the scored set, so correct stylization is never
punished — and it makes the broken shared-mask assumption stop mattering, since an attribute check needs
no pixel alignment. The cost, stated in `CRITERIA.md` §1: the scoreboard now measures **prompt
adherence**, and inherits whatever the human transcription got wrong.

### Carried out of this branch

- **`.minions/v0.13_backlog.md` · B1 — pod readiness gates.** Deferred to a version, not to this
  prototype, on the operator's decision of 2026-09-08. The five-gate sequence a third-party case study
  proposes for RunPod's endpoint-admission failures; three of the five now exist in this branch's
  `infra/up.sh`, and **`main` has none of them**. Includes one item that is a real defect rather than an
  improvement: every SSH here uses `StrictHostKeyChecking=no`.
- **`.minions/` is gitignored and this branch never merges**, so that file carries nothing on its own.
  It reaches a release only by being exported to the operator's own backlog or restated inside a change.

### Housekeeping, in this order

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
| six baseline subjects | `inputs/baseline/*.png` — digests in `baseline/README.md` |
| ten synthetic portraits | `inputs/synthetic/*.png` |
| four real photographs | `outputs/original/real_photo/` — a real person; renders stay gitignored (D14) |
| v0.12's 30 renders + scores | `outputs/baseline/<subject>/{0..4}.{png,eval.json}` |
| pinned eval models (2.3 GB) | `models/` |
| every prototype render | `prototype/renders/<UTC-date>/<run>/` (gitignored) |
| round 1's comparison images | `prototype/archive/fotor/` (gitignored; digests in `FINDINGS.md` F0) — **history; nothing live reads them** |
| the two presets | `prototype/archive/styles/*.md` and `*.json` — round 1, archived |
| round 2's criteria sheets | `prototype/sheets/*.md` — ten, reviewed 2026-09-08 |
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
**Records rather than tools; each one's result is in `FINDINGS.md`, and every one of them still runs.**
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
