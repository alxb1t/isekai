# Design — 0010 Illustrious base

**Verdict: `feasible-with-caveats`.** The mechanical work is small and local: one manifest entry,
five graph edits, one new pure function in the injector. The caveats are all of the same kind and
they are the reason this version exists at the point in the arc it does — **nothing here can be
measured.** No primary source states that any ControlNet in this stack works on an Illustrious base;
the dials do not transfer; and the register change is a judgement about output. Each is named below
with the phase that settles it and the form its answer is allowed to take. This is the **last**
version permitted to settle anything by eye.

## Context

v0.9 left a volume whose entire contents were placed by the script, a manifest with a derivation
helper, and a graph untouched since v0.8 — see `proposal.md - Why`. Four facts from that inheritance
shape what follows.

**The graph is the source of truth and `pipeline_ui.json` is stale.** It already lags the API graph
and this change makes it lag further. It is reference only and is not regenerated.

**The graph↔manifest binding runs one way.** Every model file the graph names must be declared;
the reverse is not asserted. So an extra manifest entry is legal, which is what lets Animagine stay
declared through the probe (D3).

**`mirror_entries_without_an_alternate` will demand alternates for WAI automatically.** It treats
any Hugging Face org absent from the manifest's `publishers` list as a mirror, and WAI has no
first-party HF repo at all, so the check does the right thing without being taught about Civitai.

**`:latest` is v0.9's image and can provision.** v0.9's own record says it was untouched, but that
was written mid-phase, before the merge: the push to `main` rebuilt it, and the run succeeded. What
this version still needs is the *branch's* image, because the pod provisions from the manifest baked
into whatever it boots, and the WAI entry lands here (D8).

## Goals / Non-Goals

**Goals:**

- Move the one path onto WAI v17 and demonstrate that it runs, at stated input resolutions.
- Make the register the publisher's rather than the previous base's, and close v0.8's `1girl`
  defect using a mechanism the graph already contains.
- Remove the one component with a written publisher disclaimer against this use case — or, if a
  falsifiable comparison says it contributes, keep it and record why.
- Leave every by-eye judgement labelled as a preference, so the evaluator version has a baseline to
  measure against rather than a claim to inherit.

**Non-Goals:**

- **No evaluator, and no quality claim of any kind.** Not that identity survives the swap, not that
  the dials chosen are good, not that the register improves anything.
- **No new identity mechanism.** Swapping the face adapter, adding a tagger, or making the prompt a
  function of the input are all deferred to the version that can measure them.
- **No second path.** WAI replaces Animagine; it does not join it. The overlap in D3 is a phase of
  this version, not a supported configuration.
- **No `Dockerfile` change.** `ImageScale` and `CLIPSetLastLayer` are core ComfyUI.

## Decisions

### D1 — The bytes come from a mirror; the trust comes from the digest

WAI is published on Civitai and has no first-party Hugging Face repo. The manifest pulls the file
from a pinned Hugging Face mirror revision and verifies it against **the SHA-256 Civitai itself
publishes** for the model version. That is what makes the mirror a CDN rather than a trust root: the
digest is the acceptance test, so any host serving matching bytes is equally acceptable and one
serving anything else is rejected whoever it is.

Several byte-identical mirrors exist and are declared as alternates, which v0.9's fallback walking
already knows how to use. **Availability is the real risk here, not integrity** — a single
third-party repo can disappear, and it is the alternates rather than the pin that answer that.

Two traps to avoid writing into the manifest as if they were evidence. **The file size proves
nothing**: every published WAI version reports the identical byte count, so only the digest
discriminates. And the digest Civitai publishes is computed by the platform after upload — it is a
strong, independent cross-check of the mirror, but it is not a signature by the model's author, and
the record should say so rather than implying more.

*Alternative considered:* declaring Civitai's own download as an alternate. It needs no API key, so
it would work — but `provision.py`'s pinned-source check accepts **only** a Hugging Face
`resolve/<40-hex>/` URL, and widening that regex for one entry would weaken the check that no source
resolves a mutable ref, to buy availability that six byte-identical Hugging Face mirrors already
supply. Civitai stays what it is here: the **publisher of the digest**, not a declared source.

### D2 — Injection computes the working resolution, because no node can

The rule is: preserve aspect, put the short side at the working scale, round both dimensions to a
multiple of 64. Core ComfyUI offers `ImageScale`, which needs an explicit width *and* height and
derives nothing, and `ImageScaleToTotalPixels`, which preserves aspect but targets a pixel *count*.
The second is the tempting one and it is wrong for this rule: at a fixed megapixel budget the short
side moves with the aspect ratio, so a 16:9 photo lands below the floor MistoLine's card requires
while a 4:3 photo clears it — a failure that varies by input and reports nothing.

