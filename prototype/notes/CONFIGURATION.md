# CONFIGURATION — the settled values, their provenance, and the traps around them

**Was `HANDOFF.md`; retitled and pruned 2026-09-13 at the close of round 5.** It had become two
documents wearing one title: a *"read me first in a fresh thread"* briefing, now replaced by
[`GRILLING.md`](GRILLING.md), and **the only tabulation of what the pipeline is actually set to.**
The briefing is gone. This is what was worth keeping.

**What was deleted, named so a dangling pointer resolves.** §3 (the `adopt`/`check`/`build` flow,
superseded by [`PRODUCT.md`](PRODUCT.md)), §4 and §5 (both fully in [`FINDINGS.md`](FINDINGS.md)), and
**§6c — round 4's brief**, which self-declared as stale and is what `../README.md`'s round-3 text still
points at. Its content is round 4's plan, and round 4 is closed in `../README.md` § *Round 4 closed*.

> **Under [`OPEN.md`](OPEN.md)'s **L8**, a flow declares its dials and its evaluation bar.**
> **This table is what v0.13's first flow manifest gets built from** — every value here becomes a
> declared field, and when it does, this note has done its job.

**Every value cites the finding that set it.** A value without one is not settled, it is inherited —
and this file says which is which. The evidence is in [`FINDINGS.md`](FINDINGS.md); nothing here
restates a finding's reasoning.

---

## 1 · The settled configuration

**Arrived at by measurement, not preference.** Graph: `prototype/styles/fromnoise-v1.json`.

| | value | where it came from |
|---|---|---|
| base | **WAI-illustrious-SDXL v17.0** | inherited |
| latent | `EmptyLatentImage`, **`denoise 1.0`** | **F24** — taking the photograph *out* of the latent is what removed the blur |
| `ip_weight` | **0.9** | **F25** — a ceiling, not a default; 1.2 streaks, 1.5 collapses |
| `cn_strength` | **0.8** | **F25** — the free lever: holds linework, best posterisation of any dial arm |
| `cfg` | **5** | **F26** — 7 measured worse; inside WAI's published 5–7 |
| sampler / steps | `euler_ancestral` / **28** | WAI's own recommendation — **not an untested lever** |
| clip skip | **−2** | every published WAI v17 sample generates there and none of its prose says so |
| hires | R-ESRGAN 4x+ Anime6B → **1.5x** → 20 steps | **F35** |
| hires denoise | **0.35**, for `A` and for `D` | **F39** — `A` moved from 0.50 on 2026-09-10. 0.50 was set on *style alone*; across all four axes 0.35 wins linework, identity and pose, and loses only posterisation by 0.014 |
| negative prompt | `bad quality, worst quality, sketch, censor, nsfw, lens flare, light particles, dust` | WAI's own speck fix. **Render-tested and confirmed** — `n24_real_photo_final` carried it |
| positive prefix | `masterpiece, best quality, amazing quality, newest, …` | **F34** — WAI's ladder at the *front* is +0.007, `newest` a further +0.006. **+0.013**, the first prompt *addition* to help since the definitional fixes |
| pose tags | **kept in the prompt** alongside OpenPose | **F38** — they complement rather than compete. Without them `arms_up` drops an arm, a shoulder off by 124° |

**The two flows, and `D` is `A` minus two nodes:**

```
  A   photo ─▶ InstantID (face) ─┐
             ─▶ OpenPose (skeleton) ├─▶ Illustrious ─▶ hires ─▶ anime image
      sheet ──────────────────────┘

  D   sheet ─────────────────────────▶ Illustrious ─▶ hires ─▶ anime image
      the photograph is never read at render time — and that makes D the CONTROL
```

`C` (InstantID only, no OpenPose) was tested and **rejected** against `A`.

---

## 2 · The bars

**Identity — unchanged since round 2:** **6 of 7 criteria**, with **pose and hair silhouette
mandatory**.

**Style — restated 2026-09-10**, when the third-party reference was retired. The bar is now **our own
last number**, and a drop beyond the determinism floor is a regression:

| | posterisation | linework |
|---|---:|---:|
| `A` + hires | **0.373** | **0.0181** |
| `D` + hires | **0.528** | **0.0376** |

**Determinism floors — needed to read any number at all:** linework **±0.0003**, posterisation
**±0.0020**, mean pixel |Δ| **≈2/255** across pods. **Anything smaller is GPU nondeterminism, not a
result.**

**Identity, measured N-way** (`IDENTITY.md` is the method): F40 8/10 at chance 10% · F41 14/17 at 5.9% ·
F46 SFace 9/17 independent · **F47 phone 8/10 photograph-level and 10/10 person-level**.

---

## 3 · Four corrections worth getting exactly right

**"hires greatly improves the quality" — true for `D`, mixed for `A`.** F35: `A`'s gain is mostly
**linework** (+25%), not flatness (+0.010). `D` gains on both (+47% / +0.025). Hires was the first
change in two rounds to move both axes at once.

**"validate booru tags" — not by the WD14 model.** **Two different things ship in one download:**

- **`selected_tags.csv`** — 8,106 real Danbooru tags with post counts. **This validates a sheet.**
- **the WD14 model** — reads a **render** and emits tags. **This is the evaluator**, at the far end of
  the pipeline, and **it cannot read photographs**: F29 measured 0.47 on photographs against 0.73 on
  renders, with `pose` at 0.08 and `marks` at 0.00.

**Keeping those distinct matters or the architecture diagram goes wrong.**

**The vocabulary check overclaims.** `selected_tags.csv` is the set WD14 *predicts* — a subset of
Danbooru above some post threshold. `sheet.py` prints *"not a Danbooru tag"*; **the honest statement is
*not in WD14's prediction set*, and therefore probably too rare for the base to have learnt.**
→ `MIGRATION.md` records this as a message to soften on the way across.

