# The router — prose into a criteria sheet, with an open model

**Measured 2026-09-12. `prototype/router.py` is the harness, `prototype/tagmap.py` is the mapper.**
This note is a record: every number below was produced by the harness against the operator's reviewed
sheets, on the five captions in
`evaluations/2026-09-12/descriptive_and_booru/captions/descriptive/`.

**The job:** a VLM has described the photograph in English. Turn that prose into sixteen fields of
canonical Danbooru tags, ready for the operator to review.

---

## 1 · The number, and the four configurations behind it

```
  unconstrained          0.033   68 of 88 tags outside the vocabulary
  + enum grammar         0.316   0 outside — and 20 real tags in the WRONG FIELD
  + few-shot + mapper    0.482   0 outside, no wrong-slot class left
  ───────────────────────────
  Claude, by hand        0.575   the incumbent, and not reproducible
```

Mean recall over the seven scored criteria, `vlm_reader.py`'s measure. **14.6x from the first
configuration to the last, on the same model, the same prose and the same five subjects.**

| field | free | grammar | **few-shot + mapper** | Claude |
|---|---:|---:|---:|---:|
| hair colour | 0.00 | 0.80 | **0.80** | 0.80 |
| gaze | 0.00 | 0.00 | **0.60** | 0.60 |
| clothes | 0.07 | 0.24 | **0.61** | 0.77 |
| hair silhouette | 0.00 | 0.50 | **0.60** | 0.65 |
| eye colour | 0.00 | 0.40 | **0.40** | 0.40 |
| pose | 0.17 | 0.27 | 0.37 | 0.80 |
| marks | 0.00 | 0.00 | 0.00 | 0.00 |

**`gaze`, `eye colour` and `hair colour` match the hand-routing exactly.** `pose` is the remaining gap.
`marks` is 0.00 for *every* configuration including Claude, and that is not a router failure — see §5.

**And rendered, the difference disappears.** WD14 reading the renders scored the reviewed Qwen sheet at
**0.580** against the hand-routed sheet's **0.568** — a tie on n=5.

---

## 2 · Why the grammar was not the answer, though it looked like it

Ollama's `format` takes a JSON schema. Make each field an array of `enum` values over
`selected_tags.csv` and llama.cpp compiles it into a GBNF grammar, so an invalid tag becomes
**unemittable** rather than merely wrong. That is a stronger guarantee than validating afterwards, and it
is worth much less than it sounds.

**Logit masking works on token prefixes, not on meaning.** The model starts writing the English word it
meant; the grammar permits only tokens that continue *some* valid tag; it lands on the nearest tag
sharing that prefix.

```
  the caption said        the model meant        the grammar forced
  ────────────────        ───────────────        ──────────────────
  "tucked into jeans"     tuck into jeans   ──▶  tucked penis    (640 posts)
  "shoulder-length"       shoulder length   ──▶  shoulder blades
  "white blinds"          white blinds      ──▶  white bloomers
  "body slightly angled"  body slightly …   ──▶  body armor
  "faces front"           front             ──▶  front ponytail
```

> **A valid-but-wrong tag is worse than an invalid one.** `tuck into jeans` is caught by `sheet.py check`.
> `tucked penis` passes every guard in this project and gets rendered.

It is a coin flip on whether the nearest prefix happens to be right: `blonde` → `blonde hair` won,
`tucked` → `tucked penis` lost. **The grammar converts a visible failure into an invisible one**, which is
why the shipped configuration does not use it.

**Two further costs, both measured.** It is ~70s per subject against ~15s unconstrained. And a grammar
stops invalid tokens without stopping *repetition*: one subject emitted `"white robe"` forty times until
it exhausted `num_predict` and the JSON truncated. A context-free grammar cannot express *no repeats*, so
the bound has to go on length.

---

## 3 · What the shipped configuration actually is

**Generation stays unconstrained so the model writes what it means. The mapping to canonical vocabulary
happens afterwards, by shared words rather than shared prefix.**

```
  prose ─▶ Qwen3-8B ─▶ free-text sheet ─▶ tagmap ─▶ canonical sheet
           ▲                                ▲
           │ JSON schema: 16 string         │ ① exact      already a tag
           │   fields. Structure is         │ ② suffix     blonde → blonde hair
           │   guaranteed, content is       │ ③ curated    shoulder length → medium hair
           │   free.                        │ ④ containment  tuck into jeans → jeans
           │ think: false
           │ two worked examples
```

### The four passes, and the order matters

