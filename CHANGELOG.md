# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

> **On this record's provenance.** This file was **backfilled during v0.7**, from the git
> history, after eleven phases and three releases had already shipped without it. Entries are
> reconstructed from commit messages and diffs; **anything the log does not support is not
> written here.** From v0.7 on, an entry is appended per phase under `## [Unreleased]

### Removed

- **The `qwen`, `animagine` and `animagine-i2i` paths.** All three are superseded by
  `animagine-i2i-cn`, which alone preserves identity, composition and pose. Gone with them:
  `workflows/qwen-image-edit.json`, `workflows/qwen-image-edit.reference.json`,
  `workflows/animagine-instantid.json`, `workflows/animagine-i2i.json`, their test fixtures,
  `inject_qwen`, and the four Qwen downloads in `scripts/download_models.sh`.
- **The `model-registry` capability.** Its three requirements — name resolution, injector
  pairing and mutation pairing — all describe a choice that no longer exists, so
  `openspec/specs/model-registry/` and `tests/test_model_dispatch.py` are deleted. The living
  spec goes from five capabilities to four.
- **Tests bound to the deleted paths**, including
  `test_run_without_overrides_is_byte_identical_to_v04`, which pinned v0.4's output for a path
  that is now gone, and the Qwen-only guards for a wired `cfg` dial and a graph with no identity
  node. Deleting them took the suite from v0.7's 114 tests to 81; the count going down is the
  work, not a weakened gate.
- **`tests/fixtures/`.** The fixtures were byte-identical copies of the shipped graphs with no
  drift check — a second thing to rename and a silent divergence waiting to happen.
  `tests/conftest.py` now loads `workflows/pipeline.json` directly.
- **`--model`, `--workflow` and `--prompt`.** The whole required surface becomes
  `convert.py photo.jpg`. `--prompt` was **required**, so this is **BREAKING** for every
  existing invocation: the positive prompt is now committed to the graph, which is what makes a
  render attributable. `--workflow` has no equivalent — edit `workflows/pipeline.json`.
- **Variation 0's verbatim-seed exemption.** Its stated reason was back-compat with releases
  this change deletes, and it left `--seed` with two meanings: a stream seed for variations
  1..N and a literal sampler seed for variation 0. **BREAKING**: `--seed 42` no longer
  reproduces v0.7's first render.
- **The conditioning trace in `inject`.** With no prompt to place, the walk from
  `KSampler.positive` to the first `CLIPTextEncode` has no caller. Its non-obvious insight —
  that the sampler's positive input may reach the encoder through a stack of ControlNet apply
  nodes, so it must be followed rather than looked up — is recorded in the change's `design.md`
  and in the `workflow-injection` capability header.
- **The model registry and every seam with nothing passing through it.**
  `isekai/models.py`, `Model` and `get_model` are deleted, and `Injector` and `Mutator` go with
  them from `isekai/comfy_types.py`. `pipeline.run` loses its `inject` and `mutate` parameters
  and imports them instead. `ComfyTransport` **stays** a parameter — `FakeComfyClient` is what
  makes the suite offline — and so does `workflow`, which keeps file I/O in the CLI. The rule
  this change learned: *a parameter is a seam only if something else is actually passed through
  it.*
- **Every branch with no reachable caller**: `overrides.py`'s silent no-op when a graph carries
  no `ApplyInstantIDAdvanced`, `mutate.py`'s wired-dial guard (it existed because Qwen wired
  `cfg`) and its `"102:14"` subgraph-id ordering, the `mutate is None` branch in `run`, and
  `find_node`'s `title` parameter — which no caller ever passed.
- **`arms crossed` from the committed positive prompt.** Pose is the OpenPose ControlNet's axis;
  a pose tag in the prompt competes with the mechanism that owns it. That is an architectural
  argument and needs no render to justify it — **this change makes no claim about what the graph
  now renders.**

### Changed

- **The surviving path is renamed to nothing.** `workflows/animagine-i2i-cn.json` →
  `workflows/pipeline.json`, `workflows/animagine-i2i-cn_ui.json` →
  `workflows/pipeline_ui.json`, `inject_animagine` → `inject`, and the one remaining `--model`
  value → `pipeline`. Every name available today describes the base or the technique, and v0.9
  replaces the base; the only name that version cannot invalidate is no name. The flag itself
  is then removed outright — see below.
- **Spec keys lose their model segment**:
  `workflow-injection:photo-wiring:controlnet-single-loader-across-stack` →
  `…:single-loader-fans-out`, and
  `workflow-injection:latent-init:img2img-inits-from-photo-below-one` →
  `…:inits-from-photo-below-one`.
- **BREAKING: `-o` names a directory, not a file**, defaulting to `./outputs`. A run writes
  `<output-dir>/<UTC instant>/0.png` … and a `run.json` beside them. An `-o` naming a file with
  an image extension is **rejected at parse time** — otherwise an upgrading caller silently gets
  a directory called `out.png`.
- **BREAKING: `--variations` defaults to 5**, capped at 25. Five renders to choose between is
  the product rather than an option; the ceiling exists because every variation is one billed
  GPU render, so an unbounded count bills a mistyped digit at GPU rates.
- **Every variation's seed is derived uniformly** from `--seed`, variation 0 included. The
  per-variation seed is still printed, and is now also recorded in `run.json`.
- `main()` resolves the run directory and hands the **resolved** path to `run`, which draws no
  clock of its own — which is what keeps the suite offline and deterministic.

### Added

- **Timestamped run directories and `run.json`.** The manifest records the seed the run was
  given, the per-variation seeds actually drawn and the dial values in force, so a run describes
  itself instead of depending on the operator still having the terminal it was printed to.
- **The positive prompt is pinned by equality** in the suite, and commented in
  `workflows/pipeline_ui.json` with the version that owns its register. "The string holds no
  subject text" has no mechanical form — a blacklist assertion is defeated silently by any
  rewrite — so equality makes every future prompt edit a deliberate test edit.

### Known defects

- **`1girl` fixes the gender of every input photo**, in a product whose input is "a photo of a
  person". `1girl, solo` is the Danbooru mode selector for this base rather than subject text,
  and an empty positive is not neutral on a Danbooru-trained checkpoint, so removing it would be
  a register decision. v0.8 changes no base and therefore decides no register: the defect is
  stated here and owned by **v0.9**, the version that can probe a replacement against real
  renders.

## [0.7.0] - 2026-09-01

Adoption of the OpenSpec SDD repository standard, plus the defects that adopting it exposed.

### Added

- **The spec tree.** `openspec/specs/` across five capabilities — `model-registry`,
  `workflow-injection`, `workflow-mutation`, `comfy-transport`, `cli` — as keyed scenarios
  describing behaviour the repo already shipped. 91 scenarios across 22 requirements.
- **The change tree.** `openspec/changes/` with `archive/`, and `0001-mf-standard` carrying
  all four artifacts. The zero spec delta is declared with `skip_specs: true` in a tracked
  `.openspec.yaml`, so `openspec validate --strict` passes.
- **Spec-to-test binding.** `spec` and `spec_exempt` markers registered in
  `[tool.pytest.ini_options]`, and every test bound to the scenario it proves — 117 bindings,
  zero unmarked tests.
- **A root `Makefile`** with a `gate` target mirroring the declared gate array command for
  command, so the gate a human types cannot drift from the one the orchestrator runs.
- **`.python-version`**, pinning the interpreter to 3.12.
- **`## How a change is cut here` in `CLAUDE.md`** — the change contract stated in-tree for
  the first time: the four artifacts, the id scheme, the authoring commands, the `Change:`
  trailer, the version line.
