# The v0.12 baseline — six subjects

The inputs to v0.12's metered session: six subjects, each chosen to break a metric rather than to
cover humanity (`design.md` D11). Thirty renders — six subjects × five seeds, **dials held** — are what
the evaluator is calibrated against.

**The pixels are not here.** This repository commits `run.json` artifacts and never inputs, and
committing derived faces into a project whose product is identity preservation invites a confusion the
README would then have to disclaim (`design.md` D14, D15). What is here is the recipe —
`build_subjects.py` — and the SHA-256 of every file it produces, so a re-run can be **checked** rather
than trusted. One version does not silently reverse a convention the previous one wrote down; this is
`probe/build_inputs.py`'s treatment, applied again.

## The recipe

```
python baseline/build_subjects.py --sources <synthetic portraits> --out <dir>
```

The sources are nine synthetic portraits, all 832×1216. Synthetic on purpose: no real person's
likeness enters the baseline, which makes the "do not commit derived faces" rule a matter of
convention here rather than of consequence.

## The six

| subject | stored | render target | slot | labelled |
|---|---|---|---|:---:|
| `s1_control_blonde` | 832×1216 | 1024×1472 | control — uniform blonde, frontal | ✅ |
| `s2_control_brunette` | 832×1216 | 1024×1472 | control — brunette close-up, a **different hair colour**, so the two controls are not one case counted twice | ✅ |
| `s3_multitone_balayage` | 832×1216 | 1024×1472 | multi-tone — dark roots into blonde ends, curly. The dominant-colour metric returns one mode and this hair has two | ✅ |
| `s4_multitone_bob` | 832×1216 | 1024×1472 | multi-tone — dark brown with caramel highlights, short bob. Multi-tone again, stressing a **different** thing: a small hair region rather than a large one | ✅ |
| `s5_small_face` | 832×1216 | 1024×1472 | refusal path — a full-length figure whose face is ~1.3% of the canvas. Exercises the guard and the absent-face field | ❌ |
| `s6_landscape` | **832×554** | **1536×1024** | refusal path — the only landscape input this project has ever rendered on a GPU | ❌ |

**Four are labelled, two are not.** 40 judgements is 4 subjects × 10 within-subject pairs (`design.md`
D10). `s5` and `s6` carry no labels: a subject whose axes are *expected* to refuse cannot calibrate
anything, and asking the operator to compare renders the scorer declined to score would be asking a
question with no answer on the other side.

### On `s6`, which is derived rather than generated

The source set is entirely portrait. `s6` is a crop, exactly as v0.11's landscape probe input was, and
it reuses that input's 832×554 geometry so a difference between the two versions' landscape cases is
not a difference in the crop. The crop origin is `y=150` rather than the centre, because a centred crop
of a standing figure is a crop of its chest, and a subject with no face in it measures the scale node
while proving nothing about the rest of the graph.

What the landscape case is *for* is the injector's short-side rounding on the **height** axis:
832×554 resolves to a 1536×1024 target, an aspect ratio this pipeline has never rendered and a gap
`CHANGELOG.md` v0.11 names explicitly. A crop exercises that identically to a natively-framed wide
shot.

### Sources deliberately unused

Recorded so the selection is reviewable rather than merely asserted:

- **`00060`** — the same person and the same shoot as `s5` (identical lace robe). Two slots filled by
  one subject would put one person's renders on both sides of a *different subject* comparison.
- **`00061`, `00072`** — further uniform-blonde frontal portraits. That is the case `s1` already
  covers, and a third control measures the same thing a third time.

## Digests

Every file `build_subjects.py` produced, from two consecutive runs that agreed byte for byte.
ImageMagick stamps a PNG with the time it wrote it, so the recipe strips profiles and excludes the
date chunks — without that, a recorded digest would verify nothing.

