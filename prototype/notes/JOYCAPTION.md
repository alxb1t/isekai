# Trialling JoyCaption as the photograph reader — the plan

**Written 2026-09-11, before anything was downloaded or run.** This is a plan, not a record: every number
below is either measured elsewhere and cited, or is a bar stated in advance. Nothing here reports a
result. `READER.md` is the survey that chose this candidate; this is what we do about it.

---

## 1 · Why this and not something else

**The problem is reproducibility, not quality.** The reader that turns a photograph into a criteria sheet
is currently **an agent session** — it scores 0.78 on synthetic photographs and 0.80 on real ones, which
is good, and it is **not reproducible by anyone without the transcript that produced it.** A repository
arguing for open models end to end has a closed, unversioned, un-pinnable component at step one.

**JoyCaption is the only surveyed candidate built for this vocabulary.** Apache-2.0, Llama 3.1 + LLaVA,
8B, and it ships a **Danbooru tag mode** — one of four booru modes among eleven. Critically it is trained
on **photographs as well as illustrations**, which is precisely the property WD14 lacks and why WD14
scores 0.47 on photographs against 0.73 on renders (F29).

Full candidate comparison, licences and the alternatives considered: **[`READER.md`](READER.md)**.

---

## 2 · The evidence we already have, and it is one photograph

The operator ran `standing_turn.png` through the public demo on 2026-09-11. Its raw output, scored against
that subject's **reviewed** sheet by the same recall measure `vlm_reader.py` uses:

| field | reference | found |
|---|---|---|
| count | `1girl, solo` | **all** |
| hair colour | `brown hair` | **all** |
| hair silhouette | `long hair, straight hair` | 1/2 — missed `straight hair` |
| eye colour | `brown eyes` | **all** |
| **clothes** | `red shirt, long sleeves, shirt, blue pants, denim, white footwear` | **all six** |
| accessories | `earrings` | **0/1** |
| expression | `closed mouth` | **all** |
| gaze | `looking at viewer` | **all** |
| **pose** | `standing, from side, looking back, hand on own hip` | **1/4** |
| framing | `full body` | **all** |
| body shape | `medium breasts` | **0/1** |
| background | `simple background, grey background` | 1/2 |

**Mean agreement: 0.688.** Against WD14's **0.47**, the stated floor of **0.60**, and the incumbent's
**0.78**.

> **n = 1. This is a data point, not a result**, and the only reason it is written down is that its
> *shape* is informative.

### The shape is the interesting part

**Every miss is in a field JoyCaption had no reason to look at.** It was asked for a generic Danbooru tag
dump. Nobody told it we care whether the subject is `from side`, or that `medium breasts` is the tag F26
measured as fixing the age drift that three attempts at the age tag could not.

**The incumbent scores 0.78 because it is briefed with the sixteen-field schema.** That reframes the
question this trial has to answer, and it is not "is JoyCaption good enough":

> ### Is JoyCaption a *tagger we route*, or a *reader we brief*?

Those imply completely different integrations, and §5 is written around the fork.

---

## 3 · The bar, stated before the run

Written here so it cannot be adjusted to whatever the run produces — the same discipline that makes the
incumbent's 0.78 meaningful, since its 0.60 floor was stated first, and that F1 records this project
failing to observe once already.

| result | meaning |
|---|---|
| **≥ 0.78** mean agreement over 13 photographs | **replaces the agent session.** The reproducibility problem is solved outright |
| **0.60 – 0.78** | becomes the **first-draft generator** feeding the operator's review. Better than a blank page, not a replacement |
| **< 0.60** | **fails**, as WD14 did at 0.47 |

**Measured by `vlm_reader.py`, unchanged**, against the thirteen reviewed sheets. Per-field floor stays
0.40. The middle band is not a consolation prize: `CRITERIA.md`'s architecture already has an operator
review step, and a 0.69 first draft with perfect `clothes` is a materially better starting point than
nothing.

---

## 4 · The plan

```
  ① PIN      digests + licence recorded BEFORE the download
  ② HOST     LM Studio, already installed — no new dependency
  ③ CLIENT   prototype/joycaption.py, stdlib urllib only
  ④ RUN      both phases, same 13 photographs, one sitting
  ⑤ SCORE    vlm_reader.py, unchanged
  ⑥ DECIDE   §3's bar, and §5's fork
```

### ① The artifacts, and why this exact repository

| file | size | sha256 |
|---|---|---|
| `Llama-Joycaption-Beta-One-Hf-Llava-Q4_K.gguf` | 4.92 GB | `e8ae55dd07e61d54…` |
| `llama-joycaption-beta-one-llava-mmproj-model-f16.gguf` | 0.88 GB | `94002cb5c354c7c9…` |

From **`concedo/llama-joycaption-beta-one-hf-llava-mmproj-gguf`** (12,965 downloads; `concedo` is the
KoboldCpp author).

> **⚠ The two GGUF repositories `READER.md` originally cited — `mradermacher` and `Mungert` — ship no
> `mmproj` at all.** A LLaVA-family model without its vision projector is **text-only and silently cannot
> see the image**. It would have loaded, answered, and described nothing. Found by listing the repository
> contents before downloading rather than after. `READER.md` is corrected.

**Pinned in `prototype/styles/joycaption_models.json`**, the same pattern as `wd14_models.json`: source
URL, destination, sha256, verified before every run. A score produced by unverified bytes is a number
from an unknown thing.

