# Tasks — 0012-identity-evaluator

## Progress

- [x] 1 — The licences, read and recorded; every eval artifact pinned — **before any code**
- [x] 2 — A render with the graph's own dials, and `cn_strength` made settable and pinned
- [x] 3 — `run.json` becomes a provenance record
- [ ] 4 — `evaluate.py`, the `[eval]` extra, and the stdlib guard on `convert.py`
- [ ] 5 — Prove the scorer on the renders already on disk, before any money is spent
- [ ] 6 — 🛑 **HUMAN** — the six subjects: a tracked builder, digests recorded, pixels not committed
- [ ] 7 — ⚠️ **GPU · HALT** — one session on `:v0.11-rc`, thirty fixed-dial renders
- [ ] 8 — The three probes, local and free; the guard is decided here
- [ ] 9 — 🛑 **HUMAN** — the pairwise sheet, and forty blind judgements committed alone
- [ ] 10 — The correlation, reported whatever it says

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic.** Phases 1–6 and 8–10 have it. Red → green.
2. **Run each phase's stated verification — run it, never summarize it.** Paste real output.
3. **Gate green before the commit** — `make gate`, the five commands in `.minions/minions.toml`'s
   `gate` array, in order. **Never weaken the gate to pass**; halt and say so.
4. **Append that phase's entry under `## [Unreleased]` in `CHANGELOG.md`**, using
   `### Added` / `### Changed` / `### Fixed` / `### Notes`.
5. **Check the box** in `## Progress` above, in that phase's own commit. The first unchecked entry is
   the current phase.
6. **One commit per phase**, staged **by name**, carrying the trailer `Change: 0012-identity-evaluator`
   **contiguous** with `Co-Authored-By:` — no blank line between them.

**No render change.** `workflows/pipeline.json` is edited in no phase except to be *pinned* — no dial
moves, not the register, not a ControlNet strength, not `cn_strength` (design.md D6). A version that
built an instrument and moved the thing it measures would have measured nothing.

**No image build and no volume re-provision.** `scripts/models.json` and `Dockerfile` are untouched;
phase 7 boots the already-built `:v0.11-rc` (design.md D14).

**One phase spends real money.** Phase 7. A pod goes up only for a phase marked ⚠️ GPU here,
`infra/up.sh` creates it, `infra/down.sh` tears it down, and teardown is confirmed through the RunPod
MCP with what it returned recorded. The ceiling is **45 minutes and ~$0.30 per pod session**;
exceeding it is a halt, not a judgement call. At $0.72/hr the money ceiling binds at **25 minutes**,
so plan against 25 and treat 45 as the halt. Budget: ~4 min boot + 30 renders at ~30 s ≈ **19 min ≈
$0.23**, derived from v0.11's measured 10 renders in an 8 min 23 s session.

**Phase 7 must set `RUNPOD_IMAGE`** to `:v0.11-rc` in `.env`, and clear it afterwards.

**The release criterion is that the correlation was computed, not that it was good** (design.md D17).
If the numbers do not track the operator's eye, phase 10 records that and the version ships. Re-running
the labelling after seeing scores is forbidden.

**Three phases are the operator's, not the agent's.** Phase 6 needs six source photographs, phase 7
needs the announcement and the "go", and phase 9 is forty blind judgements. A build loop **halts** at
each and says what it is waiting for; none of the three may be simulated, sampled or stood in for.

## Phase detail

### 1 — The licences, read and recorded; every eval artifact pinned — **before any code**

The one phase that can kill a model before a line is written against it (design.md D16, D18). No
scorer code is written here.

**Transcribe the licence findings** into a tracked note beside the manifest, with each URL and the date it
was read. **They were read on 2026-09-06 and are recorded in design.md D16** — this phase transcribes them
into the repository, closes the one entry left open, and verifies the constraint they imply. It does not
re-litigate them.

- **The conflict this change was cut believing in does not exist.** StyleID's CC BY-SA 4.0 is on **the
  website**; the repository and the model card agree — non-commercial research use, plus *"Do not use
  FFHQ-derived data for biometric human recognition"*, which governs the dataset rather than the encoder.
  Record both, and record that the second clause does not bind this use.
- **Four artifacts are non-commercial research**: StyleID, `segformer_b2_clothes` (NVIDIA Source Code
  License, inherited from SegFormer), and `glintr100`/antelopev2 (InsightFace's library is MIT; its
  **weights are not** — a restriction this project has been shipping since v0.9). Each is a **recorded
  deviation**, in the manner of the tile ControlNet's animation disclaimer. Record also that all four bite
  at once, retroactively, if this project ever becomes commercial.