So injection reads the photo's dimensions and writes width and height into an `ImageScale` node.
This sits naturally where it lands: injection's job is already to wire the photo into the graph, and
this is the same act with one derived value attached. Reading dimensions means parsing JPEG and PNG
headers directly, because **the runtime is stdlib-only** — roughly forty lines, a pure function over
bytes, and fully testable offline against tiny fixtures. An unreadable or truncated header is an
error, never a default: a silently wrong resolution is a wrong render rather than a failure.

`inject` therefore needs the photo's local path, which `pipeline.run` already holds as `input_path`
and can pass. It stays an argument rather than becoming state.

### D3 — Animagine stays declared until the swap is proven, then leaves in its own phase

The probe needs both checkpoints on the volume at once: WAI is added while the old stack is intact,
so a comparison is possible at all and so a failure has something to fall back to. The one-way
graph↔manifest binding makes an extra entry legal.

Removing Animagine in the same phase that adds WAI would leave the probe depending on a file the
manifest no longer declares — and a re-provision at any point in that window would delete the
comparison base and the rollback together, silently, because the script provisions exactly what the
manifest says and nothing else. v0.9 demonstrated that property deliberately; here it would bite.

Animagine's entry leaves in the final phase, after the swap is proven, as a reviewable act. Keeping
it permanently is the option this repo's "one path" rule forbids: a declared checkpoint nothing
renders with is a second path in everything but name.

### D4 — The register is the publisher's, on both prompts

WAI's model page states its own ladder and, in the same breath, warns that too many quality tags and
over-long negative prompts *reduce* image quality. The repo currently carries seven tags before an
Animagine-specific ladder and an eighteen-token negative that still contains that base's
`low score, bad score`. Adopting the publisher's positive while keeping the long negative would take
half the guidance and ignore the half that is stated as a warning.

So both prompts move: the positive to the content tags plus WAI's ladder **appended last**, which is
where every published sample puts it, and the negative to the publisher's own short form. Both stay
pinned by equality, so this is a deliberate test edit — the property v0.8 established.

**One consequence deserves to be written down rather than absorbed:** dropping `realistic,
photorealistic` from the negative removes a push *away* from the photograph, on a product whose
whole subject is a photograph. It is a deliberate consequence of taking the publisher's negative,
and if renders come back more photographic than v0.8's, that is the first place to look.

### D5 — `1girl` goes, and gender comes from the embedding already in the graph

v0.8 recorded `1girl` as a defect and named a later version as its owner. It is closed here, and the
argument is what makes it closeable without breaking two settled rules.

`1girl, solo` is a Danbooru mode selector, not subject text — but only `solo` is doing the
mode-selection work; `1girl` additionally asserts a gender. InstantID's paper documents the ID
embedding as carrying gender among its semantics, so with the tag gone that axis is supplied by a
mechanism **already in the graph** rather than by a tagger that does not exist. No new identity
mechanism is added, and the prompt stays a committed literal rather than becoming a function of the
input — so neither the evaluator-first rule nor the committed-prompt rule is touched.

This gets one of the few genuinely falsifiable acceptance criteria in the version: **a male input
photo produces a male-presenting output.** That is a judgement a person makes reliably, unlike
identity fidelity, and it can fail.

*Risk, stated rather than hidden:* on a Danbooru-trained base an under-specified register may
under-stylise. The mitigation is that the register is not empty — the content tags and the ladder
remain — and that the direction of travel matches the publisher's own advice to use fewer tags.

### D6 — Clip skip is committed, because the publisher's samples all use it

Every one of WAI v17's published sample images carries `clipSkip: 2`, and none of its prose mentions
it. Shipping without it ships a configuration the publisher never tested, in a way that is invisible
by inspection — the graph looks complete either way. So a `CLIPSetLastLayer` is committed and its
value pinned, exactly as the prompt is: configuration, not a dial, and changing it is a deliberate
test edit.

*Alternative considered:* an A/B during the probe. Rejected as the primary route — it spends metered
time to second-guess the publisher's own generation configuration, and it would be settled by eye,
which is the currency this version is trying to spend as little of as possible.

### D7 — Tile is dropped, unless a falsifiable comparison says otherwise

TTPlanet Tile's model card says its training set is realistic and that "no comic, animation
application are promised", and recommends strength 0.9 against the 0.2 this graph runs. It is the
only component in the stack with a written publisher disclaimer against the direction this version
moves in.

Dropping it on that alone would still be a judgement. So the probe runs a **strength-to-zero
comparison at a fixed seed** for each ControlNet: tuned value versus 0.0. That is mechanical and
falsifiable — it asks whether the conditioning reaches the sampler at all, not whether the result is
prettier — and it costs two renders per ControlNet. A component that is indistinguishable from
absent is deleted with evidence; one that is distinguishable is kept, and the disclaimer is recorded
against it.