| file | stored | sha256 |
|---|---|---|
| `s1_control_blonde.png` | 832×1216 | `dede5477591b55ec8aacd2a2173d6b3b0139ecd601ce36a9671d34b628e88ba6` |
| `s2_control_brunette.png` | 832×1216 | `8eb8668b09c1b3e5271566c3a87416a93dda89589cbba4bb1b38321f235776b5` |
| `s3_multitone_balayage.png` | 832×1216 | `e4fb82b3e03801bafcce3e8485aa7287e4906e1647a548638676857c31d400c8` |
| `s4_multitone_bob.png` | 832×1216 | `12e0aa923fb05edda4c4ab873019627ac241cee4b94603937437fca6589643ed` |
| `s5_small_face.png` | 832×1216 | `a9d4e1da055b46f566eb8bf035d8f144df1dd95da59ff7f692a08eb0ceeb2f12` |
| `s6_landscape.png` | 832×554 | `756ab89deabe79d2ac6464b9a7647fb96aa5def5b6f2c52ebc2b117bad75fdc8` |

## What the scorer reads from them, before any render exists

Measured locally, on CPU, against the pinned artifacts. This is not a result — it is the confirmation
that all six subjects are legible to the instrument at all, taken before a pod was created.

| subject | face box | hair area | keypoints ≥ 0.3 |
|---|---|---|---|
| `s1_control_blonde` | (363,209)–(694,554) | 0.1190 | 100 / 133 |
| `s2_control_brunette` | (210,289)–(759,898) | 0.3104 | 84 / 133 |
| `s3_multitone_balayage` | (592,305)–(766,508) | 0.0374 | 133 / 133 |
| `s4_multitone_bob` | (361,208)–(725,605) | 0.0882 | 84 / 133 |
| `s5_small_face` | (500,84)–(628,236) | 0.0198 | 133 / 133 |
| `s6_landscape` | (404,0)–(750,399) | 0.1592 | 100 / 133 |

The hair areas span 0.0198 to 0.3104 — a factor of fifteen, all of it above the scorer's 0.005 floor,
so no subject refuses its region axes for lack of pixels before the renders even exist.

**`s5`'s face was found in the photograph.** That is worth stating plainly, because `s5` was chosen as
a refusal-path subject and its refusal has therefore **not** been demonstrated here. What is measured
above is the *anime* face detector run against a photograph; whether it locates a face in `s5`'s
**renders**, where the subject is small and stylized, is a phase-8 question and is not prejudged.

## Residual risk, stated rather than discovered later

**If the source photographs are lost, this baseline becomes unreproducible, and the labels are the only
surviving artifact.** The digests above would then prove that some file once existed and nothing about
what it contained. That is the accepted cost of not committing derived faces (`design.md` D15); there
is no mitigation beyond keeping the sources, and it is written here so the trade is visible rather than
implicit.

---

# The metered session

One pod session, on `ghcr.io/alxb1t/isekai:v0.11-rc`, RTX PRO 4500 Blackwell in EU-RO-1.

| | |
|---|---|
| Pod | `<pod id>` (redacted; the identifier is account-scoped and the pod is destroyed) |
| Created | 2026-09-06T17:15:53Z |
| Torn down | 2026-09-06T17:35:51Z |
| Wall clock | **19 min 58 s** (planned against 25 min, ceiling 45 min) |
| Rate / cost | $0.72/hr → **~$0.24** (ceiling ~$0.30) |
| Teardown confirmed | RunPod MCP `list-pods` → `{"items": [], "pagination": {"total": 0, ...}}`; `get-pod <pod id>` → `404 {"detail":"pod not found","status":404,"title":"Not Found"}` |

Boot to a reachable ComfyUI took 5 min 10 s; the thirty renders took 13 min 16 s, about 26 s each.
The estimate in `tasks.md` was ~19 min ≈ $0.23, derived from v0.11's measured session — it was right
to within a minute.

