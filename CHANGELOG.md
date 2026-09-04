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

### Changed

- **The 62 GB models volume was inventoried, and nothing on it is unaccounted for.** One pod,
  read-only, 6.6 minutes of wall clock; teardown confirmed through the RunPod MCP, which returned
  an empty pod list and `404 pod not found` for the pod's id. On cost the two available figures
  disagree and both are recorded rather than one being chosen: 6.6 minutes at the pod's quoted
  $0.72/hr is $0.08, while RunPod's daily aggregate reports $0.19 of pod GPU for the day, and the
  per-pod hourly breakdown had not settled at the time of writing. Either figure is inside the
  ceiling. 48 files, 55.85 GiB, classified
  exhaustively:

  | class | files | size | |
  |---|---|---|---|
  | placed by this project's script | 11 | 16.15 GiB | every non-annotator entry of the v0.9 manifest |
  | placed by the sibling project | 10 | 10.81 GiB | nested one level deeper, under `models/` |
  | orphaned Qwen weights | 4 | 28.89 GiB | removed from the script by v0.8, never from disk |
  | staging and cache leftovers | 23 | ~1 KB | the `.hf` tree, three `.cache/huggingface` trees, one 0-byte `.partial` |
  | **unaccounted for** | **0** | **—** | **the gate on phase 9's destroy** |

  Both projects' scripts are pinned and checksummed, so everything the first two classes hold is
  re-downloadable; the remaining 28.89 GiB answers to nothing.
- **The annotator gap is confirmed empirically.** All four annotator checkpoints —
  `yolox_l.onnx`, `dw-ll_ucoco_384_bs5.torchscript.pt`, `sk_model.pth`, `sk_model2.pth` — are
  **absent from the volume**. They were being re-fetched to container disk on every pod's first
  render, exactly as the proposal argued from reading the graph.
- **The antelopev2 pin is confirmed from the volume itself.** The leftover cache tree names
  `ba0c3e10f4548361eb9a63265d87ce1140ab5a05` — the same DIAMONIK7777 revision the manifest pins,
  recorded independently by a download this change did not make.
- **The volume was extended from 62 GB to 80 GB** by the operator during this phase, so the
  "98% full" pressure recorded in `proposal.md` is relieved. It does not change the plan: the
  volume is still replaced rather than pruned, because pruning proves nothing about the manifest.
- **Correction to `proposal.md` and `design.md`: the two repositories' `.env` files do *not*
  disagree.** Both name the same volume id, and it is the account's only volume. What differs is
  the **key name** — this repo uses `RUNPOD_VOLUME_ID`, the sibling `RUNPOD_NETWORK_VOLUME_ID` —
  which is almost certainly what was mistaken for a stale id. There is no stale id to reconcile;
  phase 9 still updates both.
- **Phase 9's open question is answered.** Both manifests together are ~27.3 GiB
  (this project 16.5 GiB across 15 entries, the sibling 10.8 GiB), so the new volume needs
  roughly 40 GB for comfortable headroom — half of what the current one now carries, once the
  orphaned Qwen weights are gone.

- **`README.md` and `CLAUDE.md` describe a pinned stack.** The weights line now says the stack is
  provisioned from a pinned, checksummed manifest and that the volume is namespaced per project;
  the layout gains `scripts/models.json`, `scripts/derive_manifest.py` and `isekai/provision.py`;
  the pod-lifecycle diagram shows the `/runpod-volume` mount and the namespace symlink.
  `CLAUDE.md` records that the living spec goes to five capabilities when `model-provisioning` is
  archived, and that `provision.py` is not in `convert.py`'s import graph, so the stdlib-only
  runtime rule is untouched. **No claim is made about identity, quality or the base** — this
  version changed none of them. The five-command gate array is unchanged.

- **The volume mounts at `/runpod-volume` and the models directory is one symlink into this
  project's namespace.** `infra/up.sh`'s `volumeMountPath` moves off `/opt/ComfyUI/models`, and
  `start.sh` points `/opt/ComfyUI/models` at `/runpod-volume/isekai`. Because
  `folder_paths.models_dir` is then itself inside the namespace, **every** node resolves there —
  including the InstantID node and the Impact Subpack, which ignore `extra_model_paths.yaml` and,
  unredirected, auto-download a broken nested antelopev2 pack. One symlink also makes a scratch
  namespace and a rollback the same operation.
