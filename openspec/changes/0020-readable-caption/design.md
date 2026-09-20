# 0020 · readable caption — design

**Verdict: `feasible`.** No caveat is carried into the build as an assumption, because **both
build-time discoveries were run at the grilling rather than deferred to phase 1.** JoyCaption's booru
mode was measured on three real photographs across four prompt variants; the sentence-placement
mechanism was re-measured on three real captions and their real sheets. Both results are below, and
both changed the version.

**This design was settled by grilling against bodies.** Roughly forty assertions about `main` were
checked and **fourteen did not survive**, including the call site the largest simplification was argued
from. Where a decision overturns the brief that preceded it, it says so and what the evidence was.

**Two decisions were added during the build and are marked as such — D24 and D25.** Both are
corrections to this document rather than decisions taken inside it: the cut omitted a
`model-provisioning` spec delta that D18 requires, and phase 3 was bitten by a latent defect in
`scripts/manifest.py` that D18's own second entry makes materially worse. Neither re-opens a settled
decision; D24 is what makes D18 buildable and D25 is what makes it safe.

See `proposal.md` — Why, for motivation. See `specs/` for the requirements.

---

## Context

```
  dependencies = []                    pyproject.toml:5, held by a test importing the package
                                       with site-packages off sys.path under `python -S`
  ▶ every non-stdlib import in a runtime path is FUNCTION-LOCAL or it is not there

  caption()          caption.py:231    guard at :252-254, one production call site
  Reader             caption.py:102    one method, read(photo, briefing, workspace) -> Reading
  READER_OPTIONS     caption.py:79     temperature 0, seed 1, num_predict 1024. NO repeat_penalty
  SORTER_OPTIONS     sheet.py:153      the same plus num_predict 2048, repeat_penalty 1.15
  instructions_record  claude_cli.py:259   takes a Path and hashes the FILE
  BUDGETS            run.py:128        four entries; `BUDGETS[stage]` at run.py:499 is bare
  CAPTIONS/SHEETS/…  run.py:106-111    the layout names, one constant each
  STAGES             run_view.py:40    (CAPTIONS, SHEETS, REVIEW, PROMPTS) — an explicit tuple
  run_view.py:66     `if producer.get("pinned") is False: parts.append("unpinned")`
  VERBS              cli.py:61         SEVEN verbs, not six
  reader_for/sorter_for  wiring.py:152,157   registries keyed on hosted.implementation
  paragraphsOf()     ui/src/caption.ts:7     the caption's text rule, already browser-side
```

**Three facts from that list shape almost everything below.** `BUDGETS[stage]` is a **bare dict
lookup**, so a stage name without an entry is an uncaught `KeyError` escaping both `across()` and
`main()`'s `except Refusal` — the one unhandled exception path in a package where every failure is a
named `Refusal` (D6). `instructions_record()` **takes a `Path`** and hashes the file behind it, so a
prompt held as a module constant cannot use it (D16). And `pinned` is **write-only-`false` on every
artifact in the tree**, so `run_view.py:66` prints *"unpinned"* over all of them (D17).

## Goals / Non-Goals

**Goals:**

- The operator reads a caption one sentence to a block and stops losing his place.
- He sees, beside the prose, **every tag two taggers offer** — unfiltered, marked for what he can
  actually commit, scored where a score exists.
- `caption()` is **byte-identical in the diff** and its whole test surface stands.
- Every phase is free. No pod, no metered call, and the acceptance requires no render.

**Non-Goals:**

- **Labelling sentences with identity criteria.** Measured and refused — D2.
- **Any narrowing of either tag list.** Filtering is stage ②'s job and seeing behind it is the point.
- **Any new visual language.** No component, colour, spacing or type step outside what v0.18 shipped.
- **A design pass.** v0.18 had an eleven-frame handoff before its grilling; this has none and needs
  none, which is a decision here rather than an omission to discover at build time — D21.

---

## Decisions

### D1 · ③ ships **two** tag sources, and the second one is why ③ ships at all

**This overturns the brief's S1, S2, S9, S10 and S11, on a measurement.**

JoyCaption's booru mode was run on three real photographs across four prompt variants:

