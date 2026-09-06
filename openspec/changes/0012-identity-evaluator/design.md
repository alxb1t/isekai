# Design — `0012-identity-evaluator`

**Verdict: `feasible-with-caveats`.**

The caveats are named and none of them is a blocker: the instrument may turn out not to work, the labels
depend on an operator doing 40 blind judgements honestly, and the baseline's pixels cannot be committed. Each
is written into a decision below with what this change does about it. The one thing this design refuses is
the shape the plan arrived in — a scorer that grades — because that shape cannot be built.

## Context

See `proposal.md` — Why. What shapes the approach, all of it verified in the tree while this change was cut:

- **There is no fixed-dial render path.** `isekai/pipeline.py` calls `mutate` unconditionally per variation,
  and `isekai/mutate.py` moves `denoise`, `cfg`, `ip_weight` and all three `ControlNetApplyAdvanced`
  strengths. Nothing this repository has rendered differs from its neighbour in one dial.
- **`run.json` records `seed`, `variations`, `seeds`, `overrides`.** It cannot name the photograph, the
  graph, the base or the resolution. The renders in `outputs/final/` from 2026-09-05 are two subjects at
  1024×1600 and 1024×1472 whose inputs are identifiable only from `CHANGELOG.md` prose.
- **Every pixel consumer reads `["22", 0]`** — `ApplyInstantIDAdvanced`, `VAEEncode`, `TilePreprocessor`,
  `DWPreprocessor`, `LineArtPreprocessor` — and only `ImageScale` reads `LoadImage`. The scaled photo and the
  render are therefore the same canvas exactly. This is the load-bearing assumption of the whole design and
  it holds.
- **`LoadImage` transposes EXIF Orientation for both JPEG and PNG**, measured on the pinned build
  (`probe/README.md`). `image_dimensions` returns dimensions, not pixels, so the scorer must transpose itself.
- **`cn_strength: 0.5`** sits in `workflows/pipeline.json` and is referenced nowhere else in the tree.
- **The identity signal is `glintr100`** — insightface `antelopev2`, via `cubiq/ComfyUI_InstantID`
  (`Dockerfile:39`, `Dockerfile:45`). It is ArcFace-family.
- **The runtime is stdlib-only** and `convert.py` carries `dependencies = []`.

## Goals / Non-Goals

**Goals:**

- Make a fixed-dial render possible, and make a run identify itself.
- Produce four numbers per render on a canvas the photograph and the render provably share.
- **Measure the instrument against the operator's eye**, and report that measurement whatever it says.

**Non-Goals:**

- Grading. No verdict, no threshold, no percentage — see D1.
- Answering "which dial should move". That is what the instrument is *for*, and it is v0.13.
- Measuring rebuild drift, cross-base transfer, or anything about clothes.

## Decisions

### D1 — The evaluator ranks and diffs. It does not grade, and it never will.

Every metric compares a photograph to a drawing. There is no zero point across that gap, so a cosine of 0.62
is not 62% of anything; it is 0.62, comparable only to another 0.62 from the same base and the same batch.
The operator asked for a percentage. **A fidelity percentage is not available and this design says so
rather than shipping a rescaled number that would be read as one.**

Three axes are exempt because they mean the same thing in both domains: colour distance, region area, and
keypoint agreement. The face axis is exempt only if its calibration survives D9.

*Alternatives:* a within-batch percentile displayed 0–100 — rejected, it is meaningless across batches and
will be misread as fidelity by the person who wrote it, six months later. Provisional thresholds labelled
provisional — rejected, a provisional number that survives one version becomes real by squatter's rights.

### D2 — No verdict this version, and the rollup is earned next version from this version's labels.

A per-axis threshold requires labels; this change is what produces the first labels. "Worst axis, named"
is a rollup wearing a threshold's clothes if the thresholds were invented. The report is a table of raw
values and the human reads it — 30 renders × 4 axes is a table one person scans.

### D3 — Mutation becomes suppressible; it does not stop being the default.

`pipeline.run` gains a way to skip the mutator, and the CLI a flag that is off by default. A fixed-dial run
still draws a fresh sampler seed per variation, so the renders differ in exactly one thing. This is a change
to an existing path, which the plan claimed it would avoid; the claim was wrong, because the baseline the
plan wanted could not otherwise be rendered.

*Alternative:* treat the baseline as a distribution and characterise the jitter with many more renders —
rejected on cost, and it answers a different question.

### D4 — `run.json` becomes a provenance record; the scorer does not keep a parallel one.

