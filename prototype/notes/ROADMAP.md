# ROADMAP — the versions, in order

**Round 5, N48. Written 2026-09-13.** How the prototype becomes the product, cut into versions that each
end on a green gate and a tag. **Every carried item from four rounds is dispositioned here** — a version,
a task inside one, or dropped with its reason. An item that is none of those is an item that gets lost.

> **This is a draft for the grilling session, not a commitment.** It is what
> [`OPEN.md`](OPEN.md), [`PRODUCT.md`](PRODUCT.md) and [`MIGRATION.md`](MIGRATION.md) imply, arranged.
> Cutting a change under `openspec/changes/<id>/` is what makes any line of it real, per
> [`../../CLAUDE.md`](../../CLAUDE.md) § *How a change is cut here*.

---

## 1 · The shape: a walking skeleton, then depth

**Three sequencings were considered; the operator chose the third, 2026-09-13.**

```
  A  spine first       run dir + generation + delete old
                       → a window where captions are written by hand

  B  front first       caption + sheet layers; the old flow still renders
                       → no window, but the rejected architecture lives a version longer

  C  walking skeleton  the thinnest end-to-end path, flow A only        ← CHOSEN
                       → every seam crossed once before any is deepened
```

**Why C.** With five facades, the risk that matters is **a seam that was never crossed**. C proves all of
them against each other while each is still thin; A and B both defer that, and a facade nothing has been
passed through is a facade by assertion — `../../CLAUDE.md`'s own rule.

---

## 2 · The versions

| | delivers | makes possible | leaves broken |
|---|---|---|---|
| **v0.13** | **walking skeleton** — run directory, orchestrator, caption→sheet→assemble→render, **flow `A` only**, **Claude at ① and ②**, old flow deleted, living spec 6→9 capabilities | every seam crossed once | no `D`, no UI, no benchmark, **not open end to end** |
| **v0.14** | **the open models** — JoyCaption at ①, Qwen3-8B + the vocabulary module at ② | **the thesis is restored**; a clone runs with no API key | — |
| **v0.15** | **the flow registry** — `D` lands, `session()`, batch, seed-only variation (L4) | adding a flow is a directory | — |
| **v0.16** | **the evaluation machinery** — cohort, N-way identification, verification, per-image axes | **L3's entry gate becomes executable** | the results are not published yet |
| **v0.17** | **the review UI** (N41) — **the 0.35** | sheets diverge per flow under human editing | — |
| **v0.18** | **hardening** — Qwen pinned, per-implementation manifests (L20/L21), per-field enums | — | — |
| **v0.19** | **portfolio preparation** — the README, the showcase table (L24), thumbnails in-repo, the release-asset bundle, attribution | **the repository stops being work in progress** | — |

**v0.13 ships the measured-best configuration, and that is the whole argument for it.** Claude scores
**0.795** as a reader against JoyCaption's 0.518, and **0.575** as a router against Qwen's 0.482. The
skeleton is the version where the *architecture* is the risk, so it is the wrong version to also be
carrying the weakest components.

### The repository is work in progress until v0.19, and says so once

**The operator's decision, 2026-09-13: no per-version README polish.** A banner is set at v0.13 and
removed at v0.19, and that is the whole of the documentation work in between.

**It dissolves two concerns rather than answering them.** v0.13 is **not open end to end** — round 4
existed *because* the reader was closed *"at step one of a repository whose thesis is open models end to
end"* — and a clone of v0.13 **cannot run without an Anthropic API key**. Both matter only to someone
arriving expecting a finished thing. **A repository that declares itself unfinished is not lying about
either**, and v0.14 restores the first while v0.19 is where any claim is made at all.

**The key joins `RUNPOD_API_KEY` in the gitignored `.env`; `.env.example` declares shape only.**

**And one thing that is already solved, worth stating so it is not rediscovered.** The **0.795 was an
agent session with tools**, not a single API call — today's readers used `sheet.py find` to verify tags
before committing them. **Layer ① does not need that**, because it returns prose; **layer ② does not
need it either**, because under **L23** the vocabulary is a module the layer imports, so the model
proposes and `tagmap` canonicalises deterministically. **No tool loop has to be reproduced.** And both
layers are stdlib against an HTTPS endpoint, so **L1 is satisfied without a wheel**.

### The awkwardness, named rather than buried

**The review step is the single largest measured value in the project and it lands fifth.** Until v0.17
the pipeline ships **0.568** sheets rather than **0.917** (F44).

**It is defensible and it is not free.** F45: a bad sheet degrades *attributes*, not *likeness* — so
every render before v0.17 is still a usable picture of the right person, which is why the order holds.
**But four versions of output will be worse than this project knows how to make.**