- **The volume is shared, so nothing here reaches outside `/runpod-volume/isekai`.** Artifacts
  the sibling project also uses are duplicated rather than shared: at $0.07/GB/month that is
  about 32¢/month, and it keeps this project's manifest describing bytes this project's pins
  control.

- **`AUX_ANNOTATOR_CKPTS_PATH` moves 386 MB of annotator checkpoints onto the volume.**
  `comfyui_controlnet_aux` writes them to `<node dir>/ckpts` — the pod's container disk, which
  does not survive the pod — so `yolox_l.onnx`, `dw-ll_ucoco_384_bs5.torchscript.pt`,
  `sk_model.pth` and `sk_model2.pth` were re-fetched from Hugging Face, unpinned, during the
  first render of every pod, on metered time. Redirected onto the models tree they are ordinary
  manifest entries, fetched and verified ahead of time. The pack reads the variable as
  `os.getenv(NAME, default)`, so the environment wins over its own `config.yaml`.
- **⚠️ The pack's own log cannot confirm this.** It prints `Using ckpts path: …` from the
  *config-derived* value, not from the override, so it will report the old path while writing to
  the new one. Confirmation is a directory listing on the pod, never a log line. A future reader
  will otherwise reach for the log and conclude the redirect failed.

### Added

- **The graph and the manifest are bound by a test.** Every model filename `pipeline.json` names
  in a node's input must have a manifest entry, matched against the tail of a destination so
  `instantid/diffusion_pytorch_model.safetensors` and `openpose/diffusion_pytorch_model.safetensors`
  stay two files rather than one. This is the only mechanism that would have caught the annotator
  gap, and the only one that stops it reopening when v0.10 edits the graph.
- **A tracked mapping from node class to the files that node fetches for itself**
  (`PREPROCESSOR_MODELS`), carrying the half of the binding the graph cannot supply.
  `LineArtPreprocessor` names no file and downloads two. A graph containing a preprocessor whose
  class is absent from the mapping **fails** rather than passing silently — an unmapped
  preprocessor is an unknown quantity, not a safe default. An empty tuple is a real answer:
  `TilePreprocessor` fetches nothing, and `DWPreprocessor` names its two files in its own inputs.
  The reverse direction is deliberately not asserted — the manifest legitimately carries the
  antelopev2 pack, which `InstantIDFaceAnalysis` resolves by directory and no graph field names.

### Changed

- **`scripts/download_models.sh` is a thin driver over the manifest.** It asks
  `provision.py` for a plan, runs `wget` for whatever URL it is handed, and asks the module to
  verify and land the result. Every entry is decided before any byte moves, so a mismatch on a
  warm volume stops the run instead of surfacing halfway through a 6.9 GB transfer. The inline
  per-model shell variables are gone — every source is now a URL string the manifest carries and
  the suite can inspect.
- **The image carries provisioning's three files, not one.** The `Dockerfile` copied only the
  script; it now also copies `scripts/models.json` and `isekai/provision.py`, preserving their
  relative layout because the module resolves the manifest relative to itself. `start.sh` invokes
  the driver at its new path.
- **`wget` is installed in the image.** The previous downloader used the `hf` CLI, so the image
  never needed it; the ported one does, and the image shipped `curl` alone.
- **Pre-flight does not follow the redirect.** `resolve/<sha>/<path>` answers 302 and carries
  `x-linked-etag` on *that* response — the CDN it points at does not repeat it — so following the
  redirect loses the header and silently degrades every entry to post-download verification. All
  fifteen entries were confirmed live to pre-flight and match.

### Removed

- **The `hf` CLI dependency.** Sources are plain `resolve/<commit-sha>/` URLs fetched with
  `wget`. The cost is `hf`'s resumable, parallel transfer; the `.partial` discipline means an
  interrupted transfer restarts from zero rather than being trusted.

### Added

