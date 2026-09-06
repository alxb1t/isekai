---
version: v0.12
---

## Why

Nothing in this repository measures its own output, and v0.11.0's changelog says so in terms:
*"**nothing** about identity, fidelity or quality — no evaluator exists and none was run."* Every dial
in `workflows/pipeline.json` was chosen by eye, two register A/Bs are parked waiting on a number that
does not exist, and `cn_strength` — one of the identity node's two dials — has never been searched at
all. The project cannot answer the question it exists to answer.

This version does **not** answer it either. It builds the instrument, and then measures the instrument
against the operator's eye. That order is deliberate: a scorer nobody has checked is worse than no
scorer, because it licenses tuning against a number that may be noise.

## What Changes

**The product's render path gains one capability and one guarantee; a second entry point is added; and
the version's finding is a correlation, not a score.**

- **A render with the graph's own dials becomes possible.** `pipeline.run` calls `mutate`
  unconditionally on every variation, and `mutate` moves six dials — `denoise`, `cfg`, `ip_weight` and
  all three ControlNet strengths. There is today **no code path that renders the committed graph**, so
  "same subject, same seed, one thing moved" is not a claim this repository can make. Mutation becomes
  suppressible, and the fixed-dial render is what a baseline means.
- **`cn_strength` becomes settable and pinned.** It sits at 0.5 in `workflows/pipeline.json` and is
  referenced nowhere else in the tree: not in `apply_overrides`, not in `mutate` (which walks
  `ControlNetApplyAdvanced` and never `ApplyInstantIDAdvanced`), not in any test. This version makes it
  searchable. It does **not** search it — see `design.md` D6.
- **`run.json` becomes a provenance record.** It records `seed`, `variations`, `seeds` and `overrides`,
  and therefore cannot name the photo that produced it, the graph, the checkpoint, the working
  resolution or the resolved dials. A baseline nothing can identify is not a baseline.
- **`scripts/eval_models.json`** — a pinned, checksummed manifest of every model the scorer loads, a
  **sibling** of `scripts/models.json` rather than an addition to it: that file is what the pod
  provisions the *graph* from. The recognizer the scorer reports as a sanity channel reuses the
  graph's own `glintr100` pin byte for byte. Every licence was read before this change was
  scoped and none forbids the use: four artifacts are non-commercial research and are carried as
  recorded deviations, one — `yolov8_animeface`, **AGPL-3.0** — is a copyleft problem rather than a
  usage one and is solved by loading it through `onnxruntime` and never importing `ultralytics` into an
  Apache-2.0 public repository.
- **`evaluate.py`** — a second entry point, never on `convert.py`'s import graph, behind an optional
  `isekai[eval]` extra. Four axes over a shared canvas: face (StyleID, with ArcFace as a sanity
  channel), pose (PCK), hair colour (CIEDE2000 + mask area), and a face-location guard that refuses the
  region axes rather than scoring the wrong pixels.
- **A blind pairwise labelling pass.** The scorer emits a comparison sheet; the operator fills in 40
  within-subject judgements; the sheet is committed **before** any score is computed, so git is what
  proves the labels were not contaminated.
- **⚠️ One metered session** on the already-built `:v0.11-rc`, six subjects × five seeds at fixed
  dials, ~19 min ≈ $0.23 against the 45-minute / ~$0.30 wall.

**What this version ships as its finding** is the agreement between those 40 judgements and each axis.
If an axis does not track the operator's eye, that is the result and the version ships it.

**Deliberately not here**, each with its reason in `design.md`:

- **No verdict, no threshold, no percentage.** Thresholds need labels; this version is what produces
  the first labels. A number invented now would be a preference wearing a measurement's clothes.
- **No clothes axis and no DINOv3.** The labels are holistic identity judgements and cannot validate a
  garment metric, and deferring DINOv3 defers its licence question with it.
- **No `cn_strength` sweep and no register A/B.** Both would validate the instrument and use it on the
  same pixels. They are v0.13's opening act, run against the baseline this version commits.
- **No rebuild-drift measurement.** The baseline is pinned to `:v0.11-rc` so drift is held constant
  rather than measured; that it is unmeasured is stated rather than smoothed over.

## Capabilities

### New Capabilities

- `evaluation`: scoring one render against the photo that produced it — the shared canvas the masks and
  the render agree on, the face-location guard and its refusal, the four axes and what each may claim,
  the cross-base refusal, the report artifacts, and the blind pairwise labelling protocol.

### Modified Capabilities

- `workflow-mutation`: mutation becomes suppressible. The existing scenarios describe a graph whose
  dials are always jittered; a fixed-dial render is a second, stated behaviour, and it is what makes a
  reproducible baseline possible at all.
- `cli`: `run.json` gains the provenance a later run needs to identify what produced it — the input
  photo's digest, the graph's digest, the resolved working resolution and the per-variation resolved
  dials. `cn_strength` joins the dials the CLI can set.

### Removed Capabilities

None.

## Impact

- **Code** — `isekai/pipeline.py`, `isekai/mutate.py`, `isekai/overrides.py`, `isekai/cli.py`,
  `workflows/pipeline.json` (no dial moves; `cn_strength` is pinned where it stands), `evaluate.py` and
  `isekai/evaluate.py` and `scripts/eval_models.json` (new), `pyproject.toml`, `tests/`.
- **Not touched** — `convert.py`'s import graph, `isekai/workflow.py`'s injection and header parsing,
  `isekai/comfy_client.py`, `isekai/provision.py`, `Dockerfile`, `scripts/models.json`. No model
  artifact moves, so **no image is rebuilt and no volume is re-provisioned**.
- **Dependencies** — the runtime stays stdlib-only and `convert.py` keeps `dependencies = []`, held by
  a test that imports it without site-packages. The scorer's stack lands in an optional `[eval]` extra
  which **CI does not install**: the eval tests skip there and run on the operator's machine, the same
  posture this repository already takes toward diffusion quality. The gate array stays five commands.
- **Money** — one metered pod session, ~19 min ≈ $0.23. The scorer itself is local, CPU, $0.
- **Human time** — 40 pairwise judgements, done blind, by the operator. Not delegable.