- **Docstrings and type annotations throughout `isekai/`**, under a widened ruff selection.
- **This file.**

### Changed

- **The gate config moved to `.minions/minions.toml`**, the one path the orchestrator reads;
  `.gitignore` now excludes `.minions/*` while re-including that single tracked file.
- **CI invokes `make gate`** rather than keeping a third copy of the command list, which had
  already drifted — it was running `ruff format --check` and `ruff check` without the `.` the
  array names.
- **Ruff lint selection widened** from ruff's default to `["E", "F", "I"]`, then to
  `["E", "F", "I", "D", "ANN"]`. Selecting `E` whole enables `E501` line-length; `D` and `ANN`
  add docstrings and annotations.
- **`CLAUDE.md` rewritten** onto the repo's in-tree contract, and then onto the standard's
  template.
- **`README.md` rewritten.** It had duplicate `Quickstart` and `Setup` sections, marked
  shipped files `(planned)`, named one model where four ship, and mentioned the gate nowhere.
- **`.env.example` is now path-free**, declaring shape only.

### Fixed

- **`--variations N` billed N identical renders** on `qwen` and `animagine`. Both are
  registered without a mutation seam, so the graph never varied and N paid renders produced
  one image. Now refused before the photo is uploaded.
- **`--seed` was validated and then silently discarded** on those same models.
- **`--variations 0` uploaded the photo, rendered nothing and exited 0.** Now rejected at
  parse time.
- **`mutate` crashed with a bare `TypeError` on a linked dial.** In ComfyUI API format an
  input may legally be a `[node_id, slot]` link, and `workflows/qwen-image-edit.json` drives
  `cfg` that way — so a documented flag combination died on a raw arithmetic error. Now stops
  with a message naming the dial and the node driving it.
- **`--denoise 0.0` was silently discarded**, the value being falsy rather than absent.
- **`ValueError` on subgraph node ids.** Node ordering used `sorted(key=int)`, which cannot
  parse an id like `102:14`; the repo ships a graph containing exactly that.
- **A stray `$` in the unknown-model exit message.**

## [0.6.0] - 2026-08-15

### Added

- **`isekai/overrides.py`** — an `apply_overrides` seam setting user-chosen base dial values
  by `class_type`, and `--denoise` `[0, 1]`, `--cfg` `[0, 30]`, `--ip-weight` `[0, 1]` on the
  CLI, with a bounded-float argparse type factory turning an out-of-range value into a clean
  exit. `pipeline.run` applies overrides per variation **before** `mutate`, so
  `--denoise X --variations N` jitters around `X` and `--seed` reproduces the set.