The volume mounted and the models were already on it: `/opt/ComfyUI/models -> /runpod-volume/isekai`,
no fetch, and no failure marker at `/opt/isekai/provisioning-failed`. ComfyUI reported version
`0.34.0`, and the pinned core was confirmed on the pod itself —
`git -C /opt/ComfyUI rev-parse HEAD` → `250b2e9551a7bc7a8ebb5beb07e0fecd2983e04a`, the commit
`Dockerfile` names.

**`RUNPOD_IMAGE` was set to `:v0.11-rc` for this session and cleared immediately after**, so no later
pod silently boots an unreleased image.

## What was rendered

Six subjects × five seeds, **dials held** — the first fixed-dial renders this project has ever
produced. `convert.py` pulls each image over the tunnel and writes it locally, so nothing ever lived
only on the pod's ephemeral disk; the renders were verified complete before teardown, not after.

**The images are not here**, following v0.10's and v0.11's precedent: this repository claims
reproducibility over the submitted workflow JSON and never over pixels. What is committed is each
run's `run.json`, which now carries the provenance to identify what produced it.

| subject | renders | target | matches the injector | distinct seeds | dial sets |
|---|---|---|---|---|---|
| `s1_control_blonde` | 5 | 1024×1472 | ✅ | 5 | 1 |
| `s2_control_brunette` | 5 | 1024×1472 | ✅ | 5 | 1 |
| `s3_multitone_balayage` | 5 | 1024×1472 | ✅ | 5 | 1 |
| `s4_multitone_bob` | 5 | 1024×1472 | ✅ | 5 | 1 |
| `s5_small_face` | 5 | 1024×1472 | ✅ | 5 | 1 |
| `s6_landscape` | 5 | **1536×1024** | ✅ | 5 | 1 |

Every render's dimensions equal the target the injector computes from that subject's own photograph,
and every `run.json`'s `photo_sha256` matches the digest the builder recorded — so each batch is
provably the subject it claims to be.

**The landscape rendered.** `s6` is the first landscape input this project has ever put through a GPU,
at an aspect ratio — 1536×1024 — the pipeline had never produced. That closes the gap `CHANGELOG.md`
v0.11 named explicitly.

**The dials were held, and identically across all six subjects:**

```
denoise 0.65   cfg 5   ip_weight 0.9   cn_strength 0.5
controlnet_strength  tile 0.2   pose 0.6   lineart 0.2
```

One dial set per subject, five distinct sampler seeds per subject. That is what makes these thirty
renders a baseline rather than thirty samples of a distribution: within a subject they differ in
exactly one thing.

**No quality claim is made here.** Whether these renders preserve identity is what phases 8–10 are for,
and the answer is the operator's eye rather than this table.

---

# The three probes

CPU, local, **$0**, against the thirty renders above. Their purpose is to decide what the instrument
is allowed to claim before any of it is correlated against a human judgement.

## Probe 1 — the guard, both ways. **Both hold.**

Computed on all thirty renders at the working denoise of 0.65.

| method | median | worst | threshold | passes |
|---|---|---|---|---|
| box IoU | 0.950 | 0.857 (min) | ≥ 0.30 | **30 / 30** |
| face-box centroid offset | 0.012 | 0.024 (max) | ≤ 0.25 | **30 / 30** |

So `design.md` D9's pre-committed fallback — *if neither holds, the region axes refuse and that
refusal is what v0.12 ships* — **did not fire**. Both methods locate the face in every render, with
wide margins.

**Box IoU ships as the authoritative guard**, pinned in `isekai/evaluate.py` as
`AUTHORITATIVE_GUARD_METHOD` and held by a test. The reason is about the measurement, not the
margins: **IoU constrains size as well as position, and the centroid method constrains only
position.** A render that placed a correctly-centred face at three times the scale passes the
centroid test and fails IoU — there is a test asserting exactly that — and such a render is the kind
the guard exists to catch. IoU is also the less permissive of the two here, sitting 2.9× from its
threshold where the centroid method sits 10.4× from its own.