**Licence goes in `scripts/eval_licences.md` before the download, not after** — with the URL and the date
read, as every other pinned artifact here has. The upstream project is **Apache-2.0**
([LICENSE](https://github.com/fpgaminer/joycaption/blob/main/LICENSE), confirmed by the operator
2026-09-11); `concedo`'s requantisation states no licence of its own, and that gap is what gets recorded.

### ② Hosting: LM Studio, and the reason is the dependency rule

**Already installed**, handles the `mmproj` pairing itself, and exposes an OpenAI-compatible HTTP endpoint
on localhost. So the client is **stdlib `urllib` against a local port** — no new Python package, which
keeps `CLAUDE.md`'s *deps minimal and human-gated* rule intact without needing an exemption.

Fits 16 GB: Q4_K is 4.92 GB plus 0.88 GB projector plus context.

**Ollama is the fallback** if LM Studio's vision handling disappoints. Also already installed.

### ③–④ The two phases, run together

Both over the **same thirteen photographs** — the ten synthetic and three real subjects that already have
reviewed sheets — in one sitting, because the comparison *between* them is the finding:

| phase | prompt | writes to |
|---|---|---|
| **0** | JoyCaption's own **Danbooru tag list** mode | `vlm_drafts/…/jc_booru/` |
| **1** | **our sixteen-field schema**, the briefing `vlm_reader.py --schema` prints | `vlm_drafts/…/jc_schema/` |

Phase 0 asks *how good is the raw tag dump*. Phase 1 asks *can it follow our schema* — and its model card
warns instruction-following is its weak point, so this is a real question rather than a formality.

---

## 5 · The fork, and what each branch costs

**Phase 1's result chooses the integration.** Sketched now so neither branch is designed under the
pressure of a result.

### If the briefed schema works → drop-in replacement

`joycaption.py` writes `<id>.json` exactly as the agent session does; everything downstream is unchanged.
`sheet.py adopt` still writes the table, the operator still reviews it, `sheet.py build` still assembles
the prompt. **One stage, one model, reproducibility solved.**

### If only the tag dump works → a router is needed

A flat tag list has to be sorted into sixteen named fields, and **the field a tag lands in changes what
the prompt does with it**. That means a `tag → field` map:

- **deterministic and open** — no second model, which keeps the whole reader auditable;
- **bounded** — a few hundred tags cover the fields that matter, not `selected_tags.csv`'s 8,106;
- **real work**, and it has to be maintained as the vocabulary is used more widely.

### Either way → JoyCaption may be a first draft rather than a reader

The architecture already has the review step; `CRITERIA.md` §1 is built around it. **0.688 with perfect
`clothes` is a better starting point than a blank page even if it never reaches 0.78.** This is the
outcome the middle band of §3 describes, and it is a success rather than a fallback.

---

## 6 · Five traps, four of them visible in one sample

Every one is deterministic to fix, and none needs a model.

| trap | seen as | why it matters |
|---|---|---|
| **underscores** | `blue_pants`, `looking_at_viewer` | **F32 measured underscores as 0.013 worse than spaces** — six times the determinism floor. Convert on ingest |
| **meta tags** | `photo (medium)`, `copyright:original` | **`photo (medium)` is actively harmful** — it instructs an anime model to render a photograph. Strip |
| **non-canonical variants** | `hands on hips` | **not in the vocabulary at all** — canonical is `hands on own hips` (25,548). F28: invented tags do nothing. `sheet.py check` already catches these, which is why it runs before anything reaches a prompt |
| **redundancy** | `jeans` + `pants` + `blue pants` + `denim`; `shoes` + `sneakers` + `white footwear` | not wrong, but **the token budget is already the binding constraint** (`CRITERIA.md` §2) |
| **internal contradiction** | `smile` alongside `closed mouth` | both canonical, mildly inconsistent. The operator's review is where this is caught; worth counting how often it happens |

**The first three are a normalisation pass**, and it belongs in `joycaption.py` rather than in `sheet.py`
— `sheet.py` serves every reader, and a cleanup written for one model's quirks does not belong in the
shared path.

---

## 7 · What would make this fail, stated in advance

- **It cannot follow the schema and its tag dump is mediocre.** Then the router is expensive and the
  input to it is weak, and the honest answer is that the agent session stays until something better
  exists. Recording this as an acceptable outcome now.
- **Vision through LM Studio misbehaves on this architecture.** Ollama is the fallback; if both fail the
  blocker is hosting rather than the model, and that is a different problem with different options.
- **Q4_K degrades it materially.** The demo the operator used is presumably full precision. If the local
  numbers come in far under 0.688 on `standing_turn`, **quantisation is the first suspect** — Q8_0 at
  8.54 GB is the check, and it still fits.
- **16 GB is not enough in practice.** Q4_K plus projector plus context should fit; if it swaps, Q8_0 is
  out and the pod becomes the trial host, with the reproducibility question unresolved.

---

## 8 · Open, and deliberately not decided yet

- **Which prompt exactly for phase 1.** `vlm_reader.py --schema` prints the incumbent's briefing, and
  reusing it verbatim is the fairest comparison. But it was written *for an agent*, and a 8B captioner may
  need it shorter. **Changing it makes the comparison unfair**, so: first run uses it verbatim, and any
  rewrite is a second arm rather than a correction.
- **Whether the three real-subject photographs are included.** They have reviewed sheets and would make
  the number comparable to the incumbent's 0.80. They are also a real person's photographs going into a
  local model — which is *fine*, it never leaves the machine, and is worth stating rather than assuming.
- **What happens to `vlm_reader.py`'s own briefing** if JoyCaption wins. It is currently the reader's
  instructions; it would become one reader's instructions among two.
