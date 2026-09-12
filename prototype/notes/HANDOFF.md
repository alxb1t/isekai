# The state of the work, for a new thread

**Rounds 1–4 are complete.**

**Updated 2026-09-12 at the close of round 4 (F42–F46).** This is the file to read first in a fresh
thread. It is a summary with pointers, not a replacement: **[`ARCHITECTURE.md`](ARCHITECTURE.md) is the
shape of the whole pipeline** and is the other thing to read first; `FINDINGS.md` holds the evidence,
`ROUTER.md` how prose becomes a sheet, `IDENTITY.md` the identity method, `CRITERIA.md` the sheet's
design, `ILLUSTRIOUS.md` the base's own documentation, `READER.md` and `JOYCAPTION.md` round 4's survey
and plan, `archive/GPU.md` the infrastructure.

> **§6c is stale** — it briefs round 4, which is now closed. **What to do next is
> `../README.md` § *Start here tomorrow*** — the ranked open list, the plan, and today's three traps.
> The architectural version of the same ranking is [`ARCHITECTURE.md`](ARCHITECTURE.md) §6.

### What round 4 settled, in five lines

- **JoyCaption is in the stack as the *describer*, not the reader** — 0.518 against the agent session's
  0.795 and a 0.60 floor, kept because the *seeing* becomes reproducible from a digest · **F42**
- **An LLM + deterministic mapper is stage two.** Qwen3-8B (Apache-2.0, 5.2 GB) + `tagmap.py` reaches
  **0.482**, and *rendered* it ties the hand-routed sheet — 0.580 to 0.568 · **`ROUTER.md`**
- **Prose is dead as a render prompt.** Illustrious reads it and renders it in the wrong register ·
  **F45**
- **An absence clause is a presence instruction.** The router is where negation dies · **F44**
- **The operator's review step is worth 0.35** — 0.568 unreviewed against 0.917 reviewed. It is the one
  unbuilt stage · **F44/`ARCHITECTURE.md` §4**
- **Identity survives an encoder we did not train against.** SFace, independent: **9/17 at chance 5.9%,
  p ≈ 0.0000**, against `glintr100`'s 14/17 on the same crops. `A` is no longer self-graded, and the
  entanglement inflated the **margin 16.3x** while inflating hits only 1.6x · **F46**

---

## 1 · What exists now

**Two flows, both wanted, both kept.**

```
  A   photo ─▶ InstantID (face) ─┐
              OpenPose (skeleton)├─▶ Illustrious ─▶ hires pass ─▶ anime image
              criteria sheet ────┘

  D   criteria sheet ────────────▶ Illustrious ─▶ hires pass ─▶ anime image
      (the photograph is never read at render time)
```

`A` is the product: the operator judged it best and said face identity and pose are preserved. `D` is the
deliberate alternative: *"less identity preserved but the anime style is the maximum."* `C` (InstantID
only, no OpenPose) was tested and rejected against `A`.

**The settled configuration**, arrived at by measurement, not preference:

| | value | where it came from |
|---|---|---|
| base | WAI-illustrious-SDXL v17.0 | inherited |
| latent | `EmptyLatentImage`, `denoise 1.0` | **F24** — taking the photo out of the latent is what removed the blur |
| `ip_weight` | **0.9** | **F25** — a ceiling, not a default; 1.2 streaks, 1.5 collapses |
| `cn_strength` | **0.8** | **F25** — the free lever: holds linework, best posterisation of any dial arm |
| `cfg` | **5** | **F26** — 7 measured worse; inside WAI's published 5–7 |
| sampler / steps | `euler_ancestral` / 28 | already WAI's own recommendation — **not** an untested lever |
| hires | R-ESRGAN 4x+ Anime6B → 1.5x → 20 steps | **F35** |
| hires denoise | **0.35** for `A` and for `D` | **F39** — `A` changed from 0.50 on 2026-09-10. 0.50 was set by F35 on *style alone*; across all four axes 0.35 wins linework, identity and pose, and loses only posterisation by 0.014 |
| negative | `bad quality, worst quality, sketch, censor, nsfw, lens flare, light particles, dust` | WAI's own speck fix. **Render-tested and confirmed** — `n24_real_photo_final` is the run that carried it, read 2026-09-10 |
| pose tags | **kept in the prompt** alongside OpenPose | **F38** — they complement rather than compete. Without them `arms_up` drops an arm, a shoulder off by 124° |