**Deferring the showcase to v0.19 is what makes that safe.** v0.16 measures the unreviewed path and
v0.17 adds the review step — so **the numbers that reach the public README are the reviewed ones**,
taken after both exist, rather than a 0.568 result needing a footnote nobody reads.

### What v0.19 actually contains, since "documentation" understates it

- **The showcase table under L24** — every subject in the cohort, **including every failure**. F47 is
  the worked example of why: flow `A` was 8/10 at photograph level and **10/10 at person level**, and a
  table of only the eight hits would have hidden the better result.
- **Thumbnails in-repo** so the table renders on GitHub without a fetch; **the full-resolution bundle as
  a release asset** attached to the `v0.19.0` tag (`PRODUCT.md` §6).
- **Attribution.** A public repository with Llama-3.1-derived weights in its stack carries
  **"Built with Llama"** — `OPEN.md` Q7's one concrete action, and this is where it lands.
- **The licence posture stated plainly** — Apache-2.0, public, **distributes no model weights** (L19),
  with the non-commercial artifacts named rather than buried.
- **Removing the work-in-progress banner**, which is the act that makes every claim above load-bearing.

---

## 3 · Every carried item, dispositioned

| item | disposition |
|---|---|
| **a phone-camera set** | **DONE 2026-09-13 — F47.** 8/10 photograph-level, **10/10 person-level** |
| **N27b independent recognizer** | **DONE 2026-09-12 — F46.** SFace, `9/17 … 14/17` |
| **N41 the review UI** | **v0.17** |
| **flow `D`** | **v0.15** |
| **P6 · a synthetic 5+5 cohort** | **v0.16** — the machinery needs a cohort to run against, and v0.19 needs a *publishable* one; privacy (L19) makes it synthetic either way |
| **photograph→photograph sibling control** | **v0.16**, ~free. F47's owed control: it separates the encoder's own clustering from the pipeline's |
| **B1 pod readiness gates** | **v0.15**, with `session()`. Three of five exist on this branch; `main` has none. Includes a real defect — every SSH uses `StrictHostKeyChecking=no` |
| **Qwen3-8B unpinned** *(live defect)* | **v0.18.** Not jumped ahead, on the operator's decision: it cannot bite before v0.14 introduces Qwen, and v0.14 is where it would be noticed |
| **N40 per-field enums** | **v0.18**, a task inside the `sheet` capability. Curation, not capability: `gaze` 0.00 vs 0.60, `pose` 0.37 vs 0.80 |
| **a better VLM (`Qwen3-VL`)** | **a task, not a version.** Under **L3** a swap is a replacement, and P8's watcher is what would surface the need |
| **P1 serverless · P2 local ComfyUI** | **stay parked.** Internals of the generation layer under L5; neither changes a contract |
| **P3 boot/teardown cost** | **stays parked.** L6's batching mitigates; the 2–4 minute interactive latency is the part money does not fix |
| **P4 spend awareness** | **stays parked.** The ceiling is in the operator's head by his decision |
| **P5 the comparison feature** | **stays parked.** The *property* is free (L12 + provenance) and ships with v0.16; the *view* is a second product |
| **the "Built with Llama" attribution** | **v0.19** — Q7's one concrete action |
| **P7 commercial licence audit** | **stays parked.** Triggered by a business model, not a date |
| **P8 the model-update watcher** | **stays parked**, but **the manifest schema accommodates it from v0.13** — adding the field later would re-derive every byte-identical manifest |
| **SFace alignment** | **stays parked.** Refines a number, changes no verdict — it was deliberately last on round 4's list too |
| `face_likeness` on N38's twenty | **DROPPED.** It would have turned F45 from an eye into a number; F47 measured the same thing on better data |
| **EXIF orientation** | **MOOT — the claim was withdrawn.** `isekai/workflow.py:315` already transposes, for both codecs |
| the style LoRA · tattoos · prose-as-prompt · the enum grammar | **stay dropped**, each with its recorded reason |

---

## 4 · What this roadmap does not decide

- **Whether v0.13 is one change or several.** It carries the run directory, the orchestrator, three
  layers, a spec restructure and a deletion. **That may be more than one change can hold**, and
  `../../CLAUDE.md` binds one version to one branch, not one change — splitting it is a legitimate
  answer and the grilling session is where it should be attacked.
- **The change ids.** `(major × 100) + minor`: v0.13 → `0013`, v0.14 → `0014`, and so on.
- **Anything past v0.18.** The operator's ideas note carries seven more generation flows — portal,
  photoreal fantasy, cartoon, pixel-art, grade, cosplay, region passes. **Each enters through L3's gate:
  a prototype round, then the evaluation bar, then a version.** That is the machine this roadmap exists
  to build.