- **`yolov8_animeface` is AGPL-3.0** and is a different problem — see phase 4 and design.md D19. Record the
  finding and the constraint here; the test that enforces it lives with the code.
- **DWPose is the one entry still open.** Resolve its licence and record it. If it forbids the use, halt and
  say so: D9 already measures the guard two ways, and the pose axis would report its own absence rather than
  a zero.
- The rule that survives: **a model whose licence is restrictive may not be the sole carrier of an axis.**
  StyleID ships beside ArcFace or not at all.

**Pin every eval artifact** in `scripts/eval_models.json` — a **sibling** of `scripts/models.json`,
never merged into it: that file is the pinned manifest of what **the graph** needs on the pod, and
these run locally on the operator's machine. Same shape, same rules — a pinned revision URL, a
SHA-256, a byte count, and mirrors where they exist.

- **`glintr100` and DWPose reuse the pins `scripts/models.json` already carries**, byte for byte. The
  scorer's ArcFace must be the *same* artifact the generator injects identity with, or design.md D8's
  claim about self-grading is about two different models and is simply wrong.
- **StyleID, `segformer_b2_clothes` and `yolov8_animeface` are new pins**, resolved to a commit or
  revision and checksummed. A branch name is not a pin.
- The scorer verifies each artifact's digest when it loads it and **refuses on a mismatch**, which is
  what makes the pin a check rather than a note.

**Verify:** every licence recorded with its URL and read-date, including StyleID's website-versus-model-card
distinction quoted from both sources and DWPose's now resolved; `scripts/eval_models.json` present, every entry carrying a pinned URL and a
SHA-256, and the DWPose and `glintr100` entries **byte-identical** to `scripts/models.json`'s; a test
bound to `evaluation:pinned-artifacts:digest-mismatch-is-refused` and
`:recognizer-matches-the-generators-pin`; `make gate` green. **Halt and say so** if any licence
forbids the use — that is a plan decision, not a coding one.

### 2 — A render with the graph's own dials, and `cn_strength` made settable and pinned

Today `isekai/pipeline.py` calls `mutate` on every variation and `isekai/mutate.py` moves six dials at
once, so nothing this repository has rendered differs from its neighbour in one thing. A baseline is
impossible until this changes (design.md D3).

- **`pipeline.run` gains a way to hold the dials.** Off by default, so every existing invocation
  behaves exactly as it did. A held run still draws its own sampler seed per variation, so the renders
  differ in exactly one thing.
- **The CLI gains the flag**, defaulting to off.
- **`apply_overrides` gains `cn_strength`**, set on `ApplyInstantIDAdvanced` — never on a
  `ControlNetApplyAdvanced` node, which is a different dial with the same word in its name.
- **The CLI gains `--cn-strength`**, range-checked at parse time in zero-to-one like its neighbours.
- **`cn_strength` is pinned** beside `PROBE_DENOISE` and `PROBE_IP_WEIGHT` in
  `tests/test_workflow_injection.py`, so a silent re-tune becomes a test edit. It is **not searched**
  (design.md D6).

**Verify:** `make gate` green; new tests bound to
`workflow-mutation:variations:fixed-dials-are-the-graphs-own`,
`:fixed-dials-still-vary-the-seed`, `:fixed-dials-reproduce-from-the-seed`,
`workflow-mutation:overrides:sets-cn-strength`,
`workflow-mutation:pinned-dials:cn-strength-is-pinned`,
`cli:fixed-dials:jitter-is-the-default`, `:flag-reaches-the-run`,
`cli:dial-defaults:cn-strength-defaults-to-unset`,
`cli:dial-validation:accepts-cn-strength-in-range`, `:rejects-cn-strength-above-one`,
`:rejects-cn-strength-below-zero`. Every existing mutation and CLI test passes unchanged.

### 3 — `run.json` becomes a provenance record

It records `seed`, `variations`, `seeds` and `overrides`, and therefore cannot name the photograph, the
graph, the base or the resolution — the two batches in `outputs/final/` are identifiable only from
`CHANGELOG.md` prose. A baseline nothing can identify is not a baseline (design.md D4).

Add: the input photograph's SHA-256, the submitted graph's SHA-256, the base checkpoint named in the
graph, the resolved working resolution, the resolved per-variation dial values, and whether dials were
jittered or held. Keys are added and none removed, so an old manifest stays readable.

