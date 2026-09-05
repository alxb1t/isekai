# Phase 5 — the probe, and what it did and did not establish

One pod session, on `ghcr.io/alxb1t/isekai:v0.10-rc`, RTX PRO 4500 Blackwell in EU-RO-1.

| | |
|---|---|
| Pod | `vmdj0g7s6uekwm` |
| Created | 2026-09-05T13:32:12Z |
| Torn down | 2026-09-05T13:50:39Z |
| Wall clock | **18 min 27 s** (ceiling 45 min) |
| Rate / cost | $0.72/hr → **$0.22** (ceiling ~$0.30) |
| Teardown confirmed | RunPod MCP `get-pod` → `404 {"detail":"pod not found"}`; `list-pods` → `{"items": [], "total": 0}` |

WAI provisioned alongside Animagine at boot, from the manifest, verified: the file landed at
**6,938,040,682 bytes**, exactly the count `models.json` declares, and `download_models.sh` accepted
its digest. Provisioning took 7 min 20 s of the session (13:36:35 → 13:43:55), which is the download
of a 6.9 GB checkpoint onto the volume and is not repeated on a later boot.

**The images are not here.** They are in gitignored `outputs/`, because the manifest and the seeds
reproduce them and this repository claims reproducibility over the submitted workflow JSON, never
over pixels (design.md D9). What is here is what was submitted.

## 1 — ControlNet strength-to-zero, at a fixed seed · `controlnet-comparison.json`

Mechanical and falsifiable: does the conditioning reach the sampler at all? Not whether the result
is prettier. Photo `darya_original.jpeg` (982×1559 → **1024×1600**), sampler seed `1`, **no
mutation**, every dial held fixed — the one difference between the baseline and each comparison
render is the strength of the ControlNet under test, taken to exactly `0.0`. Harness:
`controlnet_probe.py`, beside this directory, because the product CLI has no per-ControlNet flag and
`mutate` jitters every strength on every run.

| ControlNet | Tuned | Verdict at `0.0` |
|---|---|---|
| TTPlanet Tile | 0.2 | **Strongly distinguishable.** Hair length, garment and framing all change — trousers become a dress, long hair becomes short, the subject is rendered closer. |
| xinsir OpenPose | 0.6 | **Distinguishable, subtly.** Pose, garment and composition survive; background architecture and fine face/hair detail move. |
| MistoLine | 0.2 | **Distinguishable, subtly.** Composition and garment survive; shading and background detail move. |

**None is indistinguishable from absent, so none is deleted.** That includes tile, which design.md
D7 named as the likely deletion — the comparison was allowed to say either thing and it said this
one. Tile is therefore kept, and TTPlanet's card disclaimer ("no comic, animation application are
promised", recommended strength 0.9 against the 0.2 this graph runs) is recorded against it as a
known deviation rather than resolved.

**What this does not establish.** Not that any of the three *improves* the render — only that each
measurably changes it. Diffusion is chaotic and any conditioning change perturbs the output, so
"distinguishable" is a floor, not praise. The subtle verdicts for OpenPose and MistoLine are weaker
evidence than tile's and are recorded as such.

## 2 — `denoise` and `ip_weight` · `chosen-dials.run.json`

**A preference, not a measurement** (design.md D9). Found by eye against `darya_original.jpeg` at
seed `1`, one render per point:

| denoise | ip_weight | Against the photo |
|---|---|---|
| 0.55 | 0.9 | Composition and the clutch retained; reads more photographic than anime. |
| **0.65** | **0.9** | **Chosen.** Composition, pose and the clutch retained; face keeps the photo's cues. |
| 0.75 | 0.9 | Drifts — garment becomes a dress, the clutch nearly disappears, background washes out. |
| 0.65 | 0.7 | Composition retained; the face reads slightly further from the photo than at 0.9. |