*Alternative considered:* replacing it with a domain-matched tile (`Eugeoter/noob-sdxl-controlnet-tile`
is NoobAI-native and effectively first-party). Rejected for this version: both candidates ship **zero
documentation**, so their strengths would have to be found by eye — a second unbudgeted by-eye
tuning session, to install a component we have no evidence is needed. That is the evaluator
version's work.

### D8 — A release candidate for the metered phases; `:latest` is not this version's to publish

The pod provisions from the manifest baked into the image it boots, and the WAI entry lands on this
branch — so a pod running `:latest` would provision v0.9's manifest and never fetch the checkpoint
the graph now names. A `:v0.10-rc` build is therefore published before the first pod, and both
metered phases set `RUNPOD_IMAGE` to it explicitly, which also makes each pod's image a recorded
fact rather than an assumption. It is cleared after the last metered phase, because a stale value
silently pins every later pod to an unreleased image.

`:latest` is deliberately **not** touched. This repository's CI publishes it from a push to `main`
and from nowhere else — the workflow's `workflow_dispatch` requires a tag and names it "never
`latest`" — precisely so a pre-release build cannot clobber the image a rollback reaches for. The
tag therefore becomes v0.10's on merge, by the mechanism that already exists, with no phase of this
change involved.

### D9 — Every by-eye result is recorded as a preference, never as a measurement

Two of this version's outcomes are judgements: the `denoise` / `ip_weight` values, and the
gender check. They are recorded in the change directory as the chosen run's `run.json` plus a short
note of what was compared — the images themselves stay in gitignored `outputs/`, since the manifest
plus the seeds reproduce them and this repository claims reproducibility over the submitted workflow
JSON, never over pixels.

The distinction the `CHANGELOG.md` must carry: **chosen** is not **best**, and **runs** is not
**good**. What the version establishes is that the path runs on WAI at stated input resolutions,
that each retained ControlNet demonstrably affects the render, and that a male photo yields a
male-presenting output. What it establishes about identity, fidelity or quality is nothing.

## Risks / Trade-offs

- **No primary source says any ControlNet in this stack works on an Illustrious base.** Searches of
  the model cards, GitHub issues and HF return nothing either way → D7's strength-to-zero comparison
  is the only falsifiable instrument available, and it detects the failure that matters (a component
  contributing nothing) without requiring taste.
- **No documented anime-native OpenPose exists at all.** Every Illustrious/NoobAI OpenPose repo
  found ships weights with no README → xinsir stays, on no evidence either way, with
  `scale_stick_for_xinsr_cn` still enabled since its card names the thick-line training mismatch
  that setting exists for.
- **The mirror could disappear mid-version** → alternates are declared and v0.9 already walks them;
  six byte-identical Hugging Face mirrors are available to declare.
- **Dropping `realistic, photorealistic` may pull renders toward the photograph** (D4) → recorded
  in the findings note as the first thing to check if outputs look more photographic.
- **An under-specified register may under-stylise** (D5) → the ladder and content tags remain, and
  the direction matches the publisher's stated advice; if it does under-stylise, that is a recorded
  finding for the evaluator version, not a reason to reinstate a gender tag.
- **The dials are found by eye, and this is the last time** → every value lands in the graph, and
  the run that produced it is recorded, so the evaluator version inherits a reproducible baseline
  rather than a claim.
- **The probe is metered and has a lot to do** — ControlNet comparisons, two dials, the gender check
  → the comparisons are fixed-seed and mechanical, and the ceiling is 45 minutes; exceeding it is a
  halt, and an unfinished dial search is a second session, not a rushed judgement.

## Migration Plan

1. Non-metered: manifest entry, graph edits, injector work, tests, gate green, `:v0.10-rc` published.
2. **⚠️ Probe** — `RUNPOD_IMAGE` set, WAI provisioned alongside Animagine, ControlNet comparisons,
   dials, gender check. Verdicts recorded.
3. Apply the verdicts to the graph: chosen dials, tile kept or dropped.
4. **⚠️ Final renders** — the path on WAI, at stated input resolutions.
5. Animagine's manifest entry is removed, in its own phase.

**Rollback.** Until step 5, Animagine is declared and on the volume, so reverting is a `ckpt_name`
edit and a re-provision. A technical failure — the checkpoint will not load, or no ControlNet loads
— **defers the version rather than half-shipping it**: the branch is not merged, so `:latest`
remains v0.9's image and the released path is untouched.

## Open Questions

- **Whether tile survives** — D7 makes this a phase-2 result rather than a decision, and either
  outcome is a one-line manifest and graph edit in phase 3. It changes no requirement.
- **The working scale's exact value.** The rule is fixed (short side, aspect preserved, multiple of
  64); the number is a constant the probe may adjust once, if renders at the chosen value are
  visibly off the base's trained scale. It changes no scenario, which is why the spec names "the
  working scale" rather than a literal.