**A digest of a face is not a face** — D14's rule that derived faces are not committed is untouched,
and a digest in a tracked artifact is what makes an uncommitted input checkable rather than trusted,
exactly as `probe/README.md` already does.

**Verify:** `make gate` green; new tests bound to
`workflow-mutation:output-layout:manifest-identifies-the-photo`,
`:manifest-identifies-the-graph-and-base`, `:manifest-records-resolved-dials`,
`:manifest-records-the-resolution`, and `cli:fixed-dials:mode-is-recorded`.

### 4 — `evaluate.py`, the `[eval]` extra, and the stdlib guard on `convert.py`

A second entry point beside `convert.py`, never on its import graph (design.md D12).

- **Canvas.** Call `image_dimensions` and `working_resolution` from `isekai/workflow.py` — the scorer
  states no resolution rule of its own. Transpose the photograph's *pixels* before parsing: the header
  parser returns dimensions, and `LoadImage` transposes both codecs (`probe/README.md`). Refuse when a
  render's dimensions disagree with what was derived.
- **Regions** from the photograph only, at the working resolution, with a per-mask **area floor** that
  refuses and names itself. **No per-class accuracy filter** (design.md D7).
- **Four axes** (design.md D5): face — StyleID, plus ArcFace tagged as a falsify-only sanity channel
  (design.md D8); pose — PCK normalised by the person bbox diagonal, low-confidence keypoints dropped
  and counted; hair — CIEDE2000 dominant-colour distance and mask-area ratio; and the guard.
- **The guard implements both methods** — box IoU and landmark-centroid alignment. Which one is
  authoritative is decided in phase 8, not here (design.md D9).
- **The anime-face detector is loaded through `onnxruntime`. The `ultralytics` package is never
  imported and never enters the `[eval]` extra** (design.md D19). `yolov8_animeface` is **AGPL-3.0**,
  this repository is public and Apache-2.0, and importing `ultralytics` would combine the two and force
  the whole work to AGPL. Every other model here is safe because no weights are distributed; this one
  is not, because code is. `onnxruntime` is MIT and is already in the image. A test asserts the absence
  — `spec_exempt`, structural — because a licence review nobody runs is not a control.
- **Absence is its own field.** `face_detected: false` is never a low score.
- **Cross-base** refuses the embedding axes per axis, with the reason in the record, and still reports
  colour, area and PCK.
- **Report:** one JSON per render, one table per run, every column's direction stated, the run named.
  **No average, no verdict, no percentage** (design.md D1, D2).
- **Packaging:** an optional `isekai[eval]` extra; `convert.py` keeps `dependencies = []`. **CI does
  not install the extra** — eval tests skip there. The gate array stays five commands.
- **One test imports `convert.py` without site-packages** so an accidental third-party import in the
  runtime's graph fails loudly. Mechanism decided here — `-S` in a uv venv is unverified; fall back to
  an AST walk against `sys.stdlib_module_names` if it does not hold. **Report which one was used and
  why.**

**Verify:** `make gate` green with the extra absent; `uv run --extra eval pytest` green with it
present; `ultralytics` absent from `pyproject.toml` and from the scorer's import graph, asserted by a
test; tests bound to every `evaluation:` scenario except the `pinned-artifacts:` ones (phase 1) and the
`labels:` ones (phase 9).

### 5 — Prove the scorer on the renders already on disk, before any money is spent

`outputs/final/20260905T135736Z/` and `.../20260905T140151Z/` hold five renders each at **1024×1600**
and **1024×1472** — two different subjects, jittered dials, from this exact pipeline. Wrong dials and
wrong subjects, but real 1024-canvas PNGs, and they will surface every plumbing failure for free
(design.md D13). They are untracked; confirm they are still there before planning around them.

Run `evaluate.py` end to end against both. Their `run.json` predates phase 3, so it names no
photograph — the scorer must **report the missing provenance rather than guess**, and that path is
exercised here for the first time.

**Verify:** the scorer runs to completion on both directories, or fails naming what it lacks; the
missing-provenance path is exercised and its message recorded in the CHANGELOG entry. No claim is made
about the numbers — the dials moved six ways per render and these are two different people.

### 6 — 🛑 **HUMAN · HALT** — the six subjects: a tracked builder, digests recorded, pixels not committed

`probe/build_inputs.py`'s treatment, because one version does not silently reverse a convention the
previous one wrote down (design.md D15). Byte-reproducible recipe, SHA-256 recorded per file, pixels
uncommitted.

