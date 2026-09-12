# The architecture — photograph in, anime image out

**Settled 2026-09-12, after four rounds.** Every box below is measured; the numbers are cited to the
finding that produced them. This note is the shape of the thing. `HANDOFF.md` holds the dial values,
`ROUTER.md` the stage-2 detail, `IDENTITY.md` how the output is judged.

---

## 1 · Abstract — four stages and one human

```
   photograph
       │
   ┌───▼─────────────────────────────────────────────────────────┐
   │ ① VLM — SEE                                                │
   │    reads the photograph into English prose                  │
   │    must be allowed to state absence, or it confabulates     │
   └───┬─────────────────────────────────────────────────────────┘
       │ prose
   ┌───▼─────────────────────────────────────────────────────────┐
   │ ② LLM + MAPPER — SORT                                      │
   │    prose → 16 fields of canonical booru tags                │
   │    must STRIP absence, or the generator draws it            │
   └───┬─────────────────────────────────────────────────────────┘
       │ criteria sheet
   ┌───▼─────────────────────────────────────────────────────────┐
   │ ③ HUMAN — REVIEW              ★ worth 0.35 ★               │
   │    add, delete, correct tags. The only stage that can       │
   │    recover what stage ① never saw                           │
   └───┬─────────────────────────────────────────────────────────┘
       │ reviewed sheet
   ┌───▼─────────────────────────────────────────────────────────┐
   │ ④ DIFFUSION — DRAW                                         │
   │    tags → prompt · face + skeleton from the photograph      │
   └───┬─────────────────────────────────────────────────────────┘
       ▼
   anime image
```

**Stages ① and ② want opposite things about absence, and that is the load-bearing insight.** A reader
told *"never leave a field blank"* invented nineteen identity marks on seven of ten subjects (F43). A
reader licensed to write *"no tattoos are visible"* stopped confabulating — and that sentence, passed
through to the prompt, produced a render with tattoos, because CLIP has no negation (F44). **So the seam
between them is not plumbing. It is the component that converts a licensed absence into an empty field.**

---

## 2 · Inside stage ④ — identity is carried by the legs, not the prompt

```
   photograph ──┬──▶ InsightFace ──▶ InstantID ──┐  face embedding + keypoints
                │                                │
                ├──▶ DWPose ──────▶ OpenPose ────┤  skeleton
                │                                │
                └──▶ (never enters the latent) ──┤  F24: taking the photo out
                                                 │       of the latent removed
   reviewed sheet ──▶ prompt ─────────────────────┤       the blur
                                                 │
                              EmptyLatentImage ───┤  denoise 1.0
                                                 ▼
                                    WAI-illustrious-SDXL v17.0
                                      euler_ancestral · 28 · cfg 5 · clip skip −2
                                                 │
                                                 ▼
                                    hires: R-ESRGAN Anime6B → 1.5x → 20 steps
                                           denoise 0.35
                                                 │
                                                 ▼
                                           anime image
```

**F45: the prompt's job is style and register; the legs' job is identity.** Across twenty renders in four
prompt registers — including prose that was out of distribution and two prompts poisoned with
hallucinated tattoos — InstantID and OpenPose held on every case. **A bad sheet degrades *attributes*,
not *likeness***, which is why a 0.568 sheet still renders the right person.

**Prose is not a prompt for this base.** It reads it — *"the image has a gray border"* produced a painted
grey frame — and renders it in the wrong register: 0.675 and 0.510 against the reviewed sheet's 0.917,
and the operator's reading was that neither is usable. Illustrious was captioned with tag lists in a
fixed schema and has never seen an English sentence. **Do not retry with better prose; the register is
the problem, not the wording.**

---

## 3 · The open stack — the default

```
   photograph
       │
   ① JoyCaption Beta One          Q4_K 4.92 GB + mmproj 0.88 GB · Ollama
       │                          Apache-2.0 code over Llama-3.1 weights ⚠
       │                          digests: styles/joycaption_models.json
       │ descriptive prose, ~110 words
       │
   ② Qwen3-8B + tagmap            5.2 GB · Apache-2.0 · think: false
       │                          two worked examples · unconstrained generation
       │                          then exact → suffix → curated → containment
       │ 16-field sheet · 0 invalid tags · 0 absence leaks
       │
   ③ operator                     add / delete with booru autocomplete   ← N41, unbuilt
       │
   ④ WAI-illustrious-SDXL v17.0   + InstantID + OpenPose + hires
       ▼
   anime image
```