It gains: the input photograph's SHA-256, the submitted graph's SHA-256, the base checkpoint, the resolved
working resolution, the resolved per-variation dials, and whether dials were jittered or held. A digest of a
face is not a face, so D14's rule (derived faces are not committed) is untouched.

*Alternative:* the scorer records provenance in its own file — rejected. A scorer-side record cannot
retroactively identify renders already on disk, and provenance belongs beside the pixels it describes.

### D5 — Four axes, not six. Clothes and DINOv3 are deferred.

Face (StyleID, plus ArcFace under D8), pose (PCK, normalised by the person bbox diagonal, low-confidence
keypoints dropped and counted), hair colour (CIEDE2000 dominant distance plus mask-area ratio), and the
guard. Clothes is dropped because the labels are **holistic identity** judgements and cannot validate a
garment metric — implementing an axis no label can check is spending calibration attention on nothing.
Deferring DINOv3 defers its licence question with it.

Known limitation, stated because it will bite: multi-tone hair (a dark base with a coloured underlayer) is
the norm in this aesthetic, and a dominant-colour metric returning one mode will score a render that dropped
the underlayer as unchanged. The subject set includes two such subjects specifically so the metric can be
caught doing it (D11).

### D6 — `cn_strength` is made searchable, and deliberately not searched.

It joins `apply_overrides` and the CLI, and it is pinned by a test the way `ip_weight` is. Searching it
inside this change would validate the instrument and search the dial with the same renders, and neither
result would be clean. The changelog will state plainly: 0.5 is unsearched.

### D7 — Regions come from the photograph only, and the canvas comes from the injector.

`segformer_b2_clothes` parses the transposed photograph at the injector's own working resolution; those pixel
regions are applied to the render unchanged. The scorer calls `working_resolution` and `image_dimensions`
rather than restating the rule, and refuses when a render's dimensions disagree with what it derived.

**The per-class accuracy filter the plan proposed is dropped.** It would have silently discarded classes
based on a model card's numbers from someone else's photographic test set. It is replaced by a **per-mask
area floor** measured on this photograph: a region below the floor refuses and names itself. That is a
measurement here rather than an inherited claim elsewhere.

### D8 — ArcFace is a sanity channel, not a second opinion, and the report says so.

`glintr100` is the encoder the generator injects identity *with*. A high ArcFace cosine on the output is
evidence that the adapter did the thing it optimises, measured by the loss it optimises against — it asserts
nothing about identity. A **low** ArcFace on a run that should have preserved identity is a real finding. So
ArcFace may only falsify, and that asymmetry is printed next to the number.

StyleID is contaminated differently — its training pairs were stylized with InstantID and IP-Adapter — which
is why it is the primary and not the ground truth. It is the thing being calibrated, not the thing
calibrating.

*Alternatives:* report only the disagreement between the two encoders — rejected, it throws away ArcFace's
real falsifying power. Find a third uncontaminated encoder — that is a research project, not a version.

### D9 — The guard is measured two ways, and if neither holds the refusal is the finding.