Six subjects, each earning its slot adversarially (design.md D11): **two** with multi-tone or
non-uniform hair, against the dominant-colour metric's known limitation; **one** non-frontal or
occluded face, exercising the guard's refusal path and the absent-face field; **one landscape input**,
which closes a gap `CHANGELOG.md` v0.11 names explicitly — landscape is still untested on a GPU; **two**
controls. The four to be labelled in phase 9 are named here, and the two refusal-path subjects are
not among them.

**Verify:** two consecutive runs of the builder produce identical digests; the digests are recorded;
`make gate` green. Residual risk stated in the CHANGELOG: if the source photographs are lost, the
baseline becomes unreproducible and the labels are the only surviving artifact.

### 7 — ⚠️ **GPU · HALT** — one session on `:v0.11-rc`, thirty fixed-dial renders

**Announce before `infra/up.sh`. Wait for the human "go" if the RunPod MCP is unreachable.**

Six subjects × five seeds, **dials held** (phase 2's flag), on the already-built `:v0.11-rc` so
rebuild drift is held constant rather than measured (design.md D14). Set `RUNPOD_IMAGE` to
`:v0.11-rc` before, clear it after.

Download every render **before teardown** — GPU renders live on ephemeral disk and only the models
volume persists.

`infra/down.sh` is the act that stops the billing and belongs to this session. Confirm the pod is gone
through the RunPod MCP and **record what it returned**.

**Verify:** thirty PNGs plus `run.json` carrying full provenance; each render's dimensions equal the
target the injector computes from its own photograph; the landscape subject rendered at all, which is
new; wall clock and cost recorded against the 25-minute money ceiling; teardown confirmed with the MCP
response transcribed.

### 8 — The three probes, local and free; the guard is decided here

CPU, `$0`, against phase 7's renders.

1. **The guard, both ways.** Box IoU and landmark-centroid alignment, on the same renders, at the
   working denoise. **Whichever holds ships as the guard; if neither holds, the region axes refuse and
   that refusal is what this version reports** (design.md D9). Moving `denoise` to make the meter work
   is disqualified — the product is not tuned to flatter the instrument. This decision is
   pre-committed here and is not revisited after seeing the numbers.
2. **Does StyleID separate a same-subject batch from a different subject**, at fixed dials, across six
   subjects. This can kill StyleID; with n=6 it cannot license it, and the writeup says so.
3. **Does DWPose read one of these renders at all.** If it does not, the pose axis reports its absence
   rather than a zero.

**Verify:** each probe's numbers recorded; the guard's authoritative method chosen, committed and
bound to `evaluation:guard:method-is-reported`; any axis a probe kills is removed from the report in
this phase, with its removal recorded.

### 9 — 🛑 **HUMAN · HALT** — the pairwise sheet, and forty blind judgements committed alone

The scorer emits a sheet of within-subject pairs carrying **no scores**: four subjects × ten pairs =
forty, order randomised (design.md D10).

The operator fills it in — pairwise because a forced A/B is stable where a 1–5 rating drifts across a
sitting; within-subject because comparing two different people's renders is a question with no
meaning; holistic because the felt sense of identity is holistic.

**The filled sheet is committed in its own commit, before any score for these renders is computed.**
Git ordering is what proves the labels were not contaminated. The consequence is accepted and printed:
a holistic label cannot attribute a disagreement to one axis.

**Verify:** the sheet contains no metric value; every pair draws both renders from one subject; forty
judgements recorded; the commit that adds them touches no score file. Tests bound to
`evaluation:labels:sheet-carries-no-scores`, `:pairs-are-within-one-subject`,
`:correlation-requires-prior-labels`.

### 10 — The correlation, reported whatever it says

Run the scorer over the thirty renders. Correlate the forty judgements against each axis separately,
never rolled up, with the count of judgements printed beside every figure (design.md D2, D17).

**This table is the product of v0.12.** Not the scores — the answer to whether any of this tracks the
operator's eye. If an axis lands near a coin flip, that is the finding and it ships.

The CHANGELOG entry states what this version **does not** establish, drafted before the numbers were
seen: that no metric is shown to measure identity; that no score is comparable across bases or
batches; that no dial is shown better than another; that `cn_strength` 0.5 is unsearched and merely
now searchable; that rebuild drift is recorded and unmeasured; and that there is no percentage, no
verdict and no threshold.

**Verify:** `make gate` green; the correlation table written; tests bound to
`evaluation:labels:correlation-is-per-axis`; the "does not establish" paragraph present in
`CHANGELOG.md`.