**Everything in ① and ② runs locally on 16 GiB and is digest-pinned.** Total 10.4 GB of weights.

⚠ **The licence is not cleanly Apache-2.0 and both earlier notes said it was.** Apache-2.0 covers
JoyCaption's *code*; its weights declare nothing and its base LLM is Llama-3.1, whose Community License
carries naming, acceptable-use and 700M-MAU terms. Fine for local rendering that distributes nothing.
**Not cleared for anything that ships** — recorded in the manifest and `JOYCAPTION.md` §9.

---

## 4 · The closed stack — the alternative

```
   photograph ──▶ ① Claude (vision) ──▶ ② Claude (tags) ──▶ ③ ──▶ ④
                     0.795 as a reader      0.575 as a router
```

**One model does both stages, and it is better at both.** But its sole advantage over the open stack is
quality, and it is not a large one:

| | open | closed | |
|---|---:|---:|---|
| stage ① as a reader | **0.518** | **0.795** | F42 · seven prompts tried |
| stage ② as a router | **0.482** | **0.575** | ROUTER.md §1 |
| rendered, WD14 on the output | **0.580** | **0.568** | a tie on n=5 |
| reproducible from a digest | **yes** | no | the reason round 4 existed |

**The rendered numbers tie.** The reader gap is real and the router gap is real, and by the time both
have passed through stage ③ and the generator they are inside the noise on five subjects.

**Cost, if the closed path is used at volume** — the briefing is byte-identical per photograph, so it
caches at ~10%, and Batch halves the rest:

```
   Opus 5, naive                              $0.0159 / photo      63 per $1
   Sonnet 5 + cached briefing + Batch         $0.0026 / photo     390 per $1
   Haiku 4.5 + cached briefing + Batch        $0.0013 / photo     790 per $1
```

**Which is why the two-stage split was never really about money.** A prose intermediate saves ~27% of an
already-tiny per-photograph cost; caching saves more. **The reason to split is that it puts the *seeing*
on an open, pinned model** — and the reason to keep the closed path configured is that one API key
replaces 10.4 GB of weights and a grammar.

---

## 5 · Where each stage's ceiling is

| stage | ceiling | evidence |
|---|---|---|
| ① VLM | **its eyes.** `00003`'s eyes are green; JoyCaption returned brown/blue under seven prompts and never once said green | F42 |
| ② router | **the caption.** `marks` is 0.00 for every router including Claude, because the caption denies the freckles | ROUTER.md §5 |
| ③ human | **what the photograph shows** — the only stage that can add what ① missed | §4's 0.35 |
| ④ diffusion | **the 77-token CLIP window.** Sheets already run 80–122 estimated tokens; every one is chunked and averaged | CRITERIA.md §2 |

**The stages fail in one direction only.** A worse caption cannot be repaired downstream by a better
router, and a better model at stage ② cannot recover a colour stage ① did not resolve. **So effort is
worth most at ①, and measurement is worth most at ③** — which is the argument for the review UI being
the next thing built rather than a bigger router.

---

## 6 · Open, in the order that matters

1. **The review UI** (N41) — the 0.35, and the only unbuilt stage. Requirements in `../README.md`.
2. **`pose` in the router**, 0.37 against 0.80. Curation, not capability.
3. **A better VLM.** Stage ①'s ceiling bounds everything after it. `Qwen3-VL` is the untried Apache-2.0
   control that would say how much of JoyCaption's 0.518 is its Danbooru training and how much is its
   eyes.
4. **An independent recognizer** (N27b) — `A`'s identity numbers are an upper bound while `glintr100` is
   both the encoder InstantID optimises against and the one scoring it.
5. **A phone-camera photograph.** Every input across four rounds is generated or professionally shot.
   **That is the product's actual input and it remains untested.**
