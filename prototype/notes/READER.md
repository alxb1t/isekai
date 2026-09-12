# Who reads the photograph — a survey of open candidates

**Researched 2026-09-11 for N26. Desk research only: nothing here has been run, and every number
attributed to a candidate is its publisher's or a third party's, not ours.** The one number measured in
this repository is the incumbent's, and it is at the top of §2 so the rest can be read against it.

---

## 1 · The job, stated precisely, because it is not "captioning"

The pipeline's first step turns a photograph into a **criteria sheet**: sixteen named fields, each filled
with canonical Danbooru tags.

```
  photograph ─▶ READER ─▶ { "count": "1girl, solo",
                            "hair colour": "brown hair",
                            "hair silhouette": "long hair, wavy hair",
                            "pose": "standing, hands on own hips",
                            … 12 more }
```

**This is structured extraction into a closed vocabulary, not free-text description.** The distinction
decides which candidates are even relevant:

- a model that writes *"a woman with long brown hair standing with her hands on her hips"* has done
  something useful and has **not** done this job;
- a model that emits a flat tag list has done half of it — the tags still have to be sorted into the
  sixteen fields, and the field a tag lands in changes what the prompt does with it;
- the vocabulary is closed. **F28: canonical tags work, invented ones do nothing** — across two rounds,
  no exception. `sheet.py check` enforces it against `selected_tags.csv`, so an invented tag is caught
  before it reaches a prompt, but a reader that invents freely wastes the fields it invents in.

**Three different jobs keep getting confused, and they are worth separating once more:**

| | what it does | what it is |
|---|---|---|
| `selected_tags.csv` | 8,106 tag names with post counts | the **vocabulary check** |
| the WD14 *model* | reads a **render**, emits tags | the **evaluator** (`criteria_eval.py`) |
| **the reader** | reads a **photograph**, fills the sheet | **what this note is about** |

---

## 2 · The numbers to beat, both measured here

**The incumbent is an agent session** — `vlm_reader.py --schema` prints the briefing, a model reads the
photographs, drafts land as JSON. Measured against the operator's reviewed sheets:

| | mean agreement | invented tags |
|---|---:|---:|
| **the agent session** | **0.78** synthetic · **0.80** real | ~1% (4 of ~400) |
| *floor stated before that run* | *0.60* | — |

**And the honest baseline, which is that we already own a tagger and it cannot do this.** F29 measured
WD14 on photographs at **0.47**, against 0.73 on renders — with **`pose` at 0.08 and `marks` at 0.00**.
It is trained on drawings. **Any candidate has to beat 0.47 to be interesting and 0.78 to be a
replacement**, and the gap between those two numbers is the whole search space.

> **Why replace something scoring 0.78 at all?** Because it is **not reproducible by anyone without this
> transcript.** A repository whose thesis is *open models, end to end* has a closed, unversioned,
> un-pinnable component at step one. That is the entire motivation — not quality.

---

## 3 · The candidates

### JoyCaption — the only one built for this vocabulary

| | |
|---|---|
| licence | **Not cleanly Apache-2.0 — confirmed 2026-09-12, and this row said otherwise.** Apache-2.0 covers the project's *code*; the weights carry **no `license` field**, and the base LLM is `meta-llama/Llama-3.1-8B-Instruct` under the **Llama 3.1 Community License**, which a fine-tune derives from. All four layers recorded in `prototype/styles/joycaption_models.json` and in [`JOYCAPTION.md`](JOYCAPTION.md) §9 |
| base | Llama 3.1 + LLaVA architecture, SigLIP2 vision encoder, **8B** |
| current | **Beta One**, described as nearing 1.0 |
| size | **~17 GB** at bf16; GGUF quantisations at **Q4_K 4.92 GB**, Q8_0 8.54 GB, **plus an 0.88 GB vision projector** — see the warning below |

**It has a Danbooru tag mode.** Eleven caption modes are documented, four of them booru: *Danbooru tag
list* (`lowercase_underscores`, strict `artist: / copyright: / character: / meta: / general` order),
*e621*, *Rule34*, and a generic *Booru-Like Tag List*. Nothing else surveyed here was built against this
vocabulary at all.

**It is explicitly trained on photographs as well as illustrations** — the author's framing is *"digital
art? Photoreal? Anime? Furry? JoyCaption is for everyone."* That is the property WD14 lacks and the
reason this is the lead candidate rather than merely a relevant one.