| prompt | tags | in the pinned vocabulary |
|---|---|---|
| `"Write a list of Booru tags for this image."` raw | 34–40 | 11–23% |
| the same, in llama-3 chat framing | 38–42 | 14–15% |
| **`"Write a long list of Booru tags for this image."` raw** | 45–51 | **36 / 145 = 24%** |
| the same, framed | 48–54 | 41 / 155 = 26% |

The out-of-vocabulary remainder is stock-photo keywording — `attractive`, `sexy`, `natural beauty`,
`fashion photography`, `everyday life`, `high resolution` — and it **contradicts its own prose on the
same photograph**: `blue eyes` against a caption reading *light brown eyes* and a sheet reading
`brown eyes`; `tan skin` against *light brown skin*; `full body` against *the lower half of her body is
out of shot*. The brief's own gate — *"if the output is poor, ③ is worthless"* — fired.

**`models/wd14/model.onnx` is what makes ③ survive.** It is a SwinV2 vision transformer already on
disk, 467 MB, and `selected_tags.csv` beside it is **its output layer** — the same file every flow pins
as its vocabulary, one CSV row per output neuron. Measured on the same three photographs:

```
  general tags    @0.50  @0.35  @0.25  @0.15      character tags: none on any photo
  photo 1            17     21     24     33      rating tags: 4 total, always fire
  photo 2            16     20     25     30      cost: 0.89 s to open, 0.44 s a photo
  photo 3            23     28     31     36
```

It recovers `1girl`, `solo` and `looking at viewer` on all three — **the three tags correction-mining
measured the operator adding 5 of 5 times and which stage ② has never produced** — and
`navel piercing 0.90` on a photograph whose `marks` field the sorter left empty.

**Both ship.** The operator asked for the raw JoyCaption list knowing it is wrong, because the panel is
advisory and a wrong tag costs a glance. WD14 ships because it is the only one of the two that delivers
what ③ was for.

### D2 · ④ is sentence splitting, and it labels nothing

**This overturns the brief's whole §④ and the roadmap's own description of the version.** The
mechanism — *place ②'s sheet tags onto sentences by word overlap* — was re-measured against three real
captions and their real sheets rather than the six synthetic sentences it was designed on:

| | synthetic | **real** |
|---|---|---|
| tags placed | 15 / 18 (83%) | **24 / 43 (56%)** |
| false placements | **zero** | **≥ 5** |
| sentences correctly labelled | 6 / 6 | **~12 of 32, 15 unlabelled** |

The false placements are systematic, not noise: one-word tags match any sentence containing that word.
`skin_ancestry: light` lands on *"light brown areolas"* and *"light brown eyes"*; `eyebrows: dark`
lands on *"dark brown hair"* and *"dark brown eyes"*. And the misses are structural rather than
fixable: `count: 1girl`/`solo` miss 6 of 6, `framing: upper body` misses 3 of 3 against prose reading
*"the lower half of her body is out of shot"*, `gaze: looking at viewer` misses against *"looking
directly at the camera"*, and `hair_silhouette: wavy hair` misses against *"loosely waved"*. **No
amount of punctuation-stripping reaches any of them.**

**A label reading *this sentence is about skin* over a sentence about a halter top is the anchoring
failure ③ exists to defuse, aimed at the caption.** So the labels go to v0.21, with the two
`vocabulary.py` gaps they would need. What ships is the half that was never in doubt: one sentence per
block, which the standing note says *"solves the lost-my-place problem on its own, before any tag is
shown."*

### D3 · Two functions and two seams — **not** one `Tagger` Protocol with two implementations

A Protocol earns its name when the thing behind it is interchangeable. These are not. `caption_tags()`
reaches a model over HTTP to Ollama and exists only where the manifest has a `hosted` block;
`caption_wd14()` opens a file on disk and resolves through **nothing at all**. The registry that would
key the Protocol is keyed on `hosted.implementation` (`wiring.py:152,157`), a string WD14 does not
have. A Protocol whose two implementations resolve through different mechanisms is a shared name, not a
seam, and this repository's rule is that a parameter is a seam only when something is actually passed
through it.

**Consequence, stated plainly: `summon-v1` and `conjure-v1` get a WD14 panel and no booru panel.**
That overturns the brief's S1, which reasoned that ③ was open-arm-only. It is open-arm-only for
**one** of its two halves.