**`sheet.py build` regenerates the prompt from the table, and the prompt is the tempting thing to
edit.** The operator naturally edited the prompt block; `build` would have silently overwritten it.
**L9 removes this class of error structurally** — a sheet stores fields only — so this is history rather
than a live trap, recorded because the *shape* of it recurs.

---

## 4 · Working with the vocabulary

**Tag frequency predicts strength of effect.** `narrow waist` (9,411 posts) renders an **exaggerated**
waist, because the images Danbooru tags that way are ones where the waist *is* the feature. `medium
breasts` (770,389) is near-default and renders ordinary. **Do not use a rare tag to describe something
ordinary** — the same lesson as `pale skin`, which means *bleached*, not fair.

**When the tag you want does not exist, compose two that do.** There is no `white corset` (only `black`
and `brown`), so `white camisole, corset` carries colour and structure separately. A see-through dress
over a bikini is `turtleneck, see-through, bikini under clothes` — and `bikini under clothes` (15,818)
is a real tag that says **layering**, which listing two garments does not.

**Known gaps, found on the phone set (F47):** there is no `slim`/`slender`/`fair skin`/`hazel eyes`/
`thin eyebrows`, and no adult age band between the default and `mature female` (24,349). `skinny` exists
at 5,522 and **would exaggerate**. → these are the curation input for **N40's per-field enums**, v0.18.

---

## 5 · Infrastructure, cost, and one unresolved blocker

**RunPod returns pods that reach `RUNNING` with no public IP** — `runtime: null`, `ssh.direct: null`,
proxy only, **billing normally**. Nine of fourteen pods over two days, across two datacenters and two
GPU pools. No incident posted. Details in **F31**.

- **`infra/up.sh` bounds its wait and tears the pod down itself.** The poll was unbounded — the one
  thing in the repository that could bill indefinitely while looking like it was working.
- **`RUNPOD_GPU_TYPE` accepts a preference list.** The pinned Blackwell card exists in **only two
  datacenters** — an unrecorded single point of failure until it was.
- **The HTTP-proxy fallback does not work for our client.** Cloudflare 1010-blocks stdlib `urllib` by
  user-agent; `curl` passes. **F33 claimed it worked on the strength of a `curl` probe and was never
  render-tested.** The fix is a `User-Agent` header, **untried**.
- **`GET /object_info/<NodeName>` returns 200 for nodes that do not exist.** Fetch the full
  `/object_info` and look for the key.
- **A rejected or errored pod-creating call may still have created the pod.** Twice a rejected `up.sh`
  had already reached the API; once an MCP `create-pod` returned `422` and created one anyway. **Three
  orphaned pods, ~$0.26 nobody was watching.** After any pod-creating call that errors, is interrupted
  or is rejected: **list pods before doing anything else.**

**Cost discipline.** A render is **$0.0044** of GPU time; a boot is **$0.036** — **eight renders.**
**Fewer, larger sessions beat any cheaper card available to us** (`archive/GPU.md`). → this is **L6**'s
origin, and **P3** records that batching mitigates it rather than solving it.

**And a cost the per-render figure hides.** N30's real photographs run **21–28 MB each**, and uploading
them over the SSH tunnel dominated the session — 34 renders took **27 minutes** against the ~17 the GPU
time alone predicts. **Downscale inputs before a run, or budget for the upload.** (N42's phone set was
10 MB for ten, and did not hit this.)

**The session ceiling is 60 minutes / ~$0.75 on this branch**, raised from 45 / $0.30 on 2026-09-11
because the old pair was incoherent: at $0.72/hr the money ran out at 25 minutes, so 45 was never the
real limit — and N30 was halted mid-run at 14 of 34 renders by a number nobody had noticed was binding.
**`main` keeps the old pair.**

---

## 6 · Where things live

**Both render trees are bucketed by UTC date**, because forty sibling directories with nothing in the
name to say which session made them is not a record.

```
  prototype/renders/<UTC-date>/<run>/<sid>/0.png        PAID · gitignored · irreplaceable
  prototype/derived/<UTC-date>/<name>.html              FREE · rebuilt from renders/
  prototype/evaluations/<UTC-date>/<run>/               self-contained · gitignored
```

**`prototype/paths.py` is the seam.** `render_dir(name)` and `derived_dir()` **write** and always mean
today; `resolve_render(path)` **reads** and finds an undated run under whichever bucket holds it, newest
winning. **Two things under `derived/` are deliberately not dated** — `vlm_drafts/` and
`reference_sheets/` — because they are named references other scripts open, not artifacts of a day.

| what | where |
|---|---|
| the sheet tool | `sheet.py check \| build \| adopt \| find` |
| the reader harness | `vlm_reader.py --schema`; drafts in `derived/vlm_drafts/` |
| the router harness | `router.py --model <candidate>`; the mapper is `tagmap.py` |
| the attribute evaluator | `criteria_eval.py` (WD14 on renders) |
| identity | `face_likeness.py` · `sface.py` · **`same_person.py`** (F47's verification) |
| style axes | `style_axis.py` — **always read at the photograph's canvas** |
| contact sheets | `contact_sheet.py --sheet <name>` · **`phone_report.py`** (F47) |
| sheets | `prototype/sheets/{synthetic,real}/` — `real/` gitignored (D14) |
| **17 real photographs** | `prototype/inputs/real/` — gitignored; sheets and renders too |
| **10 phone photographs, 4 people** | `prototype/inputs/real/phone/` + **`groups.json`**, the ground-truth grouping |
| held-out ten | `prototype/inputs/synthetic/portfolio/` — never tuned on |
| ten pose studies | `prototype/inputs/synthetic/pose/` — **filenames are the pose labels** |