- **`.minions/minions.toml`** (as `minions.toml` at the root), first declaring the gate array.

### Changed

- **Jitter is base-relative.** `mutate` reads a node's current value as the base and draws
  `uniform(base ± δ)` instead of an absolute `uniform(lo, hi)` — denoise ±0.05, cfg ±0.5,
  ip_weight ±0.05, each clamped to its valid bound. At the baked defaults this is
  byte-for-byte identical to the previous behaviour, pinned by a characterization test.

## [0.5.0]

Skipped — see the note at the top of this file.

## [0.4.0] - 2026-08-04

### Added

- **The workflow-mutation seam.** `mutate(workflow, rng)`, separate from `inject_*`: sets the
  KSampler seed and bounded-jitters `denoise` / `cfg` / `ip_weight`. `random.Random` is
  dependency-injected, so randomized code is deterministically unit-tested.
- **`--seed` and `--variations`**, validated at the boundary. Each variation's seed is
  printed — the reproducibility contract.
- **The `animagine-i2i-cn` model** — `animagine-i2i` plus a tile / OpenPose / lineart
  ControlNet stack, with `comfyui_controlnet_aux` and the SDXL ControlNet weights pinned into
  the image.
- **A generalized injection trace.** `inject_animagine` now walks `.positive` to the first
  `CLIPTextEncode`, so it lands through a ControlNet chain of any depth and serves the whole
  InstantID family.
- **ControlNet strength jitter** — every `ControlNetApplyAdvanced` strength varies ±0.1 around
  its tuned baseline, in deterministic node-id order so a seed reproduces the whole graph. A
  no-op on graphs without ControlNet nodes.

### Changed

- The default `--model` is now `animagine-i2i`.

## [0.3.0] - 2026-07-31

### Added

- **The `animagine-i2i` model** — the Animagine + InstantID base as img2img, taking its latent
  init from the photo via `VAEEncode` at `denoise < 1`, so the photo's composition survives.
  `denoise` becomes the identity-versus-style dial.
- The real exported Animagine img2img workflow, with the test fixtures locked to it.

## [0.2.0] - 2026-07-31

### Added

- **Model dispatch.** `--model {qwen,animagine}`, built test-first: each model owns a workflow
  JSON and an injection strategy, resolved through a name-to-`Model` registry.
  `pipeline.run` takes the strategy as a parameter rather than hardcoding Qwen.
- **The `animagine` model** — Animagine XL 4.0 with InstantID and InsightFace, where identity
  is an injected signal (face embedding and keypoints) on a from-noise SDXL base. InstantID
  nodes and weights added to the image.
- **The test harness and the transport seam** — a `uv` project with pytest, and a fake client
  standing in for ComfyUI so the suite runs offline.
- The real exported Animagine + InstantID workflow, with the test fixtures locked to it.

## [0.1.0] - 2026-07-28

### Added

- **The headless conversion pipeline.** `convert.py`, a zero-dependency CLI (stdlib `urllib`
  only) that uploads a photo, injects photo and prompt into a ComfyUI workflow by node
  `class_type` / title, submits to `/prompt`, polls `/history` and downloads from `/view`.
- **The container environment as code.** A CUDA base image with `uv`, PyTorch and ComfyUI
  serving on `:8188`, no model weights baked in; a compose file for local GPU passthrough;
  CI publishing the image to GHCR; and `scripts/download_models.sh` fetching Qwen-Image-Edit.
- **SSH into the pod image**, so `ssh -L` can reach ComfyUI privately: `start.sh` installs the
  injected public key, starts `sshd`, then runs ComfyUI in the foreground.
- **On-demand pod lifecycle.** `infra/up.sh` creates a pod from the GHCR image with the models
  volume and SSH attached, polls for its address and prints the tunnel command;
  `infra/down.sh` deletes it so per-second billing stops.
- **Self-provisioning models on boot** — `start.sh` downloads weights idempotently before
  launching ComfyUI, so a fresh pod populates the volume without manual setup.
- The validated API-format Qwen-Image-Edit workflow, and the runbook to drive it.

### Fixed

- **Blackwell (sm_120) GPUs could not run the image.** cu124 kernels gave "no kernel image is
  available"; PyTorch is pinned to 2.8.0 / cu128, whose wheels ship sm_120 kernels.

[Unreleased]: https://github.com/alxb1t/isekai/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/alxb1t/isekai/compare/v0.3...v0.7.0
[0.6.0]: https://github.com/alxb1t/isekai/compare/dffdd63...bbe6924
[0.4.0]: https://github.com/alxb1t/isekai/compare/v0.3...dffdd63
[0.3.0]: https://github.com/alxb1t/isekai/compare/v0.2...v0.3
[0.2.0]: https://github.com/alxb1t/isekai/compare/v0.1...v0.2
[0.1.0]: https://github.com/alxb1t/isekai/releases/tag/v0.1