Graph: `prototype/styles/fromnoise-v1.json`. Runners: `fromnoise.py`, `ladder_position.py`, `hires.py`,
`real_photo.py`. Every runner is one-change-per-arm by construction.

---

## 2 · Corrections worth getting exactly right

Four things worth getting exactly right, because a new thread will inherit them.

**"hires greatly improves the quality" — true for `D`, mixed for `A`.** Measured (F35):

| | posterisation | linework |
|---|---:|---:|
| `A` no hires | 0.363 | 0.0145 |
| `A` + hires 0.50 | 0.373 (+0.010) | 0.0181 (**+25%**) |
| `D` no hires | 0.503 | 0.0255 |
| `D` + hires 0.35 | 0.528 (**+0.025**) | 0.0376 (**+47%**) |
| *the third-party stylizer, round 1's reference* | *0.460* | *0.0404* |

`A`'s gain is mostly **linework**, not flatness. Hires is the first change in two rounds to move both
axes at once. **The last row is history, not a target** — see §7; as of 2026-09-10 each flow is measured
against its own previous number, not against anything outside the project.

**"validate booru tags" — not by the WD14 model.** Two different things ship in one download:

- **`selected_tags.csv`** — 8,106 real Danbooru tags with post counts. This is what validates a sheet
  (`sheet.py check`). It answers *is this a real tag* and *is it common enough to have been learnt*.
- **the WD14 model** — reads a **render** and emits tags. This is the evaluator (`criteria_eval.py`),
  at the other end of the pipeline. **It cannot read photographs**: F29 measured 0.47 on photos against
  0.73 on renders, with `pose` at 0.08 and `marks` at 0.00.

Keeping those distinct matters or the architecture diagram goes wrong.

**"the prompt structure improved the quality" — specifically, WAI's string, at the front.** F34: moving
`masterpiece, best quality, amazing quality` to the front is +0.007, adding `newest` inside it a further
+0.006. **+0.013 total**, the first prompt *addition* to help since the definitional fixes. Every sheet
now leads with `masterpiece, best quality, amazing quality, newest, 1girl, solo, …`.

**One thing missing from the summary, and it is the most important open item.** See §5.

---

## 3 · The architecture, corrected

```
  photo
    │
    ▼
  VLM reads it ──────────────── an agent session; no API dependency
    │                           `vlm_reader.py --schema` prints the briefing
    ▼
  draft.json  (15 fields, booru tags)
    │
    ▼
  sheet.py adopt ───────────── writes the draft into the sheet's TABLE only;
    │                          prose, source notes and the verdict block survive
    ▼
  sheet.py check ──────────── selected_tags.csv: UNKNOWN and rare warnings
    │
    ▼
  ★ OPERATOR REVIEWS AND EDITS THE TABLE ★     ← the step the whole design is for
    │
    ▼
  sheet.py build ──────────── rebuilds the prompt from the table
    │
    ▼
  render ──▶ anime image ──▶ criteria_eval.py (WD14 reads the render)
```

**Measured, this session:** the VLM reader scored **0.78** on ten synthetic photographs and **0.80** on
three real ones, against a floor of 0.60 stated before the run. **Four invented tags out of ~400** — a
~1% rate, all caught by the vocabulary check before reaching a prompt.

---

## 4 · The laws, rounds 1–3

Ranked by how much they should change a new thread's behaviour.

**F28 — canonical tags work, invented ones do nothing.** Across two rounds, *no exception*: every tag
that worked is a real Danbooru tag, every tag that failed is not. `hand on own knee` (9,589 posts)
worked; `centre part`, `voluminous`, `fair skin`, `young woman` did nothing. **This is now enforced by
`sheet.py`, not remembered** — because it was written down and then not applied three separate times.

