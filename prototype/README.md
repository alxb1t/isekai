# Prototype — start here

**Branch `v0.13_prototype`. Does not merge.** A workshop for answering empirical questions cheaply
before a change is cut. Tuning by eye is allowed here and nowhere else: the rule that dials are settled
by numbers binds *versions*, and a branch that never merges settles nothing.

> ### Reading order
> 1. **this file** — status, the conclusion, and what happens next
> 2. **[`SUMMARY.md`](SUMMARY.md)** — the three flows compared, the eleven findings worth keeping
> 3. **[`FINDINGS.md`](FINDINGS.md)** — F1–F23, the full evidence, newest at the bottom

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
- [x] **closing summary** — [`SUMMARY.md`](SUMMARY.md)

**Parked deliberately**, each with its reason in [`SUMMARY.md`](SUMMARY.md): train a photo→anime style
LoRA · Flux.1 Kontext dev (its VAE is gated) · the within-base known-answer probe (T8, $0, never run) ·
`s5`'s refusal path.

---

## Round 2 — the from-noise flow

**Not started. This is what the next session is for.**

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
                              ^ booru tags read off the photo
              the photograph never enters the latent
```

Architecturally this is **v0.2's deleted `animagine` from-noise path plus a tagger**. It is the *third*
path v0.8 deleted as "superseded" that we have found reason to revisit — all three asserted by eye, with
no evaluator in existence at the time.

### Tasks

- [ ] **N1 · recover the graph** — `git show e324699^:workflows/animagine.json`, the same recovery that
      worked for `qwen-image-edit.json`. Confirm every node type exists on the shipped image **before**
      booting a pod.
- [ ] **N2 · build the variant** — `denoise 1.0` / empty latent · **InstantID kept** · **OpenPose kept**
      · **tile and lineart dropped** (both condition on the photograph's *appearance*, which is the
      thing being removed) · subject description **hand-written**, not tagged.
- [ ] **N3 · one session** — the four real photographs in `outputs/original/darya` plus two synthetics,
      so results are comparable to `ladder/90_tattoo/` and `ladder/30_gallery/`. ~$0.20.
- [ ] **N4 · measure** — linework and posterisation against the same photographs, plus pose PCK.
- [ ] **N5 · decide** — if the blur goes, this is the flow and the evaluator gets re-cut around it. If
      it does not, the softness is Illustrious's rather than the method's, which is also worth knowing.

### The bar, stated before the render

**Median linework at or above the photograph's own**, against `notile-d045`'s **0.0030** and inputs
running 0.005–0.078. Anything that merely beats 0.0030 without reaching the photograph is the same
failure at a smaller scale.

**Hand-written tags on purpose.** There is no point integrating WD14 if the flow does not render
cleanly, and a typed description removes the tagger as a second variable. The tagger is step 2 and is
already researched.

### What round 2 changes downstream — decide knowingly

**The identity criteria become pose · haircut · eyes · face · clothes.** Background and accessories drop
out: from-noise cannot preserve a background, so measuring it would measure nothing. **Eyes** earn their
own axis — drift appeared in F12 and F18 repeatedly.

**And it breaks the shared-mask trick.** Every region axis assumes the render is the photograph's pixel
grid. A from-noise render will not align, so the evaluator must **parse both images independently** —
running segformer on the *anime* image, the exact thing the original design was built to avoid. That is
the fallback the method of record already names for a guard failure. Real work, real accuracy cost.

### Housekeeping, in this order

- [ ] **free the Qwen space** — 28.89 GiB, reversible: `styles/qwen_models.json` records every digest and
      source.
- [ ] **do NOT destroy the volume yet.** `decisions` §4 `probe`: *keep the old thing declared until the
      new one is proven; the irreversible act is a version's last, never its first.* Resize only after
      round 2 works — and RunPod volumes cannot shrink, so that means destroy-and-recreate, once, at the
      end.

---

## Resuming cold

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
| four real photographs | `outputs/original/darya/` — a real person; renders stay gitignored (D14) |
| v0.12's 30 renders + scores | `outputs/baseline/<subject>/{0..4}.{png,eval.json}` |
| pinned eval models (2.3 GB) | `models/` |
| every prototype render | `prototype/ladder/` (gitignored) |
| Fotor comparison images | `prototype/fotor/` (gitignored; digests in `FINDINGS.md` F0) |
| the two presets | `prototype/styles/*.md` and `*.json` |

**Live measurement scripts** — the four round 2 needs, all run as
`PYTHONPATH=. uv run --extra eval python <script>`:

| script | what it does |
|---|---|
| `style_axis.py` | posterisation + linework — **round 2's bar is stated in these units** |
| `hair_colour.py` | the colour machinery, and the known-answer test that indicted the mode |
| `retention.py` | background detail / background colour / garment colour |
| `thesis.py` | plots retention against stylization, for comparing flows |

**[`archive/`](archive/)** holds round 1's eleven pod-session runners. Records rather than tools — each
one's result is in `FINDINGS.md`. Two are worth reading before writing round 2's runner:
`archive/qwen_graph.py`, for recovering and flattening a deleted ComfyUI subgraph export into something
submittable (round 2 must do the same for `workflows/animagine.json`), and `archive/external_eval.py`,
for scoring a foreign render without fabricating provenance.

**Read [`SUMMARY.md`](SUMMARY.md) before doing anything.** It carries what was tried and failed, so it is
not retried.