### D4 · Two directories, two budgets, two idempotence checks

`tags/` and `wd14/` are siblings of `captions/` under the flow. Each gets its own `latest()` check and
its own `BUDGETS` entry, which is what makes every partial case resumable rather than stuck: WD14 is
deterministic and free, JoyCaption is over HTTP with a retry budget, and coupling their idempotence
would spend a model call to retry a matrix multiply. *prose is already complete · wd14 is already
complete · tags wrote 001.json* is a legible line.

### D5 · `caption()` is not modified, and this is the largest simplification available

**The brief argued this from a call site that does not exist.** S7 quoted
`_say(wired, run, "caption", written)`; the real code inlines the call and never binds its result
(`cli.py:369-380`), and `written` is a **parameter name** of `_say` (`cli.py:503`). The conclusion
survives the correction, and a second one strengthens it: there are **49** `caption(` call sites, 48 of
them tests, and 45 reach the stage through `tests/stages.py:27`'s wrapper — so widening the signature
would have cost four sites, not forty-nine. The reason not to widen is therefore not cost. It is that
`caption()` is the one function in this change whose behaviour must be provably unchanged, and a
function with no edit is provably unchanged by `git diff`.

### D6 · `BUDGETS` gains two entries, and without them the stage **crashes**

`budget = BUDGETS[stage]` (`run.py:499`) is a bare dict lookup. An unknown stage name is a `KeyError`,
and `across()` (`run.py:509-522`) catches only `Refusal`, as does `main()` — so it escapes as a raw
traceback and a nonzero exit, in a package where every other failure is a named `Refusal` naming its
remedy. **Rejected alternative:** passing `"caption"` as the budget key for both taggers. It works, and
it makes the refusal say *caption failed permanently* about the `wd14` directory. Two lines beat a
misleading message twice over.

### D7 · The order is prose → WD14 → JoyCaption, and the ordering **is** the failure isolation

`across()` catches `Refusal` **per input**, not per stage: `work(identifier)` does the whole
per-photograph job, so the first refusal aborts the rest of that photograph's work. Three `_say` calls
in an arbitrary order would let a flaky HTTP call to Ollama stop WD14 from ever running on a photograph
whose tags take 1.4 seconds and cannot fail transiently.

So the order is an argument, not a habit. **Prose first** — it is the only one of the three anything
downstream reads. **WD14 second** — deterministic and local, it fails only if a file is missing or
corrupt, which is one operator fix and worth stopping on. **JoyCaption last** — it is the one with a
retry budget, a port, a timeout and a truncation mode, and placing it last means its refusal blocks
nothing that would have succeeded. **Rejected:** a per-stage `try` in the caption branch. It buys
independence the ordering already delivers, for eight lines of control flow.

### D8 · One verb. `isekai caption` runs all three and says three times

**The brief argued this from *"six verbs, no orchestrator"*; there are seven** (`cli.py:61-69`). The
argument survives and gets a better body: `batch.py`'s `_prepare` refuses an input with no sheet and
names the remedy, so the operator reaches the review surface having already run `caption` and `sheet`.
A second verb he did not run produces a pane that is silently empty — and D20 settles that a missing
tag artifact is silent, never a refusal, which makes a forgotten verb **indistinguishable** from a flow
that cannot have one. Add the verb the day something other than `caption` calls tagging.

### D9 · `boundary/wd14.py` holds the session; `pipeline/tagging.py` holds the stage

The arrangement this repository already made for the other tagger: `boundary/ollama.py` holds `HOST`,
the POST and the failure classification and says in its own docstring that it contains no adapter,
while the adapter sits in `pipeline/`. WD14's boundary is the heavier of the two — a 467 MB session to
open, a pad-and-resize rule, and a **10,861-row label index whose ordering is load-bearing** — and none
of that is pipeline logic. It also puts the entire non-stdlib import behind one module, which is what
has to stay true for the `-S` guard.

### D10 · `sentencesOf()` lives in `ui/src/caption.ts`, and this dissolves the brief's S14 rather than answering it