**F32/F34 — corrections win, improvements lose.** Every change that *fixed something wrong* helped;
almost every change that *pursued an improvement from documentation* hurt. The long Illustrious
negative (−0.017), the `rating` slot (−0.012) and underscores (−0.013) all lost. Skin-tag fixes and
deleting `worst detail` won. **Prompt folklore is cheap to generate and expensive to trust.**

**F27 — the legs compete with the tags.** Dropping InstantID moves posterisation 0.358 → 0.518.
Dropping OpenPose instead moves it to 0.371. One leg was most of the style deficit;
the other is nearly free.

**F36 — most apparent model failures are description failures.** Three transcription defects on the
first real photographs produced three visible render failures; fixing the *sheet* fixed all three on the
first attempt, with no dial touched.

**F35 — read every image at one canvas.** Both style axes are resolution-sensitive. Read natively, hires
looked like a linework *loss*; read at the photograph's canvas it is a 43–47% *gain*. **The sign
flipped.** Use `load_canvas_pixels(path, canvas_for(photo))`, never `Image.open` at native size.

**F38 — ask "which one", not "how similar".** Both earlier scoreboards failed the same way. N-way
identification is stylization-invariant because every candidate is equally stylized. And report **two**
pose measures: PCK is *placement*, joint angles are *configuration*, and flow `D` once scored the best
angle error of any arm **at a PCK of 0.000** — a plausible body in entirely the wrong place.

**F39 — a settled value is settled against the axes that existed when it was set.** `A`'s hires denoise
sat at 0.50 for a day after two new instruments contradicted it, because nobody re-read it. It is 0.35.

**F41 — score what already exists before rendering more.** Two thirds of N28 was answered across three
earlier sessions and had never been put in one table; doing so shrank its pod session from 30 renders to
10. The same habit is why N26 cost nothing.

**F30 — the contact sheet is the instrument, and it can lie.** Three broken axes this round were caught
by the operator reading a contact sheet; one sheet was itself showing a stale thumbnail in two columns.

---

## 5 · What was the hole, and how it was closed

**N14 was open from round 1 to round 3 and it is now answered.** Kept here rather than deleted, because
*how* it was wrong twice is the most transferable thing this project produced.

> Round 1 instrumented only similarity-to-photograph, so the **least-stylized render won by
> construction**. Round 2 instrumented only adherence-to-description, so the flow that **never reads the
> photograph won by construction** — F29 scored `D` above `A`, 0.77 to 0.73, precisely because it was
> blind to the thing that separates them.
>
> **Both scoreboards were complete on their own terms and both missed the same axis.**

**The fix was not a better metric but a different question.** Not *how similar is this render to its
photograph* — an absolute score whose optimum is a render that did not stylize — but **which of the N
photographs did this render come from**. Every candidate in that comparison is equally stylized, so a
metric that merely punishes stylization pushes all N numbers down and leaves the ranking untouched.
**[`IDENTITY.md`](IDENTITY.md)** is the method, written to be exported.

| | subjects | chance | flow `A` | margin | |
|---|---:|---:|---:|---:|---|
| tuned-on six | 6 | 16.7% | 5/6 | +0.0485 | **F37** |
| held-out ten | 10 | 10.0% | 8/10 | +0.1170 | **F40** |
| **real seventeen** | **17** | **5.9%** | **14/17** | **+0.1172** | **F41** |

**The operator's eye agreed on all three**, and on F38 the instrument *corrected* the eye on one subject
— which counted only because the expectation had been recorded before the run.

**What is genuinely still open** is one item, and it is in §6c: an **independent recognizer**. Everything
else in rounds 1–3 is closed or deliberately dropped, and `../README.md` has the per-task record.

**Set aside deliberately, and not carried forward:**

- **The style LoRA** — round 1's `N20`, dropped 2026-09-10. It existed to close a posterisation deficit
  measured against a third-party reference this project retired; against the bar that replaced it there
  is no deficit. F19 and F22 stay as findings.