**What this does not show.** No render in the baseline recomposed the subject, so this measures that
the guard does not produce **false refusals**. It does **not** show that either method catches a
genuinely recomposed render, because there was not one to catch. The centroid method stays computed
and printed on every run, so the day the two disagree is a visible event rather than a silent one.

**`s5`'s refusal path was not exercised.** It was chosen as a refusal-path subject, and the detector
found its face in all five of its renders (IoU 0.857–0.898 — the batch's lowest, but far above the
floor). The absent-face and guard-failure paths therefore remain covered by unit tests and by nothing
in the baseline. That is a gap in the baseline, stated rather than papered over.

## Probe 2 — does StyleID separate a same-subject batch from a different subject?

Six subjects: 30 same-subject pairs (a photograph against its own renders) and 150 different-subject
pairs (a photograph against another subject's renders).

| | StyleID | ArcFace *(sanity channel)* |
|---|---|---|
| same-subject median | 0.4667 | 0.3056 |
| different-subject median | 0.2068 | 0.1176 |
| clean separation (min same > max diff) | **No** | **No** |
| overlap | 98 / 150 | 106 / 150 |
| **AUC** | **0.847** | 0.788 |
| rank-1 identification | **4 / 6** | 4 / 6 |

**The answer is a qualified yes, and the qualification is the point.** StyleID carries real signal —
an AUC of 0.847 is a long way from the 0.5 of a coin flip, and the two medians are more than two-fold
apart. But it does **not** separate cleanly: 98 of 150 different-subject pairs score at or above the
worst same-subject pair, and two of the six subjects are closer to somebody else's renders than to
their own. `s3_multitone_balayage` and `s5_small_face` both miss.

**This probe could have killed StyleID and did not. It cannot license it either, and n=6 is why.**
Six subjects is far too few to establish a threshold, and no threshold is set here. What the probe
buys is the knowledge that the axis is not noise before it is correlated against human judgement.

StyleID outscores ArcFace on both AUC and median separation, which is consistent with the role
`design.md` D8 assigns each: StyleID is the primary and ArcFace only falsifies.

## Probe 3 — does DWPose read one of these renders at all?

**Yes — all thirty, with no refusals.** The axis reports a value for every render.

But the value is **saturated**, and that is the real finding:

```
PCK   median 1.000   min 0.976   max 1.000   across all 30 renders
```

Every render's pose agrees with its photograph almost perfectly. The OpenPose ControlNet sits at
strength 0.6 and holds the pose so tightly that, **at fixed dials, this axis has almost no
variance** — twenty-one of the thirty renders sit at exactly 1.000, so 18 of the 40 within-subject
pairs are exact metric ties and the correlation is computed over the 22 that could be scored.

**These numbers were recomputed at converge**, after the pose reader's preprocessing was brought onto
the pinned artifacts' reference pipeline (a 1.25-padded aspect-preserving warp, ImageNet
normalisation, BGR input — see `CHANGELOG.md`). The re-run is local and free: the same renders, the
same photographs, the same models. **Only the pose axis moved**; every other axis in all thirty
records is byte-identical to what the metered session produced, which is what makes this a
recomputation rather than a new measurement.

**The pose axis is not removed.** Probe 3's stated question was whether DWPose can read these renders
at all, and it can; nothing was killed by the probe it was given. The saturation is a finding *about
the pipeline* — pose is not where identity varies here — rather than a defect in the axis, and
deleting the column would hide that it was measured. It is likely to become informative the moment
the pose ControlNet's strength is searched, which is v0.13's business.

The keypoint-confidence floor is doing real work: 33–56 of the 133 whole-body keypoints are dropped
on four of the six subjects, and reported as dropped rather than scored at a guessed coordinate.
`s3` and `s5`, the two full-length subjects, keep all 133.

## What no probe changed

No dial was moved to make a meter work. `denoise` stays at 0.65, and the guard was measured at the
denoise the product actually uses — `design.md` D9 disqualifies the alternative in terms, and the
question did not arise, because both methods held.

**No axis was removed.** No probe killed the axis it tested.