- **The provisioning policy, in `isekai/provision.py` and reachable by `pytest`.** For each
  manifest entry the module returns exactly one decision: **skip** (present and its digest
  matches), **abort** (present and it does not — and the file is *left on disk*, because the
  volume is shared and a file this run did not write is not this run's to remove), or **fetch**
  from a named source. A file already at its destination is hashed, never taken on its name:
  verification that ran only on the download path would leave a warm volume permanently
  unchecked, which is the case the digest exists for. `land()` verifies a transferred file and
  only then moves it into place, so an interrupted or tampered transfer never occupies the final
  name — the next run sees the file as absent rather than as present-and-trusted.
- **A pre-flight seam.** Hugging Face publishes a file's SHA-256 in the `x-linked-etag` response
  header, so a source whose published digest already disagrees with the manifest is rejected in a
  second rather than after a multi-gigabyte transfer, and the entry's next declared source is
  offered instead. This is an optimisation, never a check: a source that publishes nothing — or
  a header that cannot be read — degrades to download-and-post-verify, never to trust. The seam
  is injected and `FakeFetcher` is what keeps the suite offline, the same argument and the same
  shape as `FakeComfyClient`.
- **`scripts/models.json`, a pinned and checksummed manifest of every model artifact the
  shipped graph needs — fifteen files across eleven sources.** Each entry names a destination
  under the models tree, a SHA-256, and an ordered list of `resolve/<commit-sha>/` URLs, so a
  source addresses bytes that cannot move. Four of the entries are the annotator checkpoints
  `DWPreprocessor` and `LineArtPreprocessor` fetched for themselves at graph-execution time —
  386 MB that nothing in this repository named, and that every fresh pod re-downloaded onto
  ephemeral disk during a metered render. `LineArtPreprocessor` fetches both `sk_model.pth` and
  `sk_model2.pth` unconditionally, regardless of the graph's `coarse: "disable"`, so both are
  declared.
- **`scripts/derive_manifest.py`, the helper that produced it.** Digests are *derived*, never
  transcribed: Hugging Face publishes each LFS object's SHA-256 as its object id, so no artifact
  is downloaded to learn its digest, and every alternate source is cross-checked against its
  primary at derivation time. Revisions are data in the helper rather than resolved from a
  branch, so re-running it is byte-identical — `git diff --exit-code scripts/models.json` is the
  check that the tool and the committed data have not diverged.
- **`isekai/provision.py`, the manifest's reader and its offline checks** — no source resolves a
  mutable ref, every entry carries a well-formed SHA-256, and every entry whose primary source is
  a mirror rather than the artifact's publisher declares an alternate. Each check is proven
  against a deliberately malformed entry as well as against the tracked file. The module is
  stdlib-only (`json`, `re`, `pathlib`) and is not in `convert.py`'s import graph.

## [0.8.0] - 2026-09-04

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
- **`README.md` and `CLAUDE.md` describe one path.** The four-row model table, `--model` and
  `--prompt` in the quickstart, and the "four selectable models" status line all go; the run
  directory layout is shown instead. `CLAUDE.md` retires the additive-models invariant — **"there
  is one path; a version may replace it, it may not add a second"** — and replaces the registry
  seam with the rule this change learned: *a parameter is a seam only if something else is
  actually passed through it.* The conditioning-trace insight the deleted code carried is
  preserved there by name.
- The `README.md` license line no longer claims to match a model license the repo does not ship;
  it states the repository's own licence and that weights are licensed by their publishers.
- **`CLAUDE.md`'s metered-work guardrail is rewritten.** Teardown confirmed through the RunPod
  MCP replaces the blanket "wait for an explicit human go". The new rule states all four things
  the old protocol got for free from a human being present: who **creates** (`infra/up.sh`), who
  **tears down** (`infra/down.sh` — teardown is the act), who **confirms** (the MCP — and
  confirmation is *not* the act), and what it **degrades to** when the MCP is unreachable (the
  human "go", unchanged, for the whole session). It carries a stated ceiling: **45 minutes,
  ~$0.30** per pod session. This is an authority *expansion* in an otherwise subtractive change,
  which is why it is its own entry rather than folded into the docs one.

### Verified

- **The one path was run live on a GPU pod on 2026-09-04**, on our own image against the
  persistent models volume: `convert.py <photo>` exited 0 for two separate input photos, each
  writing `outputs/<UTC instant>/` with `0.png`–`4.png` and a `run.json` carrying five seeds.
  This records that the path **runs**; it makes no claim about fidelity, identity or quality,
  for which this repository still has no evaluator.

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
