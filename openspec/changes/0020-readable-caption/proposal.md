---
version: v0.20
---

## Why

**The operator loses his place in a paragraph, and he cannot see what the reader saw before the sorter
narrowed it.** Both are observations from a day of using the v0.18 surface, and both are answered by
changing what the source pane shows while a tag is being decided — not by changing the sheet, the
sorter or the render.

**Two build-time discoveries were run before this change was cut, and both moved it.**

**① JoyCaption's booru mode is not a Danbooru tagger.** The mode string was never in this repository —
it lived in the prototype's gitignored `router.py` — so it was recovered and measured: three real
photographs, four prompt variants, including the llama-3 chat framing the Modelfile's
`TEMPLATE {{ .Prompt }}` deliberately omits. **9–26% of what comes back is in the pinned vocabulary.**
The rest is stock-photo keywording — `attractive`, `natural beauty`, `fashion photography`,
`high resolution` — including judgements the prose briefing forbids in as many words. Worse, **it
contradicts its own prose on the same photograph**: `blue eyes` where the caption says *light brown
eyes* and the approved sheet says `brown eyes`; `tan skin` where the caption says *light brown skin*.
Chat framing moves 11% to 26% and does not change the kind of thing it is.

**② The tagger that does work was already on disk, and nothing read it.** `models/wd14/model.onnx` is
a SwinV2 vision transformer — 467 MB, gitignored, pinned in no manifest — and `selected_tags.csv`
beside it is **its output layer**, the same file every flow pins as its vocabulary. Row N of the CSV
names neuron N. So its tags are in-vocabulary **by construction** rather than by luck: 20–36 general
tags per photograph at a 0.15 floor, every one committable, every one scored. It recovers `1girl`,
`solo` and `looking at viewer` on all three photographs — the three tags correction-mining measured
the operator adding by hand **5 of 5 times** and which stage ② has never once produced — and it found
`navel piercing 0.90` on a photograph whose `marks` field the sorter left empty. It costs 0.89 s to
open and 0.44 s a photograph.

**③ The sentence labels were measured only on synthetic data, and real data refused them.** The 15/18
placement and 6/6 labelling came from six sentences and a sheet an assistant wrote. Re-run over three
**real** captions and their real sheets: **24 of 43 tags placed, with false placements the synthetic
run did not have** — `skin_ancestry: light` landing on *"light brown areolas"*, `eyebrows: dark`
landing on *"dark brown hair"* — and **15 of 32 sentences carrying no label at all**, including every
sentence about expression, gaze, framing and pose. `1girl`, `solo` and `upper body` have no lexical
route to any sentence at any quality. A label reading *this sentence is about skin* over a sentence
about a halter top is the anchoring failure the panel was designed to defuse, pointed at the caption.

**So the version splits the caption into sentences and shows two tag lists beside it, and it does not
label anything.** Splitting solves the lost-my-place problem on its own, before a tag is shown.

## What Changes

- **`isekai/pipeline/tagging.py`** — `caption_tags()` and `caption_wd14()`, **two functions and two
  seams, deliberately not one Protocol with two implementations**: one resolves through the manifest's
  `hosted.implementation` and one resolves through nothing at all, so a shared name would be a shared
  name and not a seam. Plus `FakeTagger`, and `constant_record()`.
- **`isekai/boundary/wd14.py`** — the ONNX session, the pad-and-resize rule, the label index, the
  two-digest verification, and an injectable `Session` Protocol so the suite never opens a 467 MB
  file. The arrangement `boundary/ollama.py` already has: the transport here, the adapter in
  `pipeline/`.
- **`caption()` is byte-identical in the diff.** Nothing is widened, no signature moves, and its whole
  test surface stands. Two functions sit beside it and the CLI's `caption` branch says three times —
  *prose is already complete · wd14 wrote 001.json · tags wrote 001.json*.
- **`tags/` and `wd14/`** — two sibling directories under the flow, **two `BUDGETS` entries, two
  `latest()` checks, two independent idempotence rules.** A failed hosted tagger and a complete local
  one is an ordinary, resumable state.
- **Ordering is the failure isolation.** prose → WD14 → JoyCaption, three plain `_say` calls. `across()`
  catches `Refusal` per input, not per stage, so the only stage that fails transiently runs last and
  its refusal blocks nothing that would have succeeded.
- **`scripts/vocabulary.json` gains `wd14/model.onnx`** — same publisher, same revision, re-derived by
  the existing `derive_vocabulary.py` under its byte-identical rule. **The CSV and the model are one
  artifact split in two**: a mismatched pair mislabels every tag and nothing would notice.
- **`pyproject.toml` gains a `tagging` extra** — `onnxruntime`, `numpy`, `Pillow`. **No new
  third-party code enters the tree**; all three already resolve through `eval`, whose `torch` and
  `transformers` this tagger never imports. `dependencies = []` and the `-S` guard are untouched, and
  the gate stays offline because every test runs against the fake session.