- **Tattoos** — F23: no general-purpose stylizer carries specific ink through a strong style change.
  Presence survives; design does not. A *finding*, not an open task.

---

## 6 · Infrastructure, and one unresolved blocker

**RunPod returns pods that reach `RUNNING` with no public IP** — `runtime: null`, `ssh.direct: null`,
proxy only, billing normally. Nine of fourteen pods over two days, across two datacenters and two GPU
pools. No incident posted; a published case study reports the same shape. Details in F31.

- **`infra/up.sh` now bounds its wait and tears the pod down itself.** The poll was unbounded — the one
  thing in the repo that could bill indefinitely while looking like it was working.
- **`RUNPOD_GPU_TYPE` accepts a preference list.** The pinned Blackwell card exists in **only two
  datacenters**, which was an unrecorded single point of failure.
- **The HTTP-proxy fallback does not work for our client.** Cloudflare 1010-blocks stdlib `urllib` by
  user-agent; `curl` passes. F33 claimed it worked on the strength of a `curl` probe and was **never
  render-tested**. Amended. The fix is a `User-Agent` header, untried.
- **`GET /object_info/<NodeName>` returns 200 for nodes that do not exist.** Fetch the full
  `/object_info` and look for the key.

Cost discipline: a render is **$0.0044** of GPU time; a session's boot is **$0.036** — eight times as
much. **Fewer, larger sessions is worth more than any cheaper card available to us** (`archive/GPU.md`).

**The session ceiling is 60 minutes / ~$0.75 on this branch**, raised from 45 / $0.30 on 2026-09-11.
The old pair was incoherent — at $0.72/hr the money ran out at 25 minutes, so 45 was never the real
limit, and N30 was halted mid-run at 14 of 34 renders by a number nobody had noticed was binding. **Now
time binds**: a full hour costs $0.72. `CLAUDE.md` carries the rule; `main` keeps the old pair.

**And a cost the per-render figure hides: large source photographs.** N30's real photographs run 21–28 MB
each, and uploading them over the SSH tunnel dominated the session — 34 renders took 27 minutes against
the ~17 the GPU time alone predicts. **Downscale inputs before a run, or budget for the upload.**

---

## 6b · Five traps that cost real money or real renders this session

**`sheet.py build` regenerates the prompt from the table — and the prompt is the tempting thing to
edit.** The operator naturally edited the prompt block; `build` would have silently overwritten it.
**Edit the table, never both.** The fix, untried: make `build` refuse when table and prompt have
diverged, or make the prompt the source of truth.

**A rejected or errored pod-creating call may still have created the pod.** Twice a rejected `up.sh`
had already reached the API; once an MCP `create-pod` returned `422 Unprocessable Entity` and created
one anyway. Three orphaned pods, roughly **$0.26** of billing nobody was watching. **After any
pod-creating call that errors, is interrupted, or is rejected: list pods before doing anything else.**

**Tag frequency predicts strength of effect.** `narrow waist` (9,411 posts) rendered an exaggerated
waist, because the images Danbooru tags that way are ones where the waist *is* the feature. `medium
breasts` (770,389) is near-default and renders ordinary. **Do not use a rare tag to describe something
ordinary** — the same lesson as `pale skin`, which means *bleached*.

**When the tag you want does not exist, compose two that do.** There is no `white corset` (only `black`
and `brown`), so `white camisole, corset` carries the colour and the structure separately. Likewise a
see-through dress over a bikini is `turtleneck, see-through, bikini under clothes` — and
`bikini under clothes` (15,818) is a real tag that says *layering*, which listing two garments does not.

**Caveat on the vocabulary check itself:** `selected_tags.csv` is the set WD14 *predicts*, a subset of
Danbooru above some post threshold. `sheet.py` prints `not a Danbooru tag`, which **overclaims** — the
honest statement is *not in WD14's prediction set*, and therefore probably too rare for Illustrious to
have learnt. Worth softening the message.

---

## 6c · Round 4's brief — STALE, kept as the record of what was planned