S14 reasoned about where a *placement algorithm* should live. D2 cut the placement. What remains is a
regex over a string that exactly one surface renders, and `ui/src/caption.ts` already exists for
precisely this: it holds `paragraphsOf()` because *"two components render it… a paragraph rule that
lived in both could only drift"*. A Python module would send prose to the server to be split and back.

**The cost is named rather than discovered: `sentencesOf()` is browser code, so the mechanical half of
its acceptance cannot be a pytest.** See D22.

### D11 · The prompt is `"Write a long list of Booru tags for this image.\n"`, unframed

*"Long"* is the lever: it takes 34–40 tags to 45–51 and in-vocabulary yield from 11–23% to 24%. The
llama-3 chat framing adds five tags across three photographs and is **refused**: the Modelfile pins
`TEMPLATE {{ .Prompt }}`, the shipped prose briefing goes through it unframed, and hand-building chat
markup as a module constant would make two calls to the same model use different framing and would
double-apply the day that TEMPLATE gains one.

### D12 · `TAGGER_OPTIONS` carries `repeat_penalty: 1.15` and `num_predict: 1024`

**Half of the brief's S2 is overturned by the measurement.** S2 argued `num_predict: 1024` is sized for
prose and that the tag list, coming last, is what `done_reason: length` would remove. Eight runs, every
one `done_reason: stop`, the longest 200 tokens. The budget is not the constraint and the change says
so rather than inheriting an argument the body refuses.

`repeat_penalty: 1.15` is **kept**, and not on that argument. It is kept on the sorter's precedent
(`sheet.py:153-158`): at temperature 0 there is no sampling noise to break a loop, one field came back
`"white robe"` forty times, and **a comma-separated list is that loop with more surface**. Eight runs
is not evidence of absence.

### D13 · WD14 shows everything above a 0.15 floor, sorted by confidence, with the number on the chip

At 0.35 the panel loses `blurry background 0.19`, `cowboy shot 0.20` and `head tilt 0.28` — three tags
correction-mining measured the operator adding by hand on 3, 2 and 2 of 5 inputs, which is exactly the
recall ③ exists to buy. The band also adds `black hair 0.31` on a brown-haired subject, and that is the
point of printing the number: `black hair 0.31` sitting below `brown hair 0.91` on a sorted list is
self-refuting. **Rejected: a manifest key or a flag.** Add the key the day a flow wants a different
floor, with a reason.

### D14 · `tagger_for(flow)` is resolved in `wiring`, per flow, and the session opens on first use

`Wiring.reader` and `Wiring.sorter` are `Callable[[Flow], …]` resolved **inside** `cli.py`'s flow loop
precisely so nothing is constructed until a flow asks. A 467 MB session must obey the same rule, or a
machine that never captions opens the file anyway. **Rejected: a module-level lazy session** — that is
mutable state at module scope in a package whose `__init__.py` files hold a docstring and no code by
rule. **Rejected: open per photograph** — 0.89 s × N for nothing.

### D15 · A response containing no comma is a **permanent** failure; everything else is stored raw

The operator asked for the raw list knowing it is wrong, and *wrong* is not the failure being guarded
here. If the model answers in prose, splitting on commas yields one element no `TagChip` can render —
the failure the brief's S11 named as *"detectable, and should be."* One test separates *wrong* from
*not a list at all*, and it touches no content. Anything richer starts filtering, which is what ③ exists
not to do. `ollama.ask()` already classifies a truncated response as permanent; this is the same shape
in the same place.

### D16 · `constant_record(text)` beside `instructions_record(path)` — because the helper the brief named cannot be used

**S9 said the digest would be recorded *"exactly as `instructions_record()` does"*. It cannot be.**
`instructions_record(path: Path)` (`claude_cli.py:259-272`) resolves a path, relativises it against the
repository root and hashes the file behind it. A module constant has no path and no file. And
`run-directory:provenance:producer-records-the-briefing` requires *"that text's path **and** digest"*,
so the spec has to move with the code: it gains *"and its path where it has one."*

**Rejected: a sixth file in the flow directory.** That is the trade v0.19 already priced and refused to
house `joycaption.Modelfile`, which went to `scripts/` instead. The tag list shapes the operator's
reading and not the render, so it makes no per-flow claim.

### D17 · WD14's producer carries `pinned: true` and **both** digests, and it is the first one that can