**The chosen values are the ones already in the graph.** They were tuned on Animagine and there was
no reason to expect them to transfer, so this was a real search with a null result, not a decision
skipped. It was also a **coarse** one — four renders, three denoise points and one ip_weight point,
bounded by a 25-minute budget at $0.72/hr. *Chosen* is not *best*.

## 3 — The gender check · `gender-check.run.json`

The one falsifiable acceptance criterion the register change gets, and it could have failed.

Photo `synthetic_portrait_00004_.png`, a male-presenting subject (832×1216 → **1024×1472**), seed
`1`, at the new register with `1girl` removed. **The output is unambiguously male-presenting** — an
adult man in a suit and open collar, with the photo's grey hair and facial structure carried
through. `PASS`.

So on this input the gender axis is supplied by the identity node's embedding, as design.md D5
argued it would be. One photo is one photo: this is an existence proof that the mechanism works, not
a rate.

## The thing to check first, next version

D4 predicted it and the renders are consistent with it: dropping `realistic, photorealistic` from
the negative removed a push *away* from the photograph, and these outputs read as **semi-realistic
digital painting rather than flat anime screencap**. The register also lost `1girl`, which
under-specifies further (D5's stated risk). Neither is a reason to reinstate a gender tag. It is the
first finding for the evaluator version, which is the one that can measure it.

---

# Phase 7 — the final renders on WAI, at stated input resolutions

A second pod session, same image, no rebuild: nothing dropped out of the graph in phase 6, so the
manifest `:v0.10-rc` carries still matches it. WAI was already on the volume, so ComfyUI answered
67 seconds after boot rather than after a 7-minute download.

| | |
|---|---|
| Pod | `x6uekk15wpmjso` |
| Created | 2026-09-05T13:56:19Z |
| Torn down | 2026-09-05T14:04:42Z |
| Wall clock | **8 min 23 s** (ceiling 45 min) |
| Rate / cost | $0.72/hr → **$0.10** (ceiling ~$0.30) |
| Teardown confirmed | RunPod MCP `get-pod` → `404 {"detail":"pod not found"}`; `list-pods` → `{"items": [], "total": 0}` |

`RUNPOD_IMAGE` was cleared from the untracked `.env` afterwards. A stale value silently pins every
later pod to an unreleased image.

Two photos, two aspect ratios, the full `convert.py` path at its default five variations and a fixed
`--seed 7`. Both runs exited 0 and wrote `0.png`–`4.png` plus `run.json`.

| Photo | Input | Aspect | Rendered | Run |
|---|---|---|---|---|
| `darya_original.jpeg` | 982×1559 | 1:1.588 | **1024×1600**, all five | `final-darya.run.json` |
| `synthetic_portrait_00004_.png` | 832×1216 | 1:1.462 | **1024×1472**, all five | `final-synthetic.run.json` |

Every rendered dimension equals the target `working_resolution` computes from the photo's own
header — the first live confirmation of phase 2's scale node and header parser, on real files
rather than fixtures. **Both photos were scaled up** (832 and 982 short sides, to 1024), so these
two exercise only that direction. A photo above 1024 on its short side is not covered here; the
down direction is proven by the suite and not on a GPU.

## What this establishes, and what it does not

**Establishes:** the path runs end to end on WAI-illustrious-SDXL v17.0, at the two stated input
resolutions, through the unmodified CLI, writing five variations and a run manifest per photo.

**Does not establish** — stated because v0.8's Verified block implied a generality it never tested:

- **Nothing about identity, fidelity or quality.** No evaluator exists; none was run.
- **Not that the chosen dials are good**, let alone optimal. They are a preference from four
  renders (phase 5).
- **Not that any ControlNet improves the output** — only that each retained one measurably changes
  it.
- **Not that the register improves anything.** What the register change earned is one falsifiable
  result: a male photo yields a male-presenting output.
- **Not that the path runs at any resolution.** Two portrait inputs, both below the working scale.
  A landscape photo and a photo above 1024 on its short side are untested.