> **Round 4 is closed.** This section briefed it and is left unedited because the plan it states is what
> the result should be read against. **For what to do next, see `../README.md` § *Carried out of round 4*
> or [`ARCHITECTURE.md`](ARCHITECTURE.md) §6.**

**Nothing is mid-flight. The RunPod account is empty, the working tree is clean, and every artifact is
on disk.** Rounds 1–3 are closed; `../README.md` carries every question and what answered it.

### The one job

**Trial JoyCaption as the photograph reader, and it is planned already.**
**[`JOYCAPTION.md`](JOYCAPTION.md)** is the plan — artifacts and their digests, hosting, the two phases,
the traps, and **the bar written before the run**. **[`READER.md`](READER.md)** is the survey behind the
choice. Read both before touching anything; between them there is nothing left to decide except what the
numbers say.

**Why it matters, in one line:** the reader that turns a photograph into a criteria sheet is currently
*an agent session*. It scores 0.78 and it is **not reproducible by anyone without the transcript** — a
closed component at step one of a repository whose thesis is open models end to end.

**The plan in brief**, and the detail is in `JOYCAPTION.md`:

```
  ① pin      Q4_K 4.92 GB + mmproj 0.88 GB, digests recorded FIRST
             concedo/llama-joycaption-beta-one-hf-llava-mmproj-gguf
             ⚠ the two most-cited quantisations ship NO mmproj and are blind
  ② host     LM Studio, already installed — no new Python dependency
  ③ client   prototype/joycaption.py, stdlib urllib against localhost
  ④ run      BOTH phases over the same 13 photographs in one sitting:
               phase 0  JoyCaption's own Danbooru tag mode
               phase 1  our 16-field schema, verbatim from vlm_reader.py --schema
  ⑤ score    vlm_reader.py, unchanged
  ⑥ decide   ≥0.78 replaces · 0.60–0.78 becomes a first draft · <0.60 fails
```

**One real data point exists.** The operator ran `standing_turn.png` through the public demo on
2026-09-11: **0.688** against that subject's reviewed sheet, with **all six clothes tags** correct and
every miss in a field JoyCaption had no reason to look at. n=1, and its *shape* is why phase 1 exists —
the question is whether it is a tagger we route or a reader we brief.

### The other job, smaller and unscheduled

**N27's independent recognizer.** `A`'s identity numbers are an **upper bound** because `glintr100` is
the encoder InstantID optimises against. `D`'s are clean, which is the only reason the gap reads. Both
locally pinned face encoders are entangled with this generator — the other one *more* so. Needs a model
from a different architecture and training set fetched, licence-checked and digest-pinned. **No GPU.**

### What is known and should not be re-derived

- **Flow `A` is validated end to end** — see §1's configuration table. Every dial measured, then
  confirmed on held-out faces (F40) and on **17 photographs of real people, 14/17 at chance 5.9%** (F41).
- **Full-body framing costs identity**, reproduced in **three** independent sets: `00059` in round 2,
  `15_01`/`16_01` in N29, `full_height_4`/`male_full_height` in N30. A property, not noise.
- **Nothing tests a phone snapshot.** Every photograph used so far is generated or professionally shot.
  The operator intends to gather a phone-camera set; it does not exist yet.
- **The session ceiling is 60 minutes / ~$0.75** on this branch (`CLAUDE.md`), raised 2026-09-11.
- **Large inputs dominate a session.** N30's photographs are 21–28 MB each and the uploads, not the GPU,
  made 34 renders take 27 minutes. **Downscale before a run, or budget for it.**

### The last runs on disk

| run | what | contact sheet |
|---|---|---|
| `renders/2026-09-11/n30_real/` | 17 real subjects, both flows — **the strongest identity result** | `derived/2026-09-11/n30_real_contact_sheet.html` |
| `renders/2026-09-10/n29_portfolio/` | the held-out ten | `derived/2026-09-10/n29_portfolio_contact_sheet.html` |
| `renders/2026-09-10/n25_pose/` | the pose ablation, four arms | `derived/2026-09-10/n25_pose_contact_sheet.html` |

