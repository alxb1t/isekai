# Round 2 — the state of the work, for a new thread

**Written 2026-09-09 at the end of the session that produced F24–F36.** This is the file to read first
in a fresh thread. It is a summary with pointers, not a replacement: `FINDINGS.md` holds the evidence,
`CRITERIA.md` the design, `ILLUSTRIOUS.md` the base's own documentation, `archive/GPU.md` the
infrastructure.

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
| hires denoise | **0.50** for `A`, 0.35 tested for `D` | WAI publishes a *range* `0.35~0.5`; both are its recommendation |
| negative | `bad quality, worst quality, sketch, censor, nsfw, lens flare, light particles, dust` | WAI's own speck fix, in canonical form — **applied, never render-tested** |

Graph: `prototype/styles/fromnoise-v1.json`. Runners: `fromnoise.py`, `ladder_position.py`, `hires.py`,
`real_photo.py`. Every runner is one-change-per-arm by construction.

---

## 2 · Corrections to the summary as stated

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

## 4 · The laws this round established

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

**F30 — the contact sheet is the instrument, and it can lie.** Three broken axes this round were caught
by the operator reading a contact sheet; one sheet was itself showing a stale thumbnail in two columns.

---

## 5 · What is still open

**N14 — nothing has ever measured "is this the same person" in a way that survives stylization.** This
is the honest hole in the whole project.

> Round 1 instrumented only similarity-to-photograph, so the least-stylized render won by construction.
> Round 2 instruments only adherence-to-description, so **the flow that never reads the photograph wins
> by construction** — F29 scores `D` above `A` (0.77 vs 0.73) precisely because it is blind to the thing
> that separates them.

Both scoreboards were complete on their own terms and both missed the same axis. **The operator's eye is
still the only instrument for identity**, and it has overruled the assistant's reading twice (F24, F26).

Other open items:

- **The pose question.** Pose is the VLM's weakest field on *both* real and synthetic photos (0.57/0.58)
  — the only field indifferent to input type, which suggests a vocabulary limit rather than a reading
  limit. **Flow `A` has never been run with OpenPose but no pose tags.** One variable, ~$0.06.
- **`body shape` reads 0.00 on real photos** — the reader declines to guess a breast-size tag from a
  corseted torso. Since `medium breasts` is what fixed the age drift (F26), that caution costs us the
  sheet's highest-leverage tag. A briefing fix, not a model failure.
- **Style LoRA** — round 1's parked lever, still parked, and the only remaining one for `A`'s 19%
  posterisation gap. Prompt, dials and hires are all spent.
- **Tattoos** — F23: no general-purpose stylizer carries specific ink through a strong style change.
  Presence survives; design does not. Set aside deliberately.

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

## 6c · Where to start tomorrow

**Opened 2026-09-10 as N25–N29 in [`README.md`](README.md) § *Round 3 — the session of 2026-09-10*,**
with the reasoning behind each written there rather than here. In short: does `A` need pose tags (N25),
is there an open photograph reader (N26), what does "identity transferred" mean per flow (N27), does `A`
need hires (N28), and the new held-out portraits (N29). **N27 comes first** — it decides what the others
have to measure, and both previous rounds built the scoreboard second and measured the wrong thing.

Nothing is mid-flight; the account is empty and every artifact is on disk. Three candidates, cheapest
first — **none is blocked on anything**.

1. ~~**Confirm the negative-prompt change**~~ — **done, and it holds.** `n24_real_photo_final` *is* the run
   that carried `lens flare, light particles, dust`, and the operator read the output on 2026-09-10:
   the negative works. The assumption F32 raised is closed by that column, not by a new session.
2. **The pose ablation** (~$0.06, one variable). Flow `A` with OpenPose but **no pose tags**. Pose is the
   VLM's weakest field on both real and synthetic input (0.57/0.58), so if OpenPose already carries the
   geometry, dropping the tags removes the worst-read field rather than a good one. §5.
3. **Re-brief the reader on `body shape`** ($0). It scored **0.00** on real photos because it declines to
   guess a breast-size tag — and `medium breasts` is the tag F26 measured as fixing the age drift.

The last full run is `prototype/renders/2026-09-09/n24_real_photo_final/` with
`prototype/derived/2026-09-09/n24_real_photo_final_contact_sheet.html`. Its predecessors `n21_real_photo_v1` (pre-sheet-fix) and
`n21_real_photo_v2` (reviewed tables, pre-speck-fix) are kept deliberately, so the two edit rounds are
visible as columns.

**Spend on 2026-09-09 was roughly $1.00, of which about $0.50 was waste** — IP-less pods, a failed
sibling-repo session, and three orphans. The useful renders cost less than the mistakes. Worth carrying
as a number, not an impression.

---

## 7 · Where things live

**Both render trees are bucketed by UTC date** (2026-09-10), because forty sibling directories with
nothing in the name to say which session made them is not a record:

```
  prototype/renders/2026-09-08/n9_ablation/<sid>/0.png
  prototype/derived/2026-09-09/n24_real_photo_final_contact_sheet.html
```

`prototype/paths.py` is the seam. **`render_dir(name)` and `derived_dir()` are for writing** and always mean
today; **`resolve_render(path)` is for reading** and finds an undated `prototype/renders/<run>/…` under
whichever bucket holds it, newest bucket winning. That is why `contact_sheet.py`'s forty column templates
still name no date — and why bucketing again later would need no edit there.

**Three things under `derived/` are deliberately *not* dated**, because they are named references other
scripts read rather than artifacts of a day: `vlm_drafts/`, `reference_sheets/`, and the Fotor
`*.canvas.png` bars that `style_axis.py` and archived `thesis.py` / `retention.py` open by name.

| what | where |
|---|---|
| the design | `CRITERIA.md` — the sheet, the seven scored criteria, both bars |
| the evidence | `FINDINGS.md` F24–F36, newest at the bottom |
| the base's own docs | `ILLUSTRIOUS.md` — caption schema, quality ladder, skin tags, WAI §6b |
| the GPU question | `archive/GPU.md` — settled: keep the card |
| sheets | `prototype/sheets/{synthetic,real}/` — `real/` gitignored as a directory (D14) |
| round 2's inputs, tuned on | `inputs/synthetic/` (ten) · `inputs/baseline/` (six) |
| round 3's inputs, held out | `prototype/inputs/` — **[its README](inputs/README.md) is the sourcing criteria**; ten new portraits, two real photographs |
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
giving up the external anchor, in [`README.md`](README.md) § *The style bar, restated*.