- **`run_view.STAGES` gains two names.** v0.20 *creates* the gap rather than inheriting it, and
  shipping a stage `show` cannot see is shipping a verb that lies about what a run holds.
- **`pinned: true` becomes reachable.** Every artifact in the tree today records `pinned: false` and
  `run_view.py:66` prints *"unpinned"* over all of them. A WD14 artifact is the first producer that can
  honestly claim a pin, and it carries both digests to back it.
- **The review surface** — `read_input`'s payload widens to carry both lists, **marked server-side**;
  `sentencesOf()` joins `paragraphsOf()` in `ui/src/caption.ts`; two read-only chip lists stack under
  the prose, always visible. **No component, colour, spacing or type step outside the shipped system.**
- **`npm run typecheck` enters the gate** — the only mechanical check this version's largest
  deliverable can buy, and it is added **first** so every later browser phase runs under it.
- **BREAKING — none.** Every verb, flag, artifact shape, manifest and committed digest is unchanged.
  All three flow directories are byte-identical and no flow is re-pinned.
- **Deliberately not in this version**, each with its trigger: the sentence labels and the two
  `vocabulary.py` gaps they need (**v0.21**) · `--new-version`'s meaning across three artifacts
  (inherited by pass-through, not designed) · the llama-3 chat framing (+5 tags across three
  photographs, refused) · `flow.py`'s missing type guard on `hosted` (**v0.19 review/R3** — v0.20 never
  opens that file) · ⑤, the per-sentence candidate list, which is blocked on v0.21's content.

## Capabilities

### New Capabilities

- **`tagging`** — the eleventh. Producing a list of Danbooru tags for a photograph, from a model that
  is given the photograph and nothing else, stored raw and unnarrowed, with the producer naming what
  made it. **It is not `caption`**: `caption`'s purpose is prose and three of its seven requirements
  are about absence, decline and prose-unreadability, none of which reach a tag list — and the local
  tagger takes no briefing, records no briefing digest and cannot decline.

### Modified Capabilities

- `caption`: one requirement scoped. *"SHALL NOT accept tags from it"* and *"no structured field or tag
  list is stored alongside it"* are narrowed to the **caption artifact**, so a sibling `tags/`
  directory is not a rule broken quietly. **The anti-invention rationale is left exactly as it is** —
  the 0.518 → 0.307 measurement is about pressing a *reader* into a field list, and nothing here
  disturbs it.
- `cli`: the per-flow resolution requirement names two seams and the code now has four. Widened to
  every per-flow seam, with the local tagger named as one that resolves without a manifest key at all.
- `run-directory`: the layout scenario enumerates *captions, sheets, reviews, prompts and outputs* and
  gains two names; the provenance scenario requires *"that text's path and digest"* and gains *"and its
  path where it has one"*, because a module constant has no path and `instructions_record()` takes one.
- `ui`: the source pane gains its first requirement — what it shows, that all of it is read-only, and
  that an absent tag artifact is silent rather than a refusal.

## Impact

| | |
|---|---|
| **`isekai/boundary/wd14.py`** | new — `Session`, the pad-and-resize, the label index, both digests. The `onnxruntime`/`numpy`/`Pillow` import is **function-local** |
| **`isekai/pipeline/tagging.py`** | new — two functions, `FakeTagger`, `constant_record()` |
| **`isekai/pipeline/caption.py`** | **untouched.** `caption()`, `Reader`, `Reading`, `READER_OPTIONS` and all three adapters are byte-identical |
| **`isekai/foundation/run.py`** | `+ TAGS`, `+ WD14` layout names; `BUDGETS` gains two entries. Without them `BUDGETS[stage]` is a bare `KeyError` escaping both `across()` and `main()` |
| **`isekai/interface/wiring.py`** | `+ tagger_for(flow)`, resolved per flow, constructing nothing until a flow asks |
| **`isekai/interface/cli.py`** | the `caption` branch says three times, in one fixed order |
| **`isekai/interface/run_view.py`** | `STAGES` gains two names |
| **`isekai/interface/ui/`** | `batch.py` resolves both tag artifacts; `app.py` marks server-side and widens `read_input` |
| **`ui/src/`** | `caption.ts` gains `sentencesOf()`; `SourcePanel.vue` gains two `TagChip` lists. **No new component** |
| **`scripts/vocabulary.json`** | `+ wd14/model.onnx`, `sha256 e6774bff…`, re-derived byte-identical |
| **`pyproject.toml`** | `+ [tagging] extra`. **`dependencies = []` unchanged**, lockfile re-run and committed |
| **`Makefile` · `.minions/minions.toml`** | `+ npm run typecheck`, added in phase 1 |
| **not touched** | `generate.py`, `review.py`, `sheet.py`, `claude_cli.py`, `ollama.py`, `shared/*`, `flow.py`, all three flow directories and their committed digests — **to be verified by `git grep`, not assumed** |
| **money** | **zero, every phase.** WD14 is a local ONNX pass; JoyCaption and Qwen are on localhost; no pod, and the acceptance does not require a render |