Identity runs are self-contained under `prototype/evaluations/<date>/`, each with its own `report.md`,
`manifest.json` of digests, and copies of every image scored.

---

## 7 · Where things live

**Both render trees are bucketed by UTC date**, because forty sibling directories with
nothing in the name to say which session made them is not a record:

```
  prototype/renders/2026-09-08/n9_ablation/<sid>/0.png
  prototype/derived/2026-09-11/n30_real_contact_sheet.html
```

`prototype/paths.py` is the seam. **`render_dir(name)` and `derived_dir()` are for writing** and always mean
today; **`resolve_render(path)` is for reading** and finds an undated `prototype/renders/<run>/…` under
whichever bucket holds it, newest bucket winning. That is why `contact_sheet.py`'s forty column templates
still name no date — and why bucketing again later would need no edit there.

**Two things under `derived/` are deliberately *not* dated**, because they are named references other
scripts read rather than artifacts of a day: **`vlm_drafts/`** (which mirrors the sheet and input trees —
`synthetic/`, `synthetic/pose/`, `synthetic/portfolio/`, `real/`) and `reference_sheets/`.

| what | where |
|---|---|
| the design | `CRITERIA.md` — the sheet, the seven scored criteria, both bars |
| **how identity is measured** | **`IDENTITY.md`** — face likeness (§1–7) and pose geometry (§10), their limits, and how to run them. Written to be exported |
| identity runs | `prototype/evaluations/<UTC-date>/<run>/` — self-contained, gitignored |
| the evidence | `FINDINGS.md` F24–F41, newest at the bottom |
| who reads the photograph | `READER.md` — the open candidates, their licences, and the numbers to beat |
| the base's own docs | `ILLUSTRIOUS.md` — caption schema, quality ladder, skin tags, WAI §6b |
| the GPU question | `archive/GPU.md` — settled: keep the card |
| sheets | `prototype/sheets/{synthetic,real}/` — `real/` gitignored as a directory (D14) |
| round 2's inputs, tuned on | `inputs/synthetic/` (ten) · `inputs/baseline/` (six) |
| round 3's inputs | `prototype/inputs/` — **[its README](../inputs/README.md) is the sourcing criteria** |
| · held-out ten | `prototype/inputs/synthetic/portfolio/` — never tuned on (N29) |
| · ten pose studies | `prototype/inputs/synthetic/pose/` — **filenames are the pose labels** (N25) |
| · **17 real photographs** | `prototype/inputs/real/` — gitignored, D14. Sheets and renders too |
| **the next round** | **`JOYCAPTION.md`** — the trial plan, bar stated before the run |
| the sheet tool | `sheet.py check \| build \| adopt \| find` — `find` searches the vocabulary |
| the reader harness | `vlm_reader.py --schema`; drafts in `prototype/derived/vlm_drafts/` |
| the evaluator | `criteria_eval.py` (WD14 on renders) |
| style axes | `style_axis.py`; **always read at the photograph's canvas** |
| contact sheets | `contact_sheet.py --sheet <name>` → `prototype/derived/<UTC-date>/` |
| renders | `prototype/renders/<UTC-date>/<run>/` — **PAID**, gitignored, irreplaceable |
| derived artifacts | `prototype/derived/<UTC-date>/` — **FREE**, rebuilt from `renders/` |
| a sibling repo's blocker | `archive/SYNTHETIC_PORTRAITS_FIX.md` — **fixed**; the portraits generated |

**Determinism floors**, needed to read any number: linework **±0.0003**, posterisation **±0.0020**,
mean pixel |Δ| **≈2/255** across pods. Anything smaller is GPU nondeterminism.

**The bars.** Identity is unchanged: **6 of 7 criteria**, with pose and hair silhouette mandatory.
**Style was restated on 2026-09-10** — the third-party reference is retired and the bar is now **our own
last number**: `A` + hires at posterisation **0.373** / linework **0.0181**, `D` + hires at **0.528** /
**0.0376**, and a drop beyond the determinism floor is a regression. Full reasoning, and the cost of
giving up the external anchor, in [`README.md`](../README.md) § *The style bar, restated*.