The probe computes **both** box IoU (anime-face detector on the render against the photograph's face box)
**and** landmark-centroid alignment, on the same renders, at no extra cost. Whichever holds at the working
denoise is what ships as the guard.

**Pre-committed, before any pod is created:** if neither holds, the region axes refuse, and "the instrument
cannot locate the face in our own outputs" is what v0.12 ships as its result. Moving `denoise` to make the
meter work is explicitly disqualified — the product is not tuned to flatter the instrument.

### D10 — The labels are pairwise, within-subject, holistic, and blind; git is what proves blind.

40 judgements across 4 subjects, 10 pairs each. Pairwise because "is A or B more like them?" is stable where
a 1–5 rating drifts across a sitting. Within-subject because "does subject 1's render preserve identity more
than subject 4's" is a question with no meaning. Holistic because the operator's felt sense of identity is
holistic, and forcing it through a face crop measures something they do not care about.

The consequence is accepted rather than hidden: **a single holistic label cannot attribute a disagreement to
one axis.** If face and hair correlate differently against the same label, that difference is itself a finding.

The sheet is committed in its own commit before any score is computed. The correlation refuses labels it
cannot show were prior.

### D11 — Six subjects rendered, four labelled; each subject earns its slot adversarially.

Six subjects × five seeds = 30 renders, fixed dials, on `:v0.11-rc`. Chosen to break metrics, not to cover
humanity: two with multi-tone or non-uniform hair (against D5's known limitation), one with a non-frontal or
occluded face (exercises the guard's refusal path and the absent-face field), one landscape input (closes a
gap `CHANGELOG.md` v0.11 names explicitly — landscape is still untested on a GPU), two controls.

The two refusal-path subjects need no labels, so 40 judgements covers the four that do.

### D12 — The scorer is a second entry point, and CI never installs its stack.

`evaluate.py` beside `convert.py`, no shared import graph, dependencies behind an optional `isekai[eval]`
extra. The one-path rule is about there being one way to *render*; an evaluator is not a second way to render.
A subcommand would put the extra one misplaced import away from breaking `dependencies = []`.

**CI does not install the extra.** The eval tests skip there and run on the operator's machine — the same
posture this repository already takes toward diffusion quality, which is verified by eye on a pod and never
in CI. The gate array stays five commands. What *is* enforced in CI is one test that imports `convert.py`
without site-packages, so an accidental third-party import in the runtime's graph fails loudly. The
mechanism (`-S`, or an AST walk against `sys.stdlib_module_names`) is decided in the phase that writes it;
`-S` inside a uv venv is unverified.

### D13 — The scorer is proven on the renders already on disk, before any money is spent.

The ten renders in `outputs/final/` are the wrong dials and the wrong subjects, but they are 1024-canvas
PNGs from this exact pipeline and they will surface every plumbing failure for free. The pod session is
therefore the **last** metered thing that happens, not the fourth.

### D14 — The baseline is pinned to `:v0.11-rc`; rebuild drift is recorded, not measured.

The image's Python dependency closure re-resolves at build time, so two builds of an identical `Dockerfile`
differ, and nobody has measured how much a rebuild alone moves a score. This change holds that variable
constant by reusing the already-built image rather than measuring it. `run.json` will *record* the image and
the ComfyUI commit, which is what makes the measurement possible later; recording drift is not measuring it,
and the changelog will say so.

### D15 — The subject photographs get `probe/build_inputs.py`'s treatment.

Tracked builder script, digests recorded, pixels not committed. This is already this repository's answer to
"reproducible inputs that are derived faces", and one version does not silently reverse a convention the
previous one wrote down. Residual risk accepted and stated: if the source photographs are lost, the baseline
becomes unreproducible and the labels are the only surviving artifact.

### D16 — Licences are read and recorded before code, and no ambiguous model is the sole carrier of an axis.

StyleID's project page and its model card disagree (CC BY-SA 4.0 versus non-commercial research). That
conflict is not ours to resolve, so it is carried as a **recorded deviation**, in the manner of the tile
ControlNet's animation disclaimer — with the hard rule that a model under a contradictory licence may not be
the only thing carrying an axis. StyleID therefore ships beside ArcFace or not at all.

### D17 — The release criterion is that the correlation was computed, never that it was good.

Written into `tasks.md` before the labelling happens. If the numbers do not track the operator's eye, that is
a successful version: it will have prevented tuning a pipeline against noise, for ~$0.23.

## Risks / Trade-offs

- **Every axis is noise at n=40** → the most likely single outcome, and it is a reportable result under D17,
  not a failure. The count of judgements is printed beside every correlation so the reader can discount it.
- **StyleID is contaminated by this exact generator family** → D8 makes it the calibratee rather than the
  calibrator; the operator's eye is the reference, and that is the whole point of D10.
- **The guard fails at denoise 0.65 and most of the report refuses** → pre-committed in D9. The alternative
  fallback (whole-image comparison plus a judge) needs a judge, which is a later version.
- **The operator peeks at scores before labelling** → git ordering is the only defence, and it is a real one;
  the correlation refuses labels it cannot show were prior.
- **The dominant-colour hair metric silently passes a dropped underlayer** → D5 states the limitation and
  D11 puts two subjects in the batch that can catch it. It is not fixed this version.
- **A cross-base comparison is attempted** → refused per axis with the reason in the record, not warned.
  A warning above a table of numbers is read as decoration.
- **The scorer needs something the renders do not carry, discovered after the pod is gone** → D13 orders the
  work so the scorer runs against real pixels before any money is spent. Residual risk: the disk renders are
  the wrong subjects, so a subject-specific gap could still survive to the session.
- **The `[eval]` stack is multi-gigabyte** → D12 keeps it out of CI entirely; the cost falls on the operator's
  machine once.
- **`-S` may not work inside a uv venv** → D12 names two fallbacks and defers the choice to the phase that
  writes the test, which is the only place it can be verified.

## Migration Plan

Nothing to migrate. No model artifact moves, so `scripts/models.json` is unchanged, no image is rebuilt and
no volume is re-provisioned. The mutation default is unchanged, so an existing invocation of `convert.py`
behaves exactly as it did. `run.json` gains keys and drops none, so an old manifest stays readable and a
scorer handed one reports the missing provenance rather than guessing at it.