> **⚠ A LLaVA-family GGUF needs its `mmproj` and most repackagings do not ship one.** Checked
> 2026-09-11: the two most-cited quantisations — `mradermacher` and `Mungert`, both listed in the sources
> below — contain **no vision projector at all**. Loading either gives a model that answers fluently and
> **cannot see the image**. The one that ships both is
> [`concedo/llama-joycaption-beta-one-hf-llava-mmproj-gguf`](https://huggingface.co/concedo/llama-joycaption-beta-one-hf-llava-mmproj-gguf)
> (12,965 downloads; `concedo` is the KoboldCpp author). **List a repository's contents before
> downloading it**, not after — this failure is silent.

**Stated failure modes, from the project itself:** glitches 1.5–3% of the time; multiple subjects;
left/right confusion; OCR. **The left/right confusion matters here more than it looks** — `hands on own
hips` survives it, but the pose field routinely distinguishes sides, and F38 measured that a single
wrong limb is a different pose rather than a small error.

**The caveat that decides how it would be used:** the "modes" are **prompt strings, not an API**. There
is no structured-output mode. So it would be driven by our own sixteen-field schema exactly as the agent
is — which means the comparison is fair, and it also means JoyCaption's Danbooru training is an
advantage in *vocabulary* rather than in *format*.

### Qwen3-VL — the strong generalist, and the practical local option

| | |
|---|---|
| licence | **Apache-2.0** across the released sizes |
| sizes | dense **2B → 32B**, plus MoE at 30B-A3B and 235B-A22B |
| local fit | **4B ≈ 8.9 GB**, **8B ≈ 17.5 GB**; INT4 brings 8B to roughly 6 GB |

Reported as the strongest open model on OCR and structured reading, which is the closest published proxy
for "follow a sixteen-field schema without drifting". **No booru vocabulary knowledge** — it would be
working from our briefing alone, which is precisely what the incumbent does, so this is the most direct
like-for-like replacement for the agent session.

### InternVL3 — the permissive alternative

MIT-licensed and reported as the best permissively licensed option, stronger on document layout and
table extraction, marginally ahead on general image understanding at 8B scale. One published
fine-grained-attribute comparison puts **InternVL3 at 50.1% and Qwen2.5-VL at 45.1% on pattern
recognition, both around 30% on shape** — which is a useful caution about the *absolute* difficulty of
attribute extraction, and not a measurement of our task.

### Molmo — research value, not production value

Apache-2.0 with **weights, training data and code all released**, which is a stronger openness claim than
anything else here and genuinely matters to a repository arguing for open models. But as of 2026 it is
reported as materially behind on quality, with most deployments choosing Qwen or InternVL. **Listed for
completeness and not recommended to trial first.**

### Hosted, via OpenRouter

Small vision models are effectively free at this volume — Qwen flash-class models run **$0.03–0.13 per
million tokens**, and a thirteen-photograph run is a rounding error. **But hosting reintroduces exactly
the dependency N26 exists to remove**: an API key, a vendor, a model that can be withdrawn or silently
revised. Worth it only as a *cheap way to rank candidates* before committing to a local deployment —
never as the answer.

### What does not exist

**There is no Danbooru tagger trained on photographs.** DeepDanbooru, Danbooru's own autotagger, WD14 and
its variants are all trained on anime imagery. This was searched for directly and the absence is the
finding: **the WD14-shaped hole cannot be filled by a better tagger, only by a VLM.**

---

## 4 · What this means

**JoyCaption first, Qwen3-VL second, and both against the harness that already exists.**

1. **JoyCaption Beta One** is the only candidate built for this vocabulary and trained on photographs.
   If it reaches 0.78 it replaces the agent session outright and the reproducibility problem is solved.
2. **Qwen3-VL-8B** is the like-for-like control: no booru training, driven purely by our briefing, which
   isolates *how much the Danbooru vocabulary knowledge is actually worth*. If JoyCaption and Qwen3-VL
   score the same, the vocabulary training is decorative and the field is wide open.
3. **A hybrid is not available.** The obvious "WD14 for tags, VLM for the rest" cannot work when WD14
   scores 0.08 on `pose` and 0.00 on `marks` **on photographs**. It has nothing to contribute at this
   end of the pipeline.

**No new evaluation harness is needed, and that is worth knowing before anyone builds one.**
`vlm_reader.py` already scores a draft against the operator's reviewed sheets — recall per field, mean
across fields, floors of 0.60 mean and 0.40 per field stated before the incumbent ran. **Any candidate
that writes `<id>.json` into the drafts directory is scored by the same code against the same ten
photographs, and its number is directly comparable to 0.78.**

```
  candidate ─▶ drafts/synthetic/<id>.json ─▶ vlm_reader.py ─▶ mean agreement
                                                              vs 0.78 incumbent
                                                              vs 0.47 WD14
                                                              vs 0.60 stated floor
```

**The trial is planned in [`JOYCAPTION.md`](JOYCAPTION.md)** — artifacts, hosting, the two phases and the
bar, all stated before the run.

**Cost to trial:** JoyCaption at Q4_K is 4.92 GB plus an 0.88 GB projector, and runs on the pod we already
boot, or locally.
Qwen3-VL-4B is 8.9 GB. Neither needs a GPU session of its own if it rides an existing one — and both can
be trialled on the thirteen photographs already transcribed and reviewed.

### Two things to decide before trialling, not after

- ~~**Confirm JoyCaption's licence from the weights themselves.**~~ **Done 2026-09-12, and the answer
  was not the expected one.** The weights declare nothing and the base LLM is Llama 3.1, so the honest
  statement is *Apache-2.0 code over Llama-3.1-licensed weights* — see §3's licence row. It is recorded in
  **`prototype/styles/joycaption_models.json`**, not `scripts/eval_licences.md`: that file is tracked and
  belongs to `eval_models.json`, and `wd14_models.json` already set the precedent of a prototype artifact
  carrying its own licence record.
- **State the bar first.** The incumbent's 0.60 floor was stated before it ran, which is why its 0.78
  means something. A candidate trialled without a stated bar will be judged against whatever it scores.

---

## Sources

Read 2026-09-11.

- [JoyCaption — project repository](https://github.com/fpgaminer/joycaption) — Apache-2.0, the eleven
  caption modes including four booru variants, base model, stated failure rates
- [llama-joycaption-beta-one-hf-llava — model card](https://huggingface.co/fancyfeast/llama-joycaption-beta-one-hf-llava)
  — 8B, SigLIP2, bf16 footprint, photoreal/anime coverage claim
- [JoyCaption GGUF with the vision projector](https://huggingface.co/concedo/llama-joycaption-beta-one-hf-llava-mmproj-gguf)
  — **the one to use**; Q4_K 4.92 GB and an 0.88 GB `mmproj`
- [mradermacher](https://huggingface.co/mradermacher/llama-joycaption-beta-one-hf-llava-GGUF) and
  [Mungert](https://huggingface.co/Mungert/llama-joycaption-beta-one-hf-llava-GGUF) quantisations — the
  Q4_K and Q8_0 sizes and the ~17 GB bf16 figure came from here. **Neither ships an `mmproj`**; recorded
  so nobody downloads one expecting vision
- [Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) ·
  [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) ·
  [Qwen3-VL repository](https://github.com/qwenlm/qwen3-vl) — Apache-2.0, sizes, footprints
- [Molmo — Ai2](https://allenai.org/blog/molmo) and
  [Molmo/PixMo paper](https://arxiv.org/html/2409.17146v2) — open weights, data and code
- [Best open-weight VLMs 2026](https://presenc.ai/research/best-open-weight-vision-language-models-2026)
  and [BentoML open-source VLM guide](https://www.bentoml.com/blog/multimodal-ai-a-guide-to-open-source-vision-language-models)
  — the Qwen / InternVL / Molmo standing as of 2026. **Secondary, and treated as such.**
- [Fine-grained image task benchmark](https://arxiv.org/html/2504.14988v2) — the InternVL3 50.1% /
  Qwen2.5-VL 45.1% attribute figures
- [OpenRouter model pricing](https://openrouter.ai/models) — flash-class vision pricing
- [Danbooru autotagger](https://github.com/danbooru/autotagger) ·
  [DeepDanbooru](https://github.com/kichangkim/deepdanbooru) — checked for a photograph-trained tagger;
  both are anime-trained, which is the absence recorded in §3