| pass | rule | example |
|---|---|---|
| **exact** | the phrase is already a tag | `wavy hair`, `high heels` |
| **suffix** | the vocabulary's per-field convention | `blonde` → `blonde hair`, `blue` → `blue eyes` |
| **curated** | a written-down synonym; **consumes its span** and continues | `shoulder length` → `medium hair` |
| **containment** | the tag whose *every* word is in the phrase, longest first | `tuck into jeans` → `jeans` |

**Containment, not a ratio.** Scoring `|phrase ∩ tag| / |tag|` let `white shirt open collar` return
`white sailor collar` — two of three words matched and `sailor` came free. Requiring every word of the
tag to appear in the phrase makes that unreachable and needs no threshold.

**The curated pass consumes spans rather than returning on its first hit.** Returning early was a
measured bug: `white open toe high heels` matched `open toe` → drop and the whole phrase died, losing
`high heels`. A caption phrase routinely carries two or three concepts.

### Three deliberate refusals

- **An empty list is a real answer.** `high-waisted`, `sharp focus` and `forward facing` carry nothing a
  generator can draw. Emitting nothing is correct; emitting something is F44's failure.
- **Absence clauses die here.** `no distinguishing marks` → nothing. F44: CLIP has no negation, so an
  absence in a positive prompt is a *presence instruction* — the render came back with tattoos. **The
  router is the seam where negation dies**, and `router.py`'s `absence_leaks` counter measures it.
- **Single-word matches are accepted except for stranded modifiers.** `clear sunny day` means `day` and
  `blue couch` means `couch`; requiring two words dropped both. But bare `light`, `white`, `long` and
  friends are tags in their own right and almost always a modifier stranded from a compound the
  vocabulary lacks.

### Few-shot, which was the largest untried lever

Two worked examples — one female upper body, one male, because `count` is a field and not a constant.
Drawn from `00072` and `male_cowboy_shot_1`, **neither of which is scored**, so nothing leaks. The
briefing had rules and no examples until 2026-09-12.

---

## 4 · Two traps in hosting, both measured

- **Thinking tokens are drawn from the answer's budget.** Qwen3 is a hybrid reasoner; its thinking
  truncated the JSON mid-string on the third subject. `think: false` — routing is slot-filling, not
  reasoning.
- **`Mistral-Small-3.2-24B` was abandoned on hardware, not licence.** `ollama create` copied 13 GB and
  then ran out of disk writing its validation temp, from 34 GiB free: Ollama's import wants roughly twice
  the file. And Q4_K_M is 13 GB on a 16 GiB machine, so even hosted it would page through every token —
  the test would have measured swap. **Not a verdict on the model.**

---

## 5 · What the router cannot fix, and it is the ceiling

**`marks` is 0.00 for every configuration, including Claude by hand.** The only subject with marks is
`00003` (`freckles`), and JoyCaption's caption explicitly denies them. `eye colour` sits at 0.40 for the
same reason: the caption says blue where the photograph is green.

> **A router cannot recover what the caption never carried.** The ceiling on this stack is the VLM's
> eyes, and no amount of mapping, grammar or model size reaches past it.

**Which is why the review step is not optional.** Measured end to end: the open route unreviewed delivers
**0.568** of the reviewed sheet's attributes through to the render; the reviewed sheet delivers **0.917**.
**The human in the loop is worth 0.35** — see [`ARCHITECTURE.md`](ARCHITECTURE.md) §4.

---

## 6 · Open

- **`pose` at 0.37 against Claude's 0.80** is the largest remaining gap. Captions describe pose as
  sentences — *"body slightly angled to the right"* — and the mapper drops them rather than guess. More
  `PHRASES` entries close it; that is curation, and it is the maintenance cost `JOYCAPTION.md` §5
  predicted, now with a number attached.
- **Per-field enums are unbuilt.** Derived from the vocabulary the sets are tiny — `count` 5, `framing`
  13, `gaze` 20, `body shape` 51 — and they would make a wrong-slot tag unemittable rather than scored
  down. **A crude keyword derivation is not enough**: `marks` picks up `scarf` because it contains `scar`.
- **A bigger open model is untested.** `Qwen3-32B` is Apache-2.0 and is the honest *is it size?* test,
  ~$0.50 on a pod. Worth knowing in advance: if the answer is "needs 32B", the open stack stops being
  *local* and becomes *rented*.
- **n = 5.** Every number here is five subjects. The harness takes a `--model` flag and any candidate is
  a one-line swap; the set is the thing that should grow first.
