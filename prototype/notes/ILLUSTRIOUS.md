# Illustrious and the Danbooru vocabulary — a prompting reference

**Researched 2026-09-08 for round 2 of the prototype.** The operator's own
[`danbooru_tags.md`](../../README.md) note covers the Danbooru tag system in general; **this note is about
what the Illustrious family in particular was trained on**, because F28 found that canonical tags work and
invented ones do not, and the next question is *which* canonical vocabulary and in *what shape*.

The base this repository runs is **WAI-illustrious-SDXL v17.0**, an Illustrious/SDXL finetune. Everything
below about Illustrious applies to it by inheritance, and every claim that comes from a *finetune's* card
rather than from Illustrious itself is marked, because the two can disagree.

Sources are listed at the foot. **The primary source is the Illustrious paper** (arXiv 2409.19946); the
community guides are secondary and are marked as such, because they are where the folklore lives.

---

## 1. What it was trained on — the operator's memory was right

| model | training images |
|---|---|
| Illustrious v0.1 | 7.5 M |
| Illustrious v1.0 | 10 M |
| Illustrious v1.1 | 12 M |
| Illustrious v2.0 | 20 M |
| Animagine XL 4.0 | 8.4 M *(publisher's figure)* |

The paper: *"Danbooru dataset is a public large-scale anime image dataset with over 8 million images."*
Illustrious trains on it at scale and **v1.0 onward exceeds Animagine's corpus**, with later versions
using a **Danbooru 2024-June** snapshot per the community guides.

**Why this matters for us.** A larger Danbooru corpus means *more of the tail of the tag vocabulary is
actually learned* — the rare tags that F28 says silently do nothing on a smaller model are more likely to
mean something here. It is an argument for reaching further into canonical Danbooru, not for inventing
descriptions.

The paper is also honest about the ceiling: the vocabulary *"makes it unsuitable for interpolation
tasks"* and *"struggles with more complex concepts like 'covering wound with left hand' due to
insufficient data."* **A tag exists on Danbooru is necessary, not sufficient** — it also has to be common.

---

## 2. The caption schema it was actually trained with

This is the most useful thing in the paper, and it is a direct instruction for how to order a prompt:

```
person count ||| character names ||| rating ||| general tags ||| artist ||| score range ||| year modifier
```

Our sheets emit:

```
1girl, solo ||| — ||| — ||| <the fourteen fields> ||| — ||| masterpiece, best quality, amazing quality ||| —
```

So we already match the schema in its first and sixth slots, and leave three deliberately empty
(no character, no artist — the face is the subject's own, which is the whole product). **Two slots we have
never filled are `rating` and `year modifier`**, and both are trained-in levers:

- **Rating** — `general`, `sensitive`, `questionable`, `explicit`. One community guide calls omitting it
  *"not recommended"*. Untested here.
- **Year modifier** — the paper's Table 4: `oldest` (~2017), `old` (~2019), `modern` (~2020),
  `recent` (~2022), `newest` (~2023). **A trained era-of-anime-style dial we have never touched**, and
  plausibly a lever on the flat-cel register that round 2 is still 28% short of.

---

## 3. The quality ladder — ours may contain a tag Illustrious never learned

The paper's Table 3 gives the **trained** quality tiers, each tied to a percentile band:

| tag | percentile |
|---|---|
| `worst quality` | ~8% |
| `bad quality` | ~20% |
| `average quality` | ~60% |
| `good quality` | ~82% |
| `best quality` | ~92% |
| `masterpiece` | ~100% |

**`amazing quality` is not in that list.** Our positive prompt ends `masterpiece, best quality, amazing
quality`, which came from WAI's own model page — so it is either something the *finetune* trained in, or
a community habit inherited from elsewhere. **Unresolved, and cheap to test**: an arm with it and an arm
without, since it costs three tokens in a prompt already near the window.

Community guides agree the ladder belongs **at the end** of the prompt, which is where ours is.

---

## 4. Underscores — genuinely unsettled, and the paper does not decide it

The operator's instinct is that tags should carry underscores. **The primary source does not answer it.**
What the paper says is about the *separator between* tags, not the spelling *within* one:

> *"In the v0.1 model training, we split the tags using the ',' convention, later occasionally replacing
> it with spaces based on a certain probability."*

That describes comma-versus-space **between** tags. Whether `long_hair` reached the text encoder as
`long_hair` or `long hair` is not stated, and Danbooru stores the underscored form.

The secondary sources split:

- One guide is explicit: *"Use underscores (_) instead of half-width spaces: long_hair, black_hair"*.
- Another reports the opposite in practice: replacing underscores with spaces *"often improves the
  success rate when using copyright characters"*, and recommends spaces **to save tokens**.

**The token argument is checkable and is the one that bites us**, because our prompts already exceed
CLIP's 77-token window. `long_hair` and `long hair` do not tokenise to the same number of tokens.

**Recommendation: settle it with an arm, not with a guide.** Same sheets, same seed, one render with
spaces and one with underscores. It is the cheapest unresolved question on the list and the operator's
instinct may well be right — nothing here contradicts it, and nothing here confirms it.

---

## 5. The negative prompt — ours has never changed and is shorter than the family's

The shipped negative is WAI's own short form:

```
bad quality, worst quality, worst detail, sketch, censor, nsfw
```

Community consensus for Illustrious is markedly longer, and the guides are emphatic that **Illustrious is
*sensitive* to negatives in a way Pony-family models are not** — *"they can significantly improve
results"*.

A widely-quoted short Illustrious negative:

```
lowres, worst quality, bad quality, bad anatomy, sketch, jpeg artifacts, signature, watermark,
artist name, old, oldest
```

Note that `worst quality` and `bad quality` are the **trained ladder's bottom two rungs** from §3 — so a
negative built from them is pushing against a scale the model actually learned, rather than against
adjectives. `old` and `oldest` are the **year modifiers** from §2, used in the negative to steer away from
older art styles.

Our negative contains `worst detail`, which appears in no Danbooru vocabulary and no trained ladder —
**F28's exact failure mode, sitting in the negative prompt since v0.10 and never questioned.**

**Two things worth testing, separately:** the longer negative, and the removal of `worst detail`.

---

## 6. Skin tone — why `00003` came back bleached

Straight from the Danbooru wiki, and it explains a live complaint:

| tag | the wiki's definition |
|---|---|
| `pale skin` | *"significantly lighter in tone than the usual Eurasian skintone, or skin which appears 'bleached', lacking in color"* |
| `tan` | *"skin darkened due to exposure to the sun"* |
| `dark skin` | *"darker in tone than the usual Eurasian skin tone"* |
| `very dark skin` | the step beyond `dark skin` |
| `dark-skinned female` | the gendered form, which is the one that actually carries in most models |

**`pale skin` is not "fair" — it is "bleached".** `00003`'s sheet declared it and the render obeyed
exactly, which is why the operator saw skin that was *"very very white"*. Her photograph is sun-tanned, so
the canonical tag is **`tan`**, and the correct tag for an ordinary light-skinned subject is **no skin tag
at all** — the Danbooru default *is* the usual Eurasian tone, and every skin tag is a deviation from it.

The wiki also records that `tan` and `dark skin` are near-indistinguishable without **tanlines**, which is
the feature that separates them.

**Corrected 2026-09-08** across the sheets: `pale skin` is now used only where the subject really is
pale, `tan` where the photograph is sun-darkened, and the tag is omitted where the subject is simply
light-skinned.

---

## 6b. WAI v17 itself — researched 2026-09-09

**The question was whether our finetune has a vocabulary of its own. It does not** — its guidance is
standard Danbooru tagging. But its published settings disagree with what we run in three places, and
one of them invalidates a test we already did.

| | WAI's page says | we do |
|---|---|---|
| quality string | `masterpiece, best quality, amazing quality, newest` | `masterpiece, best quality, amazing quality` |
| where it goes | *"Always **start** your positive prompt with"* it | **we put it last** |
| sampler | Euler a / `K_EULER_ANCESTRAL` | `euler_ancestral` ✅ |
| steps | 20–30 | 28 ✅ |
| CFG | 5–7 | 5 ✅ |
| hires | R-ESRGAN 4x+ Anime6B, 20 steps, denoise 0.35–0.5 | **we have no upscale stage** |

### Three things follow

- **`amazing quality` is WAI's, and §3's open question is closed.** It is not in the Illustrious paper's
  trained ladder, but it *is* in this finetune's published string, so it was trained here. Keep it.
- **`newest` belongs inside the ladder, and F32's test of it was malformed.** N16's `3_schema` arm put
  `newest` at the very end *after* the ladder and bundled it with a `general` rating tag — WAI writes it
  as the ladder's fourth element at the front. **That arm did not test what WAI recommends**, so
  `newest` deserves a second, correctly-formed attempt.
- **Ladder placement is a live disagreement between sources.** The Illustrious community guide says
  quality tags go at the end; **WAI's own page says start.** For this checkpoint the publisher wins on
  authority, and we currently follow the guide. Untested, one arm, near-zero cost.

**Our sampler, steps and CFG are already inside WAI's recommended ranges**, which kills a hypothesis:
they are not an untested lever, they are the publisher's own values.

### The hires stage is the one structural gap

WAI recommends a second pass — R-ESRGAN 4x+ Anime6B upscale, 20 steps, denoise 0.35–0.5. **We have no
upscale stage at all.** That is not a dial or a tag; it is a pipeline stage the publisher assumes and we
have never run, and it needs an upscaler model on the pod plus two graph nodes.

## 7. What to do with this — ranked, cheapest first

**Items 1–4 were run as N16 and are settled — see F32.** Only the two *definitional* fixes helped;
the longer negative, the schema slots and underscores **all made the render worse**, by 6–10x the
determinism floor. What remains is what §6b turned up:

1. **Move the quality ladder to the front, in WAI's exact form** — `masterpiece, best quality, amazing
   quality, newest` — instead of last. §6b. One arm, ~zero token cost, and it follows the publisher over
   a community guide on the publisher's own checkpoint. **The highest-value untested prompt change left.**
2. **Add the hires pass.** §6b. The one structural gap, and the publisher assumes it. Needs an upscaler
   on the pod and two nodes; not a prompt change.
3. ~~`amazing quality` in or out~~ — **closed**: it is WAI's own tag. Keep it.
4. ~~Underscores~~, ~~the long negative~~, ~~`rating`~~ — **closed by F32, all negative.**

**Every one is a prompt change, and none needs a graph change.** That is the shape round 2 has been in
since F27: the architecture is settled and the vocabulary is where the remaining gains are.

---

## Sources

Primary:
- [*Illustrious: an Open Advanced Illustration Model*](https://arxiv.org/html/2409.19946v1) — the caption
  schema, the training sizes, the quality tiers and year modifiers, the tag-separator note, and the
  stated vocabulary limitations. **Everything load-bearing above comes from here.**
- [Danbooru wiki: `pale skin`](https://danbooru.donmai.us/wiki_pages/pale_skin) ·
  [`dark skin`](https://danbooru.donmai.us/wiki_pages/dark_skin) ·
  [`tan`](https://danbooru.donmai.us/wiki_pages/tan) ·
  [Tag Group: Skin Color](https://danbooru.donmai.us/wiki_pages/tag_group:skin_color)
- [OnomaAIResearch/Illustrious-XL-v1.0 model card](https://huggingface.co/OnomaAIResearch/Illustrious-XL-v1.0)
  — read, and it says **nothing** about tag format, ordering, quality tags or negatives. Recorded so it is
  not re-read expecting an answer.

Secondary, and treated as folklore rather than fact:
- [kazumu, *Illustrious / Animagine Prompt Guide*](https://note.com/kazumu/n/n6390a899bdce?hl=en) — the
  underscore recommendation, and quality tags at the end.
- [Tensor.Art, *Comprehensive Guide of Illustrious XL*](https://tensor.art/articles/831123524065191393)
  and [*IllustriousXL Generation Guide*](https://tensor.art/articles/798120703305104719) — the negative
  prompt forms, and Illustrious's sensitivity to negatives.
- [Tech Tactician, *Booru-Style Tagging with SDXL Anime Models*](https://techtactician.com/booru-style-tagging-sdxl-anime-prompts-guide/)
  — the spaces-save-tokens argument.
- [Anifusion model comparison](https://anifusion.ai/models/) — Animagine XL 4.0's 8.4 M figure.