`run-directory:provenance:unpinned-producer-is-declared` covers *"a hosted service that exposes no
immutable revision"*. WD14 is not that — it is a local file with a digest. Every artifact in the tree
today records `pinned: false` and `run_view.py:66` prints *"unpinned"* over all of them; a WD14
artifact will be the first thing `show` reports as pinned. **Take that consequence deliberately**: it is
the field finally doing its job, not a surprise for the build to find.

### D18 · `model.onnx` is pinned in `scripts/vocabulary.json`, beside the CSV

**The CSV and the model are one artifact split in two.** Row N of `selected_tags.csv` names output
neuron N of the ONNX graph; a mismatched pair mislabels every tag silently, and nothing downstream
could notice. Pinning one and leaving the other unrecorded is the defect, and `vocabulary.json` —
publisher SmilingWolf, revision `627aef95…` — is where the other half already lives. `sha256`
`e6774bff34d43bd49f75a47db4ef217dce701c9847b546523eb85ff6dbba1db1`, 467,460,978 bytes.
`derive_vocabulary.py` must stay byte-identical on re-run, and `lfs=True` — the default — is correct
for it: `digest_of()` routes an LFS object through `published_digest()`, which reads the object id from
Hugging Face's API, so pinning a 467 MB file costs no download.

**`derive_vocabulary.py`'s own docstring argues the opposite, and it must be rewritten in the same
phase.** It reads, verbatim: *"One entry, and deliberately one. `selected_tags.csv` is published
alongside a tagger model, and **the tagger is not here: this repository does not run it**… a manifest
that carried both would make swapping the vocabulary a decision about a model nobody loads."* **That
premise is exactly what this version falsifies.** The argument was correct when written and is false
the moment `boundary/wd14.py` exists, and leaving it in place would put a tracked file in direct
contradiction with this design — which is a halt condition, not a stale comment. The replacement states
the new reason: the two files are **one artifact split in two**, row N of the CSV naming neuron N, so a
manifest carrying one without the other is a manifest that cannot detect the mismatch that matters.

### D19 · A `tagging` extra, and **no new third-party code enters the tree**

`onnxruntime`, `numpy` and `Pillow` already resolve through the `eval` extra, which also carries
`torch>=2.6` and `transformers>=4.49` — roughly 2 GB this tagger never imports. A narrow extra is the
`ui` extra's own precedent. **`dependencies = []` and the `-S` guard are untouched**, the import is
function-local in `boundary/wd14.py`, and `uv sync --locked` — gate command one — stays green because
the pins already exist in the lockfile.

### D20 · A missing tag artifact is silent: no panel, no message, never a refusal

Three ways it is legitimately absent — a run captioned before v0.20, a flow with no `hosted` block, a
failed tagger call — and none of them may block review. The tag lists are an aid, and a surface that
refuses to open because a helper is missing has confused an aid for an input; `ui`'s startup refusals
exist for what review genuinely cannot proceed without. **No message either**: a line explaining an
absence the operator caused is chrome on the busiest pane in the surface.

### D21 · No design pass. Both panels compose components v0.18 shipped

`TagChip` takes `{tag, readonly?, selected?}`; `CaptionPanel` takes `{prose, loading?}`; `SourcePanel`
already owns the column. ③ is two chip lists, ④ is the same type scale with a different block boundary.
**The constraint is the settlement: no component, colour, spacing or type step outside the shipped
system** — and a feature that cannot be built under it is a feature that needs a design pass, which
would be a finding rather than a failure. Both lists are **always visible and read-only**; nothing in
either can commit a tag, and the picker at stage ② stays the only path into a field.

**What it costs, said plainly: v0.18's acceptance was a screenshot match against eleven frames and
v0.20's cannot be.** Its acceptance is the operator's judgement on a real batch — which is what it
already was, so nothing is lost that this version had.

### D22 · The gate gains `npm run typecheck`, and its limit is written down rather than implied

**The Vue frontend has zero automated tests** — no vitest, no playwright, no `@vue/test-utils` — and
`vue-tsc --noEmit` exists in `ui/package.json` and is in no gate command. So a browser phase can end
"green" today while the bundle does not compile. `npm run typecheck` is one line in `Makefile` and one
in `.minions/minions.toml`, it is the only mechanical check this version's largest deliverable can buy,
and it is added **in phase 1** so every later browser phase runs under it.

