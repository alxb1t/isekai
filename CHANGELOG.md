# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

> **On this record's provenance.** This file was **backfilled during v0.7**, from the git
> history, after eleven phases and three releases had already shipped without it. Entries are
> reconstructed from commit messages and diffs; **anything the log does not support is not
> written here.** From v0.7 on, an entry is appended per phase under `## [Unreleased]` and cut
> at release, as the project's change contract requires.
>
> Two gaps in the record, stated rather than smoothed over:
>
> - **There is no 0.5.0.** The history goes v0.4 (2026-08-04) directly to v0.6 (2026-08-15).
>   No tag, branch or commit references a v0.5, so the version was skipped rather than lost.
> - **0.4.0 and 0.6.0 were never tagged.** They are real, completed, merged versions and are
>   recorded as releases here; their dates are their last commit rather than a tag date.
>   Tags `v0.1`–`v0.3` also use the two-part form that predates the current release contract.
>
> `0.7.0`'s heading is cut here, in the commit that completes the work; the annotated `v0.7.0`
> tag is the release act and is created against **this** commit, so the four places the
> version line lives — proposal, changelog, `pyproject.toml`, tag — all name the same thing.

## [Unreleased]

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
- **Tests bound to the deleted paths**, including `test_run_without_overrides_is_byte_identical_to_v04`,
  which pinned v0.4's output for a path that is now gone, and the Qwen-only guards for a
  wired `cfg` dial and a graph with no identity node. The suite moves from 114 tests to 81;
  the count going down is the work, not a weakened gate.

### Changed

- `--model` now accepts a single value, `animagine-i2i-cn`, which is also its default. The
  flag itself is removed in a later phase of this change.

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