**And the limit is stated in `tasks.md` rather than left to inference: the phase producing
`sentencesOf()` ends on a gate that cannot execute it.** Rejected: adding vitest for one sixteen-line
file — a test runner and a sixth gate command, in a version whose stated constraint is to add nothing
outside the existing system.

### D23 · `run_view.STAGES` gains two names, because v0.20 **creates** the gap

`STAGES: tuple[str, ...] = (CAPTIONS, SHEETS, REVIEW, PROMPTS)` (`run_view.py:40`) is explicit, so a new
directory is silently invisible to `show`. The repository's rule is not to go into files a version never
touches, and by that rule this is out of scope. **The rule does not apply**: v0.20 is not inheriting
this defect, it is creating it, and shipping a stage `show` cannot see is shipping a verb that lies
about what a run holds. The same shape as v0.18 taking `security/S1` because its own extraction made
the guard load-bearing.

### D24 · The `model-provisioning` delta the cut omitted, and why the omission was invisible

**Added during the build, at phase 3, and it is a correction to this document rather than a decision
taken inside it.** D18 pins `wd14/model.onnx` in `scripts/vocabulary.json`. The living spec forbade
exactly that, in a scenario the cut never read:

```
  openspec/specs/model-provisioning/spec.md
  Scenario: the tagger model is not in the vocabulary manifest
    Key:  model-provisioning:vocabulary:tagger-model-is-not-included
    THEN  it declares the tag list and not the model published alongside it
    AND   the two are treated as different artifacts with different consumers
```

Two tests are bound to that key and three more encode the same premise. So the phase could not go
green without either a delta or a deleted test, and a deleted test bound to a live scenario is a plan
problem rather than a coding shortcut — which is why the build halted here instead of working around
it.

**Why the cut missed it.** The grilling checked roughly forty assertions about `main` and fourteen
failed, but every one of them was about a **body** — a call site, a signature, a constant. This is a
claim in the **living spec** with no body of its own: nothing in `derive_vocabulary.py` says *the model
is excluded*, it simply has one `Spec`. The forbidding sentence lives only in prose and in two test
names. **The lesson is specific rather than general: a version that pins, unpins or re-scopes a
manifest entry must read `model-provisioning`'s spec before it is cut**, because that capability is
almost entirely assertions about what is *absent*, and absence has no body to grill.

**The shape of the delta, and the one thing it is not.** openspec refuses to retire a single scenario
through a `MODIFIED` block — a modified requirement replaces the whole block and the validator checks
that none of the current scenarios went missing. So the vocabulary requirement is `REMOVED` whole and a
successor `ADDED`: **The tag vocabulary and the model it indexes are provisioned from one manifest**.
Four scenarios cross **under their existing keys**, two of them reworded for a manifest with more than
one entry. The fifth is **inverted rather than dropped**, which is the substance of the change:

```
  before   tagger-model-is-not-included              the model must NOT be here
  after    label-index-and-model-share-a-revision    both are here, at ONE revision
```

That is a strictly stronger claim than the one it replaces. The old scenario permitted a `model.onnx`
provisioned anywhere by any route at any revision, and forbade only the manifest that could check it;
the new one makes the revision itself the contract. The two tests bound to the retired key are
rebound to the new one rather than deleted.

**What was genuinely right about the old scenario, and stays said.** While no build loaded the model,
the vocabulary really did outlive any particular tagger, and pinning one would have made swapping the
tag list a decision about a model nobody opened. The successor requirement records that as a condition
rather than deleting it — the claim is scoped to *where a build loads the model that tag list is the
output layer of*, so the retired argument is preserved as the case the new rule does not cover.

### D25 · `blob_digest` must demand the identity coding, and this was found by being bitten

**A defect in `scripts/manifest.py`, inherited rather than created, folded into v0.20 on the
operator's call.** `digest_of_url()` sends `User-Agent` and nothing else. **A request that states no
`Accept-Encoding` accepts every coding** — RFC 7231 §5.3.4 — so Hugging Face is free to answer one
fetch compressed and the next one not, and `urllib` neither negotiates nor decompresses. Observed, on
the CSV this change re-derives, during phase 3:

```
  one fetch      e6125b7c…  143049 bytes      the gzip stream, hashed in place of the file
  every other    298633d9…  308468 bytes      the artifact, and what the tracked manifest says
```

**It is worth breaking the "do not open a file this version never touches" rule for, and the reason is
this version specifically.** The wrong digest is well-formed: it is a real SHA-256, it is written to a
tracked manifest by the deriver whose whole contract is to be byte-identical, and the gate never
re-derives so nothing goes red. Before v0.20 the consequence was a provisioning refusal on a 300 KB
file. **After v0.20 the consumer is `boundary/wd14.py`**, which verifies both digests before its first
inference — so a manifest poisoned by one unlucky fetch refuses the *correct* 467 MB model and names a
fetch command that will re-download it and fail again. This version is what turns a stale pin into a
loop.

The fix is one header, `Accept-Encoding: identity`, on the one request the module makes. It is the only
change to `manifest.py`, **and no other manifest is re-derived in this version** — `models.json` and
`eval_models.json` are left exactly as they are, because re-deriving them is a different change with a
different diff to review.

---

## Risks / Trade-offs

| | |
|---|---|
| **JoyCaption's list is 76% unusable, permanently** | Accepted, deliberately, by the operator: the panel is advisory and a wrong tag costs a glance. The vocabulary marking is what makes the unusable ones obvious at a glance rather than at a commit |
| **WD14 is a third model's opinion, not "what the reader saw"** | ③'s original framing was *the same reading, unfiltered*. This is a different and stronger claim — *the tagger the vocabulary came from, unfiltered* — and the change says so rather than pretending otherwise |
| **The 0.15 floor puts wrong tags on screen** | Deliberate. The confidence is printed beside every one, sorted descending, so a wrong tag arrives pre-refuted by the tag above it |
| **Sentence splitting on `.` is naive** | A known edge, not an unknown one. The prose is constrained by briefing to plain description of a person; the acceptance names it as a thing to look for |
| **A 467 MB gitignored file the gate never sees** | The whole reason for the `Session` Protocol and the two-digest verification. The suite runs against a fake and asserts the label-index ordering, which is the one silent failure mode |

## Migration Plan

**None, and it was checked rather than assumed.** `run_view` names its stages through an explicit tuple
(`run_view.py:40`), and every stage reader names its subdirectory through `run.directory(flow, CONSTANT)`.
Three places do iterate a directory — `Run.flows` at `run.py:225`, `rendered()` at `run_view.py:128`
and `rendered_seeds` at `generate.py:230` — **and this corrects the brief's S13, which asserted nothing
does.** None of them is reached by the new directories: the first lists the run directory one level
*above* the flow to discover flow names, and the other two list `outputs/`. An old run simply lacks
`tags/` and `wd14/`, which is the same state as a run whose caption has not been produced.

## Open Questions

**None.** Four were open at the grilling — the spec delta's shape, the phase order, where placement
lives, and every claim the brief made about `main`. The first is settled at `specs/`, the second at
`tasks.md`, the third is dissolved by D2 and D10, and the fourth produced fourteen corrections, each
recorded at the decision it touches.

**Deferred with triggers, so nothing is silently assumed:**

- **The sentence labels**, plus `normalise()`'s punctuation gap and `CURATED`'s contiguous-span limit
  → **v0.21**, which opens `vocabulary.py` for its own content work. D2 records why they are not enough
  on their own.
- **`1girl` · `solo` · `upper body` have no lexical route to any sentence** → whoever builds ⑤. Word
  overlap cannot reach them at any quality, so this needs a different mechanism rather than a better
  threshold.
- **`--new-version` across three artifacts** → out of scope, declared. The two new functions take the
  flag by pass-through and it is not designed around.
- **`flow.py` has no type guard on `hosted`** — a non-object block raises a bare `TypeError` at
  `flow.py:372` or `:427`, and `hosted: "ollama"` raises a `Refusal` that misdescribes the fault as
  three missing keys → **v0.19 review/R3**. v0.20 never opens that file.
- **The llama-3 chat framing** (+5 tags across three photographs) → refused at D11; revisit only if the
  Modelfile gains a `TEMPLATE`.
